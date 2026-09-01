"""
Safety copies of the user's database.

The database holds things the user cannot rebuild on their own: the connected
accounts (every restore means redoing all the OAuth sign-ins), the licence
they paid for, the credentials of their own apps, the history behind the
numbers. Losing it is not an inconvenience, it is the end of their data.

Two non-negotiable rules:

  1. The backup uses SQLite's backup API, not a copy of the file. With WAL
     active the most recent transactions can be in the -wal file and not yet
     in the main .db: copying only the .db would lose them, silently, at
     exactly the moment a backup matters most.

  2. Backups live next to the DATA, not next to the program. The program's
     folder is replaced wholesale on every update: a backup in there would
     disappear precisely when it is needed.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import os
import sqlite3
import time

from .connection import connect

# How many to keep. Three covers the mistake noticed straight away and the
# one found two updates later, without letting the folder grow forever.
KEEP = 3

PREFIX = "cache-"
SUFFIX = ".db"


def backups_dir(db_path: str) -> str:
    """The subfolder beside the database, created if it is not there."""
    path = os.path.join(os.path.dirname(os.path.abspath(db_path)), "backups")
    os.makedirs(path, exist_ok=True)
    return path


def create(db_path: str, label: str = "") -> str:
    """A consistent copy of the database. Returns the path to the backup.

    label ends up in the filename, so that looking at the folder tells you why
    a given backup exists (for example "pre-migration-2", "pre-update-1.4.0").
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(db_path)

    stamp = time.strftime("%Y%m%d-%H%M%S")
    suffix = f"-{label}" if label else ""
    dest = os.path.join(backups_dir(db_path), f"{PREFIX}{stamp}{suffix}{SUFFIX}")

    source = connect(db_path)
    try:
        target = sqlite3.connect(dest)
        try:
            # SQLite's backup API: consistent even with the database in
            # use and with transactions still sitting in the -wal file.
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()

    prune(db_path)
    return dest


def existing(db_path: str) -> list[str]:
    """The backups that exist, newest first."""
    directory = backups_dir(db_path)
    found = [
        os.path.join(directory, name)
        for name in os.listdir(directory)
        if name.startswith(PREFIX) and name.endswith(SUFFIX)
    ]
    return sorted(found, key=os.path.getmtime, reverse=True)


def prune(db_path: str, keep: int = KEEP) -> list[str]:
    """Deletes the backups beyond the most recent ones. Returns those removed."""
    removed = []
    for path in existing(db_path)[keep:]:
        try:
            os.remove(path)
            removed.append(path)
        except OSError:
            # A backup that cannot be deleted (file held open by an
            # antivirus, permissions) is no reason to fail the operation that
            # created it.
            pass
    return removed


def restore(backup_path: str, db_path: str) -> None:
    """Returns the database to the state of the given backup.

    Here too it goes through SQLite's API rather than overwriting the file: if
    a -wal and a -shm have been left behind, a raw overwrite would leave the
    database in an inconsistent state.
    """
    if not os.path.exists(backup_path):
        raise FileNotFoundError(backup_path)

    source = sqlite3.connect(backup_path)
    try:
        target = connect(db_path)
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()
