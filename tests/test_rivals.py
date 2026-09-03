"""
Comparison against public accounts.

What is worth pinning here is not the read from the API - that is one call,
and the network is barred in the tests - but the three decisions the code
makes on its own, which nobody would notice being wrong: how a channel is
recognised from whatever the user pastes, where somebody who hides their
subscriber count ends up, and who is allowed to add one.
"""
import pytest

import rivals
from conftest import auth_headers


@pytest.fixture(autouse=True)
def empty_list():
    """Every test starts with no rivals. The table lives in the same test
    database as everything else, and that database is not recreated between
    tests: without this, the third test inherits the second one's channels and
    fails for a reason that has nothing to do with what it is checking."""
    def wipe():
        conn = rivals._conn()
        try:
            conn.execute("DELETE FROM rivals")
            conn.commit()
        finally:
            conn.close()

    wipe()
    yield
    wipe()


class TestChannelRecognition:
    """The user pastes whatever they have to hand, not a clean handle."""

    @pytest.mark.parametrize("written,expected", [
        ("@mkbhd", "@mkbhd"),
        ("mkbhd", "@mkbhd"),
        ("  @mkbhd  ", "@mkbhd"),
        ("https://youtube.com/@mkbhd", "@mkbhd"),
        ("https://www.youtube.com/@mkbhd/videos", "@mkbhd"),
        ("UCBJycsmduvYEL83R_U4JriQ", "UCBJycsmduvYEL83R_U4JriQ"),
        ("https://www.youtube.com/channel/UCBJycsmduvYEL83R_U4JriQ", "UCBJycsmduvYEL83R_U4JriQ"),
    ])
    def test_accepted_forms(self, written, expected):
        assert rivals.parse_handle(written) == expected

    @pytest.mark.parametrize("written", ["", "   ", "a", "http://example.com/@someone", "@"])
    def test_refused_forms(self, written):
        """Refuse with an error, never guess: a wrong handle would turn into a
        read of a channel other than the one intended."""
        with pytest.raises(rivals.RivalError):
            rivals.parse_handle(written)


class TestList:
    def test_adds_normalises_and_removes(self):
        rivals.add_rival("https://youtube.com/@someone")
        listed = rivals.list_rivals()
        assert [r["handle"] for r in listed] == ["@someone"]

        rivals.remove_rival(listed[0]["id"])
        assert rivals.list_rivals() == []

    def test_the_same_channel_is_not_added_twice(self):
        rivals.add_rival("@someone")
        # Written another way too: it is the same channel, and seeing it
        # twice in the ranking would be a wrong ranking.
        with pytest.raises(rivals.RivalError):
            rivals.add_rival("https://youtube.com/@someone")

    def test_beyond_the_maximum_is_refused(self):
        for name in ("@one", "@two", "@three"):
            rivals.add_rival(name)
        with pytest.raises(rivals.RivalError):
            rivals.add_rival("@four")


def _followed(conn_handle, subscribers, views, videos, title="Rival"):
    """Writes an already-fetched rival, without going through the API."""
    import json
    import time

    expected = rivals.parse_handle(conn_handle)
    rivals.add_rival(conn_handle)
    # By handle, not by position: identifying the row just inserted with
    # [-1] has already written one channel's statistics over another's.
    row = next(r for r in rivals.list_rivals() if r["handle"] == expected)
    conn = rivals._conn()
    try:
        conn.execute(
            "UPDATE rivals SET title = ?, data = ?, fetched_at = ? WHERE id = ?",
            (title, json.dumps({
                "channel_id": "UC" + "x" * 22,
                "title": title,
                "subscribers": subscribers,
                "total_views": views,
                "video_count": videos,
            }), int(time.time()), row["id"]),
        )
        conn.commit()
    finally:
        conn.close()


def _snapshot(subscribers, views, videos):
    return {"youtube": {"channels": [
        {"title": "Mine", "subscribers": subscribers, "total_views": views, "video_count": videos}
    ]}}


class TestComparison:
    def test_nothing_to_say_nothing_to_show(self):
        """No rivals, or no successful fetch: None, not an empty section. An
        empty panel looks broken."""
        assert rivals.compare(_snapshot(100, 1000, 10)) is None

        rivals.add_rival("@someone")  # added but never fetched
        assert rivals.compare(_snapshot(100, 1000, 10)) is None

    def test_position_among_the_channels(self):
        _followed("@big", 5000, 500_000, 100)
        _followed("@small", 50, 5_000, 10)

        result = rivals.compare(_snapshot(500, 50_000, 25))

        assert result["rank"] == 2, "between the two"
        assert result["ranked_of"] == 3
        assert [r["subscribers"] for r in result["rows"]] == [5000, 500, 50]

    def test_average_per_video_instead_of_the_total(self):
        """The total only rewards whoever has been publishing longest. The
        average per video is the comparison that holds between accounts of
        different ages."""
        _followed("@veteran", 5000, 500_000, 500)  # 1000 per video
        result = rivals.compare(_snapshot(500, 50_000, 25))  # 2000 per video

        mine = next(r for r in result["rows"] if r.get("mine"))
        other = next(r for r in result["rows"] if not r.get("mine"))
        assert mine["views_per_video"] == 2000.0
        assert other["views_per_video"] == 1000.0

    def test_zero_videos_does_not_divide_by_zero(self):
        _followed("@brandnew", 10, 0, 0)
        result = rivals.compare(_snapshot(500, 50_000, 25))
        other = next(r for r in result["rows"] if not r.get("mine"))
        assert other["views_per_video"] == 0.0

    def test_hiding_subscribers_does_not_put_you_last(self):
        """YouTube lets a channel hide its subscriber count. Counting it as
        zero would put that channel at the bottom for a privacy choice, which
        is not a result - and would distort everybody else's position."""
        _followed("@private", None, 900_000, 300)
        _followed("@small", 50, 5_000, 10)

        result = rivals.compare(_snapshot(500, 50_000, 25))

        assert result["rank"] == 1, "first of the two that do declare subscribers"
        assert result["ranked_of"] == 2, "the private channel stays out of the ranking"
        assert result["hidden_subscribers"] is True, "but it has to be said that it is there"
        # It still appears in the table: it has other columns worth comparing.
        assert any(r["title"] == "@private" or r.get("handle") == "@private" for r in result["rows"])


class TestPlan:
    def test_adding_requires_the_plan(self, client):
        resp = client.post("/api/rivals", json={"handle": "@someone"})
        assert resp.status_code == 402

    def test_reading_and_removing_stay_free(self, client):
        """If the subscription lapses, what you entered has to stay visible and
        deletable: otherwise it looks as though your data has vanished."""
        rivals.add_rival("@someone")
        listed = client.get("/api/rivals")
        assert listed.status_code == 200
        assert [r["handle"] for r in listed.json()["rivals"]] == ["@someone"]

        rival_id = listed.json()["rivals"][0]["id"]
        assert client.delete(f"/api/rivals/{rival_id}").status_code == 200
        assert client.get("/api/rivals").json()["rivals"] == []
