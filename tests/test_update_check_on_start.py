"""Opening the application is the moment somebody is there to be told about a
new version, and it happens far more rarely than once a day. The cache was
built around a daily cadence, which meant a user who opened the app yesterday
and opens it again an hour after a release was answered from a cache that
predates the release - and heard about the update up to a day late."""

import time
import version


def _reset(monkeypatch, cached_tag, age_seconds, fetched):
    calls = []

    def fake_fetch():
        calls.append(1)
        return fetched

    monkeypatch.setattr(version, "_fetch_latest_tag", fake_fetch)
    monkeypatch.setattr(version, "_cached", lambda: {
        "latest_tag": cached_tag,
        "checked_at": int(time.time()) - age_seconds,
    })
    monkeypatch.setattr(version, "_save", lambda tag: None)
    monkeypatch.setattr(version, "_checked_this_process", False)
    return calls


def test_the_first_check_after_launch_ignores_a_fresh_cache(monkeypatch):
    """A release published minutes ago must be seen on the next launch."""
    calls = _reset(monkeypatch, "v1.9.4", 60, "v1.10.0")
    result = version.status()
    assert len(calls) == 1, "the first check of a run must reach GitHub"
    assert result["latest"] == "1.10.0"


def test_later_checks_in_the_same_run_use_the_cache(monkeypatch):
    """One request per launch, not one per poll: the window stays open for
    hours and the front end asks repeatedly."""
    calls = _reset(monkeypatch, "v1.9.4", 60, "v1.10.0")
    version.status()
    version.status()
    version.status()
    assert len(calls) == 1


def test_a_stale_cache_is_still_refreshed_later_in_the_same_run(monkeypatch):
    calls = _reset(monkeypatch, "v1.9.4", version.CHECK_INTERVAL_SECONDS + 10, "v1.10.0")
    version.status()
    version.status()
    assert len(calls) == 2


def test_a_network_failure_keeps_the_last_known_answer(monkeypatch):
    """An update notice that is already correct must not vanish because the
    connection is gone right now."""
    _reset(monkeypatch, "v1.10.0", 60, None)
    monkeypatch.setattr(version, "APP_VERSION", "1.9.4")
    result = version.status()
    assert result["latest"] == "1.10.0"
    assert result["update_available"] is True
