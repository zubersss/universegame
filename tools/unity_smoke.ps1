# Smoke-runs the built player (U-017): screenshots menu / Earth HUD / ship HUD / space, then checks
# the player log for errors. Output: logs/smoke/*.png + coordination/reports/unity/smoke_<date>/. Owner: UNITY.
# Usage: tools/unity_smoke.ps1 [-Version 0.1.1]  (default: GameInfo.Version, the build unity_build.ps1 makes)
param([string]$Version = '')
. (Join-Path $PSScriptRoot 'unity_common.ps1')

if (-not $Version) {
    $info = Get-Content (Join-Path $RepoRoot 'Assets\_Game\Code\Runtime\GameInfo.cs') -Raw
    if ($info -match 'Version = "([^"]+)"') { $Version = $Matches[1] } else { Write-Host 'SMOKE FAILED: no Version in GameInfo.cs'; exit 1 }
}
Write-Host "Smoke: build $Version"
$exe = Join-Path $RepoRoot "Build\MERIDIAN_$Version\MERIDIAN.exe"
if (-not (Test-Path $exe)) { Write-Host "SMOKE FAILED: no build at $exe (run tools/unity_build.ps1)"; exit 1 }
$out = Join-Path $LogDir 'smoke'
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
New-Item -ItemType Directory -Force $out | Out-Null
$playerLog = Join-Path $LogDir 'player_smoke.log'

try { Enter-HeavyJobLock 'unity_smoke' } catch { Write-Host "BLOCKED: $_"; exit 2 }
try {
    $playerArgs = @('-meridianSmoke', $out, '-screen-width', '1920', '-screen-height', '1080', '-screen-fullscreen', '0', '-logFile', $playerLog)
    $p = Start-Process -FilePath $exe -ArgumentList $playerArgs -PassThru
    $null = $p.Handle
    if (-not $p.WaitForExit(120000)) { Stop-Process -Id $p.Id -Force; Write-Host 'SMOKE FAILED: player did not quit within 120 s'; exit 1 }
} finally { Exit-HeavyJobLock }

$done = Test-Path (Join-Path $out 'smoke_done.txt')
$shots = @(Get-ChildItem $out -Filter 'smoke_*.png')
$errors = @(Select-String -Path $playerLog -Pattern 'Exception|\[Error\]|error CS|NullReference' -ErrorAction SilentlyContinue |
    Where-Object { $_.Line -notmatch 'Crash!!!|UnityShaderCompiler' })
Write-Host "player exit $($p.ExitCode) | done marker $done | screenshots $($shots.Count) | error lines $($errors.Count)"
$errors | Select-Object -First 10 | ForEach-Object { Write-Host "  $($_.Line.Trim())" }

$report = Join-Path $RepoRoot ("coordination\reports\unity\smoke_" + (Get-Date -Format 'yyyy-MM-dd'))
New-Item -ItemType Directory -Force $report | Out-Null
$shots | ForEach-Object { Copy-Item $_.FullName (Join-Path $report $_.Name) -Force }
if ($done -and $shots.Count -eq 4 -and $errors.Count -eq 0) { Write-Host "SMOKE OK: $report"; exit 0 }
Write-Host 'SMOKE FAILED'
exit 1
