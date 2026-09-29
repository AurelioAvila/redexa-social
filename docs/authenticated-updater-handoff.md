# Authenticated updater handoff

The runner validates the signed manifest, downloads and checks the ZIP, then
retains both files. It copies the **currently installed** updater to its temporary
work directory and passes manifest/archive paths, channel and expected version.
It no longer extracts to the predictable `<app>.new` directory.

The separate updater validates the manifest with the unchanged bundled Ed25519
public key, requires a version newer than its bundled `version.APP_VERSION`, and
checks channel, minimum supported version and expected version. Neither a key nor
an installed-version override is accepted on the command line. It copies the ZIP
into an open temporary file, hashes and size-checks that snapshot, and extracts
from that same file, so later replacement of the input ZIP does not change the
installed bytes. Only after authentication and process exit does it extract into
a random, newly created sibling directory and call the existing swap/health/
rollback flow. Evidence failures return 7 without swapping or launching.

Existing path components are checked for symlinks and Windows reparse points,
including evidence paths and installation/backup destinations. ZIP entries reject
traversal, drive paths, alternate data streams, reserved names, symlinks and case
collisions. Staging is checked again before the swap. A protected installation
parent fails closed rather than requesting elevation or extracting elsewhere.

## Transition and packaging

An already installed old runner copies its own old updater and invokes its
existing `--new-dir` protocol. That pair can install a release containing this
change without invoking the incoming updater during the first upgrade. Subsequent
updates use the new runner and new updater together. Mixing a new runner with an
old updater, or invoking the new updater without evidence, fails closed; no legacy
unauthenticated installation fallback is provided. The first upgrade through an
old pair retains that pair's existing vulnerability. Manual installation of a
verified release is the alternative when that exposure is unacceptable.

`updater.spec` builds the standalone one-file `dist/updater.exe`. Its import chain
is `updater_bin/main.py -> updater.manifest -> updater.signature -> cryptography`
and Ed25519. PyInstaller's cryptography hook must collect the native bindings.
The repository root is explicitly in `pathex`. `version.py` defers storage imports
until a database function is called, and the updater spec excludes `cache` and
`db`; importing the standalone updater does not migrate or open application data.
The release workflow already bundles that updater beside the application before
packaging. No release workflow, signing key or publisher-signing rule was changed.

## Verification and limits

Run with the existing audit environment:

```powershell
.venv-audit/Scripts/python.exe -m pytest tests/test_updater.py tests/test_updater_handoff.py tests/test_update_check_on_start.py tests/test_release_safety.py tests/test_release_package_contents.py -ra --basetemp=.pytest-tmp-handoff-final
```

Regressions cover real test-key Ed25519 verification, missing/invalid/altered
evidence, wrong keys, downgrade/replay, channel/version constraints, no swap or
launch on rejection, ignored caller staging, snapshot replacement, process exit,
unsafe ZIP entries, real Windows junctions, copied installed-updater provenance,
CLI arguments and storage-free standalone imports. Payloads are inert; application
launch and health checks are mocked. No live installation is updated.

The local PyInstaller 6.22.3 build passed. The frozen updater authenticated the
published 1.10.4 manifest and rejected its equal-version replay with exit code 7,
without changing the empty test installation. This exercises the bundled Ed25519
dependency, not a successful production upgrade. The verification executable is
unsigned and was not distributed. Full signed install/upgrade/rollback checks and
the existing publisher-signature and timestamp gates remain required for release.

This does not protect against arbitrary code execution with the same user's
rights: such code can replace the trusted updater, alter temporary extraction
files or race path checks. Reparse checks are not handle-based filesystem locks.
The downgrade floor assumes the bundled updater matches its installation; an
attacker able to replace it with an older trusted executable can weaken that floor.
Channel and target-directory arguments are local caller inputs, not a sandbox for
hostile local invocation. Existing health/rollback behavior and cross-process
update concurrency are unchanged. Retained handoff evidence and the running
temporary updater may remain on disk after exit; cleanup is not an authenticity
guarantee.
