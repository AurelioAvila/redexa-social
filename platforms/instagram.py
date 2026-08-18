"""
Legge insight (views/likes/comments/shares/saved) degli ultimi post per uno
o piu' account Instagram elencati in IG_ACCOUNTS (formato "Nome:PREFIX,...").

Esistono due famiglie di token, con dominio e modo di passare il token
diversi - vanno rispettati per account, altrimenti 401:
  - "facebook": Page Access Token dal flusso Facebook Login (Graph API
    Explorer) -> graph.facebook.com, access_token come query param.
  - "instagram": token dal flusso Instagram Login diretto -> graph.instagram.com,
    Bearer header. Lo user_id qui e' l'IGSID (Instagram-scoped ID), diverso
    dall'Instagram Business Account ID usato nel flusso facebook.
Il tipo per ciascun account e' letto da {PREFIX}_IG_API in .env.
"""
import os
from concurrent.futures import ThreadPoolExecutor

import requests

METRICS = "views,reach,likes,comments,shares,saved,total_interactions"


def _parse_accounts() -> list[tuple[str, str]]:
    raw = os.environ.get("IG_ACCOUNTS", "")
    out = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry or ":" not in entry:
            continue
        name, prefix = entry.split(":", 1)
        out.append((name.strip(), prefix.strip()))
    return out


def _sources() -> list[dict]:
    """Account da leggere: quelli del .env piu' quelli collegati dalla
    sezione "Collega account". Le due strade convivono."""
    sources = [
        {"name": name, "kind": "env", "prefix": prefix}
        for name, prefix in _parse_accounts()
    ]

    import connections
    for conn in connections.list_connections("instagram"):
        data = conn["data"]
        sources.append({
            "name": conn["account_name"], "kind": "oauth",
            "token": data["access_token"], "user_id": data["user_id"],
            "api_kind": data.get("api_kind", "instagram"),
        })
    return sources


def _fetch_source(source: dict) -> dict:
    if source["kind"] == "oauth":
        return _fetch_one(None, source["token"], source["user_id"], source["api_kind"])
    prefix = source["prefix"]
    return _fetch_one(
        prefix,
        os.environ.get(f"{prefix}_IG_ACCESS_TOKEN"),
        os.environ.get(f"{prefix}_IG_USER_ID"),
        os.environ.get(f"{prefix}_IG_API", "facebook"),
    )


def _fetch_one(prefix: str | None, token: str | None, ig_user_id: str | None, api_kind: str) -> dict:
    if not token or not ig_user_id:
        return {"ok": False, "error": f"{prefix}_IG_ACCESS_TOKEN / {prefix}_IG_USER_ID mancanti"}

    api_base = "https://graph.instagram.com/v21.0" if api_kind == "instagram" else "https://graph.facebook.com/v21.0"
    headers = {"Authorization": f"Bearer {token}"} if api_kind == "instagram" else {}
    base_params = {} if api_kind == "instagram" else {"access_token": token}

    try:
        resp = requests.get(
            f"{api_base}/{ig_user_id}/media",
            headers=headers,
            params={**base_params, "fields": "id,caption,timestamp", "limit": 10},
            timeout=30,
        )
        resp.raise_for_status()
        media_list = resp.json().get("data", [])

        def _fetch_insight(media):
            insights_resp = requests.get(
                f"{api_base}/{media['id']}/insights",
                headers=headers,
                params={**base_params, "metric": METRICS},
                timeout=30,
            )
            if not insights_resp.ok:
                return None
            values = {i["name"]: (i.get("values") or [{}])[0].get("value", 0) for i in insights_resp.json().get("data", [])}
            return {
                "id": media["id"],
                "caption": (media.get("caption") or "").split("\n")[0][:60],
                "timestamp": media.get("timestamp"),
                **values,
            }

        # Fino a 10 chiamate HTTP per account (una per post) - farle in
        # parallelo invece che una alla volta e' cio' che ha reso il
        # refresh Instagram (5 account x 10 post) il vero collo di
        # bottiglia della dashboard, molto piu' lento di quanto sembrasse.
        with ThreadPoolExecutor(max_workers=10) as pool:
            post_results = list(pool.map(_fetch_insight, media_list))

        posts = []
        totals = {"views": 0, "likes": 0, "comments": 0, "shares": 0, "saved": 0}
        for post in post_results:
            if post is None:
                continue
            for k in totals:
                totals[k] += post.get(k, 0)
            posts.append(post)

        followers = None
        try:
            acc_resp = requests.get(
                f"{api_base}/{ig_user_id}",
                headers=headers,
                params={**base_params, "fields": "followers_count"},
                timeout=15,
            )
            if acc_resp.ok:
                followers = acc_resp.json().get("followers_count")
        except Exception:
            pass

        return {"ok": True, "followers": followers, "recent_posts": posts, "totals_last_n": totals}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def count_units() -> int:
    return len(_sources())


def fetch_stats(on_item=None) -> dict:
    sources = _sources()

    def _one(source):
        try:
            return _fetch_source(source)
        finally:
            if on_item:
                on_item()

    with ThreadPoolExecutor(max_workers=max(len(sources), 1)) as pool:
        results = list(pool.map(_one, sources))
    accounts_out = [
        {"name": source["name"], "source": source["kind"], **result}
        for source, result in zip(sources, results)
    ]
    return {"platform": "instagram", "accounts": accounts_out}
