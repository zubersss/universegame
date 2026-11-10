# Smoke-runs the built player (U-017): screenshots menu / Earth day + night / biome border / Mars canyon storm / Saturn (U-044), then checks
# the player log for errors; U-132 adds the pause card, the settings paper and a title card per planet, the Mars hauler; U-142 adds Jupiter's floe / storm deck / Crush Line / Red Spot whale and the Venus + Jupiter cards; U-150 the climb boost and the sound barrier; U-163 Earth on the smooth ground: the camp, a hill, a scoop, a tunnel, a mound, a node full / harvested, a surveyed pocket / dug, the desert, taiga, tundra, the coast cliff, a forest valley, the sea; U-173 the Survey Archive and the Launch Complex as v3 sheets, a downhill walk strip of 4 frames; U-188 the digging game (smoke_47-63: the first dig with its card, the Surface Line, a room per tier, PACK FULL, the jetpack with a full pack, ladder, winch, grapple, Sell, the Skill Tree, a Mars T4 room, the minimap and the system map); U-194 the shovel (smoke_64 crafting with thruster_mk2, smoke_65 / 66 the held shovel mid-swing and its flick, smoke_67 the tool slot with The Beam); U-212 smoke_65 the shovel's contact drawing, smoke_66 its follow-through, smoke_68 the Beam mid-dig, each with the Rig's owner on (80 shots).
# Output: logs/smoke/*.png + coordination/reports/unity/smoke_<version>/. Owner: UNITY.
# Usage: tools/unity_smoke.ps1 [-Version 0.1.1] [-Dev]  (default: GameInfo.Version; U-143: the release player in Build/MERIDIAN_<v>/, -Dev the development one)
param([string]$Version = '', [switch]$Dev)
. (Join-Path $PSScriptRoot 'unity_common.ps1')

if (-not $Version) {
    $info = Get-Content (Join-Path $RepoRoot 'Assets\_Game\Code\Runtime\GameInfo.cs') -Raw
    if ($info -match 'Version = "([^"]+)"') { $Version = $Matches[1] } else { Write-Host 'SMOKE FAILED: no Version in GameInfo.cs'; exit 1 }
}
Write-Host "Smoke: build $Version"
$exe = Get-PlayerExe $Version -Dev:$Dev
if (-not (Test-Path $exe)) { Write-Host "SMOKE FAILED: no build at $exe (run tools/unity_profile.ps1 -Build -Release, or tools/unity_build.ps1 [-Release])"; exit 1 }
Write-Host "Smoke player: $exe"
# D-203: the smoke flies every transition and each one autosaves: the run saves into a folder of its own, never the owner's slot.
if (-not (Test-PlayerSaveRootSwitch $exe)) {
    Write-Host "SMOKE REFUSED (D-203): the player at $exe predates -meridianSaveRoot; driven by this script it would autosave into the owner's real save slot. Smoke a build made after 0.6.3."
    exit 1
}
$saveRoot = New-PlayerSaveRoot 'smoke_saves'
$out = Join-Path $LogDir 'smoke'
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
New-Item -ItemType Directory -Force $out | Out-Null
$playerLog = Join-Path $LogDir 'player_smoke.log'

try { Enter-HeavyJobLock 'unity_smoke' } catch { Write-Host "BLOCKED: $_"; exit 2 }
try {
    $playerArgs = @('-meridianSmoke', $out, '-meridianSaveRoot', "`"$saveRoot`"", '-screen-width', '1920', '-screen-height', '1080', '-screen-fullscreen', '0', '-logFile', $playerLog)
    $p = Start-Process -FilePath $exe -ArgumentList $playerArgs -PassThru
    $null = $p.Handle
    if (-not $p.WaitForExit(480000)) { Stop-Process -Id $p.Id -Force; Write-Host 'SMOKE FAILED: player did not quit within 480 s'; exit 1 } # U-212: 80 shots, ~390 s
} finally { Exit-HeavyJobLock }

$done = Test-Path (Join-Path $out 'smoke_done.txt')
$shots = @(Get-ChildItem $out -Filter 'smoke_*.png')
$errors = @(Select-String -Path $playerLog -Pattern 'Exception|\[Error\]|error CS|NullReference' -ErrorAction SilentlyContinue |
    Where-Object { $_.Line -notmatch 'Crash!!!|UnityShaderCompiler' })
$flavour = if ($done) { ((Get-Content (Join-Path $out 'smoke_done.txt') -Raw).Trim() -split ' ')[2] } else { '?' }   # U-143: release | development
$tookRoot = Test-PlayerTookSaveRoot $playerLog   # D-203
Write-Host "player exit $($p.ExitCode) | done marker $done ($flavour) | screenshots $($shots.Count) | error lines $($errors.Count) | saves in $saveRoot : $tookRoot"
if (-not $tookRoot) { Write-Host "SMOKE FAILED (D-203): the player's log has no '[MERIDIAN] saves go to' line: it did not take -meridianSaveRoot and may have written the owner's save slot"; exit 1 }
$errors | Select-Object -First 10 | ForEach-Object { Write-Host "  $($_.Line.Trim())" }

$report = Join-Path $RepoRoot ("coordination\reports\unity\smoke_" + $Version) # U-132: one folder per build (was per date)
New-Item -ItemType Directory -Force $report | Out-Null
$shots | ForEach-Object { Copy-Item $_.FullName (Join-Path $report $_.Name) -Force }
if ($done -and $shots.Count -eq 80 -and $errors.Count -eq 0) { Write-Host "SMOKE OK: $report"; exit 0 }
Write-Host 'SMOKE FAILED'
exit 1
