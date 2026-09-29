"""Fail closed on the final ZIP, publisher signatures and update manifest.

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

REQUIRED_BINARIES = {'Redexa Social.exe', 'updater.exe', 'Social Dashboard.exe'}
REPOSITORY = 'https://github.com/AurelioAvila/redexa-social'


def validate_members(archive):
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
        raise ValueError('Package must contain the application, updater and compatibility launcher at its root')


def verify_manifest(package, manifest_path, version, channel):
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    verify(manifest)  # Always the public key shipped in the app; no CLI override.
    with package.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    expected = {
        'version': version,
        'channel': channel,
        'sha256': digest,
        'size': package.stat().st_size,
        'download_url': f'{REPOSITORY}/releases/download/v{version}/{package.name}',
        'release_notes_url': f'{REPOSITORY}/releases/tag/v{version}',
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError('Signed manifest does not match the final package, version, channel or release URLs')


def verify_package(package):
    with tempfile.TemporaryDirectory(prefix='redexa-release-check-') as directory:
        with zipfile.ZipFile(package) as archive:
            validate_members(archive)
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
    before = package_hash(package)
    verify_package(package)
    if manifest_path:
        verify_manifest(package, manifest_path, version, channel)
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
    if args.package.name != f'Redexa-Social-v{args.version}-win64.zip':
        raise ValueError('Unexpected release package name')
    verify_final_package(args.package, args.manifest, args.version, args.channel)
    print('Final release package verified' if args.manifest else 'Publisher signatures verified; a signed updater manifest is still required')


if __name__ == '__main__':
    main()
