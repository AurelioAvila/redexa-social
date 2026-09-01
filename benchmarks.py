"""
Copyright (c) 2026 Aurelio Avila. All rights reserved.

Average engagement figures by platform and account size.

What they are for: "engagement 3.2%" on its own says nothing. It says
something only against what people with a similar audience on the same
platform manage - 3% on TikTok is below average, the same 3% on Instagram is
above it.

Why this is a table inside the app rather than a network call: these are
public industry figures that change once a year, not on every launch. Keeping
them here means no calls, no cost, no user data leaving their computer, and no
external service to keep alive. They are updated with a release, like
everything else.

Engagement rate here is taken over followers (interactions / followers), which
is the definition every industry report uses. It differs from the reach-based
one (interactions / people reached) the app computes in analytics.py: the
first says how active your audience is, the second how convincing you are to
whoever sees you. Comparing one against the other's figures would produce
meaningless numbers, so the two are never mixed.

Source of the values: public 2026 benchmark reports (Socialinsider, Influencer
Marketing Factory, Improvado). They are orders of magnitude, not exact
measurements: the app presents them as a reference, never as a grade.
"""

# Bracket thresholds, in followers. The rule that holds on every platform is
# that engagement FALLS as the audience grows: an account of a thousand people
# is talking to a community, one of a million to an audience. Comparing a
# small account against the overall average would make it look brilliant, and
# a large one a disaster, purely as an effect of size.
TIERS = (
    (10_000, "nano"),
    (100_000, "micro"),
    (500_000, "mid"),
    (1_000_000, "macro"),
    (float("inf"), "mega"),
)

# piattaforma -> fascia -> engagement medio atteso (% sui follower).
BENCHMARKS = {
    "tiktok": {"nano": 9.0, "micro": 5.0, "mid": 3.8, "macro": 3.2, "mega": 2.8},
    "instagram": {"nano": 4.0, "micro": 2.5, "mid": 1.6, "macro": 1.3, "mega": 1.1},
    "youtube": {"nano": 3.5, "micro": 2.0, "mid": 1.5, "macro": 1.2, "mega": 1.0},
}

# Below this follower count the ratio is too jumpy: one piece of content
# doing well sends engagement to 40%, and the comparison against the industry
# average becomes a joke rather than an indication.
MIN_FOLLOWERS = 300

# How far from the average still counts as "in line". Inside this band there
# is no sense telling someone they are doing badly: ordinary month-to-month
# variation is wider than that.
BANDA = 0.25


def tier_for(followers: int) -> str:
    for soglia, nome in TIERS:
        if followers < soglia:
            return nome
    return "mega"


def expected_rate(platform: str, followers: int) -> float | None:
    """The engagement expected of an account this size."""
    per_piattaforma = BENCHMARKS.get(platform)
    if not per_piattaforma or not followers:
        return None
    return per_piattaforma.get(tier_for(followers))


def compare(platform: str, followers: int, follower_rate: float | None) -> dict | None:
    """Compares the user's engagement against the average for their bracket.

    Returns None when the comparison would not hold up (a platform with no
    reference data, followers unavailable or too few): better to say nothing
    than to hand out a verdict built on nothing.
    """
    if follower_rate is None or not followers or followers < MIN_FOLLOWERS:
        return None
    # inf and NaN survive float() and pass through json.loads untouched,
    # which accepts Infinity and NaN: reaching this far they would blow up
    # round() with an OverflowError and take the whole page down.
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
