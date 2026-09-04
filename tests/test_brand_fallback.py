"""Development builds remain usable before private brand.py is supplied."""

import billing
import own_app


def test_pricing_loads_without_private_brand_module(monkeypatch):
    monkeypatch.delenv("OAUTH_PROXY_URL", raising=False)

    result = billing.list_plans()

    assert result["plans"]
    assert result["checkout_ready"] is False


def test_connection_wizard_loads_without_private_brand_module(monkeypatch):
    monkeypatch.delenv("INSTAGRAM_REDIRECT_URI", raising=False)
    monkeypatch.delenv("TIKTOK_REDIRECT_URI", raising=False)

    assert own_app.redirect_uri("instagram") == ""
    assert own_app.redirect_uri("tiktok") == ""
