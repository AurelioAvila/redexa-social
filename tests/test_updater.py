"""
Manifest, signature and installation of an update.

An updater is the most dangerous code in a desktop app: it replaces binaries
and can leave an unusable installation on a computer we have no access to. The
cases that matter here are not the ones where it works, but the ones where it
must NOT: a wrong signature, an altered package, an earlier version served
again.
"""
import base64
import sys
import time
import types
import hashlib
import json
import os
import zipfile

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from updater import install_kind, manifest as manifest_module, signature
from updater.manifest import ManifestError


@pytest.fixture()
def key_pair():
    private_key = Ed25519PrivateKey.generate()
    pubblica_b64 = base64.b64encode(private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )).decode("ascii")
    return private_key, pubblica_b64


def sign_manifest(manifest: dict, private_key) -> dict:
    signature_bytes = private_key.sign(signature.canonical_payload(manifest))
    return {**manifest, "signature": base64.b64encode(signature_bytes).decode("ascii")}


@pytest.fixture()
def valid_manifest(key_pair):
    private_key, _ = key_pair
    return sign_manifest({
        "version": "1.5.0",
        "channel": "stable",
        "minimum_supported_version": "1.0.0",
        "mandatory": False,
        "published_at": "2026-08-18T10:00:00Z",
        "download_url": "https://github.com/x/y/releases/download/v1.5.0/pkg.zip",
        "sha256": "a" * 64,
        "size": 34_000_000,
        "release_notes_url": "https://example.com/notes",
        "database_schema_version": 2,
    }, private_key)


class TestVersionComparison:
    def test_compared_numerically_not_alphabetically(self):
        """The case that breaks a string comparison: without numbers,
        "1.10.0" would sort before "1.9.0"."""
        assert manifest_module.is_newer("1.10.0", "1.9.0") is True
        assert manifest_module.is_newer("1.9.0", "1.10.0") is False

    def test_different_lengths(self):
        assert manifest_module.is_newer("1.4", "1.4.0") is False
        assert manifest_module.is_newer("1.4.1", "1.4") is True

    def test_unreadable_version_refused(self):
        with pytest.raises(ManifestError):
            manifest_module.parse_version("ultima-versione")


class TestSignature:
    def test_signed_manifest_accepted(self, valid_manifest, key_pair):
        _, public_key = key_pair
        signature.verify(valid_manifest, public_key)  # Does not raise.

    def test_unsigned_manifest_refused(self, valid_manifest, key_pair):
        _, public_key = key_pair
        unsigned = {k: v for k, v in valid_manifest.items() if k != "signature"}
        with pytest.raises(signature.SignatureError):
            signature.verify(unsigned, public_key)

    def test_content_altered_after_signing(self, valid_manifest, key_pair):
        """The real case: somebody takes a genuine manifest and changes the
        download address to point at their own package."""
        _, public_key = key_pair
        tampered = {**valid_manifest, "download_url": "https://malicious.example/pkg.zip"}
        with pytest.raises(signature.SignatureError):
            signature.verify(tampered, public_key)

    def test_signature_from_another_key_refused(self, valid_manifest):
        other_key = Ed25519PrivateKey.generate()
        other_public_key = base64.b64encode(other_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)).decode("ascii")
        with pytest.raises(signature.SignatureError):
            signature.verify(valid_manifest, other_public_key)

    def test_placeholder_public_key_is_not_valid(self, valid_manifest):
        """Until the real key pair is generated, no update gets through: that
        is the intended behaviour, not an oversight."""
        with pytest.raises(signature.SignatureError):
            signature.verify(valid_manifest, signature.PUBLIC_KEY_B64)


