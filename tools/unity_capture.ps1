# Captures the side view on Earth at 1920x1080 to logs/capture_<name>.png. Owner: UNITY.
# Usage: tools/unity_capture.ps1 [-Name earth_surface] [-Test CaptureEarthSurface|CaptureSpace|CaptureBackdrop]
param([string]$Name = 'earth_surface', [ValidateSet('CaptureEarthSurface', 'CaptureSpace', 'CaptureBackdrop', 'CaptureDayNight', 'CaptureDustStorm', 'CaptureCreatures', 'CaptureSurveyorStates', 'CaptureFx', 'CaptureSpaceArt', 'CaptureSpawnCamp', 'CaptureBiomes', 'CaptureMarsLandforms')][string]$Test = 'CaptureEarthSurface')
. (Join-Path $PSScriptRoot 'unity_common.ps1')

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$xml = Join-Path $LogDir "capture_$stamp.xml"
$png = Join-Path $LogDir "capture_$Name.png"
Get-ChildItem $LogDir -Filter "capture_$Name*.png" | Remove-Item -Force -ErrorAction SilentlyContinue

try { Enter-HeavyJobLock "unity_capture $Name" } catch { Write-Host "BLOCKED: $_"; exit 2 }
try {
    $env:MERIDIAN_CAPTURE = $Name
    $unityArgs = @('-runTests', '-testPlatform', 'PlayMode', '-assemblyNames', 'MERIDIAN.Tests.Play',
        '-testFilter', "Meridian.Tests.SceneCapture.$Test", '-testResults', $xml)
    $r = Invoke-UnityBatch $unityArgs "unity_capture_$stamp.log" -Graphics
} finally {
    Remove-Item Env:\MERIDIAN_CAPTURE -ErrorAction SilentlyContinue
    Exit-HeavyJobLock
}

Write-Host "Log: $($r.Log)"
if ((Test-Path $xml) -and (@(Get-ChildItem $LogDir -Filter "capture_$Name*.png").Count -gt 0) -and ([xml](Get-Content $xml -Raw)).'test-run'.passed -eq '1') {
    Write-Host "CAPTURE OK: $png"; exit 0
}
Write-Host 'CAPTURE FAILED'
exit 1
