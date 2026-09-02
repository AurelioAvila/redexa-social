"""Outbound HTTP for the platform adapters, with the only retry worth having.

Every adapter here talks to somebody else's API — Instagram's Graph, TikTok's
open API, Google's — and those APIs rate limit. Until this module existed the
handling was uneven and, where it existed, wrong for the case it mattered
most: YouTube retried *any* exception on fixed 2 and 5 second sleeps, and
nothing anywhere read `Retry-After`, which is the one thing the platform
actually tells you.

What is retried, and what is deliberately not:

  429 and 5xx are retried. They mean "not now", and the next attempt has a
  real chance.

  Connection errors and timeouts are retried. A dashboard that marks an
  account as failed because a packet was dropped teaches its owner to ignore
  the word "failed", and then the revoked token goes unnoticed too.

  Every other 4xx is returned immediately. A 401 is a revoked token and a 400
  is a bad request: retrying either wastes the user's time to arrive at the
  same answer, and hammering an endpoint with a rejected credential is how a
  developer key gets suspended. This is the half that a retry-on-any-exception
  loop gets wrong.

`Retry-After` is honoured when the platform sends it, because a made-up
backoff that is shorter than the one being asked for is worse than no retry
at all — it spends the account's remaining budget arguing.

The waits are capped. This runs inside a desktop dashboard refresh, and
platforms answer 429 with `Retry-After: 900` often enough that obeying it
literally would freeze the interface for a quarter of an hour. Past the cap
the honest thing is to give up and report it, which the caller already knows
how to do.

The response is returned as it came, refusal and all, so a caller's
`raise_for_status()` behaves exactly as it did before.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import time

import requests

#: Total attempts, not retries: 3 means the first call plus two more.
ATTEMPTS = 3

#: Longest single wait, in seconds. Anything longer and the refresh has
#: stopped being a refresh.
MAX_WAIT = 20.0

#: Longest total time spent sleeping across one call's attempts.
MAX_TOTAL_WAIT = 30.0

#: Grows if the platform does not say how long to wait.
BACKOFF = (2.0, 5.0)

_RETRYABLE_ERRORS = (requests.exceptions.ConnectionError, requests.exceptions.Timeout)


def _retry_after_seconds(response) -> float | None:
    """The platform's own answer, in seconds, when it gave one we can use.

    Only the integer-seconds form. The HTTP-date form is legal and rare here,
    and parsing dates against a clock that may be wrong is a worse failure
    than falling back to our own backoff.
    """
    raw = response.headers.get("Retry-After") if response is not None else None
    if not raw:
        return None
    try:
        seconds = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return seconds if seconds >= 0 else None


def _should_retry(response) -> bool:
    if response is None:
        return False
    return response.status_code == 429 or 500 <= response.status_code < 600


def request(method: str, url: str, *, attempts: int = ATTEMPTS,
            sleep=time.sleep, requester=None, **kwargs):
    """Performs the request, retrying only transient refusals.

    `sleep` and `requester` are injectable so the policy can be tested
    without a network or a real wait.
    """
    call = requester or requests.request
    spent = 0.0
    last_error = None

    for attempt in range(attempts):
        response = None
        try:
            response = call(method, url, **kwargs)
            last_error = None
            if not _should_retry(response):
                return response
        except _RETRYABLE_ERRORS as exc:
            last_error = exc

        if attempt == attempts - 1:
            break

        asked = _retry_after_seconds(response)
        wait = asked if asked is not None else BACKOFF[min(attempt, len(BACKOFF) - 1)]
        wait = min(wait, MAX_WAIT, MAX_TOTAL_WAIT - spent)
        if wait <= 0:
            # The budget is gone. Stopping here and reporting is better than
            # a retry that has been stripped of the wait that made it worth
            # attempting.
            break
        sleep(wait)
        spent += wait

    if last_error is not None:
        raise last_error
    return response


def get(url: str, **kwargs):
    return request("GET", url, **kwargs)


def post(url: str, **kwargs):
    return request("POST", url, **kwargs)
