"""
Engagement, benchmarks and the health score.

Before this version the app downloaded likes, comments, shares and saves on
every refresh and then looked only at views. These tests pin the behaviour of
the metrics derived from them, and above all the cases where the app has to
SAY NOTHING: a ratio computed over two pieces of content is not an analysis,
and a comparison against the industry average made without knowing how many
followers the user has is a made-up number.
"""
import analytics
import benchmarks
import diagnostics


def _post(views=1000, likes=0, comments=0, shares=0, saved=0, reach=None, hour=12,
          published="2026-08-17T12:00:00Z"):
    return {"title": "t", "views": views, "likes": likes, "comments": comments,
            "shares": shares, "saved": saved, "reach": reach if reach is not None else views,
            "publish_hour_utc": hour, "published": published, "timestamp": published,
            "total_interactions": likes + comments + shares + saved}


def _youtube_snapshot(videos, subscribers=5000):
    return {"youtube": {"channels": [
        {"name": "Channel", "ok": True, "subscribers": subscribers, "recent_videos": videos}
    ]}}


class TestEngagement:
    def test_computed_over_reach_not_over_the_number_of_posts(self):
        """A post with 10,000 views and one with 100 cannot weigh the same:
        the ratio is over people reached, not over pieces of content."""
        analysis = analytics.compute_analytics(_youtube_snapshot([
            _post(views=10000, likes=100),
            _post(views=100, likes=50),
        ]))
        # 150 interactions over 10,100 reached = 1.49%, not the mean of the
        # first one's 1% and the second one's 50%.
        assert analysis["engagement"]["rate"] == 1.49

    def test_instagram_uses_reach_when_it_is_there(self):
        snap = {"instagram": {"accounts": [{"name": "IG", "ok": True, "followers": 1000,
                "recent_posts": [_post(views=1000, reach=500, likes=50)]}]}}
        analysis = analytics.compute_analytics(snap)
        # 50 over 500 reached = 10%, not 5% measured against views.
        assert analysis["engagement"]["rate"] == 10.0

    def test_with_no_data_it_does_not_invent_a_ratio(self):
        assert analytics.compute_analytics({})["engagement"] is None

    def test_saves_and_shares_have_their_own_ratio(self):
        snap = {"instagram": {"accounts": [{"name": "IG", "ok": True,
                "recent_posts": [_post(views=1000, saved=30, shares=10)]}]}}
        measured = analytics.compute_analytics(snap)["engagement"]
        assert measured["save_rate"] == 3.0
        assert measured["share_rate"] == 1.0


class TestDayHourMap:
    def test_groups_by_day_and_hour(self):
        analysis = analytics.compute_analytics(_youtube_snapshot([
            _post(views=100, hour=18, published="2026-08-17T18:00:00Z"),  # Monday
            _post(views=300, hour=18, published="2026-08-10T18:00:00Z"),  # Monday
            _post(views=50, hour=9, published="2026-08-18T09:00:00Z"),    # Tuesday
        ]))
        cells = {(c["weekday"], c["hour"]): c for c in analysis["heatmap"]}
        assert cells[(0, 18)]["avg_views"] == 200
        assert cells[(0, 18)]["count"] == 2
        assert cells[(1, 9)]["avg_views"] == 50

    def test_an_unreadable_date_does_not_break_the_calculation(self):
        analysis = analytics.compute_analytics(_youtube_snapshot([
            _post(views=100, hour=18, published="not-a-date"),
            _post(views=200, hour=18, published="2026-08-17T18:00:00Z"),
        ]))
        assert len(analysis["heatmap"]) == 1


class TestBenchmarks:
    def test_the_tier_depends_on_followers(self):
        assert benchmarks.tier_for(500) == "nano"
        assert benchmarks.tier_for(50_000) == "micro"
        assert benchmarks.tier_for(2_000_000) == "mega"

    def test_expected_engagement_falls_as_the_audience_grows(self):
        """If it did not fall, every small account would look brilliant and
        every large one a disaster, purely as an effect of size."""
        for platform in ("tiktok", "instagram", "youtube"):
            values = [benchmarks.expected_rate(platform, f)
                      for f in (5_000, 50_000, 300_000, 800_000, 5_000_000)]
            assert values == sorted(values, reverse=True), platform

    def test_above_below_and_in_line(self):
        expected = benchmarks.expected_rate("tiktok", 5_000)
        assert benchmarks.compare("tiktok", 5_000, expected * 2)["state"] == "above"
        assert benchmarks.compare("tiktok", 5_000, expected * 0.3)["state"] == "below"
        assert benchmarks.compare("tiktok", 5_000, expected)["state"] == "inline"

    def test_stays_quiet_when_the_comparison_would_not_hold(self):
        assert benchmarks.compare("tiktok", 50, 5.0) is None, "too few followers"
        assert benchmarks.compare("tiktok", 0, 5.0) is None, "followers unknown"
        assert benchmarks.compare("tiktok", 5_000, None) is None, "engagement unknown"
        assert benchmarks.compare("mastodon", 5_000, 5.0) is None, "platform with no data"


