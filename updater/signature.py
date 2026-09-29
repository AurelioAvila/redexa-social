"""
Verification of the update manifest's signature.

Why it is needed when the download already goes over HTTPS: HTTPS guarantees
nobody tampered with the data in transit, not that the file came from us. A
domain that expired and was bought by someone else, a compromised GitHub
account, a corporate proxy intercepting - in every one of those the channel is
encrypted and the package is somebody else's. The signature moves the trust
from the channel to the content.

The app ONLY verifies. The private key is never in here: it lives in the
environment that builds the releases. Disassembling the executable turns up
the public key alone, with which nothing can be signed.

Ed25519 was chosen because the signatures are short, verification is fast, and
it has no parameters to get wrong (unlike RSA, where padding and key size are
decisions that can be made badly).

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import base64
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# The PUBLIC release-signing key. It can only be replaced by publishing a new
# version of the app, which is exactly what stops an attacker from getting a
# manifest of their own signing accepted.
#
# A placeholder until the real pair is generated with
# scripts/generate_keypair.py. With an invalid value verification always fails,
# so an unsigned update cannot get through even by accident.
PUBLIC_KEY_B64 = "PJl96pjORzzxKnWzd/lu60rq8byr5aejv5JkDiscFRQ="


class SignatureError(Exception):
    """Signature missing, malformed, or not a match."""


def canonical_payload(manifest: dict) -> bytes:
    """The exact bytes the signature is computed over.

    The `signature` field is excluded (it cannot sign itself) and the keys are
    sorted with no whitespace: signing and verification have to see precisely
    the same sequence of bytes, or one extra space added by an editor is
    enough to invalidate a legitimate manifest.
    """
    without_signature = {k: v for k, v in manifest.items() if k != "signature"}
    return json.dumps(without_signature, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def verify(manifest: dict, public_key_b64: str | None = None) -> None:
    """Raises SignatureError if the manifest was not signed by us."""
    signature_bytes = manifest.get("signature")
    if not signature_bytes:
        raise SignatureError("manifest carries no signature")

    key = public_key_b64 or PUBLIC_KEY_B64
    try:
        raw_value = base64.b64decode(key)
        public_key = Ed25519PublicKey.from_public_bytes(raw_value)
    except Exception as exc:
        raise SignatureError("the public key is unusable") from exc

    try:
        public_key.verify(base64.b64decode(signature_bytes), canonical_payload(manifest))
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise SignatureError("the signature is invalid for this manifest") from exc
