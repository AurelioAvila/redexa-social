import csv
import io

import analytics
import app


def test_multiaccount_engagement_uses_each_posts_own_audience():
    def channel(followers, likes, posts=1):
        return {"ok": True, "name": "Same display name", "subscribers": followers,
                "recent_videos": [{"views": 1000, "likes": likes}] * posts}

    result = analytics.compute_analytics({"youtube": {"channels": [
        channel(5000, 100), channel(5000, 100),
    ]}})
    assert result["engagement_per_platform"]["youtube"]["follower_rate"] == 2.0
    assert result["benchmarks"] == []  # A pooled audience is not an account tier.

    result = analytics.compute_analytics({"youtube": {"channels": [
        channel(1000, 100, 2), channel(10000, 200),
    ]}})
    assert result["engagement_per_platform"]["youtube"]["follower_rate"] == 3.33


def test_unknown_follower_count_does_not_produce_a_misleading_ratio():
    accounts = [{"ok": True, "followers": followers,
                 "recent_posts": [{"views": 1000, "likes": 100}]}
                for followers in (1000, None)]
    result = analytics.compute_analytics({"instagram": {"accounts": accounts}})
    assert "follower_rate" not in result["engagement_per_platform"]["instagram"]
    assert result["benchmarks"] == []


def test_csv_treats_external_cells_as_text_and_preserves_numbers(client, monkeypatch):
    monkeypatch.setattr(app, "_current_plan", lambda _: "pro")
    snapshots = {
        "youtube": {"channels": [{"ok": True, "name": '=HYPERLINK("https://example.com")',
                                    "subscribers": 125}]},
        "instagram": {"accounts": [{"ok": True, "name": " +SUM(1,2)", "followers": 50,
                                     "totals_last_n": {"@formula": "\t=1+1"}}]},
        "tiktok": {"accounts": [{"ok": True, "name": "-formula",
                                  "totals_last_n": {"views": 500}}]},
    }
    monkeypatch.setattr(app.cache, "latest_snapshot", snapshots.get)
    response = client.get("/api/export.csv")
    assert response.status_code == 200
    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[1][1].startswith("'=")
    assert rows[1][3] == "125"
    assert any(row[1].startswith("' +") for row in rows)
    assert any(row[2:] == ["'@formula", "'\t=1+1"] for row in rows)
    assert rows[-1] == ["tiktok", "'-formula", "views", "500"]


def test_csv_control_prefixes_and_normal_values():
    for value in ("=1+1", "+1", "-1", "@SUM(1)", "\ttext", "\rtext", "\ntext", "  =1"):
        assert app._csv_cell(value) == "'" + value
    for value in ("Normal account", 42, -42, 3.2, None):
        assert app._csv_cell(value) == value
