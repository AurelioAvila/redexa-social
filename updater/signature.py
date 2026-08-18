"""
Verifica della firma del manifest degli aggiornamenti.

Perche' serve, dato che si scarica gia' via HTTPS: HTTPS garantisce che
nessuno abbia manomesso i dati durante il trasporto, non che il file venga
da noi. Un dominio scaduto e ricomprato, un account GitHub compromesso, un
proxy aziendale che intercetta - in tutti questi casi il canale e' cifrato
e il pacchetto e' di qualcun altro. La firma sposta la fiducia dal canale
al contenuto.

L'app SOLO verifica. La chiave privata non e' mai qui dentro: sta
nell'ambiente che crea le release. Anche disassemblando l'eseguibile si
trova solo la chiave pubblica, con cui non si puo' firmare nulla.

Ed25519 e' scelto perche' le firme sono corte, la verifica e' veloce e non
ha parametri da sbagliare (a differenza di RSA, dove padding e dimensione
della chiave sono decisioni che si possono prendere male).

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import base64
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# Chiave PUBBLICA di firma delle release. Sostituibile solo pubblicando una
# nuova versione dell'app: e' esattamente cio' che impedisce a un attaccante
# di far accettare un manifest firmato da lui.
#
# Segnaposto finche' non viene generata la coppia definitiva con
# scripts/generate_keypair.py. Con un valore non valido la verifica fallisce
# sempre, quindi un aggiornamento non firmato non passa nemmeno per errore.
PUBLIC_KEY_B64 = "REPLACE_WITH_RELEASE_PUBLIC_KEY"


class SignatureError(Exception):
    """Firma assente, malformata o non corrispondente."""


def canonical_payload(manifest: dict) -> bytes:
    """I byte esatti su cui si calcola la firma.

    Il campo `signature` viene escluso (non puo' firmare se stesso) e le
    chiavi sono ordinate senza spazi: firma e verifica devono vedere
    esattamente la stessa sequenza di byte, altrimenti basta uno spazio in
    piu' aggiunto da un editor per invalidare un manifest legittimo.
    """
    senza_firma = {k: v for k, v in manifest.items() if k != "signature"}
    return json.dumps(senza_firma, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def verify(manifest: dict, public_key_b64: str | None = None) -> None:
    """Solleva SignatureError se il manifest non e' firmato da noi."""
    firma = manifest.get("signature")
    if not firma:
        raise SignatureError("manifest senza firma")

    chiave = public_key_b64 or PUBLIC_KEY_B64
    try:
        grezza = base64.b64decode(chiave)
        pubblica = Ed25519PublicKey.from_public_bytes(grezza)
    except Exception as exc:
        raise SignatureError("chiave pubblica non utilizzabile") from exc

    try:
        pubblica.verify(base64.b64decode(firma), canonical_payload(manifest))
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise SignatureError("firma non valida per questo manifest") from exc
