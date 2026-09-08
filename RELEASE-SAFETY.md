# Release verification

Every distribution requires two independent checks: Windows Authenticode on
the shipped application, updater and compatibility launcher, and an Ed25519
update manifest describing the exact final ZIP. Neither replaces the other.

`scripts/verify_authenticode.ps1` requires embedded Authenticode signatures,
Windows `Valid` status, publisher **Aurelio Avila**, a timestamp certificate,
and a successful `signtool verify /pa /all /tw` result. Missing timestamps,
untrusted signatures and SignTool warnings fail the gate. SignTool comes from
the Windows SDK. PowerShell 7 (`pwsh.exe`, provided on GitHub's Windows runners)
is required; verification never executes a downloaded application.
See [Microsoft's SignTool reference](https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool).

`scripts/verify_release.py` extracts the final ZIP into a temporary directory,
rejects unsafe or duplicate members, requires all three launchers at the root,
and verifies every EXE and MSI in the archive. Bundled third-party DLLs are not
re-signed as this publisher. Any future separately distributed DLL or installer
needs an explicit release path with equivalent verification before shipping.
The verifier also checks the updater signature against the public key already
shipped in `updater/signature.py`, plus the ZIP hash, size, version, channel and
release URLs. Changing or repackaging a verified artifact requires running the
checks again and generating a new signed manifest.
The ZIP hash is compared before and after publisher and manifest verification;
changed bytes invalidate the result. Release versions are validated before
being written to workflow outputs or used in later commands.

Example for a final stable package (substitute the actual release version):

```powershell
python scripts/verify_release.py --package Redexa-Social-v1.9.4-win64.zip --manifest latest.json --version 1.9.4
```

Omitting `--manifest` performs only the publisher check. This is used before
manifest generation and is **not** sufficient to distribute an update.

## Workflow coverage

- `ci.yml` runs application tests, release rejection tests, signature-policy
  tests and Worker tests on pushes and pull requests. It uses the public brand
  template and needs no production secrets. Release jobs reuse these tests.
- `release.yml` requires a version tag, checks the release configuration,
  verifies binaries before packaging, and verifies the final ZIP and required
  manifest immediately before publishing. Only the selected channel's manifest
  is uploaded, missing files fail publication, and beta releases are prereleases.
  An existing release is refused so previously uploaded assets cannot silently
  replace the locally verified package. Runs for the same ref are serialized.
- `sign-local-manifest.yml` accepts an existing draft and expected ZIP hash. It
  now verifies the actual Windows signatures before signing, then validates the
  final package and manifest before uploading the manifest. It does not publish
  the draft. A missing or mismatched `UPDATE_SIGNING_KEY` blocks the operation.
- `winget-publish.yml` downloads and verifies the selected stable release ZIP
  and manifest before changing the catalog fork or submitting it to WinGet,
  including manual and release-event invocations.
  Its installer selector matches only the exact verified ZIP filename.

## Signing integration still required

The repository contains updater key generation and manifest signing scripts,
but no publisher Authenticode signing provider or signing-session integration.
Hosted builds therefore stop at the publisher gate until that integration is
provided. Do not bypass it or upload the unsigned build as a fallback.

Use the user's existing certificate and authorized signing session to sign the
three local launchers before packaging. Use SHA-256 with a trusted timestamp,
then run the final-package verifier. No new certificate, updater key, credential
names or secret values are introduced by this remediation. The existing
`UPDATE_SIGNING_KEY` must match the public key installed in the app. Production
credentials and signing-session availability have not been inspected.

A valid signature does not guarantee the absence of SmartScreen warnings.

## Website deployment boundary

The official homepage is served by `oauth-proxy/worker.js`, using
`oauth-proxy/branding.js`, on `redexa.getcertsprint.com`. The same Worker also
serves OAuth and licensing through its existing workers.dev endpoint. GitHub
Pages serves `docs/` separately at `aurelioavila.github.io/redexa-social/`.
Changing `docs/` alone does not correct the official landing page.

Keep the existing Worker domains, OAuth redirect allowlist and GitHub Pages
callback documents. Do not add a Pages CNAME or redirect callback URLs as part
of SEO work. Public guide aliases may redirect to their extensionless canonical
URLs; `/exchange` and `/refresh` must remain POST endpoints on all current hosts.
