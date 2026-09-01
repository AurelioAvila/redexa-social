"""
Il lato applicazione dell'aggiornamento: decide, scarica, verifica, e passa
la mano al processo separato.

L'ordine dei controlli non e' casuale. Si verifica prima la firma del
manifest, poi si scarica, poi si controlla l'impronta del pacchetto, e solo
alla fine si tocca qualcosa. Ogni passo che fallisce lascia il computer
esattamente come era.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

from . import install_kind, manifest as manifest_module

DOWNLOAD_TIMEOUT = 60
# Un pacchetto molto piu' grande del previsto e' un problema, non un
# aggiornamento: si smette di scaricare invece di riempire il disco.
MAX_PACKAGE_BYTES = 300 * 1024 * 1024
# Limite su quanto puo' occupare una volta scompattato: un archivio piccolo
# puo' espandersi enormemente.
MAX_EXTRACTED_BYTES = 1024 * 1024 * 1024

# Un solo aggiornamento per volta. Senza, due richieste ravvicinate
# lancerebbero due processi che si contendono la stessa cartella, ciascuno
# convinto di essere l'unico: lo scambio del secondo troverebbe uno stato
# che non si aspetta.
_install_lock = __import__("threading").Lock()

CHECK_INTERVAL_SECONDS = 24 * 3600
_STATE_KEY = "updater_state"


class UpdateError(Exception):
    pass


def _dimentica_il_passato(stato: dict, installata: str) -> dict:
    """Butta cio' che lo stato dice di versioni che non sono piu' future.

    L'esito dell'ultimo controllo resta valido un giorno, ma la versione
    installata puo' cambiare prima: basta un aggiornamento fatto a mano,
    da winget, o una reinstallazione. Da quel momento la memoria annuncia
    una versione che l'utente ha gia', l'avviso non se ne va, e premere
    "Installa" fallisce - il manifest, giustamente, rifiuta di installare
    qualcosa che non e' piu' recente di cio' che gira. Vista da fuori e'
    un'app che si offre di aggiornarsi e poi dice di no.

    Vale anche per "salta questa versione": una volta superata, la scelta
    non deve zittire gli avvisi futuri.
    """
    def superata(versione) -> bool:
        """Una versione che non e' piu' avanti di quella installata.
        Un valore illeggibile si considera superato: e' comunque inutile."""
        if not versione:
            return False
        try:
            return not manifest_module.is_newer(str(versione), installata)
        except manifest_module.ManifestError:
            return True

    ripulito = dict(stato)
    if superata((ripulito.get("last_result") or {}).get("version")):
        ripulito.pop("last_result", None)
        ripulito["last_check"] = 0
    if superata(ripulito.get("skipped")):
        ripulito.pop("skipped", None)

    if ripulito != stato:
        import cache
        # Si riscrive lo stato intero, non un merge: qui le chiavi vanno
        # tolte, e _save_state sa solo aggiungerle.
        cache.kv_set(_STATE_KEY, ripulito)
    return ripulito


def _updater_disponibile() -> bool:
    """C'e' l'eseguibile che sostituisce i file, accanto all'applicazione?"""
    if not getattr(sys, "frozen", False):
        return True  # dai sorgenti si usa updater_bin/main.py
    return os.path.exists(os.path.join(install_kind.app_directory(), "updater.exe"))


# ------------------------------------------------------------------ stato

def _state() -> dict:
    import cache

    return cache.kv_get(_STATE_KEY, max_age_seconds=10 ** 9) or {}


def _save_state(**campi) -> None:
    import cache

    cache.kv_set(_STATE_KEY, {**_state(), **campi})


def channel() -> str:
    return _state().get("channel") or manifest_module.CHANNEL_STABLE


def set_channel(nome: str) -> None:
    if nome not in (manifest_module.CHANNEL_STABLE, manifest_module.CHANNEL_BETA):
        raise UpdateError(f"canale sconosciuto: {nome!r}")
    _save_state(channel=nome)


def skip_version(versione: str) -> None:
    """L'utente non vuole sentir parlare di questa versione.

    Vale solo per gli aggiornamenti non obbligatori: uno critico si
    ripropone comunque.
    """
    _save_state(skipped=versione)


def snooze(ore: int = 24) -> None:
    _save_state(remind_after=int(time.time()) + ore * 3600)


# --------------------------------------------------------------- verifica

