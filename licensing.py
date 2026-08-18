"""
Licenze: quale piano ha davvero questa installazione.

Il piano non puo' essere deciso dal computer del cliente - il database
sarebbe sul PC di chi deve pagare. La chiave viene emessa dal servizio dopo
il pagamento e verificata online; qui si conserva solo l'esito.

Tolleranza offline: se il servizio non risponde (rete assente, Cloudflare
giu'), l'ultimo esito valido continua a valere per GRACE_DAYS. Un cliente
che ha pagato non deve ritrovarsi bloccato perche' e' in aereo o perche'
un nostro servizio ha un disservizio.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import json
import sqlite3
import time

import cache
import db

# Quanto a lungo vale l'ultima verifica riuscita quando il servizio non
# risponde. Abbastanza da coprire un viaggio o un disservizio prolungato,
# non tanto da rendere inutile la verifica.
GRACE_SECONDS = 7 * 24 * 3600

# Ogni quanto ricontrollare quando tutto funziona: una licenza revocata
# (rimborso, abbonamento disdetto) smette di valere entro un giorno.
RECHECK_SECONDS = 24 * 3600

_TABLE = """
CREATE TABLE IF NOT EXISTS license (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    key TEXT NOT NULL,
    plan TEXT NOT NULL,
    email TEXT NOT NULL DEFAULT '',
    last_ok INTEGER NOT NULL,
    last_check INTEGER NOT NULL
)
"""


def _conn() -> sqlite3.Connection:
    conn = db.connect(cache.DB_PATH)
    conn.execute(_TABLE)
    # Migrazione soft per installazioni precedenti alla distinzione fra
    # "servizio irraggiungibile" e "licenza revocata".
    cols = [r[1] for r in conn.execute("PRAGMA table_info(license)").fetchall()]
    if "revoked" not in cols:
        conn.execute("ALTER TABLE license ADD COLUMN revoked INTEGER NOT NULL DEFAULT 0")
    return conn


def _service_url() -> str:
    import brand

    return (brand.get("OAUTH_PROXY_URL") or "").rstrip("/")


def stored() -> dict | None:
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT key, plan, email, last_ok, last_check, revoked FROM license WHERE id = 1"
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return {"key": row[0], "plan": row[1], "email": row[2], "last_ok": row[3],
            "last_check": row[4], "revoked": bool(row[5])}


def _save(key: str, plan: str, email: str, ok: bool, revoked: bool = False) -> None:
    now = int(time.time())
    prev = stored()
    last_ok = now if ok else (prev["last_ok"] if prev else 0)
    conn = _conn()
    try:
        conn.execute(
            """INSERT INTO license (id, key, plan, email, last_ok, last_check, revoked)
               VALUES (1, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 key = excluded.key, plan = excluded.plan, email = excluded.email,
                 last_ok = excluded.last_ok, last_check = excluded.last_check,
                 revoked = excluded.revoked""",
            (key, plan, email, last_ok, now, 1 if revoked else 0),
        )
        conn.commit()
    finally:
        conn.close()


def clear() -> None:
    conn = _conn()
    try:
        conn.execute("DELETE FROM license WHERE id = 1")
        conn.commit()
    finally:
        conn.close()


def _ask_service(key: str, register: bool = False) -> dict:
    """Chiede al servizio se la chiave e' valida. Solleva se non risponde:
    e' il chiamante a decidere se ricadere sull'ultimo esito noto.

    Manda anche l'identificativo del dispositivo: e' cosi' che il Worker
    conta quante installazioni diverse stanno usando la stessa chiave.
    `register=True` solo per un clic esplicito su "Activate" - un controllo
    in background non deve mai poter aggiungere un nuovo dispositivo da
    solo, altrimenti una chiave copiata su una macchina diversa si
    registrerebbe in silenzio al primo refresh automatico."""
    import requests

    base = _service_url()
    if not base:
        raise RuntimeError("license_service_unavailable")
    resp = requests.post(f"{base}/license/verify", json={
        "key": key, "device_id": cache.device_id(), "register": register,
    }, timeout=15)
    if not resp.ok:
        raise RuntimeError("license_service_unavailable")
    return resp.json()


def activate(key: str) -> dict:
    """Attiva una chiave inserita dall'utente. Qui la verifica deve riuscire
    davvero: senza rete non si puo' sapere se la chiave e' buona, e accettarla
    sulla fiducia significherebbe regalare i piani a pagamento."""
    key = (key or "").strip().upper()
    if not key:
        return {"ok": False, "code": "license_missing"}

    try:
        data = _ask_service(key, register=True)
    except Exception:
        return {"ok": False, "code": "license_service_unavailable"}

    if not data.get("valid"):
        return {"ok": False, "code": data.get("reason") or "license_not_found"}

    plan = data.get("plan") or "free"
    _save(key, plan, data.get("email") or "", ok=True)
    return {"ok": True, "plan": plan, "email": data.get("email") or ""}


def billing_portal_url() -> dict:
    """URL del portale clienti Stripe per la chiave attiva: e' li' che si
    disdice davvero, non rimuovendo solo la chiave da questo computer (quella
    lascerebbe l'abbonamento a rinnovarsi comunque)."""
    import requests

    lic = stored()
    if not lic or not lic["key"]:
        return {"ok": False, "code": "license_missing"}

    base = _service_url()
    if not base:
        return {"ok": False, "code": "license_service_unavailable"}
    try:
        resp = requests.post(f"{base}/billing/portal", json={"key": lic["key"]}, timeout=15)
    except Exception:
        return {"ok": False, "code": "license_service_unavailable"}
    if not resp.ok:
        try:
            code = resp.json().get("error") or "license_service_unavailable"
        except Exception:
            code = "license_service_unavailable"
        return {"ok": False, "code": code}
    data = resp.json()
    if not data.get("url"):
        return {"ok": False, "code": "license_service_unavailable"}
    return {"ok": True, "url": data["url"]}


def refresh_if_due() -> None:
    """Ricontrolla in background la licenza salvata, se e' passato abbastanza
    tempo. Silenzioso: un problema di rete non deve disturbare l'utente."""
    lic = stored()
    if not lic:
        return
    if int(time.time()) - lic["last_check"] < RECHECK_SECONDS:
        return
    try:
        data = _ask_service(lic["key"])
    except Exception:
        # Servizio irraggiungibile: non si sa nulla di nuovo, quindi vale
        # ancora l'ultimo esito buono (entro il periodo di tolleranza).
        return

    if data.get("valid"):
        _save(lic["key"], data.get("plan") or "free", data.get("email") or "", ok=True)
    else:
        # Il servizio ha risposto, e la risposta e' "non valida": rimborso o
        # abbonamento disdetto. Qui la tolleranza non c'entra - quella serve
        # a coprire i problemi di rete, non a lasciare attivo per una
        # settimana un piano che non e' piu' pagato.
        _save(lic["key"], lic["plan"], lic["email"], ok=False, revoked=True)


def current_plan() -> str:
    """Il piano che questa installazione puo' davvero usare."""
    import plans

    lic = stored()
    if not lic:
        return plans.FREE
    # Revoca esplicita: nessuna tolleranza, il piano decade subito.
    if lic["revoked"]:
        return plans.FREE

    age = int(time.time()) - lic["last_ok"]
    if age > GRACE_SECONDS:
        return plans.FREE
    return plans.normalize(lic["plan"])


def status() -> dict:
    """Stato per l'interfaccia: che piano, da quale chiave, e se c'e' qualcosa
    che l'utente deve sapere (licenza non piu' valida, verifica scaduta)."""
    import plans

    lic = stored()
    if not lic:
        return {"active": False, "plan": plans.FREE, "key": "", "email": ""}

    now = int(time.time())
    age = now - lic["last_ok"]
    # Revocata o troppo vecchia: in entrambi i casi non sblocca piu' nulla,
    # ma il motivo da spiegare all'utente e' diverso.
    revoked = lic["revoked"]
    expired = revoked or age > GRACE_SECONDS
    # Verifica non riuscita ma non ancora decisiva: il servizio non risponde
    # da un po' e il piano regge grazie al periodo di tolleranza.
    stale = not revoked and lic["last_check"] > lic["last_ok"]

    return {
        "active": not expired,
        "revoked": revoked,
        "plan": plans.FREE if expired else plans.normalize(lic["plan"]),
        # Della chiave si mostra solo la coda: basta a riconoscerla, e uno
        # screenshot dell'app non la regala a nessuno.
        "key": f"...{lic['key'][-6:]}" if lic["key"] else "",
        "email": lic["email"],
        "expired": expired,
        "stale": stale and not expired,
        "last_ok": lic["last_ok"],
    }
