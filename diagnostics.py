"""
Automatic diagnostics computed in code (zero AI calls, zero cost, instant).

This goes beyond checking whether an API responds. The most useful checks
for publishers concern their content: how many days an account has been
inactive, whether a channel has videos but no views, and whether an account
has any data yet. A token problem should be flagged, but an account that has
been inactive for two weeks matters just as much, and no API will say so.

Each entry has a severity, category, short title, details, next step, and,
where appropriate, an action the frontend can turn into a button.

Text is carried as `code` + `params` because the interface supports six
languages: an Italian sentence chosen here would remain Italian even when
the app is in English. The Italian strings remain in the payload as fallbacks,
so a missing translation key falls back to the previous text rather than
displaying a raw code on screen.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import time
from datetime import datetime, timezone

import config

# "Inactive content" thresholds, in days.
STALE_WARN_DAYS = 4
STALE_BAD_DAYS = 8


def _days_since(iso_or_unix, is_unix: bool = False) -> float | None:
    if not iso_or_unix:
        return None
    try:
        if is_unix:
            ts = float(iso_or_unix)
        else:
            ts = datetime.fromisoformat(str(iso_or_unix).replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return None
    return (time.time() - ts) / 86400


def _latest_days(items, field, is_unix=False) -> float | None:
    """Days elapsed since the most recent publication in the list."""
    best = None
    for item in items or []:
        days = _days_since(item.get(field), is_unix)
        if days is not None and (best is None or days < best):
            best = days
    return best


def _has_accounts(platform: str) -> bool:
    """Check whether the platform has at least one account linked through the
    app or configured manually. This distinguishes "no data yet" from "nothing
    linked yet": on first launch, suggesting a Refresh that cannot find
    anything would send the user into a dead end."""
    import os

    env_lists = {"youtube": "YT_CHANNELS", "instagram": "IG_ACCOUNTS", "tiktok": "TT_ACCOUNTS"}
    var = env_lists.get(platform)
    if var and os.environ.get(var, "").strip():
        return True
    try:
        import connections
        return bool(connections.list_connections(platform))
    except Exception:
        return False


GOTO_CONNECTIONS = {"type": "goto", "section": "connections"}


def _no_account_issue(platform: str, label: str) -> dict:
    return _issue(
        "yellow", "Not linked", f"No {label} account",
        f"You haven't linked any {label} account yet.",
        "Press Link and sign in - it only takes a few seconds.",
        platform, GOTO_CONNECTIONS,
        code="diag_no_account", params={"p": label},
    )


def _no_data_issue(platform: str, label: str) -> dict:
    return _issue(
        "yellow", "No data", f"{label} has no data",
        "No data has been loaded yet.", "Press Refresh to load your data.",
        platform, code="diag_no_data", params={"p": label},
    )


def _all_ok_issue(platform: str, label: str, n: int) -> dict:
    return _issue(
        "green", "All good", f"{label}: {n} accounts healthy",
        "Every account responds and posts consistently.",
        "No action needed.", platform,
        code="diag_all_ok", params={"p": label, "n": n},
    )


def _issue(severity, category, title, text, next_step, platform=None, action=None,
           code=None, params=None) -> dict:
    out = {
        "severity": severity, "category": category, "title": title,
        "text": text, "next_step": next_step,
    }
    if platform:
        out["platform"] = platform
    if action:
        out["action"] = action
    if code:
        out["code"] = code
        out["params"] = params or {}
    return out


# Error pattern -> (category, next step, translation code).
_ERROR_PATTERNS = [
    (("video.list",), "Permission not granted",
     "The stats-read permission must be approved on the platform's developer portal - it cannot be fixed from the app.",
     "diagerr_scope_denied"),
    (("invalid_grant", "expired", "revoked"), "Access expired",
     "Link this account again: the authorization expired or was revoked.",
     "diagerr_expired"),
    (("invalid_scope",), "Permissions out of sync",
     "The requested permissions don't match the ones originally granted: link the account again to realign them.",
     "diagerr_scope_mismatch"),
    (("permission", "#10", "does not have permission"), "Missing permission",
     "The account didn't grant the required permission: link it again and accept every request.",
     "diagerr_permission"),
    (("quota", "rate limit", "429"), "Too many requests",
     "Wait a few minutes before refreshing again: the platform's rate limit was reached.",
     "diagerr_rate"),
    (("401", "unauthorized", "authentication"), "Invalid credentials",
     "Link the account again to reissue access.",
     "diagerr_auth"),
    (("404", "not found"), "Account not found",
     "The linked account can no longer be reached: it may have been removed or renamed.",
     "diagerr_notfound"),
    (("timeout", "connection", "network"), "Network problem",
     "Try refreshing again: this looks like a temporary connection issue.",
     "diagerr_network"),
]


def _classify_error(err: str) -> tuple[str, str, str]:
    """Recognize common OAuth/API error patterns to provide a category and a
    concrete next step instead of a generic 'unknown error'."""
    low = (err or "").lower()
    for needles, category, step, code in _ERROR_PATTERNS:
        if any(n in low for n in needles):
            return category, step, code
    return ("Unclassified error", "Try refreshing again; if it persists, link the account again.",
            "diagerr_unknown")


def _unreachable_issue(name: str, error: str, platform: str, action=None) -> dict:
    category, step, code = _classify_error(error)
    return _issue("red", category, f"{name}: not responding", str(error or "")[:220], step,
                  platform, action, code=code, params={"name": name})


def _check_content_freshness(label: str, name: str, days: float | None, platform: str) -> dict | None:
    """The most useful check for publishers: how long activity has stalled."""
    if days is None:
        return None
    d = int(days)
    if days >= STALE_BAD_DAYS:
        return _issue("red", "Posting stalled", f"{name}: nothing for {d} days",
                      f"The latest content on {label} is {d} days old.",
                      "Post something: platforms reward consistency, and reach drops fast on inactive profiles.",
                      platform, code="diag_stale_bad", params={"name": name, "p": label, "d": d})
    if days >= STALE_WARN_DAYS:
        return _issue("yellow", "Slowing down", f"{name}: last post {d} days ago",
                      f"Nothing new on {label} for {d} days.",
                      "Get back to your usual pace before reach starts to slide.",
                      platform, code="diag_stale_warn", params={"name": name, "p": label, "d": d})
    return None


def _check_youtube(data: dict) -> list[dict]:
    if not _has_accounts("youtube"):
        return [_no_account_issue("youtube", "YouTube")]
    if not data:
        return [_no_data_issue("youtube", "YouTube")]
    issues = []
    channels = data.get("channels", [])
    if not channels:
        return [_no_account_issue("youtube", "YouTube")]

    for c in channels:
        if not c.get("ok"):
            issues.append(_unreachable_issue(c.get("name"), c.get("error", ""), "youtube", GOTO_CONNECTIONS))
            continue

        stale = _check_content_freshness("YouTube", c.get("name"), _latest_days(c.get("recent_videos"), "published"), "youtube")
        if stale:
            issues.append(stale)

        if c.get("video_count", 0) > 0 and c.get("recent_views_last10", 0) == 0:
            issues.append(_issue("yellow", "No views", f"{c.get('name')}: 0 views on the latest videos",
                                 "The most recent videos have no views yet.",
                                 "That's normal if they just went up; if they are a few days old, revisit the title, thumbnail and opening seconds.",
                                 "youtube", code="diag_zero_views", params={"name": c.get("name")}))

    if not issues:
        issues.append(_all_ok_issue("youtube", "YouTube", len(channels)))
    return issues


def _check_instagram(data: dict) -> list[dict]:
    if not _has_accounts("instagram"):
        return [_no_account_issue("instagram", "Instagram")]
    if not data:
        return [_no_data_issue("instagram", "Instagram")]
    issues = []
    accounts = data.get("accounts", [])
    if not accounts:
        return [_no_account_issue("instagram", "Instagram")]

    for a in accounts:
        if not a.get("ok"):
            issues.append(_unreachable_issue(a.get("name"), a.get("error", ""), "instagram", GOTO_CONNECTIONS))
            continue

        stale = _check_content_freshness("Instagram", a.get("name"), _latest_days(a.get("recent_posts"), "timestamp"), "instagram")
        if stale:
            issues.append(stale)

    if not issues:
        issues.append(_all_ok_issue("instagram", "Instagram", len(accounts)))
    return issues


def _check_tiktok(data: dict) -> list[dict]:
    if not _has_accounts("tiktok"):
        return [_no_account_issue("tiktok", "TikTok")]
    if not data:
        return [_no_data_issue("tiktok", "TikTok")]
    issues = []
    accounts = data.get("accounts", [])
    if not accounts:
        return [_no_account_issue("tiktok", "TikTok")]

    for a in accounts:
        if a.get("not_configured"):
            issues.append(_issue("yellow", "Needs setup", f"{a.get('name')}: not configured",
                                 "The account is listed but has no credentials attached.",
                                 "Link the account, or remove it from the list if you don't need it.",
                                 "tiktok", GOTO_CONNECTIONS,
                                 code="diag_not_configured", params={"name": a.get("name")}))
            continue
        if not a.get("ok"):
            issues.append(_unreachable_issue(a.get("name"), a.get("error", ""), "tiktok"))
            continue

        stale = _check_content_freshness("TikTok", a.get("name"), _latest_days(a.get("recent_videos"), "create_time", is_unix=True), "tiktok")
        if stale:
            issues.append(stale)

    if not issues:
        issues.append(_all_ok_issue("tiktok", "TikTok", len(accounts)))
    return issues


def _check_x(data: dict) -> list[dict]:
    if not data:
        return [_no_data_issue("x", "X")]
    if not data.get("credentials_configured"):
        return [_issue("yellow", "Not linked", "X not linked",
                       "No X credentials configured.",
                       "X doesn't expose read analytics on the free plan, so this section stays informational for now.",
                       "x", code="diag_x_not_linked", params={})]
    return [_issue("green", "Linked", "X linked",
                   "Credentials are in place. Read analytics aren't available on X's free plan.",
                   "No action needed.", "x", code="diag_x_linked", params={})]


def _check_certsprint(data: dict) -> list[dict]:
    # Personal module: config.enabled_platforms excludes it from customer builds.
    if not data:
        return [_no_data_issue("certsprint", "CertSprint")]
    issues = []
    uptime = data.get("uptime", {})
    if not uptime.get("up"):
        issues.append(_issue("red", "Website unavailable", "CertSprint offline",
                             f"The website is not responding ({uptime.get('error', 'unknown error')}).",
                             "Confirm the deployment is active and the configured URL is correct.", "certsprint"))
    elif uptime.get("latency_ms", 0) > 2000:
        issues.append(_issue("yellow", "Performance", "CertSprint is slow",
                             f"The website responded in {uptime['latency_ms']}ms.",
                             "Check the hosting logs for a cold start or elevated load.", "certsprint"))

    vulns = data.get("npm_audit", {}).get("vulnerabilities", {})
    if vulns.get("critical") or vulns.get("high"):
        issues.append(_issue("red", "Dependency security", "Vulnerabilities require attention",
                             f"npm audit found {vulns.get('critical', 0)} critical and {vulns.get('high', 0)} high vulnerabilities.",
                             "Run 'npm audit fix', review breaking changes, and audit the repository again.", "certsprint"))
    elif vulns.get("moderate"):
        issues.append(_issue("yellow", "Dependency security", "Moderate vulnerabilities",
                             f"npm audit found {vulns['moderate']} moderate vulnerabilities.",
                             "Schedule an 'npm audit fix' after reviewing the proposed changes.", "certsprint"))

    lint = data.get("eslint", {})
    if lint.get("configured") and lint.get("errors"):
        issues.append(_issue("yellow", "Code quality", f"{lint['errors']} ESLint errors",
                             "The linter found errors in the repository.",
                             "Run 'npx eslint . --fix' and review any remaining errors manually.", "certsprint"))

    if not issues:
        issues.append(_issue("green", "All clear", "CertSprint is healthy",
                             "The website is online, no relevant vulnerabilities were found, and the code is clean.", "No action required.", "certsprint"))
    return issues


CHECKS = {
    "youtube": _check_youtube,
    "instagram": _check_instagram,
    "tiktok": _check_tiktok,
    "x": _check_x,
    "certsprint": _check_certsprint,
}


# ----------------------------------------------------------- strategy
#
# The checks below examine whether published content is working, not whether
# the APIs respond. They apply across platforms and use analysis already
# computed in analytics.py, so they require no additional calls.
#
# General rule: silence is better than a claim based on two posts. Every
# check has a minimum data threshold below which it simply returns no opinion.

_PLATFORM_NAMES = {"youtube": "YouTube", "instagram": "Instagram", "tiktok": "TikTok"}

# Below these post counts, a ratio describes an isolated case, not a trend.
MIN_POSTS_ENGAGEMENT = 4
MIN_POSTS_RESONANCE = 5

# Content viewed often but never saved or shared was consumed, not valued.
# The threshold is deliberately low: a few shares are enough to clear it,
# so falling below it truly indicates zero resonance.
RESONANCE_THRESHOLD = 0.15  # % of reach, saves + shares

# How far a platform may trail the best one before the gap is worth noting.
# Above this ratio, the difference is not an imbalance; one channel naturally
# performs better than another.
IMBALANCE = 0.15


def _check_benchmark(analysis: dict) -> list[dict]:
    """Compare your engagement with accounts that have a similar audience size."""
    out_of_range = []
    for comparison in analysis.get("benchmarks", []):
        platform_name = comparison["platform"]
        display_name = _PLATFORM_NAMES.get(platform_name, platform_name)
        check_params = {"p": display_name, "r": comparison["rate"], "e": comparison["expected"]}

        if comparison["state"] == "below":
            out_of_range.append(_issue(
                "yellow", "Engagement under benchmark",
                f"{display_name}: engagement below average for your size",
                f"Your engagement on {display_name} is {comparison['rate']}% against an average of "
                f"{comparison['expected']}% for accounts with a similar following.",
                "Look at which of your own posts got the most saves and shares, and do more of those: "
                "reach follows engagement, not the other way around.",
                platform_name, code="diag_bench_below", params=check_params))
        elif comparison["state"] == "above":
            out_of_range.append(_issue(
                "green", "Engagement above benchmark",
                f"{display_name}: engagement above average",
                f"Your engagement on {display_name} is {comparison['rate']}%, above the "
                f"{comparison['expected']}% average for accounts of your size.",
                "Keep the format that is working: this is the audience responding, not the algorithm.",
                platform_name, code="diag_bench_above", params=check_params))
    return out_of_range


def _check_resonance(analysis: dict) -> list[dict]:
    """Views without saves or shares: watched and forgotten."""
    out_of_range = []
    for platform_name, measure in (analysis.get("engagement_per_platform") or {}).items():
        # YouTube exposes neither saves nor shares through the read scope.
        # A zero there means nothing, and blaming the customer for poor
        # resonance would be our mistake, not theirs.
        if platform_name == "youtube":
            continue
        if measure.get("items", 0) < MIN_POSTS_RESONANCE:
            continue
        resonance = (measure.get("save_rate", 0) or 0) + (measure.get("share_rate", 0) or 0)
        if resonance < RESONANCE_THRESHOLD and measure.get("reach", 0) > 0:
            display_name = _PLATFORM_NAMES.get(platform_name, platform_name)
            out_of_range.append(_issue(
                "yellow", "Low resonance",
                f"{display_name}: seen but not saved or shared",
                f"Across your last {measure['items']} posts on {display_name}, saves and shares add up to "
                f"{round(resonance, 2)}% of the accounts you reached.",
                "Views alone don't compound. Content people save or send to someone else is what the "
                "platform pushes further - try something useful enough to keep, or worth passing on.",
                platform_name, code="diag_resonance",
                params={"p": display_name, "n": measure["items"], "r": round(resonance, 2)}))
    return out_of_range


def _check_imbalance(analysis: dict) -> list[dict]:
    """Identify one stalled platform while the others are performing."""
    for_platform = analysis.get("per_platform") or {}
    active = {p: d for p, d in for_platform.items()
              if p in _PLATFORM_NAMES and d.get("count", 0) > 0}
    if len(active) < 2:
        return []

    averages = {p: d["views"] / d["count"] for p, d in active.items()}
    top = max(averages, key=averages.get)
    if averages[top] <= 0:
        return []

    out_of_range = []
    for platform_name, avg_views in averages.items():
        if platform_name == top or avg_views / averages[top] >= IMBALANCE:
            continue
        display_name = _PLATFORM_NAMES.get(platform_name, platform_name)
        best_name = _PLATFORM_NAMES.get(top, top)
        out_of_range.append(_issue(
            "yellow", "Platform lagging",
            f"{display_name} is far behind {best_name}",
            f"Your posts average {round(avg_views)} views on {display_name} against {round(averages[top])} on "
            f"{best_name}.",
            f"Either adapt what already works on {best_name} to {display_name}'s format, or stop spreading "
            f"yourself thin and put that time where it already pays.",
            platform_name, code="diag_imbalance",
            params={"p": display_name, "b": best_name, "v": round(avg_views), "bv": round(averages[top])}))
    return out_of_range


def _check_posting_hours(analysis: dict) -> list[dict]:
    """Identify a strong time slot that is not being used consistently."""
    best_hours = analysis.get("best_hours") or []
    if len(best_hours) < 2:
        return []

    top, worst = best_hours[0], best_hours[-1]
    # If the best reliable slot performs at least twice as well as the worst,
    # the difference is not noise.
    if worst["avg_views"] <= 0 or top["avg_views"] < worst["avg_views"] * 2:
        return []

    return [_issue(
        "yellow", "Timing", f"Your {top['hour']:02d}:00 slot performs best",
        f"Posts published around {top['hour']:02d}:00 UTC average {top['avg_views']} views, "
        f"against {worst['avg_views']} around {worst['hour']:02d}:00.",
        f"Move your next posts closer to {top['hour']:02d}:00 and see whether the gap holds.",
        None, code="diag_timing",
        params={"h": f"{top['hour']:02d}", "v": top["avg_views"],
                "lh": f"{worst['hour']:02d}", "lv": worst["avg_views"]})]


def _check_strategy(analysis: dict) -> list[dict]:
    """Run every check that examines results rather than errors."""
    if not analysis:
        return []
    out_of_range = []
    for check in (_check_benchmark, _check_resonance, _check_imbalance, _check_posting_hours):
        try:
            out_of_range.extend(check(analysis))
        except Exception:
            # A calculation error in one check must not erase all diagnostics:
            # lose that check, not the page.
            import logging
            logging.warning("diagnostic check failed: %s",
                            check.__name__, exc_info=True)
    return out_of_range


# Weight of each score component. The weights sum to 1.
#
# Engagement carries the most weight because it is the only component that
# shows whether anyone cares about the content. The other three show whether
# the machine is running, not whether it is going anywhere.
WEIGHTS = {"technical": 0.25, "engagement": 0.30, "consistency": 0.25, "coverage": 0.20}

# Issue codes meaning "this step has not been completed yet," rather than
# "something is broken"; they must not count toward the problem badge.
NUDGE_CODES = {"diag_no_account", "diag_no_data", "diag_x_not_linked", "diag_not_configured"}

# Days after which consistency falls to zero. This uses the same thresholds
# as the "time since last post" check to avoid two judgments on the same fact.
FULL_CONSISTENCY_DAYS = 3
ZERO_CONSISTENCY_DAYS = 30


def _score_item(value: float | None, weight: float, item_key: str, detail: str,
          code: str | None = None, params: dict | None = None) -> dict:
    out = {"key": item_key, "score": None if value is None else round(value),
           "weight": weight, "detail": detail}
    if code:
        out["code"] = code
        out["params"] = params or {}
    return out


def _health_score(issues: list[dict], analysis: dict, snapshot: dict) -> dict:
    """Score social performance, not the number of checks that passed.

    The previous score was the percentage of green checks: without technical
    errors, it reached 100% even with zero growth and zero engagement, awarding
    top marks to a stalled account as long as the APIs responded. This version
    weighs four distinct factors and shows where the number comes from, so the
    reader knows what to improve.

    A component may be None when there is not enough data to assess it. In that
    case it is excluded and its weight redistributed, rather than treated as
    zero—which would penalize missing information rather than poor results.
    """
    if _connected_accounts(snapshot) == 0:
        # With zero linked accounts, "zero technical problems" does not mean
        # "all good"; it means there was nothing to check. Without this early
        # return, "technical" would still reach 100 (no red issues against a
        # total forced to 1) and "coverage" would be 0, producing a middling
        # percentage that looks meaningful but is only noise for an empty account.
        return {"score": None, "parts": [_score_item(None, WEIGHTS[k], k, "no account linked yet")
                                          for k in ("technical", "engagement", "consistency", "coverage")]}

    score_items = []

    # 1. Technical: are the accounts responding?
    red_count = sum(1 for i in issues if i["severity"] == "red")
    total_checks = len(issues) or 1
    technical = max(0.0, 100.0 - (red_count / total_checks) * 100 * 2)
    score_items.append(_score_item(technical, WEIGHTS["technical"], "technical",
                      f"{red_count} problem(s) blocking data collection",
                      code="health_detail_technical", params={"n": red_count}))

    # 2. Engagement relative to the account's tier.
    comparisons = (analysis or {}).get("benchmarks") or []
    if comparisons:
        # 100 = in line with the industry average; 200 = twice the average.
        ratios = [min(2.0, c["rate"] / c["expected"]) for c in comparisons if c.get("expected")]
        engagement = (sum(ratios) / len(ratios)) * 50 if ratios else None
        detail = f"compared against {len(comparisons)} platform benchmark(s)"
        eng_code, eng_params = "health_detail_engagement", {"n": len(comparisons)}
    else:
        engagement, detail = None, "not enough follower data to compare"
        eng_code, eng_params = "health_detail_engagement_none", {}
    score_items.append(_score_item(engagement, WEIGHTS["engagement"], "engagement", detail, code=eng_code, params=eng_params))

    # 3. Consistency: how long since the last post.
    days_since = _days_since_last_post(snapshot)
    if days_since is None:
        consistency, detail = None, "no dated content yet"
        cost_code, cost_params = "health_detail_consistency_none", {}
    else:
        if days_since <= FULL_CONSISTENCY_DAYS:
            consistency = 100.0
        elif days_since >= ZERO_CONSISTENCY_DAYS:
            consistency = 0.0
        else:
            span = ZERO_CONSISTENCY_DAYS - FULL_CONSISTENCY_DAYS
            consistency = 100.0 * (1 - (days_since - FULL_CONSISTENCY_DAYS) / span)
        detail = f"last post {int(days_since)} day(s) ago"
        cost_code, cost_params = "health_detail_consistency", {"days": int(days_since)}
    score_items.append(_score_item(consistency, WEIGHTS["consistency"], "consistency", detail, code=cost_code, params=cost_params))

    # 4. Coverage: how many platforms are actually in use.
    active = sum(1 for p, d in ((analysis or {}).get("per_platform") or {}).items()
                 if p in _PLATFORM_NAMES and d.get("count", 0) > 0)
    possible = len([p for p in config.enabled_platforms() if p in _PLATFORM_NAMES]) or 1
    coverage = min(100.0, active / possible * 100)
    score_items.append(_score_item(coverage, WEIGHTS["coverage"], "coverage",
                      f"{active} of {possible} platform(s) with recent content",
                      code="health_detail_coverage", params={"active": active, "total": possible}))

    valid = [v for v in score_items if v["score"] is not None]
    if not valid:
        return {"score": None, "parts": score_items}

    total_weight = sum(v["weight"] for v in valid)
    score = sum(v["score"] * v["weight"] for v in valid) / total_weight
    return {"score": round(score), "parts": score_items}


def _connected_accounts(snapshot: dict) -> int:
    """Count accounts that actually respond, not merely those listed—the same
    distinction the overview uses for the sidebar count."""
    n = 0
    for channel in (snapshot.get("youtube") or {}).get("channels", []):
        if channel.get("ok"):
            n += 1
    for account in (snapshot.get("instagram") or {}).get("accounts", []):
        if account.get("ok"):
            n += 1
    for account in (snapshot.get("tiktok") or {}).get("accounts", []):
        if account.get("ok"):
            n += 1
    return n


def _days_since_last_post(snapshot: dict) -> float | None:
    """Return the number of days since the latest post on any platform.

    Use the most recent post across all platforms: someone who posts on TikTok
    every day and YouTube every two months is not inactive, and saying otherwise
    because one channel moves more slowly would be wrong.
    """
    days_since = []

    for channel in (snapshot.get("youtube") or {}).get("channels", []):
        if channel.get("ok"):
            days_since.append(_latest_days(channel.get("recent_videos"), "published"))

    for account in (snapshot.get("instagram") or {}).get("accounts", []):
        if account.get("ok"):
            days_since.append(_latest_days(account.get("recent_posts"), "timestamp"))

    for account in (snapshot.get("tiktok") or {}).get("accounts", []):
        if account.get("ok"):
            days_since.append(_latest_days(account.get("recent_videos"), "create_time", is_unix=True))

    available = [g for g in days_since if g is not None]
    return min(available) if available else None


def run_diagnostics(snapshot: dict, analytics_data: dict | None = None) -> dict:
    all_issues = []
    for platform in config.enabled_platforms():
        check_fn = CHECKS.get(platform)
        if not check_fn:
            continue
        for issue in check_fn(snapshot.get(platform)):
            all_issues.append({"platform": platform, **issue})

    # Strategy checks examine results, not errors. They run afterward because
    # they use analysis already computed from the same data.
    all_issues.extend(_check_strategy(analytics_data or {}))

    order = {"red": 0, "yellow": 1, "green": 2}
    all_issues.sort(key=lambda i: order.get(i["severity"], 3))

    counts = {"red": 0, "yellow": 0, "green": 0}
    for i in all_issues:
        counts[i["severity"]] = counts.get(i["severity"], 0) + 1

    health = _health_score(all_issues, analytics_data or {}, snapshot)

    # "Nothing linked yet" is not a problem; it is the normal state of a newly
    # installed app. Counting it with real problems triggers the wrong alarm on
    # first launch (five red notifications before the user has done anything).
    # The badge counts only items requiring action on an existing account.
    # Linking prompts remain visible in the list but do not inflate the number.
    actionable = sum(1 for i in all_issues
                      if i["severity"] in ("red", "yellow") and i.get("code") not in NUDGE_CODES)

    return {"issues": all_issues, "counts": counts, "actionable": actionable,
            "score": health["score"], "score_parts": health["parts"]}
