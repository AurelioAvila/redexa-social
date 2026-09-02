"""
The retry policy for outbound calls to the platform APIs.

What matters here is not that retrying exists — it is what is *not* retried.
A loop that retries any error, which is what youtube.py used to do, spends
the user's time on a 401 to arrive at the same answer and hammers an
endpoint with a credential the platform has already rejected. That is how a
developer key gets suspended.

The other half is the wait. `Retry-After: 900` is not rare, and obeying it
literally inside a desktop dashboard refresh freezes the interface for a
quarter of an hour: the cap is a product decision, not a detail, so it is
covered here too.

No network and no real sleeping: `requester` and `sleep` are injected.
"""
import os

import pytest
import requests

from platforms import _http


class FakeResponse:
    def __init__(self, status_code, retry_after=None):
        self.status_code = status_code
        self.headers = {} if retry_after is None else {"Retry-After": retry_after}


def fake_requester(*responses):
    """Answers with the given sequence, and records how it was called."""
    calls = []

    def call(method, url, **kwargs):
        calls.append((method, url))
        item = responses[min(len(calls) - 1, len(responses) - 1)]
        if isinstance(item, Exception):
            raise item
        return item

    call.calls = calls
    return call


def recording_sleep():
    waits = []
    return waits, waits.append


def test_a_good_response_neither_sleeps_nor_retries():
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(200))

    resp = _http.get("https://example.test", requester=call, sleep=sleep)

    assert resp.status_code == 200
    assert len(call.calls) == 1
    assert waits == []


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
def test_a_final_refusal_comes_straight_back(status):
    """401 is the case that matters: it is a revoked token, and retrying it
    does not make it valid again."""
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(status))

    resp = _http.get("https://example.test", requester=call, sleep=sleep)

    assert resp.status_code == status
    assert len(call.calls) == 1, f"{status} must not be retried"
    assert waits == []


@pytest.mark.parametrize("status", [429, 500, 502, 503])
def test_a_transient_refusal_is_retried(status):
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(status), FakeResponse(200))

    resp = _http.get("https://example.test", requester=call, sleep=sleep)

    assert resp.status_code == 200
    assert len(call.calls) == 2
    assert waits == [_http.BACKOFF[0]]


def test_the_platforms_retry_after_beats_our_own_backoff():
    """A made-up wait shorter than the one being asked for is worse than no
    retry at all: it spends what is left of the account's budget arguing."""
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(429, retry_after="7"), FakeResponse(200))

    _http.get("https://example.test", requester=call, sleep=sleep)

    assert waits == [7.0]


def test_an_absurd_retry_after_is_capped():
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(429, retry_after="900"), FakeResponse(200))

    _http.get("https://example.test", requester=call, sleep=sleep)

    assert waits == [_http.MAX_WAIT]
    assert sum(waits) <= _http.MAX_TOTAL_WAIT


def test_an_unreadable_retry_after_falls_back_to_the_backoff():
    """The HTTP-date form is legal. We do not parse it, but it must not take
    the call down with it."""
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(429, retry_after="Wed, 21 Oct 2026 07:28:00 GMT"),
                          FakeResponse(200))

    resp = _http.get("https://example.test", requester=call, sleep=sleep)

    assert resp.status_code == 200
    assert waits == [_http.BACKOFF[0]]


def test_after_the_last_attempt_the_refusal_is_returned_not_raised():
    """The caller runs raise_for_status(), so it has to keep behaving the way
    it did: this returns the response, not an exception."""
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(429))

    resp = _http.get("https://example.test", requester=call, sleep=sleep)

    assert resp.status_code == 429
    assert len(call.calls) == _http.ATTEMPTS
    assert len(waits) == _http.ATTEMPTS - 1


def test_a_network_error_is_retried_and_finally_raised():
    waits, sleep = recording_sleep()
    call = fake_requester(requests.exceptions.ConnectionError("network down"))

    with pytest.raises(requests.exceptions.ConnectionError):
        _http.get("https://example.test", requester=call, sleep=sleep)

    assert len(call.calls) == _http.ATTEMPTS


def test_a_network_that_comes_back_does_not_fail_the_call():
    """The case retrying exists for: a dropped packet must not mark an account
    as broken, or the word "failed" stops meaning anything and the revoked
    token goes unnoticed too."""
    waits, sleep = recording_sleep()
    call = fake_requester(requests.exceptions.Timeout("timed out"), FakeResponse(200))

    resp = _http.get("https://example.test", requester=call, sleep=sleep)

    assert resp.status_code == 200
    assert len(call.calls) == 2


def test_the_time_spent_waiting_has_an_overall_cap():
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(429, retry_after="20"))

    _http.get("https://example.test", attempts=6, requester=call, sleep=sleep)

    assert sum(waits) <= _http.MAX_TOTAL_WAIT


def test_the_method_and_url_arrive_intact():
    call = fake_requester(FakeResponse(200))

    _http.post("https://example.test/token", requester=call, sleep=lambda _: None)

    assert call.calls == [("POST", "https://example.test/token")]
