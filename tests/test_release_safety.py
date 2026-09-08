"""Release gates reject unsigned, substituted and incomplete artifacts."""
import base64
import json
from pathlib import Path
import stat
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from scripts import make_manifest, verify_release
from updater import signature


@pytest.fixture
def package(tmp_path):
    path = tmp_path / 'Redexa-Social-v1.9.4-win64.zip'
    with zipfile.ZipFile(path, 'w') as archive:
        for name in verify_release.REQUIRED_BINARIES:
            archive.writestr(name, b'unsigned test fixture')
    return path


@pytest.fixture
def signed_manifest(package, monkeypatch):
    # Ephemeral test key, never the production key or a stored credential.
    key = Ed25519PrivateKey.generate()
    monkeypatch.setattr(signature, 'PUBLIC_KEY_B64', base64.b64encode(
        key.public_key().public_bytes_raw()).decode())
    manifest = make_manifest.build(str(package), '1.9.4',
        f'{verify_release.REPOSITORY}/releases/download/v1.9.4/{package.name}',
        'stable', '1.0.0', False, 2,
        f'{verify_release.REPOSITORY}/releases/tag/v1.9.4')
    manifest = make_manifest.sign(manifest, base64.b64encode(key.private_bytes_raw()).decode())
    path = package.with_suffix('.json')
    path.write_text(json.dumps(manifest), encoding='utf-8')
    return path, manifest, key


def test_matching_signed_manifest(package, signed_manifest):
    verify_release.verify_manifest(package, signed_manifest[0], '1.9.4', 'stable')


@pytest.mark.parametrize('field,value', [
    ('sha256', '0' * 64), ('size', 1), ('version', '1.9.3'),
    ('channel', 'beta'), ('download_url', 'https://example.com/substitute.zip'),
    ('release_notes_url', 'https://example.com/notes'),
])
def test_even_a_signed_manifest_must_describe_this_package(package, signed_manifest, field, value):
    path, manifest, key = signed_manifest
    manifest[field] = value
    path.write_text(json.dumps(make_manifest.sign(manifest,
        base64.b64encode(key.private_bytes_raw()).decode())), encoding='utf-8')
    with pytest.raises(ValueError, match='does not match'):
        verify_release.verify_manifest(package, path, '1.9.4', 'stable')


def test_unsigned_manifest(package, signed_manifest):
    path, manifest, _ = signed_manifest
    del manifest['signature']
    path.write_text(json.dumps(manifest), encoding='utf-8')
    with pytest.raises(signature.SignatureError):
        verify_release.verify_manifest(package, path, '1.9.4', 'stable')


def test_missing_manifest(package, tmp_path):
    with pytest.raises(FileNotFoundError):
        verify_release.verify_manifest(package, tmp_path / 'absent.json', '1.9.4', 'stable')


def test_changed_zip_after_manifest_signing(package, signed_manifest):
    with zipfile.ZipFile(package, 'a') as archive:
        archive.writestr('extra.txt', 'changed after signing')
    with pytest.raises(ValueError, match='does not match'):
        verify_release.verify_manifest(package, signed_manifest[0], '1.9.4', 'stable')


def test_package_calls_windows_verifier_and_propagates_failure(package, monkeypatch):
    def reject(command, **kwargs):
        assert command[:3] == ['pwsh.exe', '-NoProfile', '-NonInteractive']
        assert kwargs['check'] is True
        root = Path(command[-1])
        assert (root / 'updater.exe').read_bytes() == b'unsigned test fixture'
        raise subprocess.CalledProcessError(1, command)
    monkeypatch.setattr(subprocess, 'run', reject)
    with pytest.raises(subprocess.CalledProcessError):
        verify_release.verify_package(package)


@pytest.mark.parametrize('name', ['../escape.exe', '/absolute.exe', 'C:/escape.exe',
    'file:stream.exe', 'updater.exe.', 'folder/../escape.exe',
    'UPDATER.EXE'])
