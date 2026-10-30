# Lit preview of one asset key to logs/preview_<key>.png (U-006). Owner: UNITY.
# Usage: tools/unity_art_preview.ps1 <category/name/variant>
param([Parameter(Mandatory)][string]$Key)
. (Join-Path $PSScriptRoot 'unity_common.ps1')

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
try { Enter-HeavyJobLock "unity_art_preview $Key" } catch { Write-Host "BLOCKED: $_"; exit 2 }
try {
    # Rendering needs a graphics device, so this job runs without -nographics.
    $r = Invoke-UnityBatch @('-executeMethod', 'Meridian.EditorTools.ArtPreview.RunFromCommandLine', '-artKey', $Key) "unity_preview_$stamp.log" -Graphics
} finally { Exit-HeavyJobLock }

$line = Select-String -Path $r.Log -Pattern '\[MERIDIAN\] PREVIEW (OK|FAILED).*' | Select-Object -Last 1
Write-Host "Log: $($r.Log)"
if ($line) { Write-Host $line.Line.Trim() }
if ($r.ExitCode -ne 0 -or -not $line -or $line.Line -notmatch 'PREVIEW OK') { exit 1 }
exit 0
