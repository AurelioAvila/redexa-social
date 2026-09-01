"""
Statistical analysis computed in code over data already collected (no external
calls, no cost) - top posts by views, and the publishing window with the best
average performance, per platform and overall. It exists to answer "which
posts work and when should I publish them" without paying for an AI analysis
every time.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import benchmarks


def _num(valore) -> float:
    """A usable number, whatever turned up.

    The data goes through JSON written to disk and read back: one row spoiled
    by an interrupted write, or a platform changing a field's type (YouTube
    sends its statistics as strings, for instance), is enough for a ">"
    comparison between str and int to blow up the whole Overview page. Here
    the odd value becomes zero and things carry on, the way cache.py already
    handles unreadable rows.
    """
    if valore is None or isinstance(valore, bool):
        return 0.0
    try:
        n = float(valore)
    except (TypeError, ValueError):
        return 0.0
    # inf and NaN pass through float() and through json.loads untouched
    # (which accepts Infinity and NaN): reaching this far, they would break
    # every rounding that follows.
    if n != n or n in (float("inf"), float("-inf")):
        return 0.0
    return n


def _lista(valore) -> list:
    """Only lists are iterated: a dict or a string where a list was expected
    would get as far as calling `.get()` on a character."""
    return valore if isinstance(valore, list) else []


def _weekday(iso_or_epoch) -> int | None:
    """0 = Monday, 6 = Sunday. None when the date is absent or unreadable.

    Needed for the day-by-hour map: knowing you do better "at 18:00" is far
    less useful than knowing "on Tuesdays at 18:00", and until now the day was
    being thrown away even though all three platforms send it.
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
                # YouTube exposes neither saves nor shares under the
                # readonly scope: they stay at zero rather than invented.
                "likes": likes, "comments": comments, "shares": 0, "saved": 0,
                "interactions": likes + comments,
                # Impressions are not available without the YouTube
                # Analytics API (a different authorization): views are the
                # base engagement is measured against.
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
            # total_interactions arrives already summed from Meta: use it
            # when it is there, so the interactions the API counts and we do
            # not enumerate (replies, for one) are not lost.
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
                # reach = unique accounts reached, the correct base for
                # engagement on Instagram. Falls back to views when absent.
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
                # TikTok does not expose saves under the read scopes.
                "likes": likes, "comments": comments, "shares": shares, "saved": 0,
                "interactions": likes + comments + shares,
                "reach": views,
            })
    return out


def _followers_by_platform(snapshot: dict) -> dict:
    """Total followers per platform, summed across the connected accounts.

    Needed for the comparison against industry averages, which are expressed
    as a percentage of followers. Platforms that do not expose them are left
    out rather than appearing as a zero that would skew every ratio.
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
    """How much the people who see something actually engage with it.

    Computed over reach (or views where reach does not exist) rather than over
    the number of posts: ten posts at a thousand views and one at ten thousand
    have to count for what they genuinely reached.
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


# A "best time to post" derived from a single post is not an analysis: it is
# that post. Below these thresholds the app says the data is not enough,
# rather than printing a number that looks like advice.
MIN_ITEMS_FOR_HOURS = 6      # contenuti con orario e views, in totale
MIN_SAMPLES_PER_HOUR = 2     # contenuti dentro la singola fascia


def compute_analytics(snapshot: dict) -> dict:
    all_items = (
        _youtube_items(snapshot.get("youtube"))
        + _instagram_items(snapshot.get("instagram"))
        + _tiktok_items(snapshot.get("tiktok"))
    )

    top_posts = sorted(all_items, key=lambda i: i["views"], reverse=True)[:10]

    # Content still at zero views says nothing about timing: keeping it in
    # the average drags every slot down uniformly and makes the hour of the
    # one post that did well look "best" for no other reason.
    rated = [i for i in all_items if i["hour"] is not None and i["views"] > 0]

    hour_buckets = {}  # hour -> {"views": totale, "count": n}
    for item in rated:
        b = hour_buckets.setdefault(item["hour"], {"views": 0, "count": 0})
        b["views"] += item["views"]
        b["count"] += 1

    hourly = [
        {"hour": h, "avg_views": round(b["views"] / b["count"]), "count": b["count"]}
        for h, b in hour_buckets.items()
    ]
    hourly.sort(key=lambda h: h["avg_views"], reverse=True)

    # A slot is offered as advice only when it rests on more than one piece
    # of content and there is enough material overall.
    enough = len(rated) >= MIN_ITEMS_FOR_HOURS
    reliable = [h for h in hourly if h["count"] >= MIN_SAMPLES_PER_HOUR] if enough else []

    # All 24 hours, including the ones with nothing published: the day chart
    # needs them, and there a gap is information (you have never posted then)
    # just as much as a tall bar is.
    by_hour = {h["hour"]: h for h in hourly}
    all_hours = [
        by_hour.get(h, {"hour": h, "avg_views": 0, "count": 0})
        for h in range(24)
    ]

    # A day-by-hour map: "Tuesday at 18:00" is advice, "at 18:00" on its own
    # much less so. Only cells with at least one piece of content are kept: a
    # 7x24 grid of zeroes is not information.
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

    # Engagement overall and per platform, out of data we were already
    # downloading and throwing away: until now only views were read from each
    # piece of content, while likes, comments, shares and saves arrived from
    # the APIs on every refresh and were ignored.
    engagement = _engagement(all_items)
    followers = _followers_by_platform(snapshot)
    engagement_per_platform = {}
    confronti = []
    for piattaforma in per_platform:
        contenuti = [i for i in all_items if i["platform"] == piattaforma]
        misura = _engagement(contenuti)
        if not misura:
            continue
        # Engagement over followers: the definition industry reports use,
        # different from the reach-based one computed above. It exists only
        # for the benchmark comparison and does not replace the other.
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

    # Content above and below your own average: the useful comparison is
    # against yourself, not an industry mean that knows nothing about your
    # audience. A minimum base is needed, or "above average" is describing
    # nothing but chance.
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
        # How much content actually has data: a per-item average taken over
        # everything (zeroes included) is arithmetically correct but tells a
        # different story from the one it appears to tell.
        "items_with_views": len(with_views),
        "avg_views_per_item": round(total_views / len(with_views)) if with_views else 0,
        # The frontend uses these to say "more data needed" rather than
        # showing an invented posting window.
        "hours_enough_data": bool(reliable),
        "hours_items_needed": max(0, MIN_ITEMS_FOR_HOURS - len(rated)),
    }
