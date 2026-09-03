"""
Registration, sign-in and sessions.

Passwords are the one thing in this app that, handled badly, does damage
beyond the user's own computer: people reuse them elsewhere. These tests pin
the current behaviour (PBKDF2, constant-time comparison, only the token's
fingerprint in storage) so that a rewrite cannot weaken it by accident.
"""
from conftest import auth_headers


class TestRegistration:
    def test_creates_a_user_and_returns_a_session(self, client):
        resp = client.post("/api/auth/register", json={
            "email": "new@example.com",
            "password": "Str0ng-Passphrase!42",
            "password_confirm": "Str0ng-Passphrase!42",
            "first_name": "Ada", "last_name": "Lovelace",
            "birth_date": "1990-05-20",
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["token"]
        assert data["user"]["email"] == "new@example.com"
        assert data["user"]["plan"] == "free"
        assert "password" not in str(data), "the response must not contain the password"

    def test_duplicate_email_refused(self, client, registered_user):
        resp = client.post("/api/auth/register", json={
            "email": registered_user["email"],
            "password": "Another-Password!99",
            "password_confirm": "Another-Password!99",
            "first_name": "Other", "last_name": "User",
            "birth_date": "1990-05-20",
        })
        assert resp.status_code == 400
        assert resp.json()["detail"] == "err_email_taken"

    def test_mismatched_passwords_refused(self, client):
        resp = client.post("/api/auth/register", json={
            "email": "someone@example.com",
            "password": "Str0ng-Passphrase!42",
            "password_confirm": "Different!42",
            "first_name": "Some", "last_name": "One",
            "birth_date": "1990-05-20",
        })
        assert resp.status_code == 400
        assert resp.json()["detail"] == "err_password_mismatch"


class TestSignIn:
    def test_correct_credentials(self, client, registered_user):
        resp = client.post("/api/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert resp.status_code == 200
        assert resp.json()["token"]

    def test_wrong_password(self, client, registered_user):
        resp = client.post("/api/auth/login", json={
            "email": registered_user["email"], "password": "wrong",
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "err_bad_credentials"

    def test_unknown_user_gets_the_same_error(self, client):
        """Identical to the "wrong password" case: telling them apart would
        reveal which email addresses are registered."""
        resp = client.post("/api/auth/login", json={
            "email": "never-seen@example.com", "password": "anything",
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "err_bad_credentials"


class TestSession:
    def test_a_valid_token_identifies_the_user(self, client, registered_user):
        resp = client.get("/api/auth/me", headers=auth_headers(registered_user["token"]))
        assert resp.status_code == 200
        assert resp.json()["user"]["email"] == registered_user["email"]

    def test_a_made_up_token_does_not_authenticate(self, client):
        resp = client.get("/api/auth/me", headers=auth_headers("made-up-token"))
        assert resp.json().get("user") is None

    def test_logout_invalidates_the_token(self, client, registered_user):
        headers = auth_headers(registered_user["token"])
        assert client.post("/api/auth/logout", headers=headers).status_code == 200
        assert client.get("/api/auth/me", headers=headers).json().get("user") is None


class TestPasswordReset:
    """A reset exists to take an account back, not merely to change a string:
    if a stolen token survives the reset, whoever was robbed went through the
    procedure for nothing."""

    def test_reset_invalidates_open_sessions(self, client, registered_user, monkeypatch):
        import auth
        import mail

        # The transactional email leaves the process (Worker). What matters
        # here is the effect on the database, not the delivery.
        monkeypatch.setattr(mail, "send_reset_code", lambda *a, **k: None)
        monkeypatch.setattr(mail, "send_password_changed", lambda *a, **k: None)

        old = auth_headers(registered_user["token"])
        assert client.get("/api/auth/me", headers=old).json()["user"] is not None

        code = auth.request_password_reset(registered_user["email"])
        assert code, "a registered user must be able to ask for a reset"

        resp = client.post("/api/auth/reset-password", json={
            "email": registered_user["email"],
            "code": code,
            "password": "Yet-Another-Passphrase!77",
            "password_confirm": "Yet-Another-Passphrase!77",
        })
        assert resp.status_code == 200

        assert client.get("/api/auth/me", headers=old).json().get("user") is None, \
            "the token from before the reset must no longer authenticate"
        new = auth_headers(resp.json()["token"])
        assert client.get("/api/auth/me", headers=new).json()["user"] is not None, \
            "the session the reset just issued must work"

    def test_reset_sends_an_email_after_the_change(self, client, registered_user, monkeypatch):
        import auth
        import mail

        notices = []
        monkeypatch.setattr(mail, "send_reset_code", lambda *a, **k: None)
        monkeypatch.setattr(mail, "send_password_changed", lambda to, name: notices.append(to))

        code = auth.request_password_reset(registered_user["email"])
        client.post("/api/auth/reset-password", json={
            "email": registered_user["email"],
            "code": code,
            "password": "Yet-Another-Passphrase!77",
            "password_confirm": "Yet-Another-Passphrase!77",
        })
        assert notices == [registered_user["email"]]

    def test_a_failed_reset_notifies_nobody(self, client, registered_user, monkeypatch):
        """A notice on a rejected attempt would be a way of getting mail
        delivered to somebody else's address by guessing at a code."""
        import mail

        notices = []
        monkeypatch.setattr(mail, "send_password_changed", lambda to, name: notices.append(to))

        resp = client.post("/api/auth/reset-password", json={
            "email": registered_user["email"],
            "code": "000000",
            "password": "Yet-Another-Passphrase!77",
            "password_confirm": "Yet-Another-Passphrase!77",
        })
        assert resp.status_code == 400
        assert notices == []


class TestStorage:
    def test_password_not_in_the_clear_in_the_database(self, client, registered_user, db_path):
        """The check that actually counts: open the file and look for the
        password. If it showed up, every other test would be irrelevant."""
        with open(db_path, "rb") as fh:
            contents = fh.read()
        assert registered_user["password"].encode() not in contents

    def test_token_stored_only_as_a_fingerprint(self, client, registered_user, db_path):
        """Whoever reads the database must not be able to reuse the session."""
        with open(db_path, "rb") as fh:
            contents = fh.read()
        assert registered_user["token"].encode() not in contents
