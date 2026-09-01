"""
Explicit schema versioning.

Until now every module created its own tables with CREATE TABLE IF NOT
EXISTS, plus a scattering of defensive ALTER TABLEs. That works while the
changes are additive and nobody makes a mistake, but there is no way to know
where a database stands, no way to make a change in several steps, and no way
back if something goes wrong.

Two decisions that constrain everything after them:

  Adoption, not reconstruction. An existing database is declared "version 1"
  exactly as it is. No tables are recreated, no data is moved, nothing is
  touched: the only thing that changes is that where we stand is now written
  down. An update must never be the moment a user loses their connected
  accounts.

  Additive migrations only. New tables and new columns, never a rename and
  never a drop. The reason is the way back: if an update fails and is rolled
  back, the older version has to still be able to read the database. The code
  always reads explicit columns (never SELECT *), so extra columns and tables
  are ignored without trouble.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import sqlite3

from .connection import connect

# Tables historically created by the individual modules. Listing them here
# makes the starting schema readable in one place; they stay IF NOT EXISTS
# because on an existing database they must do absolutely nothing.
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
    """Version 1: photographs the historical schema.

    On a database already in use it changes nothing (every statement is IF NOT
    EXISTS). On a new one it creates the base tables. The other modules'
    tables (users, sessions, connections, license, own_apps, update_check)
    go on being created where they always were: a later migration will pull
    them in here, when there is a real need to change them.
    """
    for statement in _BASELINE_TABLES:
        conn.execute(statement)


def _encrypt_secrets(conn: sqlite3.Connection) -> None:
    """Version 2: encrypts the secrets that were in the clear until now.

    It covers the OAuth tokens of the connected accounts and the client
    secrets of the apps the user registered. It does not cover the licence
    key: that is worth little to whoever steals the file (the service already
    caps the number of devices) and encrypting it would create a real problem
    — a customer who, after reinstalling Windows, can no longer even read back
    the key they paid for.

    Every value is encrypted and immediately decrypted again as a check: if
    the round trip does not hold, it raises and the runner restores everything
    from the backup. Better to stay in the clear than to end up with no
    tokens.

    Off Windows there is no DPAPI: the migration records the version anyway
    without encrypting anything, so development on other systems works and the
    database stays compatible.
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
        # The accounts and own-apps tables are still created by their own
        # modules on first use: on a freshly created database they are not
        # there, and this migration must not assume otherwise.
        return bool(conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?", (nome,)
        ).fetchone())

    # Tokens of the connected accounts: the whole JSON block, which holds
    # the refresh token and the client secret together.
    if tabella_esiste("connections"):
        for identificativo, blocco in conn.execute(
                "SELECT id, data FROM connections").fetchall():
            if secrets_store.is_protected(blocco):
                continue
            conn.execute("UPDATE connections SET data = ? WHERE id = ?",
                         (cifra_verificando(blocco), identificativo))

    # Credentials of the apps the user registered.
    if tabella_esiste("own_apps"):
        for piattaforma, segreto in conn.execute(
                "SELECT platform, client_secret FROM own_apps").fetchall():
            if secrets_store.is_protected(segreto):
                continue
            conn.execute("UPDATE own_apps SET client_secret = ? WHERE platform = ?",
                         (cifra_verificando(segreto), piattaforma))


def _connection_auth_state(conn: sqlite3.Connection) -> None:
    """Adds the authorization state to the stored connections.

    Before this there was nowhere to record that an account's token had
    stopped working: diagnostics said "authorization expired" while "Connect
    account" went on showing it as active, because it read the same row it
    always had without knowing it had become unusable.

    Columns are only added: an earlier version of the app reading this
    database keeps working, because its queries list columns one by one and
    simply never ask for these two.
    """
    if not conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='connections'"
    ).fetchone():
        return

    colonne = [r[1] for r in conn.execute("PRAGMA table_info(connections)").fetchall()]
    if "auth_state" not in colonne:
        # '' = never failed. The alternative (NULL) would force every read
        # to tell "no problem" apart from "we do not know".
        conn.execute("ALTER TABLE connections ADD COLUMN auth_state TEXT NOT NULL DEFAULT ''")
    if "auth_checked_at" not in colonne:
        conn.execute("ALTER TABLE connections ADD COLUMN auth_checked_at INTEGER NOT NULL DEFAULT 0")


# (version, readable name, function). Append at the end, never reorder: the
# number is what stays written in the user's database.
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
    """Is there already anything of the user's in here?"""
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
    # No version recorded but tables present: this is a database created by
    # an earlier version of the app, before versioning existed. It should be
    # adopted at version 1, not treated as empty.
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
    """Brings the database up to the latest schema version.

    Idempotent: already up to date, it does nothing and takes no backup. If a
    migration fails, the database is returned to its previous state and the
    error is re-raised: an update that does not start beats a database left
    half-way.

    Returns a summary of what happened, free of sensitive values and fit for
    the log.
    """
    from . import backup as backup_module

    conn = connect(db_path)
    try:
        version = current_version(conn)
        pending = [m for m in MIGRATIONS if m[0] > version]
        if not pending:
            # Record the adoption of a pre-existing database anyway, so that
            # from next time the version is written rather than inferred.
            _set_version(conn, version)
            conn.commit()
            return {"from": version, "to": version, "applied": [], "backup": None}
    finally:
        conn.close()

    # A safety net before anything is touched. On a freshly created database
    # there is nothing to save yet.
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
        # An UPDATE does not erase the previous bytes: they stay in the
        # file's free pages until something reuses them. Without this, the
        # tokens that were just encrypted would remain readable in the clear
        # inside the same file, and the migration would only look like one.
        # It cannot run inside a transaction, so it goes after the commit; if
        # it fails it does not undo a migration that succeeded.
        try:
            conn.execute("VACUUM")
        except sqlite3.DatabaseError:
            pass
        conn.close()

    return {"from": version, "to": LATEST, "applied": applied, "backup": backup_path}
