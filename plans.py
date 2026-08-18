"""
Cosa include ogni piano, in un posto solo.

Finora la pagina dei prezzi elencava funzioni "Pro" che in realta' erano
disponibili a tutti: si vendeva qualcosa che il codice non faceva rispettare.
Qui i limiti diventano una tabella unica, applicata dal server - il frontend
la legge per mostrare gli stati bloccati, ma non e' lui a decidere: chi
volesse aggirarli chiamando le API a mano troverebbe comunque un rifiuto.

Sono elencate solo le funzioni che esistono davvero. Spazi di lavoro,
report white-label e accesso multi-utente non sono implementati, quindi non
compaiono qui e non vengono promessi come attivi.
"""

FREE = "free"
PRO = "pro"
STUDIO = "studio"

DEFAULT_PLAN = FREE

# max_accounts: None = senza limite (nessun piano lo usa al momento).
ENTITLEMENTS = {
    FREE: {
        "max_accounts": 1,
        "history": False,      # storico e grafici di trend
        "best_hours": False,   # fasce orarie consigliate
        "csv_export": False,
    },
    PRO: {
        "max_accounts": 3,
        "history": True,
        "best_hours": True,
        "csv_export": True,
    },
    STUDIO: {
        "max_accounts": 10,
        "history": True,
        "best_hours": True,
        "csv_export": True,
    },
}


def normalize(plan: str | None) -> str:
    """Un piano sconosciuto (o assente, es. utente non registrato) vale come
    Free: mai come qualcosa di piu' generoso."""
    plan = (plan or "").strip().lower()
    return plan if plan in ENTITLEMENTS else DEFAULT_PLAN


def entitlements(plan: str | None) -> dict:
    return dict(ENTITLEMENTS[normalize(plan)])


def allows(plan: str | None, feature: str) -> bool:
    return bool(entitlements(plan).get(feature))


def max_accounts(plan: str | None) -> int | None:
    return entitlements(plan).get("max_accounts")


def public_entitlements(plan: str | None) -> dict:
    """Quello che il frontend riceve per disegnare lucchetti e inviti
    all'upgrade senza doverli indovinare."""
    ent = entitlements(plan)
    return {"plan": normalize(plan), **ent}
