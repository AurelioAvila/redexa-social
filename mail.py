"""
Le email transazionali dell'account locale (non le licenze, quelle
vivono in licensing.py): codice di reset password, benvenuto alla
registrazione, avviso di password modificata. Instradate sul Worker per lo stesso motivo dello scambio
OAuth e delle licenze - la chiave Resend non puo' vivere in un eseguibile
distribuito.

Un fallimento qui non deve mai interrompere il flusso che lo ha chiamato:
registrarsi o chiedere un reset deve funzionare anche offline o col Worker
irraggiungibile, solo senza l'email di corredo.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import connections


def send_reset_code(to: str, code: str) -> None:
    _post("/mail/reset-code", {"to": to, "code": code})


def send_welcome(to: str, name: str) -> None:
    _post("/mail/welcome", {"to": to, "name": name})


def send_password_changed(to: str, name: str) -> None:
    """Avvisa che la password e' cambiata davvero, non che e' stata chiesta.

    E' l'unico modo in cui il titolare dell'account scopre un cambio che non
    ha fatto lui: qui l'account e' locale, quindi significa che qualcuno ha
    avuto accesso a questo computer.
    """
    _post("/mail/password-changed", {"to": to, "name": name})


def _post(path: str, payload: dict) -> None:
    # Tutto qui dentro, compreso proxy_url(): su un clone senza brand.py
    # (sviluppo, CI) quella chiamata solleva ModuleNotFoundError, non
    # restituisce semplicemente una stringa vuota. Un'eccezione che sfugge
    # da qui manderebbe in errore la registrazione stessa - esattamente
    # quello che il commento del modulo dice non deve succedere mai.
    try:
        import requests

        base = connections.proxy_url()
        if not base:
            return
        requests.post(f"{base}{path}", json=payload, timeout=8)
    except Exception:
        pass
