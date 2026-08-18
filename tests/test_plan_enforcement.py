"""
I limiti dei piani devono valere sul server, non solo nell'interfaccia.

Un lucchetto disegnato nel frontend si toglie con dieci secondi di
strumenti per sviluppatori. Se il rifiuto non arriva dal server, il piano a
pagamento e' una richiesta cortese. Questi test chiamano le API direttamente,
saltando l'interfaccia, esattamente come farebbe chi vuole aggirarli.
"""
import plans


class TestTabellaDeiPiani:
    def test_free_non_include_le_funzioni_a_pagamento(self):
        assert plans.allows("free", "csv_export") is False
        assert plans.allows("free", "history") is False
        assert plans.allows("free", "best_hours") is False

    def test_pro_e_studio_le_includono(self):
        for piano in ("pro", "studio"):
            assert plans.allows(piano, "csv_export") is True
            assert plans.allows(piano, "history") is True

    def test_piano_sconosciuto_trattato_come_free(self):
        """Un valore corrotto o inventato non deve sbloccare nulla."""
        assert plans.allows("piano-inventato", "csv_export") is False
        assert plans.allows("", "csv_export") is False
        assert plans.allows(None, "csv_export") is False

    def test_limiti_account_crescenti(self):
        assert plans.max_accounts("free") == 1
        assert plans.max_accounts("pro") == 3
        assert plans.max_accounts("studio") == 10


class TestRifiutoDalServer:
    def test_export_csv_negato_senza_licenza(self, client):
        """Chiamata diretta all'API, senza passare dall'interfaccia."""
        resp = client.get("/api/export.csv")
        assert resp.status_code == 403, (
            "L'esportazione CSV e' una funzione a pagamento: il server deve "
            "rifiutarla, non limitarsi a nascondere il pulsante"
        )

    def test_export_csv_concesso_con_licenza_pro(self, client, db_path, monkeypatch):
        import licensing

        licensing._save("SD-PRO-AAAA-BBBB-CCCC-DDDD", "pro", "a@b.it", ok=True)
        resp = client.get("/api/export.csv")
        assert resp.status_code == 200

    def test_snapshot_senza_licenza_non_espone_lo_storico(self, client, db_path):
        """La storia e' una funzione Pro: nel piano gratuito il server non
        deve nemmeno spedirla, altrimenti basta guardare la risposta."""
        import cache

        cache.save_snapshot("youtube", {"followers": 10})
        cache.save_snapshot("youtube", {"followers": 20})

        dati = client.get("/api/snapshot").json()
        entitlements = dati.get("entitlements", {})
        assert entitlements.get("history") is False

        for piattaforma in dati.get("platforms", {}).values():
            if isinstance(piattaforma, dict):
                assert not piattaforma.get("history"), (
                    "lo storico non deve comparire nella risposta per un piano gratuito"
                )
