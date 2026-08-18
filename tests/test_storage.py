"""
Cosa sopravvive e cosa no.

La distinzione fra "cache" (ricalcolabile con un Aggiorna) e
"configurazione" (account collegati, licenza, credenziali proprie) e' la
regola piu' facile da rompere durante un riordino, e la piu' costosa: se
"Svuota la cache" portasse via anche i collegamenti, l'utente dovrebbe
rifare tutti gli accessi OAuth senza capire perche'.

Qui viene fissata anche la regola dell'identificativo di installazione, che
deve restare stabile: se cambiasse ad ogni pulizia, il servizio licenze lo
vedrebbe come un computer nuovo e consumerebbe un'attivazione ogni volta.
"""
import cache
import connections
import licensing
import own_app


class TestCacheRicalcolabile:
    def test_snapshot_salvato_e_riletto(self, db_path):
        cache.save_snapshot("youtube", {"followers": 100})
        assert cache.latest_snapshot("youtube")["followers"] == 100

    def test_svuotare_cancella_gli_snapshot(self, db_path):
        cache.save_snapshot("youtube", {"followers": 100})
        cache.clear_all()
        assert cache.latest_snapshot("youtube") is None


class TestSalvataggiNelloStessoSecondo:
    """Regressione.

    fetched_at ha risoluzione al secondo. Due salvataggi ravvicinati - due
    click su Aggiorna, o un aggiornamento subito dopo un altro - finiscono
    con lo stesso valore, e a pari merito l'ordinamento non era deciso da
    noi ma da SQLite, che restituiva l'ordine di inserimento.

    Conseguenza vera: "l'ultimo snapshot" era il piu' vecchio dei due, e i
    numeri sembravano tornare indietro dopo un aggiornamento.
    """

    def test_ultimo_snapshot_e_davvero_l_ultimo(self, db_path):
        for n in (1, 2, 3):
            cache.save_snapshot("youtube", {"followers": n})
        assert cache.latest_snapshot("youtube")["followers"] == 3

    def test_storico_resta_in_ordine_cronologico(self, db_path):
        for n in (1, 2, 3):
            cache.save_snapshot("youtube", {"followers": n})
        assert [r["followers"] for r in cache.history("youtube")] == [1, 2, 3]

    def test_ultima_osservazione_e_davvero_l_ultima(self, db_path):
        for testo in ("prima", "seconda", "terza"):
            cache.save_insight(testo, based_on_fetch_at=0)
        assert cache.latest_insight()["text"] == "terza"


class TestConfigurazioneSopravvive:
    """Il cuore della regola: clear_all() non deve toccare nulla di cio' che
    l'utente ha dovuto configurare a mano."""

    def test_collegamenti_sopravvivono(self, db_path):
        connections.save_connection("youtube", "Canale", "id-1", {"refresh_token": "x"})
        cache.clear_all()
        assert len(connections.list_connections("youtube")) == 1

    def test_licenza_sopravvive(self, db_path):
        licensing._save("SD-PRO-AAAA-BBBB-CCCC-DDDD", "pro", "a@b.it", ok=True)
        cache.clear_all()
        assert licensing.stored()["plan"] == "pro"

    def test_app_proprie_sopravvivono(self, db_path):
        own_app._conn().execute(
            "INSERT INTO own_apps (platform, client_id, client_secret, created_at)"
            " VALUES ('tiktok', 'chiave', 'segreto', 0)"
        ).connection.commit()
        cache.clear_all()
        assert own_app.get("tiktok")["client_id"] == "chiave"

    def test_identificativo_installazione_stabile(self, db_path):
        """Se cambiasse ad ogni pulizia, ogni "Svuota la cache" brucerebbe
        un'attivazione della licenza."""
        prima = cache.device_id()
        cache.clear_all()
        assert cache.device_id() == prima
        assert len(prima) == 32


class TestCollegamenti:
    def test_scollegare_l_ultimo_account_svuota_i_numeri(self, db_path):
        """Senza questo, la dashboard continuerebbe a mostrare i numeri di
        un account che non e' piu' collegato, come se fossero ancora veri."""
        connections.save_connection("youtube", "Canale", "id-1", {"refresh_token": "x"})
        cache.save_snapshot("youtube", {"followers": 100})
        collegamento = connections.list_connections("youtube")[0]

        connections.delete_connection(collegamento["id"])

        assert connections.list_connections("youtube") == []
        assert cache.latest_snapshot("youtube") is None

    def test_i_token_non_escono_verso_il_frontend(self, db_path):
        """public_connections e' la versione che finisce nel browser: i
        token devono restare indietro."""
        sentinella = "valore-finto-che-non-deve-uscire"
        connections.save_connection("youtube", "Canale", "id-1",
                                    {"refresh" + "_token": sentinella})
        pubblici = connections.public_connections()
        assert pubblici and "data" not in pubblici[0]
        assert sentinella not in str(pubblici)

    def test_stesso_account_aggiornato_non_duplicato(self, db_path):
        connections.save_connection("youtube", "Nome vecchio", "id-1", {"refresh_token": "a"})
        connections.save_connection("youtube", "Nome nuovo", "id-1", {"refresh_token": "b"})
        elenco = connections.list_connections("youtube")
        assert len(elenco) == 1
        assert elenco[0]["account_name"] == "Nome nuovo"


class TestDatoCorrotto:
    """Una riga illeggibile non deve rompere la dashboard.

    Sono dati che scrive l'app stessa, quindi normalmente sono validi. Ma
    una scrittura interrotta (corrente che va via, errore del disco) ne
    lascerebbe una rovinata, e prima l'eccezione risaliva fino alla pagina
    principale: la dashboard restava rotta ad ogni apertura, senza che
    l'utente potesse capire perche'.
    """

    def _sporca(self, db_path, platform="youtube"):
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE snapshots SET data = '{rovinato' WHERE platform = ?",
                     (platform,))
        conn.commit(); conn.close()

    def test_ultimo_snapshot_rovinato_non_solleva(self, db_path):
        cache.save_snapshot("youtube", {"followers": 100})
        self._sporca(db_path)
        assert cache.latest_snapshot("youtube") is None

    def test_storico_salta_solo_la_riga_rovinata(self, db_path):
        cache.save_snapshot("youtube", {"followers": 1})
        cache.save_snapshot("youtube", {"followers": 2})
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE snapshots SET data = 'non-json' WHERE rowid = 1")
        conn.commit(); conn.close()

        storico = cache.history("youtube")
        assert [r["followers"] for r in storico] == [2], (
            "la riga buona deve sopravvivere a quella rovinata"
        )

    def test_cache_generica_rovinata_si_comporta_da_vuota(self, db_path):
        cache.kv_set("prova", {"x": 1})
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE kv_cache SET data = '{'")
        conn.commit(); conn.close()

        assert cache.kv_get("prova", max_age_seconds=10**9) is None
