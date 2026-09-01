"""
Statistical analysis computed from previously collected data (zero external
calls, zero cost): top posts by views and the publishing time slot with the
best average performance, by platform and overall. It answers "which posts
work, and when should I publish them?" without requesting AI analysis each time.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import benchmarks


def _num(valore) -> float:
    """Return a usable number regardless of the input received.

    Data is saved to disk as JSON and read back. A single row corrupted by
    an interrupted write, or a platform changing a field's type (YouTube,
    for example, sends statistics as strings), is enough for a ">" comparison
    between str and int to crash the entire Overview page. Here, unexpected
    data becomes zero and processing continues, as cache.py already does for
    unreadable rows.
    """
    if valore is None or isinstance(valore, bool):
        return 0.0
    try:
        n = float(valore)
    except (TypeError, ValueError):
        return 0.0
    # inf and NaN pass through float() and json.loads (which accepts Infinity
    # and NaN): if they reached this point, every subsequent rounding
    # operation would fail.
    if n != n or n in (float("inf"), float("-inf")):
        return 0.0
    return n


def _lista(valore) -> list:
    """Iterate only over lists: a dictionary or string in place of a list
    would eventually lead to calling `.get()` on a character."""
    return valore if isinstance(valore, list) else []


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
        testo = str(iso_or_epoch).replace("Z", "+00:00")
        return datetime.fromisoformat(testo).weekday()
    except (ValueError, TypeError, OSError, OverflowError):
        return None


def _youtube_items(data: dict) -> list[dict]:
    if not data:
        return []
    out = []
    for c in _lista(data.get("channels")):
        if not isinstance(c, dict) or not c.get("ok"):
            continue
        for v in _lista(c.get("recent_videos")):
            if not isinstance(v, dict):
                continue
            likes = _num(v.get("likes"))
            comments = _num(v.get("comments"))
            views = _num(v.get("views"))
            out.append({
                "platform": "youtube", "account": c.get("name", ""), "title": v.get("title", ""),
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
    for a in _lista(data.get("accounts")):
        if not isinstance(a, dict) or not a.get("ok"):
            continue
        for p in _lista(a.get("recent_posts")):
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
                "title": p.get("caption", "(senza didascalia)"),
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
    for a in _lista(data.get("accounts")):
        if not isinstance(a, dict) or not a.get("ok"):
            continue
        for v in _lista(a.get("recent_videos")):
            if not isinstance(v, dict):
                continue
            likes = _num(v.get("likes"))
            comments = _num(v.get("comments"))
            shares = _num(v.get("shares"))
            views = _num(v.get("views"))
            out.append({
                "platform": "tiktok", "account": a.get("name", ""), "title": v.get("title", ""),
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

    canali = _lista((snapshot.get("youtube") or {}).get("channels"))
    iscritti = [_num(c.get("subscribers")) for c in canali
                if isinstance(c, dict) and c.get("ok")]
    if any(iscritti):
        out["youtube"] = int(sum(iscritti))

    for piattaforma in ("instagram", "tiktok"):
        conti = _lista((snapshot.get(piattaforma) or {}).get("accounts"))
        valori = [_num(a.get("followers")) for a in conti
                  if isinstance(a, dict) and a.get("ok")]
        if any(valori):
            out[piattaforma] = int(sum(valori))

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
    interazioni = sum(i.get("interactions", 0) or 0 for i in items)
    salvataggi = sum(i.get("saved", 0) or 0 for i in items)
    condivisioni = sum(i.get("shares", 0) or 0 for i in items)
    return {
        "rate": round(interazioni / base * 100, 2),
        "save_rate": round(salvataggi / base * 100, 2),
        "share_rate": round(condivisioni / base * 100, 2),
        "interactions": interazioni,
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
    celle = {}
    for item in rated:
        if item.get("weekday") is None:
            continue
        chiave = (item["weekday"], item["hour"])
        c = celle.setdefault(chiave, {"views": 0, "count": 0})
        c["views"] += item["views"]
        c["count"] += 1
    heatmap = [
        {"weekday": g, "hour": o, "avg_views": round(c["views"] / c["count"]), "count": c["count"]}
        for (g, o), c in sorted(celle.items())
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
    confronti = []
    for piattaforma in per_platform:
        contenuti = [i for i in all_items if i["platform"] == piattaforma]
        misura = _engagement(contenuti)
        if not misura:
            continue
        # Follower-based engagement is the definition used by industry reports,
        # unlike the reach-based figure calculated above. It is used only for
        # benchmark comparisons and does not replace the other measure.
        seguaci = followers.get(piattaforma)
        if seguaci and contenuti:
            interazioni = sum(i.get("interactions", 0) or 0 for i in contenuti)
            misura["follower_rate"] = round(
                interazioni / (len(contenuti) * seguaci) * 100, 2)
            confronto = benchmarks.compare(piattaforma, seguaci, misura["follower_rate"])
            if confronto:
                confronti.append(confronto)
        engagement_per_platform[piattaforma] = misura

    total_views = sum(i["views"] for i in all_items)
    with_views = [i for i in all_items if i["views"] > 0]

    # Posts above and below their own average: the useful comparison is with
    # past performance, not an industry average that knows nothing about this
    # audience. A minimum sample is required, or "above average" is mere chance.
    outliers = {"over": [], "under": []}
    if len(with_views) >= 4:
        media = total_views / len(with_views)
        if media > 0:
            ordinati = sorted(with_views, key=lambda i: i["views"], reverse=True)
            for voce in ordinati:
                scarto = round((voce["views"] - media) / media * 100)
                riga = {"platform": voce["platform"], "account": voce["account"],
                        "title": voce["title"], "views": voce["views"], "delta_pct": scarto}
                if scarto >= 50 and len(outliers["over"]) < 5:
                    outliers["over"].append(riga)
                elif scarto <= -50:
                    outliers["under"].append(riga)
            outliers["under"] = outliers["under"][-5:]
            outliers["avg"] = round(media)

    return {
        "engagement": engagement,
        "engagement_per_platform": engagement_per_platform,
        "followers_per_platform": followers,
        "benchmarks": confronti,
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