def test_unsafe_or_duplicate_zip_names(package, name):
    member = zipfile.ZipInfo('fixture')
    member.filename = name  # Preserve backslashes; Windows ZipInfo normalizes constructor input.
    with zipfile.ZipFile(package, 'a') as archive:
        archive.writestr(member, b'unsafe')
    with zipfile.ZipFile(package) as archive, pytest.raises(ValueError):
        verify_release.validate_members(archive)


def test_backslash_member_rejected_before_extraction():
    # ZipInfo normalizes backslashes on Windows when reading an archive.
    # Exercise the raw member policy as well, independently of the host OS.
    member = zipfile.ZipInfo('fixture')
    member.filename = 'nested\\escape.exe'
    with pytest.raises(ValueError, match='Unsafe ZIP'):
        verify_release.validate_members(SimpleNamespace(infolist=lambda: [member]))


def test_symlink_rejected(package):
    info = zipfile.ZipInfo('link.exe')
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(package, 'a') as archive:
        archive.writestr(info, 'updater.exe')
    with zipfile.ZipFile(package) as archive, pytest.raises(ValueError):
        verify_release.validate_members(archive)


@pytest.mark.parametrize('missing', sorted(verify_release.REQUIRED_BINARIES))
def test_each_shipped_launcher_is_required(tmp_path, missing):
    with zipfile.ZipFile(tmp_path / 'incomplete.zip', 'w') as archive:
        for name in verify_release.REQUIRED_BINARIES - {missing}:
            archive.writestr(name, b'fixture')
        with pytest.raises(ValueError, match='must contain'):
            verify_release.validate_members(archive)


@pytest.mark.parametrize('configured', [False, True])
def test_manifest_generation_fails_without_matching_production_key(package, monkeypatch, configured):
    output = package.with_suffix('.json')
    monkeypatch.setattr(sys, 'argv', ['make_manifest.py', '--package', str(package),
        '--version', '1.9.4', '--download-url', 'https://example.com/pkg.zip', '--out', str(output)])
    if configured:
        monkeypatch.setenv('UPDATE_SIGNING_KEY', base64.b64encode(
            Ed25519PrivateKey.generate().private_bytes_raw()).decode())
        with pytest.raises(signature.SignatureError):
            make_manifest.main()
    else:
        monkeypatch.delenv('UPDATE_SIGNING_KEY', raising=False)
        assert make_manifest.main() == 1
    assert not output.exists()


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows Authenticode required')
def test_real_windows_verifier_rejects_unsigned_package(package, capfd):
    with pytest.raises(subprocess.CalledProcessError):
        verify_release.verify_package(package)
    assert 'Invalid or missing embedded Authenticode signature' in capfd.readouterr().err


@pytest.mark.parametrize('phase', ['publisher', 'manifest'])
def test_zip_changed_during_verification_is_rejected(package, monkeypatch, phase):
    def change_bytes(*args):
        with package.open('ab') as stream:
            stream.write(b'changed during verification')
    monkeypatch.setattr(verify_release, 'verify_package', change_bytes if phase == 'publisher' else lambda *a: None)
    monkeypatch.setattr(verify_release, 'verify_manifest', change_bytes if phase == 'manifest' else lambda *a: None)
    with pytest.raises(ValueError, match='bytes changed during verification'):
        verify_release.verify_final_package(package, package.with_suffix('.json'), '1.9.4', 'stable')


def test_unchanged_zip_completes_both_checks(package, monkeypatch):
    calls = []
    monkeypatch.setattr(verify_release, 'verify_package', lambda *a: calls.append('publisher'))
    monkeypatch.setattr(verify_release, 'verify_manifest', lambda *a: calls.append('manifest'))
    verify_release.verify_final_package(package, package.with_suffix('.json'), '1.9.4', 'stable')
    assert calls == ['publisher', 'manifest']
