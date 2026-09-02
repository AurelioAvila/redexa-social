"""
La politica di rilancio delle chiamate alle API delle piattaforme.

Quello che conta bloccare qui non e' che il rilancio esista - e' cosa NON
viene rilanciato. Un ciclo che ritenta qualsiasi errore, che e' quello che
faceva youtube.py, su un 401 spende il tempo dell'utente per arrivare alla
stessa risposta e martella un endpoint con una credenziale gia' rifiutata,
che e' il modo in cui una chiave sviluppatore viene sospesa.

L'altra meta' e' l'attesa. `Retry-After: 900` non e' raro, e obbedirgli alla
lettera dentro un aggiornamento di una dashboard desktop congela
l'interfaccia per un quarto d'ora: il tetto e' una decisione di prodotto, non
un dettaglio, quindi e' verificata.

Nessuna rete e nessuna attesa vera: `requester` e `sleep` sono iniettati.
"""
import pytest
import requests

from platforms import _http


class FakeResponse:
    def __init__(self, status_code, retry_after=None):
        self.status_code = status_code
        self.headers = {} if retry_after is None else {"Retry-After": retry_after}


def fake_requester(*responses):
    """Risponde con la sequenza data, e registra come e' stata chiamata."""
    calls = []

    def call(method, url, **kwargs):
        calls.append((method, url))
        item = responses[min(len(calls) - 1, len(responses) - 1)]
        if isinstance(item, Exception):
            raise item
        return item

    call.calls = calls
    return call


def recording_sleep():
    waits = []
    return waits, waits.append


def test_una_risposta_buona_non_dorme_e_non_ritenta():
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(200))

    resp = _http.get("https://example.test", requester=call, sleep=sleep)

    assert resp.status_code == 200
    assert len(call.calls) == 1
    assert waits == []


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
def test_un_rifiuto_definitivo_torna_subito(status):
    """Il 401 e' il caso che conta: e' un token revocato, e ritentarlo non
    lo fa tornare valido."""
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(status))

    resp = _http.get("https://example.test", requester=call, sleep=sleep)

    assert resp.status_code == status
    assert len(call.calls) == 1, f"{status} non deve essere ritentato"
    assert waits == []


@pytest.mark.parametrize("status", [429, 500, 502, 503])
def test_un_rifiuto_temporaneo_viene_ritentato(status):
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(status), FakeResponse(200))

    resp = _http.get("https://example.test", requester=call, sleep=sleep)

    assert resp.status_code == 200
    assert len(call.calls) == 2
    assert waits == [_http.BACKOFF[0]]


def test_retry_after_della_piattaforma_batte_il_nostro_backoff():
    """Un'attesa inventata piu' corta di quella richiesta e' peggio di
    nessun rilancio: spende il budget rimasto all'account discutendo."""
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(429, retry_after="7"), FakeResponse(200))

    _http.get("https://example.test", requester=call, sleep=sleep)

    assert waits == [7.0]


def test_un_retry_after_assurdo_viene_tagliato():
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(429, retry_after="900"), FakeResponse(200))

    _http.get("https://example.test", requester=call, sleep=sleep)

    assert waits == [_http.MAX_WAIT]
    assert sum(waits) <= _http.MAX_TOTAL_WAIT


def test_un_retry_after_illeggibile_ricade_sul_backoff():
    """La forma HTTP-date e' legale. Non la interpretiamo, ma non deve far
    saltare la chiamata."""
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(429, retry_after="Wed, 21 Oct 2026 07:28:00 GMT"),
                          FakeResponse(200))

    resp = _http.get("https://example.test", requester=call, sleep=sleep)

    assert resp.status_code == 200
    assert waits == [_http.BACKOFF[0]]


def test_dopo_l_ultimo_tentativo_torna_il_rifiuto_invece_di_sollevare():
    """Il chiamante fa raise_for_status(): deve continuare a comportarsi
    come prima, quindi qui torna la risposta, non un'eccezione."""
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(429))

    resp = _http.get("https://example.test", requester=call, sleep=sleep)

    assert resp.status_code == 429
    assert len(call.calls) == _http.ATTEMPTS
    assert len(waits) == _http.ATTEMPTS - 1


def test_un_errore_di_rete_viene_ritentato_e_alla_fine_sollevato():
    waits, sleep = recording_sleep()
    call = fake_requester(requests.exceptions.ConnectionError("rete giu'"))

    with pytest.raises(requests.exceptions.ConnectionError):
        _http.get("https://example.test", requester=call, sleep=sleep)

    assert len(call.calls) == _http.ATTEMPTS


def test_una_rete_che_torna_su_non_fa_fallire_la_chiamata():
    """Il caso per cui il rilancio esiste: un pacchetto perso non deve
    marcare un account come rotto, altrimenti la parola 'fallito' smette di
    voler dire qualcosa e passa inosservato anche il token revocato."""
    waits, sleep = recording_sleep()
    call = fake_requester(requests.exceptions.Timeout("scaduto"), FakeResponse(200))

    resp = _http.get("https://example.test", requester=call, sleep=sleep)

    assert resp.status_code == 200
    assert len(call.calls) == 2


def test_il_tempo_speso_ad_aspettare_ha_un_tetto_complessivo():
    waits, sleep = recording_sleep()
    call = fake_requester(FakeResponse(429, retry_after="20"))

    _http.get("https://example.test", attempts=6, requester=call, sleep=sleep)

    assert sum(waits) <= _http.MAX_TOTAL_WAIT


def test_il_metodo_e_l_url_arrivano_intatti():
    call = fake_requester(FakeResponse(200))

    _http.post("https://example.test/token", requester=call, sleep=lambda _: None)

    assert call.calls == [("POST", "https://example.test/token")]
