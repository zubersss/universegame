# BudgetGate profile run (U-014): runs BudgetGateTests with graphics and writes
# coordination/reports/unity/perf_<date>.md with every Bible section 11.1 row. Owner: UNITY.
# -Build (U-041, D-036): also builds the development player and runs its memory probe
# (nine legs: Earth, Space, Mars, Space, Mercury, Space, Venus, Space, Earth again; U-091) under the same lock, adding "dev build" rows to the report.
# -Probe (U-086): runs the probe on the player already in Build/ without rebuilding it.
# The Editor's memory rows stay as an upper bound. Limits are Bible 11.1 v4 (D-089).
# Usage: tools/unity_profile.ps1 [-Build | -Probe] [-SkipGate]
param([switch]$Build, [switch]$Probe, [switch]$SkipGate)
. (Join-Path $PSScriptRoot 'unity_common.ps1')

$date = Get-Date -Format 'yyyy-MM-dd'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$xml = Join-Path $LogDir "profile_$stamp.xml"
$report = Join-Path $RepoRoot "coordination\reports\unity\perf_$date.md"
$probeOut = Join-Path $LogDir "memory_probe_$stamp.jsonl"
$buildOk = $true
$runProbe = $Build -or $Probe

$jobName = 'unity_profile' + $(if ($Build) { ' + dev build memory probe' } elseif ($Probe) { ' + memory probe (existing build)' } else { '' })
try { Enter-HeavyJobLock $jobName } catch { Write-Host "BLOCKED: $_"; exit 2 }
try {
    if (-not $SkipGate) {
        $env:MERIDIAN_PROFILE_REPORT = $report
        $env:MERIDIAN_FREE_RAM_MB = [int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024)  # D-083: free RAM before the Editor launches
        $unityArgs = @('-runTests', '-testPlatform', 'PlayMode', '-assemblyNames', 'MERIDIAN.Tests.Play',
            '-testFilter', 'Meridian.Tests.BudgetGateTests', '-testResults', $xml)
        $r = Invoke-UnityBatch $unityArgs "unity_profile_$stamp.log" -Graphics
        Remove-Item Env:\MERIDIAN_PROFILE_REPORT -ErrorAction SilentlyContinue
        Remove-Item Env:\MERIDIAN_FREE_RAM_MB -ErrorAction SilentlyContinue
        Write-Host "Log: $($r.Log)"
    }
    if ($Build) {
        $b = Invoke-UnityBatch @('-quit', '-executeMethod', 'Meridian.EditorTools.BuildTools.BuildFromCommandLine') "unity_build_$stamp.log"
        $line = Select-String -Path $b.Log -Pattern '\[MERIDIAN\] BUILD (OK|FAILED).*' | Select-Object -Last 1
        Write-Host "Build log: $($b.Log)"
        if ($line) { Write-Host $line.Line.Trim() }
        if ($b.ExitCode -ne 0 -or -not $line -or $line.Line -notmatch 'BUILD OK') { $buildOk = $false }
    }
    if ($runProbe -and $buildOk) {
        # D-080: the built game runs only after the Editor batch has exited (Invoke-UnityBatch waits for it).
        $version = (Select-String -Path (Join-Path $RepoRoot 'Assets\_Game\Code\Runtime\GameInfo.cs') -Pattern 'Version = "([^"]+)"').Matches[0].Groups[1].Value
        $exe = Join-Path $RepoRoot "Build\MERIDIAN_$version\MERIDIAN.exe"
        if (-not (Test-Path $exe)) { Write-Host "PROBE: no player at $exe (build first)"; $buildOk = $false }
        else {
            $playerLog = Join-Path $LogDir "memory_probe_$stamp.log"
            $p = Start-Process -FilePath $exe -PassThru -ArgumentList @('-meridianMemoryProbe', "`"$probeOut`"",
                '-screen-fullscreen', '0', '-screen-width', '1920', '-screen-height', '1080', '-logFile', "`"$playerLog`"")
            if (-not $p.WaitForExit(480000)) { Stop-Process -Id $p.Id -Force; Write-Host 'PROBE TIMED OUT (8 min)'; $buildOk = $false }
            Write-Host "Player log: $playerLog"
        }
    }
} finally {
    Remove-Item Env:\MERIDIAN_PROFILE_REPORT -ErrorAction SilentlyContinue
    Exit-HeavyJobLock
}

# ---- dev-build rows (U-041; v4 limits U-091, D-089) ----
$memRed = $false
# Report symbols as code points (tools/*.ps1 stay ASCII).
$le = [char]0x2264; $ar = [char]0x2192; $times = [char]0x00D7; $sec = [char]0x00A7; $dot = [char]0x00B7
$limit = "< 2.0 GB working set (warn 1.7), $le 512 MB textures, $le 150 MB audio"
if ($runProbe) {
    $rows = @('', '## Memory in the development player (U-041, D-036; limits v4, D-089)', '',
        "The route Earth $ar launch $ar Space $ar entry $ar Earth (warm, D-114) $ar launch $ar Space $ar entry $ar Mars $ar launch $ar Space $ar entry $ar Mercury $ar launch $ar Space $ar entry $ar Venus $ar launch $ar Space $ar entry $ar Earth again (nine legs, real launches and entries, U-091) in Build/MERIDIAN_<version>/MERIDIAN.exe (development build), 1920${times}1080 windowed; counters read after GC + UnloadUnusedAssets and 120 frames per leg. Working set and private commit from the OS (ProcessMemory); the Editor rows above stay as an upper bound. Meshes are printed, not judged.", '',
        "| Row | Budget (${sec}11.1 v4) | Measured | Status |", '|---|---|---|---|')
    $legs = @()
    if ($buildOk -and (Test-Path $probeOut)) { $legs = @(Get-Content $probeOut | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json } | Where-Object { $null -ne $_.systemMB }) }
    if ($legs.Count -eq 0) { $rows += "| Memory $dot dev build | $limit | no probe result (build or probe failed) | red |"; $memRed = $true }
    $byLeg = @{}
    foreach ($l in $legs) {
        if ($l.error) { $rows += "| Memory $dot dev build | | probe error: $($l.error) | red |"; $memRed = $true; continue }
        $byLeg[[string]$l.leg] = $l
        $ws = if ($l.workingSetMB -gt 0) { [long]$l.workingSetMB } else { [long]$l.systemMB }
        $tex = if ($null -ne $l.textureMB) { [long]$l.textureMB } else { -1 }
        $ok = ($ws -ge 0) -and ($ws -lt 2048) -and ($tex -ge 0) -and ($tex -le 512) -and ($l.audioMB -le 150)
        if (-not $ok) { $memRed = $true }
        $status = if (-not $ok) { 'red' } elseif ($ws -ge 1741) { 'green (above the 1.7 GB warning line)' } else { 'green' }
        $wsText = if ($l.workingSetMB -gt 0) { "working set $($l.workingSetMB) MB, system $($l.systemMB) MB" } else { "system $($l.systemMB) MB (working set n/a: judged on system memory)" }
        $privText = if ($null -ne $l.privateMB -and $l.privateMB -ge 0) { ", private $($l.privateMB) MB" } else { '' }
        $meshText = if ($null -ne $l.meshMB -and $l.meshMB -ge 0) { ", meshes $($l.meshMB) MB" } else { '' }
        $texText = if ($tex -ge 0) { "textures $tex MB" } else { 'textures n/a (red)' }
        $rows += "| Memory $dot $($l.leg) (dev build) | $limit | $wsText$privText, $texText$meshText, audio $($l.audioMB) MB | $status |"
        if ($l.prevGroup) {
            $resOk = ([int]$l.prevHandles -eq 0)
            $ownText = ''
            if ($l.ownGroup) {
                $own = if ($null -ne $l.ownHandles) { [int]$l.ownHandles } else { -1 }
                if ($own -gt 0) { $ownText = "; own $($l.ownGroup) handles $own" } else { $ownText = "; own $($l.ownGroup) handles $own (nothing tracked)"; $resOk = $false }
            }
            if (-not $resOk) { $memRed = $true }
            $rows += "| Residency $dot $($l.leg) (dev build) | previous planet released within 5 s; the planet's own handles tracked (v4) | $($l.prevGroup) handles $($l.prevHandles) after $($l.prevWait) s (holders: $($l.holders))$ownText; resident: $($l.resident) | $(if ($resOk) { 'green' } else { 'red' }) |"
        }
        if ($l.ownGroup) {
            if ($null -eq $l.loadSec) { $rows += "| Planet load $dot $($l.leg) (dev build) | $le 5 s (D-089) | old player: rebuild (no loadSec) | red |"; $memRed = $true }
            elseif ([double]$l.loadSec -ge 0) {
                $lok = ([double]$l.loadSec -le 5)
                if (-not $lok) { $memRed = $true }
                $rows += "| Planet load $dot $($l.leg) (dev build) | $le 5 s: entry start $ar terrain settled + no pending load (D-089) | $($l.loadSec) s ($($l.breakdown)) | $(if ($lok) { 'green' } else { 'red' }) |"
            }
            if ($null -ne $l.packedSprites -and [int]$l.packedSprites -eq 0) { $rows += "| Sprite atlases $dot $($l.leg) (dev build) | $le 8 per planet (D-089) | n/a: sprite packing is off (0 packed sprites) | n/a (LEAD) |" }
            elseif ($null -ne $l.atlases) { $atl = [int]$l.atlases; $aok = ($atl -le 8); if (-not $aok) { $memRed = $true }; $rows += "| Sprite atlases $dot $($l.leg) (dev build) | $le 8 per planet (D-089) | $atl loaded | $(if ($aok) { 'green' } else { 'red' }) |" }
        }
        if ($null -ne $l.transitionSec -and [double]$l.transitionSec -ge 0) {
            $tok = ([double]$l.transitionSec -le 1.5)
            if (-not $tok) { $memRed = $true }
            $rows += "| Transition $dot $($l.leg) (dev build) | $le 1.5 s (D-089) | $($l.transitionSec) s, worst iris-in frame $($l.irisInWorstMs) ms | $(if ($tok) { 'green' } else { 'red' }) |"
        }
        if ($null -ne $l.bundles) {
            $planetBundles = @([string]$l.bundles -split ', ' | Where-Object { $_ -like 'planet_*' -and $_ -notlike 'planet_space*' -and $_ -notlike 'planet_warden*' -and $_ -notlike 'planet_waystation*' -and $_ -notlike 'planet_rig*' })
            $foreign = @($planetBundles | Where-Object { (-not $l.ownGroup) -or (($_ -ne $l.ownGroup) -and ($_ -notlike "$($l.ownGroup)_*")) })
            $bok = ($foreign.Count -eq 0)
            if (-not $bok) { $memRed = $true }
            $rows += "| Bundles $dot $($l.leg) (dev build) | only the leg's own planet among the loaded planet bundles (none in Space) | $($l.bundles) | $(if ($bok) { 'green' } else { 'red' }) |"
        }
        if ($null -ne $l.nonStreamingMB) {
            $sum = [long]$l.nonStreamingMB + [long]$l.desiredMB
            $warn = if ($sum -gt [long]$l.mipBudgetMB) { ' (warn: streamed model maps reduced)' } else { '' }
            $rows += "| Mip streaming $dot $($l.leg) (dev build) | info | non-streaming $($l.nonStreamingMB) MB + desired $($l.desiredMB) MB vs $($l.mipBudgetMB) MB budget$warn | info |"
        }
        if ($null -ne $l.monoUsedMB) {
            # U-112 (D-116): the heap and the counts that can grow per visit, per leg (info; the creep row takes their per-visit deltas).
            $rows += "| Heap $dot $($l.leg) (dev build) | info (U-112): Mono used / heap, native allocated / reserved (unused), Addressable handles held, loaded GameObjects, TMP texts, AudioSources | mono $($l.monoUsedMB) / $($l.monoHeapMB) MB, native $($l.allocMB) / $($l.reservedMB) MB ($($l.unusedReservedMB) unused), handles $($l.handlesHeld), objects $($l.gameObjects), tmp $($l.tmpObjects), audio $($l.audioSources) | info |"
        }
    }
    # D-114: the boot -> warm Earth delta is the Space scene's resident set (belt, discs, waystations, starfield): its own row, <= 150 MB.
    $warm = $byLeg['Earth (warm)']; $boot = $byLeg['Earth']
    if ($null -ne $warm -and $null -ne $boot) {
        $wsW = if ($warm.workingSetMB -gt 0) { [long]$warm.workingSetMB } else { [long]$warm.systemMB }
        $wsB = if ($boot.workingSetMB -gt 0) { [long]$boot.workingSetMB } else { [long]$boot.systemMB }
        $dWs = $wsW - $wsB
        $dPriv = if ($null -ne $warm.privateMB -and $null -ne $boot.privateMB) { [long]$warm.privateMB - [long]$boot.privateMB } else { 0 }
        $dok = ($dWs -le 150) -and ($dPriv -le 150)
        if (-not $dok) { $memRed = $true }
        $rows += "| Boot $ar warm $dot Earth (dev build) | $le 150 MB: the Space scene resident after the first launch + re-entry (D-114) | working set +$dWs MB, private +$dPriv MB | $(if ($dok) { 'green' } else { 'red' }) |"
    }
    # Return rows (D-089 / D-114): a second visit stays within 10 % of its baseline (Earth: the warm leg; Space: the first Space leg).
    foreach ($pair in @(@('Space after Mars', 'Space'), @('Earth again', 'Earth (warm)'))) {
        $again = $byLeg[$pair[0]]; $first = $byLeg[$pair[1]]
        if ($null -eq $again -or $null -eq $first) { continue }
        $wsA = if ($again.workingSetMB -gt 0) { [long]$again.workingSetMB } else { [long]$again.systemMB }
        $wsF = if ($first.workingSetMB -gt 0) { [long]$first.workingSetMB } else { [long]$first.systemMB }
        # D-116: the row judges private commit; working set is info. Without a private figure (an old probe) it falls back to working set.
        $hasPriv = ($null -ne $again.privateMB -and $null -ne $first.privateMB -and [long]$first.privateMB -gt 0)
        if ($hasPriv) {
            $rok = [long]$again.privateMB -le [long]([long]$first.privateMB * 1.10)
            $pct = [math]::Round(([double]$again.privateMB / [double]$first.privateMB - 1.0) * 100.0, 1)
            $measured = "private $($again.privateMB) vs $($first.privateMB) MB ($(if ($pct -ge 0) { '+' })$pct %); working set $wsA vs $wsF MB (info)"
        } else {
            $rok = ($wsF -gt 0) -and ($wsA -le [long]($wsF * 1.10))
            $measured = "working set $wsA vs $wsF MB (no private figure)"
        }
        if (-not $rok) { $memRed = $true }
        $rows += "| Return $dot $($pair[0]) (dev build) | private commit within 10 % of $($pair[1]) (D-089 / D-116) | $measured | $(if ($rok) { 'green' } else { 'red' }) |"
    }
    # D-116: the per-visit creep, (private at the last leg - private at Earth (warm)) / planet visits after the warm leg; info through C1, a budget row (<= 10 MB) from C2.
    $warmLeg = $byLeg['Earth (warm)']; $lastLeg = $legs | Select-Object -Last 1
    if ($null -ne $warmLeg -and $null -ne $lastLeg -and $null -ne $warmLeg.privateMB -and $null -ne $lastLeg.privateMB) {
        $warmIndex = [array]::IndexOf(@($legs | ForEach-Object { [string]$_.leg }), 'Earth (warm)')
        $visits = @($legs | Select-Object -Skip ($warmIndex + 1) | Where-Object { [string]$_.leg -notlike 'Space*' }).Count
        if ($visits -gt 0) {
            $creep = [math]::Round(([double]$lastLeg.privateMB - [double]$warmLeg.privateMB) / $visits, 1)
            # U-112: the same delta per visit for the heap counters the probe prints per leg, so the hunt starts from the report.
            $extra = ''
            if ($null -ne $warmLeg.monoUsedMB -and $null -ne $lastLeg.monoUsedMB) {
                $extra = "; per visit: mono $([math]::Round(([double]$lastLeg.monoUsedMB - [double]$warmLeg.monoUsedMB) / $visits, 1)) MB, native allocated $([math]::Round(([double]$lastLeg.allocMB - [double]$warmLeg.allocMB) / $visits, 1)) MB, reserved $([math]::Round(([double]$lastLeg.reservedMB - [double]$warmLeg.reservedMB) / $visits, 1)) MB, handles $([math]::Round(([double]$lastLeg.handlesHeld - [double]$warmLeg.handlesHeld) / $visits, 1)), objects $([math]::Round(([double]$lastLeg.gameObjects - [double]$warmLeg.gameObjects) / $visits, 0)), tmp $([math]::Round(([double]$lastLeg.tmpObjects - [double]$warmLeg.tmpObjects) / $visits, 1)), audio $([math]::Round(([double]$lastLeg.audioSources - [double]$warmLeg.audioSources) / $visits, 1))"
            }
            $rows += "| Creep per visit (dev build) | info through C1, $le 10 MB from C2 (D-116): (private at $($lastLeg.leg) $ar private at Earth (warm)) / $visits planet visits | $creep MB per visit (private $($warmLeg.privateMB) $ar $($lastLeg.privateMB) MB)$extra | info |"
        }
    }
    $mip = $legs | Where-Object { $null -ne $_.mipActive } | Select-Object -First 1
    if ($null -ne $mip) {
        $mok = ([int]$mip.mipActive -eq 1) -and ([long]$mip.mipBudgetMB -eq 512)
        if (-not $mok) { $memRed = $true }
        $rows += "| Mip streaming (dev build) | on, 512 MB budget (D-089) | active $($mip.mipActive), budget $($mip.mipBudgetMB) MB | $(if ($mok) { 'green' } else { 'red' }) |"
    }
    # U-095: the film pass's GPU cost at 1080p (FrameTimingManager in the player: frame GPU time with the pass on minus off).
    $film = @()
    if ($buildOk -and (Test-Path $probeOut)) { $film = @(Get-Content $probeOut | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json } | Where-Object { $null -ne $_.filmPassMs }) }
    if ($film.Count -eq 0) { $rows += "| Film pass GPU $dot Earth (dev build) | $le 0.6 ms at 1080p (U-095) | no film probe result | red |"; $memRed = $true }
    foreach ($f in $film) {
        $pass = [double]$f.filmPassMs
        $fok = ([double]$f.filmGpuOnMs -gt 0) -and ($pass -le 0.6)
        if (-not $fok) { $memRed = $true }
        $fText = if ([double]$f.filmGpuOnMs -le 0) { 'no GPU timings from FrameTimingManager' } else { "on $($f.filmGpuOnMs) ms, off $($f.filmGpuOffMs) ms, pass $($f.filmPassMs) ms at $($f.width)${times}$($f.height)" }
        $rows += "| Film pass GPU $dot $($f.leg) (dev build) | $le 0.6 ms at 1080p (U-095) | $fText | $(if ($fok) { 'green' } else { 'red' }) |"
    }
    if (Test-Path $report) {
        $text = Get-Content $report -Raw -Encoding UTF8
        $cut = $text.IndexOf("`n## Memory in the development player")
        if ($cut -ge 0) { $text = $text.Substring(0, $cut) }
        Set-Content -Path $report -Value ($text.TrimEnd() + "`n" + ($rows -join "`n") + "`n") -Encoding UTF8 -NoNewline
    } else {
        Set-Content -Path $report -Value (($rows -join "`n") + "`n") -Encoding UTF8 -NoNewline
    }
    $rows | Where-Object { $_ -like '| Memory*' -or $_ -like '| Residency*' -or $_ -like '| Film*' -or $_ -like '| Planet load*' -or $_ -like '| Transition*' -or $_ -like '| Bundles*' -or $_ -like '| Sprite atlases*' -or $_ -like '| Return*' -or $_ -like '| Mip*' -or $_ -like '| Boot*' -or $_ -like '| Creep*' -or $_ -like '| Heap*' } | ForEach-Object { Write-Host $_ }
}

if ($SkipGate) { if ($memRed) { Write-Host 'BUILD MEMORY RED'; exit 1 } else { Write-Host 'BUILD MEMORY GREEN'; exit 0 } }
if (-not (Test-Path $xml)) { Write-Host 'PROFILE FAILED: no results file'; exit 1 }
[xml]$doc = Get-Content $xml -Raw
$passed = $doc.'test-run'.passed -eq '1'
if (Test-Path $report) { Write-Host "Report: $report" } else { Write-Host 'Report not written (test failed before the end)' }
if ($passed -and -not $memRed) { Write-Host 'BUDGETGATE GREEN'; exit 0 }
if ($passed) { Write-Host 'BUDGETGATE GREEN, BUILD MEMORY RED'; exit 1 }
$msg = $doc.SelectSingleNode('//test-case/failure/message')
Write-Host "BUDGETGATE RED: $($msg.InnerText)"
exit 1