class TestManifestValidation:
    def test_a_good_manifest(self, valid_manifest, key_pair):
        _, public_key = key_pair
        assert manifest_module.validate(valid_manifest, "1.4.0", "stable", public_key)

    def test_downgrade_refused(self, valid_manifest, key_pair):
        """An old but genuine manifest, replayed by somebody intercepting the
        network, would take the user back to a version with known problems."""
        _, public_key = key_pair
        with pytest.raises(ManifestError, match="not newer"):
            manifest_module.validate(valid_manifest, "1.6.0", "stable", public_key)

    def test_same_version_refused(self, valid_manifest, key_pair):
        _, public_key = key_pair
        with pytest.raises(ManifestError):
            manifest_module.validate(valid_manifest, "1.5.0", "stable", public_key)

    def test_a_beta_manifest_does_not_reach_stable_users(self, valid_manifest, key_pair):
        private_key, public_key = key_pair
        beta = sign_manifest({**{k: v for k, v in valid_manifest.items()
                                  if k != "signature"}, "channel": "beta"}, private_key)
        with pytest.raises(ManifestError, match="channel"):
            manifest_module.validate(beta, "1.4.0", "stable", public_key)

    def test_minimum_version_too_high(self, valid_manifest, key_pair):
        private_key, public_key = key_pair
        m = sign_manifest({**{k: v for k, v in valid_manifest.items()
                               if k != "signature"},
                            "minimum_supported_version": "1.4.9"}, private_key)
        with pytest.raises(ManifestError, match="requires version"):
            manifest_module.validate(m, "1.4.0", "stable", public_key)

    def test_malformed_digest_refused(self, valid_manifest, key_pair):
        private_key, public_key = key_pair
        m = sign_manifest({**{k: v for k, v in valid_manifest.items()
                               if k != "signature"}, "sha256": "troppo-corta"}, private_key)
        with pytest.raises(ManifestError, match="64-character digest"):
            manifest_module.validate(m, "1.4.0", "stable", public_key)

    def test_non_https_download_refused(self, valid_manifest, key_pair):
        private_key, public_key = key_pair
        m = sign_manifest({**{k: v for k, v in valid_manifest.items()
                               if k != "signature"},
                            "download_url": "http://esempio.it/pkg.zip"}, private_key)
        with pytest.raises(ManifestError, match="HTTPS"):
            manifest_module.validate(m, "1.4.0", "stable", public_key)


class TestInstallationKind:
    def test_a_winget_install_does_not_self_update(self):
        """Two mechanisms replacing the same files would leave winget and the
        app disagreeing about what is installed."""
        path = r"C:\Users\x\AppData\Local\Microsoft\WinGet\Packages\Tizio.App\app.exe"
        assert install_kind.detect(path) == install_kind.WINGET
        assert install_kind.can_self_update(install_kind.WINGET) is False
        assert install_kind.explain(install_kind.WINGET) == "update_managed_by_winget"

    def test_a_portable_install_does_update(self):
        path = r"C:\Users\x\Desktop\Social Dashboard\Social Dashboard.exe"
        assert install_kind.detect(path) == install_kind.PORTABLE
        assert install_kind.can_self_update(install_kind.PORTABLE) is True


class TestPackage:
    def _sample_zip(self, folder, contents=b"fake executable"):
        path = os.path.join(folder, "pkg.zip")
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("Social Dashboard.exe", contents)
        return path

    def test_a_different_digest_discards_the_package(self, tmp_path, monkeypatch,
                                                       valid_manifest, key_pair):
        """The downloaded package is not the one the signed manifest declares:
        throw it away without even opening it."""
        from updater import runner

        zip_path = self._sample_zip(str(tmp_path))
        data = {**valid_manifest, "sha256": "b" * 64,
                "download_url": "https://example.com/pkg.zip"}

        def fake_download(url, destination, wait_seconds):
            import shutil
            shutil.copy(zip_path, destination)

        monkeypatch.setattr(runner, "_download", fake_download)
        monkeypatch.setattr(install_kind, "detect", lambda *a: install_kind.PORTABLE)

        with pytest.raises(runner.UpdateError, match="does not match the signature"):
            runner.prepare(data)

    def test_an_intact_package_is_extracted(self, tmp_path, monkeypatch,
                                              valid_manifest):
        from updater import runner

        zip_path = self._sample_zip(str(tmp_path))
        digest = hashlib.sha256(open(zip_path, "rb").read()).hexdigest()
        data = {**valid_manifest, "sha256": digest}

        def fake_download(url, destination, wait_seconds):
            import shutil
            shutil.copy(zip_path, destination)

        monkeypatch.setattr(runner, "_download", fake_download)
        monkeypatch.setattr(install_kind, "detect", lambda *a: install_kind.PORTABLE)

        result = runner.prepare(data)
        assert os.path.exists(os.path.join(result["staging_dir"], "Social Dashboard.exe"))

    def test_archive_with_paths_outside_the_folder_refused(self, tmp_path):
        """A deliberately crafted archive can hold "..\\..\\something" and write
        outside the destination folder."""
        from updater import runner

        malicious = os.path.join(str(tmp_path), "malicious.zip")
        with zipfile.ZipFile(malicious, "w") as z:
            z.writestr("../../outside.txt", "I should not be here")

        destination = os.path.join(str(tmp_path), "dest")
        os.makedirs(destination)
        with pytest.raises(runner.UpdateError, match="suspicious path"):
            runner._extract(malicious, destination)


