# Deterministic trust-policy tests; no certificate, private key or signing session.
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/verify_authenticode.ps1" -Directory '.'

$script:toolCalls = 0
$script:toolExit = 0
function Test-SignTool {
    $script:toolCalls++
    if (($args[0..3] -join ' ') -ne 'verify /pa /all /tw') { throw 'Incorrect verification flags' }
    $global:LASTEXITCODE = $script:toolExit
}
function Get-AuthenticodeSignature { return $script:signature }
function Set-TestSignature($Status = 'Valid', $Publisher = 'Aurelio Avila', $Timestamp = $true, $Type = 'Authenticode') {
    $certificate = [pscustomobject]@{ Publisher = $Publisher }
    $certificate | Add-Member ScriptMethod GetNameInfo { param($type, $issuer) return $this.Publisher }
    $script:signature = [pscustomobject]@{
        Status = $Status
        SignatureType = $Type
        SignerCertificate = $certificate
        TimeStamperCertificate = $(if ($Timestamp) { [pscustomobject]@{} } else { $null })
    }
    $script:toolCalls = 0
    $script:toolExit = 0
}
function Assert-Rejected([string]$Expected) {
    try { Assert-PublisherSignature 'fixture.exe' 'Test-SignTool' }
    catch {
        if ($_.Exception.Message -notlike "*$Expected*") { throw }
        return
    }
    throw "Expected rejection: $Expected"
}

Set-TestSignature
Assert-PublisherSignature 'fixture.exe' 'Test-SignTool'
if ($script:toolCalls -ne 1) { throw 'Trust verification was bypassed' }
foreach ($status in 'NotSigned', 'HashMismatch', 'NotTrusted', 'UnknownError') {
    Set-TestSignature -Status $status
    Assert-Rejected 'Invalid or missing'
    if ($script:toolCalls -ne 0) { throw 'Invalid signature reached SignTool' }
}
Set-TestSignature -Publisher 'Another Publisher'
Assert-Rejected 'Unexpected publisher'
Set-TestSignature -Timestamp $false
Assert-Rejected 'Missing trusted timestamp'
Set-TestSignature -Type 'Catalog'
Assert-Rejected 'Invalid or missing'
foreach ($code in 1, 2) {
    Set-TestSignature
    $script:toolExit = $code
    Assert-Rejected 'failed or warned'
}
Write-Output '10 Authenticode policy cases passed (simulated trust results).'
# GitHub's PowerShell wrapper propagates LASTEXITCODE. The final negative test
# deliberately sets it to 2; do not leak that simulated result into the job.
$global:LASTEXITCODE = 0