def check(force: bool = False) -> dict:
    """C'e' un aggiornamento? Non scarica niente, non cambia niente.

    Risposta sempre nella stessa forma, cosi' l'interfaccia non deve
    distinguere fra "non disponibile" e "errore": in entrambi i casi non
    c'e' nulla da proporre all'utente.
    """
    import version

    tipo = install_kind.detect()
    if not install_kind.can_self_update(tipo):
        return {"available": False, "reason": install_kind.explain(tipo),
                "managed_externally": True}
    # Le build fino alla 1.5.x non avevano updater.exe accanto all'app: senza
    # quel file la sostituzione non puo' avvenire, e chiedendolo solo alla
    # fine si scaricavano 41 MB per poi fermarsi su un errore generico. Chi
    # ha una di quelle copie non e' bloccato: scarica a mano, ed e'
    # esattamente cio' che dice il percorso "gestita da qualcun altro".
    if not _updater_disponibile():
        return {"available": False, "reason": "update_needs_manual_download",
                "managed_externally": True}

    stato = _dimentica_il_passato(_state(), version.APP_VERSION)
    if not force:
        if stato.get("remind_after", 0) > time.time():
            return {"available": False, "reason": "postponed"}
        if time.time() - stato.get("last_check", 0) < CHECK_INTERVAL_SECONDS:
            memorizzato = stato.get("last_result")
            if memorizzato:
                return memorizzato
            return {"available": False, "reason": "checked_recently"}

    try:
        grezzo = manifest_module.fetch(channel())
        dati = manifest_module.validate(grezzo, version.APP_VERSION, channel())
    except manifest_module.ManifestError as exc:
        # Nessun aggiornamento valido non e' un errore da mostrare: puo'
        # semplicemente non essercene uno nuovo, o la rete non c'e'.
        logging.info("no applicable update: %s", exc)
        _save_state(last_check=int(time.time()))
        return {"available": False, "reason": "no_update"}

    if not dati.get("mandatory") and stato.get("skipped") == dati["version"]:
        return {"available": False, "reason": "skipped"}

    risultato = {
        "available": True,
        "version": dati["version"],
        "size": dati["size"],
        "mandatory": bool(dati.get("mandatory")),
        "release_notes_url": dati.get("release_notes_url", ""),
        "published_at": dati.get("published_at", ""),
        "channel": dati.get("channel"),
    }
    _save_state(last_check=int(time.time()), last_result=risultato)
    return risultato


# ------------------------------------------------------------- download

def _download(url: str, destinazione: str, attesa: int) -> None:
    richiesta = urllib.request.Request(
        url, headers={"User-Agent": "social-dashboard-updater"})
    try:
        with urllib.request.urlopen(richiesta, timeout=DOWNLOAD_TIMEOUT) as risposta:
            scaricati = 0
            with open(destinazione, "wb") as fh:
                while True:
                    blocco = risposta.read(256 * 1024)
                    if not blocco:
                        break
                    scaricati += len(blocco)
                    if scaricati > MAX_PACKAGE_BYTES:
                        raise UpdateError("pacchetto oltre la dimensione ammessa")
                    fh.write(blocco)
    except (urllib.error.URLError, OSError) as exc:
        raise UpdateError(f"download failed: {exc}") from exc


def _sha256(percorso: str) -> str:
    impronta = hashlib.sha256()
    with open(percorso, "rb") as fh:
        for blocco in iter(lambda: fh.read(1024 * 1024), b""):
            impronta.update(blocco)
    return impronta.hexdigest()


def _estrai(zip_path: str, destinazione: str) -> None:
    """Scompatta rifiutando percorsi fuori posto e archivi spropositati.

    Due controlli distinti:

      Percorsi. Un archivio costruito ad arte puo' contenere voci tipo
      "..\\..\\system32": senza controllo, scompattarlo scriverebbe dove non
      deve.

      Dimensione da scompattato. Un archivio di poche centinaia di kilobyte
      puo' espandersi in decine di gigabyte e riempire il disco. Il pacchetto
      viene gia' confrontato con l'impronta del manifest firmato, quindi
      questo non e' iniettabile da un estraneo - ma un limite costa nulla e
      copre anche il caso di un pacchetto sbagliato costruito da noi.
    """
    with zipfile.ZipFile(zip_path) as archivio:
        radice = os.path.abspath(destinazione)
        totale = 0
        for voce in archivio.infolist():
            finale = os.path.abspath(os.path.join(radice, voce.filename))
            if not finale.startswith(radice + os.sep) and finale != radice:
                raise UpdateError(f"archivio con percorso sospetto: {voce.filename}")
            totale += voce.file_size
            if totale > MAX_EXTRACTED_BYTES:
                raise UpdateError("archivio troppo grande una volta scompattato")
        archivio.extractall(destinazione)


