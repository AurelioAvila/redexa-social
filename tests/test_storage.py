"""
What survives and what does not.

The distinction between "cache" (recomputable with a Refresh) and
"configuration" (connected accounts, licence, own credentials) is the rule
most easily broken during a tidy-up, and the most expensive: if "Clear the
cache" also took the connections away, the user would have to redo every OAuth
sign-in without understanding why.

The installation identifier's rule is pinned here too: it has to stay stable.
If it changed with every clean-up, the licence service would see a new computer
and burn an activation each time.
"""
import cache
import connections
import licensing
import own_app


class TestRecomputableCache:
    def test_snapshot_saved_and_read_back(self, db_path):
        cache.save_snapshot("youtube", {"followers": 100})
        assert cache.latest_snapshot("youtube")["followers"] == 100

    def test_clearing_deletes_the_snapshots(self, db_path):
        cache.save_snapshot("youtube", {"followers": 100})
        cache.clear_all()
        assert cache.latest_snapshot("youtube") is None


class TestSavesWithinTheSameSecond:
    """A regression.

    fetched_at has one-second resolution. Two saves close together - two clicks
    on Refresh, or one refresh right after another - end up with the same
    value, and on a tie the ordering was not decided by us but by SQLite, which
    returned insertion order.

    Real consequence: "the latest snapshot" was the older of the two, and the
    numbers appeared to go backwards after a refresh.
    """

    def test_latest_snapshot_really_is_the_latest(self, db_path):
        for n in (1, 2, 3):
            cache.save_snapshot("youtube", {"followers": n})
        assert cache.latest_snapshot("youtube")["followers"] == 3

    def test_history_stays_in_chronological_order(self, db_path):
        for n in (1, 2, 3):
            cache.save_snapshot("youtube", {"followers": n})
        assert [r["followers"] for r in cache.history("youtube")] == [1, 2, 3]

    def test_latest_insight_really_is_the_latest(self, db_path):
        for text in ("first", "second", "third"):
            cache.save_insight(text, based_on_fetch_at=0)
        assert cache.latest_insight()["text"] == "third"


class TestConfigurationSurvives:
    """The heart of the rule: clear_all() must not touch anything the user had
    to configure by hand."""

    def test_connections_survive(self, db_path):
        connections.save_connection("youtube", "Channel", "id-1", {"refresh_token": "x"})
        cache.clear_all()
        assert len(connections.list_connections("youtube")) == 1

    def test_licence_survives(self, db_path):
        licensing._save("SD-PRO-AAAA-BBBB-CCCC-DDDD", "pro", "a@b.it", ok=True)
        cache.clear_all()
        assert licensing.stored()["plan"] == "pro"

    def test_own_apps_survive(self, db_path):
        own_app._conn().execute(
            "INSERT INTO own_apps (platform, client_id, client_secret, created_at)"
            " VALUES ('tiktok', 'key', 'secret', 0)"
        ).connection.commit()
        cache.clear_all()
        assert own_app.get("tiktok")["client_id"] == "key"

    def test_installation_identifier_is_stable(self, db_path):
        """If it changed with every clean-up, each "Clear the cache" would burn
        one licence activation."""
        before = cache.device_id()
        cache.clear_all()
        assert cache.device_id() == before
        assert len(before) == 32


class TestConnections:
    def test_disconnecting_the_last_account_clears_the_numbers(self, db_path):
        """Without this, the dashboard would go on showing the numbers of an
        account that is no longer connected, as if they were still true."""
        connections.save_connection("youtube", "Channel", "id-1", {"refresh_token": "x"})
        cache.save_snapshot("youtube", {"followers": 100})
        connection = connections.list_connections("youtube")[0]

        connections.delete_connection(connection["id"])

        assert connections.list_connections("youtube") == []
        assert cache.latest_snapshot("youtube") is None

    def test_tokens_do_not_reach_the_frontend(self, db_path):
        """public_connections is the version that ends up in the browser: the
        tokens have to stay behind."""
        sentinel = "fake-value-that-must-not-get-out"
        connections.save_connection("youtube", "Channel", "id-1",
                                    {"refresh" + "_token": sentinel})
        public = connections.public_connections()
        assert public and "data" not in public[0]
        assert sentinel not in str(public)

    def test_the_same_account_updated_is_not_duplicated(self, db_path):
        connections.save_connection("youtube", "Old name", "id-1", {"refresh_token": "a"})
        connections.save_connection("youtube", "New name", "id-1", {"refresh_token": "b"})
        listed = connections.list_connections("youtube")
        assert len(listed) == 1
        assert listed[0]["account_name"] == "New name"


