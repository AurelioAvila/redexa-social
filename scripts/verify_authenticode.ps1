param([Parameter(Mandatory = $true)][string]$Directory)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Find-SignTool {
    $command = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $sdk = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits/10/bin'
    $tool = Get-ChildItem -Path "$sdk/*/x64/signtool.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
    if (-not $tool) { throw 'Windows SDK SignTool is required; distribution is blocked.' }
    return $tool.FullName
}

function Assert-PublisherSignature([string]$Path, [string]$SignTool) {
    $signature = Get-AuthenticodeSignature -LiteralPath $Path
    if ($signature.Status -ne 'Valid' -or $signature.SignatureType -ne 'Authenticode') {
        throw "Invalid or missing embedded Authenticode signature: $Path"
    }
    $publisher = $signature.SignerCertificate.GetNameInfo(
        [System.Security.Cryptography.X509Certificates.X509NameType]::SimpleName, $false)
    if ($publisher -cne 'Aurelio Avila') { throw "Unexpected publisher: $Path" }
    if (-not $signature.TimeStamperCertificate) { throw "Missing trusted timestamp: $Path" }

    # Validate every embedded signature and its timestamp under Windows trust
    # policy. /tw warns about absent timestamps; warnings are failures here.
    & $SignTool verify /pa /all /tw $Path
    if ($LASTEXITCODE -ne 0) { throw "SignTool verification failed or warned: $Path" }
    Write-Output "Verified publisher and timestamp: $Path"
}

if ($MyInvocation.InvocationName -ne '.') {
    $tool = Find-SignTool
    $files = @(Get-ChildItem -LiteralPath $Directory -Recurse -File |
        Where-Object { $_.Extension -in '.exe', '.msi' })
    if ($files.Count -eq 0) { throw 'No Windows executables or installers found.' }
    foreach ($file in $files) { Assert-PublisherSignature $file.FullName $tool }
}
