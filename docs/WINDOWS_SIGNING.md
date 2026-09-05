# Windows release signing

Use Aurelio Avila's Certum code-signing certificate from the current user's
Windows certificate store. Connect SimplySign Desktop and install Windows SDK
SignTool before signing. The current certificate thumbprint is
`4F8341A74D16077AE1849DC8B8CAC99F22606754`.

Build and test a new release version using the existing release instructions.
After the application, compatibility launcher and updater have been bundled,
sign all three first-party executables before creating the release archive:

```powershell
$ErrorActionPreference = 'Stop'
$signTool = (Get-Command signtool.exe -ErrorAction Stop).Source
$releaseFiles = @(
    'dist/Redexa Social/Redexa Social.exe',
    'dist/Redexa Social/Social Dashboard.exe',
    'dist/Redexa Social/updater.exe'
)
foreach ($releaseFile in $releaseFiles) {
    if (-not (Test-Path -LiteralPath $releaseFile -PathType Leaf)) {
        throw "Missing release file: $releaseFile"
    }
}
foreach ($releaseFile in $releaseFiles) {
    & $signTool sign /sha1 4F8341A74D16077AE1849DC8B8CAC99F22606754 /fd SHA256 /tr http://time.certum.pl /td SHA256 $releaseFile
    if ($LASTEXITCODE -ne 0) { throw "Signing failed: $releaseFile" }
    & $signTool verify /pa /all /v $releaseFile
    if ($LASTEXITCODE -ne 0) { throw "Verification failed: $releaseFile" }
}
```

Review the expected publisher, certificate chain and timestamp. Package only
after every signature verifies successfully. Then generate the archive checksum
and the existing Ed25519-signed update manifest with `scripts/make_manifest.py`.
The updater signing key is separate from the Certum certificate: retain the
existing key and verify the manifest with the application's embedded public key.

Publish under a new version, then submit WinGet using the final archive URL and
checksum. Never replace an already published archive with changed bytes or reuse
its old manifest. The existing cloud build does not have access to SimplySign;
this local signing procedure must complete before publishing a signed release.

The v1.9.3 application, updater and compatibility launcher were signed and
timestamped on 2026-09-05. Verify every subsequent build independently.
Do not disable signature verification or antivirus protection to proceed.
