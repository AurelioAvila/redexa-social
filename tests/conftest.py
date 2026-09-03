"""
Shared fixtures.

Two guarantees every test needs, or none of them are trustworthy:

  1. The test database is never the user's. Every module reads cache.DB_PATH
     at call time (not at import), so rewriting it is enough to divert the
     whole app onto a temporary file.

  2. No real network calls. Starting the app spawns a thread that queries the
     licence service, and /api/version queries GitHub: in a test those become
     slowness, results that change from one day to the next, and traffic
     aimed at real services. Here the network is barred, and an attempt fails
     the test instead of going unnoticed.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Any call heading outside fails the test rather than actually going
    out."""

    def blocked(*args, **kwargs):
        raise AssertionError(
            "The test attempted a real network call. "
            "Replace the function with a fake."
        )

    for target in (
        "requests.get",
        "requests.post",
        "requests.put",
        "requests.delete",
        "requests.request",
        "urllib.request.urlopen",
    ):
        monkeypatch.setattr(target, blocked, raising=False)


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """The login/registration limiter keeps its state in a module-level dict
    shared by every test in the same pytest process: without clearing it, a
    test that registers several users in a row trips the 429 meant for a real
    client getting its password wrong ten times, not for a suite creating ten
    different ones in a second."""
    import rate_limit

    rate_limit._attempts.clear()
    yield
    rate_limit._attempts.clear()


@pytest.fixture()
def db_path(monkeypatch, tmp_path):
    """Diverts the whole app onto a throwaway database."""
    import cache

    path = str(tmp_path / "cache.db")
    monkeypatch.setattr(cache, "DB_PATH", path)
    return path


@pytest.fixture()
def client(db_path, monkeypatch):
    """An HTTP client against the real app.

    base_url is 127.0.0.1 deliberately: the anti-DNS-rebinding guard rejects
    Hosts that are not local, and TestClient's default ("testserver") would be
    refused with a 400. See test_security_guards for the explicit check of
    that behaviour.
    """
    from fastapi.testclient import TestClient

    import app as backend
    import licensing

    # The startup event rechecks the licence over the network: not here.
    monkeypatch.setattr(licensing, "refresh_if_due", lambda: None, raising=False)

    return TestClient(backend.app, base_url="http://127.0.0.1:8787")


@pytest.fixture()
def registered_user(client):
    """An already-registered user, with their session token."""
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "tester@example.com",
            "password": "Str0ng-Passphrase!42",
            "password_confirm": "Str0ng-Passphrase!42",
            "first_name": "Test",
            "last_name": "User",
            "birth_date": "1990-05-20",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return {"token": data["token"], "user": data["user"], "email": "tester@example.com",
            "password": "Str0ng-Passphrase!42"}


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
