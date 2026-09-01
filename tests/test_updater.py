"""
Manifest, firma e installazione dell'aggiornamento.

Un updater e' il codice piu' pericoloso di un'app desktop: sostituisce
binari e puo' lasciare un'installazione inutilizzabile su un computer a cui
non abbiamo accesso. Qui i casi che contano non sono quelli in cui funziona,
ma quelli in cui NON deve funzionare: firma sbagliata, pacchetto alterato,
versione precedente riproposta.
"""
import base64
import sys
import time
import types
import hashlib
import json
import os
import zipfile

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from updater import install_kind, manifest as manifest_module, signature
from updater.manifest import ManifestError


@pytest.fixture()
def coppia_chiavi():
    privata = Ed25519PrivateKey.generate()
    pubblica_b64 = base64.b64encode(privata.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )).decode("ascii")
    return privata, pubblica_b64


def firma_manifest(manifest: dict, privata) -> dict:
    firma = privata.sign(signature.canonical_payload(manifest))
    return {**manifest, "signature": base64.b64encode(firma).decode("ascii")}


@pytest.fixture()
def manifest_valido(coppia_chiavi):
    privata, _ = coppia_chiavi
    return firma_manifest({
        "version": "1.5.0",
        "channel": "stable",
        "minimum_supported_version": "1.0.0",
        "mandatory": False,
        "published_at": "2026-08-18T10:00:00Z",
        "download_url": "https://github.com/x/y/releases/download/v1.5.0/pkg.zip",
        "sha256": "a" * 64,
        "size": 34_000_000,
        "release_notes_url": "https://example.com/notes",
        "database_schema_version": 2,
    }, privata)


class TestConfrontoVersioni:
    def test_confronto_numerico_non_alfabetico(self):
        """Il caso che rompe il confronto fra stringhe: senza numeri,
        "1.10.0" risulterebbe precedente a "1.9.0"."""
        assert manifest_module.is_newer("1.10.0", "1.9.0") is True
        assert manifest_module.is_newer("1.9.0", "1.10.0") is False

    def test_lunghezze_diverse(self):
        assert manifest_module.is_newer("1.4", "1.4.0") is False
        assert manifest_module.is_newer("1.4.1", "1.4") is True

    def test_versione_illeggibile_rifiutata(self):
        with pytest.raises(ManifestError):
            manifest_module.parse_version("ultima-versione")


class TestFirma:
    def test_manifest_firmato_accettato(self, manifest_valido, coppia_chiavi):
        _, pubblica = coppia_chiavi
        signature.verify(manifest_valido, pubblica)  # non solleva

    def test_manifest_senza_firma_rifiutato(self, manifest_valido, coppia_chiavi):
        _, pubblica = coppia_chiavi
        senza = {k: v for k, v in manifest_valido.items() if k != "signature"}
        with pytest.raises(signature.SignatureError):
            signature.verify(senza, pubblica)

    def test_contenuto_alterato_dopo_la_firma(self, manifest_valido, coppia_chiavi):
        """Il caso vero: qualcuno prende un manifest autentico e cambia
        l'indirizzo di download verso il proprio pacchetto."""
        _, pubblica = coppia_chiavi
        manomesso = {**manifest_valido, "download_url": "https://malevolo.example/pkg.zip"}
        with pytest.raises(signature.SignatureError):
            signature.verify(manomesso, pubblica)

    def test_firma_di_un_altra_chiave_rifiutata(self, manifest_valido):
        altra = Ed25519PrivateKey.generate()
        altra_pubblica = base64.b64encode(altra.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)).decode("ascii")
        with pytest.raises(signature.SignatureError):
            signature.verify(manifest_valido, altra_pubblica)

    def test_chiave_pubblica_segnaposto_non_valida(self, manifest_valido):
        """Finche' non si genera la coppia vera, nessun aggiornamento passa:
        e' il comportamento voluto, non una svista."""
        with pytest.raises(signature.SignatureError):
            signature.verify(manifest_valido, signature.PUBLIC_KEY_B64)


