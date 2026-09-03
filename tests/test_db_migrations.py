"""
Schema versioning, with attention on the case that matters: the database of a
user upgrading from an earlier version.

If these tests pass but the adoption is wrong, the damage is invisible in
development (where the database is empty) and shows up in full on users'
computers, which lose connected accounts and licence.
"""
import os
import sqlite3

import pytest

import db
from db import backup as backup_module
from db import migrations


def _database_as_an_earlier_version(path: str) -> None:
    """Rebuilds a database as 1.3.x left it: tables created by the individual
    modules, no trace of schema_version, and real data inside."""
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
    conn.execute("INSERT INTO device (id) VALUES ('historic-identifier')")
    conn.execute(
        "INSERT INTO connections (platform, account_name, account_id, data, created_at)"
        " VALUES ('youtube', 'Historic Channel', 'uc-123', '{}', 1700000000)"
    )
    conn.execute(
        "INSERT INTO license (id, key, plan, email, last_ok, last_check, revoked)"
        " VALUES (1, 'SD-PRO-OLD-KEY', 'pro', 'user@example.com', 1, 1, 0)"
    )
    conn.commit()
    conn.close()


class TestNewDatabase:
    def test_starts_from_zero_and_reaches_the_latest_version(self, tmp_path):
        path = str(tmp_path / "cache.db")
        result = db.ensure_current(path)

        assert result["from"] == 0
        assert result["to"] == migrations.LATEST
        assert result["backup"] is None, "an empty database has nothing to save"

        conn = db.connect(path)
        assert db.current_version(conn) == migrations.LATEST
        conn.close()

    def test_creates_the_base_tables(self, tmp_path):
        path = str(tmp_path / "cache.db")
        db.ensure_current(path)

        conn = db.connect(path)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.close()
        assert {"snapshots", "insights", "kv_cache", "device"} <= tables


class TestAdoptingAnExistingDatabase:
    """The real case: a user upgrading."""

    def test_a_pre_existing_database_is_adopted_as_version_one(self, tmp_path):
        path = str(tmp_path / "cache.db")
        _database_as_an_earlier_version(path)

        result = db.ensure_current(path)

        assert result["from"] == 1, (
            "a database that is already full is not 'new': treating it as "
            "empty would mean recreating its tables over the top"
        )
        assert "baseline" not in result["applied"], (
            "the starting migration must not be re-run on a database that "
            "already has its tables"
        )

    def test_the_users_data_stays_intact(self, tmp_path):
        path = str(tmp_path / "cache.db")
        _database_as_an_earlier_version(path)

        db.ensure_current(path)

        conn = db.connect(path)
        assert conn.execute("SELECT id FROM device").fetchone()[0] == "historic-identifier"
        assert conn.execute("SELECT account_name FROM connections").fetchone()[0] == "Historic Channel"
        assert conn.execute("SELECT plan FROM license WHERE id = 1").fetchone()[0] == "pro"
        conn.close()

    def test_running_it_twice_changes_nothing(self, tmp_path):
        path = str(tmp_path / "cache.db")
        _database_as_an_earlier_version(path)

        db.ensure_current(path)
        second = db.ensure_current(path)

        assert second["applied"] == []
        assert second["backup"] is None


class TestConcurrencySettings:
    def test_wal_is_on(self, tmp_path):
        """Without WAL, reading from the interface while the refresh thread
        writes leads to "database is locked"."""
        path = str(tmp_path / "cache.db")
        conn = db.connect(path)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        assert mode.lower() == "wal"

    def test_busy_timeout_is_set(self, tmp_path):
        path = str(tmp_path / "cache.db")
        conn = db.connect(path)
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] > 0
        conn.close()


class TestBackup:
    def test_the_backup_contains_the_data(self, tmp_path):
        path = str(tmp_path / "cache.db")
        _database_as_an_earlier_version(path)

        copy = backup_module.create(path, label="probe")

        assert os.path.exists(copy)
        conn = sqlite3.connect(copy)
        assert conn.execute("SELECT id FROM device").fetchone()[0] == "historic-identifier"
        conn.close()

    def test_the_backup_sits_beside_the_data_not_the_program(self, tmp_path):
        """The program's folder is replaced on every update: a backup inside it
        would disappear exactly when it is needed."""
        path = str(tmp_path / "cache.db")
        _database_as_an_earlier_version(path)

        copy = backup_module.create(path)

        assert os.path.dirname(copy) == os.path.join(str(tmp_path), "backups")

    def test_it_keeps_only_three(self, tmp_path):
        path = str(tmp_path / "cache.db")
        _database_as_an_earlier_version(path)

        for n in range(5):
            backup_module.create(path, label=f"n{n}")

        assert len(backup_module.existing(path)) == 3

    def test_restoring_brings_the_data_back(self, tmp_path):
        path = str(tmp_path / "cache.db")
        _database_as_an_earlier_version(path)
        copy = backup_module.create(path)

        conn = db.connect(path)
        conn.execute("DELETE FROM connections")
        conn.commit()
        conn.close()

        backup_module.restore(copy, path)

        conn = db.connect(path)
        assert conn.execute("SELECT account_name FROM connections").fetchone()[0] == "Historic Channel"
        conn.close()

    def test_backup_consistent_with_writes_still_in_the_wal(self, tmp_path):
        """The reason SQLite's own API is used instead of copying the file:
        with WAL the latest transactions may not be in the main .db yet, and a
        raw copy would lose them."""
        path = str(tmp_path / "cache.db")
        _database_as_an_earlier_version(path)

        conn = db.connect(path)  # turns WAL on
        conn.execute("INSERT INTO device (id) VALUES ('written-just-now')")
        conn.commit()

        copy = backup_module.create(path)  # database still open
        conn.close()

        check = sqlite3.connect(copy)
        identifiers = {r[0] for r in check.execute("SELECT id FROM device").fetchall()}
        check.close()
        assert "written-just-now" in identifiers


class TestMigrationFailure:
    def test_an_error_puts_the_database_back_as_it_was(self, tmp_path, monkeypatch):
        """If a future migration blows up halfway, the user has to find the
        database they had before, not one stranded in between."""
        path = str(tmp_path / "cache.db")
        _database_as_an_earlier_version(path)
        db.ensure_current(path)
        version_before = migrations.LATEST

        def broken_migration(conn):
            conn.execute("CREATE TABLE new_table (x INTEGER)")
            raise RuntimeError("simulated error halfway through the migration")

        monkeypatch.setattr(migrations, "MIGRATIONS",
                            migrations.MIGRATIONS + [(99, "broken", broken_migration)])

        with pytest.raises(RuntimeError):
            db.ensure_current(path)

        conn = db.connect(path)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        version = db.current_version(conn)
        conn.close()

        assert "new_table" not in tables, "the half-done work has to disappear"
        assert version == version_before, (
            "the version has to stay at the last successful migration, not "
            "advance to the failed one"
        )
