"""
Il manifest degli aggiornamenti: cosa dice, e quando ci si puo' fidare.

Un manifest firmato dimostra solo che l'abbiamo scritto noi. Non dice che
sia *quello giusto adesso*: una copia autentica ma vecchia, riproposta da
qualcuno che intercetta la rete, farebbe tornare l'utente a una versione
precedente con vulnerabilita' note. Per questo, oltre alla firma, ci sono
controlli su cosa il manifest afferma.
"""
import json
import re
import urllib.error
import urllib.request

from . import signature

# Canali disponibili. "beta" si sceglie dalle impostazioni: chi non lo fa
# non vede mai una versione di prova.
CHANNEL_STABLE = "stable"
CHANNEL_BETA = "beta"

MANIFEST_URLS = {
    CHANNEL_STABLE: "https://github.com/AurelioAvila/social-dashboard/releases/latest/download/latest.json",
    CHANNEL_BETA: "https://github.com/AurelioAvila/social-dashboard/releases/latest/download/beta.json",
}

FETCH_TIMEOUT = 15
# Un manifest e' un oggetto piccolo: qualsiasi cosa piu' grande non e' un
# manifest, ed evita di tenere in memoria cio' che un server ostile manda.
MAX_MANIFEST_BYTES = 64 * 1024

_VERSION_RE = re.compile(r"^\d+(\.\d+){0,3}$")


class ManifestError(Exception):
    """Manifest assente, malformato, o non applicabile a questa copia."""


def parse_version(raw: str) -> tuple[int, ...]:
    """'1.4.0' -> (1, 4, 0). Solleva se non e' una versione riconoscibile."""
    pulita = (raw or "").strip().lstrip("vV")
    if not _VERSION_RE.match(pulita):
        raise ManifestError(f"versione non valida: {raw!r}")
    return tuple(int(p) for p in pulita.split("."))


def is_newer(candidate: str, installed: str) -> bool:
    """Confronto per componenti numeriche, non alfabetico: senza questo
    "1.10.0" risulterebbe precedente a "1.9.0"."""
    a, b = parse_version(candidate), parse_version(installed)
    lunghezza = max(len(a), len(b))
    a += (0,) * (lunghezza - len(a))
    b += (0,) * (lunghezza - len(b))
    return a > b


REQUIRED_FIELDS = ("version", "channel", "download_url", "sha256", "size", "signature")


def validate(manifest: dict, installed_version: str, channel: str = CHANNEL_STABLE,
             public_key_b64: str | None = None) -> dict:
    """Controlla che il manifest sia autentico E applicabile.

    L'ordine conta: la firma si verifica per prima, cosi' tutto cio' che si
    legge dopo proviene da un documento che sappiamo essere nostro.
    """
    if not isinstance(manifest, dict):
        raise ManifestError("manifest non e' un oggetto JSON")

    mancanti = [c for c in REQUIRED_FIELDS if c not in manifest]
    if mancanti:
        raise ManifestError(f"campi mancanti: {', '.join(mancanti)}")

    # 1. E' nostro?
    try:
        signature.verify(manifest, public_key_b64)
    except signature.SignatureError as exc:
        raise ManifestError(f"firma rifiutata: {exc}") from exc

    # 2. E' del canale che l'utente ha scelto? Un manifest beta autentico non
    #    deve poter arrivare a chi ha chiesto solo versioni stabili.
    if manifest.get("channel") != channel:
        raise ManifestError(
            f"manifest del canale {manifest.get('channel')!r}, atteso {channel!r}")

    # 3. E' piu' recente? Blocca sia i downgrade sia il riutilizzo di un
    #    manifest vecchio ma autentico, che e' il modo piu' semplice per
    #    riportare qualcuno a una versione con problemi noti.
    if not is_newer(manifest["version"], installed_version):
        raise ManifestError(
            f"versione {manifest['version']} non successiva a quella installata "
            f"({installed_version})")

    # 4. Questa copia e' abbastanza recente da poter fare il salto?
    minima = manifest.get("minimum_supported_version")
    if minima and is_newer(minima, installed_version):
        raise ManifestError(
            f"aggiornamento riservato alla versione {minima} o successiva; "
            f"questa e' la {installed_version}")

    # 5. L'impronta deve essere una vera SHA-256, altrimenti il controllo del
    #    pacchetto scaricato non significherebbe niente.
    impronta = str(manifest.get("sha256", "")).strip()
    if not re.fullmatch(r"[0-9a-fA-F]{64}", impronta):
        raise ManifestError("sha256 non e' un'impronta valida a 64 cifre")

    dimensione = manifest.get("size")
    if not isinstance(dimensione, int) or dimensione <= 0:
        raise ManifestError("size mancante o non valida")

    if not str(manifest.get("download_url", "")).startswith("https://"):
        raise ManifestError("download_url deve essere https")

    return manifest


def fetch(channel: str = CHANNEL_STABLE, url: str | None = None) -> dict:
    """Scarica il manifest grezzo. Non lo convalida: lo fa validate()."""
    indirizzo = url or MANIFEST_URLS.get(channel)
    if not indirizzo:
        raise ManifestError(f"canale sconosciuto: {channel!r}")

    richiesta = urllib.request.Request(
        indirizzo, headers={"User-Agent": "social-dashboard-updater"})
    try:
        with urllib.request.urlopen(richiesta, timeout=FETCH_TIMEOUT) as risposta:
            grezzo = risposta.read(MAX_MANIFEST_BYTES + 1)
    except (urllib.error.URLError, OSError) as exc:
        raise ManifestError(f"manifest non raggiungibile: {exc}") from exc

    if len(grezzo) > MAX_MANIFEST_BYTES:
        raise ManifestError("manifest troppo grande per essere autentico")

    try:
        return json.loads(grezzo)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ManifestError("manifest non e' JSON valido") from exc
    except RecursionError as exc:
        # JSON annidato all'infinito: senza questo l'eccezione uscirebbe
        # grezza da un percorso che il chiamante gestisce come "nessun
        # aggiornamento", e diventerebbe un errore visibile all'utente.
        raise ManifestError("manifest troppo annidato") from exc
