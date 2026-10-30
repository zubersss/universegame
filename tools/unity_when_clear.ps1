# Retries a tools/unity_*.ps1 job while UNITY must wait (exit 2: another role's lock, a waiting
# role's turn, or low memory; D-026). want_unity.lock stays while waiting. Owner: UNITY.
# Usage: tools/unity_when_clear.ps1 unity_test.ps1 -Params @{ Mode = 'PlayMode' }   (gives up after 40 min)
param([Parameter(Mandatory)][string]$Script, [hashtable]$Params = @{})
. (Join-Path $PSScriptRoot 'unity_common.ps1')
$deadline = (Get-Date).AddMinutes(40)
while ($true) {
    & (Join-Path $PSScriptRoot $Script) @Params
    $code = $LASTEXITCODE
    if ($code -ne 2) { exit $code }
    if ((Get-Date) -gt $deadline) { Clear-HeavyJobWant; Write-Host 'GAVE UP: lock never cleared in 40 min'; exit 2 }
    Start-Sleep -Seconds 30
}
