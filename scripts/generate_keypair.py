"""
Generates the key pair that update manifests are signed with.

Run this ONCE, and then:

  - the PUBLIC key is pasted into updater/signature.py and ships inside the
    distributed executable: it can only verify;

  - the PRIVATE key must never enter the repository. It belongs in the
    GitHub Actions secrets and in somewhere safe off this computer (a
    password manager, a USB stick in a drawer).

Losing the private key means never publishing an update that existing
installations will accept again: the only remedy would be asking everyone to
reinstall the app by hand. Backing it up is not a formality.

    python scripts/generate_keypair.py

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import base64
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def main() -> int:
    privata = Ed25519PrivateKey.generate()
    pubblica = privata.public_key()

    from cryptography.hazmat.primitives import serialization

    privata_b64 = base64.b64encode(privata.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )).decode("ascii")

    pubblica_b64 = base64.b64encode(pubblica.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )).decode("ascii")

    print("=" * 70)
    print("PUBLIC KEY - paste into updater/signature.py")
    print("=" * 70)
    print(f'PUBLIC_KEY_B64 = "{pubblica_b64}"')
    print()
    print("=" * 70)
    print("PRIVATE KEY - GitHub Actions secret UPDATE_SIGNING_KEY")
    print("=" * 70)
    print(privata_b64)
    print()
    print("DO NOT commit it or paste it into a chat. Keep an offline backup")
    print("outside this computer. If it is lost, existing installations")
    print("will no longer accept updates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
