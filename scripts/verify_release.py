"""Fail closed on the final ZIP, publisher signatures and update manifest.

A release carries two archives of the same signed build:

* ``Redexa-Social-v<version>-win64.zip`` is what people download, from the
  website, the release page and winget. It holds the application and its
  updater, nothing else.
* ``Redexa-Social-v<version>-update.zip`` is what installed copies fetch. It
  adds ``Social Dashboard.exe``, a launcher that only starts
  ``Redexa Social.exe``. Copies installed before the rename (1.9.1 and older)
  update with their own updater, which restarts ``Social Dashboard.exe`` after
  replacing the files and rolls the update back if that file is missing. The
  application removes the launcher once it has moved the old shortcuts.

The signed manifest describes the update archive in ``download_url``,
``sha256`` and ``size`` (the fields every updater reads) and the download
archive in ``package_url``, ``package_sha256`` and ``package_size``.

This verifier never signs, reads credentials, or executes packaged programs.
The Windows SDK and the Windows trust store are required for Authenticode.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from updater.signature import verify  # noqa: E402

REQUIRED_BINARIES = {'Redexa Social.exe', 'updater.exe'}
LEGACY_LAUNCHER = 'Social Dashboard.exe'
REPOSITORY = 'https://github.com/AurelioAvila/redexa-social'
# Archive suffix -> manifest fields (url, digest, size) that describe it.
KINDS = {
    'win64': ('package_url', 'package_sha256', 'package_size'),
    'update': ('download_url', 'sha256', 'size'),
}


def package_kind(package, version):
    for kind in KINDS:
        if package.name == f'Redexa-Social-v{version}-{kind}.zip':
            return kind
    raise ValueError('Unexpected release package name')


def validate_members(archive, kind):
    seen = set()
    for member in archive.infolist():
        name = member.filename
        path = PurePosixPath(name)
        parts = name.rstrip('/').split('/')
        if (path.is_absolute() or '\\' in name or ':' in name
                or any(p in ('', '.', '..') or p.endswith((' ', '.')) for p in parts)
                or stat.S_ISLNK(member.external_attr >> 16)):
            raise ValueError('Unsafe ZIP member')
        normalized = str(path).casefold()
        if normalized in seen:
            raise ValueError('Duplicate ZIP member')
        seen.add(normalized)
    files = {m.filename for m in archive.infolist() if not m.is_dir()}
    if not REQUIRED_BINARIES <= files:
        raise ValueError('Package must contain the application and updater at its root')
    if kind == 'update' and LEGACY_LAUNCHER not in files:
        raise ValueError('The update package must keep the launcher older installations restart')
    if kind == 'win64' and any(PurePosixPath(f).name.casefold() == LEGACY_LAUNCHER.casefold() for f in files):
        raise ValueError('The download package must not contain the legacy launcher')


def verify_manifest(package, manifest_path, version, channel, kind):
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    verify(manifest)  # Always the public key shipped in the app; no CLI override.
    url, digest, size = KINDS[kind]
    expected = {
        'version': version,
        'channel': channel,
        digest: package_hash(package),
        size: package.stat().st_size,
        url: f'{REPOSITORY}/releases/download/v{version}/{package.name}',
        'release_notes_url': f'{REPOSITORY}/releases/tag/v{version}',
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError('Signed manifest does not match the final package, version, channel or release URLs')


def verify_package(package, kind):
    with tempfile.TemporaryDirectory(prefix='redexa-release-check-') as directory:
        with zipfile.ZipFile(package) as archive:
            validate_members(archive, kind)
            archive.extractall(directory)
        subprocess.run([
            'pwsh.exe', '-NoProfile', '-NonInteractive', '-File',
            str(Path(__file__).with_name('verify_authenticode.ps1')),
            '-Directory', directory,
        ], check=True)


def package_hash(package):
    with package.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_final_package(package, manifest_path, version, channel):
    kind = package_kind(package, version)
    if kind == 'win64' and manifest_path and 'package_url' not in json.loads(
            Path(manifest_path).read_text(encoding='utf-8')):
        # Releases up to 1.10.10 had one archive, named -win64, that was also
        # the update archive. Their signed manifests describe it as such.
        kind = 'update'
    before = package_hash(package)
    verify_package(package, kind)
    if manifest_path:
        verify_manifest(package, manifest_path, version, channel, kind)
    if package_hash(package) != before:
        raise ValueError('Package bytes changed during verification')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', required=True, type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--version', required=True)
    parser.add_argument('--channel', choices=['stable', 'beta'], default='stable')
    args = parser.parse_args()
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', args.version):
        raise ValueError('Invalid release version')
    verify_final_package(args.package, args.manifest, args.version, args.channel)
    print('Final release package verified' if args.manifest else 'Publisher signatures verified; a signed updater manifest is still required')


if __name__ == '__main__':
    main()