class TestConvalidaManifest:
    def test_manifest_buono(self, manifest_valido, coppia_chiavi):
        _, pubblica = coppia_chiavi
        assert manifest_module.validate(manifest_valido, "1.4.0", "stable", pubblica)

    def test_downgrade_rifiutato(self, manifest_valido, coppia_chiavi):
        """Un manifest vecchio ma autentico, riproposto da chi intercetta la
        rete, riporterebbe l'utente a una versione con problemi noti."""
        _, pubblica = coppia_chiavi
        with pytest.raises(ManifestError, match="not newer"):
            manifest_module.validate(manifest_valido, "1.6.0", "stable", pubblica)

    def test_stessa_versione_rifiutata(self, manifest_valido, coppia_chiavi):
        _, pubblica = coppia_chiavi
        with pytest.raises(ManifestError):
            manifest_module.validate(manifest_valido, "1.5.0", "stable", pubblica)

    def test_manifest_beta_non_arriva_a_chi_vuole_stable(self, manifest_valido, coppia_chiavi):
        privata, pubblica = coppia_chiavi
        beta = firma_manifest({**{k: v for k, v in manifest_valido.items()
                                  if k != "signature"}, "channel": "beta"}, privata)
        with pytest.raises(ManifestError, match="canale"):
            manifest_module.validate(beta, "1.4.0", "stable", pubblica)

    def test_versione_minima_troppo_alta(self, manifest_valido, coppia_chiavi):
        privata, pubblica = coppia_chiavi
        m = firma_manifest({**{k: v for k, v in manifest_valido.items()
                               if k != "signature"},
                            "minimum_supported_version": "1.4.9"}, privata)
        with pytest.raises(ManifestError, match="requires version"):
            manifest_module.validate(m, "1.4.0", "stable", pubblica)

    def test_impronta_malformata_rifiutata(self, manifest_valido, coppia_chiavi):
        privata, pubblica = coppia_chiavi
        m = firma_manifest({**{k: v for k, v in manifest_valido.items()
                               if k != "signature"}, "sha256": "troppo-corta"}, privata)
        with pytest.raises(ManifestError, match="64-character digest"):
            manifest_module.validate(m, "1.4.0", "stable", pubblica)

    def test_download_non_https_rifiutato(self, manifest_valido, coppia_chiavi):
        privata, pubblica = coppia_chiavi
        m = firma_manifest({**{k: v for k, v in manifest_valido.items()
                               if k != "signature"},
                            "download_url": "http://esempio.it/pkg.zip"}, privata)
        with pytest.raises(ManifestError, match="HTTPS"):
            manifest_module.validate(m, "1.4.0", "stable", pubblica)


class TestTipoInstallazione:
    def test_installazione_winget_non_si_autoaggiorna(self):
        """Due meccanismi che sostituiscono gli stessi file lascerebbero
        winget e l'app in disaccordo su cosa c'e' installato."""
        percorso = r"C:\Users\x\AppData\Local\Microsoft\WinGet\Packages\Tizio.App\app.exe"
        assert install_kind.detect(percorso) == install_kind.WINGET
        assert install_kind.can_self_update(install_kind.WINGET) is False
        assert install_kind.explain(install_kind.WINGET) == "update_managed_by_winget"

    def test_installazione_portable_si_aggiorna(self):
        percorso = r"C:\Users\x\Desktop\Social Dashboard\Social Dashboard.exe"
        assert install_kind.detect(percorso) == install_kind.PORTABLE
        assert install_kind.can_self_update(install_kind.PORTABLE) is True


class TestPacchetto:
    def _zip_di_prova(self, cartella, contenuto=b"eseguibile finto"):
        percorso = os.path.join(cartella, "pkg.zip")
        with zipfile.ZipFile(percorso, "w") as z:
            z.writestr("Social Dashboard.exe", contenuto)
        return percorso

    def test_impronta_diversa_fa_scartare_il_pacchetto(self, tmp_path, monkeypatch,
                                                       manifest_valido, coppia_chiavi):
        """Il pacchetto scaricato non e' quello dichiarato dal manifest
        firmato: si butta senza nemmeno aprirlo."""
        from updater import runner

        zip_path = self._zip_di_prova(str(tmp_path))
        dati = {**manifest_valido, "sha256": "b" * 64,
                "download_url": "https://esempio.it/pkg.zip"}

        def finto_download(url, destinazione, attesa):
            import shutil
            shutil.copy(zip_path, destinazione)

        monkeypatch.setattr(runner, "_download", finto_download)
        monkeypatch.setattr(install_kind, "detect", lambda *a: install_kind.PORTABLE)

        with pytest.raises(runner.UpdateError, match="non corrisponde"):
            runner.prepare(dati)

    def test_pacchetto_integro_viene_estratto(self, tmp_path, monkeypatch,
                                              manifest_valido):
        from updater import runner

        zip_path = self._zip_di_prova(str(tmp_path))
        impronta = hashlib.sha256(open(zip_path, "rb").read()).hexdigest()
        dati = {**manifest_valido, "sha256": impronta}

        def finto_download(url, destinazione, attesa):
            import shutil
            shutil.copy(zip_path, destinazione)

        monkeypatch.setattr(runner, "_download", finto_download)
        monkeypatch.setattr(install_kind, "detect", lambda *a: install_kind.PORTABLE)

        esito = runner.prepare(dati)
        assert os.path.exists(os.path.join(esito["staging_dir"], "Social Dashboard.exe"))

    def test_archivio_con_percorsi_fuori_cartella_rifiutato(self, tmp_path):
        """Un archivio costruito ad arte puo' contenere "..\\..\\qualcosa" e
        scrivere fuori dalla cartella di destinazione."""
        from updater import runner

        cattivo = os.path.join(str(tmp_path), "cattivo.zip")
        with zipfile.ZipFile(cattivo, "w") as z:
            z.writestr("../../fuori.txt", "non dovrei stare qui")

        destinazione = os.path.join(str(tmp_path), "dest")
        os.makedirs(destinazione)
        with pytest.raises(runner.UpdateError, match="sospetto"):
            runner._estrai(cattivo, destinazione)


