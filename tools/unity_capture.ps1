# Captures the side view on Earth at 1920x1080 to logs/capture_<name>.png. Owner: UNITY.
# Usage: tools/unity_capture.ps1 [-Name earth_surface]
param([string]$Name = 'earth_surface')
. (Join-Path $PSScriptRoot 'unity_common.ps1')

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$xml = Join-Path $LogDir "capture_$stamp.xml"
$png = Join-Path $LogDir "capture_$Name.png"
Remove-Item $png -Force -ErrorAction SilentlyContinue

try { Enter-HeavyJobLock "unity_capture $Name" } catch { Write-Host "BLOCKED: $_"; exit 2 }
try {
    $env:MERIDIAN_CAPTURE = $Name
    $unityArgs = @('-runTests', '-testPlatform', 'PlayMode', '-assemblyNames', 'MERIDIAN.Tests.Play',
        '-testFilter', 'Meridian.Tests.SceneCapture.CaptureEarthSurface', '-testResults', $xml)
    $r = Invoke-UnityBatch $unityArgs "unity_capture_$stamp.log" -Graphics
} finally {
    Remove-Item Env:\MERIDIAN_CAPTURE -ErrorAction SilentlyContinue
    Exit-HeavyJobLock
}

Write-Host "Log: $($r.Log)"
if ((Test-Path $xml) -and (Test-Path $png) -and ([xml](Get-Content $xml -Raw)).'test-run'.passed -eq '1') {
    Write-Host "CAPTURE OK: $png"; exit 0
}
Write-Host 'CAPTURE FAILED'
exit 1
