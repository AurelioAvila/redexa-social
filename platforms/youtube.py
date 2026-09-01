"""
Reads public statistics (subscriberCount, viewCount, videoCount) for every
YouTube channel listed in YT_CHANNELS (format "Name:PREFIX,..."), reusing the
same OAuth pattern as solofounded-bot/src/analytics.py. Only the
youtube.readonly scope is needed, already authorized on the existing refresh
tokens - no YouTube Analytics API.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import logging
import os
import time
from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def _service_from_creds(refresh_token: str, client_id: str, client_secret: str, scopes: list[str]):
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )
    return build("youtube", "v3", credentials=creds)


def _service_for(prefix: str):
    # Some existing refresh tokens were issued with a different scope (only
    # youtube.upload, say, or the full "youtube") - the refresh fails with
    # invalid_scope if a scope that was not granted originally is asked for
    # here. Override per channel with {PREFIX}_YOUTUBE_SCOPE in the .env when
    # needed.
    scope = os.environ.get(f"{prefix}_YOUTUBE_SCOPE", "https://www.googleapis.com/auth/youtube.readonly")
    return _service_from_creds(
        os.environ[f"{prefix}_YOUTUBE_REFRESH_TOKEN"],
        os.environ[f"{prefix}_YOUTUBE_CLIENT_ID"],
        os.environ[f"{prefix}_YOUTUBE_CLIENT_SECRET"],
        scope.split(),
    )


def _parse_channels() -> list[tuple[str, str]]:
    raw = os.environ.get("YT_CHANNELS", "")
    out = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry or ":" not in entry:
            continue
        name, prefix = entry.split(":", 1)
        out.append((name.strip(), prefix.strip()))
    return out


def _sources() -> list[dict]:
    """The channels to read: those configured by hand in the .env plus those
    connected with "Connect account" (OAuth sign-in). The two routes coexist,
    so an existing manual setup does not stop working the moment someone
    starts using the automatic connection."""
    sources = [{"name": name, "prefix": prefix, "kind": "env"} for name, prefix in _parse_channels()]

    import connections
    for conn in connections.list_connections("youtube"):
        data = conn["data"]
        sources.append({
            "name": conn["account_name"],
            "kind": "oauth",
            "connection_id": conn["id"],
            "refresh_token": data["refresh_token"],
            "client_id": data["client_id"],
            "client_secret": data["client_secret"],
            "scopes": data.get("scopes") or ["https://www.googleapis.com/auth/youtube.readonly"],
        })
    return sources


def count_units() -> int:
    """How many channels are configured - used for a fine-grained refresh
    progress (one unit of work per channel rather than one for the whole
    platform) instead of a single bar lurching across 5 entries."""
    return len(_sources())


def _fetch_channel(source: dict) -> dict:
    """One read attempt for a single channel - pulled out into a function so
    fetch_stats can retry it once on a transient error (a momentary hiccup
    from Google's token endpoint, say, while several channels or platforms
    refresh in parallel)."""
    if source["kind"] == "oauth":
        youtube = _service_from_creds(
            source["refresh_token"], source["client_id"], source["client_secret"], source["scopes"]
        )
    else:
        youtube = _service_for(source["prefix"])
    name = source["name"]
    resp = youtube.channels().list(part="statistics,snippet", mine=True).execute()
    item = resp["items"][0]
    stats = item["statistics"]

    recent_views = 0
    recent_videos = []
    try:
        uploads = youtube.channels().list(part="contentDetails", mine=True).execute()
        playlist_id = uploads["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        items = youtube.playlistItems().list(part="contentDetails", playlistId=playlist_id, maxResults=10).execute()
        video_ids = [i["contentDetails"]["videoId"] for i in items["items"]]
        if video_ids:
            videos = youtube.videos().list(part="statistics,snippet", id=",".join(video_ids)).execute()
            for v in videos["items"]:
                views = int(v["statistics"].get("viewCount", 0))
                recent_views += views
                published = v["snippet"].get("publishedAt")
                hour = None
                if published:
                    try:
                        hour = datetime.fromisoformat(published.replace("Z", "+00:00")).astimezone(timezone.utc).hour
                    except (TypeError, ValueError):
                        hour = None
                recent_videos.append({
                    "title": v["snippet"].get("title", ""),
                    "published": published,
                    "publish_hour_utc": hour,
                    "views": views,
                    "likes": int(v["statistics"].get("likeCount", 0)),
                    "comments": int(v["statistics"].get("commentCount", 0)),
                })
    except Exception:
        logging.debug("could not fetch recent YouTube videos", exc_info=True)

    return {
        "name": name,
        "title": item["snippet"]["title"],
        "subscribers": int(stats.get("subscriberCount", 0)),
        "total_views": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "recent_views_last10": recent_views,
        "recent_videos": recent_videos,
        "source": source["kind"],
        "ok": True,
    }


def fetch_stats(on_item=None) -> dict:
    import connections

    channels_out = []
    errors = []
    for source in _sources():
        name = source["name"]
        last_exc = None
        result = None
        # Up to 3 attempts with growing backoff - absorbs transient
        # hiccups from Google's token endpoint when several channels or
        # platforms refresh OAuth in parallel (seen in practice on the
        # compiled exe even though it does not reproduce in isolation),
        # rather than flagging the channel as failed after a single momentary
        # failure.
        for attempt, backoff in enumerate((0, 2, 5)):
            if backoff:
                time.sleep(backoff)
            try:
                result = _fetch_channel(source)
                last_exc = None
                break
            except Exception as exc:
                last_exc = exc
        # Record whether the authorization still holds: without this the
        # channel stayed "connected" in the interface even after Google had
        # revoked the token, and the two screens contradicted each other.
        connections.record_fetch_outcome(source.get("connection_id"),
                                         None if result is not None else last_exc)
        if result is not None:
            channels_out.append(result)
        else:
            errors.append(f"{name}: {last_exc}")
            channels_out.append({"name": name, "ok": False, "error": str(last_exc), "source": source["kind"],
                                 "needs_reauth": connections.is_auth_failure(str(last_exc))})
        if on_item:
            on_item()

    return {"platform": "youtube", "channels": channels_out, "errors": errors}
