"""
The update manifest: what it says, and when it can be trusted.

A signed manifest proves only that we wrote it. It does not say it is *the
right one now*: a genuine but old copy, replayed by someone intercepting the
network, would walk the user back to an earlier version with known
vulnerabilities. That is why, beyond the signature, there are checks on what
the manifest actually claims.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import json
import re
import urllib.error
import urllib.request

from . import signature

# The available channels. "beta" is chosen in the settings: anyone who does
# not choose it never sees a test build.
CHANNEL_STABLE = "stable"
CHANNEL_BETA = "beta"

MANIFEST_URLS = {
    CHANNEL_STABLE: "https://github.com/AurelioAvila/social-dashboard/releases/latest/download/latest.json",
    CHANNEL_BETA: "https://github.com/AurelioAvila/social-dashboard/releases/latest/download/beta.json",
}

FETCH_TIMEOUT = 15
# A manifest is a small object: anything larger is not a manifest, and this
# avoids holding in memory whatever a hostile server decides to send.
MAX_MANIFEST_BYTES = 64 * 1024

_VERSION_RE = re.compile(r"^\d+(\.\d+){0,3}$")


class ManifestError(Exception):
    """Manifest missing, malformed, or not applicable to this copy."""


def parse_version(raw: str) -> tuple[int, ...]:
    """'1.4.0' -> (1, 4, 0). Raises if it is not a recognizable version."""
    pulita = (raw or "").strip().lstrip("vV")
    if not _VERSION_RE.match(pulita):
        raise ManifestError(f"invalid version: {raw!r}")
    return tuple(int(p) for p in pulita.split("."))


def is_newer(candidate: str, installed: str) -> bool:
    """Compared by numeric component rather than alphabetically: without this
    "1.10.0" would sort before "1.9.0"."""
    a, b = parse_version(candidate), parse_version(installed)
    lunghezza = max(len(a), len(b))
    a += (0,) * (lunghezza - len(a))
    b += (0,) * (lunghezza - len(b))
    return a > b


REQUIRED_FIELDS = ("version", "channel", "download_url", "sha256", "size", "signature")


def validate(manifest: dict, installed_version: str, channel: str = CHANNEL_STABLE,
             public_key_b64: str | None = None) -> dict:
    """Checks that the manifest is authentic AND applicable.

    The order matters: the signature is verified first, so everything read
    afterwards comes from a document we know to be ours.
    """
    if not isinstance(manifest, dict):
        raise ManifestError("manifest non e' un oggetto JSON")

    missing = [c for c in REQUIRED_FIELDS if c not in manifest]
    if missing:
        raise ManifestError(f"missing fields: {', '.join(missing)}")

    # 1. E' nostro?
    try:
        signature.verify(manifest, public_key_b64)
    except signature.SignatureError as exc:
        raise ManifestError(f"firma rifiutata: {exc}") from exc

    # 2. Is it for the channel the user chose? A genuine beta manifest must
    #    not be able to reach someone who asked for stable builds only.
    if manifest.get("channel") != channel:
        raise ManifestError(
            f"manifest del canale {manifest.get('channel')!r}, atteso {channel!r}")

    # 3. Is it newer? This blocks both downgrades and the replay of an old
    #    but genuine manifest, which is the simplest way to walk someone back
    #    to a version with known problems.
    if not is_newer(manifest["version"], installed_version):
        raise ManifestError(
            f"version {manifest['version']} is not newer than the installed version "
            f"({installed_version})")

    # 4. Is this copy recent enough to make the jump?
    minima = manifest.get("minimum_supported_version")
    if minima and is_newer(minima, installed_version):
        raise ManifestError(
            f"update requires version {minima} or later; "
            f"this installation is {installed_version}")

    # 5. The digest has to be a real SHA-256, or checking the downloaded
    #    package would mean nothing.
    impronta = str(manifest.get("sha256", "")).strip()
    if not re.fullmatch(r"[0-9a-fA-F]{64}", impronta):
        raise ManifestError("sha256 must be a valid 64-character digest")

    dimensione = manifest.get("size")
    if not isinstance(dimensione, int) or dimensione <= 0:
        raise ManifestError("size is missing or invalid")

    if not str(manifest.get("download_url", "")).startswith("https://"):
        raise ManifestError("download_url must use HTTPS")

    return manifest


def fetch(channel: str = CHANNEL_STABLE, url: str | None = None) -> dict:
    """Downloads the raw manifest. Does not validate it: validate() does."""
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
        raise ManifestError("manifest too large to be genuine")

    try:
        return json.loads(grezzo)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ManifestError("manifest non e' JSON valido") from exc
    except RecursionError as exc:
        # Infinitely nested JSON: without this the exception would escape
        # raw from a path the caller treats as "no update", and would become
        # an error the user sees.
        raise ManifestError("manifest troppo annidato") from exc