def _staging_dir(work_dir: str) -> str:
    """Dove scompattare la nuova versione.

    Accanto alla cartella dell'applicazione, non nella cartella temporanea
    di sistema: lo scambio finale e' un rinomino, e su Windows un rinomino
    fra volumi diversi non e' possibile. Con TEMP su C: e l'app su D:
    l'aggiornamento fallirebbe sempre, per chiunque non tenga l'app sul
    disco di sistema.

    Se accanto all'app non si puo' scrivere (installazione in una cartella
    protetta), si ripiega sulla cartella temporanea: lo scambio se ne
    accorgera' e copiera' invece di rinominare.
    """
    cartella_app = install_kind.app_directory()
    accanto = os.path.join(os.path.dirname(cartella_app),
                           os.path.basename(cartella_app) + ".new")
    try:
        if os.path.exists(accanto):
            shutil.rmtree(accanto, ignore_errors=True)
        os.makedirs(accanto, exist_ok=True)
        prova = os.path.join(accanto, ".scrivibile")
        with open(prova, "w") as fh:
            fh.write("x")
        os.remove(prova)
        return accanto
    except OSError:
        logging.info("the application directory is not writable; "
                     "the new version will be prepared in the temporary directory")
        ripiego = os.path.join(work_dir, "new")
        os.makedirs(ripiego, exist_ok=True)
        return ripiego


def prepare(manifest_data: dict | None = None) -> dict:
    """Scarica e verifica il pacchetto. Non installa ancora nulla."""
    import version

    tipo = install_kind.detect()
    if not install_kind.can_self_update(tipo):
        raise UpdateError(install_kind.explain(tipo))

    dati = manifest_data
    if dati is None:
        dati = manifest_module.validate(
            manifest_module.fetch(channel()), version.APP_VERSION, channel())

    cartella = tempfile.mkdtemp(prefix="socialdashboard-update-")
    pacchetto = os.path.join(cartella, "package.zip")

    try:
        _download(dati["download_url"], pacchetto, DOWNLOAD_TIMEOUT)

        impronta = _sha256(pacchetto)
        if impronta.lower() != dati["sha256"].lower():
            # Il manifest e' firmato, quindi l'impronta e' quella che abbiamo
            # dichiarato noi: se non combacia, il file scaricato non e' il
            # nostro. Si butta senza aprirlo.
            raise UpdateError("il pacchetto scaricato non corrisponde alla firma")

        estratto = _staging_dir(cartella)
        _estrai(pacchetto, estratto)
        os.remove(pacchetto)
    except Exception:
        # Qualunque cosa vada storta, non si lascia in giro il mezzo
        # scaricamento: sono decine di megabyte che nessuno cancellerebbe.
        shutil.rmtree(cartella, ignore_errors=True)
        raise

    return {"staging_dir": estratto, "work_dir": cartella, "version": dati["version"]}


# --------------------------------------------------------------- applica

def _copia_updater(destinazione: str) -> str:
    """Porta l'updater fuori dalla cartella dell'app.

    Non puo' sostituire la cartella da cui sta girando, quindi lavora da una
    copia in un'altra posizione.
    """
    cartella_app = install_kind.app_directory()
    origine = os.path.join(cartella_app, "updater.exe")
    if os.path.exists(origine):
        copia = os.path.join(destinazione, "updater.exe")
        shutil.copy2(origine, copia)
        return copia

    if getattr(sys, "frozen", False):
        # In una build compilata sys.executable e' l'applicazione, non
        # l'interprete Python: usare il ripiego lancerebbe l'app stessa con
        # gli argomenti dell'updater, che non capirebbe. Meglio fermarsi con
        # un motivo chiaro che fare una cosa senza senso.
        raise UpdateError("updater.exe was not found next to the application; "
                          "this version's package is incomplete")

    # Sorgenti (sviluppo): si esegue lo script con l'interprete corrente.
    return ""


def apply(preparato: dict) -> dict:
    """Avvia il processo separato e chiede all'app di chiudersi.

    Da qui in poi l'aggiornamento non e' piu' nelle nostre mani: se qualcosa
    va storto, e' l'updater a rimettere a posto.

    Un solo aggiornamento per volta: due processi che si contendono la
    stessa cartella si troverebbero uno lo stato dell'altro.
    """
    import cache
    import db

    if not _install_lock.acquire(blocking=False):
        raise UpdateError("an update is already in progress")

    try:
        return _apply(preparato)
    except Exception:
        # Il pacchetto scompattato pesa quanto l'applicazione intera: se lo
        # scambio non parte, va buttato subito. Restava dov'era, e ogni
        # tentativo fallito lasciava un'altra copia da centoventinove
        # megabyte accanto alla cartella dell'app, che nessuno avrebbe mai
        # cercato per cancellarla.
        _pulisci(preparato)
        raise
    finally:
        _install_lock.release()


def _pulisci(preparato: dict) -> None:
    for chiave in ("staging_dir", "work_dir"):
        percorso = preparato.get(chiave)
        if percorso and os.path.exists(percorso):
            shutil.rmtree(percorso, ignore_errors=True)


