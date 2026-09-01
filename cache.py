"""
Local storage (SQLite) for the latest snapshot per platform, plus the history
behind the trend charts. No network calls here: local reads and writes only,
so reopening the app costs neither traffic nor money.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import json
import os
import sqlite3
import sys
import time
import db

# cache.db holds the user's account connections (YouTube/Instagram/TikTok):
# it has to survive reinstalls and rebuilds of the exe, so it cannot sit next
# to the executable (that folder is recreated from scratch by every
# build/installer, wiping everything). It goes in a stable user folder outside
# the app's own.
if getattr(sys, "frozen", False):
    DATA_DIR = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "SocialDashboard")
    os.makedirs(DATA_DIR, exist_ok=True)
else:
    DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DATA_DIR, "cache.db")

# One-off migration: if an earlier install kept the db next to the exe, move
# it to the new stable location rather than losing the data.
if getattr(sys, "frozen", False) and not os.path.exists(DB_PATH):
    _legacy_path = os.path.join(os.path.dirname(sys.executable), "cache.db")
    if os.path.exists(_legacy_path):
        import shutil
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
    # soft migration for databases created before the scope column existed
    cols = [r[1] for r in conn.execute("PRAGMA table_info(insights)").fetchall()]
    if "scope" not in cols:
        conn.execute("ALTER TABLE insights ADD COLUMN scope TEXT NOT NULL DEFAULT 'all'")
    return conn


def _leggi_json(grezzo: str, contesto: str) -> dict | None:
    """Reads a row we wrote ourselves, without killing the app if it is spoiled.

    This is data the application writes itself, so normally it is valid. But a
    write interrupted halfway (power cut, disk error) would leave an unreadable
    row, and without this the exception would travel all the way up to the main
    page: the dashboard would stay broken on every open, with no way for the
    user to understand why or do anything about it.

    Skipping the damaged value costs a missing number at worst, and the next
    Refresh puts it back.
    """
    import logging

    try:
        return json.loads(grezzo)
    except (ValueError, TypeError):
        logging.warning("stored data is unreadable (%s); ignoring it until "
                        "the next refresh", contesto)
        return None


def kv_set(key: str, data: dict) -> None:
    """A generic key/value cache on disk (used for instance by certsprint.py
    for npm audit/eslint) - it survives an app restart, unlike a plain
    in-memory dict that empties on every open."""
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
        # rowid as the tie-break: fetched_at has one-second resolution, so
        # two saves close together (two clicks on Refresh) come out level,
        # and without this SQLite returned the OLDER of the two - the numbers
        # appeared to go backwards after a refresh.
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
    """An anonymous, permanent identifier for this installation, used only to
    count how many distinct devices are using the same licence key. It lives
    in a table of its own rather than kv_cache: it has to survive "Clear
    cached data", or every cleanup would make the installation look like a
    new device to the Worker and burn an extra activation for nothing."""
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
    """Deletes a platform's whole stored history - not just the latest
    snapshot. Needed when no connected account is left: without it, Overview
    would go on showing the numbers of the last disconnected account until
    someone pressed Refresh by hand, which reads as real data rather than a
    cache that was never emptied."""
    conn = _conn()
    try:
        conn.execute("DELETE FROM snapshots WHERE platform = ?", (platform,))
        conn.commit()
    finally:
        conn.close()


def clear_all() -> None:
    """Empties everything a refresh can recompute: snapshots, observations, the
    generic cache. It does not touch connections, the licence, or the
    customer's own apps - those are configuration rather than cache, and
    losing them by accident to a "clear cache" button would be a nasty
    surprise."""
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
        if dati is not None:
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
