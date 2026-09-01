"""
What each plan includes, in one place.

Until now the pricing page listed "Pro" features that were in fact available
to everyone: we were selling something the code did not enforce. Here the
limits become a single table, applied by the server - the frontend reads it
to draw the locked states, but it does not decide: anyone getting around it
by calling the API by hand still meets a refusal.

Only features that genuinely exist are listed. Workspaces, white-label
reports and multi-user access are not implemented, so they do not appear here
and are not promised as active.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""

FREE = "free"
PRO = "pro"
STUDIO = "studio"

DEFAULT_PLAN = FREE

# max_accounts: None = no limit (no plan uses it at the moment).
ENTITLEMENTS = {
    FREE: {
        "max_accounts": 1,
        "history": False,      # storico e grafici di trend
        "best_hours": False,   # fasce orarie consigliate
        "csv_export": False,
        # Comparison against hand-picked public accounts (rivals.py). Paid
        # because it answers the question someone opens a tool like this to
        # ask - "how am I doing against people doing what I do" - and because
        # it spends API quota on every read.
        "rivals": False,
    },
    PRO: {
        "max_accounts": 3,
        "history": True,
        "best_hours": True,
        "csv_export": True,
        "rivals": True,
    },
    STUDIO: {
        "max_accounts": 10,
        "history": True,
        "best_hours": True,
        "csv_export": True,
        "rivals": True,
    },
}


def normalize(plan: str | None) -> str:
    """An unknown plan (or none at all, e.g. an unregistered user) counts as
    Free: never as anything more generous."""
    plan = (plan or "").strip().lower()
    return plan if plan in ENTITLEMENTS else DEFAULT_PLAN


def entitlements(plan: str | None) -> dict:
    return dict(ENTITLEMENTS[normalize(plan)])


def allows(plan: str | None, feature: str) -> bool:
    return bool(entitlements(plan).get(feature))


def max_accounts(plan: str | None) -> int | None:
    return entitlements(plan).get("max_accounts")


def public_entitlements(plan: str | None) -> dict:
    """What the frontend receives so it can draw padlocks and upgrade prompts
    without having to guess at them."""
    ent = entitlements(plan)
    return {"plan": normalize(plan), **ent}
