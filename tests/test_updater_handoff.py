"""Exercise the process boundary with real Ed25519 evidence and inert payloads."""
import base64
import hashlib
import json
import os
import stat
from pathlib import Path
import subprocess
import sys
import zipfile
from unittest.mock import Mock

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from updater import runner, signature
from updater_bin import main as updater


@pytest.fixture
def handoff(tmp_path, monkeypatch):
    key = Ed25519PrivateKey.generate()
    monkeypatch.setattr(signature, "PUBLIC_KEY_B64", base64.b64encode(
        key.public_key().public_bytes_raw()).decode())
    monkeypatch.setattr(updater, "log", lambda message: None)
    app = tmp_path / "app"
    app.mkdir()
    (app / "Redexa Social.exe").write_bytes(b"old")
    archive = tmp_path / "package.zip"
    manifest = tmp_path / "manifest.json"
    staged = tmp_path / "app.new"
    staged.mkdir()
    (staged / "Redexa Social.exe").write_bytes(b"injected staging payload")

    def evidence(version="99.0.0", channel="stable", member="Redexa Social.exe", **fields):
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr(member, b"authenticated payload")
        data = dict(version=version, channel=channel, download_url="https://example.com/app.zip",
                    size=archive.stat().st_size, sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
        data.update(fields)
        data["signature"] = base64.b64encode(key.sign(signature.canonical_payload(data))).decode()
        manifest.write_text(json.dumps(data), encoding="utf-8")
        return data

    evidence()
    calls = {name: Mock(return_value=True) for name in ("wait_for_exit", "launch", "is_healthy")}
    for name, mock in calls.items():
        monkeypatch.setattr(updater, name, mock)
    calls["swap_in"] = Mock(wraps=updater.swap_in)
    monkeypatch.setattr(updater, "swap_in", calls["swap_in"])
    args = dict(app_dir=str(app), new_dir=str(staged), exe_name="Redexa Social.exe", pid=123,
                expected_version="99.0.0", manifest_path=str(manifest), archive_path=str(archive))
    return args, evidence, calls


@pytest.mark.parametrize("damage", ["missing_manifest", "missing_archive", "unsigned", "invalid_json",
    "oversized_manifest", "manifest_tamper", "archive_tamper", "size", "downgrade", "replay",
    "wrong_key", "channel", "minimum", "expected_version", "exe_escape", "missing_exe"])
def test_evidence_failures_never_swap_or_launch(handoff, damage):
    args, evidence, calls = handoff
    manifest, archive = Path(args["manifest_path"]), Path(args["archive_path"])
    if damage == "missing_manifest":
        manifest.unlink()
    elif damage == "missing_archive":
        archive.unlink()
    elif damage == "invalid_json":
        manifest.write_text("{")
    elif damage == "oversized_manifest":
        manifest.write_bytes(b" " * 65537)
    elif damage in ("unsigned", "manifest_tamper", "wrong_key"):
        data = json.loads(manifest.read_text())
        if damage == "unsigned":
            del data["signature"]
        elif damage == "manifest_tamper":
            data["sha256"] = "0" * 64
        else:
            data["signature"] = base64.b64encode(Ed25519PrivateKey.generate().sign(
                signature.canonical_payload(data))).decode()
        manifest.write_text(json.dumps(data))
    elif damage == "archive_tamper":
        original = archive.read_bytes()
        archive.write_bytes(b"!" + original[1:])
    elif damage == "size":
        evidence(size=1)
    elif damage in ("downgrade", "replay"):
        args["expected_version"] = "1.0.0" if damage == "downgrade" else updater.APP_VERSION
        evidence(version=args["expected_version"])
    elif damage == "channel":
        evidence(channel="beta")
    elif damage == "minimum":
        evidence(minimum_supported_version="98.0.0")
    elif damage == "expected_version":
        args["expected_version"] = "100.0.0"
    elif damage == "exe_escape":
        args["exe_name"] = "../outside.exe"
    else:
        evidence(member="readme.txt")
    assert updater.run(**args) == 7
    calls["swap_in"].assert_not_called()
    calls["launch"].assert_not_called()
    assert (Path(args["app_dir"]) / "Redexa Social.exe").read_bytes() == b"old"


def test_installs_only_fresh_authenticated_extraction(handoff):
    args, _, calls = handoff
    assert updater.run(**args) == 0
    assert (Path(args["app_dir"]) / "Redexa Social.exe").read_bytes() == b"authenticated payload"
    assert (Path(args["new_dir"]) / "Redexa Social.exe").read_bytes() == b"injected staging payload"
    staging = Path(calls["swap_in"].call_args.args[1])
    assert staging.parent == Path(args["app_dir"]).parent
    assert staging.name.startswith(".redexa-update-")
    assert not staging.exists()
    calls["launch"].assert_called_once()


def test_archive_replaced_after_verification_is_not_reopened(handoff):
    args, _, calls = handoff
    def replace_archive(pid):
        Path(args["archive_path"]).write_bytes(b"changed after verification")
        return True
    calls["wait_for_exit"].side_effect = replace_archive
    assert updater.run(**args) == 0
    assert (Path(args["app_dir"]) / "Redexa Social.exe").read_bytes() == b"authenticated payload"


def test_running_app_is_not_replaced(handoff):
    args, _, calls = handoff
    calls["wait_for_exit"].return_value = False
    assert updater.run(**args) == 2
    calls["swap_in"].assert_not_called()
    calls["launch"].assert_not_called()


def test_signed_symlink_entry_is_refused(handoff):
    args, evidence, calls = handoff
    link = zipfile.ZipInfo("Redexa Social.exe")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    evidence(member=link)
    assert updater.run(**args) == 7
    calls["swap_in"].assert_not_called()
    calls["launch"].assert_not_called()


def test_case_colliding_archive_entries_are_refused(tmp_path):
    archive = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("App.exe", b"one")
        z.writestr("app.exe", b"two")
    destination = tmp_path / "unpacked"
    destination.mkdir()
    with pytest.raises(runner.UpdateError, match="suspicious path"):
        runner._extract(archive, destination)
    assert list(destination.iterdir()) == []


def test_prepare_authenticates_supplied_manifest_before_download(monkeypatch):
    download = Mock()
    monkeypatch.setattr(runner, "_download", download)
    monkeypatch.setattr(runner.install_kind, "detect", lambda: "portable")
    monkeypatch.setattr(runner, "channel", lambda: "stable")
    with pytest.raises(runner.manifest_module.ManifestError):
        runner.prepare({"version": "99.0.0"})
    download.assert_not_called()


@pytest.mark.parametrize("member", ["../escape.exe", "..\\escape.exe", "/absolute.exe",
    "C:drive.exe", "file:stream", "NUL.txt", "dir./file", "dir /file"])
def test_signed_unsafe_paths_are_refused(handoff, member):
    args, evidence, calls = handoff
    evidence(member=member)
    assert updater.run(**args) == 7
    calls["swap_in"].assert_not_called()
    calls["launch"].assert_not_called()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows junction regression")
@pytest.mark.parametrize("target", ["app", "app.old", "app.failed", "evidence"])
def test_junction_paths_are_refused(handoff, tmp_path, target):
    args, _, calls = handoff
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel").write_text("untouched")
    junction = tmp_path / target
    if target == "app":
        (junction / "Redexa Social.exe").unlink()
        junction.rmdir()
    # cmd's mklink is needed only to construct an inert test junction.
    subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(outside)], check=True,
                   capture_output=True)
    try:
        if target == "evidence":
            args["manifest_path"] = str(junction / "manifest.json")
        assert updater.run(**args) == 7
        calls["swap_in"].assert_not_called()
        calls["launch"].assert_not_called()
        assert (outside / "sentinel").read_text() == "untouched"
    finally:
        os.rmdir(junction)


def test_current_installed_updater_is_copied_not_downloaded(tmp_path, monkeypatch):
    app, work = tmp_path / "app", tmp_path / "work"
    app.mkdir()
    work.mkdir()
    (app / "updater.exe").write_bytes(b"current installed updater")
    monkeypatch.setattr(runner.install_kind, "app_directory", lambda: str(app))
    assert Path(runner._copy_updater(str(work))).read_bytes() == b"current installed updater"


def test_source_cli_has_no_trust_key_override(tmp_path):
    script = Path(updater.__file__).resolve()
    result = subprocess.run([sys.executable, str(script), "--help"], cwd=tmp_path,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "--manifest" in result.stdout and "--archive" in result.stdout
    assert "--public-key" not in result.stdout and "--installed-version" not in result.stdout


def test_standalone_import_does_not_load_application_storage(tmp_path):
    root = Path(updater.__file__).resolve().parent.parent
    result = subprocess.run([sys.executable, "-c",
        "import sys; sys.path.insert(0, sys.argv[1]); "
        "from updater_bin import main; "
        "assert 'cache' not in sys.modules and 'db' not in sys.modules; "
        "assert 'cryptography.hazmat.primitives.asymmetric.ed25519' in sys.modules",
        str(root)], cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
