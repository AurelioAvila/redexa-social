"""
X (Twitter): il piano free dell'API espone solo la scrittura, non la
lettura di metriche (impressions/engagement). Qui verifichiamo solo che
le credenziali siano presenti e mostriamo un avviso esplicito, per non far
credere di avere dati che non esistono.
"""
import os


def count_units() -> int:
    return 1


def fetch_stats(on_item=None) -> dict:
    has_creds = all(os.environ.get(k) for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"))
    if on_item:
        on_item()
    return {
        "platform": "x",
        "ok": has_creds,
        "limitation": "X's free API tier doesn't expose read metrics (impressions/engagement). "
                       "Only publishing is automated; this section just shows credential status.",
        "credentials_configured": has_creds,
    }
