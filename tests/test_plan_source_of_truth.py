"""Two ways a free installation used to hold a paid plan.

Both are the same mistake in different clothes: the server asked something
the customer controls, and believed the answer.

  1. `_current_plan` took the more generous of the verified licence and
     `users.plan` — a column in cache.db, on the customer's own disk, outside
     the DPAPI protection that covers connection tokens. `auth.set_plan` is
     its only writer and has no callers, so it was never legitimately
     anything but 'free'; it existed purely as a trusted input the adversary
     owned. One UPDATE unlocked history, best hours, rivals, CSV export and
     the ten-account cap, with the licence still answering 'free'.

  2. The grace period was measured with `time.time()`. Move the Windows clock
     back and `age` went negative, never exceeded GRACE_SECONDS, and the plan
     never lapsed — while `refresh_if_due` read the same negative interval as
     "not due yet" and stopped asking the service anything at all. Activate
     once, cancel, set the date back: Pro forever, and the UI showed a
     healthy licence with no stale flag.

`rate_limit.py` already got this right with `time.monotonic()`. These tests
exist so the licence stays the only thing that decides.
"""
import sqlite3

import cache
import licensing
import plans
from conftest import auth_headers


class TestTheLocalDatabaseCannotGrantAPlan:
    def test_editing_users_plan_by_hand_unlocks_nothing(self, client, registered_user):
        token = registered_user["token"]
        assert client.get("/api/export.csv", headers=auth_headers(token)).status_code == 403

        conn = sqlite3.connect(cache.DB_PATH)
        try:
            conn.execute("UPDATE users SET plan = 'studio'")
            conn.commit()
        finally:
            conn.close()

        # Same request, same account, a plan column that now says studio.
        assert client.get("/api/export.csv", headers=auth_headers(token)).status_code == 403, (
            "a paid endpoint answered because of a value written into the "
            "customer's own database file"
        )

    def test_the_snapshot_does_not_report_a_hand_written_plan(self, client, registered_user):
        conn = sqlite3.connect(cache.DB_PATH)
        try:
            conn.execute("UPDATE users SET plan = 'studio'")
            conn.commit()
        finally:
            conn.close()

        body = client.get("/api/snapshot", headers=auth_headers(registered_user["token"])).json()

        assert body["entitlements"]["plan"] == plans.FREE
        assert body["entitlements"]["csv_export"] is False
        assert body["rivals"] is None


class TestTheClockCannotExtendAPlan:
    def test_a_clock_moved_back_does_not_keep_the_plan(self, db_path, monkeypatch):
        licensing._save("KEY-1", plans.PRO, "a@b.test", ok=True)
        assert licensing.current_plan() == plans.PRO

        # A year earlier than the last successful check: not a young licence,
        # an unusable reading.
        real = licensing.time.time()
        monkeypatch.setattr(licensing.time, "time", lambda: real - 365 * 24 * 3600)

        assert licensing.current_plan() == plans.FREE

    def test_a_clock_moved_back_makes_the_recheck_due_again(self, db_path, monkeypatch):
        licensing._save("KEY-2", plans.PRO, "a@b.test", ok=True)

        real = licensing.time.time()
        monkeypatch.setattr(licensing.time, "time", lambda: real - 365 * 24 * 3600)

        asked = []
        monkeypatch.setattr(licensing, "_ask_service", lambda key: asked.append(key) or {"valid": False})

        licensing.refresh_if_due()

        assert asked == ["KEY-2"], "a backwards clock must not silence the recheck"
        assert licensing.current_plan() == plans.FREE

    def test_the_grace_period_still_covers_an_unreachable_service(self, db_path, monkeypatch):
        """The guard must not cost a paying customer their plan when the only
        thing wrong is the network."""
        licensing._save("KEY-3", plans.PRO, "a@b.test", ok=True)

        real = licensing.time.time()
        monkeypatch.setattr(licensing.time, "time", lambda: real + 3 * 24 * 3600)

        def unreachable(_key):
            raise RuntimeError("service down")

        monkeypatch.setattr(licensing, "_ask_service", unreachable)
        licensing.refresh_if_due()

        assert licensing.current_plan() == plans.PRO

    def test_a_plan_still_lapses_once_the_grace_period_runs_out(self, db_path, monkeypatch):
        licensing._save("KEY-4", plans.PRO, "a@b.test", ok=True)

        real = licensing.time.time()
        monkeypatch.setattr(licensing.time, "time", lambda: real + licensing.GRACE_SECONDS + 60)

        assert licensing.current_plan() == plans.FREE


class TestNotEveryRefusalIsARevocation:
    """The service distinguishes "you are not entitled" from "this device is
    not on the key's list". Recording the second as revocation cost a paying
    customer their plan with no grace the moment their device id changed —
    a reinstall or a hardware change is enough."""

    def _answer(self, monkeypatch, payload):
        """Make the recheck genuinely due by moving the clock forward past
        RECHECK_SECONDS, rather than reaching into the stored row: that is
        the path production takes, and it also puts last_check ahead of
        last_ok the way a real recheck a day later does."""
        monkeypatch.setattr(licensing, "_ask_service", lambda key: payload)
        real = licensing.time.time()
        monkeypatch.setattr(
            licensing.time, "time", lambda: real + licensing.RECHECK_SECONDS + 60
        )

    def test_a_device_that_needs_reactivating_keeps_the_plan_for_now(self, db_path, monkeypatch):
        licensing._save("KEY-5", plans.PRO, "a@b.test", ok=True)
        self._answer(monkeypatch, {"valid": False, "reason": "license_reactivate_needed"})

        licensing.refresh_if_due()

        assert licensing.stored()["revoked"] is False
        assert licensing.current_plan() == plans.PRO
        assert licensing.status()["stale"] is True, "the customer has to be told to reactivate"

    def test_the_device_limit_is_not_a_revocation_either(self, db_path, monkeypatch):
        licensing._save("KEY-6", plans.PRO, "a@b.test", ok=True)
        self._answer(monkeypatch, {"valid": False, "reason": "license_device_limit", "limit": 1})

        licensing.refresh_if_due()

        assert licensing.stored()["revoked"] is False
        assert licensing.current_plan() == plans.PRO

    def test_a_cancelled_subscription_still_revokes_at_once(self, db_path, monkeypatch):
        licensing._save("KEY-7", plans.PRO, "a@b.test", ok=True)
        self._answer(monkeypatch, {"valid": False, "reason": "license_inactive"})

        licensing.refresh_if_due()

        assert licensing.stored()["revoked"] is True
        assert licensing.current_plan() == plans.FREE

    def test_an_unknown_key_revokes_too(self, db_path, monkeypatch):
        licensing._save("KEY-8", plans.PRO, "a@b.test", ok=True)
        self._answer(monkeypatch, {"valid": False, "reason": "license_not_found"})

        licensing.refresh_if_due()

        assert licensing.stored()["revoked"] is True

    def test_an_answer_with_no_reason_at_all_revokes(self, db_path, monkeypatch):
        """Fail closed on a shape we do not recognise."""
        licensing._save("KEY-9", plans.PRO, "a@b.test", ok=True)
        self._answer(monkeypatch, {"valid": False})

        licensing.refresh_if_due()

        assert licensing.stored()["revoked"] is True
