"""
Reads insights (views/likes/comments/shares/saved) for the latest posts of one
or more Instagram accounts listed in IG_ACCOUNTS (format "Name:PREFIX,...").

There are two families of token, with different domains and different ways of
passing the token - they have to be honoured per account, or the answer is a
401:
  - "facebook": a Page Access Token from the Facebook Login flow (Graph API
    Explorer) -> graph.facebook.com, access_token as a query parameter.
  - "instagram": a token from the direct Instagram Login flow ->
    graph.instagram.com, Bearer header. The user_id here is the IGSID
    (Instagram-scoped ID), which is not the Instagram Business Account ID used
    in the facebook flow.
Which type each account uses is read from {PREFIX}_IG_API in the .env.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import logging
import os
from concurrent.futures import ThreadPoolExecutor

from . import _http

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
    """The accounts to read: those from the .env plus those connected through
    "Connect account". The two routes coexist."""
    sources = [
        {"name": name, "kind": "env", "prefix": prefix}
        for name, prefix in _parse_accounts()
    ]

    import connections
    for conn in connections.list_connections("instagram"):
        data = conn["data"]
        sources.append({
            "name": conn["account_name"], "kind": "oauth",
            "connection_id": conn["id"],
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
        return {"ok": False, "error": f"{prefix}_IG_ACCESS_TOKEN / {prefix}_IG_USER_ID missing"}

    api_base = "https://graph.instagram.com/v21.0" if api_kind == "instagram" else "https://graph.facebook.com/v21.0"
    headers = {"Authorization": f"Bearer {token}"} if api_kind == "instagram" else {}
    base_params = {} if api_kind == "instagram" else {"access_token": token}

    try:
        resp = _http.get(
            f"{api_base}/{ig_user_id}/media",
            headers=headers,
            params={**base_params, "fields": "id,caption,timestamp", "limit": 10},
            timeout=30,
        )
        resp.raise_for_status()
        media_list = resp.json().get("data", [])

        def _fetch_insight(media):
            insights_resp = _http.get(
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

        # Up to 10 HTTP calls per account (one per post) - making them in
        # parallel rather than one at a time is what fixed the Instagram
        # refresh (5 accounts x 10 posts), which was the dashboard's real
        # bottleneck and far slower than it looked.
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
            acc_resp = _http.get(
                f"{api_base}/{ig_user_id}",
                headers=headers,
                params={**base_params, "fields": "followers_count"},
                timeout=15,
            )
            if acc_resp.ok:
                followers = acc_resp.json().get("followers_count")
        except Exception:
            logging.debug("could not fetch the Instagram follower count", exc_info=True)

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

    # Writes to the authorization state happen here, outside the pool: the
    # accounts are queried in parallel but the database is touched by one
    # thread only, in sequence.
    import connections

    accounts_out = []
    for source, result in zip(sources, results):
        errore = None if result.get("ok") else result.get("error")
        connections.record_fetch_outcome(source.get("connection_id"), errore)
        voce = {"name": source["name"], "source": source["kind"], **result}
        if errore and connections.is_auth_failure(str(errore)):
            voce["needs_reauth"] = True
        accounts_out.append(voce)
    return {"platform": "instagram", "accounts": accounts_out}
