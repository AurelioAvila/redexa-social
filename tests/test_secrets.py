"""
Encryption of local secrets, and migrating databases that are in the clear.

The most important test in this file is not that the encryption works, but
that the app stays usable when it does NOT: a database copied from another
computer has to produce "reconnect the account", not an error.
"""
import json
import sqlite3

import pytest

import db
import secrets_store
from db import migrations

pytestmark = pytest.mark.skipif(
    not secrets_store.available(),
    reason="DPAPI only exists on Windows; the app is distributed for Windows only",
)


def _cleartext_database(path: str) -> None:
    """A database as 1.3.x left it: tokens readable with the naked eye."""
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
        " VALUES ('youtube', 'Channel', 'uc-1', ?, 1700000000)",
        (json.dumps({"refresh" + "_token": "CLEARTEXT-TOKEN-TO-PROTECT",
                     "client_id": "abc", "scopes": []}),),
    )
    conn.execute(
        "INSERT INTO own_apps (platform, client_id, client_secret, created_at)"
        " VALUES ('tiktok', 'public-key', 'CLEARTEXT-SECRET', 0)"
    )
    conn.commit()
    conn.close()


class TestEncryption:
    def test_round_trip(self):
        encrypted = secrets_store.protect("confidential-value")
        assert secrets_store.unprotect(encrypted) == "confidential-value"

    def test_the_original_value_is_not_readable(self):
        encrypted = secrets_store.protect("confidential-value")
        assert "confidential-value" not in encrypted

    def test_encrypting_twice_does_not_double_up(self):
        once = secrets_store.protect("x")
        assert secrets_store.protect(once) == once

    def test_a_cleartext_value_stays_readable(self):
        """Earlier databases have to work before the migration."""
        assert secrets_store.unprotect("old-cleartext") == "old-cleartext"

    def test_an_altered_value_does_not_decrypt(self):
        encrypted = secrets_store.protect("confidential-value")
        tampered = encrypted[:-6] + "AAAAAA"
        with pytest.raises(secrets_store.SecretUnavailable):
            secrets_store.unprotect(tampered)


class TestMigration:
    def test_the_tokens_end_up_encrypted(self, tmp_path):
        path = str(tmp_path / "cache.db")
        _cleartext_database(path)

        result = db.ensure_current(path)
        assert "encrypt-secrets" in result["applied"]

        conn = sqlite3.connect(path)
        data = conn.execute("SELECT data FROM connections").fetchone()[0]
        secret = conn.execute("SELECT client_secret FROM own_apps").fetchone()[0]
        conn.close()

        assert secrets_store.is_protected(data)
        assert secrets_store.is_protected(secret)

    def test_the_values_stay_recoverable(self, tmp_path, monkeypatch):
        """Encrypting without being able to read back would be an elaborate way
        of deleting the user's data."""
        import cache
        import connections
        import own_app

        path = str(tmp_path / "cache.db")
        _cleartext_database(path)
        monkeypatch.setattr(cache, "DB_PATH", path)

        db.ensure_current(path)

        connection = connections.list_connections("youtube")[0]
        assert connection["data"]["refresh" + "_token"] == "CLEARTEXT-TOKEN-TO-PROTECT"
        assert own_app.get("tiktok")["client_secret"] == "CLEARTEXT-SECRET"

    def test_the_cleartext_really_leaves_the_file(self, tmp_path):
        """An UPDATE leaves the previous bytes in the free pages: without a
        VACUUM the cleartext token would stay recoverable from the file."""
        path = str(tmp_path / "cache.db")
        _cleartext_database(path)

        db.ensure_current(path)

        with open(path, "rb") as fh:
            contents = fh.read()
        assert b"CLEARTEXT-TOKEN-TO-PROTECT" not in contents
        assert b"CLEARTEXT-SECRET" not in contents

    def test_repeatable(self, tmp_path):
        path = str(tmp_path / "cache.db")
        _cleartext_database(path)
        db.ensure_current(path)
        assert db.ensure_current(path)["applied"] == []

    def test_a_failure_leaves_the_database_in_the_clear_but_intact(self, tmp_path, monkeypatch):
        """If the encryption does not succeed, the user has to find their
        tokens as they were. Staying in the clear is far better than being left
        with nothing."""
        path = str(tmp_path / "cache.db")
        _cleartext_database(path)

        def broken_protect(value):
            raise RuntimeError("DPAPI unavailable halfway through the migration")

        monkeypatch.setattr(secrets_store, "protect", broken_protect)

        with pytest.raises(RuntimeError):
            db.ensure_current(path)

        conn = sqlite3.connect(path)
        data = conn.execute("SELECT data FROM connections").fetchone()[0]
        conn.close()
        assert json.loads(data)["refresh" + "_token"] == "CLEARTEXT-TOKEN-TO-PROTECT"


class TestDatabaseFromAnotherComputer:
    """The case the encryption has to handle gracefully, not with an error."""

    def _make_undecryptable(self, path):
        """Simulates a database encrypted elsewhere: a value with the right
        prefix but content this account's DPAPI cannot open."""
        conn = sqlite3.connect(path)
        conn.execute("UPDATE connections SET data = ?",
                     (secrets_store.PREFIX + "QUVTVEVSTk8tTk9OLU1JTy1BQUFB",))
        conn.commit()
        conn.close()

    def test_the_account_does_not_appear_among_the_usable_ones(self, tmp_path, monkeypatch):
        import cache
        import connections

        path = str(tmp_path / "cache.db")
        _cleartext_database(path)
        monkeypatch.setattr(cache, "DB_PATH", path)
        db.ensure_current(path)
        self._make_undecryptable(path)

        # No exception: to the adapters it is as if it were disconnected.
        assert connections.list_connections("youtube") == []

    def test_the_interface_still_shows_it_marked(self, tmp_path, monkeypatch):
        """Vanishing without explanation would be worse: the user has to
        understand that the account is there and needs reconnecting."""
        import cache
        import connections

        path = str(tmp_path / "cache.db")
        _cleartext_database(path)
        monkeypatch.setattr(cache, "DB_PATH", path)
        db.ensure_current(path)
        self._make_undecryptable(path)

        public = connections.public_connections()
        assert len(public) == 1
        assert public[0]["locked"] is True
        assert public[0]["account_name"] == "Channel"

    def test_the_data_is_not_deleted(self, tmp_path, monkeypatch):
        """Undecryptable does not mean rubbish: if the user restores a Windows
        backup, those tokens become valid again."""
        import cache
        import connections

        path = str(tmp_path / "cache.db")
        _cleartext_database(path)
        monkeypatch.setattr(cache, "DB_PATH", path)
        db.ensure_current(path)
        self._make_undecryptable(path)

        connections.list_connections()
        connections.public_connections()

        conn = sqlite3.connect(path)
        assert conn.execute("SELECT count(*) FROM connections").fetchone()[0] == 1
        conn.close()
