"""
Local SQLite storage for each platform's latest snapshot and trend history.
No network calls are made here: only local reads and writes, so reopening
the app generates neither traffic nor cost.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import json
import os
import sqlite3
import shutil
import sys
import time
import db

# cache.db contains the user's account connections (YouTube/Instagram/
# TikTok). It must survive reinstallations and executable rebuilds, so it
# cannot reside beside the executable (that directory is recreated from
# scratch by each build/installer). Keep it in a stable user directory
# outside the application directory.
if getattr(sys, "frozen", False):
    _appdata = os.getenv("APPDATA") or os.path.expanduser("~")
    DATA_DIR = os.path.join(_appdata, "RedexaSocial")
    _legacy_data_dir = os.path.join(_appdata, "SocialDashboard")
    if not os.path.exists(DATA_DIR) and os.path.isdir(_legacy_data_dir):
        try:
            shutil.move(_legacy_data_dir, DATA_DIR)
        except OSError:
            # Never strand an existing account database because Windows or a
            # backup tool temporarily locked the legacy directory.
            DATA_DIR = _legacy_data_dir
    os.makedirs(DATA_DIR, exist_ok=True)
else:
    DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATA_DIR, "cache.db")

# One-time migration: if a previous installation stored the database beside
# the executable, move it to the new stable location to preserve the data.
if getattr(sys, "frozen", False) and not os.path.exists(DB_PATH):
    _legacy_path = os.path.join(os.path.dirname(sys.executable), "cache.db")
    if os.path.exists(_legacy_path):
        shutil.move(_legacy_path, DB_PATH)


def _conn():
    conn = db.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            platform TEXT,
            fetched_at INTEGER,
            data TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scope TEXT NOT NULL DEFAULT 'all',
            generated_at INTEGER,
            based_on_fetch_at INTEGER,
            text TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kv_cache (
            key TEXT PRIMARY KEY,
            saved_at INTEGER,
            data TEXT
        )
    """)
    # Compatible migration for databases created before the scope column.
    cols = [r[1] for r in conn.execute("PRAGMA table_info(insights)").fetchall()]
    if "scope" not in cols:
        conn.execute("ALTER TABLE insights ADD COLUMN scope TEXT NOT NULL DEFAULT 'all'")
    return conn


def _leggi_json(grezzo: str, contesto: str) -> dict | None:
    """Read an application-managed row without crashing if it is corrupted.

    The application writes this data, so it is normally valid. However, an
    interrupted write caused by a power loss or disk error could leave an
    unreadable row. Without this safeguard, the exception would reach the
    main page and break the dashboard on every launch without giving the
    user a clear cause or remedy.

    Ignoring the damaged data causes at most one missing value, which the
    next refresh restores.
    """
    import logging

    try:
        return json.loads(grezzo)
    except (ValueError, TypeError):
        logging.warning("stored data is unreadable (%s); ignoring it until "
                        "the next refresh", contesto)
        return None


def kv_set(key: str, data: dict) -> None:
    """Generic on-disk key/value cache (used, for example, by certsprint.py
    for npm audit/eslint). Unlike an in-memory dictionary, it survives
    application restarts."""
    conn = _conn()
    try:
        conn.execute("INSERT OR REPLACE INTO kv_cache (key, saved_at, data) VALUES (?, ?, ?)",
                     (key, int(time.time()), json.dumps(data)))
        conn.commit()
    finally:
        conn.close()


def kv_get(key: str, max_age_seconds: int) -> dict | None:
    conn = _conn()
    try:
        row = conn.execute("SELECT saved_at, data FROM kv_cache WHERE key = ?", (key,)).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    saved_at, data = row
    if time.time() - saved_at > max_age_seconds:
        return None
    return _leggi_json(data, contesto=f"kv_cache[{key}]")


def save_snapshot(platform: str, data: dict) -> None:
    conn = _conn()
    try:
        conn.execute("INSERT INTO snapshots (platform, fetched_at, data) VALUES (?, ?, ?)",
                     (platform, int(time.time()), json.dumps(data)))
        conn.commit()
    finally:
        conn.close()


