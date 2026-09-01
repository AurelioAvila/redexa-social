"""
Per-platform analysis, computed in code over data already downloaded.

This function used to call a paid model: every click on "Analyse" cost money,
needed an API key, took seconds, and - once the credit ran out - showed the
customer the provider's raw error ("credit balance is too low..."). For a
product that is sold, that is unacceptable on three counts: variable cost, an
external dependency, and messages about services the customer never bought.

The same useful questions are answered from data the app already holds: which
piece of content is the best, which are below average, at what rhythm things
are published, how much engagement a view generates. Instant, free, offline,
and identical on every run.

As in the diagnostics, the text travels as `code` + `params` so it follows the
language chosen in the interface; the written sentence stays as the fallback.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import time
from datetime import datetime

# Below these thresholds an observation would be noise rather than
# information: with two posts, "average" and "best" are the same thing and say
# nothing at all.
MIN_ITEMS_FOR_COMPARISON = 4
FLOP_RATIO = 0.4          # sotto il 40% della media = sotto-performante
STAR_RATIO = 1.5          # sopra il 150% della media = da replicare

# With six connected accounts, one observation per metric per account comes
# to twenty lines: nobody reads them, and the whole value of a summary panel
# is not having to. Only the few that genuinely matter are kept.
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
    """The platform's channels or accounts, normalized into one shape so the
    rest of the module does not need to know where the data came from."""
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

    # Content at zero: worth knowing before reading any average.
    zeros = len(items) - len(with_views)
    if zeros and zeros == len(items):
        return [_insight("warn", "ins_all_zero",
                         f"{name}: none of the last {len(items)} posts have any views yet.",
                         name=name, n=len(items))]
    if zeros:
        # `n` is the count that picks singular or plural in the
        # translation, so it has to be the one that varies (the items at
        # zero), not the total - otherwise it read "1 items".
        out.append(_insight("warn", "ins_some_zero",
                            f"{name}: {zeros} of the last {len(items)} posts still have zero views.",
                            name=name, n=zeros, tot=len(items)))

    avg = sum(i["views"] for i in with_views) / len(with_views)

    # Best and worst only mean something with enough content behind them:
    # across two posts "the best" is a truism, not an analysis.
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
                            f"{name}: {rate:.1f}% di engagement sugli ultimi contenuti "
                            f"({interactions:,} interazioni su {total_views:,} views).",
                            name=name, rate=f"{rate:.1f}", i=interactions, v=total_views))

    # Publishing rhythm: the figure that most often explains a decline.
    stamps = sorted([i["ts"] for i in items if i["ts"]], reverse=True)
    if len(stamps) >= 3:
        gaps = [(stamps[k] - stamps[k + 1]) / 86400 for k in range(len(stamps) - 1)]
        avg_gap = sum(gaps) / len(gaps)
        since = (time.time() - stamps[0]) / 86400
        # Someone publishing several times a day does not have "one item
        # every 0.2 days": true, but unreadable. Below a day the fraction is
        # flipped and it talks in times per day.
        daily = avg_gap > 0 and avg_gap < 1
        per_day = round(1 / avg_gap, 1) if daily else 0

        if since > max(avg_gap * 2, 1) and since >= 3:
            if daily:
                out.append(_insight("warn", "ins_cadence_broken_daily",
                                    f"{name}: di solito pubblichi piu' volte al giorno, ma l'ultimo contenuto "
                                    f"risale a {int(since)} giorni fa.",
                                    name=name, d=int(since)))
            else:
                out.append(_insight("warn", "ins_cadence_broken",
                                    f"{name}: di solito pubblichi ogni {avg_gap:.1f} giorni, ma l'ultimo contenuto "
                                    f"risale a {int(since)} giorni fa.",
                                    name=name, gap=f"{avg_gap:.1f}", d=int(since)))
        elif daily:
            out.append(_insight("info", "ins_cadence_daily",
                                f"{name}: pubblichi circa {per_day} volte al giorno.",
                                name=name, n=per_day))
        else:
            out.append(_insight("info", "ins_cadence",
                                f"{name}: pubblichi in media ogni {avg_gap:.1f} giorni.",
                                name=name, gap=f"{avg_gap:.1f}"))
    return out


def generate_insights(snapshot: dict, platform: str = "all") -> list[dict]:
    """Osservazioni sulla piattaforma indicata. Nessuna rete, nessun costo."""
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
        # Problems first: if only one thing can be said about an account,
        # let it be the one that asks for action, not its cadence.
        found.sort(key=lambda i: KIND_PRIORITY.get(i["kind"], 3))
        out.extend(found[:MAX_PER_ENTITY])

    # Comparison between accounts: only where there is more than one, or it
    # is a league table of one and adds nothing.
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