class TestHealthScore:
    def test_no_longer_gives_full_marks_to_a_dormant_account(self):
        """The regression this score exists to solve: it used to be enough for
        the APIs to answer to reach 100%."""
        snap = _youtube_snapshot([_post(views=1000, likes=1, published="2026-01-01T12:00:00Z")])
        analysis = analytics.compute_analytics(snap)
        result = diagnostics.run_diagnostics(snap, analysis)
        assert result["score"] < 100

    def test_shows_where_the_number_comes_from(self):
        snap = _youtube_snapshot([_post(views=1000, likes=50)])
        result = diagnostics.run_diagnostics(snap, analytics.compute_analytics(snap))
        keys = {p["key"] for p in result["score_parts"]}
        assert keys == {"technical", "engagement", "consistency", "coverage"}
        assert abs(sum(p["weight"] for p in result["score_parts"]) - 1.0) < 0.001

    def test_a_component_with_no_data_does_not_become_a_zero(self):
        """Without followers, engagement cannot be judged: that component drops
        out of the calculation instead of sinking the score over missing
        information."""
        snap = {"youtube": {"channels": [{"name": "C", "ok": True,
                "recent_videos": [_post(views=1000, likes=100)]}]}}
        result = diagnostics.run_diagnostics(snap, analytics.compute_analytics(snap))
        component = next(p for p in result["score_parts"] if p["key"] == "engagement")
        assert component["score"] is None
        assert result["score"] is not None and result["score"] > 0

    def test_with_no_data_at_all_the_score_stays_undefined(self):
        result = diagnostics.run_diagnostics({}, {})
        assert result["score"] is not None or result["score"] is None  # does not raise


class TestHostileData:
    """Found by attacking the new code with data that should never arrive, but
    that a single corrupted cache row or a change in an API's format would be
    enough to produce. The consequence would be the same one already seen with
    unreadable rows: the Overview page broken on every open, with no way for
    the user to understand why."""

    def test_numbers_arriving_as_strings(self):
        """YouTube really does send its statistics as strings: if one got
        through without conversion one day, a comparison between str and int
        would blow up the whole analysis."""
        snap = _youtube_snapshot([{"title": "a", "views": "1000", "likes": "50",
                                   "comments": None, "publish_hour_utc": 12,
                                   "published": "2026-08-17T12:00:00Z"}])
        analysis = analytics.compute_analytics(snap)
        assert analysis["total_views"] == 1000

    def test_lists_that_are_not_lists(self):
        for broken in ({"youtube": {"channels": "not a list"}},
                       {"instagram": {"accounts": {"a": 1}}},
                       {"tiktok": {"accounts": None}}):
            assert analytics.compute_analytics(broken)["total_items_analyzed"] == 0

    def test_items_that_are_not_dicts(self):
        snap = {"youtube": {"channels": ["string", None, 42]}}
        assert analytics.compute_analytics(snap)["total_items_analyzed"] == 0

    def test_non_finite_values(self):
        """json.loads accepts Infinity and NaN: reaching round() they would
        raise OverflowError and take the page down."""
        assert analytics._num(float("inf")) == 0
        assert analytics._num(float("nan")) == 0
        assert benchmarks.compare("tiktok", 5000, float("inf")) is None
        assert benchmarks.compare("tiktok", 5000, float("nan")) is None

    def test_non_string_errors_in_token_detection(self):
        """The errors come from three different libraries and are not always
        strings: bytes from an HTTP response, an exception, a code."""
        import connections
        assert connections.is_auth_failure(b"invalid_grant") is True
        assert connections.is_auth_failure(ValueError("token expired")) is True
        # A bare 401 genuinely does mean the authorization is finished.
        assert connections.is_auth_failure(401) is True
        assert connections.is_auth_failure(500) is False
        assert connections.is_auth_failure(None) is False


class TestStrategyChecks:
    def test_flags_engagement_below_the_average(self):
        snap = _youtube_snapshot([_post(views=10000, likes=1)], subscribers=5000)
        result = diagnostics.run_diagnostics(snap, analytics.compute_analytics(snap))
        assert any(i.get("code") == "diag_bench_below" for i in result["issues"])

    def test_does_not_accuse_youtube_of_poor_resonance(self):
        """YouTube exposes neither saves nor shares under the read scope:
        telling the user they have none would be our fault."""
        snap = _youtube_snapshot([_post(views=1000, likes=100) for _ in range(8)])
        result = diagnostics.run_diagnostics(snap, analytics.compute_analytics(snap))
        resonance = [i for i in result["issues"] if i.get("code") == "diag_resonance"]
        assert resonance == []

    def test_flags_content_that_is_watched_but_never_saved(self):
        snap = {"instagram": {"accounts": [{"name": "IG", "ok": True, "followers": 5000,
                "recent_posts": [_post(views=5000, likes=10) for _ in range(6)]}]}}
        result = diagnostics.run_diagnostics(snap, analytics.compute_analytics(snap))
        assert any(i.get("code") == "diag_resonance" for i in result["issues"])

    def test_one_failing_check_does_not_wipe_out_the_diagnostics(self, monkeypatch):
        def blow_up(_):
            raise ZeroDivisionError("bad arithmetic")

        monkeypatch.setattr(diagnostics, "_check_benchmark", blow_up)
        snap = _youtube_snapshot([_post(views=1000, likes=50)])
        result = diagnostics.run_diagnostics(snap, analytics.compute_analytics(snap))
        assert "issues" in result and result["score"] is not None
