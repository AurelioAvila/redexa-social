$ErrorActionPreference = 'Stop'
$tempRoot = Join-Path ([IO.Path]::GetTempPath()) ('redexa-shortcut-test-' + [guid]::NewGuid())
$appFolder = New-Item -ItemType Directory -Path (Join-Path $tempRoot 'app')
$links = New-Item -ItemType Directory -Path (Join-Path $tempRoot 'links')
New-Item -ItemType File -Path (Join-Path $appFolder.FullName 'Redexa Social.exe') | Out-Null
$shell = New-Object -ComObject WScript.Shell
$old = $shell.CreateShortcut((Join-Path $links.FullName 'Social Dashboard.lnk'))
$old.TargetPath = Join-Path $appFolder.FullName 'Social Dashboard.exe'
$old.Arguments = '--example'
$old.Save()
$unrelated = $shell.CreateShortcut((Join-Path $links.FullName 'Other.lnk'))
$unrelated.TargetPath = Join-Path $tempRoot 'other.exe'
$unrelated.Save()
1..2 | ForEach-Object {
    & "$PSScriptRoot/../scripts/migrate_shortcuts.ps1" -AppDirectory $appFolder.FullName -ShortcutDirectories $links.FullName
}
$updated = $shell.CreateShortcut((Join-Path $links.FullName 'Redexa Social.lnk'))
if ($updated.TargetPath -ne (Join-Path $appFolder.FullName 'Redexa Social.exe')) { throw 'Target not migrated' }
if ($updated.IconLocation -ne "$($updated.TargetPath),0") { throw 'Icon not migrated' }
if ($updated.Arguments -ne '--example') { throw 'Arguments lost' }
if (Test-Path (Join-Path $links.FullName 'Social Dashboard.lnk')) { throw 'Old shortcut still present' }
if ($shell.CreateShortcut($unrelated.FullName).TargetPath -ne $unrelated.TargetPath) { throw 'Unrelated shortcut changed' }
Write-Output 'Shortcut migration and repeated-run checks passed.'
