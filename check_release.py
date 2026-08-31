"""
Run this check BEFORE distributing a build.

It catches two failures that are otherwise easy to discover too late:
confidential credentials embedded in the executable and a missing token
exchange proxy configuration.

    python check_release.py            # check configuration
    python check_release.py --dist     # also inspect the compiled executable

The command exits with code 1 on failure so CI can block an unsafe release.

Copyright (c) 2026 Aurelio Avila. All rights reserved.
"""
import os
import sys
import zlib

# Google documents installed-app client secrets as non-confidential, so they
# are intentionally excluded. The two values below are confidential.
CONFIDENTIAL = ("INSTAGRAM_APP_SECRET", "TIKTOK_CLIENT_SECRET")

DIST_EXE = os.path.join("dist", "Social Dashboard", "Social Dashboard.exe")


def check_config() -> list[str]:
    problems = []
    try:
        import brand
    except Exception as exc:
        return [f"brand.py could not be imported: {exc}"]

    proxy = (brand.get("OAUTH_PROXY_URL") or "").strip()
    embedded = [name for name in CONFIDENTIAL if (brand.get(name) or "").strip()]

    if not proxy:
        problems.append(
            "OAUTH_PROXY_URL is not configured. Without the proxy, client "
            "secrets are compiled into the executable and can be extracted "
            "by anyone who downloads it (see oauth-proxy/README.md)."
        )
    if embedded:
        problems.append(
            "Confidential credentials are present in brand.py and would be "
            "embedded in the build: " + ", ".join(embedded) + ". Clear them "
            "after enabling the proxy."
        )
    return problems


def _decompressed_blobs(data: bytes):
    """Reconstruct zlib blocks as an extractor would inspect a PyInstaller executable."""
    i = 0
    while i < len(data) - 1:
        if data[i] == 0x78:
            try:
                yield zlib.decompressobj().decompress(data[i:i + 400_000])
            except Exception:
                pass
        i += 1


def check_binary() -> list[str]:
    if not os.path.exists(DIST_EXE):
        return [f"Executable not found ({DIST_EXE}); build it before running this check."]

    try:
        import brand
    except Exception:
        return ["brand.py could not be imported, so the expected values are unknown."]

    wanted = {}
    for name in CONFIDENTIAL:
        value = (brand.get(name) or "").strip()
        if value:
            wanted[name] = value.encode()
    if not wanted:
        return []

    blob = open(DIST_EXE, "rb").read()
    found = set()
    for chunk in _decompressed_blobs(blob):
        for name, needle in wanted.items():
            if needle in chunk:
                found.add(name)
        if len(found) == len(wanted):
            break

    return [
        f"{name} can be extracted from the distributed executable."
        for name in sorted(found)
    ]


def check_starts() -> list[str]:
    """The built application must actually start.

    Three releases went out with an executable that could only open a dialog
    saying "No module named 'webview'": pywebview was installed on the
    developer's machine and missing from requirements.txt, so CI - which
    starts from a clean environment - built packages without the window the
    application opens on its first line of work. Nothing in the pipeline ever
    ran the thing it had just built, so nothing noticed. Everything else here
    inspects the build; this runs it.

    It also protects the update path: the updater replaces the files, starts
    the new version and rolls back if it does not answer. A package that
    cannot start turns every automatic update into a silent rollback.
    """
    import json
    import subprocess
    import time
    import urllib.error
    import urllib.request

    import version

    if not os.path.exists(DIST_EXE):
        return [f"{DIST_EXE} not found: build the application before checking it"]

    url = "http://127.0.0.1:8787/api/version"
    try:
        with urllib.request.urlopen(url, timeout=2):
            return ["port 8787 is already in use: close the running application "
                    "so the check measures the build it just made"]
    except (urllib.error.URLError, OSError):
        pass  # nobody listening: that is what we want

    processo = subprocess.Popen([DIST_EXE], cwd=os.path.dirname(DIST_EXE))
    try:
        scadenza = time.time() + 90
        ultimo = "no answer"
        while time.time() < scadenza:
            if processo.poll() is not None:
                return [f"the application exited immediately (code {processo.returncode}); "
                        "it would show an error dialog instead of a window"]
            try:
                with urllib.request.urlopen(url, timeout=3) as risposta:
                    dati = json.loads(risposta.read())
                riportata = str(dati.get("current", ""))
                if riportata == version.APP_VERSION:
                    return []
                ultimo = (f"it answers but reports version {riportata}, "
                          f"not {version.APP_VERSION}")
            except (urllib.error.URLError, OSError, ValueError) as exc:
                ultimo = str(exc)
            time.sleep(1)
        return [f"the built application did not answer on {url} within 90s: {ultimo}"]
    finally:
        processo.kill()
        processo.wait(timeout=10)


def _version_reminder() -> None:
    """Warn when APP_VERSION still matches the latest Git tag.

    This is informational because an unpublished local tag can be legitimate.
    """
    try:
        import subprocess
        import version
        tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                              capture_output=True, text=True, timeout=5).stdout.strip()
        current_tag = tag.lstrip("vV")
        if current_tag and current_tag == version.APP_VERSION:
            print(f"Reminder: APP_VERSION ({version.APP_VERSION}) matches "
                  f"the latest Git tag ({tag}). For a new release, update "
                  "APP_VERSION in version.py before publishing.")
    except Exception:
        pass  # Missing Git or tags is not a release-check failure.


def main() -> int:
    problems = check_config()
    if "--dist" in sys.argv:
        problems += check_binary()
        problems += check_starts()

    _version_reminder()

    # The exit status is the CI contract. Avoid printing values derived from
    # credential checks, even when they are only credential names.
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
