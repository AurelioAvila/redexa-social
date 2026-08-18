"""
Fixtures condivise.

Due garanzie che tutti i test devono avere, altrimenti non sono affidabili:

  1. Il database di prova non e' mai quello dell'utente. Tutti i moduli
     leggono cache.DB_PATH al momento della chiamata (non all'import),
     quindi basta riscriverlo per dirottare l'intera app su un file
     temporaneo.

  2. Nessuna chiamata di rete reale. L'avvio dell'app lancia un thread che
     interroga il servizio licenze, e /api/version interroga GitHub: in un
     test diventerebbero lentezza, risultati che cambiano da un giorno
     all'altro e traffico verso servizi veri. Qui la rete e' sbarrata e un
     tentativo fa fallire il test invece di passare inosservato.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Qualsiasi uscita verso l'esterno fa fallire il test, invece di
    partire davvero."""

    def blocked(*args, **kwargs):
        raise AssertionError(
            "Il test ha tentato una chiamata di rete reale. "
            "Sostituisci la funzione con un finto."
        )

    for target in (
        "requests.get",
        "requests.post",
        "requests.put",
        "requests.delete",
        "requests.request",
        "urllib.request.urlopen",
    ):
        monkeypatch.setattr(target, blocked, raising=False)


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Il limitatore di login/registrazione tiene lo stato in un dizionario
    a livello di modulo, condiviso da tutti i test dello stesso processo
    pytest: senza azzerarlo, un test che registra piu' utenti di seguito fa
    scattare il 429 destinato a un client reale che sbaglia password dieci
    volte, non a una suite che ne crea dieci diversi in un secondo."""
    import rate_limit

    rate_limit._attempts.clear()
    yield
    rate_limit._attempts.clear()


@pytest.fixture()
def db_path(monkeypatch, tmp_path):
    """Dirotta l'intera app su un database usa-e-getta."""
    import cache

    path = str(tmp_path / "cache.db")
    monkeypatch.setattr(cache, "DB_PATH", path)
    return path


@pytest.fixture()
def client(db_path, monkeypatch):
    """Client HTTP sull'app vera.

    base_url e' 127.0.0.1 di proposito: il guardiano anti DNS-rebinding
    rifiuta gli Host che non sono locali, e il valore predefinito del
    TestClient ("testserver") verrebbe respinto con 400. Vedere
    test_security_guards per la verifica esplicita del comportamento.
    """
    from fastapi.testclient import TestClient

    import app as backend
    import licensing

    # L'evento di avvio ricontrolla la licenza in rete: qui non deve partire.
    monkeypatch.setattr(licensing, "refresh_if_due", lambda: None, raising=False)

    return TestClient(backend.app, base_url="http://127.0.0.1:8787")


@pytest.fixture()
def registered_user(client):
    """Un utente gia' registrato, con il suo token di sessione."""
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "tester@example.com",
            "password": "Str0ng-Passphrase!42",
            "password_confirm": "Str0ng-Passphrase!42",
            "first_name": "Test",
            "last_name": "User",
            "birth_date": "1990-05-20",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return {"token": data["token"], "user": data["user"], "email": "tester@example.com",
            "password": "Str0ng-Passphrase!42"}


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
