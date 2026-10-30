# Windows dev build to Build/MERIDIAN_<version>/. Owner: UNITY.
# Usage: tools/unity_build.ps1 [-Release]
param([switch]$Release)
. (Join-Path $PSScriptRoot 'unity_common.ps1')

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
try { Enter-HeavyJobLock 'unity_build' } catch { Write-Host "BLOCKED: $_"; exit 2 }
try {
    $unityArgs = @('-quit', '-executeMethod', 'Meridian.EditorTools.BuildTools.BuildFromCommandLine')
    if ($Release) { $unityArgs += '-meridianRelease' }
    $r = Invoke-UnityBatch $unityArgs "unity_build_$stamp.log"
} finally { Exit-HeavyJobLock }

$result = Select-String -Path $r.Log -Pattern '\[MERIDIAN\] BUILD (OK|FAILED).*' | Select-Object -Last 1
Write-Host "Log: $($r.Log)"
if ($result) { Write-Host $result.Line.Trim() }
Get-CompileErrors $r.Log | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" }
if ($r.ExitCode -ne 0 -or -not $result -or $result.Line -notmatch 'BUILD OK') { exit 1 }
exit 0