class TestFolderSwap:
    """The moment at which the user's installation is at its most fragile."""

    def _fake_installation(self, root, version_string):
        folder = os.path.join(root, "app")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "version.txt"), "w") as fh:
            fh.write(version_string)
        return folder

    def test_the_swap_installs_the_new_and_keeps_the_old(self, tmp_path):
        from updater_bin import main as updater_main

        app = self._fake_installation(str(tmp_path), "1.4.0")
        new_folder = os.path.join(str(tmp_path), "new")
        os.makedirs(new_folder)
        with open(os.path.join(new_folder, "version.txt"), "w") as fh:
            fh.write("1.5.0")

        old_folder = updater_main.swap_in(app, new_folder)

        assert open(os.path.join(app, "version.txt")).read() == "1.5.0"
        assert open(os.path.join(old_folder, "version.txt")).read() == "1.4.0", (
            "the previous version has to stay available for a rollback"
        )

    def test_rollback_restores_the_previous_version(self, tmp_path, monkeypatch):
        from updater_bin import main as updater_main

        app = self._fake_installation(str(tmp_path), "1.4.0")
        new_folder = os.path.join(str(tmp_path), "new")
        os.makedirs(new_folder)
        with open(os.path.join(new_folder, "version.txt"), "w") as fh:
            fh.write("1.5.0-broken")

        old_folder = updater_main.swap_in(app, new_folder)
        monkeypatch.setattr(updater_main, "launch", lambda exe: None)

        updater_main.roll_back(app, old_folder, "Social Dashboard.exe")

        assert open(os.path.join(app, "version.txt")).read() == "1.4.0", (
            "after a failed update the user has to find the app they had "
            "before, working"
        )

    def test_if_the_app_does_not_close_nothing_is_touched(self, tmp_path, monkeypatch):
        """Replacing the files while the app is still alive means locked files
        and a half-finished installation."""
        from updater_bin import main as updater_main

        app = self._fake_installation(str(tmp_path), "1.4.0")
        new_folder = os.path.join(str(tmp_path), "new")
        os.makedirs(new_folder)

        monkeypatch.setattr(updater_main, "wait_for_exit", lambda pid, timeout=30: False)

        code = updater_main.run(app, new_folder, "app.exe", 12345, "1.5.0")

        assert code == 2
        assert open(os.path.join(app, "version.txt")).read() == "1.4.0"
        assert os.path.exists(new_folder), "the downloaded package must not be lost"


