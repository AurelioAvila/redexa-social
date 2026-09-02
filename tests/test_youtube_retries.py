"""YouTube must not retry a credential Google has already rejected.

The fetch loop makes up to three attempts with a growing backoff, which is
right for a momentary hiccup on Google's token endpoint — that is what it was
written for. It retried *everything*, though, including `invalid_grant` from
a revoked token: 7 seconds of dead waiting per channel, and three requests
carrying a credential the platform had already refused, multiplied by
channels and by every refresh.

`platforms/_http.py` exists to stop exactly that, and says so in its own
docstring: hammering an endpoint with a rejected credential is how a
developer key gets suspended. YouTube is the one adapter never moved onto
it, so the same policy is applied inside its loop, reusing the predicate the
next line already trusts to decide whether to send the user through a
sign-in.
"""
import pytest

import connections
from platforms import youtube


@pytest.fixture()
def one_channel(monkeypatch):
    monkeypatch.setattr(youtube, "_sources", lambda: [
        {"name": "Canale", "kind": "oauth", "connection_id": 1},
    ])
    monkeypatch.setattr(connections, "record_fetch_outcome", lambda cid, exc: None)
    # No real waiting, and the test can prove the backoff was skipped too.
    slept = []
    monkeypatch.setattr(youtube.time, "sleep", slept.append)
    return slept


def _raising(monkeypatch, exc):
    calls = []

    def fetch(source):
        calls.append(source)
        raise exc

    monkeypatch.setattr(youtube, "_fetch_channel", fetch)
    return calls


def test_a_revoked_token_is_tried_once(one_channel, monkeypatch):
    calls = _raising(monkeypatch, RuntimeError("invalid_grant: Token has been expired or revoked."))

    out = youtube.fetch_stats()

    assert len(calls) == 1, f"a rejected credential was sent {len(calls)} times"
    assert one_channel == [], "and nothing waited for it"
    assert out["channels"][0]["ok"] is False
    assert out["channels"][0]["needs_reauth"] is True


def test_a_passing_hiccup_still_gets_its_three_attempts(one_channel, monkeypatch):
    calls = _raising(monkeypatch, RuntimeError("backendError: transient failure"))

    youtube.fetch_stats()

    assert len(calls) == 3, "the retry this loop exists for has to survive"
    assert one_channel == [2, 5], "with the documented backoff"


def test_a_channel_that_answers_on_the_second_try_succeeds(one_channel, monkeypatch):
    calls = []

    def flaky(source):
        calls.append(source)
        if len(calls) == 1:
            raise RuntimeError("backendError: transient failure")
        return {"name": "Canale", "ok": True, "subscribers": 10, "source": "oauth"}

    monkeypatch.setattr(youtube, "_fetch_channel", flaky)

    out = youtube.fetch_stats()

    assert len(calls) == 2
    assert out["channels"][0]["ok"] is True


def test_the_predicate_is_the_one_the_rest_of_the_app_uses(one_channel, monkeypatch):
    """Not a second opinion written for this loop: if is_auth_failure ever
    stops recognising something, the retry policy and the "reconnect this
    account" prompt have to be wrong together rather than separately."""
    seen = []
    real = connections.is_auth_failure
    monkeypatch.setattr(connections, "is_auth_failure",
                        lambda err: seen.append(err) or real(err))
    _raising(monkeypatch, RuntimeError("invalid_grant"))

    youtube.fetch_stats()

    assert seen, "the loop has to ask, not guess"