def _apply(preparato: dict) -> dict:
    import cache
    import db

    cartella_app = install_kind.app_directory()

    # Rete di sicurezza sui dati dell'utente, prima di toccare i file.
    try:
        db.backup.create(cache.DB_PATH, label=f"pre-update-{preparato['version']}")
    except FileNotFoundError:
        pass  # database non ancora creato: non c'e' niente da salvare

    updater = _copia_updater(preparato["work_dir"])
    argomenti = [
        "--app-dir", cartella_app,
        "--new-dir", preparato["staging_dir"],
        "--exe-name", os.path.basename(sys.executable) if getattr(sys, "frozen", False)
                      else "Social Dashboard.exe",
        "--pid", str(os.getpid()),
        "--expect-version", preparato["version"],
    ]

    if updater:
        comando = [updater, *argomenti]
    else:
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "updater_bin", "main.py")
        comando = [sys.executable, script, *argomenti]

    # La cartella di lavoro NON deve essere quella dell'applicazione. Su
    # Windows la directory corrente di un processo la tiene aperta, e
    # l'updater ereditava quella dell'app: appena provava a rinominare la
    # cartella si sentiva rispondere "il file e' utilizzato da un altro
    # processo" - da se' stesso. L'app si chiudeva davvero, i file restavano
    # dov'erano, e l'aggiornamento finiva con un ripristino.
    _avvia_updater(comando, cwd=tempfile.gettempdir())
    logging.info("updater avviato per la versione %s", preparato["version"])
    _chiudi_dopo_la_risposta()
    return {"ok": True, "version": preparato["version"]}


def _avvia_updater(comando: list[str], cwd: str) -> None:
    """Avvia l'updater in modo che sopravviva alla chiusura dell'app.

    Non basta staccarlo dalla console. Se l'applicazione e' stata lanciata
    dentro un "job object" - lo fanno lanciatori, strumenti di gestione da
    remoto, alcune sandbox antivirus e gli ambienti di automazione - i figli
    entrano nello stesso job ed ereditano la sua fine: quando il job si
    chiude vengono terminati tutti insieme. L'updater viene ucciso subito
    dopo essere partito, l'app si e' gia' chiusa per lasciarlo lavorare, e
    l'utente resta senza finestra e senza aggiornamento. E' successo davvero,
    e nel log resta solo la riga "update to X started" senza seguito.

    CREATE_BREAKAWAY_FROM_JOB lo tira fuori dal job. Non tutti i job lo
    consentono: quando e' vietato, CreateProcess rifiuta con "accesso
    negato", e allora si riparte senza - meglio un updater dentro il job che
    nessun updater.
    """
    if sys.platform != "win32":
        subprocess.Popen(comando, cwd=cwd, close_fds=True)
        return

    staccato = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        subprocess.Popen(comando, cwd=cwd, close_fds=True,
                         creationflags=staccato | subprocess.CREATE_BREAKAWAY_FROM_JOB)
    except OSError as exc:
        logging.info("breakaway from the job object refused (%s); "
                     "starting the updater inside it", exc)
        subprocess.Popen(comando, cwd=cwd, close_fds=True, creationflags=staccato)


def _chiudi_dopo_la_risposta(ritardo: float = 1.5) -> None:
    """Chiude l'applicazione poco dopo aver risposto al browser.

    L'updater aspetta che questo processo termini prima di toccare i file:
    e' l'unico momento in cui l'eseguibile non e' piu' bloccato da Windows.
    Nessuno pero' lo chiudeva. Il risultato non era un errore ma un silenzio:
    la barra arrivava al 100%, trenta secondi dopo l'updater rinunciava
    ("the application did not close") e l'utente restava sulla versione
    vecchia senza che niente glielo dicesse. Nel log degli aggiornamenti
    quella riga e' l'esito piu' frequente in assoluto.

    Il ritardo serve a far arrivare la risposta HTTP prima della chiusura,
    altrimenti l'interfaccia mostrerebbe un errore di rete proprio mentre
    l'aggiornamento sta partendo davvero.

    Solo nell'eseguibile: dai sorgenti l'aggiornamento non parte comunque
    (install_kind lo classifica "development"), e un os._exit dentro i test
    ucciderebbe pytest invece di fallire.
    """
    if not getattr(sys, "frozen", False):
        return

    def esci():
        time.sleep(ritardo)
        # Prima la via pulita: chiudere la finestra fa terminare il loop di
        # pywebview e il processo esce da solo, come se l'utente avesse
        # premuto la X.
        try:
            import webview
            for finestra in list(getattr(webview, "windows", [])):
                finestra.destroy()
        except Exception:
            logging.info("no window to close: exiting directly")
        # Se entro qualche secondo siamo ancora qui, si esce comunque: far
        # fallire l'aggiornamento per restare aperti sarebbe il peggiore dei
        # due esiti. Il database e' gia' stato salvato poco sopra.
        time.sleep(3)
        os._exit(0)

    __import__("threading").Thread(target=esci, daemon=True).start()
