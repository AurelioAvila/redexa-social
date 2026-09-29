# Release operations

Application source and application tests: `AurelioAvila/redexa-social-source` (private).
Public downloads, signed manifests, WinGet and Discord: `AurelioAvila/redexa-social`.

1. Build from the private source repository only after its CI and relevant local tests pass. Record the exact source commit in the local release evidence.
2. Sign every final Windows executable payload and installer with Aurelio Avila and a trusted timestamp. Verify the packaged signatures before uploading.
3. Create a draft release in this public repository and upload the verified ZIP. Preserve the existing public URL format.
4. Dispatch `sign-local-manifest.yml` here with the draft tag and exact ZIP SHA256. It checks every executable signature, signs using the existing protected key and verifies the manifest against the archive.
5. Verify the resulting manifest and the updater handoff locally before publishing the draft. Publication triggers the existing WinGet submission and Discord announcement once.
6. Verify the public archive, signed latest manifest, website metadata and actual WinGet PR.

No new Windows build or publication may use the historical public application branches as its development source. Historical artifacts are retained byte-for-byte; this migration does not repackage, resign or reannounce them. The current supported release is 1.10.8.
