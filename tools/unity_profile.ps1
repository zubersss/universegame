# BudgetGate profile run (U-014): runs BudgetGateTests with graphics and writes
# coordination/reports/unity/perf_<date>.md with every Bible section 11.1 row. Owner: UNITY.
# -Build (U-041, D-036): also builds the development player and runs its memory probe
# (nine legs: Earth, Space, Mars, Space, Mercury, Space, Venus, Space, Earth again; U-091) under the same lock, adding "dev build" rows to the report.
# -Probe (U-086): runs the probe on the player already in Build/ without rebuilding it.
# -Release (U-143): after a green probe the same code is built again as the release player in Build/MERIDIAN_<v>/ under the same
# hold (no Development Build watermark; the owner's build); the probed development player stays in Build/MERIDIAN_<v>_dev/.
# The Editor's memory rows stay as an upper bound. Limits are Bible 11.1 v4 (D-089).
# -Control <version> (D-191 amended, LEAD 2026-11-09 21:1x): after this build's probe, the SAME probe runs on the last build's
# development player (Build/MERIDIAN_<version>_dev/, still on disk) in the same lock, and this build's frame and transition rows
# are judged against it: more than 20 % above the control is red (the release build is then not made). A figure recorded in
# another hour is not a baseline: on 2026-11-09 the same 0.6.1 player read 28-48 % slower at night than in the afternoon.
# Usage: tools/unity_profile.ps1 [-Build | -Probe] [-SkipGate] [-Release] [-Control 0.6.1]
param([switch]$Build, [switch]$Probe, [switch]$SkipGate, [switch]$Release, [string]$Control = '')
. (Join-Path $PSScriptRoot 'unity_common.ps1')

$date = Get-Date -Format 'yyyy-MM-dd'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$xml = Join-Path $LogDir "profile_$stamp.xml"
$report = Join-Path $RepoRoot "coordination\reports\unity\perf_$date.md"
$probeOut = Join-Path $LogDir "memory_probe_$stamp.jsonl"
$controlOut = Join-Path $LogDir "memory_probe_control_${Control}_$stamp.jsonl"
$controlRan = $false
$buildOk = $true
$runProbe = $Build -or $Probe

$jobName = 'unity_profile' + $(if ($Build) { ' + dev build memory probe' } elseif ($Probe) { ' + memory probe (existing build)' } else { '' }) + $(if ($Release -and $runProbe) { ' + release build' } else { '' })