class TestScambioCartelle:
    """Il momento in cui l'installazione dell'utente e' piu' fragile."""

    def _finta_installazione(self, radice, versione):
        cartella = os.path.join(radice, "app")
        os.makedirs(cartella, exist_ok=True)
        with open(os.path.join(cartella, "versione.txt"), "w") as fh:
            fh.write(versione)
        return cartella

    def test_scambio_mette_la_nuova_e_conserva_la_vecchia(self, tmp_path):
        from updater_bin import main as updater_main

        app = self._finta_installazione(str(tmp_path), "1.4.0")
        nuova = os.path.join(str(tmp_path), "nuova")
        os.makedirs(nuova)
        with open(os.path.join(nuova, "versione.txt"), "w") as fh:
            fh.write("1.5.0")

        vecchia = updater_main.scambia(app, nuova)

        assert open(os.path.join(app, "versione.txt")).read() == "1.5.0"
        assert open(os.path.join(vecchia, "versione.txt")).read() == "1.4.0", (
            "la versione precedente deve restare disponibile per il ripristino"
        )

    def test_ripristino_rimette_la_versione_precedente(self, tmp_path, monkeypatch):
        from updater_bin import main as updater_main

        app = self._finta_installazione(str(tmp_path), "1.4.0")
        nuova = os.path.join(str(tmp_path), "nuova")
        os.makedirs(nuova)
        with open(os.path.join(nuova, "versione.txt"), "w") as fh:
            fh.write("1.5.0-rotta")

        vecchia = updater_main.scambia(app, nuova)
        monkeypatch.setattr(updater_main, "avvia", lambda exe: None)

        updater_main.ripristina(app, vecchia, "Social Dashboard.exe")

        assert open(os.path.join(app, "versione.txt")).read() == "1.4.0", (
            "dopo un aggiornamento fallito l'utente deve ritrovare l'app che "
            "aveva prima, funzionante"
        )

    def test_se_l_app_non_si_chiude_non_si_tocca_niente(self, tmp_path, monkeypatch):
        """Sostituire i file mentre l'app e' ancora viva significa file
        bloccati e installazione a meta'."""
        from updater_bin import main as updater_main

        app = self._finta_installazione(str(tmp_path), "1.4.0")
        nuova = os.path.join(str(tmp_path), "nuova")
        os.makedirs(nuova)

        monkeypatch.setattr(updater_main, "attendi_uscita", lambda pid, timeout=30: False)

        codice = updater_main.esegui(app, nuova, "app.exe", 12345, "1.5.0")

        assert codice == 2
        assert open(os.path.join(app, "versione.txt")).read() == "1.4.0"
        assert os.path.exists(nuova), "il pacchetto scaricato non va perso"


