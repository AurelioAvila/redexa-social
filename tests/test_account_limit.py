"""The account limit has to hold on every way in, not on the tidy one.

`/api/connections/connect/{platform}` checked `plans.max_accounts` before
opening the browser. The guided paste flow did not — and that flow is not an
alternative anybody chose: Instagram and TikTok refuse a redirect to
127.0.0.1, so it is the only way to connect either of them. A Free account,
capped at one, could add as many as it liked through the two platforms that
require it.

The check now lives in `connections.save_connection`, where all three
connectors converge, and it asks `licensing.current_plan()` itself rather
than taking the plan as an argument — the plan became a fact about the
installation, not about the request, so there is no header to plumb through
and no caller who can forget it.
"""
import pytest

import connections
import licensing
import plans


def _stored(platform, account_id, name="acct"):
    connections.save_connection(platform, name, account_id, {"token": "x"})


@pytest.fixture()
def free_plan(db_path, monkeypatch):
    monkeypatch.setattr(licensing, "current_plan", lambda: plans.FREE)
    return db_path


@pytest.fixture()
def pro_plan(db_path, monkeypatch):
    monkeypatch.setattr(licensing, "current_plan", lambda: plans.PRO)
    return db_path


class TestTheCapHoldsWhereverTheAccountArrives:
    def test_free_stops_at_one_account(self, free_plan):
        _stored("youtube", "chan-1")

        with pytest.raises(connections.PlanAccountLimit) as refused:
            _stored("instagram", "insta-1")

        assert refused.value.limit == 1
        assert len(connections.public_connections()) == 1

    def test_the_refusal_carries_the_code_the_interface_already_knows(self, free_plan):
        _stored("youtube", "chan-1")

        with pytest.raises(connections.PlanAccountLimit) as refused:
            _stored("tiktok", "tok-1")

        # start_connect's worker reports str(exc), and this is the message the
        # pre-check already returns, so both paths speak the same code.
        assert str(refused.value) == "plan_account_limit"

    def test_pro_allows_three_and_refuses_the_fourth(self, pro_plan):
        for n in range(3):
            _stored("youtube", f"chan-{n}")

        with pytest.raises(connections.PlanAccountLimit):
            _stored("youtube", "chan-4")

        assert len(connections.public_connections()) == 3


class TestWhatMustStillWork:
    def test_reconnecting_an_account_already_stored_is_never_refused(self, free_plan):
        """save_connection is an upsert. Someone re-authorising the account
        they already have is not adding one, and refusing them would lock a
        Free user out of fixing their own expired token."""
        _stored("youtube", "chan-1", name="before")

        _stored("youtube", "chan-1", name="after")

        rows = connections.public_connections()
        assert len(rows) == 1
        assert rows[0]["account_name"] == "after"

    def test_the_first_account_on_a_fresh_install_goes_in(self, free_plan):
        _stored("youtube", "chan-1")
        assert len(connections.public_connections()) == 1


class TestTheGuidedFlowReportsTheRealReason:
    def test_the_limit_is_not_disguised_as_a_failed_connection(self, free_plan, monkeypatch):
        """finish_guided used to collapse every exception into
        "connect_failed", which would have told a user whose authorisation
        worked perfectly that it had not."""
        _stored("youtube", "chan-1")

        monkeypatch.setitem(connections.GUIDED, "instagram",
                            lambda code: _stored("instagram", "insta-1"))
        monkeypatch.setattr(connections, "_check_state", lambda platform, state: None)
        monkeypatch.setattr(connections, "coming_soon", lambda platform: False)

        result = connections.finish_guided("instagram", "https://example.test/?code=abc&state=s")

        assert result["ok"] is False
        assert result["message"] == "plan_account_limit"
        assert result["limit"] == 1

    def test_a_genuine_failure_still_reads_as_one(self, pro_plan, monkeypatch):
        def boom(code):
            raise RuntimeError("the platform said no")

        monkeypatch.setitem(connections.GUIDED, "instagram", boom)
        monkeypatch.setattr(connections, "_check_state", lambda platform, state: None)
        monkeypatch.setattr(connections, "coming_soon", lambda platform: False)

        result = connections.finish_guided("instagram", "https://example.test/?code=abc&state=s")

        assert result["message"] == "connect_failed"