def latest_snapshot(platform: str) -> dict | None:
    conn = _conn()
    try:
        # Use rowid as a tiebreaker because fetched_at has one-second
        # resolution. Two rapid saves can share a timestamp; without rowid,
        # SQLite returned the OLDER row and values appeared to regress after
        # a refresh.
        row = conn.execute(
            "SELECT fetched_at, data FROM snapshots WHERE platform = ?"
            " ORDER BY fetched_at DESC, rowid DESC LIMIT 1",
            (platform,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    dati = _leggi_json(row[1], contesto=f"snapshot {platform}")
    if dati is None:
        return None
    return {"fetched_at": row[0], **dati}


def device_id() -> str:
    """Permanent anonymous identifier for this installation.

    It is used only to count distinct devices sharing a license key. It has
    its own table instead of kv_cache so it survives "Clear cached data";
    otherwise each cleanup would make the Worker treat the installation as
    a new device and needlessly consume another activation.
    """
    import secrets

    conn = _conn()
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS device (id TEXT PRIMARY KEY)")
        row = conn.execute("SELECT id FROM device LIMIT 1").fetchone()
        if row:
            return row[0]
        new_id = secrets.token_hex(16)
        conn.execute("INSERT INTO device (id) VALUES (?)", (new_id,))
        conn.commit()
        return new_id
    finally:
        conn.close()


def clear_snapshot(platform: str) -> None:
    """Delete all stored history for a platform, not only its latest snapshot.

    This is needed when no linked accounts remain. Otherwise, Overview would
    keep showing data from the last disconnected account until the user
    manually refreshes, making stale cache entries appear current.
    """
    conn = _conn()
    try:
        conn.execute("DELETE FROM snapshots WHERE platform = ?", (platform,))
        conn.commit()
    finally:
        conn.close()


def clear_all() -> None:
    """Clear everything that a refresh can rebuild: snapshots, insights, and
    the generic cache. Preserve connections, licenses, and customer-owned
    apps because they are configuration, not cache, and must not be removed
    accidentally by a cache-clearing action.
    """
    conn = _conn()
    try:
        conn.execute("DELETE FROM snapshots")
        conn.execute("DELETE FROM insights")
        conn.execute("DELETE FROM kv_cache")
        conn.commit()
    finally:
        conn.close()


def history(platform: str, limit: int = 30) -> list[dict]:
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT fetched_at, data FROM snapshots WHERE platform = ?"
            " ORDER BY fetched_at DESC, rowid DESC LIMIT ?",
            (platform, limit),
        ).fetchall()
    finally:
        conn.close()
    storico = []
    for r in reversed(rows):
        dati = _leggi_json(r[1], contesto=f"storico {platform}")
        if dati is None:
            continue
        # A refresh that failed is stored as a snapshot like any other:
        # {"platform": ..., "ok": False, "error": ...}, with no channels in
        # it at all. The trend extractors read the missing list as an empty
        # one and record 0 — indistinguishable from a real reading of zero,
        # so turning the Wi-Fi off and pressing Refresh put a permanent
        # -100% drop alert into the Pro charts. History is append-only, so
        # nothing ever took it back out.
        #
        # Filtered here rather than at the extractors: every reader of the
        # series wants data points, and a failure is not one. The row stays
        # in the table, where latest_snapshot and the error text still see
        # it.
        if dati.get("ok") is False:
            continue
        storico.append({"fetched_at": r[0], **dati})
    return storico


def save_insight(text: str, based_on_fetch_at: int, scope: str = "all") -> None:
    conn = _conn()
    try:
        conn.execute("INSERT INTO insights (scope, generated_at, based_on_fetch_at, text) VALUES (?, ?, ?, ?)",
                     (scope, int(time.time()), based_on_fetch_at, text))
        conn.commit()
    finally:
        conn.close()


def latest_insight(scope: str = "all") -> dict | None:
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT generated_at, based_on_fetch_at, text FROM insights WHERE scope = ?"
            " ORDER BY generated_at DESC, rowid DESC LIMIT 1",
            (scope,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return {"generated_at": row[0], "based_on_fetch_at": row[1], "text": row[2]}
