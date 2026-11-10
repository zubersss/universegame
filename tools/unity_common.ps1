# Shared helpers for tools/unity_*.ps1 (dot-source this file). Owner: UNITY.
$ErrorActionPreference = 'Stop'

$script:RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$script:LogDir = Join-Path $RepoRoot 'logs'
$script:LockDir = Join-Path $RepoRoot 'coordination\locks'
$script:LockFile = Join-Path $LockDir 'heavy_unity.lock'
New-Item -ItemType Directory -Force $LogDir | Out-Null
New-Item -ItemType Directory -Force $LockDir | Out-Null

function Get-UnityExe {
    $file = Join-Path $RepoRoot 'tools\paths.json'
    if (-not (Test-Path $file)) { throw 'tools/paths.json missing (LEAD writes it).' }
    $raw = Get-Content $file -Raw
    $exe = $null
    try { $exe = ($raw | ConvertFrom-Json).unityExe } catch {
        # paths.json may hold unescaped Windows backslashes; read the value directly.
        if ($raw -match '"unityExe"\s*:\s*"([^"]+)"') { $exe = $Matches[1] -replace '\\\\', '\' }
    }
    if (-not $exe -or -not (Test-Path $exe)) { throw "unityExe not found: $exe" }
    return $exe
}

function Test-UnityEditorRunning {
    # Unity Hub ships its own 'unity.exe serve'; only the Editor binary counts (CLAUDE.md rule 6, D-015).
    $editor = Get-Process unity -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*\Hub\Editor\*' }
    return [bool]$editor
}

# D-026 fair turns + memory gate (CLAUDE.md rule 6).
$script:WantFile = Join-Path $LockDir 'want_unity.lock'
$script:ReleaseStamp = Join-Path $LogDir 'unity_last_release.txt'
$script:MinFreeGB = 1.5
# D-156 (one-off gates, LEAD-ruled): MERIDIAN_RAM_GATE_MB lowers the gate for one run; MERIDIAN_WATCH_CAP_MB stops the Editor if its working
# set summed with every worker it spawned (import, bee) passes the cap (MERIDIAN_WATCH_FLOOR_MB: or free RAM falls under the floor); the peak is logged to logs/unity_peaks.log. Unset: unchanged.
if ($env:MERIDIAN_RAM_GATE_MB) { $script:MinFreeGB = [math]::Round([double]$env:MERIDIAN_RAM_GATE_MB / 1024, 2) }
# D-037 replaced the 2-minute yield window: UNITY waits for every older request (see Enter-HeavyJobLock).
$script:WantMaxAgeMinutes = 30      # want files older than this are ignored
$script:MaxJobMinutes = 20          # one heavy job holds the lock at most this long

function Get-FreeMemoryGB {
    return [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
}

# LEAD 18:5x (2026-11-09): on this 7.6 GB machine a perf row cannot be judged without the memory beside it. Free RAM, the size of
# Windows' compression store and the largest private holders (an idle "ollama app" held 4.2 GB all day; how much of it was compressed
# differed from run to run). Every perf wrapper prints it at its start and its end.
function Get-MemoryNote {
    $store = Get-Process -Name 'Memory Compression' -ErrorAction SilentlyContinue | Select-Object -First 1
    $storeMb = if ($store) { [math]::Round($store.WorkingSet64 / 1MB) } else { 0 }
    $big = Get-Process | Sort-Object PrivateMemorySize64 -Descending | Select-Object -First 4 | ForEach-Object { "$($_.ProcessName) $([math]::Round($_.PrivateMemorySize64 / 1MB)) MB" }
    # LEAD 19:2x: the machine's uptime and the minutes since the last heavy job's log was written (if a slow reading tracks heat, here)
    $up = [math]::Round(((Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime).TotalHours, 1)
    $last = Get-ChildItem $LogDir -Filter 'unity_*.log' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $since = if ($last) { [math]::Round(((Get-Date) - $last.LastWriteTime).TotalMinutes, 1) } else { -1 }
    return "free $(Get-FreeMemoryGB) GB, compression store $storeMb MB, largest private: $($big -join ', '); up $up h, $since min since the last Unity job's log"
}

function Write-Want([string]$job) {
    # D-039 guard (LEAD cycle 159): never file a want while UNITY still holds the lock, and after UNITY's own
    # job never file one while another role's want is waiting: that role goes first, and UNITY files only once
    # its heavy lock appears (its want is gone then). Without a want UNITY still retries and yields (D-037).
    if (Test-Path $LockFile) { return }
    if ((Get-OtherWants).Count -gt 0 -and (Get-LastRelease) -gt (Get-Date).AddMinutes(-$WantMaxAgeMinutes)) { return }
    if (-not (Test-Path $WantFile)) { "$((Get-Date).ToString('s')) $job" | Set-Content -Encoding utf8 $WantFile }
}

function Get-OtherWants {
    $cutoff = (Get-Date).AddMinutes(-$WantMaxAgeMinutes)
    return @(Get-ChildItem $LockDir -Filter 'want_*.lock' -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne 'want_unity.lock' -and $_.LastWriteTime -gt $cutoff })
}

# U-143: the game version (GameInfo.Version) and the player folders: the release in Build\MERIDIAN_<v>\, the probed development build in Build\MERIDIAN_<v>_dev\.
function Get-GameVersion {
    $m = Select-String -Path (Join-Path $RepoRoot 'Assets\_Game\Code\Runtime\GameInfo.cs') -Pattern 'Version = "([^"]+)"'
    if (-not $m) { return '' }
    return $m.Matches[0].Groups[1].Value
}
function Get-PlayerExe([string]$Version, [switch]$Dev) {
    $suffix = if ($Dev) { '_dev' } else { '' }
    return Join-Path $RepoRoot ("Build\MERIDIAN_{0}{1}\MERIDIAN.exe" -f $Version, $suffix)
}

function Get-LastRelease {
    if (-not (Test-Path $ReleaseStamp)) { return [datetime]::MinValue }
    try { return [datetime]::Parse((Get-Content $ReleaseStamp -Raw).Trim()) } catch { return [datetime]::MinValue }
}

# Throws (after writing want_unity.lock) when UNITY must wait; on success holds heavy_unity.lock.
function Enter-HeavyJobLock([string]$job) {
    if ($env:MERIDIAN_LOCK_HELD -eq '1') { return } # inside unity_check.ps1: the outer call holds the lock (D-037)
    $cutoff = (Get-Date).AddHours(-2)
    foreach ($l in Get-ChildItem $LockDir -Filter 'heavy_*.lock' -ErrorAction SilentlyContinue) {
        if ($l.Name -ne 'heavy_unity.lock' -and $l.LastWriteTime -gt $cutoff) {
            Write-Want $job
            throw "HeavyJobLock held by $($l.Name): $(Get-Content $l.FullName -Raw)"
        }
    }
    if (Test-UnityEditorRunning) { Write-Want $job; throw 'Unity Editor is running; batch jobs cannot open the project.' }
    $blender = Get-Process blender -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*Blender Foundation*' }
    if ($blender) { Write-Want $job; throw 'blender.exe is running (HeavyJobLock).' }

    # D-037 strict turns: a waiting role whose request is older than ours (or we have none) goes first,
    # until it has taken the lock (it deletes its want file then). Equal turns: the older request wins.
    $mine = if (Test-Path $WantFile) { (Get-Item $WantFile).LastWriteTime } else { Get-Date }
    $ahead = @(Get-OtherWants | Where-Object { $_.LastWriteTime -le $mine })
    if ($ahead.Count -gt 0) {
        Write-Want $job
        throw "yielding to $($ahead[0].Name) (filed $($ahead[0].LastWriteTime.ToString('HH:mm:ss')), before UNITY's request; D-037)"
    }
    $free = Get-FreeMemoryGB
    if ($free -lt $MinFreeGB) {
        Write-Want $job
        throw "only $free GB free RAM (< $MinFreeGB GB; D-026)"
    }
    "$((Get-Date).ToString('s')) $job" | Set-Content -Encoding utf8 $LockFile
    Remove-Item $WantFile -Force -ErrorAction SilentlyContinue
}

function Exit-HeavyJobLock {
    if ($env:MERIDIAN_LOCK_HELD -eq '1') { return }
    Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
    (Get-Date).ToString('o') | Set-Content -Encoding utf8 $ReleaseStamp
}

# Gives up waiting: drops want_unity.lock so other roles aren't held back by a stale request.
function Clear-HeavyJobWant { Remove-Item $WantFile -Force -ErrorAction SilentlyContinue }

# D-156: a process and every descendant (one CIM snapshot): the root's working set, the tree's summed, and the descendants (to stop them).
function Get-ProcessTree([int]$RootId) {
    $procs = @(Get-CimInstance Win32_Process -Property ProcessId, ParentProcessId, WorkingSetSize -ErrorAction SilentlyContinue)
    $root = $procs | Where-Object { $_.ProcessId -eq $RootId } | Select-Object -First 1
    $kids = New-Object System.Collections.Generic.List[object]
    $frontier = @($RootId)
    while ($frontier.Count -gt 0 -and $kids.Count -le 64) {
        $next = @($procs | Where-Object { $frontier -contains $_.ParentProcessId -and $_.ProcessId -ne $RootId })
        foreach ($k in $next) { $kids.Add($k) }
        $frontier = @($next | ForEach-Object { $_.ProcessId })
    }
    $rootMB = if ($root) { [int]($root.WorkingSetSize / 1MB) } else { 0 }
    $treeMB = $rootMB + [int](($kids | Measure-Object -Property WorkingSetSize -Sum).Sum / 1MB)
    return [pscustomobject]@{ RootMB = $rootMB; TreeMB = $treeMB; Kids = $kids }
}

function Invoke-UnityBatch([string[]]$UnityArgs, [string]$LogName, [switch]$Graphics) {
    $exe = Get-UnityExe
    $log = Join-Path $LogDir $LogName
    $all = @('-batchmode')
    if (-not $Graphics) { $all += '-nographics' }
    $all += @('-projectPath', $RepoRoot, '-logFile', $log) + $UnityArgs
    $p = Start-Process -FilePath $exe -ArgumentList $all -PassThru -NoNewWindow
    $null = $p.Handle # cache the handle, or ExitCode reads back empty after WaitForExit
    if ($env:MERIDIAN_WATCH_CAP_MB) {
        # D-156 watchdog (LEAD 20:5x): poll each second; stop the Editor and its workers when the WHOLE tree (the Editor + every descendant,
        # summed) passes the cap or free RAM falls under the floor; log the peaks.
        $cap = [int]$env:MERIDIAN_WATCH_CAP_MB
        $floor = if ($env:MERIDIAN_WATCH_FLOOR_MB) { [int]$env:MERIDIAN_WATCH_FLOOR_MB } else { 0 }
        $peak = 0; $treePeak = 0; $minFree = [int]::MaxValue; $why = $null
        $until = (Get-Date).AddMinutes($MaxJobMinutes)
        while (-not $p.WaitForExit(1000)) {
            $t = Get-ProcessTree $p.Id
            $ws = $t.RootMB; $tree = $t.TreeMB; $kids = $t.Kids
            $free = [int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024)
            if ($ws -gt $peak) { $peak = $ws }; if ($tree -gt $treePeak) { $treePeak = $tree }; if ($free -lt $minFree) { $minFree = $free }
            if ($tree -gt $cap) { $why = "the Editor with its workers at $tree MB (the Editor $ws MB) passed the $cap MB cap" }
            elseif ($floor -gt 0 -and $free -lt $floor) { $why = "free RAM fell to $free MB (< $floor MB)" }
            elseif ((Get-Date) -gt $until) { $why = "over $MaxJobMinutes min (D-026)" }
            if ($why) {
                foreach ($k in $kids) { Stop-Process -Id $k.ProcessId -Force -ErrorAction SilentlyContinue }
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
                break
            }
        }
        $line = "{0} {1} | Editor peak {2} MB, with its workers {3} MB, min free {4} MB | tree cap {5} MB{6}" -f (Get-Date).ToString("s"), $LogName, $peak, $treePeak, $minFree, $cap, $(if ($why) { " | STOPPED: $why" } else { "" })
        Add-Content -Path (Join-Path $LogDir "unity_peaks.log") -Value $line
        Write-Host "[watchdog] $line"
        if ($why) { Write-Host "WATCHDOG STOP (D-156): $why"; return [pscustomobject]@{ ExitCode = 137; Log = $log } }
        return [pscustomobject]@{ ExitCode = $p.ExitCode; Log = $log }
    }
    # D-026: one heavy job holds the lock at most 20 min.
    if (-not $p.WaitForExit($MaxJobMinutes * 60 * 1000)) {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Write-Host "TIMEOUT: Unity batch exceeded $MaxJobMinutes min and was stopped (D-026)."
        return [pscustomobject]@{ ExitCode = 124; Log = $log }
    }
    return [pscustomobject]@{ ExitCode = $p.ExitCode; Log = $log }
}

function Get-CompileErrors([string]$log) {
    if (-not (Test-Path $log)) { return @('log missing') }
    return @(Select-String -Path $log -Pattern 'error CS\d+' | ForEach-Object { $_.Line.Trim() } | Sort-Object -Unique)
}

function Get-CompileWarnings([string]$log) {
    if (-not (Test-Path $log)) { return @() }
    return @(Select-String -Path $log -Pattern 'warning CS\d+' | ForEach-Object { $_.Line.Trim() } |
        Where-Object { $_ -match 'Assets[\\/]_Game' } | Sort-Object -Unique)
}
