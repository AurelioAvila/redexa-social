param(
    [Parameter(Mandatory)][string]$AppDirectory,
    [string[]]$ShortcutDirectories = @(
        [Environment]::GetFolderPath('Desktop'),
        [Environment]::GetFolderPath('CommonDesktopDirectory'),
        [Environment]::GetFolderPath('Programs')
    )
)
$ErrorActionPreference = 'Stop'
$appRoot = (Resolve-Path -LiteralPath $AppDirectory).Path
$target = Join-Path $appRoot 'Redexa Social.exe'
if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw 'Redexa Social.exe is missing.' }
$shell = New-Object -ComObject WScript.Shell
$folders = $ShortcutDirectories | Select-Object -Unique
foreach ($folder in $folders) {
    if (-not $folder) { continue }
    foreach ($file in Get-ChildItem -LiteralPath $folder -Filter '*.lnk' -ErrorAction SilentlyContinue) {
        try {
            $link = $shell.CreateShortcut($file.FullName)
            if ([IO.Path]::GetDirectoryName($link.TargetPath) -ine $appRoot) { continue }
            if ([IO.Path]::GetFileName($link.TargetPath) -notin @('Social Dashboard.exe', 'Redexa Social.exe')) { continue }
            $link.TargetPath = $target
            $link.IconLocation = "$target,0"
            $link.WorkingDirectory = $appRoot
            $link.Description = 'Redexa Social - creator analytics'
            $link.Save()
            if ($file.BaseName -eq 'Social Dashboard') {
                $newPath = Join-Path $folder 'Redexa Social.lnk'
                if (-not (Test-Path -LiteralPath $newPath)) {
                    Rename-Item -LiteralPath $file.FullName -NewName 'Redexa Social.lnk'
                }
            }
        } catch {
            Write-Warning "Could not update shortcut '$($file.Name)': $($_.Exception.Message)"
        }
    }
}
