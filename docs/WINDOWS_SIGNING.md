# Windows release signing

Use Aurelio Avila's Certum code-signing certificate from the current user's
Windows certificate store. Connect SimplySign Desktop and install Windows SDK
SignTool before signing. The current certificate thumbprint is
`4F8341A74D16077AE1849DC8B8CAC99F22606754`.

Build and test a new release version using the existing release instructions.
After the application, compatibility launcher and updater have been bundled,
sign every native executable and library before creating the release archive:

```powershell
$ErrorActionPreference = 'Stop'
$signTool = (Get-Command signtool.exe -ErrorAction SilentlyContinue).Source
if (-not $signTool) {
    $signTool = (Get-ChildItem "${env:ProgramFiles(x86)}/Windows Kits/10/bin/*/x64/signtool.exe" |
        Sort-Object FullName -Descending | Select-Object -First 1).FullName
}
if (-not $signTool) { throw 'Windows SDK SignTool is required.' }
$releaseFiles = @(Get-ChildItem -LiteralPath 'dist/Redexa Social' -Recurse -File |
    Where-Object { $_.Extension -in '.exe', '.dll', '.pyd', '.msi' })
if ($releaseFiles.Count -eq 0) { throw 'No native release files found.' }
foreach ($releaseFile in $releaseFiles) {
    & $signTool sign /sha1 4F8341A74D16077AE1849DC8B8CAC99F22606754 /fd SHA256 /tr http://time.certum.pl /td SHA256 $releaseFile.FullName
    if ($LASTEXITCODE -ne 0) { throw "Signing failed: $releaseFile" }
    & $signTool verify /pa /all /tw $releaseFile.FullName
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
