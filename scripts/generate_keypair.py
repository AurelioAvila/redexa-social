"""
Genera la coppia di chiavi con cui si firmano i manifest degli aggiornamenti.

Si esegue UNA VOLTA SOLA. Poi:

  - la chiave PUBBLICA va incollata in updater/signature.py e finisce
    dentro l'eseguibile distribuito: serve solo a verificare;

  - la chiave PRIVATA non deve mai entrare nel repository. Va messa fra i
    segreti di GitHub Actions e conservata in un posto sicuro fuori dal
    computer (gestore di password, chiavetta in cassetto).

Perdere la chiave privata significa non poter piu' pubblicare aggiornamenti
che le installazioni esistenti accettino: l'unico rimedio sarebbe far
reinstallare l'app a mano a tutti. Farne una copia di sicurezza non e' una
formalita'.

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
    print("CHIAVE PUBBLICA - da incollare in updater/signature.py")
    print("=" * 70)
    print(f'PUBLIC_KEY_B64 = "{pubblica_b64}"')
    print()
    print("=" * 70)
    print("CHIAVE PRIVATA - segreto GitHub Actions  UPDATE_SIGNING_KEY")
    print("=" * 70)
    print(privata_b64)
    print()
    print("NON committarla. NON incollarla in una chat. Conservane una copia")
    print("fuori da questo computer: se la perdi, le installazioni esistenti")
    print("non accetteranno piu' nessun aggiornamento.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
