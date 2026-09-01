"""
The transactional email for the local account (not licences - those live in
licensing.py): password reset code, welcome on registration, password-changed
notice. Routed through the Worker for the same reason as the OAuth exchange
and the licences - the Resend key cannot live inside a distributed
executable.

A failure here must never interrupt the flow that called it: registering or
asking for a reset has to work offline, or with the Worker unreachable, just
without the accompanying email.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import connections


def send_reset_code(to: str, code: str) -> None:
    _post("/mail/reset-code", {"to": to, "code": code})


def send_welcome(to: str, name: str) -> None:
    _post("/mail/welcome", {"to": to, "name": name})


def send_password_changed(to: str, name: str) -> None:
    """Reports that the password actually changed, not that one was asked for.

    It is the only way the account holder learns of a change they did not
    make: the account is local here, so it means someone had access to this
    computer.
    """
    _post("/mail/password-changed", {"to": to, "name": name})


def _post(path: str, payload: dict) -> None:
    # Everything goes inside here, proxy_url() included: on a clone without
    # brand.py (development, CI) that call raises ModuleNotFoundError rather
    # than simply returning an empty string. An exception escaping from here
    # would fail the registration itself - precisely what the module comment
    # says must never happen.
    try:
        import requests

        base = connections.proxy_url()
        if not base:
            return
        requests.post(f"{base}{path}", json=payload, timeout=8)
    except Exception:
        pass
