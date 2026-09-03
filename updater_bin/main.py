"""
The process that replaces the application's files.

It exists separately because on Windows a running executable cannot overwrite
itself: its files are locked as long as the process lives. So the app stages
everything, launches this and closes; this waits until it has genuinely gone,
swaps the folders, restarts it and checks it is alive. If it is not, it puts
the previous version back.

It is copied into a temporary folder before starting: it cannot replace the
folder it is running from.

The rules everything else is subordinate to:

  - The DATA folder is never touched. Only the program's.
  - Nothing is deleted until the new version has proved it starts. The old one
    is kept aside until the very end.
  - If anything does not add up, go back. A user on the previous version is a
    user who can work; one with half an installation is not.

It uses the standard library only: fewer things can be missing at exactly the
moment the app is gone.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request

# How long to wait for the app to close on its own before giving up.
WAIT_FOR_EXIT_SECONDS = 30
# How long the new version gets to answer before it counts as broken.
HEALTH_TIMEOUT_SECONDS = 30
HEALTH_URL = "http://127.0.0.1:8787/api/version"


def log(message: str) -> None:
    """A readable record of what happened, free of sensitive values.

    When an update goes wrong this file is the only thing left to work out
    why: the app was not there.
    """
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {message}"
    print(line, flush=True)
    try:
        folder = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"),
                                "SocialDashboard")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "update.log"), "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def wait_for_exit(pid: int, timeout: int = WAIT_FOR_EXIT_SECONDS) -> bool:
    """Waits until the app's process has genuinely ended.

    Replacing the files while it is still alive means locked files and a
    half-finished folder.
    """
    if not pid:
        return True
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not process_alive(pid):
            return True
        time.sleep(0.4)
    return not process_alive(pid)


def process_alive(pid: int) -> bool:
    if sys.platform != "win32":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    import ctypes

    SYNCHRONIZE = 0x00100000
    handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
    if not handle:
        return False
    ctypes.windll.kernel32.CloseHandle(handle)
    return True


def swap_in(app_dir: str, new_dir: str) -> str:
    """Puts the new version where the old one was.

    Two renames rather than copying file by file: a rename within one volume
    is near-instant and does not leave a half-updated folder if it is
    interrupted. Returns where the old one ended up, so it can be put back.
    """
    old_dir = app_dir.rstrip("\\/") + ".old"
    if os.path.exists(old_dir):
        shutil.rmtree(old_dir, ignore_errors=True)

    os.rename(app_dir, old_dir)
    try:
        try:
            os.rename(new_dir, app_dir)
        except OSError as exc:
            # On Windows a rename across volumes is not possible
            # (WinError 17). It happens when the new version was staged in
            # the system temporary folder on C: and the application lives on
            # another disk. Copy instead: slower, but the only way, and
            # without it the update would fail for anyone who does not keep
            # the app on the system drive.
            if getattr(exc, "winerror", None) != 17 and exc.errno not in (18,):
                raise
            log("new version is on another volume; copying instead of renaming")
            shutil.copytree(new_dir, app_dir)
            shutil.rmtree(new_dir, ignore_errors=True)
    except OSError:
        # Put the old one straight back, or the user is left with no
        # application at all.
        if os.path.exists(app_dir):
            shutil.rmtree(app_dir, ignore_errors=True)
        os.rename(old_dir, app_dir)
        raise
    return old_dir


def launch(exe: str):
    import subprocess

    return subprocess.Popen([exe], cwd=os.path.dirname(exe), close_fds=True)


def is_healthy(expected_version: str, timeout: int = HEALTH_TIMEOUT_SECONDS) -> bool:
    """Is the new version alive, and did it report the right version?

    The process existing is not enough: it could have started and died moments
    later over a missing module. We wait until it genuinely answers.
    """
    deadline = time.time() + timeout
    last_error = ""
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=3) as response:
                data = json.loads(response.read())
            current = str(data.get("current", ""))
            if current == expected_version:
                return True
            last_error = f"responded but reported version {current}"
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last_error = str(exc)
        time.sleep(1)
    log(f"health check failed: {last_error}")
    return False


def run(app_dir: str, new_dir: str, exe_name: str, pid: int,
           expected_version: str) -> int:
    log(f"update to {expected_version} started")

    if not wait_for_exit(pid):
        log("the application did not close; update cancelled without changing files")
        return 2

    try:
        old_dir = swap_in(app_dir, new_dir)
    except OSError as exc:
        # The files were not touched, but the application already closed to
        # let us work: leaving it closed and saying nothing is the worst way
        # to fail. Reopen whatever is there.
        log(f"replacement failed ({exc}); the previous version is intact")
        try:
            launch(os.path.join(app_dir, exe_name))
            log("previous version restarted")
        except OSError as errore:
            log(f"could not reopen the application ({errore}); it is intact "
                f"and must be started by hand")
        return 3

    exe = os.path.join(app_dir, exe_name)
    log("files replaced; restarting")
    try:
        launch(exe)
    except OSError as exc:
        log(f"the new version did not start ({exc}); restoring the previous version")
        return roll_back(app_dir, old_dir, exe_name)

    if not is_healthy(expected_version):
        log("the new version did not respond; restoring the previous version")
        return roll_back(app_dir, old_dir, exe_name)

    shutil.rmtree(old_dir, ignore_errors=True)
    log(f"update to {expected_version} completed")
    return 0


def roll_back(app_dir: str, old_dir: str, exe_name: str) -> int:
    """Puts the previous version back and restarts it.

    Restoring the files and restarting are two different things and are kept
    apart: if the restore works but the restart does not, the user has an
    intact application and only needs to reopen it. Telling them "restore
    failed" in that case is untrue and frightens them for nothing.
    """
    try:
        broken_dir = app_dir.rstrip("\\/") + ".failed"
        if os.path.exists(broken_dir):
            shutil.rmtree(broken_dir, ignore_errors=True)
        if os.path.exists(app_dir):
            os.rename(app_dir, broken_dir)
        os.rename(old_dir, app_dir)
        shutil.rmtree(broken_dir, ignore_errors=True)
    except OSError as exc:
        # Worst case: the files did not make it back. Say exactly where they
        # are, because the only way out of this is by hand.
        log(f"RESTORE FAILED ({exc}). "
            f"The previous version is available at: {old_dir}")
        return 4

    log("previous version restored")

    try:
        launch(os.path.join(app_dir, exe_name))
    except OSError as exc:
        # Every file is in place: only the automatic reopen is missing.
        log(f"automatic restart failed ({exc}); "
            f"the application is intact and must be reopened manually")
        return 6

    log("previous version restarted")
    return 1


def main() -> int:
    p = argparse.ArgumentParser(description="Replace Social Dashboard application files.")
    p.add_argument("--app-dir", required=True)
    p.add_argument("--new-dir", required=True)
    p.add_argument("--exe-name", default="Social Dashboard.exe")
    p.add_argument("--pid", type=int, default=0)
    p.add_argument("--expect-version", required=True)
    args = p.parse_args()

    # A second safety net over the current directory: whoever launches us
    # should already hand us one outside the app's folder, but if it stayed
    # the application's we would be the ones holding it open and the rename
    # would fail. It costs one line and does not depend on who started us.
    try:
        os.chdir(tempfile.gettempdir())
    except OSError:
        pass

    try:
        return run(args.app_dir, args.new_dir, args.exe_name, args.pid,
                      args.expect_version)
    except Exception as exc:  # no failure may go unrecorded
        log(f"unexpected error during update: {exc}")
        return 5


if __name__ == "__main__":
    sys.exit(main())
