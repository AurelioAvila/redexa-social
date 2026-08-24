"""
Il processo che sostituisce i file dell'applicazione.

Esiste separato perche' su Windows un eseguibile in esecuzione non puo'
sovrascrivere se stesso: i suoi file sono bloccati finche' il processo vive.
Quindi l'app prepara tutto, lancia questo e si chiude; questo aspetta che
sia davvero uscita, scambia le cartelle, la riavvia e controlla che sia
viva. Se non lo e', rimette indietro la versione precedente.

Viene copiato in una cartella temporanea prima di partire: non puo'
sostituire la cartella da cui sta girando.

Regole a cui tutto il resto e' subordinato:

  - La cartella dei DATI non viene mai toccata. Solo quella del programma.
  - Niente viene cancellato finche' la nuova versione non ha dimostrato di
    avviarsi. La vecchia resta da parte fino all'ultimo.
  - Se qualcosa non torna, si torna indietro. Un utente con la versione
    precedente e' un utente che lavora; uno con mezza installazione no.

Usa solo la libreria standard: meno cose possono mancare proprio nel
momento in cui l'app non c'e' piu'.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import argparse
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.request

# Quanto aspettare che l'app si chiuda da sola prima di rinunciare.
WAIT_FOR_EXIT_SECONDS = 30
# Quanto dare alla nuova versione per rispondere prima di considerarla rotta.
HEALTH_TIMEOUT_SECONDS = 30
HEALTH_URL = "http://127.0.0.1:8787/api/version"


def log(messaggio: str) -> None:
    """Traccia leggibile di cosa e' successo, senza valori sensibili.

    Se un aggiornamento va male, questo file e' l'unica cosa che resta per
    capire perche': l'app non c'era.
    """
    riga = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {messaggio}"
    print(riga, flush=True)
    try:
        cartella = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"),
                                "SocialDashboard")
        os.makedirs(cartella, exist_ok=True)
        with open(os.path.join(cartella, "update.log"), "a", encoding="utf-8") as fh:
            fh.write(riga + "\n")
    except OSError:
        pass


def attendi_uscita(pid: int, timeout: int = WAIT_FOR_EXIT_SECONDS) -> bool:
    """Aspetta che il processo dell'app termini davvero.

    Sostituire i file mentre e' ancora vivo significa file bloccati e una
    cartella a meta'.
    """
    if not pid:
        return True
    scadenza = time.time() + timeout
    while time.time() < scadenza:
        if not processo_vivo(pid):
            return True
        time.sleep(0.4)
    return not processo_vivo(pid)


def processo_vivo(pid: int) -> bool:
    if sys.platform != "win32":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    import ctypes

    SYNCHRONIZE = 0x00100000
    handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
    if not handle:
        return False
    ctypes.windll.kernel32.CloseHandle(handle)
    return True


def scambia(app_dir: str, nuova_dir: str) -> str:
    """Mette la nuova versione al posto della vecchia.

    Due rinomini invece di copiare file per file: un rinomino nello stesso
    volume e' quasi istantaneo e non lascia una cartella mezza aggiornata se
    si interrompe. Restituisce dove e' finita la vecchia, per poterla
    rimettere.
    """
    vecchia_dir = app_dir.rstrip("\\/") + ".old"
    if os.path.exists(vecchia_dir):
        shutil.rmtree(vecchia_dir, ignore_errors=True)

    os.rename(app_dir, vecchia_dir)
    try:
        try:
            os.rename(nuova_dir, app_dir)
        except OSError as exc:
            # Su Windows un rinomino fra volumi diversi non e' possibile
            # (WinError 17). Capita quando la nuova versione e' stata
            # preparata nella cartella temporanea di sistema, su C:, e
            # l'applicazione sta su un altro disco. Si copia: piu' lento,
            # ma e' l'unico modo, e senza questo l'aggiornamento
            # fallirebbe per chiunque non tenga l'app sul disco di sistema.
            if getattr(exc, "winerror", None) != 17 and exc.errno not in (18,):
                raise
            log("new version is on another volume; copying instead of renaming")
            shutil.copytree(nuova_dir, app_dir)
            shutil.rmtree(nuova_dir, ignore_errors=True)
    except OSError:
        # Rimetti subito la vecchia al suo posto, altrimenti l'utente resta
        # senza applicazione.
        if os.path.exists(app_dir):
            shutil.rmtree(app_dir, ignore_errors=True)
        os.rename(vecchia_dir, app_dir)
        raise
    return vecchia_dir


def avvia(exe: str):
    import subprocess

    return subprocess.Popen([exe], cwd=os.path.dirname(exe), close_fds=True)


def in_salute(versione_attesa: str, timeout: int = HEALTH_TIMEOUT_SECONDS) -> bool:
    """La nuova versione e' viva e si e' presentata con la versione giusta?

    Non basta che il processo esista: potrebbe essere partito e morire
    subito dopo per un modulo mancante. Si aspetta che risponda davvero.
    """
    scadenza = time.time() + timeout
    ultimo_errore = ""
    while time.time() < scadenza:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=3) as risposta:
                dati = json.loads(risposta.read())
            corrente = str(dati.get("current", ""))
            if corrente == versione_attesa:
                return True
            ultimo_errore = f"responded but reported version {corrente}"
        except (urllib.error.URLError, OSError, ValueError) as exc:
            ultimo_errore = str(exc)
        time.sleep(1)
    log(f"health check failed: {ultimo_errore}")
    return False


def esegui(app_dir: str, nuova_dir: str, exe_name: str, pid: int,
           versione_attesa: str) -> int:
    log(f"update to {versione_attesa} started")

    if not attendi_uscita(pid):
        log("the application did not close; update cancelled without changing files")
        return 2

    try:
        vecchia_dir = scambia(app_dir, nuova_dir)
    except OSError as exc:
        log(f"replacement failed ({exc}); the previous version is intact")
        return 3

    exe = os.path.join(app_dir, exe_name)
    log("files replaced; restarting")
    try:
        avvia(exe)
    except OSError as exc:
        log(f"the new version did not start ({exc}); restoring the previous version")
        return ripristina(app_dir, vecchia_dir, exe_name)

    if not in_salute(versione_attesa):
        log("the new version did not respond; restoring the previous version")
        return ripristina(app_dir, vecchia_dir, exe_name)

    shutil.rmtree(vecchia_dir, ignore_errors=True)
    log(f"update to {versione_attesa} completed")
    return 0


def ripristina(app_dir: str, vecchia_dir: str, exe_name: str) -> int:
    """Rimette la versione precedente e la riavvia.

    Rimettere i file e riavviare sono due cose distinte, e vanno tenute
    separate: se il ripristino riesce ma il riavvio no, l'utente ha
    l'applicazione integra e deve solo riaprirla. Dirgli "ripristino non
    riuscito" in quel caso e' falso e lo spaventa per niente.
    """
    try:
        rotta_dir = app_dir.rstrip("\\/") + ".failed"
        if os.path.exists(rotta_dir):
            shutil.rmtree(rotta_dir, ignore_errors=True)
        if os.path.exists(app_dir):
            os.rename(app_dir, rotta_dir)
        os.rename(vecchia_dir, app_dir)
        shutil.rmtree(rotta_dir, ignore_errors=True)
    except OSError as exc:
        # Peggiore dei casi: i file non sono tornati al loro posto. Si dice
        # esattamente dove sono, perche' l'unica via d'uscita e' manuale.
        log(f"RESTORE FAILED ({exc}). "
            f"The previous version is available at: {vecchia_dir}")
        return 4

    log("previous version restored")

    try:
        avvia(os.path.join(app_dir, exe_name))
    except OSError as exc:
        # I file ci sono tutti: manca solo la riapertura automatica.
        log(f"automatic restart failed ({exc}); "
            f"the application is intact and must be reopened manually")
        return 6

    log("previous version restarted")
    return 1


def main() -> int:
    p = argparse.ArgumentParser(description="Replace Social Dashboard application files.")
    p.add_argument("--app-dir", required=True)
    p.add_argument("--new-dir", required=True)
    p.add_argument("--exe-name", default="Social Dashboard.exe")
    p.add_argument("--pid", type=int, default=0)
    p.add_argument("--expect-version", required=True)
    args = p.parse_args()

    try:
        return esegui(args.app_dir, args.new_dir, args.exe_name, args.pid,
                      args.expect_version)
    except Exception as exc:  # nessun errore deve restare senza traccia
        log(f"unexpected error during update: {exc}")
        return 5


if __name__ == "__main__":
    sys.exit(main())