# U-143: the release build after a green probe (0 when not asked or built OK, 1 when it fails). The lock is taken again (a no-op under an outer hold).
function Complete-Release {
    if (-not ($Release -and $runProbe)) { return 0 }
    try { $null = Enter-HeavyJobLock 'unity_profile: the release build after a green probe (U-143)' } catch { Write-Host "RELEASE BUILD BLOCKED: $_"; return 2 }
    try {
        $rb = Invoke-UnityBatch @('-quit', '-executeMethod', 'Meridian.EditorTools.BuildTools.BuildFromCommandLine', '-meridianRelease') "unity_build_release_$stamp.log"
    } finally { $null = Exit-HeavyJobLock }
    $rline = Select-String -Path $rb.Log -Pattern '\[MERIDIAN\] BUILD (OK|FAILED).*' | Select-Object -Last 1
    Write-Host "Release build log: $($rb.Log)"
    if ($rline) { Write-Host $rline.Line.Trim() }
    $rexe = Get-PlayerExe (Get-GameVersion)
    if ($rb.ExitCode -ne 0 -or -not $rline -or $rline.Line -notmatch 'BUILD OK' -or -not (Test-Path $rexe)) { Write-Host 'RELEASE BUILD FAILED'; return 1 }
    Write-Host "RELEASE BUILD OK: $rexe"
    return 0
}
try { Enter-HeavyJobLock $jobName } catch { Write-Host "BLOCKED: $_"; exit 2 }
$memStart = Get-MemoryNote   # LEAD 18:5x (2026-11-09): the machine's memory beside every perf row
$memEnd = ''
Write-Host "Machine memory at the start: $memStart"
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
        $version = Get-GameVersion
        $exe = Get-PlayerExe $version -Dev   # U-143: the probe runs on the development player (its memory counters)
        if (-not (Test-Path $exe)) { Write-Host "PROBE: no player at $exe (build first)"; $buildOk = $false }
        # D-203: the probe flies nine legs and each transition autosaves: its saves go to a folder of the run's own.
        elseif (-not (Test-PlayerSaveRootSwitch $exe)) { Write-Host "PROBE REFUSED (D-203): the player at $exe predates -meridianSaveRoot; it would autosave into the owner's real save slot"; $buildOk = $false }
        else {
            $playerLog = Join-Path $LogDir "memory_probe_$stamp.log"
            $probeSaves = New-PlayerSaveRoot 'probe_saves'
            $p = Start-Process -FilePath $exe -PassThru -ArgumentList @('-meridianMemoryProbe', "`"$probeOut`"", '-meridianSaveRoot', "`"$probeSaves`"",
                '-screen-fullscreen', '0', '-screen-width', '1920', '-screen-height', '1080', '-logFile', "`"$playerLog`"")
            if (-not $p.WaitForExit(480000)) { Stop-Process -Id $p.Id -Force; Write-Host 'PROBE TIMED OUT (8 min)'; $buildOk = $false }
            Write-Host "Player log: $playerLog"
            if (-not (Test-PlayerTookSaveRoot $playerLog)) { Write-Host "PROBE RED (D-203): the player's log has no '[MERIDIAN] saves go to' line: it did not take -meridianSaveRoot"; $buildOk = $false }
            # D-194 (LEAD 2026-11-09): the Windows player draws on Direct3D 11, pinned in ProjectSettings; the Editor's perf captures are
            # forced to the same API. A probe whose player drew on anything else is not this game's and is red.
            $api = $null
            if (Test-Path $playerLog) { $api = Select-String -Path $playerLog -Pattern 'Version:\s+Direct3D [0-9.]+' | Select-Object -First 1 }
            $apiText = 'no Direct3D line in the player log'
            if ($api) { $apiText = ($api.Matches[0].Value -replace '\s+', ' ') }
            Write-Host "Player graphics API: $apiText"
            if ($apiText -notmatch 'Direct3D 11') { Write-Host 'PROBE RED: the player did not draw on Direct3D 11 (D-194)'; $buildOk = $false }
        }
    }
    if ($runProbe -and $buildOk -and $Control) {
        # D-191 amended: the last build's player on the same machine, right after this build's
        $exeC = Get-PlayerExe $Control -Dev
        if (-not (Test-Path $exeC)) { Write-Host "CONTROL: no player at $exeC" }
        # D-203: a control built before -meridianSaveRoot (0.6.3 and older) would write the owner's save slot: it is not run.
        elseif (-not (Test-PlayerSaveRootSwitch $exeC)) { Write-Host "CONTROL SKIPPED (D-203): the player at $exeC predates -meridianSaveRoot; probing it would autosave into the owner's real save slot. No control row for this build." }
        else {
            $controlLog = Join-Path $LogDir "memory_probe_control_${Control}_$stamp.log"
            $controlSaves = New-PlayerSaveRoot 'probe_control_saves'
            $pc = Start-Process -FilePath $exeC -PassThru -ArgumentList @('-meridianMemoryProbe', "`"$controlOut`"", '-meridianSaveRoot', "`"$controlSaves`"",
                '-screen-fullscreen', '0', '-screen-width', '1920', '-screen-height', '1080', '-logFile', "`"$controlLog`"")
            if (-not $pc.WaitForExit(480000)) { Stop-Process -Id $pc.Id -Force; Write-Host 'CONTROL PROBE TIMED OUT (8 min)' }
            else { $controlRan = Test-Path $controlOut }
            Write-Host "Control player log: $controlLog"
        }
    }
} finally {
    Remove-Item Env:\MERIDIAN_PROFILE_REPORT -ErrorAction SilentlyContinue
    $memEnd = Get-MemoryNote
    Write-Host "Machine memory at the end: $memEnd"
    Exit-HeavyJobLock
}
# The memory note goes under the gate's "Load during measurement" line (the gate rewrites the report on each run).
if ((-not $SkipGate) -and (Test-Path $report)) {
    $text = Get-Content $report -Raw -Encoding UTF8
    $rx = [regex]'(?m)^- Load during measurement[^\r\n]*\r?\n'
    $note = "- Machine memory (LEAD 2026-11-09): at the start $memStart; at the end $memEnd"
    if ($rx.IsMatch($text) -and $text.IndexOf('- Machine memory (LEAD 2026-11-09)') -lt 0) {
        $text = $rx.Replace($text, { param($m) $m.Value + $note + "`n" }, 1)
        Set-Content -Path $report -Value $text -Encoding UTF8 -NoNewline
    }
}

