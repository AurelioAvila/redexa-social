"""The smallest rate limit the authentication endpoints can be given.

The app runs locally (127.0.0.1) and cross-origin access is already refused
by _local_only_guard in app.py, but that defence does nothing about a script
on the same machine — or someone with physical access to the PC — trying
logins and registrations in rapid succession. The PBKDF2 auth.py derives its
hash with slows every attempt on its own, but without an explicit limit
nothing stops thousands of automated requests one after another.

In memory, with no external dependency: consistent with a single-process
local app, and nothing to coordinate between instances the way Redis or a
shared store would need.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException

_lock = threading.Lock()
_attempts: dict[str, deque] = defaultdict(deque)


def enforce(key: str, max_attempts: int, window_seconds: int) -> None:
    """Raises HTTPException(429) when `key` has already exceeded
    `max_attempts` requests within the last `window_seconds`. Otherwise it
    records this attempt and lets the request through."""
    now = time.monotonic()
    with _lock:
        bucket = _attempts[key]
        cutoff = now - window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= max_attempts:
            retry_after = int(window_seconds - (now - bucket[0])) + 1
            raise HTTPException(
                429,
                "Troppi tentativi. Riprova tra qualche minuto.",
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)
