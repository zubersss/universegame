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

function Enter-HeavyJobLock([string]$job) {
    $cutoff = (Get-Date).AddHours(-2)
    foreach ($l in Get-ChildItem $LockDir -Filter 'heavy_*.lock' -ErrorAction SilentlyContinue) {
        if ($l.Name -ne 'heavy_unity.lock' -and $l.LastWriteTime -gt $cutoff) {
            throw "HeavyJobLock held by $($l.Name): $(Get-Content $l.FullName -Raw)"
        }
    }
    if (Test-UnityEditorRunning) { throw 'Unity Editor is running; batch jobs cannot open the project.' }
    $blender = Get-Process blender -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*Blender Foundation*' }
    if ($blender) { throw 'blender.exe is running (HeavyJobLock).' }
    "$((Get-Date).ToString('s')) $job" | Set-Content -Encoding utf8 $LockFile
}

function Exit-HeavyJobLock { Remove-Item $LockFile -Force -ErrorAction SilentlyContinue }

function Invoke-UnityBatch([string[]]$UnityArgs, [string]$LogName) {
    $exe = Get-UnityExe
    $log = Join-Path $LogDir $LogName
    $all = @('-batchmode', '-nographics', '-projectPath', $RepoRoot, '-logFile', $log) + $UnityArgs
    $p = Start-Process -FilePath $exe -ArgumentList $all -Wait -PassThru -NoNewWindow
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
