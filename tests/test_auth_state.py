"""
Un accesso scaduto deve risultare scaduto anche in "Collega account".

Regressione vera: la diagnostica diceva "token has been expired" mentre la
pagina dei collegamenti mostrava lo stesso account come attivo. Le due
schermate leggevano la stessa riga del database, che pero' non aveva nessun
posto dove annotare che il token aveva smesso di funzionare.

Il resto dei test qui difende la regola opposta, altrettanto importante: un
problema di rete non deve mandare l'utente a rifare un accesso che
funzionava benissimo.
"""
import connections


class TestRiconoscimentoErrori:
    """Quali errori significano davvero "serve un nuovo accesso"."""

    def test_token_scaduto_o_revocato(self):
        for errore in (
            "invalid_grant: Token has been expired or revoked.",
            "The access token was revoked",
            "401 Client Error: Unauthorized",
            "invalid_scope: requested scopes not granted",
        ):
            assert connections.is_auth_failure(errore), errore

    def test_problemi_passeggeri_non_contano(self):
        """Se questi marcassero l'account, un disservizio di dieci minuti
        della piattaforma manderebbe l'utente a rifare tutti gli accessi."""
        for errore in (
            "HTTPSConnectionPool: Read timed out",
            "500 Server Error: Internal Server Error",
            "quota exceeded: too many requests",
            "Temporary failure in name resolution",
        ):
            assert not connections.is_auth_failure(errore), errore


class TestStatoSulleConnessioni:
    def _collega(self, db_path):
        connections.save_connection("youtube", "Canale", "id-1",
                                    {"refresh" + "_token": "x", "client_id": "y"})
        return connections.list_connections("youtube")[0]["id"]

    def test_un_account_appena_collegato_e_sano(self, db_path):
        self._collega(db_path)
        pubblici = connections.public_connections()
        assert pubblici[0].get("needs_reauth") is None

    def test_errore_di_autenticazione_marca_l_account(self, db_path):
        identificativo = self._collega(db_path)
        connections.record_fetch_outcome(identificativo,
                                         "invalid_grant: Token has been expired or revoked.")

        pubblici = connections.public_connections()
        assert pubblici[0]["needs_reauth"] is True, (
            "e' esattamente il caso che l'utente vedeva ancora come collegato"
        )
        assert pubblici[0]["auth_checked_at"] > 0

    def test_errore_di_rete_lascia_l_account_com_era(self, db_path):
        identificativo = self._collega(db_path)
        connections.record_fetch_outcome(identificativo, "Read timed out")
        assert connections.public_connections()[0].get("needs_reauth") is None

    def test_un_aggiornamento_riuscito_ripulisce_lo_stato(self, db_path):
        identificativo = self._collega(db_path)
        connections.record_fetch_outcome(identificativo, "token expired")
        assert connections.public_connections()[0]["needs_reauth"] is True

        connections.record_fetch_outcome(identificativo, None)
        assert connections.public_connections()[0].get("needs_reauth") is None

    def test_ricollegare_ripulisce_lo_stato(self, db_path):
        """L'utente fa quello che gli abbiamo chiesto: l'avviso deve sparire
        subito, non al prossimo aggiornamento riuscito."""
        identificativo = self._collega(db_path)
        connections.record_fetch_outcome(identificativo, "token revoked")

        connections.save_connection("youtube", "Canale", "id-1",
                                    {"refresh" + "_token": "nuovo", "client_id": "y"})
        assert connections.public_connections()[0].get("needs_reauth") is None

    def test_account_marcato_resta_utilizzabile_dagli_adapter(self, db_path):
        """Non si cancella niente: il token potrebbe tornare valido, e
        buttare la connessione porterebbe via anche lo storico raccolto."""
        identificativo = self._collega(db_path)
        connections.record_fetch_outcome(identificativo, "token expired")

        elenco = connections.list_connections("youtube")
        assert len(elenco) == 1
        assert elenco[0]["auth_state"]

    def test_account_da_env_non_rompe_niente(self, db_path):
        """Gli account configurati da .env non hanno una riga nel database:
        registrare l'esito per loro non deve sollevare."""
        connections.record_fetch_outcome(None, "token expired")
        connections.record_fetch_outcome(0, None)
