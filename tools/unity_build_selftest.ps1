# Self-test of the U-143 build wiring, without the Editor or a player: every tools/unity_*.ps1 parses; the probe runs on the
# development player in Build/MERIDIAN_<v>_dev/, the smoke on the release player in Build/MERIDIAN_<v>/; unity_release asks
# unity_profile for the release build after a green probe; BuildTools writes the same folders. Owner: UNITY.
# Usage: tools/unity_build_selftest.ps1   (exit 0 = all checks pass)
. (Join-Path $PSScriptRoot 'unity_common.ps1')
$ErrorActionPreference = 'Stop'
$fails = 0
function Check([bool]$ok, [string]$what) {
    if ($ok) { Write-Host "  ok    $what" } else { Write-Host "  FAIL  $what"; $script:fails++ }
}

Write-Host '== every wrapper parses'
foreach ($f in Get-ChildItem $PSScriptRoot -Filter 'unity_*.ps1') {
    $tokens = $null; $errs = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$tokens, [ref]$errs)
    Check ($errs.Count -eq 0) ("{0} parses{1}" -f $f.Name, $(if ($errs.Count) { ': ' + $errs[0].Message + ' (line ' + $errs[0].Extent.StartLineNumber + ')' } else { '' }))
}

Write-Host '== the player folders'
$v = Get-GameVersion
Check ($v -match '^\d+\.\d+\.\d+$') "GameInfo.Version reads ($v)"
Check ((Get-PlayerExe '9.9.9') -eq (Join-Path $RepoRoot 'Build\MERIDIAN_9.9.9\MERIDIAN.exe')) 'the release player: Build\MERIDIAN_<v>\'
Check ((Get-PlayerExe '9.9.9' -Dev) -eq (Join-Path $RepoRoot 'Build\MERIDIAN_9.9.9_dev\MERIDIAN.exe')) 'the development player: Build\MERIDIAN_<v>_dev\'
$tools = Get-Content (Join-Path $RepoRoot 'Assets\_Game\Code\Editor\BuildTools.cs') -Raw
Check ($tools -match 'DevSuffix = "_dev"') 'BuildTools.DevSuffix matches'
Check ($tools -match 'locationPathName = \$"\{OutputFolderFor\(release\)\}/') 'BuildTools writes by the build kind'
Check ($tools -match 'options = release \? BuildOptions\.None : BuildOptions\.Development') 'the release build drops the Development flag (no watermark)'

Write-Host '== the wiring'
$profile = Get-Content (Join-Path $PSScriptRoot 'unity_profile.ps1') -Raw
$release = Get-Content (Join-Path $PSScriptRoot 'unity_release.ps1') -Raw
$smoke = Get-Content (Join-Path $PSScriptRoot 'unity_smoke.ps1') -Raw
Check ($profile -match '\$exe = Get-PlayerExe \$version -Dev') 'the probe runs on the development player'
Check ($profile -match "'-meridianRelease'") 'unity_profile -Release builds with -meridianRelease'
Check ($profile -match "Write-Host 'BUDGETGATE GREEN'; exit \(Complete-Release\)") 'the release build follows a green BudgetGate + probe'
Check ($profile -match "Write-Host 'BUILD MEMORY GREEN'; exit \(Complete-Release\)") 'and a green probe with -SkipGate (a D-152 re-probe)'
Check (-not ($profile -match "BUILD MEMORY RED'; exit \(Complete")) 'never after a red probe'
Check ($release -match "unity_profile\.ps1'\) -Build -Release") 'unity_release asks for both builds in one call'
Check ($release -match 'Test-Path \(Get-PlayerExe \$version\)') 'unity_release smokes only when the release player exists'
Check ($smoke -match '\$exe = Get-PlayerExe \$Version -Dev:\$Dev') 'the smoke runs the release player unless -Dev'
$bs = Get-Content (Join-Path $RepoRoot 'Assets\_Game\Code\Runtime\Core\BuildSmoke.cs') -Raw
Check ($bs -match 'Debug\.isDebugBuild \? "development" : "release"') 'the smoke marker names the player kind'

if ($fails -gt 0) { Write-Host "BUILD SELFTEST FAILED ($fails)"; exit 1 }
Write-Host 'BUILD SELFTEST OK'
exit 0
