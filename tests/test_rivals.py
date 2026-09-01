"""
Confronto con account pubblici.

Quello che vale la pena bloccare qui non e' la lettura dall'API - quella e'
una chiamata, e la rete nei test e' sbarrata - ma le tre decisioni che il
codice prende da solo e che nessuno noterebbe se fossero sbagliate: come si
riconosce un canale da quello che l'utente incolla, dove finisce chi
nasconde gli iscritti, e chi puo' aggiungerne.
"""
import pytest

import rivals
from conftest import auth_headers


@pytest.fixture(autouse=True)
def elenco_vuoto():
    """Ogni test parte senza rivali. La tabella vive nello stesso database
    di prova di tutto il resto, che non viene ricreato fra un test e
    l'altro: senza questo, il terzo test eredita i canali del secondo e
    fallisce per un motivo che non ha niente a che vedere con quello che
    sta verificando."""
    def svuota():
        conn = rivals._conn()
        try:
            conn.execute("DELETE FROM rivals")
            conn.commit()
        finally:
            conn.close()

    svuota()
    yield
    svuota()


class TestRiconoscimentoCanale:
    """L'utente incolla quello che ha sottomano, non un handle pulito."""

    @pytest.mark.parametrize("scritto,atteso", [
        ("@mkbhd", "@mkbhd"),
        ("mkbhd", "@mkbhd"),
        ("  @mkbhd  ", "@mkbhd"),
        ("https://youtube.com/@mkbhd", "@mkbhd"),
        ("https://www.youtube.com/@mkbhd/videos", "@mkbhd"),
        ("UCBJycsmduvYEL83R_U4JriQ", "UCBJycsmduvYEL83R_U4JriQ"),
        ("https://www.youtube.com/channel/UCBJycsmduvYEL83R_U4JriQ", "UCBJycsmduvYEL83R_U4JriQ"),
    ])
    def test_forme_accettate(self, scritto, atteso):
        assert rivals.parse_handle(scritto) == atteso

    @pytest.mark.parametrize("scritto", ["", "   ", "a", "http://example.com/@tizio", "@"])
    def test_forme_rifiutate(self, scritto):
        """Rifiutare con un errore, mai indovinare: un handle sbagliato
        diventerebbe una lettura di un canale che non e' quello voluto."""
        with pytest.raises(rivals.RivalError):
            rivals.parse_handle(scritto)


class TestElenco:
    def test_aggiunge_normalizza_e_rimuove(self):
        rivals.add_rival("https://youtube.com/@tizio")
        elenco = rivals.list_rivals()
        assert [r["handle"] for r in elenco] == ["@tizio"]

        rivals.remove_rival(elenco[0]["id"])
        assert rivals.list_rivals() == []

    def test_lo_stesso_canale_non_si_aggiunge_due_volte(self):
        rivals.add_rival("@tizio")
        # Written another way too: it is the same channel, and seeing it
        # due volte nella classifica sarebbe una classifica sbagliata.
        with pytest.raises(rivals.RivalError):
            rivals.add_rival("https://youtube.com/@tizio")

    def test_oltre_il_massimo_si_rifiuta(self):
        for nome in ("@uno", "@due", "@tre"):
            rivals.add_rival(nome)
        with pytest.raises(rivals.RivalError):
            rivals.add_rival("@quattro")


def _seguito(conn_handle, iscritti, viste, video, titolo="Rivale"):
    """Scrive un rivale gia' letto, senza passare dall'API."""
    import json
    import time

    atteso = rivals.parse_handle(conn_handle)
    rivals.add_rival(conn_handle)
    # By handle, not by position: identifying the row just inserted with
    # [-1] has already written one channel's statistics over another's.
    riga = next(r for r in rivals.list_rivals() if r["handle"] == atteso)
    conn = rivals._conn()
    try:
        conn.execute(
            "UPDATE rivals SET title = ?, data = ?, fetched_at = ? WHERE id = ?",
            (titolo, json.dumps({
                "channel_id": "UC" + "x" * 22,
                "title": titolo,
                "subscribers": iscritti,
                "total_views": viste,
                "video_count": video,
            }), int(time.time()), riga["id"]),
        )
        conn.commit()
    finally:
        conn.close()


