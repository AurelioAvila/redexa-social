"""Development builds remain usable before private brand.py is supplied."""

import builtins

import billing
import own_app


def hide_private_brand(monkeypatch):
    real_import = builtins.__import__

    def import_without_brand(name, *args, **kwargs):
        if name == "brand":
            raise ModuleNotFoundError("brand.py intentionally unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_brand)


def test_pricing_loads_without_private_brand_module(monkeypatch):
    hide_private_brand(monkeypatch)
    monkeypatch.delenv("OAUTH_PROXY_URL", raising=False)

    result = billing.list_plans()

    assert result["plans"]
    assert result["checkout_ready"] is False


def test_connection_wizard_loads_without_private_brand_module(monkeypatch):
    hide_private_brand(monkeypatch)
    monkeypatch.delenv("INSTAGRAM_REDIRECT_URI", raising=False)
    monkeypatch.delenv("TIKTOK_REDIRECT_URI", raising=False)

    assert own_app.redirect_uri("instagram") == ""
    assert own_app.redirect_uri("tiktok") == ""
