"""
The app's version number, and the update check.

Until now the version lived only in the GitHub release tag: it was written
nowhere inside the app, so there was nothing to compare the latest published
one against. APP_VERSION is the single source: update it here on every
release (check_release.py is the reminder).

This module does no more than ask GitHub for the latest tag and compare it
with APP_VERSION - it downloads nothing and installs nothing. Downloading,
verifying the manifest's Ed25519 signature and replacing the running
executable are a separate module, updater/, which app.py calls on its own
(see updater/runner.py for the order of the checks). This file exists because
that machinery still needs to know, before it downloads anything at all,
whether the remote version really is newer than this one.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import json
import time
import urllib.request

import cache
import db

APP_VERSION = "1.9.2"

RELEASES_API = "https://api.github.com/repos/AurelioAvila/social-dashboard/releases/latest"
RELEASES_PAGE = "https://github.com/AurelioAvila/social-dashboard/releases/latest"

# One check a day is enough: this is not something that changes often, and
# every extra request to GitHub is a request that can fail and slow down
# startup for nothing.
CHECK_INTERVAL_SECONDS = 24 * 3600


def _parse(tag: str) -> tuple[int, ...] | None:
    """'v1.2.5' -> (1, 2, 5). None when the tag does not follow the expected
    shape, so a comparison that fails neither blocks nor goes the wrong
    way."""
    raw = tag.lstrip("vV").strip()
    parts = raw.split(".")
    if not (1 <= len(parts) <= 4) or not all(p.isdigit() for p in parts):
        return None
    return tuple(int(p) for p in parts)


def _is_newer(remote: str, local: str) -> bool:
    r, l = _parse(remote), _parse(local)
    if r is None or l is None:
        return False
    return r > l


def _fetch_latest_tag() -> str | None:
    req = urllib.request.Request(RELEASES_API, headers={"Accept": "application/vnd.github+json",
                                                          "User-Agent": "social-dashboard-update-check"})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read())
        return data.get("tag_name")
    except Exception:
        # Offline, rate limited, GitHub down: none of it is the user's
        # fault and none of it belongs in front of them. Try again at the
        # next check.
        return None


def _conn():
    import sqlite3
    conn = db.connect(cache.DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS update_check (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            latest_tag TEXT,
            checked_at INTEGER NOT NULL
        )
    """)
    return conn


def _cached() -> dict | None:
    conn = _conn()
    try:
        row = conn.execute("SELECT latest_tag, checked_at FROM update_check WHERE id = 1").fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return {"latest_tag": row[0], "checked_at": row[1]}


def _save(latest_tag: str | None) -> None:
    conn = _conn()
    try:
        conn.execute(
            """INSERT INTO update_check (id, latest_tag, checked_at) VALUES (1, ?, ?)
               ON CONFLICT(id) DO UPDATE SET latest_tag = excluded.latest_tag, checked_at = excluded.checked_at""",
            (latest_tag, int(time.time())),
        )
        conn.commit()
    finally:
        conn.close()


def status() -> dict:
    """Asks GitHub at most once a day and answers from the cache otherwise. A
    network failure does not touch the cache: the last known good result
    keeps showing, rather than an already-correct update notice vanishing
    just because the connection is gone right now."""
    cached = _cached()
    stale = not cached or (time.time() - cached["checked_at"]) > CHECK_INTERVAL_SECONDS

    latest_tag = cached["latest_tag"] if cached else None
    if stale:
        fresh = _fetch_latest_tag()
        if fresh:
            latest_tag = fresh
            _save(fresh)
        elif not cached:
            _save(None)

    return {
        "current": APP_VERSION,
        "latest": (latest_tag or "").lstrip("vV") or None,
        "update_available": bool(latest_tag and _is_newer(latest_tag, APP_VERSION)),
        "url": RELEASES_PAGE,
    }
