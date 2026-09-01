"""
Builds and signs a release manifest.

Runs in the pipeline, where the private key arrives from the repository
secrets and never touches the disk in the clear for longer than it must.

    python scripts/make_manifest.py \
        --package Social-Dashboard-v1.4.0-win64.zip \
        --version 1.4.0 \
        --download-url https://github.com/.../Social-Dashboard-v1.4.0-win64.zip \
        --out latest.json

The private key is passed through the environment (UPDATE_SIGNING_KEY),
never as an argument: arguments are visible in the process list and end up in
the pipeline logs.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from updater.manifest import CHANNEL_STABLE  # noqa: E402
from updater.signature import canonical_payload  # noqa: E402


def sha256_of(path: str) -> str:
    impronta = hashlib.sha256()
    with open(path, "rb") as fh:
        for blocco in iter(lambda: fh.read(1024 * 1024), b""):
            impronta.update(blocco)
    return impronta.hexdigest()


def build(package: str, version: str, download_url: str, channel: str,
          minimum_supported: str, mandatory: bool, schema_version: int,
          release_notes_url: str) -> dict:
    return {
        "version": version,
        "channel": channel,
        "minimum_supported_version": minimum_supported,
        "mandatory": mandatory,
        "published_at": datetime.datetime.now(datetime.timezone.utc)
                                .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "download_url": download_url,
        "sha256": sha256_of(package),
        "size": os.path.getsize(package),
        "release_notes_url": release_notes_url,
        "database_schema_version": schema_version,
    }


def sign(manifest: dict, private_key_b64: str) -> dict:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(private_key_b64))
    signature = key.sign(canonical_payload(manifest))
    return {**manifest, "signature": base64.b64encode(signature).decode("ascii")}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--package", required=True, help="release zip archive")
    p.add_argument("--version", required=True)
    p.add_argument("--download-url", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--channel", default=CHANNEL_STABLE)
    p.add_argument("--minimum-supported", default="1.0.0")
    p.add_argument("--mandatory", action="store_true")
    p.add_argument("--schema-version", type=int, default=2)
    p.add_argument("--release-notes-url", default="")
    args = p.parse_args()

    key = os.environ.get("UPDATE_SIGNING_KEY", "").strip()
    if not key:
        print("UPDATE_SIGNING_KEY is not configured; an unsigned manifest "
              "would be rejected by every installation.", file=sys.stderr)
        return 1

    manifest = build(args.package, args.version, args.download_url, args.channel,
                     args.minimum_supported, args.mandatory, args.schema_version,
                     args.release_notes_url)
    signed = sign(manifest, key)

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(signed, fh, indent=2, ensure_ascii=False)

    # Nothing sensitive here: a signature is public by definition.
    print(f"manifest written: {args.out}")
    print(f"  version {signed['version']}  channel {signed['channel']}")
    print(f"  sha256  {signed['sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
