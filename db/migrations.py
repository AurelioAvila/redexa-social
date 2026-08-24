"""
Versionamento esplicito dello schema.

Finora ogni modulo creava le sue tabelle da solo con CREATE TABLE IF NOT
EXISTS, piu' qualche ALTER TABLE difensivo sparso. Funziona finche' le
modifiche sono additive e nessuno sbaglia, ma non c'e' modo di sapere a che
punto e' un database, ne' di fare un cambiamento in piu' passi, ne' di
tornare indietro se qualcosa va storto.

Due scelte che vincolano tutto quello che verra' dopo:

  Adozione, non ricostruzione. Un database gia' esistente viene dichiarato
  "versione 1" cosi' com'e'. Non si ricreano tabelle, non si spostano dati,
  non si tocca nulla: l'unica cosa che cambia e' che da adesso c'e' scritto
  a che punto siamo. Un aggiornamento non deve mai essere il momento in cui
  l'utente perde gli account collegati.

  Solo migrazioni additive. Nuove tabelle e nuove colonne, mai rinominare o
  eliminare. Il motivo e' il ritorno alla versione precedente: se
  l'aggiornamento fallisce e si torna indietro, la versione vecchia deve
  poter ancora leggere il database. Il codice legge sempre colonne esplicite
  (mai SELECT *), quindi colonne e tabelle in piu' le ignora senza problemi.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import sqlite3

from .connection import connect

# Tabelle create storicamente dai singoli moduli. Elencarle qui rende lo
# schema di partenza leggibile in un posto solo; restano IF NOT EXISTS
# perche' su un database esistente non devono fare assolutamente nulla.
_BASELINE_TABLES = (
    """CREATE TABLE IF NOT EXISTS snapshots (
        platform TEXT, fetched_at INTEGER, data TEXT)""",
    """CREATE TABLE IF NOT EXISTS insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL DEFAULT 'all',
        generated_at INTEGER, based_on_fetch_at INTEGER, text TEXT)""",
    """CREATE TABLE IF NOT EXISTS kv_cache (
        key TEXT PRIMARY KEY, saved_at INTEGER, data TEXT)""",
    """CREATE TABLE IF NOT EXISTS device (id TEXT PRIMARY KEY)""",
)


def _baseline(conn: sqlite3.Connection) -> None:
    """Versione 1: fotografa lo schema storico.

    Su un database gia' in uso non cambia niente (tutte le istruzioni sono
    IF NOT EXISTS). Su uno nuovo crea le tabelle di base. Le tabelle degli
    altri moduli (users, sessions, connections, license, own_apps,
    update_check) continuano a nascere dove nascevano: verranno accorpate
    qui da una migrazione successiva, quando servira' davvero cambiarle.
    """
    for statement in _BASELINE_TABLES:
        conn.execute(statement)


def _encrypt_secrets(conn: sqlite3.Connection) -> None:
    """Versione 2: cifra i segreti che finora stavano in chiaro.

    Riguarda i token OAuth degli account collegati e i client secret delle
    app registrate dall'utente. Non riguarda la chiave di licenza: vale poco
    per chi ruba il file (il numero di dispositivi e' gia' limitato dal
    servizio) e cifrarla creerebbe un problema vero, cioe' un cliente che
    dopo una reinstallazione di Windows non riesce piu' nemmeno a rileggere
    la chiave che ha pagato.

    Ogni valore viene cifrato e subito ridecifrato per conferma: se il giro
    non torna, si solleva e il runner riporta indietro tutto dal backup.
    Meglio restare in chiaro che restare senza token.

    Fuori da Windows non c'e' DPAPI: la migrazione registra comunque la
    versione senza cifrare nulla, cosi' lo sviluppo su altri sistemi
    funziona e il database resta compatibile.
    """
    import json

    import secrets_store

    if not secrets_store.available():
        return

    def cifra_verificando(valore: str) -> str:
        cifrato = secrets_store.protect(valore)
        if secrets_store.unprotect(cifrato) != valore:
            raise RuntimeError("encryption verification failed")
        return cifrato

    def tabella_esiste(nome: str) -> bool:
        # Le tabelle degli account e delle app proprie nascono ancora nei
        # rispettivi moduli, al primo uso: su un database appena creato non
        # ci sono, e questa migrazione non deve presumere il contrario.
        return bool(conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (nome,)
        ).fetchone())

    # Token degli account collegati: l'intero blocco JSON, che contiene
    # refresh token e client secret insieme.
    if tabella_esiste("connections"):
        for identificativo, blocco in conn.execute(
                "SELECT id, data FROM connections").fetchall():
            if secrets_store.is_protected(blocco):
                continue
            conn.execute("UPDATE connections SET data = ? WHERE id = ?",
                         (cifra_verificando(blocco), identificativo))

    # Credenziali delle app registrate dall'utente.
    if tabella_esiste("own_apps"):
        for piattaforma, segreto in conn.execute(
                "SELECT platform, client_secret FROM own_apps").fetchall():
            if secrets_store.is_protected(segreto):
                continue
            conn.execute("UPDATE own_apps SET client_secret = ? WHERE platform = ?",
                         (cifra_verificando(segreto), piattaforma))


def _connection_auth_state(conn: sqlite3.Connection) -> None:
    """Aggiunge lo stato di autenticazione alle connessioni salvate.

    Prima non esisteva nessun posto dove annotare che il token di un
    account aveva smesso di funzionare: la diagnostica diceva "accesso
    scaduto" ma "Collega account" continuava a mostrarlo attivo, perche'
    leggeva la stessa riga di sempre senza sapere che era diventata
    inutilizzabile.

    Solo aggiunta di colonne: una versione precedente dell'app che legge
    questo database continua a funzionare, perche' le sue query elencano
    le colonne una per una e queste due semplicemente non le chiede.
    """
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='connections'"
    ).fetchone():
        return

    colonne = [r[1] for r in conn.execute("PRAGMA table_info(connections)").fetchall()]
    if "auth_state" not in colonne:
        # '' = mai fallito. L'alternativa (NULL) obbligherebbe ogni lettura
        # a distinguere fra "nessun problema" e "non lo sappiamo".
        conn.execute("ALTER TABLE connections ADD COLUMN auth_state TEXT NOT NULL DEFAULT ''")
    if "auth_checked_at" not in colonne:
        conn.execute("ALTER TABLE connections ADD COLUMN auth_checked_at INTEGER NOT NULL DEFAULT 0")


# (versione, nome leggibile, funzione). Aggiungere in fondo, mai riordinare:
# il numero e' cio' che resta scritto nel database dell'utente.
MIGRATIONS = [
    (1, "baseline", _baseline),
    (2, "encrypt-secrets", _encrypt_secrets),
    (3, "connection-auth-state", _connection_auth_state),
]

LATEST = max(version for version, _, _ in MIGRATIONS)


def _ensure_version_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS schema_version (
               id INTEGER PRIMARY KEY CHECK (id = 1),
               version INTEGER NOT NULL,
               updated_at INTEGER NOT NULL)"""
    )


