"""
Accesso al database: connessioni, versionamento dello schema, backup.

Volutamente indipendente dal resto dell'app (non importa cache ne' altro):
il percorso del database arriva sempre da fuori, cosi' anche l'updater, che
gira in un processo separato dove l'app non e' caricata, puo' usarlo per
mettere al sicuro i dati prima di sostituire i file.
"""
from . import backup
from .connection import connect
from .migrations import LATEST, current_version, ensure_current

__all__ = ["connect", "ensure_current", "current_version", "LATEST", "backup"]
