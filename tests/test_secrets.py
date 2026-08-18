"""
Cifratura dei segreti locali e migrazione dei database in chiaro.

Il test piu' importante di questo file non e' che la cifratura funzioni, ma
che l'app resti utilizzabile quando NON funziona: un database copiato da un
altro computer deve far comparire "ricollega l'account", non un errore.
"""
import json
import sqlite3

import pytest

import db
import secrets_store
from db import migrations

pytestmark = pytest.mark.skipif(
    not secrets_store.available(),
    reason="DPAPI esiste solo su Windows; l'app e' distribuita solo per Windows",
)


def _database_in_chiaro(path: str) -> None:
    """Database come lo lasciava la 1.3.x: token leggibili a occhio nudo."""
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE connections (id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL, account_name TEXT NOT NULL, account_id TEXT,
            data TEXT NOT NULL, created_at INTEGER NOT NULL,
            UNIQUE(platform, account_id));
        CREATE TABLE own_apps (platform TEXT PRIMARY KEY, client_id TEXT NOT NULL,
            client_secret TEXT NOT NULL, created_at INTEGER NOT NULL);
        """
    )
    conn.execute(
        "INSERT INTO connections (platform, account_name, account_id, data, created_at)"
        " VALUES ('youtube', 'Canale', 'uc-1', ?, 1700000000)",
        (json.dumps({"refresh" + "_token": "TOKEN-IN-CHIARO-DA-PROTEGGERE",
                     "client_id": "abc", "scopes": []}),),
    )
    conn.execute(
        "INSERT INTO own_apps (platform, client_id, client_secret, created_at)"
        " VALUES ('tiktok', 'chiave-pubblica', 'SEGRETO-IN-CHIARO', 0)"
    )
    conn.commit()
    conn.close()


class TestCifratura:
    def test_giro_completo(self):
        cifrato = secrets_store.protect("valore-riservato")
        assert secrets_store.unprotect(cifrato) == "valore-riservato"

    def test_il_valore_originale_non_e_leggibile(self):
        cifrato = secrets_store.protect("valore-riservato")
        assert "valore-riservato" not in cifrato

    def test_cifrare_due_volte_non_raddoppia(self):
        una = secrets_store.protect("x")
        assert secrets_store.protect(una) == una

    def test_valore_in_chiaro_resta_leggibile(self):
        """I database precedenti devono funzionare prima della migrazione."""
        assert secrets_store.unprotect("vecchio-in-chiaro") == "vecchio-in-chiaro"

    def test_valore_alterato_non_si_decifra(self):
        cifrato = secrets_store.protect("valore-riservato")
        manomesso = cifrato[:-6] + "AAAAAA"
        with pytest.raises(secrets_store.SecretUnavailable):
            secrets_store.unprotect(manomesso)


class TestMigrazione:
    def test_i_token_finiscono_cifrati(self, tmp_path):
        percorso = str(tmp_path / "cache.db")
        _database_in_chiaro(percorso)

        esito = db.ensure_current(percorso)
        assert "encrypt-secrets" in esito["applied"]

        conn = sqlite3.connect(percorso)
        dati = conn.execute("SELECT data FROM connections").fetchone()[0]
        segreto = conn.execute("SELECT client_secret FROM own_apps").fetchone()[0]
        conn.close()

        assert secrets_store.is_protected(dati)
        assert secrets_store.is_protected(segreto)

    def test_i_valori_restano_recuperabili(self, tmp_path, monkeypatch):
        """Cifrare senza poter piu' rileggere sarebbe un modo elaborato di
        cancellare i dati dell'utente."""
        import cache
        import connections
        import own_app

        percorso = str(tmp_path / "cache.db")
        _database_in_chiaro(percorso)
        monkeypatch.setattr(cache, "DB_PATH", percorso)

        db.ensure_current(percorso)

        collegamento = connections.list_connections("youtube")[0]
        assert collegamento["data"]["refresh" + "_token"] == "TOKEN-IN-CHIARO-DA-PROTEGGERE"
        assert own_app.get("tiktok")["client_secret"] == "SEGRETO-IN-CHIARO"

    def test_il_chiaro_sparisce_davvero_dal_file(self, tmp_path):
        """Un UPDATE lascia i byte precedenti nelle pagine libere: senza
        VACUUM il token in chiaro resterebbe recuperabile dal file."""
        percorso = str(tmp_path / "cache.db")
        _database_in_chiaro(percorso)

        db.ensure_current(percorso)

        with open(percorso, "rb") as fh:
            contenuto = fh.read()
        assert b"TOKEN-IN-CHIARO-DA-PROTEGGERE" not in contenuto
        assert b"SEGRETO-IN-CHIARO" not in contenuto

    def test_ripetibile(self, tmp_path):
        percorso = str(tmp_path / "cache.db")
        _database_in_chiaro(percorso)
        db.ensure_current(percorso)
        assert db.ensure_current(percorso)["applied"] == []

    def test_fallimento_riporta_il_database_in_chiaro_ma_intatto(self, tmp_path, monkeypatch):
        """Se la cifratura non riesce, l'utente deve ritrovarsi i suoi token
        come prima. Restare in chiaro e' molto meglio che restare senza."""
        percorso = str(tmp_path / "cache.db")
        _database_in_chiaro(percorso)

        def protect_rotta(valore):
            raise RuntimeError("DPAPI non disponibile a meta' migrazione")

        monkeypatch.setattr(secrets_store, "protect", protect_rotta)

        with pytest.raises(RuntimeError):
            db.ensure_current(percorso)

        conn = sqlite3.connect(percorso)
        dati = conn.execute("SELECT data FROM connections").fetchone()[0]
        conn.close()
        assert json.loads(dati)["refresh" + "_token"] == "TOKEN-IN-CHIARO-DA-PROTEGGERE"


