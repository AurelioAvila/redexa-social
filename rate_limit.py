"""Rate limiting minimale per gli endpoint di autenticazione.

L'app gira in locale (127.0.0.1) e l'accesso cross-origin e' gia' bloccato
da _local_only_guard in app.py, ma quella difesa non impedisce a uno script
sulla stessa macchina - o a un utente malintenzionato con accesso fisico al
PC - di tentare login/registrazioni ripetute in rapida sequenza. bcrypt
rallenta ogni tentativo di per se', ma senza un limite esplicito nulla
impedisce migliaia di richieste automatizzate in sequenza.

In-memory, senza dipendenze esterne: coerente con un'app single-process
locale (niente Redis/store condiviso da coordinare tra istanze).
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException

_lock = threading.Lock()
_attempts: dict[str, deque] = defaultdict(deque)


def enforce(key: str, max_attempts: int, window_seconds: int) -> None:
    """Solleva HTTPException(429) se `key` ha gia' superato `max_attempts`
    richieste negli ultimi `window_seconds`. Altrimenti registra il tentativo
    corrente e lascia proseguire la richiesta."""
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
