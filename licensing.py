"""
Licensing: the plan this installation is actually entitled to use.

The customer's computer cannot determine the plan because the database
would be controlled by the person required to pay. The service issues the
key after payment and verifies it online; only the result is stored here.

Offline grace period: if the service is unavailable due to connectivity or
a Cloudflare outage, the latest valid result remains effective for
GRACE_DAYS. Paying customers must not be blocked while offline or during a
service outage.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import json
import sqlite3
import time

import cache
import db

# How long the latest successful verification remains valid when the service
# is unavailable. Long enough for travel or an extended outage, but not long
# enough to make verification ineffective.
GRACE_SECONDS = 7 * 24 * 3600

# Verification interval during normal operation. A revoked license caused by
# a refund or canceled subscription becomes invalid within one day.
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
    # Compatible migration for installations created before distinguishing
    # an unavailable service from a revoked license.
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
    """Ask the service whether the key is valid.

    Raise if the service does not respond so the caller can decide whether
    to use the latest known result. The device identifier lets the Worker
    count distinct installations using the same key. Use `register=True`
    only after an explicit "Activate" click; background checks must never
    register a new device, or a copied key would register silently during
    the first automatic refresh.
    """
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
    """Activate a key entered by the user.

    Verification must succeed because the key cannot be validated offline;
    accepting it without verification would grant a paid plan for free.
    """
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
    """Return the Stripe customer portal URL for the active key.

    Subscriptions must be canceled there. Merely removing the key from this
    computer would allow the subscription to keep renewing.
    """
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
    """Recheck the stored license in the background when due.

    Remain silent because network issues must not disrupt the user.
    """
    lic = stored()
    if not lic:
        return
    # A negative interval means the clock now sits behind the last check.
    # Skipping the recheck on that reading is what made a rolled-back clock
    # permanent: nothing was ever asked again. Treat it as due instead.
    since_check = int(time.time()) - lic["last_check"]
    if 0 <= since_check < RECHECK_SECONDS:
        return
    try:
        data = _ask_service(lic["key"])
    except Exception:
        # The service is unavailable, so no new information exists and the
        # latest successful result remains valid within the grace period.
        return

    if data.get("valid"):
        _save(lic["key"], data.get("plan") or "free", data.get("email") or "", ok=True)
    else:
        # Not every "invalid" means the subscription is gone. The service
        # distinguishes them and this used to throw the distinction away:
        # license_reactivate_needed (this device is not on the key's list,
        # which a reinstall or a hardware change causes) and
        # license_device_limit were both recorded as revocation, and
        # revocation has no grace — so a paying customer whose device id
        # changed lost their plan on the next background check, permanently.
        #
        # Only the two answers that mean "you are not entitled" revoke. The
        # rest save without extending last_ok, so the plan keeps working
        # inside the grace period, status() reports it as stale, and the
        # customer has those days to reactivate the device.
        revoked = data.get("reason") in (None, "", "license_not_found", "license_inactive")
        _save(lic["key"], lic["plan"], lic["email"], ok=False, revoked=revoked)


def current_plan() -> str:
    """Return the plan this installation is entitled to use."""
    import plans

    lic = stored()
    if not lic:
        return plans.FREE
    # Explicit revocation has no grace period; the plan expires immediately.
    if lic["revoked"]:
        return plans.FREE

    age = int(time.time()) - lic["last_ok"]
    # Grace covers a service that cannot be reached. It does not cover a clock
    # the customer sets: with time.time() moving backwards, `age` went
    # negative, never exceeded the grace period, and handed out the plan
    # forever — cancel the subscription, set the date back, keep Pro. A
    # negative age is not a young licence, it is an unusable reading, so it
    # fails closed. refresh_if_due now asks again in that state, and one
    # successful answer rewrites last_ok and clears it on its own.
    if age < 0 or age > GRACE_SECONDS:
        return plans.FREE
    return plans.normalize(lic["plan"])


def status() -> dict:
    """Return UI status: plan, key, and any license or verification issue."""
    import plans

    lic = stored()
    if not lic:
        return {"active": False, "plan": plans.FREE, "key": "", "email": ""}

    now = int(time.time())
    age = now - lic["last_ok"]
    # Revoked or too old: neither state unlocks features, but each requires a
    # different explanation to the user.
    revoked = lic["revoked"]
    # `age < 0` for the same reason as in current_plan: a clock behind the
    # last successful check is an unusable reading, not a young licence.
    # Without it this screen reported a healthy active plan while
    # current_plan had already dropped to free — the UI contradicting the
    # entitlements on the same data.
    expired = revoked or age < 0 or age > GRACE_SECONDS
    # Verification failed but is not yet decisive: the service has been
    # unavailable, and the plan remains active during the grace period.
    stale = not revoked and lic["last_check"] > lic["last_ok"]

    return {
        "active": not expired,
        "revoked": revoked,
        "plan": plans.FREE if expired else plans.normalize(lic["plan"]),
        # Show only the key suffix: enough to identify it without exposing
        # the full key in an application screenshot.
        "key": f"...{lic['key'][-6:]}" if lic["key"] else "",
        "email": lic["email"],
        "expired": expired,
        "stale": stale and not expired,
        "last_ok": lic["last_ok"],
    }
