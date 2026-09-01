"""
Reads video statistics (views/likes/comments/shares) for the TikTok accounts
listed in TT_ACCOUNTS (format "Name:PREFIX,..."), reusing the same
refresh-token flow as solofounded-bot/src/tiktok_upload.py::_get_access_token
but pointed at the read endpoint /video/list/ rather than upload.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import os
from datetime import datetime, timezone

import requests

API_BASE = "https://open.tiktokapis.com/v2"
VIDEO_FIELDS = "id,title,view_count,like_count,comment_count,share_count,create_time"


def _is_configured(prefix: str) -> bool:
    """TT_ACCOUNTS can list an account whose {PREFIX}_TIKTOK_* variables exist
    but are empty (a placeholder never filled in) - without this check TikTok
    makes the call anyway and returns a misleading 401 Unauthorized instead of
    saying plainly that the account is not configured yet."""
    return all(
        os.environ.get(f"{prefix}_TIKTOK_{key}")
        for key in ("CLIENT_KEY", "CLIENT_SECRET", "REFRESH_TOKEN")
    )


def _exchange_refresh(client_key: str, client_secret: str, refresh_token: str) -> str:
    resp = requests.post(
        f"{API_BASE}/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"TikTok refresh token failed: {data}")
    granted_scope = data.get("scope", "")
    if "video.list" not in granted_scope:
        # Known limitation: the TikTok app is authorized for upload and
        # publish only, not for reading statistics - getting the video.list
        # scope needs an App Review on TikTok for Developers. Nothing here can
        # fix it, but it has to be reported clearly rather than as the generic
        # 401 the call to /video/list/ would return.
        raise RuntimeError(
            f"Token is valid but lacks the 'video.list' permission (granted scope: {granted_scope or 'none'}) - "
            "TikTok App Review is required before stats can be read."
        )
    return data["access_token"]


def _get_access_token(prefix: str) -> str:
    return _exchange_refresh(
        os.environ[f"{prefix}_TIKTOK_CLIENT_KEY"],
        os.environ[f"{prefix}_TIKTOK_CLIENT_SECRET"],
        os.environ[f"{prefix}_TIKTOK_REFRESH_TOKEN"],
    )


def _parse_accounts() -> list[tuple[str, str]]:
    raw = os.environ.get("TT_ACCOUNTS", "")
    out = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry or ":" not in entry:
            continue
        name, prefix = entry.split(":", 1)
        out.append((name.strip(), prefix.strip()))
    return out


def _sources() -> list[dict]:
    """Accounts from the .env plus those connected from "Connect account"."""
    sources = [{"name": name, "kind": "env", "prefix": prefix} for name, prefix in _parse_accounts()]

    import connections
    for conn in connections.list_connections("tiktok"):
        data = conn["data"]
        sources.append({
            "name": conn["account_name"], "kind": "oauth",
            "connection_id": conn["id"],
            "refresh_token": data["refresh_token"],
            "client_key": data.get("client_key", ""),
            # Absent when the connection went through the proxy: in that
            # case the secret was never stored here at all.
            "client_secret": data.get("client_secret", ""),
            "via_proxy": bool(data.get("via_proxy")),
        })
    return sources


def _access_token_from(source: dict) -> str:
    if source["kind"] == "env":
        return _get_access_token(source["prefix"])
    if source.get("via_proxy"):
        # The refresh needs the secret too: the endpoint holding it does that.
        import connections
        data = connections.proxy_call("refresh", {
            "platform": "tiktok", "refresh_token": source["refresh_token"],
        })
        granted = data.get("scope", "")
        if "video.list" not in granted:
            raise RuntimeError(
                f"Token is valid but lacks the 'video.list' permission (granted scope: {granted or 'none'}) - "
                "TikTok App Review is required before stats can be read."
            )
        return data["access_token"]
    return _exchange_refresh(source["client_key"], source["client_secret"], source["refresh_token"])


def count_units() -> int:
    return len(_sources())


def _fetch_follower_count(access_token: str) -> int | None:
    """The follower count, so engagement can be compared against industry
    averages (which are expressed as a percentage of followers).

    Never raises: it is a secondary figure, and an account that does not
    expose it still has to return its video statistics. Uses the
    user.info.stats scope, already requested when connecting - no new
    authorization to ask the user for.
    """
    try:
        resp = requests.get(
            f"{API_BASE}/user/info/",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"fields": "follower_count"},
            timeout=15,
        )
        if not resp.ok:
            return None
        return resp.json().get("data", {}).get("user", {}).get("follower_count")
    except Exception:
        return None


def fetch_stats(limit: int = 10, on_item=None) -> dict:
    import connections

    accounts_out = []
    errors = []
    for source in _sources():
        name = source["name"]
        try:
            if source["kind"] == "env" and not _is_configured(source["prefix"]):
                accounts_out.append({
                    "name": name, "ok": False, "not_configured": True,
                    "error": f"TikTok is not connected yet - link the account from the Link account page.",
                })
                continue
            access_token = _access_token_from(source)
            resp = requests.post(
                f"{API_BASE}/video/list/",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                params={"fields": VIDEO_FIELDS},
                json={"max_count": limit},
                timeout=30,
            )
            resp.raise_for_status()
            videos = resp.json().get("data", {}).get("videos", [])
            followers = _fetch_follower_count(access_token)

            totals = {"views": 0, "likes": 0, "comments": 0, "shares": 0}
            for v in videos:
                totals["views"] += v.get("view_count", 0)
                totals["likes"] += v.get("like_count", 0)
                totals["comments"] += v.get("comment_count", 0)
                totals["shares"] += v.get("share_count", 0)

            accounts_out.append({
                "name": name,
                "ok": True,
                "followers": followers,
                "video_count": len(videos),
                "totals_last_n": totals,
                "recent_videos": [
                    {
                        "id": v.get("id"), "title": v.get("title", "")[:60],
                        "views": v.get("view_count", 0), "likes": v.get("like_count", 0),
                        "comments": v.get("comment_count", 0), "shares": v.get("share_count", 0),
                        "create_time": v.get("create_time"),
                        "publish_hour_utc": (
                            datetime.fromtimestamp(v["create_time"], tz=timezone.utc).hour
                            if v.get("create_time") else None
                        ),
                    }
                    for v in videos
                ],
            })
            connections.record_fetch_outcome(source.get("connection_id"), None)
        except Exception as exc:
            errors.append(f"{name}: {exc}")
            connections.record_fetch_outcome(source.get("connection_id"), exc)
            accounts_out.append({"name": name, "ok": False, "error": str(exc),
                                 "needs_reauth": connections.is_auth_failure(str(exc))})
        finally:
            if on_item:
                on_item()

    return {"platform": "tiktok", "accounts": accounts_out, "errors": errors}
