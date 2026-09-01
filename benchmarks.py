"""
Copyright (c) 2026 Aurelio Avila. All rights reserved.

Average engagement values by platform and account size.

Purpose: "3.2% engagement" means nothing on its own. It becomes meaningful
only when compared with accounts that have a similar audience on the same
platform: 3% on TikTok is below average, while the same 3% on Instagram is
above average.

Why this lives in a table within the app rather than behind a network call:
these are public industry figures that change once a year, not every time
the app opens. Keeping them here means zero calls, zero cost, no user data
leaving the computer, and no external service to keep running. They are
updated with a release, like everything else.

Here, engagement rate is measured against followers (interactions / followers),
the definition used by industry reports. This differs from reach-based
engagement (interactions / people reached), which the app calculates in
analytics.py: the former shows how active your audience is, while the latter
shows how compelling the content is to those who see it. Comparing one with
the other's values would produce meaningless numbers, so they are never mixed.

Sources: public 2026 benchmark reports (Socialinsider, Influencer Marketing
Factory, Improvado). These are approximate ranges, not exact measurements:
the app presents them as reference points, never as grades.
"""

# Tier thresholds, in followers. The rule across all platforms is that
# engagement FALLS as the audience grows: an account with one thousand
# followers speaks to a community; one with a million speaks to a crowd.
# Comparing a small account with the overall average would make it look
# exceptional, and a large one disastrous, purely because of size.
TIERS = (
    (10_000, "nano"),
    (100_000, "micro"),
    (500_000, "mid"),
    (1_000_000, "macro"),
    (float("inf"), "mega"),
)

# platform -> tier -> expected average engagement (% of followers).
BENCHMARKS = {
    "tiktok": {"nano": 9.0, "micro": 5.0, "mid": 3.8, "macro": 3.2, "mega": 2.8},
    "instagram": {"nano": 4.0, "micro": 2.5, "mid": 1.6, "macro": 1.3, "mega": 1.1},
    "youtube": {"nano": 3.5, "micro": 2.0, "mid": 1.5, "macro": 1.2, "mega": 1.0},
}

# Below this follower count, the ratio is too volatile: one successful post
# can push engagement to 40%, turning the industry comparison into a joke
# rather than a useful indicator.
MIN_FOLLOWERS = 300

# How far a result may deviate from the average while remaining "in line."
# Within this band, it makes no sense to say performance is poor: normal
# month-to-month variation is greater than this.
BANDA = 0.25


def tier_for(followers: int) -> str:
    for soglia, nome in TIERS:
        if followers < soglia:
            return nome
    return "mega"


def expected_rate(platform: str, followers: int) -> float | None:
    """Expected average engagement for an account of this size."""
    per_piattaforma = BENCHMARKS.get(platform)
    if not per_piattaforma or not followers:
        return None
    return per_piattaforma.get(tier_for(followers))


def compare(platform: str, followers: int, follower_rate: float | None) -> dict | None:
    """Compare the user's engagement with the average for their tier.

    Return None when the comparison would not be meaningful (no reference
    data for the platform, or follower data is unavailable or insufficient):
    saying nothing is better than offering a judgment based on nothing.
    """
    if follower_rate is None or not followers or followers < MIN_FOLLOWERS:
        return None
    # inf and NaN survive float() and pass through json.loads, which accepts
    # Infinity and NaN. At this point they would make round() raise an
    # OverflowError and take down the entire page.
    if follower_rate != follower_rate or follower_rate in (float("inf"), float("-inf")):
        return None
    atteso = expected_rate(platform, followers)
    if not atteso:
        return None

    scarto = (follower_rate - atteso) / atteso
    if scarto > BANDA:
        stato = "above"
    elif scarto < -BANDA:
        stato = "below"
    else:
        stato = "inline"

    return {
        "platform": platform,
        "tier": tier_for(followers),
        "followers": followers,
        "rate": round(follower_rate, 2),
        "expected": atteso,
        "state": stato,
        "delta_pct": round(scarto * 100),
    }
