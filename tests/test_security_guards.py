"""
Il guardiano che rende sicuro un server in ascolto su localhost.

Questi test esistono perche' la protezione e' invisibile: se un giorno
qualcuno spostasse o togliesse il middleware, l'app continuerebbe a
funzionare perfettamente durante l'uso normale, e nessuno se ne
accorgerebbe finche' una pagina web ostile non leggesse le statistiche
private del cliente o cancellasse i suoi dati.
"""
import pytest


class TestHostGuard:
    """DNS rebinding: un dominio che punta a 127.0.0.1 diventa "stessa
    origine" per il browser. L'unica difesa e' rifiutare gli Host estranei."""

    @pytest.mark.parametrize("host", ["evil.com", "8.8.8.8", "127.0.0.1.evil.com"])
    def test_host_esterno_rifiutato(self, client, host):
        resp = client.get("/api/config", headers={"Host": host})
        assert resp.status_code == 400
        assert resp.json()["error"] == "bad_host"

    @pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "localhost:8787",
                                      "127.0.0.1:9999"])
    def test_host_locale_accettato(self, client, host):
        assert client.get("/api/config", headers={"Host": host}).status_code == 200


class TestOriginGuard:
    """CSRF: un sito aperto in un'altra scheda non deve poter chiamare le
    rotte che cambiano stato. La risposta non la leggerebbe comunque, ma il
    danno (cache svuotata, licenza rimossa) sarebbe gia' fatto."""

    @pytest.mark.parametrize("origin", ["https://evil.com", "null",
                                        "http://127.0.0.1.evil.com"])
    def test_origin_estraneo_rifiutato(self, client, origin):
        resp = client.post("/api/cache/clear", headers={"Origin": origin})
        assert resp.status_code == 403
        assert resp.json()["error"] == "bad_origin"

    def test_origin_locale_accettato(self, client):
        resp = client.post("/api/cache/clear",
                           headers={"Origin": "http://127.0.0.1:8787"})
        assert resp.status_code == 200

    def test_lettura_non_richiede_origin(self, client):
        """I metodi che non cambiano nulla restano liberi: il guardiano
        controlla solo le richieste che scrivono."""
        assert client.get("/api/config", headers={"Origin": "https://evil.com"}).status_code == 200

    def test_richiesta_senza_origin_accettata(self, client):
        """Comportamento attuale, documentato di proposito: un browser
        manda sempre Origin su una POST cross-origin, quindi l'assenza
        indica una chiamata locale legittima (la finestra dell'app, uno
        script dell'utente) e non un attacco dal web."""
        assert client.post("/api/cache/clear").status_code == 200
