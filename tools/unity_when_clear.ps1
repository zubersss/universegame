# Retries a tools/unity_*.ps1 job while HeavyJobLock is held by another role (exit 2). Owner: UNITY.
# Usage: tools/unity_when_clear.ps1 unity_test.ps1 -Params @{ Mode = 'PlayMode' }   (gives up after 40 min)
param([Parameter(Mandatory)][string]$Script, [hashtable]$Params = @{})
$deadline = (Get-Date).AddMinutes(40)
while ($true) {
    & (Join-Path $PSScriptRoot $Script) @Params
    $code = $LASTEXITCODE
    if ($code -ne 2) { exit $code }
    if ((Get-Date) -gt $deadline) { Write-Host 'GAVE UP: lock never cleared in 40 min'; exit 2 }
    Start-Sleep -Seconds 20
}
