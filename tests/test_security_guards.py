"""
The guard that makes a server listening on localhost safe.

These tests exist because the protection is invisible: if somebody moved or
removed the middleware one day, the app would keep working perfectly in normal
use and nobody would notice, until a hostile web page read the customer's
private statistics or deleted their data.
"""
import pytest


class TestHostGuard:
    """DNS rebinding: a domain pointing at 127.0.0.1 becomes "same origin" as
    far as the browser is concerned. The only defence is refusing foreign
    Hosts."""

    @pytest.mark.parametrize("host", ["evil.com", "8.8.8.8", "127.0.0.1.evil.com"])
    def test_external_host_refused(self, client, host):
        resp = client.get("/api/config", headers={"Host": host})
        assert resp.status_code == 400
        assert resp.json()["error"] == "bad_host"

    @pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "localhost:8787",
                                      "127.0.0.1:9999"])
    def test_local_host_accepted(self, client, host):
        assert client.get("/api/config", headers={"Host": host}).status_code == 200


class TestOriginGuard:
    """CSRF: a site open in another tab must not be able to call the routes
    that change state. It would not get to read the response anyway, but the
    damage (cache cleared, licence removed) would already be done."""

    @pytest.mark.parametrize("origin", ["https://evil.com", "null",
                                        "http://127.0.0.1.evil.com"])
    def test_foreign_origin_refused(self, client, origin):
        resp = client.post("/api/cache/clear", headers={"Origin": origin})
        assert resp.status_code == 403
        assert resp.json()["error"] == "bad_origin"

    def test_local_origin_accepted(self, client):
        resp = client.post("/api/cache/clear",
                           headers={"Origin": "http://127.0.0.1:8787"})
        assert resp.status_code == 200

    def test_reads_do_not_require_an_origin(self, client):
        """Methods that change nothing stay open: the guard only inspects the
        requests that write."""
        assert client.get("/api/config", headers={"Origin": "https://evil.com"}).status_code == 200

    def test_request_without_origin_accepted(self, client):
        """Current behaviour, documented deliberately: a browser always sends
        Origin on a cross-origin POST, so its absence indicates a legitimate
        local call (the app's own window, a script of the user's) and not an
        attack from the web."""
        assert client.post("/api/cache/clear").status_code == 200
