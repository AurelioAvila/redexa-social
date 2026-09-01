"""
"Use your own app": credentials for a Meta or TikTok app the customer
registered.

Why this exists. Instagram and TikTok distinguish two situations:

  - an app that connects *other* people's accounts, which requires the
    platform's review (for Instagram, Meta's business verification too, which
    wants documents from a registered business);
  - an app that connects the account of *whoever created it*, which requires
    no review at all: Instagram allows it in Development mode for anyone with
    a role on the app, TikTok through the Sandbox.

The second is exactly the position of a customer who wants to see their own
numbers. Registering their app takes ten minutes and connects their account
immediately, without waiting on approval for ours. This is not a workaround:
it is the use both platforms intend.

The credentials stay on this computer and never pass through the proxy: the
customer keeps their own secret, so the token exchange happens locally (see
connections.using_proxy).

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import re
import sqlite3
import time

import cache
import db
import secrets_store

# Platforms where the customer can register an app of their own.
SUPPORTED = ("instagram", "tiktok")

# Format checks on the credentials.
#
# Not a flourish: almost every real error is a bad copy and paste (fields
# swapped, half of it pasted, invisible whitespace picked up with the value).
# Catching it here produces a precise message immediately, instead of a
# sign-in that fails three screens later without explaining why. Deliberately
# loose: they exist to reject the obvious mistake, not to guess what format
# the platforms will use next.
FORMATS = {
    "instagram": {
        "client_id": (r"^\d{10,25}$", "ownapp_bad_ig_id"),
        "client_secret": (r"^[A-Za-z0-9]{20,64}$", "ownapp_bad_ig_secret"),
    },
    "tiktok": {
        # The "sbaw" prefix belongs to Sandbox keys, and is the normal case
        # here: the Sandbox is what allows reading your own data without an
        # App Review. Accepting only "aw" would have rejected precisely the
        # credentials this flow exists to use.
        "client_id": (r"^(sb)?aw[A-Za-z0-9]{8,30}$", "ownapp_bad_tt_key"),
        "client_secret": (r"^[A-Za-z0-9]{20,80}$", "ownapp_bad_tt_secret"),
    },
}


def _conn() -> sqlite3.Connection:
    conn = db.connect(cache.DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS own_apps (
            platform TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            client_secret TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)
    return conn


def get(platform: str) -> dict | None:
    """The stored credentials for this platform, if there are any."""
    if platform not in SUPPORTED:
        return None
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT client_id, client_secret, created_at FROM own_apps WHERE platform = ?",
            (platform,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None

    import logging

    import secrets_store

    try:
        segreto = secrets_store.unprotect(row[1])
    except secrets_store.SecretUnavailable:
        # A database that came from another computer or Windows account:
        # the credentials are there but unusable here. Better to say "not
        # configured" and have the wizard run again than to hand an
        # unreadable secret to the platform and have the sign-in refused with
        # an incomprehensible error.
        logging.warning("%s app credentials cannot be decrypted by this "
                        "Windows account; enter them again", platform)
        return None

    return {"client_id": row[0], "client_secret": segreto, "created_at": row[2]}


def configured(platform: str) -> bool:
    return get(platform) is not None


def redirect_uri(platform: str) -> str:
    """The return address the customer has to register in their own app. It is
    the same as ours: a static page on GitHub Pages that already exists, so
    they do not have to publish a site of their own."""
    import brand
    return brand.get("INSTAGRAM_REDIRECT_URI" if platform == "instagram" else "TIKTOK_REDIRECT_URI")


def check_format(platform: str, client_id: str, client_secret: str) -> str | None:
    """The format error's code, or None when the values look plausible."""
    rules = FORMATS.get(platform)
    if not rules:
        return "ownapp_unsupported"
    values = {"client_id": client_id, "client_secret": client_secret}
    for field, (pattern, code) in rules.items():
        if not re.match(pattern, values[field] or ""):
            return code
    return None


def _verify_tiktok(key: str, secret: str) -> str | None:
    """Asks TikTok whether the pair genuinely exists.

    TikTok issues a "client_credentials" token to valid apps only, and it is a
    call with no side effects: it costs nothing and turns an error that would
    have surfaced mid-sign-in into a clear message while the customer still
    has the credentials page open.

    A network problem must not block saving: in that case nothing is claimed,
    and the real connection is what says how it went.
    """
    import requests
    try:
        resp = requests.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"client_key": key, "client_secret": secret,
                  "grant_type": "client_credentials"},
            timeout=15,
        )
    except Exception:
        return None
    if resp.ok and "access_token" in resp.json():
        return None
    print(f"[own-app] tiktok rejected credentials: {resp.text[:200]}")
    return "ownapp_tt_refused"


def save(platform: str, client_id: str, client_secret: str) -> dict:
    """Validates and stores. Returns {"ok": True} or an error code."""
    if platform not in SUPPORTED:
        return {"ok": False, "message": "ownapp_unsupported"}

    client_id = (client_id or "").strip()
    client_secret = (client_secret or "").strip()
    if not client_id or not client_secret:
        return {"ok": False, "message": "ownapp_missing"}

    bad = check_format(platform, client_id, client_secret)
    if bad:
        return {"ok": False, "message": bad}

    if platform == "tiktok":
        refused = _verify_tiktok(client_id, client_secret)
        if refused:
            return {"ok": False, "message": refused}

    conn = _conn()
    try:
        conn.execute(
            """INSERT INTO own_apps (platform, client_id, client_secret, created_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(platform) DO UPDATE SET
                 client_id = excluded.client_id,
                 client_secret = excluded.client_secret,
                 created_at = excluded.created_at""",
            (platform, client_id, secrets_store.protect(client_secret), int(time.time())),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


def clear(platform: str) -> dict:
    conn = _conn()
    try:
        conn.execute("DELETE FROM own_apps WHERE platform = ?", (platform,))
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


def status(platform: str) -> dict:
    """What to show in the interface. The secret never leaves this module: the
    tail of the client id is enough for the customer to recognize which app
    they connected, without exposing anything more."""
    saved = get(platform)
    return {
        "platform": platform,
        "supported": platform in SUPPORTED,
        "configured": bool(saved),
        "client_id_hint": ("…" + saved["client_id"][-4:]) if saved else "",
        "redirect_uri": redirect_uri(platform),
    }
