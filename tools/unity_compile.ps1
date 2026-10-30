# Batch compile gate: exits 0 only with zero 'error CS'. Owner: UNITY.
# Usage: tools/unity_compile.ps1 [-ExecuteMethod Namespace.Class.Method]
param([string]$ExecuteMethod = '')
. (Join-Path $PSScriptRoot 'unity_common.ps1')

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
try { Enter-HeavyJobLock 'unity_compile' } catch { Write-Host "BLOCKED: $_"; exit 2 }
try {
    $unityArgs = @('-quit')
    if ($ExecuteMethod) { $unityArgs += @('-executeMethod', $ExecuteMethod) }
    $r = Invoke-UnityBatch $unityArgs "unity_compile_$stamp.log"
} finally { Exit-HeavyJobLock }

$errors = Get-CompileErrors $r.Log
$warnings = Get-CompileWarnings $r.Log
Write-Host "Log: $($r.Log)"
Write-Host "Unity exit code: $($r.ExitCode) | error CS: $($errors.Count) | warning CS (_Game): $($warnings.Count)"
$errors | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" }
$warnings | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" }
if ($errors.Count -gt 0 -or $r.ExitCode -ne 0) { exit 1 }
exit 0
