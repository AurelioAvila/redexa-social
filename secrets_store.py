"""
Cifratura dei segreti conservati in locale, legata all'account Windows.

Cosa protegge davvero, detto con precisione perche' promettere piu' del
vero e' peggio che non promettere niente:

  Protegge da    il file cache.db copiato via (chiavetta, backup finito su
                 un cloud, sincronizzazione, computer rivenduto) e aperto
                 altrove: senza le credenziali Windows di quell'utente su
                 quella macchina, i token non si decifrano.
                 Protegge anche da un altro account Windows sullo stesso
                 computer.

  NON protegge da un programma malevolo che gira come l'utente stesso:
                 puo' chiedere a DPAPI di decifrare esattamente come fa
                 l'app, o leggere i valori dalla memoria. Nessuna cifratura
                 locale puo' impedirlo, e va scritto nel README invece di
                 lasciar credere il contrario.

Si usa DPAPI di Windows tramite ctypes: nessuna libreria da aggiungere,
nessuna chiave da custodire (la gestisce il sistema operativo, legata
all'account), niente da inserire all'avvio.

I valori cifrati sono riconoscibili dal prefisso, cosi' un database vecchio
con valori in chiaro resta leggibile e la migrazione sa cosa ha gia' fatto.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import base64
import ctypes
import sys

# Marca i valori cifrati. Serve a distinguerli da quelli in chiaro dei
# database precedenti, e a rendere la migrazione ripetibile senza danni.
PREFIX = "enc:v1:"

# Entropia aggiuntiva legata all'applicazione: non e' un segreto (sta
# dentro l'eseguibile) ma impedisce che un altro programma sullo stesso
# account decifri questi valori chiamando DPAPI a caso.
_ENTROPY = b"SocialDashboard/v1/local-secrets"

_CRYPTPROTECT_UI_FORBIDDEN = 0x01


class SecretUnavailable(Exception):
    """Il valore c'e' ma non e' decifrabile su questo computer/account.

    Succede se il database arriva da un'altra macchina, da un altro utente
    Windows, o dopo una reinstallazione del sistema. Non e' un errore da
    nascondere ne' da trattare come dato corrotto: il rimedio e' ricollegare
    l'account, e i dati restano dove sono.
    """


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32),
                ("pbData", ctypes.POINTER(ctypes.c_char))]


def available() -> bool:
    """DPAPI utilizzabile qui? Falso fuori da Windows (sviluppo, test)."""
    return sys.platform == "win32"


def _to_blob(data: bytes) -> _Blob:
    buffer = ctypes.create_string_buffer(data, len(data))
    return _Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))


def _from_blob(blob: _Blob) -> bytes:
    size = blob.cbData
    out = ctypes.create_string_buffer(size)
    ctypes.memmove(out, blob.pbData, size)
    ctypes.windll.kernel32.LocalFree(blob.pbData)
    return out.raw


def is_protected(value: str) -> bool:
    return isinstance(value, str) and value.startswith(PREFIX)


def protect(value: str) -> str:
    """Cifra un valore. Se e' gia' cifrato lo restituisce com'e'.

    Fuori da Windows restituisce il valore invariato: l'app e' solo per
    Windows, e far fallire lo sviluppo o i test su altri sistemi non
    aggiungerebbe sicurezza a nessuno.
    """
    if value is None or value == "" or is_protected(value):
        return value
    if not available():
        return value

    dati = _to_blob(value.encode("utf-8"))
    entropia = _to_blob(_ENTROPY)
    uscita = _Blob()

    ok = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(dati), None, ctypes.byref(entropia),
        None, None, _CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(uscita),
    )
    if not ok:
        raise SecretUnavailable("CryptProtectData non riuscita")

    return PREFIX + base64.b64encode(_from_blob(uscita)).decode("ascii")


def unprotect(value: str) -> str:
    """Decifra un valore. Un valore in chiaro (database precedente) torna
    invariato, cosi' la lettura funziona prima e dopo la migrazione."""
    if value is None or value == "" or not is_protected(value):
        return value
    if not available():
        raise SecretUnavailable("the value is encrypted but DPAPI is unavailable")

    try:
        grezzo = base64.b64decode(value[len(PREFIX):])
    except Exception as exc:
        raise SecretUnavailable("the encrypted value is unreadable") from exc

    dati = _to_blob(grezzo)
    entropia = _to_blob(_ENTROPY)
    uscita = _Blob()

    ok = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(dati), None, ctypes.byref(entropia),
        None, None, _CRYPTPROTECT_UI_FORBIDDEN, ctypes.byref(uscita),
    )
    if not ok:
        # Caso tipico: database copiato da un altro computer o da un altro
        # account Windows. E' esattamente cio' che la cifratura deve
        # impedire, quindi non e' un guasto: e' il sistema che funziona.
        raise SecretUnavailable("the value cannot be decrypted by this Windows account")

    return _from_blob(uscita).decode("utf-8")
