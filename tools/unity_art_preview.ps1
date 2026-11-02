# Lit preview of one asset key to logs/preview_<key>.png (U-006). Owner: UNITY.
# Usage: tools/unity_art_preview.ps1 <category/name/variant>[,<key>...]   (model keys in a list render in one Unity session)
# Runs the ArtPreviewCapture PlayMode test (Light2D needs the player loop) with graphics on.
param([Parameter(Mandatory)][string]$Key)
. (Join-Path $PSScriptRoot 'unity_common.ps1')

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$xml = Join-Path $LogDir "preview_$stamp.xml"
$pngs = @($Key -split ',' | ForEach-Object { Join-Path $LogDir ("preview_" + ($_.Trim() -replace '/', '_') + ".png") })
$pngs | ForEach-Object { Remove-Item $_ -Force -ErrorAction SilentlyContinue }

try { Enter-HeavyJobLock "unity_art_preview $Key" } catch { Write-Host "BLOCKED: $_"; exit 2 }
try {
    $env:MERIDIAN_PREVIEW_KEY = $Key
    $unityArgs = @('-runTests', '-testPlatform', 'PlayMode', '-assemblyNames', 'MERIDIAN.Tests.Play',
        '-testFilter', 'Meridian.Tests.ArtPreviewCapture.RenderPreview', '-testResults', $xml)
    $r = Invoke-UnityBatch $unityArgs "unity_preview_$stamp.log" -Graphics
} finally {
    Remove-Item Env:\MERIDIAN_PREVIEW_KEY -ErrorAction SilentlyContinue
    Exit-HeavyJobLock
}

Write-Host "Log: $($r.Log)"
if ((Test-Path $xml) -and -not ($pngs | Where-Object { -not (Test-Path $_) })) {
    [xml]$doc = Get-Content $xml -Raw
    if ($doc.'test-run'.passed -eq '1') { $pngs | ForEach-Object { Write-Host "PREVIEW OK: $_" }; exit 0 }
}
$fail = if (Test-Path $xml) { ([xml](Get-Content $xml -Raw)).SelectSingleNode("//test-case/failure/message").InnerText } else { 'no results file' }
Write-Host "PREVIEW FAILED: $fail"
exit 1
