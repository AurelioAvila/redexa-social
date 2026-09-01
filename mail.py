"""
Transactional email for local accounts (licensing messages live in
licensing.py): password-reset codes, registration welcomes and password-change
notifications. Messages are routed through the Worker for the same reason as
OAuth and licensing requests: the Resend key cannot live in a distributed
executable.

A delivery failure must never interrupt the calling flow. Registration and
password-reset requests must continue to work offline or while the Worker is
unreachable, only without the accompanying email.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import logging

import connections


def send_reset_code(to: str, code: str) -> None:
    _post("/mail/reset-code", {"to": to, "code": code})


def send_welcome(to: str, name: str) -> None:
    _post("/mail/welcome", {"to": to, "name": name})


def send_password_changed(to: str, name: str) -> None:
    """Report a completed password change, not merely a requested one.

    This is the only way for the account owner to discover an unauthorized
    change. Accounts are local, so such a change implies access to this device.
    """
    _post("/mail/password-changed", {"to": to, "name": name})


def _post(path: str, payload: dict) -> None:
    # Keep every operation, including proxy_url(), inside this best-effort
    # boundary. Development and CI clones may not contain brand.py, and an
    # email failure must not make registration itself fail.
    try:
        import requests

        base = connections.proxy_url()
        if not base:
            return
        requests.post(f"{base}{path}", json=payload, timeout=8)
    except Exception:
        logging.warning("transactional email delivery failed", exc_info=True)
