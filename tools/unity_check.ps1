# One hand-off check under a single HeavyJobLock (U-043, D-037): compile (optionally running an
# -ExecuteMethod such as scene authoring), then EditMode, then PlayMode, without giving the lock up
# in between. Use with unity_when_clear.ps1 to wait for the turn. Owner: UNITY.
# Usage: tools/unity_check.ps1 [-ExecuteMethod Meridian.EditorTools.SceneAuthoring.Run] [-PlayFilter "A|B"] [-SkipEditMode] [-SkipPlayMode]
param([string]$ExecuteMethod = '', [string]$PlayFilter = '', [switch]$SkipEditMode, [switch]$SkipPlayMode)
. (Join-Path $PSScriptRoot 'unity_common.ps1')

try { Enter-HeavyJobLock 'unity_check (compile + EditMode + PlayMode)' } catch { Write-Host "BLOCKED: $_"; exit 2 }
$started = Get-Date
$env:MERIDIAN_LOCK_HELD = '1'
$code = 0
try {
    Write-Host '== compile'
    & (Join-Path $PSScriptRoot 'unity_compile.ps1') -ExecuteMethod $ExecuteMethod
    $code = $LASTEXITCODE
    if ($code -eq 0 -and -not $SkipEditMode) {
        Write-Host '== EditMode'
        & (Join-Path $PSScriptRoot 'unity_test.ps1') -Mode EditMode
        $code = $LASTEXITCODE
    }
    if ($code -eq 0 -and -not $SkipPlayMode) {
        Write-Host '== PlayMode'
        $p = @{ Mode = 'PlayMode' }
        if ($PlayFilter) { $p.Filter = $PlayFilter }
        & (Join-Path $PSScriptRoot 'unity_test.ps1') @p
        $code = $LASTEXITCODE
    }
} finally {
    Remove-Item Env:\MERIDIAN_LOCK_HELD -ErrorAction SilentlyContinue
    Exit-HeavyJobLock
}
Write-Host ("CHECK {0} in {1:F1} min (one lock)" -f ($(if ($code -eq 0) { 'OK' } else { 'FAILED' })), ((Get-Date) - $started).TotalMinutes)
exit $code
