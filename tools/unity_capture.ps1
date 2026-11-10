# Captures the side view on Earth at 1920x1080 to logs/capture_<name>.png. Owner: UNITY.
# Usage: tools/unity_capture.ps1 [-Name earth_surface] [-Test CaptureEarthSurface|CaptureSpace|CaptureBackdrop]
param([string]$Name = 'earth_surface', [ValidateSet('CaptureEarthSurface', 'CaptureSpace', 'CaptureBackdrop', 'CaptureDayNight', 'CaptureDustStorm', 'CaptureCreatures', 'CaptureSurveyorStates', 'CaptureFx', 'CaptureSpaceArt', 'CaptureSpawnCamp', 'CaptureBiomes', 'CaptureMarsLandforms', 'CaptureBiomeBorder', 'CaptureRigModules', 'CaptureMercury', 'CaptureVenus', 'CaptureInnerCreatures', 'CaptureBases', 'CaptureDepthBands', 'CaptureStageLayers', 'CaptureC0Earth', 'CaptureIrisStrip', 'CaptureC0Strip', 'CaptureC0Set', 'CaptureU107Ship', 'CaptureV41Set', 'CaptureU103Ship', 'CaptureU109Climb', 'CaptureU104Hud', 'CaptureC1FlightStrip', 'CaptureU114Creatures', 'CaptureU110Scenes', 'CaptureU116Sun', 'CaptureU119Maw', 'CaptureU122Pool', 'CaptureU118Mars', 'CaptureU128Shore', 'CaptureU123Mercury', 'CaptureU124Ui', 'CaptureU125Venus', 'CaptureU127Jupiter', 'CaptureU148Climb', 'CaptureU150Boom', 'CaptureU156Ground', 'CaptureU157Brush', 'CaptureU158Finds', 'CaptureU159Mars', 'CaptureU174DigRun', 'CaptureU175Tree', 'CaptureU184Map', 'CaptureU182Tiers', 'CaptureU182Perf', 'CaptureU186Ground', 'CaptureU183Looks', 'CaptureU176Ascent', 'CaptureU178Expedition', 'CaptureU190CampShaft', 'CaptureU185Hints', 'CaptureU181Grain', 'CaptureU180Pois', 'CaptureU171Sea', 'CaptureU193Shovel', 'CaptureU195DigFeel', 'CaptureU200Walls', 'CaptureU196Holes', 'CaptureU204Panels', 'CaptureU205', 'CaptureU207Backdrop', 'CaptureU207Sets', 'CaptureB242Walls', 'CaptureU192', 'CaptureU209Strips')][string]$Test = 'CaptureEarthSurface', [switch]$NoPicture, [switch]$D3D11)
# -NoPicture: the test measures and saves no picture (CaptureU182Perf): a passed test alone is OK (LEAD 17:5x: it read as a failure).
# D-194 (LEAD 11-09 23:5x): every capture runs with the Editor forced to Direct3D 11, the built player's API. Left automatic the Editor
#   took Direct3D 12 and the player 11; on this Intel UHD a grainy BC7 texture costs several times more to draw on 12, so a frame
#   figure read on 12 said nothing of the player (U-207's trial). -D3D11 is kept as a no-op for older calls.
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
    $unityArgs = @('-force-d3d11') + $unityArgs   # D-194: the player's API
    $r = Invoke-UnityBatch $unityArgs "unity_capture_$stamp.log" -Graphics
} finally {
    Remove-Item Env:\MERIDIAN_CAPTURE -ErrorAction SilentlyContinue
    Exit-HeavyJobLock
}

Write-Host "Log: $($r.Log)"
$pictures = @(Get-ChildItem $LogDir -Filter "capture_$Name*.png").Count
if ((Test-Path $xml) -and ($NoPicture -or $pictures -gt 0) -and ([xml](Get-Content $xml -Raw)).'test-run'.passed -eq '1') {
    if ($pictures -gt 0) { Write-Host "CAPTURE OK: $png" } else { Write-Host "CAPTURE OK (no picture expected): $xml" }
    exit 0
}
Write-Host 'CAPTURE FAILED'
exit 1
