"""
X (Twitter): the API's free tier exposes writing only, not reading metrics
(impressions, engagement). All this checks is that the credentials are
present, and it says so plainly rather than letting anyone believe there is
data behind the connection.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
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