class TestVulnerabilitaCorrette:
    """Difetti trovati attaccando il codice appena scritto, non leggendolo."""

    def test_archivio_che_esplode_una_volta_scompattato(self, tmp_path):
        """Poche centinaia di kilobyte che diventano gigabyte: il pacchetto
        e' gia' confrontato con l'impronta del manifest firmato, quindi non
        e' iniettabile da un estraneo, ma un limite copre anche il caso di
        un pacchetto sbagliato costruito da noi."""
        from updater import runner

        bomba = os.path.join(str(tmp_path), "bomba.zip")
        with zipfile.ZipFile(bomba, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("grosso.bin", b"\0" * (runner.MAX_EXTRACTED_BYTES + 1024))

        destinazione = os.path.join(str(tmp_path), "dest")
        os.makedirs(destinazione)
        with pytest.raises(runner.UpdateError, match="scompattato"):
            runner._estrai(bomba, destinazione)

    def test_secondo_aggiornamento_in_parallelo_respinto(self, monkeypatch):
        """Due processi che si contendono la stessa cartella troverebbero
        ciascuno lo stato dell'altro."""
        from updater import runner

        runner._install_lock.acquire()
        try:
            with pytest.raises(runner.UpdateError, match="already in progress"):
                runner.apply({"version": "1.5.0", "staging_dir": "x", "work_dir": "y"})
        finally:
            runner._install_lock.release()

    def test_l_avviso_sparisce_quando_la_versione_e_gia_installata(self, monkeypatch, tmp_path):
        """L'esito dell'ultimo controllo vale un giorno, ma la versione
        installata puo' cambiare prima: un aggiornamento manuale, winget, una
        reinstallazione. Da quel momento la memoria annunciava una versione
        gia' presente, l'avviso non se ne andava e premere "Installa"
        falliva - il manifest rifiuta cio' che non e' piu' recente."""
        from updater import runner

        # A stand-in database: _state reads what kv_set wrote, as it does in
        # production. With a fixed dict, _save_state's merge would put back
        # the very key that was just removed.
        salvato = {
            "last_check": int(time.time()),
            "last_result": {"available": True, "version": "1.7.2"},
            "skipped": "1.7.2",
        }
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(install_kind, "detect", lambda *a: install_kind.PORTABLE)
        monkeypatch.setattr(install_kind, "app_directory", lambda: str(tmp_path))
        (tmp_path / "updater.exe").write_bytes(b"finto")
        monkeypatch.setattr(runner, "_state", lambda: dict(salvato))
        import version
        monkeypatch.setattr(version, "APP_VERSION", "1.7.3", raising=False)
        import cache
        def scrivi(chiave, dati):
            salvato.clear()
            salvato.update(dati)

        monkeypatch.setattr(cache, "kv_set", scrivi)
        monkeypatch.setattr(runner.manifest_module, "fetch",
                            lambda canale: (_ for _ in ()).throw(
                                runner.manifest_module.ManifestError("niente di nuovo")))

        esito = runner.check()

        assert esito["available"] is False, "annunciava una versione gia' installata"
        assert "last_result" not in salvato, "la memoria scaduta e' rimasta"
        assert "skipped" not in salvato, "il 'salta' di una versione superata e' rimasto"

    def test_una_versione_futura_saltata_resta_saltata(self, monkeypatch, tmp_path):
        """La pulizia non deve mangiarsi le scelte ancora valide."""
        from updater import runner

        stato = {"skipped": "2.0.0", "last_check": 0}
        import version
        monkeypatch.setattr(version, "APP_VERSION", "1.7.3", raising=False)
        ripulito = runner._dimentica_il_passato(stato, "1.7.3")
        assert ripulito["skipped"] == "2.0.0"

    def test_l_app_si_chiude_dopo_aver_ceduto_il_passo_all_updater(self, monkeypatch):
        """Il difetto che rendeva inutile tutto il resto.

        L'updater aspetta che l'applicazione termini: e' l'unico momento in
        cui Windows smette di tenere bloccato l'eseguibile. Nessuno pero' la
        chiudeva, quindi ogni aggiornamento finiva a "the application did
        not close" trenta secondi dopo, in silenzio.
        """
        from updater import runner

        chiuse = []
        uscite = []

        class FintaFinestra:
            def destroy(self):
                chiuse.append(True)

        finto_webview = types.ModuleType("webview")
        finto_webview.windows = [FintaFinestra()]
        monkeypatch.setitem(sys.modules, "webview", finto_webview)
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(runner.time, "sleep", lambda _s: None)
        monkeypatch.setattr(runner.os, "_exit", lambda code: uscite.append(code))

        runner._chiudi_dopo_la_risposta()
        for _ in range(200):
            if chiuse and uscite:
                break
            time.sleep(0.01)

        assert chiuse, "la finestra dell'app non e' stata chiusa"
        assert uscite == [0], "il processo non e' uscito: l'updater aspetterebbe invano"

    def test_dai_sorgenti_non_si_chiude_niente(self, monkeypatch):
        """Un os._exit dentro i test ucciderebbe pytest, e dai sorgenti
        l'aggiornamento non parte comunque."""
        from updater import runner

        uscite = []
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        monkeypatch.setattr(runner.os, "_exit", lambda code: uscite.append(code))

        runner._chiudi_dopo_la_risposta(ritardo=0)
        time.sleep(0.1)
        assert uscite == []

    def test_senza_updater_exe_si_propone_il_download_manuale(self, monkeypatch, tmp_path):
        """Le build fino alla 1.5.x non avevano updater.exe accanto all'app.

        Chiederlo solo alla fine significava scaricare quaranta megabyte per
        poi fermarsi su un errore generico. Meglio dire subito che questa
        copia si aggiorna a mano, che e' il percorso gia' previsto per le
        installazioni gestite da qualcun altro.
        """
        from updater import runner

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(install_kind, "detect", lambda *a: install_kind.PORTABLE)
        monkeypatch.setattr(install_kind, "app_directory", lambda: str(tmp_path))

        esito = runner.check(force=True)
        assert esito["available"] is False
        assert esito["managed_externally"] is True
        assert esito["reason"] == "update_needs_manual_download"

    def test_un_tentativo_fallito_non_lascia_il_pacchetto_sul_disco(self, monkeypatch, tmp_path):
        """Il pacchetto scompattato pesa quanto l'applicazione: ogni
        tentativo fallito ne lasciava una copia accanto alla cartella
        dell'app, dove nessuno sarebbe andato a cercarla."""
        from updater import runner

        staging = tmp_path / "Social Dashboard.new"
        lavoro = tmp_path / "work"
        staging.mkdir(); lavoro.mkdir()
        (staging / "grosso.bin").write_bytes(b"x" * 1024)

        def _apply_che_fallisce(_preparato):
            raise runner.UpdateError("updater.exe non trovato")

        monkeypatch.setattr(runner, "_apply", _apply_che_fallisce)

        with pytest.raises(runner.UpdateError):
            runner.apply({"version": "1.7.0", "staging_dir": str(staging),
                          "work_dir": str(lavoro)})

        assert not staging.exists(), "la nuova versione scompattata e' rimasta sul disco"
        assert not lavoro.exists()

    def test_l_updater_esce_dal_job_object_che_ucciderebbe_l_app(self, monkeypatch):
        """Un updater che muore insieme a chi lo ha lanciato non serve a
        niente: l'app si e' gia' chiusa per lasciargli sostituire i file."""
        from updater import runner

        tentativi = []

        def finto_popen(comando, **kwargs):
            tentativi.append(kwargs.get("creationflags", 0))
            return object()

        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setattr(runner.subprocess, "Popen", finto_popen)
        runner._avvia_updater(["updater.exe"], cwd="C:\Temp")

        assert tentativi, "l'updater non e' stato avviato"
        assert tentativi[0] & runner.subprocess.CREATE_BREAKAWAY_FROM_JOB

    def test_se_il_job_vieta_l_uscita_l_updater_parte_lo_stesso(self, monkeypatch):
        """Non tutti i job consentono di uscirne: meglio un updater dentro il
        job che nessun updater."""
        from updater import runner

        tentativi = []

        def finto_popen(comando, **kwargs):
            flag = kwargs.get("creationflags", 0)
            tentativi.append(flag)
            if flag & runner.subprocess.CREATE_BREAKAWAY_FROM_JOB:
                raise OSError("accesso negato")
            return object()

        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setattr(runner.subprocess, "Popen", finto_popen)
        runner._avvia_updater(["updater.exe"], cwd="C:\Temp")

        assert len(tentativi) == 2, "non ha riprovato senza breakaway"
        assert not (tentativi[1] & runner.subprocess.CREATE_BREAKAWAY_FROM_JOB)
        assert tentativi[1] & runner.subprocess.DETACHED_PROCESS

    def test_l_updater_non_parte_dentro_la_cartella_da_sostituire(self, monkeypatch, tmp_path):
        """Su Windows la directory corrente di un processo la tiene aperta.

        L'updater ereditava quella dell'applicazione, cioe' esattamente la
        cartella che deve rinominare: il rinomino falliva con "il file e'
        utilizzato da un altro processo" - da se' stesso. L'app si era gia'
        chiusa, quindi il risultato era un aggiornamento annullato e una
        finestra sparita.
        """
        from updater import runner

        cartella_app = tmp_path / "Social Dashboard"
        cartella_app.mkdir()
        (cartella_app / "updater.exe").write_bytes(b"finto")
        lavoro = tmp_path / "work"
        lavoro.mkdir()
        chiamate = {}

        class FintoPopen:
            def __init__(self, comando, **kwargs):
                chiamate["cwd"] = kwargs.get("cwd")

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(install_kind, "app_directory", lambda: str(cartella_app))
        monkeypatch.setattr(runner.subprocess, "Popen", FintoPopen)
        monkeypatch.setattr(runner, "_chiudi_dopo_la_risposta", lambda *a, **k: None)
        import db
        monkeypatch.setattr(db.backup, "create", lambda *a, **k: None)

        runner._apply({"version": "1.7.3", "staging_dir": str(tmp_path / "new"),
                       "work_dir": str(lavoro)})

        avviato_in = os.path.abspath(chiamate["cwd"])
        assert not avviato_in.startswith(os.path.abspath(str(cartella_app))), (
            "l'updater parte dentro la cartella che deve rinominare")

    def test_scambio_fallito_riapre_l_applicazione(self, tmp_path, monkeypatch):
        """L'app si e' chiusa per farci lavorare: se poi non si tocca niente,
        lasciarla chiusa in silenzio e' il modo peggiore di fallire."""
        from updater_bin import main as updater_main

        app = tmp_path / "app"
        app.mkdir()
        riavvii = []
        monkeypatch.setattr(updater_main, "attendi_uscita", lambda pid, timeout=30: True)
        monkeypatch.setattr(updater_main, "scambia",
                            lambda a, n: (_ for _ in ()).throw(OSError("file in uso")))
        monkeypatch.setattr(updater_main, "avvia", lambda exe: riavvii.append(exe))

        esito = updater_main.esegui(str(app), str(tmp_path / "new"),
                                    "Social Dashboard.exe", 0, "1.7.3")

        assert esito == 3
        assert riavvii == [os.path.join(str(app), "Social Dashboard.exe")]

    def test_build_compilata_senza_updater_si_ferma(self, monkeypatch, tmp_path):
        """In una build compilata sys.executable e' l'applicazione, non
        Python: il vecchio ripiego avrebbe rilanciato l'app stessa con gli
        argomenti dell'updater."""
        from updater import runner

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(install_kind, "app_directory", lambda: str(tmp_path))

        with pytest.raises(runner.UpdateError, match="package is incomplete"):
            runner._copia_updater(str(tmp_path))

    def test_scambio_fra_volumi_diversi(self, tmp_path, monkeypatch):
        """os.rename fra volumi diversi non e' possibile su Windows: senza
        ripiego, chi tiene l'app su un disco diverso da quello di sistema
        non riuscirebbe MAI ad aggiornare."""
        from updater_bin import main as updater_main

        app = os.path.join(str(tmp_path), "app")
        nuova = os.path.join(str(tmp_path), "nuova")
        os.makedirs(app); os.makedirs(nuova)
        open(os.path.join(app, "v.txt"), "w").write("1.4.0")
        open(os.path.join(nuova, "v.txt"), "w").write("1.5.0")

        rename_vero = os.rename

        def rename_che_rifiuta_fra_volumi(src, dst):
            if os.path.basename(src) == "nuova":
                errore = OSError(18, "Cross-device link")
                errore.winerror = 17
                raise errore
            return rename_vero(src, dst)

        monkeypatch.setattr(os, "rename", rename_che_rifiuta_fra_volumi)
        vecchia = updater_main.scambia(app, nuova)

        assert open(os.path.join(app, "v.txt")).read() == "1.5.0", (
            "con volumi diversi si deve copiare invece di rinominare"
        )
        assert open(os.path.join(vecchia, "v.txt")).read() == "1.4.0"

    def test_manifest_spropositato_rifiutato(self, monkeypatch):
        """Un manifest e' un oggetto piccolo. Il limite di dimensione e' cio'
        che rende irraggiungibile l'annidamento estremo: RecursionError
        arriverebbe intorno ai 100.000 livelli, ma in 64 KB non ce ne
        stanno nemmeno la meta'."""
        from updater import manifest as M

        enorme = (b'{"a":' + b"1" * (M.MAX_MANIFEST_BYTES + 1024) + b"}")

        class FintaRisposta:
            def read(self, n=None):
                return enorme[:n] if n else enorme
            def __enter__(self): return self
            def __exit__(self, *a): return False

        monkeypatch.setattr(M.urllib.request, "urlopen", lambda *a, **k: FintaRisposta())
        with pytest.raises(M.ManifestError, match="troppo grande"):
            M.fetch(url="https://esempio.it/latest.json")
