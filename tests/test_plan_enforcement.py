"""
Plan limits have to hold on the server, not only in the interface.

A padlock drawn in the frontend comes off with ten seconds of developer tools.
If the refusal does not come from the server, the paid plan is a polite
request. These tests call the APIs directly, skipping the interface, exactly
as somebody trying to get around them would.
"""
import config
import plans


class TestPlanTable:
    def test_free_does_not_include_the_paid_features(self):
        assert plans.allows("free", "csv_export") is False
        assert plans.allows("free", "history") is False
        assert plans.allows("free", "best_hours") is False

    def test_pro_and_studio_do_include_them(self):
        for plan in ("pro", "studio"):
            assert plans.allows(plan, "csv_export") is True
            assert plans.allows(plan, "history") is True

    def test_unknown_plan_treated_as_free(self):
        """A corrupted or invented value must unlock nothing."""
        assert plans.allows("made-up-plan", "csv_export") is False
        assert plans.allows("", "csv_export") is False
        assert plans.allows(None, "csv_export") is False

    def test_account_limits_increase(self):
        assert plans.max_accounts("free") == 1
        assert plans.max_accounts("pro") == 3
        assert plans.max_accounts("studio") == 10


class TestRefusalFromTheServer:
    def test_csv_export_denied_without_a_licence(self, client):
        """A direct API call, not going through the interface."""
        resp = client.get("/api/export.csv")
        assert resp.status_code == 403, (
            "CSV export is a paid feature: the server has to refuse it, not "
            "merely hide the button"
        )

    def test_csv_export_allowed_with_a_pro_licence(self, client, db_path, monkeypatch):
        import licensing

        licensing._save("SD-PRO-AAAA-BBBB-CCCC-DDDD", "pro", "a@b.it", ok=True)
        resp = client.get("/api/export.csv")
        assert resp.status_code == 200

    def test_snapshot_without_a_licence_does_not_expose_history(self, client, db_path):
        """History is a Pro feature: on the free plan the server must not even
        send it, otherwise looking at the response is enough."""
        import cache

        cache.save_snapshot("youtube", {"followers": 10})
        cache.save_snapshot("youtube", {"followers": 20})

        data = client.get("/api/snapshot").json()
        entitlements = data.get("entitlements", {})
        assert entitlements.get("history") is False

        # This used to iterate data["platforms"], a key /api/snapshot has
        # never built, so the loop body never ran once and the guard this
        # test is named after was never checked. The history the docstring
        # is about travels in "trends", which is where it has to be empty.
        assert data.get("trends") == {}, (
            "history must not appear in the response on a free plan"
        )
        for platform in config.enabled_platforms():
            # `or {}`, not a get default: a platform with no snapshot yet is
            # present with the value None, and a default only applies to a
            # key that is absent.
            assert not (data.get(platform) or {}).get("history"), (
                f"{platform}'s history must not appear on a free plan"
            )
