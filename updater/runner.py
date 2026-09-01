"""
The application's side of an update: it decides, downloads, verifies, and
hands over to the separate process.

The order of the checks is not incidental. The manifest signature is verified
first, then the download happens, then the package digest is checked, and only
at the very end is anything touched. Every step that fails leaves the computer
exactly as it was.

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
# A package far larger than expected is a problem, not an update: stop
# downloading rather than fill the disk.
MAX_PACKAGE_BYTES = 300 * 1024 * 1024
# A cap on how much it may occupy once unpacked: a small archive can expand
# enormously.
MAX_EXTRACTED_BYTES = 1024 * 1024 * 1024

# One update at a time. Without this, two requests close together would
# launch two processes contending for the same folder, each believing it is
# alone: the second one's swap would find a state it does not expect.
_install_lock = __import__("threading").Lock()

CHECK_INTERVAL_SECONDS = 24 * 3600
_STATE_KEY = "updater_state"


class UpdateError(Exception):
    pass


def _dimentica_il_passato(stato: dict, installata: str) -> dict:
    """Discards whatever the state says about versions that are no longer ahead.

    The last check's result stays valid for a day, but the installed version
    can change sooner: a manual update, one through winget, or a reinstall is
    enough. From then on the stored result announces a version the user
    already has, the notice will not go away, and pressing "Install" fails -
    the manifest, quite rightly, refuses to install something that is not
    newer than what is running. From outside it looks like an app that offers
    to update itself and then says no.

    The same applies to "skip this version": once it has been passed, that
    choice must not silence future notices.
    """
    def superata(versione) -> bool:
        """A version that is no longer ahead of the installed one.
        An unreadable value counts as passed: it is useless either way."""
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
        # The whole state is rewritten rather than merged: keys have to be
        # removed here, and _save_state only knows how to add them.
        cache.kv_set(_STATE_KEY, ripulito)
    return ripulito


def _updater_disponibile() -> bool:
    """Is the executable that replaces the files sitting beside the app?"""
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
    """The user does not want to hear about this version.

    Applies to non-mandatory updates only: a critical one comes back anyway.
    """
    _save_state(skipped=versione)


def snooze(ore: int = 24) -> None:
    _save_state(remind_after=int(time.time()) + ore * 3600)


# --------------------------------------------------------------- verifica

def check(force: bool = False) -> dict:
    """Is there an update? Nothing is downloaded, nothing is changed.

    The answer always takes the same shape, so the interface does not have to
    tell "not available" from "error": in both cases there is nothing to offer
    the user.
    """
    import version

    tipo = install_kind.detect()
    if not install_kind.can_self_update(tipo):
        return {"available": False, "reason": install_kind.explain(tipo),
                "managed_externally": True}
    # Builds up to 1.5.x had no updater.exe beside the app: without that
    # file the replacement cannot happen, and asking only at the end meant
    # downloading 41 MB before stopping on a generic error. Anyone on one of
    # those copies is not stuck: they download by hand, which is exactly what
    # the "managed by someone else" path already says.
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
        # No valid update is not an error worth showing: there may simply
        # not be a newer one, or the network may be gone.
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
    """Unpacks, refusing misplaced paths and disproportionate archives.

    Two separate checks:

      Paths. A deliberately crafted archive can hold entries like
      "..\\..\\system32": unchecked, unpacking it would write where it must
      not.

      Unpacked size. An archive of a few hundred kilobytes can expand into
      tens of gigabytes and fill the disk. The package is already compared
      against the digest in the signed manifest, so this is not something an
      outsider can inject - but a limit costs nothing and also covers a bad
      package built by us.
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
    """Where to unpack the new version.

    Beside the application's folder, not in the system temporary directory:
    the final swap is a rename, and on Windows a rename across volumes is not
    possible. With TEMP on C: and the app on D: the update would fail every
    time, for anyone who does not keep the app on the system disk.

    If writing next to the app is not allowed (an install in a protected
    folder), it falls back to the temporary directory: the swap will notice
    and copy instead of renaming.
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
    """Downloads and verifies the package. Installs nothing yet."""
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
            # The manifest is signed, so the digest is the one we declared:
            # if it does not match, the downloaded file is not ours. It is
            # thrown away without being opened.
            raise UpdateError("il pacchetto scaricato non corrisponde alla firma")

        estratto = _staging_dir(cartella)
        _estrai(pacchetto, estratto)
        os.remove(pacchetto)
    except Exception:
        # Whatever goes wrong, the half-finished download is not left lying
        # around: it is tens of megabytes nobody would ever delete.
        shutil.rmtree(cartella, ignore_errors=True)
        raise

    return {"staging_dir": estratto, "work_dir": cartella, "version": dati["version"]}


# --------------------------------------------------------------- applica

def _copia_updater(destinazione: str) -> str:
    """Moves the updater out of the app's folder.

    It cannot replace the folder it is running from, so it works from a copy
    somewhere else.
    """
    cartella_app = install_kind.app_directory()
    origine = os.path.join(cartella_app, "updater.exe")
    if os.path.exists(origine):
        copia = os.path.join(destinazione, "updater.exe")
        shutil.copy2(origine, copia)
        return copia

    if getattr(sys, "frozen", False):
        # In a compiled build sys.executable is the application, not the
        # Python interpreter: taking the fallback would launch the app itself
        # with the updater's arguments, which it would not understand. Better
        # to stop with a clear reason than to do something senseless.
        raise UpdateError("updater.exe was not found next to the application; "
                          "this version's package is incomplete")

    # From source (development): run the script with the current interpreter.
    return ""


def apply(preparato: dict) -> dict:
    """Starts the separate process and asks the app to close.

    From here on the update is out of our hands: if something goes wrong, the
    updater is what puts it back.

    One update at a time: two processes contending for the same folder would
    each find the other's state.
    """
    import cache
    import db

    if not _install_lock.acquire(blocking=False):
        raise UpdateError("an update is already in progress")

    try:
        return _apply(preparato)
    except Exception:
        # The unpacked package weighs as much as the whole application: if
        # the swap does not start, it has to go immediately. It used to stay
        # where it was, and every failed attempt left another
        # hundred-and-twenty-nine megabyte copy beside the app's folder that
        # nobody would ever have gone looking for to delete.
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

    # A safety net over the user's data, before any file is touched.
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

    # The working directory MUST NOT be the application's. On Windows a
    # process's current directory holds that directory open, and the updater
    # was inheriting the app's: the moment it tried to rename the folder it
    # was told "the file is in use by another process" - by itself. The app
    # really did close, the files stayed where they were, and the update ended
    # in a rollback.
    _avvia_updater(comando, cwd=tempfile.gettempdir())
    logging.info("updater avviato per la versione %s", preparato["version"])
    _chiudi_dopo_la_risposta()
    return {"ok": True, "version": preparato["version"]}


def _avvia_updater(comando: list[str], cwd: str) -> None:
    """Starts the updater so that it outlives the app closing.

    Detaching it from the console is not enough. If the application was
    launched inside a "job object" - launchers, remote-management tools, some
    antivirus sandboxes and automation environments all do this - the children
    join the same job and inherit its end: when the job closes they are all
    terminated together. The updater is killed moments after starting, the app
    has already closed to let it work, and the user is left with no window and
    no update. This genuinely happened, and all the log keeps is the line
    "update to X started" with nothing after it.

    CREATE_BREAKAWAY_FROM_JOB pulls it out of the job. Not every job permits
    that: where it is forbidden, CreateProcess refuses with "access denied",
    and then we start again without it - an updater inside the job beats no
    updater at all.
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
    """Closes the application shortly after answering the browser.

    The updater waits for this process to end before touching any file: that
    is the only moment the executable is no longer locked by Windows. Nothing,
    however, was closing it. The result was not an error but a silence: the bar
    reached 100%, thirty seconds later the updater gave up ("the application
    did not close") and the user stayed on the old version with nothing to
    tell them. In the update log that line is the single most common outcome.

    The delay is there to let the HTTP response arrive before the shutdown, or
    the interface would show a network error at the exact moment the update is
    genuinely starting.

    Only in the executable: from source the update does not start anyway
    (install_kind classifies it as "development"), and an os._exit inside the
    tests would kill pytest rather than fail.
    """
    if not getattr(sys, "frozen", False):
        return

    def esci():
        time.sleep(ritardo)
        # The clean way first: closing the window ends pywebview's loop and
        # the process exits on its own, as though the user had clicked the X.
        try:
            import webview
            for finestra in list(getattr(webview, "windows", [])):
                finestra.destroy()
        except Exception:
            logging.info("no window to close: exiting directly")
        # If we are still here a few seconds later, exit anyway: failing the
        # update in order to stay open is the worse of the two outcomes. The
        # database was already saved just above.
        time.sleep(3)
        os._exit(0)

    __import__("threading").Thread(target=esci, daemon=True).start()
