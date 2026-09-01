"""
One place where database connections are opened.

Before this every module opened its own with a bare sqlite3.connect(), so the
settings that matter were active nowhere:

  journal_mode=WAL   Without it, a simultaneous reader and writer block each
                     other. The app reads from the interface while the refresh
                     thread writes: exactly the case WAL solves. It is a
                     permanent setting, written into the file once.

  busy_timeout       Without it, a write that finds the database busy fails
                     immediately with "database is locked" instead of waiting
                     the half-second it needs.

This module deliberately does not import cache: the path comes from outside.
That keeps it usable by the updater, which runs in a separate process where
the app is not even loaded.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import sqlite3

# How long to wait before declaring the database busy. Five seconds is far
# more than this app's writes need, and far less than a user would call
# "frozen".
BUSY_TIMEOUT_MS = 5000


def connect(db_path: str) -> sqlite3.Connection:
    """A connection with the right settings already applied."""
    conn = sqlite3.connect(db_path, timeout=BUSY_TIMEOUT_MS / 1000)
    conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    # WAL is persistent: once set it stays in the file. Reapplying it on
    # every connection costs nothing and covers databases created earlier. On
    # filesystems that do not support it (some network shares) SQLite refuses
    # the change: there we stay on the classic journal, which works just as
    # well, rather than preventing the app from starting.
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.DatabaseError:
        pass
    return conn
