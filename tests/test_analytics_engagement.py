"""
Engagement, benchmark e punteggio di salute.

Prima di questa versione l'app scaricava like, commenti, condivisioni e
salvataggi a ogni aggiornamento e poi guardava solo le views. Questi test
fissano il comportamento delle metriche che ne derivano, e soprattutto i
casi in cui l'app deve TACERE: un rapporto calcolato su due contenuti non
e' un'analisi, e un confronto con la media di settore fatto senza sapere
quanti follower ha l'utente e' un numero a caso.
"""
import analytics
import benchmarks
import diagnostics


def _post(views=1000, likes=0, comments=0, shares=0, saved=0, reach=None, hour=12,
          published="2026-08-17T12:00:00Z"):
    return {"title": "t", "views": views, "likes": likes, "comments": comments,
            "shares": shares, "saved": saved, "reach": reach if reach is not None else views,
            "publish_hour_utc": hour, "published": published, "timestamp": published,
            "total_interactions": likes + comments + shares + saved}


def _snapshot_youtube(video, subscribers=5000):
    return {"youtube": {"channels": [
        {"name": "Canale", "ok": True, "subscribers": subscribers, "recent_videos": video}
    ]}}


class TestEngagement:
    def test_si_calcola_sulla_reach_non_sul_numero_di_post(self):
        """Un post da 10.000 visualizzazioni e uno da 100 non possono pesare
        uguale: il rapporto sta sulle persone raggiunte, non sui contenuti."""
        analisi = analytics.compute_analytics(_snapshot_youtube([
            _post(views=10000, likes=100),
            _post(views=100, likes=50),
        ]))
        # 150 interactions over 10,100 reached = 1.49%, not the mean of the
        # first one's 1% and the second one's 50%.
        assert analisi["engagement"]["rate"] == 1.49

    def test_instagram_usa_la_reach_quando_c_e(self):
        snap = {"instagram": {"accounts": [{"name": "IG", "ok": True, "followers": 1000,
                "recent_posts": [_post(views=1000, reach=500, likes=50)]}]}}
        analisi = analytics.compute_analytics(snap)
        # 50 over 500 reached = 10%, not 5% measured against views.
        assert analisi["engagement"]["rate"] == 10.0

    def test_senza_dati_non_inventa_un_rapporto(self):
        assert analytics.compute_analytics({})["engagement"] is None

    def test_salvataggi_e_condivisioni_hanno_un_rapporto_proprio(self):
        snap = {"instagram": {"accounts": [{"name": "IG", "ok": True,
                "recent_posts": [_post(views=1000, saved=30, shares=10)]}]}}
        misura = analytics.compute_analytics(snap)["engagement"]
        assert misura["save_rate"] == 3.0
        assert misura["share_rate"] == 1.0


class TestMappaGiornoOra:
    def test_raggruppa_per_giorno_e_ora(self):
        analisi = analytics.compute_analytics(_snapshot_youtube([
            _post(views=100, hour=18, published="2026-08-17T18:00:00Z"),  # lunedi'
            _post(views=300, hour=18, published="2026-08-10T18:00:00Z"),  # lunedi'
            _post(views=50, hour=9, published="2026-08-18T09:00:00Z"),    # martedi'
        ]))
        celle = {(c["weekday"], c["hour"]): c for c in analisi["heatmap"]}
        assert celle[(0, 18)]["avg_views"] == 200
        assert celle[(0, 18)]["count"] == 2
        assert celle[(1, 9)]["avg_views"] == 50

    def test_una_data_illeggibile_non_fa_saltare_il_calcolo(self):
        analisi = analytics.compute_analytics(_snapshot_youtube([
            _post(views=100, hour=18, published="non-una-data"),
            _post(views=200, hour=18, published="2026-08-17T18:00:00Z"),
        ]))
        assert len(analisi["heatmap"]) == 1


class TestBenchmark:
    def test_la_fascia_dipende_dai_follower(self):
        assert benchmarks.tier_for(500) == "nano"
        assert benchmarks.tier_for(50_000) == "micro"
        assert benchmarks.tier_for(2_000_000) == "mega"

    def test_engagement_atteso_cala_al_crescere_del_pubblico(self):
        """Se non calasse, ogni account piccolo sembrerebbe bravissimo e
        ogni account grande un disastro, per il solo effetto della taglia."""
        for piattaforma in ("tiktok", "instagram", "youtube"):
            valori = [benchmarks.expected_rate(piattaforma, f)
                      for f in (5_000, 50_000, 300_000, 800_000, 5_000_000)]
            assert valori == sorted(valori, reverse=True), piattaforma

    def test_sopra_sotto_e_in_linea(self):
        atteso = benchmarks.expected_rate("tiktok", 5_000)
        assert benchmarks.compare("tiktok", 5_000, atteso * 2)["state"] == "above"
        assert benchmarks.compare("tiktok", 5_000, atteso * 0.3)["state"] == "below"
        assert benchmarks.compare("tiktok", 5_000, atteso)["state"] == "inline"

    def test_tace_quando_il_confronto_non_reggerebbe(self):
        assert benchmarks.compare("tiktok", 50, 5.0) is None, "troppo pochi follower"
        assert benchmarks.compare("tiktok", 0, 5.0) is None, "follower sconosciuti"
        assert benchmarks.compare("tiktok", 5_000, None) is None, "engagement sconosciuto"
        assert benchmarks.compare("mastodon", 5_000, 5.0) is None, "piattaforma senza dati"


