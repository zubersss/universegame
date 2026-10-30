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
$script:YieldWindowMinutes = 2      # after releasing, UNITY yields to a waiting role for this long
$script:WantMaxAgeMinutes = 30      # want files older than this are ignored
$script:MaxJobMinutes = 20          # one heavy job holds the lock at most this long

function Get-FreeMemoryGB {
    return [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
}

function Write-Want([string]$job) {
    if (-not (Test-Path $WantFile)) { "$((Get-Date).ToString('s')) $job" | Set-Content -Encoding utf8 $WantFile }
}

function Get-OtherWants {
    $cutoff = (Get-Date).AddMinutes(-$WantMaxAgeMinutes)
    return @(Get-ChildItem $LockDir -Filter 'want_*.lock' -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne 'want_unity.lock' -and $_.LastWriteTime -gt $cutoff })
}

function Get-LastRelease {
    if (-not (Test-Path $ReleaseStamp)) { return [datetime]::MinValue }
    try { return [datetime]::Parse((Get-Content $ReleaseStamp -Raw).Trim()) } catch { return [datetime]::MinValue }
}

# Throws (after writing want_unity.lock) when UNITY must wait; on success holds heavy_unity.lock.
function Enter-HeavyJobLock([string]$job) {
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

    $wants = Get-OtherWants
    $sinceRelease = ((Get-Date) - (Get-LastRelease)).TotalMinutes
    if ($wants.Count -gt 0 -and $sinceRelease -lt $YieldWindowMinutes) {
        Write-Want $job
        throw "yielding to $($wants[0].Name) (UNITY released the lock $([math]::Round($sinceRelease, 1)) min ago; D-026)"
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
    Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
    (Get-Date).ToString('o') | Set-Content -Encoding utf8 $ReleaseStamp
}

# Gives up waiting: drops want_unity.lock so other roles aren't held back by a stale request.
function Clear-HeavyJobWant { Remove-Item $WantFile -Force -ErrorAction SilentlyContinue }

function Invoke-UnityBatch([string[]]$UnityArgs, [string]$LogName, [switch]$Graphics) {
    $exe = Get-UnityExe
    $log = Join-Path $LogDir $LogName
    $all = @('-batchmode')
    if (-not $Graphics) { $all += '-nographics' }
    $all += @('-projectPath', $RepoRoot, '-logFile', $log) + $UnityArgs
    $p = Start-Process -FilePath $exe -ArgumentList $all -PassThru -NoNewWindow
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