# ---- dev-build rows (U-041; v4 limits U-091, D-089) ----
$memRed = $false
# Report symbols as code points (tools/*.ps1 stay ASCII).
$le = [char]0x2264; $ar = [char]0x2192; $times = [char]0x00D7; $sec = [char]0x00A7; $dot = [char]0x00B7
$limit = "< 2.0 GB working set (warn 1.7), $le 512 MB textures, $le 150 MB audio"
if ($runProbe) {
    $rows = @('', '## Memory in the development player (U-041, D-036; limits v4, D-089)', '',
        "The route Earth $ar launch $ar Space $ar entry $ar Earth (warm, D-114) $ar launch $ar Space $ar entry $ar Mars $ar launch $ar Space $ar entry $ar Mercury $ar launch $ar Space $ar entry $ar Venus $ar launch $ar Space $ar entry $ar Earth again, then a second loop $ar Mars again $ar Earth again 2 (U-112 / D-139: a one-time first-visit cost against a per-visit creep) (thirteen legs, real launches and entries, U-091) in Build/MERIDIAN_<version>/MERIDIAN.exe (development build), 1920${times}1080 windowed; counters read after GC + UnloadUnusedAssets and 120 frames per leg. Working set and private commit from the OS (ProcessMemory); the Editor rows above stay as an upper bound. Meshes are printed, not judged.", '',
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
        # U-211 (LEAD 2026-11-10): the worst frame of the first second after the transition, from the frame it ended in: where a hitch
        # as the view comes up is judged (the autosave ran in that frame until the build after 0.6.3). An older player has no figure.
        if ($null -ne $l.afterWorstMs -and [double]$l.afterWorstMs -ge 0) {
            $hok = ([double]$l.afterWorstMs -le 50)
            if (-not $hok) { $memRed = $true }
            $rows += "| Worst frame in the first second after the transition $dot $($l.leg) (dev build) | $le 50 ms (Bible 11.1; U-211) | $($l.afterWorstMs) ms | $(if ($hok) { 'green' } else { 'red' }) |"
        }
        if ($null -ne $l.bundles) {
            $planetBundles = @([string]$l.bundles -split ', ' | Where-Object { $_ -like 'planet_*' -and $_ -notlike 'planet_space*' -and $_ -notlike 'planet_warden*' -and $_ -notlike 'planet_waystation*' -and $_ -notlike 'planet_rig*' -and $_ -notlike 'planet_dig*' })
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
            $gfxText = if ($null -ne $l.gfxMB) { "; gfx driver $($l.gfxMB) MB; textures $($l.texCount) ($($l.texSizeMB) MB), meshes $($l.meshCount) ($($l.meshSizeMB) MB), shaders $($l.shaders), materials $($l.materials), clips $($l.animClips)" } else { '' }
            $rows += "| Heap $dot $($l.leg) (dev build) | info (U-112): Mono used / heap, native allocated / reserved (unused), Addressable handles held, loaded GameObjects, TMP texts, AudioSources; D-139: the graphics driver's memory and the loaded textures / meshes / shaders / materials | mono $($l.monoUsedMB) / $($l.monoHeapMB) MB, native $($l.allocMB) / $($l.reservedMB) MB ($($l.unusedReservedMB) unused), handles $($l.handlesHeld), objects $($l.gameObjects), tmp $($l.tmpObjects), audio $($l.audioSources)$gfxText | info |"
        }
        if ($null -ne $l.held) {
            # D-139: the sets a leg keeps (Residency's held keys with counts): the biome layer sets, the near disc frames, the Sun rig, the creature sheets.
            $rows += "| Resident sets $dot $($l.leg) (dev build) | info (U-112 / D-139): the Addressable keys held after the settle | $($l.held) | info |"
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
    # Return rows (D-089 / D-114; U-202, D-189 for Space): a later visit stays within 10 % of its WARM baseline. Earth again against
    # Earth (warm); Space after Mars and every later Space leg against "Space after Earth", the Space leg after the first planet visit
    # (the first Space leg is cold: its one-time warm-up, Mono heap 40 -> 54 MB and the warm sets, read as a 10 % "return" on three
    # builds). A probe file without that leg keeps the cold baseline.
    $spaceBase = if ($null -ne $byLeg['Space after Earth']) { 'Space after Earth' } else { 'Space' }
    $pairs = New-Object System.Collections.ArrayList
    foreach ($name in @('Space after Mars', 'Space after Mercury', 'Space after Venus', 'Space after Earth again', 'Space after Mars again')) { $null = $pairs.Add(@($name, $spaceBase)) }
    $null = $pairs.Add(@('Earth again', 'Earth (warm)'))
    # D-189: the first Space leg -> warm Space delta has its own row, capped at 150 MB private, so a leak cannot hide inside the
    # warm-up; and the old cold-baseline figure stays beside it as an info line through 0.6.4 (three builds).
    $coldSpace = $byLeg['Space']; $warmSpace = $byLeg['Space after Earth']
    if ($null -ne $coldSpace -and $null -ne $warmSpace -and $null -ne $coldSpace.privateMB -and $null -ne $warmSpace.privateMB -and [long]$coldSpace.privateMB -gt 0) {
        $dWarm = [long]$warmSpace.privateMB - [long]$coldSpace.privateMB
        $wok = ($dWarm -le 150)
        if (-not $wok) { $memRed = $true }
        $rows += "| Space first $ar warm (dev build) | $le 150 MB private: the one-time warm-up after the first Space leg (D-189) | private $($coldSpace.privateMB) $ar $($warmSpace.privateMB) MB ($(if ($dWarm -ge 0) { '+' })$dWarm MB) | $(if ($wok) { 'green' } else { 'red (over the cap: D-189 reopens)' }) |"
        $afterMars = $byLeg['Space after Mars']
        if ($null -ne $afterMars -and $null -ne $afterMars.privateMB) {
            $pctCold = [math]::Round(([double]$afterMars.privateMB / [double]$coldSpace.privateMB - 1.0) * 100.0, 1)
            $rows += "| Return $dot Space after Mars against the cold first Space leg (dev build) | info through 0.6.4 (D-189): the figure D-089's row judged until 0.6.1 | private $($afterMars.privateMB) vs $($coldSpace.privateMB) MB ($(if ($pctCold -ge 0) { '+' })$pctCold %) | info |"
        }
    }
    foreach ($pair in $pairs) {
        $again = $byLeg[$pair[0]]; $first = $byLeg[$pair[1]]
        if ($null -eq $again -or $null -eq $first) { continue }
        if ($pair[0] -eq $pair[1]) { continue }
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
        $rule = if ($pair[0] -like 'Space*') { 'D-089 / D-116; the warm Space baseline, D-189' } else { 'D-089 / D-116' }
        $rows += "| Return $dot $($pair[0]) (dev build) | private commit within 10 % of $($pair[1]) ($rule) | $measured | $(if ($rok) { 'green' } else { 'red' }) |"
    }
    # D-116: the per-visit creep, (private at the last leg - private at Earth (warm)) / planet visits after the warm leg; info through C1, a budget row (<= 10 MB) from C2.
    $warmLeg = $byLeg['Earth (warm)']; $lastLeg = if ($null -ne $byLeg['Earth again']) { $byLeg['Earth again'] } else { $legs | Select-Object -Last 1 } # D-116: the four visits to Earth again; the second loop has its own row
    if ($null -ne $warmLeg -and $null -ne $lastLeg -and $null -ne $warmLeg.privateMB -and $null -ne $lastLeg.privateMB) {
        $warmIndex = [array]::IndexOf(@($legs | ForEach-Object { [string]$_.leg }), 'Earth (warm)')
        $lastIndex = [array]::IndexOf(@($legs | ForEach-Object { [string]$_.leg }), [string]$lastLeg.leg)
        $visits = @($legs | Select-Object -Skip ($warmIndex + 1) -First ($lastIndex - $warmIndex) | Where-Object { [string]$_.leg -notlike 'Space*' }).Count
        if ($visits -gt 0) {
            $creep = [math]::Round(([double]$lastLeg.privateMB - [double]$warmLeg.privateMB) / $visits, 1)
            # U-112: the same delta per visit for the heap counters the probe prints per leg, so the hunt starts from the report.
            $extra = ''
            if ($null -ne $warmLeg.monoUsedMB -and $null -ne $lastLeg.monoUsedMB) {
                $extra = "; per visit: mono $([math]::Round(([double]$lastLeg.monoUsedMB - [double]$warmLeg.monoUsedMB) / $visits, 1)) MB, native allocated $([math]::Round(([double]$lastLeg.allocMB - [double]$warmLeg.allocMB) / $visits, 1)) MB, reserved $([math]::Round(([double]$lastLeg.reservedMB - [double]$warmLeg.reservedMB) / $visits, 1)) MB, handles $([math]::Round(([double]$lastLeg.handlesHeld - [double]$warmLeg.handlesHeld) / $visits, 1)), objects $([math]::Round(([double]$lastLeg.gameObjects - [double]$warmLeg.gameObjects) / $visits, 0)), tmp $([math]::Round(([double]$lastLeg.tmpObjects - [double]$warmLeg.tmpObjects) / $visits, 1)), audio $([math]::Round(([double]$lastLeg.audioSources - [double]$warmLeg.audioSources) / $visits, 1))"
                if ($null -ne $warmLeg.gfxMB -and $null -ne $lastLeg.gfxMB) { $extra += "; gfx driver $([math]::Round(([double]$lastLeg.gfxMB - [double]$warmLeg.gfxMB) / $visits, 1)) MB, textures $([math]::Round(([double]$lastLeg.texSizeMB - [double]$warmLeg.texSizeMB) / $visits, 1)) MB ($([math]::Round(([double]$lastLeg.texCount - [double]$warmLeg.texCount) / $visits, 1))), meshes $([math]::Round(([double]$lastLeg.meshSizeMB - [double]$warmLeg.meshSizeMB) / $visits, 1)) MB, shaders $([math]::Round(([double]$lastLeg.shaders - [double]$warmLeg.shaders) / $visits, 1)), materials $([math]::Round(([double]$lastLeg.materials - [double]$warmLeg.materials) / $visits, 1))" }
            }
            $rows += "| First-visit cost per planet (dev build) | info (D-143): (private at $($lastLeg.leg) $ar private at Earth (warm)) / $visits first visits - what a planet's own content costs the first time; the Creep row judges the second loop | $creep MB per planet (private $($warmLeg.privateMB) $ar $($lastLeg.privateMB) MB)$extra | info |"
        }
    }
    # U-112 (D-139): the second loop — Mars again, Earth again 2 — against Earth again: a per-visit creep repeats here, a one-time first-visit cost does not.
    $again = $byLeg['Earth again']; $again2 = $byLeg['Earth again 2']
    if ($null -ne $again -and $null -ne $again2 -and $null -ne $again.privateMB -and $null -ne $again2.privateMB) {
        $creep2 = [math]::Round(([double]$again2.privateMB - [double]$again.privateMB) / 2, 1)
        $extra2 = ''
        if ($null -ne $again.gfxMB -and $null -ne $again2.gfxMB) { $extra2 = "; per visit: gfx driver $([math]::Round(([double]$again2.gfxMB - [double]$again.gfxMB) / 2, 1)) MB, native allocated $([math]::Round(([double]$again2.allocMB - [double]$again.allocMB) / 2, 1)) MB, textures $([math]::Round(([double]$again2.texSizeMB - [double]$again.texSizeMB) / 2, 1)) MB, meshes $([math]::Round(([double]$again2.meshSizeMB - [double]$again.meshSizeMB) / 2, 1)) MB, shaders $([math]::Round(([double]$again2.shaders - [double]$again.shaders) / 2, 1)), handles $([math]::Round(([double]$again2.handlesHeld - [double]$again.handlesHeld) / 2, 1))" }
        # LEAD cycle 270: the Mono heap and the allocator reserve per visit too (the 0.4.3 second loop read 7.5 MB with every attributed counter at 0).
        if ($null -ne $again.monoHeapMB -and $null -ne $again2.monoHeapMB) { $extra2 += "; Mono heap $([math]::Round(([double]$again2.monoHeapMB - [double]$again.monoHeapMB) / 2, 1)) MB (used $([math]::Round(([double]$again2.monoUsedMB - [double]$again.monoUsedMB) / 2, 1)) MB), native reserved $([math]::Round(([double]$again2.reservedMB - [double]$again.reservedMB) / 2, 1)) MB" }
        $pct2 = [math]::Round(([double]$again2.privateMB / [double]$again.privateMB - 1.0) * 100.0, 1)
        $cok = ($creep2 -le 10)
        if (-not $cok) { $memRed = $true }
        $rows += "| Creep per visit (dev build) | $le 10 MB from C2 (D-116 / D-143): the second loop, (private at Earth again 2 $ar private at Earth again) / 2 planet visits | $creep2 MB per visit (private $($again.privateMB) $ar $($again2.privateMB) MB, $(if ($pct2 -ge 0) { '+' })$pct2 %)$extra2 | $(if ($cok) { 'green' } else { 'red' }) |"
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
        $blocks = if ($null -ne $f.filmDiffs) { " (D-180: the median of $(@($f.filmDiffs).Count) interleaved pairs of $($f.filmBlockFrames) frames, spread $($f.filmSpreadMs) ms; on $(@($f.filmOn) -join ' / '), off $(@($f.filmOff) -join ' / '), on - off $(@($f.filmDiffs) -join ' / '))" } else { '' }
        $fText = if ([double]$f.filmGpuOnMs -le 0) { 'no GPU timings from FrameTimingManager' } else { "on $($f.filmGpuOnMs) ms, off $($f.filmGpuOffMs) ms, pass $($f.filmPassMs) ms at $($f.width)${times}$($f.height)$blocks" }
        $rows += "| Film pass GPU $dot $($f.leg) (dev build) | $le 0.6 ms at 1080p (U-095, D-180) | $fText | $(if ($fok) { 'green' } else { 'red' }) |"
    }
    # U-148 (D-158): the climb's frame times on Earth (a real pad-to-Escape-Line climb at full thrust in the player; the iris apart).
    $climb = @()
    if ($buildOk -and (Test-Path $probeOut)) { $climb = @(Get-Content $probeOut | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json } | Where-Object { $null -ne $_.climbP99Ms }) }
    if ($climb.Count -eq 0) { $rows += "| Climb $dot Earth (dev build) | p99 $le 20 ms, no frame > 50 ms outside the iris (U-148) | no climb probe result | red |"; $memRed = $true }
    foreach ($c in $climb) {
        $cok = ([double]$c.climbP99Ms -le 20) -and ([int]$c.climbOver50 -eq 0) -and ([int]$c.climbFrames -gt 60) -and $c.reachedSpace
        if (-not $cok) { $memRed = $true }
        $rows += "| Climb $dot Earth (dev build) | p99 $le 20 ms, no frame > 50 ms outside the iris (U-148) | $($c.climbFrames) frames in $($c.climbSeconds) s to $($c.topSpeed) m/s: p99 $($c.climbP99Ms) ms, worst $($c.climbWorstMs) ms, $($c.climbOver50) over 50 ms; the iris $($c.irisFrames) frames, longest $($c.irisWorstMs) ms; in Space $($c.reachedSpace) | $(if ($cok) { 'green' } else { 'red' }) |"
    }
    # U-216 (D-205): the living stage's prices at Earth's camp in the dev player (MemoryProbe.LivingCost): six states interleaved. Reported, not gated.
    $living = @()
    if ($buildOk -and (Test-Path $probeOut)) { $living = @(Get-Content $probeOut | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json } | Where-Object { $null -ne $_.livingStates }) }
    foreach ($lv in $living) {
        $st = @($lv.livingStates); $mn = @($lv.livingMainMs); $rd = @($lv.livingRenderMs); $gp = @($lv.livingGpuMs); $dr = @($lv.livingDraws)
        $diff = { param($a, $b) '{0:+0.000;-0.000;0.000}' -f ([double]$a - [double]$b) }
        $diffDraws = { param($a, $b) '{0:+0.0;-0.0;0.0}' -f ([double]$a - [double]$b) }
        $rows += @('', "### The living stage (U-216): its price in the development player at Earth's camp, $($lv.livingPxPerMetre) px a metre, $($lv.width)${times}$($lv.height)", '',
            "$($lv.livingPieces) stand-in pieces, $($lv.livingVertices) vertices; the lamp reads the normal map: $($lv.livingLampNormals). Medians of $($lv.livingRounds) interleaved rounds of $($lv.livingBlockFrames) frames a state; spread of a state's GPU blocks: $(@($lv.livingGpuSpreadMs) -join ' / ') ms, of its main-thread blocks: $(@($lv.livingMainSpreadMs) -join ' / ') ms. Reported, not gated.", '',
            '| State | Main thread ms | Render thread ms | GPU frame ms | Draw calls |', '|---|---|---|---|---|')
        for ($i = 0; $i -lt $st.Count; $i++) { $rows += "| $($st[$i]) | $($mn[$i]) | $($rd[$i]) | $($gp[$i]) | $($dr[$i]) |" }
        $rows += @('', '| Price | Main thread ms | Render thread ms | GPU frame ms | Draw calls |', '|---|---|---|---|---|')
        $rows += "| Living stage $dot the whole stage (all - off) | $(& $diff $mn[1] $mn[0]) | $(& $diff $rd[1] $rd[0]) | $(& $diff $gp[1] $gp[0]) | $(& $diffDraws $dr[1] $dr[0]) |"
        $parts = @('the wind (the bend and the push)', 'the air (motes, leaves, shafts, the cloud shadow)', 'the vine chain', 'the lit piece and its lamp')
        for ($i = 0; $i -lt 4; $i++) {
            $k = $i + 2
            $rows += "| Living stage $dot $($parts[$i]) (all - $($st[$k])) | $(& $diff $mn[1] $mn[$k]) | $(& $diff $rd[1] $rd[$k]) | $(& $diff $gp[1] $gp[$k]) | $(& $diffDraws $dr[1] $dr[$k]) |"
        }
        $rows += @('', "The chip's frame budget left with the whole stage on: GPU $('{0:0.00}' -f (16.6 - [double]$gp[1])) ms of 16.6 (its frame takes $($gp[1]) ms), main thread $('{0:0.00}' -f (16.6 - [double]$mn[1])) ms of 16.6 (it takes $($mn[1]) ms).")
    }
    # D-191 amended: this build's frame and transition rows against the control's, both measured in this lock.
    if ($Control) {
        $rows += @('', "### The last build's control (D-191): $Control's development player probed in the same lock", '',
            "| Row | $Control (control) | this build | this build against the control | Status |", '|---|---|---|---|---|')
        if (-not $controlRan) { $rows += "| Control | | no control result (no player on disk, or its probe failed) | | red |"; $memRed = $true }
        else {
            $legsC = @(Get-Content $controlOut | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json })
            $byLegC = @{}
            foreach ($l in $legsC) { if ($null -ne $l.leg -and $null -ne $l.systemMB) { $byLegC[[string]$l.leg] = $l } }
            # one comparison: red when this build reads more than 20 % above the control (and the control read something)
            function Add-ControlRow([string]$name, $now, $then, [string]$unit, [bool]$judged) {
                if ($null -eq $now -or $null -eq $then -or [double]$then -le 0) { return }
                $pct = [math]::Round(([double]$now / [double]$then - 1.0) * 100.0, 1)
                $ok = (-not $judged) -or ($pct -le 20)
                if (-not $ok) { $script:memRed = $true }
                $script:rows += "| $name | $then $unit | $now $unit | $(if ($pct -ge 0) { '+' })$pct % | $(if (-not $judged) { 'info' } elseif ($ok) { 'green' } else { 'red (over 20 %)' }) |"
            }
            foreach ($l in $legs) {
                $c = $byLegC[[string]$l.leg]
                if ($null -eq $c) { continue }
                if ($null -ne $l.transitionSec -and [double]$l.transitionSec -ge 0) { Add-ControlRow "Transition $dot $($l.leg)" $l.transitionSec $c.transitionSec 's' $true }
            }
            $climbC = @($legsC | Where-Object { $null -ne $_.climbP99Ms }) | Select-Object -First 1
            $climbN = $climb | Select-Object -First 1
            if ($null -ne $climbC -and $null -ne $climbN) {
                Add-ControlRow "Climb p99 $dot Earth" $climbN.climbP99Ms $climbC.climbP99Ms 'ms' $true
                Add-ControlRow "Climb worst frame $dot Earth" $climbN.climbWorstMs $climbC.climbWorstMs 'ms' $false   # one frame of ~1400: printed, not judged
            }
            $filmC = @($legsC | Where-Object { $null -ne $_.filmGpuOnMs }) | Select-Object -First 1
            $filmN = $film | Select-Object -First 1
            if ($null -ne $filmC -and $null -ne $filmN) {
                Add-ControlRow "GPU frame, film on $dot Earth" $filmN.filmGpuOnMs $filmC.filmGpuOnMs 'ms' $true
                Add-ControlRow "GPU frame, film off $dot Earth" $filmN.filmGpuOffMs $filmC.filmGpuOffMs 'ms' $true
            }
        }
        $rows += "Machine at the start: $memStart; at the end: $memEnd"
    }
    if (Test-Path $report) {
        $text = Get-Content $report -Raw -Encoding UTF8
        $cut = $text.IndexOf("`n## Memory in the development player")
        if ($cut -ge 0) { $text = $text.Substring(0, $cut) }
        Set-Content -Path $report -Value ($text.TrimEnd() + "`n" + ($rows -join "`n") + "`n") -Encoding UTF8 -NoNewline
    } else {
        Set-Content -Path $report -Value (($rows -join "`n") + "`n") -Encoding UTF8 -NoNewline
    }
    $rows | Where-Object { $_ -like '| Memory*' -or $_ -like '| Residency*' -or $_ -like '| Film*' -or $_ -like '| Planet load*' -or $_ -like '| Transition*' -or $_ -like '| Bundles*' -or $_ -like '| Sprite atlases*' -or $_ -like '| Return*' -or $_ -like '| Mip*' -or $_ -like '| Boot*' -or $_ -like '| Creep*' -or $_ -like '| Heap*' -or $_ -like '| Climb*' -or $_ -like '| Space first*' -or $_ -like '| GPU frame*' -or $_ -like '| Control*' -or $_ -like '| Living*' } | ForEach-Object { Write-Host $_ }
}

if ($SkipGate) { if ($memRed -or -not $buildOk) { Write-Host 'BUILD MEMORY RED'; exit 1 } else { Write-Host 'BUILD MEMORY GREEN'; exit (Complete-Release) } }
if (-not (Test-Path $xml)) { Write-Host 'PROFILE FAILED: no results file'; exit 1 }
[xml]$doc = Get-Content $xml -Raw
$passed = $doc.'test-run'.passed -eq '1'
if (Test-Path $report) { Write-Host "Report: $report" } else { Write-Host 'Report not written (test failed before the end)' }
if ($passed -and -not $memRed -and $buildOk) { Write-Host 'BUDGETGATE GREEN'; exit (Complete-Release) }
if ($passed) { Write-Host 'BUDGETGATE GREEN, BUILD MEMORY RED'; exit 1 }
$msg = $doc.SelectSingleNode('//test-case/failure/message')
Write-Host "BUDGETGATE RED: $($msg.InnerText)"
exit 1
