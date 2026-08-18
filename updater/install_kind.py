"""
Come e' stata installata questa copia, e chi ha il diritto di aggiornarla.

Il problema concreto: chi installa con `winget install` ottiene un pacchetto
che winget considera suo e aggiorna con `winget upgrade`. Se anche l'updater
interno sostituisse i file, i due si contenderebbero la stessa cartella -
winget si ritroverebbe una versione diversa da quella che ha in archivio, e
l'utente un'installazione incoerente che nessuno dei due sa piu' riparare.

La regola: se l'ha installata qualcun altro, e' qualcun altro che la
aggiorna. L'app lo dice e si toglie di mezzo.
"""
import os
import sys

PORTABLE = "portable"      # zip scompattato dall'utente: ce ne occupiamo noi
WINGET = "winget"          # gestita da winget: si aggiorna con winget upgrade
DEVELOPMENT = "development"  # eseguita dai sorgenti: non si aggiorna nulla

# winget mette i pacchetti "portable" qui sotto, e crea i collegamenti in
# una cartella Links vicina.
_WINGET_MARKERS = (
    os.path.join("microsoft", "winget", "packages"),
    os.path.join("microsoft", "winget", "links"),
)


def app_directory() -> str:
    """Cartella che contiene l'applicazione installata."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def detect(executable_path: str | None = None) -> str:
    percorso = (executable_path or getattr(sys, "executable", "") or "").lower()

    if not getattr(sys, "frozen", False) and executable_path is None:
        return DEVELOPMENT
    if any(marker in percorso for marker in _WINGET_MARKERS):
        return WINGET
    return PORTABLE


def can_self_update(kind: str | None = None) -> bool:
    return (kind or detect()) == PORTABLE


def explain(kind: str | None = None) -> str:
    """Codice del messaggio da mostrare, tradotto dall'interfaccia."""
    corrente = kind or detect()
    if corrente == WINGET:
        return "update_managed_by_winget"
    if corrente == DEVELOPMENT:
        return "update_running_from_source"
    return ""
