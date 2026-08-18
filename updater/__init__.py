"""
Aggiornamento automatico: controllo, verifica della firma, installazione.

Il processo che sostituisce davvero i file sta in updater_bin/, separato di
proposito: su Windows un eseguibile in esecuzione non puo' sovrascrivere se
stesso.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
from . import install_kind, manifest, runner, signature

__all__ = ["manifest", "signature", "install_kind", "runner"]