def _has_user_tables(conn: sqlite3.Connection) -> bool:
    """C'e' gia' roba dell'utente qui dentro?"""
    row = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type = 'table'"
        " AND name NOT LIKE 'sqlite_%' AND name <> 'schema_version'"
    ).fetchone()
    return bool(row and row[0])


def current_version(conn: sqlite3.Connection) -> int:
    """Versione dello schema. 0 = database nuovo, mai migrato."""
    _ensure_version_table(conn)
    row = conn.execute("SELECT version FROM schema_version WHERE id = 1").fetchone()
    if row:
        return int(row[0])
    # Nessuna versione registrata ma tabelle presenti: e' un database creato
    # da una versione precedente dell'app, quando il versionamento non
    # esisteva. Va adottato alla versione 1, non trattato come vuoto.
    return 1 if _has_user_tables(conn) else 0


def _set_version(conn: sqlite3.Connection, version: int) -> None:
    import time

    conn.execute(
        """INSERT INTO schema_version (id, version, updated_at) VALUES (1, ?, ?)
           ON CONFLICT(id) DO UPDATE SET version = excluded.version,
                                         updated_at = excluded.updated_at""",
        (version, int(time.time())),
    )


def ensure_current(db_path: str) -> dict:
    """Porta il database all'ultima versione dello schema.

    Idempotente: se e' gia' aggiornato non fa nulla e non crea backup.
    Se una migrazione fallisce, il database viene riportato allo stato
    precedente e l'errore viene rilanciato: meglio un aggiornamento che non
    parte di un database a meta'.

    Restituisce un riassunto dell'accaduto, senza dati sensibili, adatto a
    essere messo nei log.
    """
    from . import backup as backup_module

    conn = connect(db_path)
    try:
        version = current_version(conn)
        pending = [m for m in MIGRATIONS if m[0] > version]
        if not pending:
            # Registra comunque l'adozione di un database preesistente, cosi'
            # dalla prossima volta la versione e' scritta e non dedotta.
            _set_version(conn, version)
            conn.commit()
            return {"from": version, "to": version, "applied": [], "backup": None}
    finally:
        conn.close()

    # Rete di sicurezza prima di toccare qualunque cosa. Su un database
    # appena creato non c'e' ancora niente da salvare.
    backup_path = None
    if version > 0:
        backup_path = backup_module.create(db_path, label=f"pre-migration-{LATEST}")

    applied = []
    conn = connect(db_path)
    try:
        for number, name, run in pending:
            run(conn)
            _set_version(conn, number)
            conn.commit()
            applied.append(name)
    except Exception:
        conn.close()
        if backup_path:
            backup_module.restore(backup_path, db_path)
        raise
    else:
        # Un UPDATE non cancella i byte precedenti: restano nelle pagine
        # libere del file finche' qualcosa non li riusa. Senza questo, i
        # token appena cifrati resterebbero leggibili in chiaro dentro lo
        # stesso file, e la migrazione sarebbe solo apparente.
        # Non puo' stare in una transazione, quindi va dopo il commit; se
        # fallisce non annulla una migrazione riuscita.
        try:
            conn.execute("VACUUM")
        except sqlite3.DatabaseError:
            pass
        conn.close()

    return {"from": version, "to": LATEST, "applied": applied, "backup": backup_path}
