"""
Single-platform analysis computed in code from data already downloaded.

This function previously called a paid model: every click on "Analyze" cost
money, required an API key, took seconds, and—when the credit ran out—showed
the customer the provider's raw error ("credit balance is too low..."). For a
commercial product, that is unacceptable on three fronts: variable cost,
external dependency, and messages about services the customer did not buy.

The same useful questions can be answered with data the app already has:
which content performs best, which posts are below average, how frequently
content is published, and how much engagement each view generates. The result
is instant, free, offline, and identical on every run.

As with diagnostics, text travels as `code` + `params` so it follows the
language selected in the interface; the Italian sentence remains as a fallback.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import time
from datetime import datetime

# Below these thresholds, an observation would be noise rather than insight:
# with only two posts, "average" and "best" overlap and reveal nothing.
MIN_ITEMS_FOR_COMPARISON = 4
FLOP_RATIO = 0.4          # below 40% of the average = underperforming
STAR_RATIO = 1.5          # above 150% of the average = worth replicating

# With six linked accounts, one observation per metric per account produces
# twenty lines. Nobody reads them, and the point of a summary panel is to avoid
# reading them all. Keep only the few observations that truly matter.
MAX_PER_ENTITY = 2
MAX_TOTAL = 6
KIND_PRIORITY = {"warn": 0, "good": 1, "info": 2}


def _to_unix(value, is_unix: bool = False) -> float | None:
    if not value:
        return None
    try:
        if is_unix:
            return float(value)
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return None


def _entities(platform: str, data: dict) -> list[dict]:
    """Normalize the platform's channels/accounts into a common structure so
    the rest of the module need not know where the data came from."""
    if not data:
        return []
    if platform == "youtube":
        raw, items_key, ts_field, is_unix = data.get("channels", []), "recent_videos", "published", False
    elif platform == "instagram":
        raw, items_key, ts_field, is_unix = data.get("accounts", []), "recent_posts", "timestamp", False
    elif platform == "tiktok":
        raw, items_key, ts_field, is_unix = data.get("accounts", []), "recent_videos", "create_time", True
    else:
        return []

    out = []
    for e in raw:
        if not e.get("ok"):
            continue
        items = []
        for it in e.get(items_key, []) or []:
            ts = _to_unix(it.get(ts_field), is_unix)
            hour = it.get("publish_hour_utc")
            if hour is None and ts is not None:
                hour = datetime.utcfromtimestamp(ts).hour
            items.append({
                "title": (it.get("title") or it.get("caption") or "").strip(),
                "views": it.get("views", 0) or 0,
                "likes": it.get("likes", 0) or 0,
                "comments": it.get("comments", 0) or 0,
                "shares": it.get("shares", 0) or 0,
                "ts": ts,
                "hour": hour,
            })
        out.append({"name": e.get("name", ""), "items": items, "raw": e})
    return out


def _insight(kind: str, code: str, text: str, **params) -> dict:
    return {"kind": kind, "code": code, "text": text, "params": params}


def _short(title: str, n: int = 60) -> str:
    title = (title or "").replace("\n", " ").strip()
    if not title:
        return "(untitled)"
    return title if len(title) <= n else title[: n - 1] + "…"


def _analyze_entity(name: str, items: list[dict]) -> list[dict]:
    out = []
    with_views = [i for i in items if i["views"] > 0]

    if not items:
        return [_insight("info", "ins_no_items", f"{name}: no recent content to analyze.", name=name)]

    # Zero-view posts: useful to know before reading any average.
    zeros = len(items) - len(with_views)
    if zeros and zeros == len(items):
        return [_insight("warn", "ins_all_zero",
                         f"{name}: none of the last {len(items)} posts have any views yet.",
                         name=name, n=len(items))]
    if zeros:
        # `n` is the count that determines singular/plural in translation, so
        # it must be the varying value (zero-view posts), not the total;
        # otherwise the interface displayed "1 posts."
        out.append(_insight("warn", "ins_some_zero",
                            f"{name}: {zeros} of the last {len(items)} posts still have zero views.",
                            name=name, n=zeros, tot=len(items)))

    avg = sum(i["views"] for i in with_views) / len(with_views)

    # Best and worst are meaningful only with enough history: with two posts,
    # "the best" is a tautology, not analysis.
    if len(with_views) >= MIN_ITEMS_FOR_COMPARISON:
        best = max(with_views, key=lambda i: i["views"])
        if best["views"] >= avg * STAR_RATIO:
            out.append(_insight("good", "ins_star",
                                f"{name}: \"{_short(best['title'])}\" got {best['views']:,} views, "
                                f"{round(best['views'] / avg, 1)}x the account average. Look at what sets it apart and do it again.",
                                name=name, title=_short(best["title"]), v=best["views"],
                                x=round(best["views"] / avg, 1)))

        flops = [i for i in with_views if i["views"] < avg * FLOP_RATIO]
        if flops:
            worst = min(flops, key=lambda i: i["views"])
            out.append(_insight("warn", "ins_flop",
                                f"{name}: {len(flops)} posts below 40% of the average, the weakest being "
                                f"\"{_short(worst['title'])}\" with {worst['views']:,} views.",
                                name=name, n=len(flops), title=_short(worst["title"]), v=worst["views"]))

    # Engagement: how often a view turns into an interaction.
    total_views = sum(i["views"] for i in with_views)
    interactions = sum(i["likes"] + i["comments"] + i["shares"] for i in items)
    if total_views > 0 and interactions > 0:
        rate = interactions / total_views * 100
        out.append(_insight("info", "ins_engagement",
                            f"{name}: {rate:.1f}% engagement on recent content "
                            f"({interactions:,} interactions across {total_views:,} views).",
                            name=name, rate=f"{rate:.1f}", i=interactions, v=total_views))

    # Publishing cadence: the metric that most often explains a decline.
    stamps = sorted([i["ts"] for i in items if i["ts"]], reverse=True)
    if len(stamps) >= 3:
        gaps = [(stamps[k] - stamps[k + 1]) / 86400 for k in range(len(stamps) - 1)]
        avg_gap = sum(gaps) / len(gaps)
        since = (time.time() - stamps[0]) / 86400
        # Someone who posts several times a day does not have "one post every
        # 0.2 days": accurate, but unreadable. Below one day, invert the
        # fraction and express the cadence as posts per day.
        daily = avg_gap > 0 and avg_gap < 1
        per_day = round(1 / avg_gap, 1) if daily else 0

        if since > max(avg_gap * 2, 1) and since >= 3:
            if daily:
                out.append(_insight("warn", "ins_cadence_broken_daily",
                                    f"{name}: you usually post several times a day, but the latest "
                                    f"content is {int(since)} days old.",
                                    name=name, d=int(since)))
            else:
                out.append(_insight("warn", "ins_cadence_broken",
                                    f"{name}: you usually post every {avg_gap:.1f} days, but the latest "
                                    f"content is {int(since)} days old.",
                                    name=name, gap=f"{avg_gap:.1f}", d=int(since)))
        elif daily:
            out.append(_insight("info", "ins_cadence_daily",
                                f"{name}: you post about {per_day} times a day.",
                                name=name, n=per_day))
        else:
            out.append(_insight("info", "ins_cadence",
                                f"{name}: you post every {avg_gap:.1f} days on average.",
                                name=name, gap=f"{avg_gap:.1f}"))
    return out


def generate_insights(snapshot: dict, platform: str = "all") -> list[dict]:
    """Generate observations for the selected platform. No network, no cost."""
    data = snapshot.get(platform) if isinstance(snapshot, dict) else None

    if platform == "x":
        return [_insight("info", "ins_x_free_plan",
                         "X does not expose read analytics on the free plan, so there is nothing to analyze.")]

    entities = _entities(platform, data)
    if not entities:
        return [_insight("info", "ins_no_data",
                         "No data to analyze: connect an account and select Refresh.")]

    out = []
    for e in entities:
        found = _analyze_entity(e["name"], e["items"])
        # Put critical findings first: if only one thing can be said about an
        # account, choose the item requiring action, not its cadence.
        found.sort(key=lambda i: KIND_PRIORITY.get(i["kind"], 3))
        out.extend(found[:MAX_PER_ENTITY])

    # Compare accounts only when there is more than one; otherwise it is a
    # "ranking of one" that adds nothing.
    if len(entities) > 1:
        totals = [(e["name"], sum(i["views"] for i in e["items"])) for e in entities]
        totals = [t for t in totals if t[1] > 0]
        if len(totals) > 1:
            totals.sort(key=lambda t: t[1], reverse=True)
            out.append(_insight("info", "ins_best_account",
                                f"{totals[0][0]} is the best-performing account: {totals[0][1]:,} views versus "
                                f"{totals[-1][1]:,} for {totals[-1][0]}.",
                                best=totals[0][0], bv=totals[0][1], worst=totals[-1][0], wv=totals[-1][1]))

    if not out:
        out.append(_insight("good", "ins_nothing_notable",
                            "No issues were detected in the latest content."))

    out.sort(key=lambda i: KIND_PRIORITY.get(i["kind"], 3))
    return out[:MAX_TOTAL]
