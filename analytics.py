"""
Statistical analysis computed from previously collected data (zero external
calls, zero cost): top posts by views and the publishing time slot with the
best average performance, by platform and overall. It answers "which posts
work, and when should I publish them?" without requesting AI analysis each time.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import benchmarks


def _num(value) -> float:
    """Return a usable number regardless of the input received.

    Data is saved to disk as JSON and read back. A single row corrupted by
    an interrupted write, or a platform changing a field's type (YouTube,
    for example, sends statistics as strings), is enough for a ">" comparison
    between str and int to crash the entire Overview page. Here, unexpected
    data becomes zero and processing continues, as cache.py already does for
    unreadable rows.
    """
    if value is None or isinstance(value, bool):
        return 0.0
    try:
        n = float(value)
    except (TypeError, ValueError):
        return 0.0
    # inf and NaN pass through float() and json.loads (which accepts Infinity
    # and NaN): if they reached this point, every subsequent rounding
    # operation would fail.
    if n != n or n in (float("inf"), float("-inf")):
        return 0.0
    return n


def _as_list(value) -> list:
    """Iterate only over lists: a dictionary or string in place of a list
    would eventually lead to calling `.get()` on a character."""
    return value if isinstance(value, list) else []


def _weekday(iso_or_epoch) -> int | None:
    """0 = Monday, 6 = Sunday. None if the date is missing or unreadable.

    Used for the day-by-hour map: knowing that performance peaks "at 18:00"
    is far less useful than knowing "Tuesday at 18:00," yet the day was
    previously discarded even though all three platforms provide it.
    """
    from datetime import datetime, timezone

    if iso_or_epoch in (None, ""):
        return None
    try:
        if isinstance(iso_or_epoch, (int, float)):
            return datetime.fromtimestamp(iso_or_epoch, tz=timezone.utc).weekday()
        text = str(iso_or_epoch).replace("Z", "+00:00")
        return datetime.fromisoformat(text).weekday()
    except (ValueError, TypeError, OSError, OverflowError):
        return None


def _youtube_items(data: dict) -> list[dict]:
    if not data:
        return []
    out = []
    for c in _as_list(data.get("channels")):
        if not isinstance(c, dict) or not c.get("ok"):
            continue
        for v in _as_list(c.get("recent_videos")):
            if not isinstance(v, dict):
                continue
            likes = _num(v.get("likes"))
            comments = _num(v.get("comments"))
            views = _num(v.get("views"))
            out.append({
                "platform": "youtube", "account": c.get("name", ""), "title": v.get("title", ""),
                "followers": _num(c.get("subscribers")),
                "views": views, "hour": v.get("publish_hour_utc"),
                "weekday": _weekday(v.get("published")),
                # YouTube exposes neither saves nor shares with the read-only
                # scope, so they remain zero rather than being fabricated.
                "likes": likes, "comments": comments, "shares": 0, "saved": 0,
                "interactions": likes + comments,
                # Impressions are unavailable without the YouTube Analytics
                # API (which requires separate authorization), so views are
                # the basis for engagement comparisons.
                "reach": views,
            })
    return out


def _instagram_items(data: dict) -> list[dict]:
    if not data:
        return []
    out = []
    for a in _as_list(data.get("accounts")):
        if not isinstance(a, dict) or not a.get("ok"):
            continue
        for p in _as_list(a.get("recent_posts")):
            if not isinstance(p, dict):
                continue
            hour = None
            ts = p.get("timestamp")
            if ts:
                try:
                    hour = int(str(ts)[11:13])
                except (ValueError, TypeError):
                    hour = None
            likes = _num(p.get("likes"))
            comments = _num(p.get("comments"))
            shares = _num(p.get("shares"))
            saved = _num(p.get("saved"))
            views = _num(p.get("views"))
            # Meta provides total_interactions already summed. Use it when
            # available so interactions counted by the API but not listed
            # here (such as replies) are not lost.
            interactions = _num(p.get("total_interactions"))
            if not interactions:
                interactions = likes + comments + shares + saved
            out.append({
                "platform": "instagram", "account": a.get("name", ""),
                "followers": _num(a.get("followers")),
                "title": p.get("caption", "(no caption)"),
                "views": views, "hour": hour,
                "weekday": _weekday(ts),
                "likes": likes, "comments": comments, "shares": shares, "saved": saved,
                "interactions": interactions,
                # reach = unique accounts reached, the correct basis for
                # Instagram engagement. Fall back to views when unavailable.
                "reach": _num(p.get("reach")) or views,
            })
    return out


def _tiktok_items(data: dict) -> list[dict]:
    if not data:
        return []
    out = []
    for a in _as_list(data.get("accounts")):
        if not isinstance(a, dict) or not a.get("ok"):
            continue
        for v in _as_list(a.get("recent_videos")):
            if not isinstance(v, dict):
                continue
            likes = _num(v.get("likes"))
            comments = _num(v.get("comments"))
            shares = _num(v.get("shares"))
            views = _num(v.get("views"))
            out.append({
                "platform": "tiktok", "account": a.get("name", ""), "title": v.get("title", ""),
                "followers": _num(a.get("followers")),
                "views": views, "hour": v.get("publish_hour_utc"),
                "weekday": _weekday(v.get("create_time")),
                # TikTok does not expose saves through read scopes.
                "likes": likes, "comments": comments, "shares": shares, "saved": 0,
                "interactions": likes + comments + shares,
                "reach": views,
            })
    return out


def _followers_by_platform(snapshot: dict) -> dict:
    """Total followers by platform, summed across linked accounts.

    Used for comparison with industry averages, which are expressed as a
    percentage of followers. Platforms that do not expose follower counts
    are omitted rather than shown as zero, which would distort every ratio.
    """
    out = {}

    channels = _as_list((snapshot.get("youtube") or {}).get("channels"))
    subscribers = [_num(c.get("subscribers")) for c in channels
                if isinstance(c, dict) and c.get("ok")]
    if any(subscribers):
        out["youtube"] = int(sum(subscribers))

    for platform in ("instagram", "tiktok"):
        account_list = _as_list((snapshot.get(platform) or {}).get("accounts"))
        values = [_num(a.get("followers")) for a in account_list
                  if isinstance(a, dict) and a.get("ok")]
        if any(values):
            out[platform] = int(sum(values))

    return out


def _engagement(items: list[dict]) -> dict | None:
    """Measure how much viewers actually interact with content.

    Calculate it from reach (or views where reach is unavailable), not the
    number of posts: ten posts with one thousand views and one with ten
    thousand should be weighted by the audiences they actually reached.
    """
    base = sum(i.get("reach", 0) or 0 for i in items)
    if base <= 0:
        return None
    interaction_total = sum(i.get("interactions", 0) or 0 for i in items)
    saves = sum(i.get("saved", 0) or 0 for i in items)
    share_count = sum(i.get("shares", 0) or 0 for i in items)
    return {
        "rate": round(interaction_total / base * 100, 2),
        "save_rate": round(saves / base * 100, 2),
        "share_rate": round(share_count / base * 100, 2),
        "interactions": interaction_total,
        "reach": base,
        "items": len(items),
    }


# A "best time slot" derived from a single post is not analysis: it is that
# post. Below these thresholds, the app reports insufficient data instead
# of displaying a number that looks like advice.
MIN_ITEMS_FOR_HOURS = 6      # total posts with a time and views
MIN_SAMPLES_PER_HOUR = 2     # posts within an individual time slot


def compute_analytics(snapshot: dict) -> dict:
    all_items = (
        _youtube_items(snapshot.get("youtube"))
        + _instagram_items(snapshot.get("instagram"))
        + _tiktok_items(snapshot.get("tiktok"))
    )

    top_posts = sorted(all_items, key=lambda i: i["views"], reverse=True)[:10]

    # Posts still at zero views reveal nothing about timing. Including them
    # in the average lowers every slot uniformly and makes the hour of the
    # only successful post appear "best."
    rated = [i for i in all_items if i["hour"] is not None and i["views"] > 0]

    hour_buckets = {}  # hour -> {"views": total, "count": n}
    for item in rated:
        b = hour_buckets.setdefault(item["hour"], {"views": 0, "count": 0})
        b["views"] += item["views"]
        b["count"] += 1

    hourly = [
        {"hour": h, "avg_views": round(b["views"] / b["count"]), "count": b["count"]}
        for h, b in hour_buckets.items()
    ]
    hourly.sort(key=lambda h: h["avg_views"], reverse=True)

    # Recommend a slot only when it is supported by more than one post and
    # there is enough data overall.
    enough = len(rated) >= MIN_ITEMS_FOR_HOURS
    reliable = [h for h in hourly if h["count"] >= MIN_SAMPLES_PER_HOUR] if enough else []

    # Include all 24 hours, even those with no posts, for the daily chart.
    # A gap is informative (nothing was ever posted then), just like a tall bar.
    by_hour = {h["hour"]: h for h in hourly}
    all_hours = [
        by_hour.get(h, {"hour": h, "avg_views": 0, "count": 0})
        for h in range(24)
    ]

    # Day-by-hour map: "Tuesday at 18:00" is useful advice; "at 18:00" alone
    # is much less so. Keep only cells with at least one post: an entirely
    # empty 7x24 grid conveys no information.
    cells = {}
    for item in rated:
        if item.get("weekday") is None:
            continue
        cell_key = (item["weekday"], item["hour"])
        c = cells.setdefault(cell_key, {"views": 0, "count": 0})
        c["views"] += item["views"]
        c["count"] += 1
    heatmap = [
        {"weekday": g, "hour": o, "avg_views": round(c["views"] / c["count"]), "count": c["count"]}
        for (g, o), c in sorted(cells.items())
    ]

    per_platform = {}
    for item in all_items:
        p = per_platform.setdefault(item["platform"], {"views": 0, "count": 0})
        p["views"] += item["views"]
        p["count"] += 1

    # Overall and per-platform engagement, using data already downloaded and
    # previously discarded. Until now, only views were examined, while likes,
    # comments, shares, and saves arrived with every API refresh and were ignored.
    engagement = _engagement(all_items)
    followers = _followers_by_platform(snapshot)
    engagement_per_platform = {}
    comparisons = []
    for platform in per_platform:
        posts = [i for i in all_items if i["platform"] == platform]
        measure = _engagement(posts)
        if not measure:
            continue
        # Follower-based engagement is the definition used by industry reports,
        # unlike the reach-based figure calculated above. It is used only for
        # benchmark comparisons and does not replace the other measure.
        # Each post belongs to one audience. Multiplying all posts by all
        # linked followers artificially lowers engagement as accounts are added.
        if posts and all(i["followers"] > 0 for i in posts):
            interaction_total = sum(i.get("interactions", 0) or 0 for i in posts)
            measure["follower_rate"] = round(
                interaction_total / sum(i["followers"] for i in posts) * 100, 2)
            accounts = _as_list((snapshot.get(platform) or {}).get(
                "channels" if platform == "youtube" else "accounts"))
            active_accounts = [a for a in accounts if isinstance(a, dict) and a.get("ok")]
            # Industry tiers describe a single account, not a pooled audience.
            comparison = benchmarks.compare(
                platform, posts[0]["followers"], measure["follower_rate"]
            ) if len(active_accounts) == 1 else None
            if comparison:
                comparisons.append(comparison)
        engagement_per_platform[platform] = measure

    total_views = sum(i["views"] for i in all_items)
    with_views = [i for i in all_items if i["views"] > 0]

    # Posts above and below their own average: the useful comparison is with
    # past performance, not an industry average that knows nothing about this
    # audience. A minimum sample is required, or "above average" is mere chance.
    outliers = {"over": [], "under": []}
    if len(with_views) >= 4:
        mean_views = total_views / len(with_views)
        if mean_views > 0:
            ordered = sorted(with_views, key=lambda i: i["views"], reverse=True)
            for entry in ordered:
                deviation = round((entry["views"] - mean_views) / mean_views * 100)
                row = {"platform": entry["platform"], "account": entry["account"],
                        "title": entry["title"], "views": entry["views"], "delta_pct": deviation}
                if deviation >= 50 and len(outliers["over"]) < 5:
                    outliers["over"].append(row)
                elif deviation <= -50:
                    outliers["under"].append(row)
            outliers["under"] = outliers["under"][-5:]
            outliers["avg"] = round(mean_views)

    return {
        "engagement": engagement,
        "engagement_per_platform": engagement_per_platform,
        "followers_per_platform": followers,
        "benchmarks": comparisons,
        "heatmap": heatmap,
        "outliers": outliers,
        "top_posts": top_posts,
        "best_hours": reliable[:5],
        "all_hours": all_hours,
        "per_platform": per_platform,
        "total_views": total_views,
        "total_items_analyzed": len(all_items),
        # Number of posts that actually contain data. An average calculated
        # across all posts (including those at zero) is mathematically correct
        # but communicates something different from what it appears to mean.
        "items_with_views": len(with_views),
        "avg_views_per_item": round(total_views / len(with_views)) if with_views else 0,
        # The frontend uses these values to report "more data needed" instead
        # of displaying a fabricated time slot.
        "hours_enough_data": bool(reliable),
        "hours_items_needed": max(0, MIN_ITEMS_FOR_HOURS - len(rated)),
    }
