"""
Time series and changes, computed from the snapshots already written to
cache.db on every refresh (no external calls, no cost).

Until now that history was written and read nowhere: here it becomes the basis
for the sparklines and for the "+N% since the last refresh" badges - which is
to say, for noticing a decline instead of only looking at today's number.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import cache

# Each platform's "headline" metric: the one that ends up in the sparkline
# and in the comparison against the previous refresh.
def _youtube_metric(snap: dict) -> float:
    return sum(c.get("subscribers", 0) for c in snap.get("channels", []) if c.get("ok"))


def _youtube_views(snap: dict) -> float:
    return sum(c.get("recent_views_last10", 0) for c in snap.get("channels", []) if c.get("ok"))


def _instagram_metric(snap: dict) -> float:
    return sum(a.get("followers", 0) for a in snap.get("accounts", []) if a.get("ok"))


def _instagram_views(snap: dict) -> float:
    return sum((a.get("totals_last_n") or {}).get("views", 0) for a in snap.get("accounts", []) if a.get("ok"))


def _tiktok_metric(snap: dict) -> float:
    return sum((a.get("totals_last_n") or {}).get("views", 0) for a in snap.get("accounts", []) if a.get("ok"))


def _certsprint_metric(snap: dict) -> float:
    return (snap.get("uptime") or {}).get("latency_ms", 0)


METRICS = {
    "youtube": {"primary": ("Iscritti", _youtube_metric), "secondary": ("Views ultimi video", _youtube_views)},
    "instagram": {"primary": ("Follower", _instagram_metric), "secondary": ("Views ultimi post", _instagram_views)},
    "tiktok": {"primary": ("Views", _tiktok_metric), "secondary": None},
    "certsprint": {"primary": ("Latenza (ms)", _certsprint_metric), "secondary": None},
}


def _series(platform: str, extractor, limit: int) -> list[dict]:
    out = []
    for snap in cache.history(platform, limit=limit):
        try:
            value = extractor(snap)
        except Exception:
            continue
        out.append({"t": snap.get("fetched_at"), "v": value})
    return out


def _delta(series: list[dict]) -> dict | None:
    """The change between the latest point and the previous one that differs.
    The immediately preceding point is skipped when identical: refreshing
    twice in a row with nothing changing must not show a hollow '0%' in place
    of the last real movement."""
    if len(series) < 2:
        return None
    current = series[-1]["v"]
    for prev in reversed(series[:-1]):
        if prev["v"] != current:
            diff = current - prev["v"]
            pct = (diff / prev["v"] * 100) if prev["v"] else None
            return {
                "from": prev["v"], "to": current, "diff": diff,
                "pct": round(pct, 1) if pct is not None else None,
                "since": prev["t"],
            }
    return {"from": current, "to": current, "diff": 0, "pct": 0, "since": series[0]["t"]}


def compute_trends(limit: int = 30) -> dict:
    import config

    out = {}
    enabled = set(config.enabled_platforms())
    for platform, metrics in METRICS.items():
        if platform not in enabled:
            continue
        entry = {}
        for slot in ("primary", "secondary"):
            spec = metrics.get(slot)
            if not spec:
                continue
            label, extractor = spec
            series = _series(platform, extractor, limit)
            if not series:
                continue
            entry[slot] = {
                "label": label,
                "series": series,
                "current": series[-1]["v"],
                "delta": _delta(series),
                "points": len(series),
            }
        if entry:
            out[platform] = entry
    return out
