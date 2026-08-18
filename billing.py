"""
Piani e avvio del pagamento.

I dati della carta non passano MAI da questa app. Nemmeno la chiave segreta
di Stripe: sarebbe compilata dentro l'eseguibile e chiunque potrebbe
rileggerla decomprimendo il binario. La sessione di pagamento la crea il
servizio, che e' anche l'unico a poter stabilire chi ha pagato davvero -
un database dei piani che vive sul computer del cliente non e' una prova
di pagamento.
"""
import requests

# I testi viaggiano come codice + frase italiana di riserva: la pagina dei
# prezzi e' quella che incassa, e mostrarla in italiano a un cliente che ha
# scelto un'altra lingua e' il posto peggiore dove farlo.
#
# NB: nessun piano promette piu' "analisi AI". Quella funzione chiamava un
# modello a pagamento, e' stata sostituita da un'analisi calcolata in locale
# ed e' inclusa ovunque: continuare a venderla come esclusiva a pagamento
# sarebbe una promessa falsa.
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
    """Versione per il frontend: le liste diventano {code, text} cosi'
    l'interfaccia traduce e, se una chiave manca, mostra comunque la frase."""
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
    """Il pagamento e' disponibile se il servizio e' raggiungibile. Non
    dipende piu' da una configurazione locale: nella build del cliente non
    ci sarebbe mai stata, e il pulsante sarebbe stato spento per tutti."""
    return bool(_service_url())


def start_checkout(plan_id: str, billing_cycle: str, user_email: str = "") -> dict:
    """Chiede al servizio la pagina di pagamento per questo piano.

    L'importo lo decide il servizio, non l'app: se lo scegliesse il client,
    chi modifica l'eseguibile potrebbe farsi generare un abbonamento da zero
    euro."""
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
        # Il dettaglio resta nei log per il debug; all'utente arriva un
        # codice, che l'interfaccia mostra nella sua lingua.
        print(f"[billing] checkout failed {resp.status_code}: {resp.text[:200]}")
        return {"ok": False, "message": "checkout_unavailable"}

    url = resp.json().get("url")
    if not url:
        return {"ok": False, "message": "checkout_unavailable"}
    return {"ok": True, "checkout_url": url}