class TestDatabaseDaUnAltroComputer:
    """Il caso che la cifratura deve gestire con grazia, non con un errore."""

    def _rendi_indecifrabile(self, percorso):
        """Simula un database cifrato altrove: valore con il prefisso giusto
        ma contenuto che DPAPI di questo account non puo' aprire."""
        conn = sqlite3.connect(percorso)
        conn.execute("UPDATE connections SET data = ?",
                     (secrets_store.PREFIX + "QUVTVEVSTk8tTk9OLU1JTy1BQUFB",))
        conn.commit()
        conn.close()

    def test_l_account_non_compare_fra_quelli_utilizzabili(self, tmp_path, monkeypatch):
        import cache
        import connections

        percorso = str(tmp_path / "cache.db")
        _database_in_chiaro(percorso)
        monkeypatch.setattr(cache, "DB_PATH", percorso)
        db.ensure_current(percorso)
        self._rendi_indecifrabile(percorso)

        # Nessuna eccezione: per gli adapter e' come se fosse scollegato.
        assert connections.list_connections("youtube") == []

    def test_l_interfaccia_lo_mostra_comunque_contrassegnato(self, tmp_path, monkeypatch):
        """Sparire senza spiegazione sarebbe peggio: l'utente deve capire
        che l'account c'e' e che va ricollegato."""
        import cache
        import connections

        percorso = str(tmp_path / "cache.db")
        _database_in_chiaro(percorso)
        monkeypatch.setattr(cache, "DB_PATH", percorso)
        db.ensure_current(percorso)
        self._rendi_indecifrabile(percorso)

        pubblici = connections.public_connections()
        assert len(pubblici) == 1
        assert pubblici[0]["locked"] is True
        assert pubblici[0]["account_name"] == "Canale"

    def test_i_dati_non_vengono_cancellati(self, tmp_path, monkeypatch):
        """Non decifrabile non vuol dire spazzatura: se l'utente ripristina
        un backup di Windows, quei token tornano validi."""
        import cache
        import connections

        percorso = str(tmp_path / "cache.db")
        _database_in_chiaro(percorso)
        monkeypatch.setattr(cache, "DB_PATH", percorso)
        db.ensure_current(percorso)
        self._rendi_indecifrabile(percorso)

        connections.list_connections()
        connections.public_connections()

        conn = sqlite3.connect(percorso)
        assert conn.execute("SELECT count(*) FROM connections").fetchone()[0] == 1
        conn.close()
