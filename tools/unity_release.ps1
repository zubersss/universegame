# One release check under a single HeavyJobLock (U-077, D-037): compile (with graphics, so texture
# reimports run), EditMode, the BudgetGate profile with the development build and its memory probe
# (unity_profile.ps1 -Build), then the player smoke set (unity_smoke.ps1), without giving the lock up
# in between. Use with unity_when_clear.ps1 to wait for the turn. Owner: UNITY.
# Usage: tools/unity_release.ps1 [-SkipEditMode] [-PlayFilter "A|B" | -FullPlayMode] [-SkipProfile] [-SkipSmoke]
param([switch]$SkipEditMode, [string]$PlayFilter = '', [switch]$FullPlayMode, [switch]$SkipProfile, [switch]$SkipSmoke)
. (Join-Path $PSScriptRoot 'unity_common.ps1')

try { Enter-HeavyJobLock 'unity_release (compile + EditMode + profile -Build + smoke)' } catch { Write-Host "BLOCKED: $_"; exit 2 }
$started = Get-Date
$env:MERIDIAN_LOCK_HELD = '1'
$code = 0
try {
    Write-Host '== compile (graphics: texture reimports)'
    & (Join-Path $PSScriptRoot 'unity_compile.ps1') -Graphics
    $code = $LASTEXITCODE
    if ($code -eq 0 -and -not $SkipEditMode) {
        Write-Host '== EditMode'
        & (Join-Path $PSScriptRoot 'unity_test.ps1') -Mode EditMode
        $code = $LASTEXITCODE
    }
    if ($code -eq 0 -and $FullPlayMode) {
        Write-Host '== PlayMode (full suite, U-092)'
        & (Join-Path $PSScriptRoot 'unity_test.ps1') -Mode PlayMode
        $code = $LASTEXITCODE
    }
    elseif ($code -eq 0 -and $PlayFilter) {
        Write-Host "== PlayMode ($PlayFilter)"
        & (Join-Path $PSScriptRoot 'unity_test.ps1') -Mode PlayMode -Filter $PlayFilter
        $code = $LASTEXITCODE
    }
    $profileCode = 0
    if ($code -eq 0 -and -not $SkipProfile) {
        Write-Host '== profile + dev build + (after a green probe) the release build (U-143)'
        & (Join-Path $PSScriptRoot 'unity_profile.ps1') -Build -Release
        $profileCode = $LASTEXITCODE   # a red BudgetGate row still leaves a build to smoke; reported below
    }
    $version = Get-GameVersion
    if ($code -eq 0 -and -not $SkipSmoke -and (Test-Path (Get-PlayerExe $version))) {
        Write-Host '== smoke (the release player, U-143)'
        & (Join-Path $PSScriptRoot 'unity_smoke.ps1')
        $code = $LASTEXITCODE
    }
} finally {
    Remove-Item Env:\MERIDIAN_LOCK_HELD -ErrorAction SilentlyContinue
    Exit-HeavyJobLock
}
if ($code -eq 0 -and $profileCode -ne 0) { $code = $profileCode }
Write-Host ("RELEASE {0} in {1:F1} min (one lock; profile exit $profileCode)" -f ($(if ($code -eq 0) { 'OK' } else { 'FAILED' })), ((Get-Date) - $started).TotalMinutes)
exit $code
