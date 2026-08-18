"""
Numero di versione dell'app e controllo di aggiornamento.

Fino ad ora la versione viveva solo nel tag della release GitHub: dentro
l'app non c'era scritta da nessuna parte, quindi non c'era nulla con cui
confrontare l'ultima pubblicata. APP_VERSION e' la fonte unica: va aggiornata
qui ad ogni release (lo ricorda check_release.py).

Il controllo aggiornamenti non scarica o installa nulla in automatico: la
build non e' firmata e non esiste un canale di aggiornamento affidabile per
sostituire un eseguibile in esecuzione. Si limita a dire "c'e' una versione
piu' nuova" con un link alla pagina di download, che l'utente apre e decide
lui. Piu' lento di un aggiornamento automatico, ma niente si installa da
solo senza che il cliente lo scelga.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import json
import time
import urllib.request

import cache
import db

APP_VERSION = "1.4.0"

RELEASES_API = "https://api.github.com/repos/AurelioAvila/social-dashboard/releases/latest"
RELEASES_PAGE = "https://github.com/AurelioAvila/social-dashboard/releases/latest"

# Un controllo al giorno basta: non e' un dato che cambia spesso, e ogni
# richiesta in piu' verso GitHub e' una richiesta che potrebbe fallire e
# rallentare l'avvio per nulla.
CHECK_INTERVAL_SECONDS = 24 * 3600


def _parse(tag: str) -> tuple[int, ...] | None:
    """'v1.2.5' -> (1, 2, 5). None se il tag non segue lo schema atteso,
    cosi' un confronto fallito non blocca ne' sbaglia direzione."""
    raw = tag.lstrip("vV").strip()
    parts = raw.split(".")
    if not (1 <= len(parts) <= 4) or not all(p.isdigit() for p in parts):
        return None
    return tuple(int(p) for p in parts)


def _is_newer(remote: str, local: str) -> bool:
    r, l = _parse(remote), _parse(local)
    if r is None or l is None:
        return False
    return r > l


def _fetch_latest_tag() -> str | None:
    req = urllib.request.Request(RELEASES_API, headers={"Accept": "application/vnd.github+json",
                                                          "User-Agent": "social-dashboard-update-check"})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read())
        return data.get("tag_name")
    except Exception:
        # Offline, rate limit, GitHub giu': non e' un errore dell'utente e
        # non deve comparirgli davanti. Si ritenta al prossimo controllo.
        return None


def _conn():
    import sqlite3
    conn = db.connect(cache.DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS update_check (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            latest_tag TEXT,
            checked_at INTEGER NOT NULL
        )
    """)
    return conn


def _cached() -> dict | None:
    conn = _conn()
    try:
        row = conn.execute("SELECT latest_tag, checked_at FROM update_check WHERE id = 1").fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return {"latest_tag": row[0], "checked_at": row[1]}


def _save(latest_tag: str | None) -> None:
    conn = _conn()
    try:
        conn.execute(
            """INSERT INTO update_check (id, latest_tag, checked_at) VALUES (1, ?, ?)
               ON CONFLICT(id) DO UPDATE SET latest_tag = excluded.latest_tag, checked_at = excluded.checked_at""",
            (latest_tag, int(time.time())),
        )
        conn.commit()
    finally:
        conn.close()


def status() -> dict:
    """Interroga GitHub al massimo una volta al giorno, altrimenti risponde
    dalla cache. Un fallimento di rete non tocca la cache: si continua a
    mostrare l'ultimo esito buono conosciuto invece di far sparire un avviso
    di aggiornamento gia' corretto solo perche' ora manca la connessione."""
    cached = _cached()
    stale = not cached or (time.time() - cached["checked_at"]) > CHECK_INTERVAL_SECONDS

    latest_tag = cached["latest_tag"] if cached else None
    if stale:
        fresh = _fetch_latest_tag()
        if fresh:
            latest_tag = fresh
            _save(fresh)
        elif not cached:
            _save(None)

    return {
        "current": APP_VERSION,
        "latest": (latest_tag or "").lstrip("vV") or None,
        "update_available": bool(latest_tag and _is_newer(latest_tag, APP_VERSION)),
        "url": RELEASES_PAGE,
    }
