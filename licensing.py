"""
Licences: which plan this installation actually has.

The plan cannot be decided by the customer's computer - the database would sit
on the PC of the person who is supposed to pay. The key is issued by the
service after payment and verified online; only the outcome is kept here.

Offline grace: when the service does not answer (no network, Cloudflare down),
the last valid result goes on standing for GRACE_DAYS. A customer who paid
should not find themselves locked out because they are on a plane, or because
something of ours is having an outage.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import json
import sqlite3
import time

import cache
import db

# How long the last successful check stands when the service does not
# answer. Long enough to cover a trip or a drawn-out outage, not so long that
# checking stops meaning anything.
GRACE_SECONDS = 7 * 24 * 3600

# How often to re-check while everything works: a revoked licence (a
# refund, a cancelled subscription) stops counting within a day.
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
    # Soft migration for installations older than the distinction between
    # "service unreachable" and "licence revoked".
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
    """Asks the service whether the key is valid. Raises when it does not
    answer: falling back to the last known result is the caller's decision.

    It also sends the device identifier, which is how the Worker counts how
    many distinct installations are using one key. `register=True` only for an
    explicit click on "Activate" - a background check must never be able to
    add a new device on its own, or a key copied onto a different machine
    would register itself silently at the first automatic refresh."""
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
    """Activates a key the user typed in. The check has to genuinely succeed
    here: with no network there is no way to know whether the key is good, and
    taking it on trust would be giving the paid plans away."""
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
    """The Stripe customer-portal URL for the active key: cancelling actually
    happens there, not by removing the key from this computer, which would
    leave the subscription renewing regardless."""
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
    """Re-checks the stored licence in the background, once enough time has
    passed. Silent: a network problem is not the user's to deal with."""
    lic = stored()
    if not lic:
        return
    if int(time.time()) - lic["last_check"] < RECHECK_SECONDS:
        return
    try:
        data = _ask_service(lic["key"])
    except Exception:
        # Service unreachable: nothing new is known, so the last good
        # result still stands (within the grace period).
        return

    if data.get("valid"):
        _save(lic["key"], data.get("plan") or "free", data.get("email") or "", ok=True)
    else:
        # The service answered, and the answer is "not valid": a refund or
        # a cancelled subscription. Grace has no part in this - it is there to
        # cover network trouble, not to keep a plan alive for a week after it
        # stopped being paid for.
        _save(lic["key"], lic["plan"], lic["email"], ok=False, revoked=True)


def current_plan() -> str:
    """The plan this installation can actually use."""
    import plans

    lic = stored()
    if not lic:
        return plans.FREE
    # An explicit revocation: no grace, the plan lapses immediately.
    if lic["revoked"]:
        return plans.FREE

    age = int(time.time()) - lic["last_ok"]
    if age > GRACE_SECONDS:
        return plans.FREE
    return plans.normalize(lic["plan"])


def status() -> dict:
    """State for the interface: which plan, from which key, and whether there
    is anything the user needs to know (licence no longer valid, check gone
    stale)."""
    import plans

    lic = stored()
    if not lic:
        return {"active": False, "plan": plans.FREE, "key": "", "email": ""}

    now = int(time.time())
    age = now - lic["last_ok"]
    # Revoked or too old: either way it unlocks nothing further, but the
    # reason to explain to the user is not the same.
    revoked = lic["revoked"]
    expired = revoked or age > GRACE_SECONDS
    # A check that failed without settling anything: the service has been
    # unreachable for a while and the plan is holding on grace.
    stale = not revoked and lic["last_check"] > lic["last_ok"]

    return {
        "active": not expired,
        "revoked": revoked,
        "plan": plans.FREE if expired else plans.normalize(lic["plan"]),
        # Only the tail of the key is shown: enough to recognize it, and a
        # screenshot of the app hands it to nobody.
        "key": f"...{lic['key'][-6:]}" if lic["key"] else "",
        "email": lic["email"],
        "expired": expired,
        "stale": stale and not expired,
        "last_ok": lic["last_ok"],
    }
