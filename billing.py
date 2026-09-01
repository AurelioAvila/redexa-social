"""
Plans, and starting a payment.

Card details NEVER pass through this app. Neither does the Stripe secret key:
it would be compiled into the executable and anyone could read it back by
unpacking the binary. The payment session is created by the service, which is
also the only thing that can establish who actually paid - a plans database
living on the customer's computer is not proof of payment.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import requests

# The copy travels as a code plus a fallback sentence: the pricing page is
# the one that takes money, and showing it in the wrong language to a customer
# who picked another one is the worst possible place to do that.
#
# Note: no plan promises "AI analysis" any more. That feature called a paid
# model, it was replaced by an analysis computed locally, and it is included
# everywhere: going on selling it as a paid exclusive would be a false
# promise.
PLANS = [
    {
        "id": "free",
        "name": "Free",
        "price_monthly": 0,
        "price_yearly": 0,
        "tagline_code": "plan_free_tagline",
        "tagline": "To get started and understand your numbers.",
        "accounts_code": "plan_free_accounts",
        "accounts": "1 linked account",
        "features": [
            ("plan_feat_all_socials", "Stats for every supported social network"),
            ("plan_feat_manual_refresh", "Manual on-demand refresh"),
            ("plan_feat_analytics", "Analytics: top posts and time slots"),
            ("plan_feat_diagnostics", "Automatic error diagnostics"),
            ("plan_feat_insights", "Automatic observations on your content"),
        ],
        "missing": [
            ("plan_feat_history", "Full history with trend charts"),
            ("plan_feat_reports", "Automated reports"),
        ],
    },
    {
        "id": "pro",
        "name": "Pro",
        "price_monthly": 12,
        "price_yearly": 120,
        "tagline_code": "plan_pro_tagline",
        "tagline": "For those posting daily who want to grow.",
        "accounts_code": "plan_pro_accounts",
        "accounts": "3 linked accounts",
        "popular": True,
        "features": [
            ("plan_feat_all_free", "Everything in Free"),
            ("plan_feat_history", "Full history with trend charts"),
            ("plan_feat_compare", "Period comparison and drop alerts"),
            ("plan_feat_hours", "Publishing time suggestions"),
            ("plan_feat_csv", "CSV data export"),
        ],
        "missing": [],
    },
    {
        "id": "studio",
        "name": "Studio",
        "price_monthly": 39,
        "price_yearly": 390,
        "tagline_code": "plan_studio_tagline",
        "tagline": "For agencies and multi-brand managers.",
        "accounts_code": "plan_studio_accounts",
        "accounts": "10 linked accounts",
        "features": [
            ("plan_feat_all_pro", "Everything in Pro"),
            ("plan_feat_workspaces", "Separate workspaces per client"),
            ("plan_feat_whitelabel", "Automated white-label PDF reports"),
            ("plan_feat_multiuser", "Multi-user team access"),
            ("plan_feat_priority", "Priority support"),
        ],
        "missing": [],
    },
]


def _public_plan(plan: dict) -> dict:
    """The frontend's version: the lists become {code, text} so the interface
    can translate and, when a key is missing, still show the sentence."""
    out = {k: v for k, v in plan.items() if k not in ("features", "missing")}
    for key in ("features", "missing"):
        out[key] = [{"code": c, "text": txt} for c, txt in plan.get(key, [])]
    return out

PLANS_BY_ID = {p["id"]: p for p in PLANS}


def list_plans() -> dict:
    return {
        "plans": [_public_plan(p) for p in PLANS],
        "checkout_ready": checkout_ready(),
        "currency": "EUR",
    }


def _service_url() -> str:
    import brand

    return (brand.get("OAUTH_PROXY_URL") or "").rstrip("/")


def checkout_ready() -> bool:
    """Payment is available when the service is reachable. It no longer depends
    on any local configuration: in the customer's build there would never
    have been one, and the button would have been dead for everybody."""
    return bool(_service_url())


def start_checkout(plan_id: str, billing_cycle: str, user_email: str = "") -> dict:
    """Asks the service for the payment page for this plan.

    The amount is decided by the service, not the app: if the client chose it,
    anyone editing the executable could have a zero-euro subscription
    generated for themselves."""
    plan = PLANS_BY_ID.get(plan_id)
    if not plan or plan_id == "free":
        return {"ok": False, "message": "plan_unknown"}

    base = _service_url()
    if not base:
        return {"ok": False, "message": "checkout_unavailable"}

    try:
        resp = requests.post(
            f"{base}/checkout",
            json={
                "plan": plan_id,
                "cycle": "yearly" if billing_cycle == "yearly" else "monthly",
                "email": user_email,
            },
            timeout=30,
        )
    except Exception:
        return {"ok": False, "message": "checkout_unavailable"}

    if not resp.ok:
        # The detail stays in the logs for debugging; the user gets a code,
        # which the interface renders in their own language.
        print(f"[billing] checkout failed {resp.status_code}: {resp.text[:200]}")
        return {"ok": False, "message": "checkout_unavailable"}

    url = resp.json().get("url")
    if not url:
        return {"ok": False, "message": "checkout_unavailable"}
    return {"ok": True, "checkout_url": url}
