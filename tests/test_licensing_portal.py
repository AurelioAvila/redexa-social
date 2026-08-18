"""
Il portale clienti Stripe e' l'unico posto dove un abbonamento si disdice
davvero. "Rimuovi" nell'interfaccia stacca solo la chiave da questo
computer, ma lascia l'abbonamento a rinnovarsi: senza questo endpoint
l'utente non avrebbe alcun modo, dentro l'app, di annullarlo per davvero.
"""
import licensing


class _RispostaFinta:
    def __init__(self, status=200, corpo=None):
        self.ok = status < 400
        self.status_code = status
        self._corpo = corpo or {}

    def json(self):
        return self._corpo


class TestPortaleFatturazione:
    def test_senza_licenza_salvata(self, db_path):
        esito = licensing.billing_portal_url()
        assert esito == {"ok": False, "code": "license_missing"}

    def test_senza_servizio_configurato(self, db_path, monkeypatch):
        licensing._save("SD-PRO-AAAA-BBBB-CCCC-DDDD", "pro", "a@b.it", ok=True)
        monkeypatch.setattr(licensing, "_service_url", lambda: "")
        esito = licensing.billing_portal_url()
        assert esito == {"ok": False, "code": "license_service_unavailable"}

    def test_url_restituito_dal_servizio(self, db_path, monkeypatch):
        licensing._save("SD-PRO-AAAA-BBBB-CCCC-DDDD", "pro", "a@b.it", ok=True)
        monkeypatch.setattr(licensing, "_service_url", lambda: "https://esempio.workers.dev")

        import requests

        def finto_post(url, json=None, timeout=None):
            assert url == "https://esempio.workers.dev/billing/portal"
            assert json == {"key": "SD-PRO-AAAA-BBBB-CCCC-DDDD"}
            return _RispostaFinta(200, {"url": "https://billing.stripe.com/session/xyz"})

        monkeypatch.setattr(requests, "post", finto_post)
        esito = licensing.billing_portal_url()
        assert esito == {"ok": True, "url": "https://billing.stripe.com/session/xyz"}

    def test_chiave_senza_cliente_stripe(self, db_path, monkeypatch):
        """Es. una licenza emessa a mano, mai passata da un pagamento Stripe:
        il Worker risponde license_not_found, e va mostrato cosi' com'e'."""
        licensing._save("SD-PRO-AAAA-BBBB-CCCC-DDDD", "pro", "a@b.it", ok=True)
        monkeypatch.setattr(licensing, "_service_url", lambda: "https://esempio.workers.dev")

        import requests

        monkeypatch.setattr(
            requests, "post",
            lambda *a, **k: _RispostaFinta(400, {"error": "license_not_found"}),
        )
        esito = licensing.billing_portal_url()
        assert esito == {"ok": False, "code": "license_not_found"}

    def test_servizio_irraggiungibile(self, db_path, monkeypatch):
        licensing._save("SD-PRO-AAAA-BBBB-CCCC-DDDD", "pro", "a@b.it", ok=True)
        monkeypatch.setattr(licensing, "_service_url", lambda: "https://esempio.workers.dev")

        import requests

        def scoppia(*a, **k):
            raise RuntimeError("rete assente")

        monkeypatch.setattr(requests, "post", scoppia)
        esito = licensing.billing_portal_url()
        assert esito == {"ok": False, "code": "license_service_unavailable"}
