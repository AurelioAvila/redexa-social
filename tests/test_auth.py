"""
Registrazione, accesso e sessioni.

Le password sono l'unica cosa in questa app che, se gestita male, fa danno
anche fuori dal computer dell'utente: le persone le riutilizzano altrove.
Questi test bloccano il comportamento attuale (PBKDF2, confronto a tempo
costante, in archivio solo l'impronta del token) in modo che una riscrittura
non possa indebolirlo per sbaglio.
"""
from conftest import auth_headers


class TestRegistrazione:
    def test_crea_utente_e_restituisce_sessione(self, client):
        resp = client.post("/api/auth/register", json={
            "email": "nuovo@example.com",
            "password": "Str0ng-Passphrase!42",
            "password_confirm": "Str0ng-Passphrase!42",
            "first_name": "Ada", "last_name": "Lovelace",
            "birth_date": "1990-05-20",
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["token"]
        assert data["user"]["email"] == "nuovo@example.com"
        assert data["user"]["plan"] == "free"
        assert "password" not in str(data), "la risposta non deve contenere la password"

    def test_email_duplicata_rifiutata(self, client, registered_user):
        resp = client.post("/api/auth/register", json={
            "email": registered_user["email"],
            "password": "Altra-Password!99",
            "password_confirm": "Altra-Password!99",
            "first_name": "Altro", "last_name": "Utente",
            "birth_date": "1990-05-20",
        })
        assert resp.status_code == 400
        assert resp.json()["detail"] == "err_email_taken"

    def test_password_non_coincidenti_rifiutate(self, client):
        resp = client.post("/api/auth/register", json={
            "email": "tizio@example.com",
            "password": "Str0ng-Passphrase!42",
            "password_confirm": "Diversa!42",
            "first_name": "Tizio", "last_name": "Caio",
            "birth_date": "1990-05-20",
        })
        assert resp.status_code == 400
        assert resp.json()["detail"] == "err_password_mismatch"


class TestAccesso:
    def test_credenziali_corrette(self, client, registered_user):
        resp = client.post("/api/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert resp.status_code == 200
        assert resp.json()["token"]

    def test_password_sbagliata(self, client, registered_user):
        resp = client.post("/api/auth/login", json={
            "email": registered_user["email"], "password": "sbagliata",
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "err_bad_credentials"

    def test_utente_inesistente_stesso_errore(self, client):
        """Identico al caso "password sbagliata": distinguerli rivelerebbe
        quali email sono registrate."""
        resp = client.post("/api/auth/login", json={
            "email": "mai-visto@example.com", "password": "qualsiasi",
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "err_bad_credentials"


class TestSessione:
    def test_token_valido_identifica_utente(self, client, registered_user):
        resp = client.get("/api/auth/me", headers=auth_headers(registered_user["token"]))
        assert resp.status_code == 200
        assert resp.json()["user"]["email"] == registered_user["email"]

    def test_token_inventato_non_autentica(self, client):
        resp = client.get("/api/auth/me", headers=auth_headers("token-inventato"))
        assert resp.json().get("user") is None

    def test_logout_invalida_il_token(self, client, registered_user):
        headers = auth_headers(registered_user["token"])
        assert client.post("/api/auth/logout", headers=headers).status_code == 200
        assert client.get("/api/auth/me", headers=headers).json().get("user") is None


class TestResetPassword:
    """Il reset esiste per riprendersi un account, non solo per cambiare una
    stringa: se un token rubato sopravvive al reset, chi ha subito il furto ha
    fatto la procedura per niente."""

    def test_reset_invalida_le_sessioni_aperte(self, client, registered_user, monkeypatch):
        import auth
        import mail

        # L'email transazionale esce dal processo (Worker). Qui interessa
        # l'effetto sul database, non la consegna.
        monkeypatch.setattr(mail, "send_reset_code", lambda *a, **k: None)
        monkeypatch.setattr(mail, "send_password_changed", lambda *a, **k: None)

        vecchio = auth_headers(registered_user["token"])
        assert client.get("/api/auth/me", headers=vecchio).json()["user"] is not None

        codice = auth.request_password_reset(registered_user["email"])
        assert codice, "l'utente registrato deve poter chiedere un reset"

        resp = client.post("/api/auth/reset-password", json={
            "email": registered_user["email"],
            "code": codice,
            "password": "Un-Altra-Passphrase!77",
            "password_confirm": "Un-Altra-Passphrase!77",
        })
        assert resp.status_code == 200

        assert client.get("/api/auth/me", headers=vecchio).json().get("user") is None,             "il token di prima del reset non deve piu' autenticare"
        nuovo = auth_headers(resp.json()["token"])
        assert client.get("/api/auth/me", headers=nuovo).json()["user"] is not None,             "la sessione appena emessa dal reset deve invece funzionare"

    def test_reset_avvisa_per_email_dopo_il_cambio(self, client, registered_user, monkeypatch):
        import auth
        import mail

        avvisi = []
        monkeypatch.setattr(mail, "send_reset_code", lambda *a, **k: None)
        monkeypatch.setattr(mail, "send_password_changed", lambda to, name: avvisi.append(to))

        codice = auth.request_password_reset(registered_user["email"])
        client.post("/api/auth/reset-password", json={
            "email": registered_user["email"],
            "code": codice,
            "password": "Un-Altra-Passphrase!77",
            "password_confirm": "Un-Altra-Passphrase!77",
        })
        assert avvisi == [registered_user["email"]]

    def test_reset_fallito_non_avvisa_nessuno(self, client, registered_user, monkeypatch):
        """Un avviso su un tentativo respinto sarebbe un modo per far arrivare
        posta a un indirizzo altrui indovinando un codice."""
        import mail

        avvisi = []
        monkeypatch.setattr(mail, "send_password_changed", lambda to, name: avvisi.append(to))

        resp = client.post("/api/auth/reset-password", json={
            "email": registered_user["email"],
            "code": "000000",
            "password": "Un-Altra-Passphrase!77",
            "password_confirm": "Un-Altra-Passphrase!77",
        })
        assert resp.status_code == 400
        assert avvisi == []


class TestArchiviazione:
    def test_password_non_in_chiaro_nel_database(self, client, registered_user, db_path):
        """Il controllo che conta davvero: aprire il file e cercare la
        password. Se comparisse, qualunque altro test sarebbe irrilevante."""
        with open(db_path, "rb") as fh:
            contenuto = fh.read()
        assert registered_user["password"].encode() not in contenuto

    def test_token_salvato_solo_come_impronta(self, client, registered_user, db_path):
        """Chi legge il database non deve poter riusare la sessione."""
        with open(db_path, "rb") as fh:
            contenuto = fh.read()
        assert registered_user["token"].encode() not in contenuto