class TestFixedVulnerabilities:
    """Defects found by attacking the freshly written code, not by reading it."""

    def test_archive_that_explodes_once_unpacked(self, tmp_path):
        """A few hundred kilobytes that become gigabytes: the package is
        already checked against the signed manifest's digest, so an outsider
        cannot inject one, but a limit also covers the case of a wrong package
        built by us."""
        from updater import runner

        bomb = os.path.join(str(tmp_path), "bomb.zip")
        with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("big.bin", b"\0" * (runner.MAX_EXTRACTED_BYTES + 1024))

        destination = os.path.join(str(tmp_path), "dest")
        os.makedirs(destination)
        with pytest.raises(runner.UpdateError, match="too large once unpacked"):
            runner._extract(bomb, destination)

    def test_a_second_parallel_update_is_rejected(self, monkeypatch):
        """Two processes competing for the same folder would each find the
        other's state."""
        from updater import runner

        runner._install_lock.acquire()
        try:
            with pytest.raises(runner.UpdateError, match="already in progress"):
                runner.apply({"version": "1.5.0", "staging_dir": "x", "work_dir": "y"})
        finally:
            runner._install_lock.release()

    def test_the_notice_goes_away_when_the_version_is_already_installed(self, monkeypatch, tmp_path):
        """The last check's result is valid for a day, but the installed
        version can change sooner: a manual update, winget, a reinstall. From
        then on the stored result announced a version already present, the
        notice would not go away, and pressing "Install" failed - the manifest
        refuses anything that is not newer."""
        from updater import runner

        # A stand-in database: _state reads what kv_set wrote, as it does in
        # production. With a fixed dict, _save_state's merge would put back
        # the very key that was just removed.
        saved_state = {
            "last_check": int(time.time()),
            "last_result": {"available": True, "version": "1.7.2"},
            "skipped": "1.7.2",
        }
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(install_kind, "detect", lambda *a: install_kind.PORTABLE)
        monkeypatch.setattr(install_kind, "app_directory", lambda: str(tmp_path))
        (tmp_path / "updater.exe").write_bytes(b"fake")
        monkeypatch.setattr(runner, "_state", lambda: dict(saved_state))
        import version
        monkeypatch.setattr(version, "APP_VERSION", "1.7.3", raising=False)
        import cache
        def write_state(key, data):
            saved_state.clear()
            saved_state.update(data)

        monkeypatch.setattr(cache, "kv_set", write_state)
        monkeypatch.setattr(runner.manifest_module, "fetch",
                            lambda channel_: (_ for _ in ()).throw(
                                runner.manifest_module.ManifestError("nothing new")))

        result = runner.check()

        assert result["available"] is False, "it was announcing a version already installed"
        assert "last_result" not in saved_state, "the stale stored result is still there"
        assert "skipped" not in saved_state, "the 'skip' of a superseded version is still there"

    def test_a_skipped_future_version_stays_skipped(self, monkeypatch, tmp_path):
        """The clean-up must not eat choices that are still valid."""
        from updater import runner

        state = {"skipped": "2.0.0", "last_check": 0}
        import version
        monkeypatch.setattr(version, "APP_VERSION", "1.7.3", raising=False)
        cleaned_state = runner._forget_superseded_state(state, "1.7.3")
        assert cleaned_state["skipped"] == "2.0.0"

    def test_the_app_exits_after_handing_over_to_the_updater(self, monkeypatch):
        """The defect that made everything else pointless.

        The updater waits for the application to end: that is the only moment
        Windows stops holding the executable locked. But nothing was closing
        it, so every update ended at "the application did not close" thirty
        seconds later, silently.
        """
        from updater import runner

        closed_windows = []
        exits = []

        class FakeWindow:
            def destroy(self):
                closed_windows.append(True)

        fake_webview = types.ModuleType("webview")
        fake_webview.windows = [FakeWindow()]
        monkeypatch.setitem(sys.modules, "webview", fake_webview)
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(runner.time, "sleep", lambda _s: None)
        monkeypatch.setattr(runner.os, "_exit", lambda code: exits.append(code))

        runner._quit_after_responding()
        for _ in range(200):
            if closed_windows and exits:
                break
            time.sleep(0.01)

        assert closed_windows, "the app's window was not closed"
        assert exits == [0], "the process did not exit: the updater would wait in vain"

    def test_from_source_nothing_is_closed(self, monkeypatch):
        """An os._exit inside the tests would kill pytest, and from source the
        update does not start anyway."""
        from updater import runner

        exits = []
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        monkeypatch.setattr(runner.os, "_exit", lambda code: exits.append(code))

        runner._quit_after_responding(delay=0)
        time.sleep(0.1)
        assert exits == []

    def test_without_updater_exe_a_manual_download_is_offered(self, monkeypatch, tmp_path):
        """Builds up to 1.5.x had no updater.exe beside the app.

        Asking for it only at the end meant downloading forty megabytes and
        then stopping on a generic error. Better to say straight away that this
        copy updates by hand, which is the path already provided for
        installations managed by somebody else.
        """
        from updater import runner

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(install_kind, "detect", lambda *a: install_kind.PORTABLE)
        monkeypatch.setattr(install_kind, "app_directory", lambda: str(tmp_path))

        result = runner.check(force=True)
        assert result["available"] is False
        assert result["managed_externally"] is True
        assert result["reason"] == "update_needs_manual_download"

    def test_a_failed_attempt_leaves_no_package_on_disk(self, monkeypatch, tmp_path):
        """The unpacked package is as large as the application: every failed
        attempt left a copy of it beside the app's folder, where nobody would
        have gone looking for it."""
        from updater import runner

        staging = tmp_path / "Social Dashboard.new"
        work = tmp_path / "work"
        staging.mkdir(); work.mkdir()
        (staging / "big.bin").write_bytes(b"x" * 1024)

        def _apply_that_fails(_preparato):
            raise runner.UpdateError("updater.exe not found")

        monkeypatch.setattr(runner, "_apply", _apply_that_fails)

        with pytest.raises(runner.UpdateError):
            runner.apply({"version": "1.7.0", "staging_dir": str(staging),
                          "work_dir": str(work)})

        assert not staging.exists(), "the unpacked new version was left on disk"
        assert not work.exists()

    def test_the_updater_breaks_out_of_the_job_object_that_would_kill_the_app(self, monkeypatch):
        """An updater that dies along with whoever launched it is useless: the
        app has already closed to let it replace the files."""
        from updater import runner

        attempts = []

        def fake_popen(command, **kwargs):
            attempts.append(kwargs.get("creationflags", 0))
            return object()

        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setattr(runner.subprocess, "Popen", fake_popen)
        runner._launch_updater(["updater.exe"], cwd=r"C:\Temp")

        assert attempts, "the updater was not started"
        assert attempts[0] & runner.subprocess.CREATE_BREAKAWAY_FROM_JOB

    def test_if_the_job_forbids_breakaway_the_updater_still_starts(self, monkeypatch):
        """Not every job allows breaking away: an updater inside the job is
        better than no updater."""
        from updater import runner

        attempts = []

        def fake_popen(command, **kwargs):
            flag = kwargs.get("creationflags", 0)
            attempts.append(flag)
            if flag & runner.subprocess.CREATE_BREAKAWAY_FROM_JOB:
                raise OSError("access denied")
            return object()

        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setattr(runner.subprocess, "Popen", fake_popen)
        runner._launch_updater(["updater.exe"], cwd=r"C:\Temp")

        assert len(attempts) == 2, "it did not retry without breakaway"
        assert not (attempts[1] & runner.subprocess.CREATE_BREAKAWAY_FROM_JOB)
        assert attempts[1] & runner.subprocess.DETACHED_PROCESS

    def test_the_updater_does_not_start_inside_the_folder_it_replaces(self, monkeypatch, tmp_path):
        """On Windows a process holds its current directory open.

        The updater inherited the application's, which is exactly the folder it
        has to rename: the rename failed with "the file is in use by another
        process" - by itself. The app had already closed, so the result was a
        cancelled update and a window that had vanished.
        """
        from updater import runner

        app_folder = tmp_path / "Social Dashboard"
        app_folder.mkdir()
        (app_folder / "updater.exe").write_bytes(b"fake")
        work = tmp_path / "work"
        work.mkdir()
        calls = {}

        class FakePopen:
            def __init__(self, command, **kwargs):
                calls["cwd"] = kwargs.get("cwd")

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(install_kind, "app_directory", lambda: str(app_folder))
        monkeypatch.setattr(runner.subprocess, "Popen", FakePopen)
        monkeypatch.setattr(runner, "_quit_after_responding", lambda *a, **k: None)
        import db
        monkeypatch.setattr(db.backup, "create", lambda *a, **k: None)

        runner._apply({"version": "1.7.3", "staging_dir": str(tmp_path / "new"),
                       "work_dir": str(work)})

        started_in = os.path.abspath(calls["cwd"])
        assert not started_in.startswith(os.path.abspath(str(app_folder))), (
            "the updater starts inside the folder it has to rename")

    def test_a_failed_swap_reopens_the_application(self, tmp_path, monkeypatch):
        """The app closed to let us work: if nothing is then touched, leaving
        it closed and saying nothing is the worst way to fail."""
        from updater_bin import main as updater_main

        app = tmp_path / "app"
        app.mkdir()
        restarts = []
        monkeypatch.setattr(updater_main, "wait_for_exit", lambda pid, timeout=30: True)
        monkeypatch.setattr(updater_main, "swap_in",
                            lambda a, n: (_ for _ in ()).throw(OSError("file in use")))
        monkeypatch.setattr(updater_main, "launch", lambda exe: restarts.append(exe))

        result = updater_main.run(str(app), str(tmp_path / "new"),
                                    "Social Dashboard.exe", 0, "1.7.3")

        assert result == 3
        assert restarts == [os.path.join(str(app), "Social Dashboard.exe")]

    def test_a_frozen_build_without_the_updater_stops(self, monkeypatch, tmp_path):
        """In a frozen build sys.executable is the application, not Python:
        the old fallback would have relaunched the app itself with the
        updater's arguments."""
        from updater import runner

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(install_kind, "app_directory", lambda: str(tmp_path))

        with pytest.raises(runner.UpdateError, match="package is incomplete"):
            runner._copy_updater(str(tmp_path))

    def test_swap_across_different_volumes(self, tmp_path, monkeypatch):
        """os.rename across different volumes is not possible on Windows:
        without a fallback, anyone keeping the app on a disk other than the
        system one could NEVER update."""
        from updater_bin import main as updater_main

        app = os.path.join(str(tmp_path), "app")
        new_folder = os.path.join(str(tmp_path), "new")
        os.makedirs(app); os.makedirs(new_folder)
        open(os.path.join(app, "v.txt"), "w").write("1.4.0")
        open(os.path.join(new_folder, "v.txt"), "w").write("1.5.0")

        real_rename = os.rename

        def rename_that_refuses_across_volumes(src, dst):
            if os.path.basename(src) == "new":
                error = OSError(18, "Cross-device link")
                error.winerror = 17
                raise error
            return real_rename(src, dst)

        monkeypatch.setattr(os, "rename", rename_that_refuses_across_volumes)
        old_folder = updater_main.swap_in(app, new_folder)

        assert open(os.path.join(app, "v.txt")).read() == "1.5.0", (
            "across different volumes it has to copy instead of rename"
        )
        assert open(os.path.join(old_folder, "v.txt")).read() == "1.4.0"

    def test_an_oversized_manifest_is_refused(self, monkeypatch):
        """A manifest is a small object. The size limit is what puts extreme
        nesting out of reach: RecursionError would arrive at around 100,000
        levels, and 64 KB does not hold even half that many."""
        from updater import manifest as M

        huge = (b'{"a":' + b"1" * (M.MAX_MANIFEST_BYTES + 1024) + b"}")

        class FakeResponse:
            def read(self, n=None):
                return huge[:n] if n else huge
            def __enter__(self): return self
            def __exit__(self, *a): return False

        monkeypatch.setattr(M.urllib.request, "urlopen", lambda *a, **k: FakeResponse())
        with pytest.raises(M.ManifestError, match="too large to be genuine"):
            M.fetch(url="https://example.com/latest.json")