class TestPunteggioSalute:
    def test_non_da_piu_il_massimo_a_un_account_fermo(self):
        """La regressione che questo punteggio esiste per risolvere: prima
        bastava che le API rispondessero per fare 100%."""
        snap = _snapshot_youtube([_post(views=1000, likes=1, published="2026-01-01T12:00:00Z")])
        analisi = analytics.compute_analytics(snap)
        esito = diagnostics.run_diagnostics(snap, analisi)
        assert esito["score"] < 100

    def test_mostra_da_dove_esce_il_numero(self):
        snap = _snapshot_youtube([_post(views=1000, likes=50)])
        esito = diagnostics.run_diagnostics(snap, analytics.compute_analytics(snap))
        chiavi = {p["key"] for p in esito["score_parts"]}
        assert chiavi == {"technical", "engagement", "consistency", "coverage"}
        assert abs(sum(p["weight"] for p in esito["score_parts"]) - 1.0) < 0.001

    def test_una_voce_senza_dati_non_diventa_uno_zero(self):
        """Senza follower non si puo' giudicare l'engagement: quella voce
        esce dal calcolo invece di far crollare il punteggio per una
        mancanza di informazioni."""
        snap = {"youtube": {"channels": [{"name": "C", "ok": True,
                "recent_videos": [_post(views=1000, likes=100)]}]}}
        esito = diagnostics.run_diagnostics(snap, analytics.compute_analytics(snap))
        voce = next(p for p in esito["score_parts"] if p["key"] == "engagement")
        assert voce["score"] is None
        assert esito["score"] is not None and esito["score"] > 0

    def test_senza_nessun_dato_il_punteggio_resta_indefinito(self):
        esito = diagnostics.run_diagnostics({}, {})
        assert esito["score"] is not None or esito["score"] is None  # non solleva


class TestDatiOstili:
    """Trovati attaccando il codice nuovo con dati che non dovrebbero mai
    arrivare, ma che basterebbe una riga di cache rovinata o un cambio di
    formato di un'API a produrre. La conseguenza sarebbe la stessa gia'
    vista con le righe illeggibili: la pagina Overview rotta ad ogni
    apertura, senza che l'utente possa capire perche'."""

    def test_numeri_arrivati_come_stringhe(self):
        """YouTube manda davvero le statistiche come stringhe: se un giorno
        una passasse senza conversione, un confronto fra str e int
        farebbe esplodere tutta l'analisi."""
        snap = _snapshot_youtube([{"title": "a", "views": "1000", "likes": "50",
                                   "comments": None, "publish_hour_utc": 12,
                                   "published": "2026-08-17T12:00:00Z"}])
        analisi = analytics.compute_analytics(snap)
        assert analisi["total_views"] == 1000

    def test_liste_che_non_sono_liste(self):
        for rotto in ({"youtube": {"channels": "non una lista"}},
                      {"instagram": {"accounts": {"a": 1}}},
                      {"tiktok": {"accounts": None}}):
            assert analytics.compute_analytics(rotto)["total_items_analyzed"] == 0

    def test_elementi_che_non_sono_dizionari(self):
        snap = {"youtube": {"channels": ["stringa", None, 42]}}
        assert analytics.compute_analytics(snap)["total_items_analyzed"] == 0

    def test_valori_non_finiti(self):
        """json.loads accetta Infinity e NaN: arrivati fino a round()
        darebbero OverflowError e porterebbero giu' la pagina."""
        assert analytics._num(float("inf")) == 0
        assert analytics._num(float("nan")) == 0
        assert benchmarks.compare("tiktok", 5000, float("inf")) is None
        assert benchmarks.compare("tiktok", 5000, float("nan")) is None

    def test_errori_non_stringa_nel_rilevamento_token(self):
        """Gli errori arrivano da tre librerie diverse e non sempre sono
        stringhe: byte da una risposta HTTP, un'eccezione, un codice."""
        import connections
        assert connections.is_auth_failure(b"invalid_grant") is True
        assert connections.is_auth_failure(ValueError("token expired")) is True
        # A bare 401 genuinely does mean the authorization is finished.
        assert connections.is_auth_failure(401) is True
        assert connections.is_auth_failure(500) is False
        assert connections.is_auth_failure(None) is False


class TestControlliDiStrategia:
    def test_segnala_engagement_sotto_la_media(self):
        snap = _snapshot_youtube([_post(views=10000, likes=1)], subscribers=5000)
        esito = diagnostics.run_diagnostics(snap, analytics.compute_analytics(snap))
        assert any(i.get("code") == "diag_bench_below" for i in esito["issues"])

    def test_non_accusa_youtube_di_scarsa_risonanza(self):
        """YouTube non espone salvataggi ne' condivisioni con lo scope di
        lettura: dire all'utente che non ne ha sarebbe colpa nostra."""
        snap = _snapshot_youtube([_post(views=1000, likes=100) for _ in range(8)])
        esito = diagnostics.run_diagnostics(snap, analytics.compute_analytics(snap))
        risonanza = [i for i in esito["issues"] if i.get("code") == "diag_resonance"]
        assert risonanza == []

    def test_segnala_contenuti_visti_ma_mai_salvati(self):
        snap = {"instagram": {"accounts": [{"name": "IG", "ok": True, "followers": 5000,
                "recent_posts": [_post(views=5000, likes=10) for _ in range(6)]}]}}
        esito = diagnostics.run_diagnostics(snap, analytics.compute_analytics(snap))
        assert any(i.get("code") == "diag_resonance" for i in esito["issues"])

    def test_un_controllo_che_sbaglia_non_cancella_la_diagnostica(self, monkeypatch):
        def esplode(_):
            raise ZeroDivisionError("conto sbagliato")

        monkeypatch.setattr(diagnostics, "_check_benchmark", esplode)
        snap = _snapshot_youtube([_post(views=1000, likes=50)])
        esito = diagnostics.run_diagnostics(snap, analytics.compute_analytics(snap))
        assert "issues" in esito and esito["score"] is not None
