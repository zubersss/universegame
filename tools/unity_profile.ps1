# BudgetGate profile run (U-014): runs BudgetGateTests with graphics and writes
# coordination/reports/unity/perf_<date>.md with every Bible section 11.1 row. Owner: UNITY.
# -Build (U-041, D-036): also builds the development player and runs its memory probe
# (Earth, Space, Mars, Mercury, Venus) under the same lock, adding "dev build" rows to the report.
# -Probe (U-086): runs the probe on the player already in Build/ without rebuilding it.
# The Editor's memory rows stay as an upper bound. Limits are Bible 11.1 v3 (D-077).
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
            if (-not $p.WaitForExit(300000)) { Stop-Process -Id $p.Id -Force; Write-Host 'PROBE TIMED OUT (5 min)'; $buildOk = $false }
            Write-Host "Player log: $playerLog"
        }
    }
} finally {
    Remove-Item Env:\MERIDIAN_PROFILE_REPORT -ErrorAction SilentlyContinue
    Exit-HeavyJobLock
}

# ---- dev-build rows (U-041; v3 limits U-086, D-077) ----
$memRed = $false
# Report symbols as code points (tools/*.ps1 stay ASCII).
$le = [char]0x2264; $ar = [char]0x2192; $times = [char]0x00D7; $sec = [char]0x00A7; $dot = [char]0x00B7
$limit = "$le 4.5 GB working set (warn 4.0), $le 2.0 GB textures, $le 600 MB meshes, $le 150 MB audio"
if ($runProbe) {
    $rows = @('', '## Memory in the development player (U-041, D-036; limits v3, D-077)', '',
        "The route Earth $ar launch $ar Space $ar entry $ar Mars, then Mercury and Venus loaded directly (U-060), in Build/MERIDIAN_<version>/MERIDIAN.exe (development build), 1920${times}1080 windowed; counters read after 120 frames per leg. Working set from the OS (ProcessMemory); the Editor rows above stay as an upper bound.", '',
        "| Row | Budget (${sec}11.1 v3) | Measured | Status |", '|---|---|---|---|')
    $legs = @()
    if ($buildOk -and (Test-Path $probeOut)) { $legs = @(Get-Content $probeOut | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json } | Where-Object { $null -ne $_.systemMB }) }
    if ($legs.Count -eq 0) { $rows += "| Memory $dot dev build | $limit | no probe result (build or probe failed) | red |"; $memRed = $true }
    foreach ($l in $legs) {
        if ($l.error) { $rows += "| Memory $dot dev build | | probe error: $($l.error) | red |"; $memRed = $true; continue }
        $ws = if ($l.workingSetMB -gt 0) { [long]$l.workingSetMB } else { [long]$l.systemMB }
        $meshOk = ($null -eq $l.meshMB) -or ($l.meshMB -lt 0) -or ($l.meshMB -le 600)
        $ok = ($ws -ge 0) -and ($ws -le 4608) -and ($l.textureMB -le 2048) -and $meshOk -and ($l.audioMB -le 150)
        if (-not $ok) { $memRed = $true }
        $status = if (-not $ok) { 'red' } elseif ($ws -gt 4096) { 'green (above the 4.0 GB warning line)' } else { 'green' }
        $wsText = if ($l.workingSetMB -gt 0) { "working set $($l.workingSetMB) MB, system $($l.systemMB) MB" } else { "system $($l.systemMB) MB (working set n/a: judged on system memory)" }
        $meshText = if ($null -ne $l.meshMB -and $l.meshMB -ge 0) { ", meshes $($l.meshMB) MB" } else { ", meshes n/a (old player)" }
        $rows += "| Memory $dot $($l.leg) (dev build) | $limit | $wsText, textures $($l.textureMB) MB$meshText, audio $($l.audioMB) MB | $status |"
        if ($l.prevGroup) {
            $resOk = ([int]$l.prevHandles -eq 0)
            if (-not $resOk) { $memRed = $true }
            $rows += "| Residency $dot $($l.leg) (dev build) | previous planet released within 5 s (v3) | $($l.prevGroup) handles $($l.prevHandles) after $($l.prevWait) s (holders: $($l.holders)); resident: $($l.resident) | $(if ($resOk) { 'green' } else { 'red' }) |"
        }
    }
    if (Test-Path $report) {
        $text = Get-Content $report -Raw -Encoding UTF8
        $cut = $text.IndexOf("`n## Memory in the development player")
        if ($cut -ge 0) { $text = $text.Substring(0, $cut) }
        Set-Content -Path $report -Value ($text.TrimEnd() + "`n" + ($rows -join "`n") + "`n") -Encoding UTF8 -NoNewline
    } else {
        Set-Content -Path $report -Value (($rows -join "`n") + "`n") -Encoding UTF8 -NoNewline
    }
    $rows | Where-Object { $_ -like '| Memory*' -or $_ -like '| Residency*' } | ForEach-Object { Write-Host $_ }
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