def _snapshot(iscritti, viste, video):
    return {"youtube": {"channels": [
        {"title": "Il mio", "subscribers": iscritti, "total_views": viste, "video_count": video}
    ]}}


class TestConfronto:
    def test_niente_da_dire_niente_da_mostrare(self):
        """Nessun rivale, o nessuna lettura riuscita: None, non una sezione
        vuota. Un riquadro vuoto sembra rotto."""
        assert rivals.compare(_snapshot(100, 1000, 10)) is None

        rivals.add_rival("@tizio")  # aggiunto ma mai letto
        assert rivals.compare(_snapshot(100, 1000, 10)) is None

    def test_posizione_fra_i_canali(self):
        _seguito("@grande", 5000, 500_000, 100)
        _seguito("@piccolo", 50, 5_000, 10)

        esito = rivals.compare(_snapshot(500, 50_000, 25))

        assert esito["rank"] == 2, "in mezzo ai due"
        assert esito["ranked_of"] == 3
        assert [r["subscribers"] for r in esito["rows"]] == [5000, 500, 50]

    def test_media_per_video_invece_del_totale(self):
        """Il totale premia solo chi pubblica da piu' tempo. La media per
        video e' il confronto che regge fra account di eta' diverse."""
        _seguito("@anziano", 5000, 500_000, 500)  # 1000 per video
        esito = rivals.compare(_snapshot(500, 50_000, 25))  # 2000 per video

        mio = next(r for r in esito["rows"] if r.get("mine"))
        altro = next(r for r in esito["rows"] if not r.get("mine"))
        assert mio["views_per_video"] == 2000.0
        assert altro["views_per_video"] == 1000.0

    def test_zero_video_non_divide_per_zero(self):
        _seguito("@nuovo", 10, 0, 0)
        esito = rivals.compare(_snapshot(500, 50_000, 25))
        altro = next(r for r in esito["rows"] if not r.get("mine"))
        assert altro["views_per_video"] == 0.0

    def test_chi_nasconde_gli_iscritti_non_finisce_ultimo(self):
        """YouTube permette di nascondere il numero di iscritti. Contarlo
        come zero metterebbe quel canale in fondo per una scelta di privacy,
        che non e' un risultato - e falserebbe la posizione di tutti gli
        altri."""
        _seguito("@riservato", None, 900_000, 300)
        _seguito("@piccolo", 50, 5_000, 10)

        esito = rivals.compare(_snapshot(500, 50_000, 25))

        assert esito["rank"] == 1, "primo fra i due che dichiarano gli iscritti"
        assert esito["ranked_of"] == 2, "il canale riservato non entra nella classifica"
        assert esito["hidden_subscribers"] is True, "ma va detto che c'e'"
        # Compare comunque nella tabella: ha altre colonne da confrontare.
        assert any(r["title"] == "@riservato" or r.get("handle") == "@riservato" for r in esito["rows"])


class TestPiano:
    def test_aggiungere_richiede_il_piano(self, client):
        risposta = client.post("/api/rivals", json={"handle": "@tizio"})
        assert risposta.status_code == 402

    def test_leggere_e_togliere_restano_liberi(self, client):
        """Se l'abbonamento scade, quello che hai inserito deve restare
        visibile e cancellabile: altrimenti sembra che i tuoi dati siano
        spariti."""
        rivals.add_rival("@tizio")
        elenco = client.get("/api/rivals")
        assert elenco.status_code == 200
        assert [r["handle"] for r in elenco.json()["rivals"]] == ["@tizio"]

        rivale_id = elenco.json()["rivals"][0]["id"]
        assert client.delete(f"/api/rivals/{rivale_id}").status_code == 200
        assert client.get("/api/rivals").json()["rivals"] == []
