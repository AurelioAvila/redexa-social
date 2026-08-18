"""
Versionamento dello schema, con l'attenzione puntata sul caso che conta:
il database di un utente che sta aggiornando da una versione precedente.

Se questi test passano ma l'adozione e' sbagliata, il danno non si vede in
sviluppo (dove il database e' vuoto) e si vede tutto sui computer degli
utenti, che perdono account collegati e licenza.
"""
import os
import sqlite3

import pytest

import db
from db import backup as backup_module
from db import migrations


def _database_come_versione_precedente(path: str) -> None:
    """Ricostruisce un database come lo lasciava la 1.3.x: tabelle create
    dai singoli moduli, nessuna traccia di schema_version, e dati veri
    dentro."""
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE snapshots (platform TEXT, fetched_at INTEGER, data TEXT);
        CREATE TABLE insights (id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL DEFAULT 'all', generated_at INTEGER,
            based_on_fetch_at INTEGER, text TEXT);
        CREATE TABLE kv_cache (key TEXT PRIMARY KEY, saved_at INTEGER, data TEXT);
        CREATE TABLE device (id TEXT PRIMARY KEY);
        CREATE TABLE connections (id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL, account_name TEXT NOT NULL, account_id TEXT,
            data TEXT NOT NULL, created_at INTEGER NOT NULL,
            UNIQUE(platform, account_id));
        CREATE TABLE license (id INTEGER PRIMARY KEY CHECK (id = 1), key TEXT,
            plan TEXT, email TEXT, last_ok INTEGER, last_check INTEGER,
            revoked INTEGER NOT NULL DEFAULT 0);
        """
    )
    conn.execute("INSERT INTO device (id) VALUES ('identificativo-storico')")
    conn.execute(
        "INSERT INTO connections (platform, account_name, account_id, data, created_at)"
        " VALUES ('youtube', 'Canale Storico', 'uc-123', '{}', 1700000000)"
    )
    conn.execute(
        "INSERT INTO license (id, key, plan, email, last_ok, last_check, revoked)"
        " VALUES (1, 'SD-PRO-VECCHIA-CHIAVE', 'pro', 'utente@example.com', 1, 1, 0)"
    )
    conn.commit()
    conn.close()


class TestDatabaseNuovo:
    def test_parte_da_zero_e_arriva_all_ultima_versione(self, tmp_path):
        percorso = str(tmp_path / "cache.db")
        esito = db.ensure_current(percorso)

        assert esito["from"] == 0
        assert esito["to"] == migrations.LATEST
        assert esito["backup"] is None, "un database vuoto non ha nulla da salvare"

        conn = db.connect(percorso)
        assert db.current_version(conn) == migrations.LATEST
        conn.close()

    def test_crea_le_tabelle_di_base(self, tmp_path):
        percorso = str(tmp_path / "cache.db")
        db.ensure_current(percorso)

        conn = db.connect(percorso)
        tabelle = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.close()
        assert {"snapshots", "insights", "kv_cache", "device"} <= tabelle


class TestAdozioneDatabaseEsistente:
    """Il caso vero: un utente che aggiorna."""

    def test_database_preesistente_adottato_come_versione_uno(self, tmp_path):
        percorso = str(tmp_path / "cache.db")
        _database_come_versione_precedente(percorso)

        esito = db.ensure_current(percorso)

        assert esito["from"] == 1, (
            "un database gia' pieno non e' 'nuovo': trattarlo come vuoto "
            "significherebbe rifargli sopra le tabelle"
        )
        assert "baseline" not in esito["applied"], (
            "la migrazione di partenza non deve essere rieseguita su un "
            "database che ha gia' le sue tabelle"
        )

    def test_i_dati_dell_utente_restano_intatti(self, tmp_path):
        percorso = str(tmp_path / "cache.db")
        _database_come_versione_precedente(percorso)

        db.ensure_current(percorso)

        conn = db.connect(percorso)
        assert conn.execute("SELECT id FROM device").fetchone()[0] == "identificativo-storico"
        assert conn.execute("SELECT account_name FROM connections").fetchone()[0] == "Canale Storico"
        assert conn.execute("SELECT plan FROM license WHERE id = 1").fetchone()[0] == "pro"
        conn.close()

    def test_eseguirlo_due_volte_non_cambia_nulla(self, tmp_path):
        percorso = str(tmp_path / "cache.db")
        _database_come_versione_precedente(percorso)

        db.ensure_current(percorso)
        secondo = db.ensure_current(percorso)

        assert secondo["applied"] == []
        assert secondo["backup"] is None


class TestImpostazioniConcorrenza:
    def test_wal_attivo(self, tmp_path):
        """Senza WAL, leggere dall'interfaccia mentre il thread di
        aggiornamento scrive porta a "database is locked"."""
        percorso = str(tmp_path / "cache.db")
        conn = db.connect(percorso)
        modo = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        assert modo.lower() == "wal"

    def test_busy_timeout_impostato(self, tmp_path):
        percorso = str(tmp_path / "cache.db")
        conn = db.connect(percorso)
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] > 0
        conn.close()


class TestBackup:
    def test_backup_contiene_i_dati(self, tmp_path):
        percorso = str(tmp_path / "cache.db")
        _database_come_versione_precedente(percorso)

        copia = backup_module.create(percorso, label="prova")

        assert os.path.exists(copia)
        conn = sqlite3.connect(copia)
        assert conn.execute("SELECT id FROM device").fetchone()[0] == "identificativo-storico"
        conn.close()

    def test_backup_accanto_ai_dati_non_al_programma(self, tmp_path):
        """La cartella del programma viene sostituita ad ogni aggiornamento:
        un backup li' dentro sparirebbe quando serve."""
        percorso = str(tmp_path / "cache.db")
        _database_come_versione_precedente(percorso)

        copia = backup_module.create(percorso)

        assert os.path.dirname(copia) == os.path.join(str(tmp_path), "backups")

    def test_ne_conserva_solo_tre(self, tmp_path):
        percorso = str(tmp_path / "cache.db")
        _database_come_versione_precedente(percorso)

        for n in range(5):
            backup_module.create(percorso, label=f"n{n}")

        assert len(backup_module.existing(percorso)) == 3

    def test_ripristino_riporta_indietro_i_dati(self, tmp_path):
        percorso = str(tmp_path / "cache.db")
        _database_come_versione_precedente(percorso)
        copia = backup_module.create(percorso)

        conn = db.connect(percorso)
        conn.execute("DELETE FROM connections")
        conn.commit()
        conn.close()

        backup_module.restore(copia, percorso)

        conn = db.connect(percorso)
        assert conn.execute("SELECT account_name FROM connections").fetchone()[0] == "Canale Storico"
        conn.close()

    def test_backup_coerente_con_scritture_ancora_nel_wal(self, tmp_path):
        """La ragione per cui si usa l'API di SQLite invece di copiare il
        file: con WAL le ultime transazioni possono non essere ancora nel
        .db principale, e una copia grezza le perderebbe."""
        percorso = str(tmp_path / "cache.db")
        _database_come_versione_precedente(percorso)

        conn = db.connect(percorso)  # attiva WAL
        conn.execute("INSERT INTO device (id) VALUES ('scritto-adesso')")
        conn.commit()

        copia = backup_module.create(percorso)  # database ancora aperto
        conn.close()

        verifica = sqlite3.connect(copia)
        identificativi = {r[0] for r in verifica.execute("SELECT id FROM device").fetchall()}
        verifica.close()
        assert "scritto-adesso" in identificativi


class TestFallimentoMigrazione:
    def test_un_errore_riporta_il_database_com_era(self, tmp_path, monkeypatch):
        """Se una migrazione futura esplode a meta', l'utente deve
        ritrovarsi il database di prima, non uno a meta' strada."""
        percorso = str(tmp_path / "cache.db")
        _database_come_versione_precedente(percorso)
        db.ensure_current(percorso)
        versione_prima = migrations.LATEST

        def migrazione_rotta(conn):
            conn.execute("CREATE TABLE nuova_tabella (x INTEGER)")
            raise RuntimeError("errore simulato a meta' migrazione")

        monkeypatch.setattr(migrations, "MIGRATIONS",
                            migrations.MIGRATIONS + [(99, "rotta", migrazione_rotta)])

        with pytest.raises(RuntimeError):
            db.ensure_current(percorso)

        conn = db.connect(percorso)
        tabelle = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        versione = db.current_version(conn)
        conn.close()

        assert "nuova_tabella" not in tabelle, "il lavoro a meta' deve sparire"
        assert versione == versione_prima, (
            "la versione deve restare all'ultima migrazione riuscita, non "
            "avanzare a quella fallita"
        )
