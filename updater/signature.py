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

# The PUBLIC release-signing keys. They can only be replaced by publishing a
# new version of the app, which is exactly what stops an attacker from getting
# a manifest of their own signing accepted.
#
# PUBLIC_KEY_B64 is the key releases are signed with: every installed copy
# trusts it, and the release tooling (make_manifest, verify_release) accepts
# no other, so a manifest older copies would refuse cannot be published.
PUBLIC_KEY_B64 = "PJl96pjORzzxKnWzd/lu60rq8byr5aejv5JkDiscFRQ="

# A second key, trusted from the bridge release on and signing nothing yet.
# The first key's private half exists only as a GitHub secret; this one's is
# also kept offline by the owner. Once most installations run the bridge, the
# two values are swapped and releases are signed with this one
# (RELEASE-SAFETY.md, "Update key rotation").
NEXT_PUBLIC_KEY_B64 = "1k/HuC8GFgKkqSvmH9GLX/pegRhFTHNNd/9/X99oqfw="


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
    """Raises SignatureError if the manifest was not signed by us.

    With no key given, a signature by either trusted key is accepted.
    """
    signature_bytes = manifest.get("signature")
    if not signature_bytes:
        raise SignatureError("manifest carries no signature")

    # Read at call time, not import time, so both values are the live ones.
    keys = [public_key_b64] if public_key_b64 else [PUBLIC_KEY_B64, NEXT_PUBLIC_KEY_B64]
    payload = canonical_payload(manifest)
    for key in keys:
        try:
            public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(key))
        except Exception as exc:
            raise SignatureError("the public key is unusable") from exc
        try:
            public_key.verify(base64.b64decode(signature_bytes), payload)
            return
        except (InvalidSignature, ValueError, TypeError):
            continue
    raise SignatureError("the signature is invalid for this manifest")
