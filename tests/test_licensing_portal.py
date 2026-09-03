"""
The Stripe customer portal is the only place a subscription is really
cancelled. "Remove" in the interface only detaches the key from this computer
and leaves the subscription renewing: without this endpoint the user would
have no way, inside the app, of actually cancelling it.
"""
import licensing


class _FakeResponse:
    def __init__(self, status=200, body=None):
        self.ok = status < 400
        self.status_code = status
        self._body = body or {}

    def json(self):
        return self._body


class TestBillingPortal:
    def test_with_no_saved_licence(self, db_path):
        result = licensing.billing_portal_url()
        assert result == {"ok": False, "code": "license_missing"}

    def test_with_no_service_configured(self, db_path, monkeypatch):
        licensing._save("SD-PRO-AAAA-BBBB-CCCC-DDDD", "pro", "a@b.it", ok=True)
        monkeypatch.setattr(licensing, "_service_url", lambda: "")
        result = licensing.billing_portal_url()
        assert result == {"ok": False, "code": "license_service_unavailable"}

    def test_url_returned_by_the_service(self, db_path, monkeypatch):
        licensing._save("SD-PRO-AAAA-BBBB-CCCC-DDDD", "pro", "a@b.it", ok=True)
        monkeypatch.setattr(licensing, "_service_url", lambda: "https://example.workers.dev")

        import requests

        def fake_post(url, json=None, timeout=None):
            assert url == "https://example.workers.dev/billing/portal"
            assert json == {"key": "SD-PRO-AAAA-BBBB-CCCC-DDDD"}
            return _FakeResponse(200, {"url": "https://billing.stripe.com/session/xyz"})

        monkeypatch.setattr(requests, "post", fake_post)
        result = licensing.billing_portal_url()
        assert result == {"ok": True, "url": "https://billing.stripe.com/session/xyz"}

    def test_key_with_no_stripe_customer(self, db_path, monkeypatch):
        """E.g. a licence issued by hand that never went through a Stripe
        payment: the Worker answers license_not_found, and that is shown as
        it is."""
        licensing._save("SD-PRO-AAAA-BBBB-CCCC-DDDD", "pro", "a@b.it", ok=True)
        monkeypatch.setattr(licensing, "_service_url", lambda: "https://example.workers.dev")

        import requests

        monkeypatch.setattr(
            requests, "post",
            lambda *a, **k: _FakeResponse(400, {"error": "license_not_found"}),
        )
        result = licensing.billing_portal_url()
        assert result == {"ok": False, "code": "license_not_found"}

    def test_service_unreachable(self, db_path, monkeypatch):
        licensing._save("SD-PRO-AAAA-BBBB-CCCC-DDDD", "pro", "a@b.it", ok=True)
        monkeypatch.setattr(licensing, "_service_url", lambda: "https://example.workers.dev")

        import requests

        def blow_up(*a, **k):
            raise RuntimeError("no network")

        monkeypatch.setattr(requests, "post", blow_up)
        result = licensing.billing_portal_url()
        assert result == {"ok": False, "code": "license_service_unavailable"}