class TestCorruptedData:
    """An unreadable row must not break the dashboard.

    This is data the app writes itself, so it is normally valid. But an
    interrupted write (power cut, disk error) would leave one corrupted, and
    the exception used to travel all the way up to the main page: the dashboard
    stayed broken on every open, with no way for the user to understand why.
    """

    def _corrupt(self, db_path, platform="youtube"):
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE snapshots SET data = '{broken' WHERE platform = ?",
                     (platform,))
        conn.commit(); conn.close()

    def test_a_corrupted_latest_snapshot_does_not_raise(self, db_path):
        cache.save_snapshot("youtube", {"followers": 100})
        self._corrupt(db_path)
        assert cache.latest_snapshot("youtube") is None

    def test_history_skips_only_the_corrupted_row(self, db_path):
        cache.save_snapshot("youtube", {"followers": 1})
        cache.save_snapshot("youtube", {"followers": 2})
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE snapshots SET data = 'not-json' WHERE rowid = 1")
        conn.commit(); conn.close()

        history = cache.history("youtube")
        assert [r["followers"] for r in history] == [2], (
            "the good row has to survive the corrupted one"
        )

    def test_a_corrupted_generic_cache_behaves_as_empty(self, db_path):
        cache.kv_set("probe", {"x": 1})
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE kv_cache SET data = '{'")
        conn.commit(); conn.close()

        assert cache.kv_get("probe", max_age_seconds=10**9) is None


class TestAFailedFetchIsNotHistory:
    """A refresh that fails is saved as a snapshot like any other, with no
    channels in it. The trend extractors read the missing list as empty and
    record 0, which is indistinguishable from a real reading of zero: turn
    the Wi-Fi off, press Refresh, and the Pro chart takes a permanent -100%
    drop alert, because history is append-only and nothing removes it."""

    def test_the_error_row_does_not_enter_the_series(self, db_path):
        cache.save_snapshot("youtube", {"followers": 1000, "ok": True})
        cache.save_snapshot("youtube", {"platform": "youtube", "ok": False, "error": "no network"})

        assert [r.get("followers") for r in cache.history("youtube")] == [1000]

    def test_the_most_recent_snapshot_still_sees_it(self, db_path):
        """Filtered out of the series, not deleted: latest_snapshot and the
        error text go on reading it."""
        cache.save_snapshot("youtube", {"followers": 1000, "ok": True})
        cache.save_snapshot("youtube", {"platform": "youtube", "ok": False, "error": "no network"})

        assert cache.latest_snapshot("youtube").get("ok") is False

    def test_a_valid_reading_of_zero_stays_in_history(self, db_path):
        """The filter looks at ok, not at the value: a brand-new channel really
        at zero is data, and disappearing from the charts would be the opposite
        mistake."""
        cache.save_snapshot("youtube", {"followers": 0, "ok": True})

        assert [r.get("followers") for r in cache.history("youtube")] == [0]

    def test_the_100_percent_drop_no_longer_appears(self, db_path):
        import trends

        cache.save_snapshot("youtube", {"channels": [{"ok": True, "subscribers": 1000}]})
        cache.save_snapshot("youtube", {"platform": "youtube", "ok": False, "error": "429"})

        computed = trends.compute_trends().get("youtube") or {}
        delta = ((computed.get("primary") or {}).get("delta")) or {}
        assert delta.get("pct") != -100.0, "a failed refresh is not a collapse"
