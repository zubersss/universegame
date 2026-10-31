<#
.SYNOPSIS
  Render MERIDIAN art: tools/blender_render.ps1 <key|category|all> [-Preview]
.DESCRIPTION
  Wraps: blender --background --factory-startup --python blender/render.py -- --asset|--category|--all [--preview]
  A key has three parts (props/common/calibration); one or two parts is a category prefix.
  Full renders above 512 px or of more than one asset are heavy jobs: they honor
  HeavyJobLock (CLAUDE.md rule 6) and refuse to start while Unity's Editor or another
  Blender runs, or below the memory gate: 1.0 GB free for Cycles-CPU sprite categories
  (D-033), 1.5 GB otherwise (D-026). While refused it leaves coordination/locks/want_blender.lock
  so UNITY can see BLENDER is waiting, and deletes it on acquire (B-024). `all` runs one
  Blender process per category and yields to a fresh want_unity.lock between them.
  Exit codes: 0 ok, 1 render/contract failure, 2 bad usage, 3 busy / gated / yielded.
#>
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$Target,
    [switch]$Preview
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot

function Fail([int]$code, [string]$msg) { Write-Host "blender_render: $msg"; exit $code }

# tools/paths.json (LEAD's file). Tolerate unescaped Windows backslashes.
$pathsFile = Join-Path $Root 'tools/paths.json'
if (-not (Test-Path $pathsFile)) { Fail 2 'tools/paths.json missing' }
$rawPaths = Get-Content $pathsFile -Raw
try { $paths = $rawPaths | ConvertFrom-Json }
catch { $paths = ($rawPaths -replace '(?<!\\)\\(?![\\"])', '\\') | ConvertFrom-Json }
$blender = $paths.blenderExe
if (-not $blender -or -not (Test-Path $blender)) { Fail 2 "blenderExe not found: '$blender'" }

# Resolve the target into jobs. `all` is split by category: one Blender process per category,
# so no single job runs long (D-026: <= 20 min) and BLENDER can yield to UNITY between them.
$manifest = Get-Content (Join-Path $Root 'blender/manifest.json') -Raw | ConvertFrom-Json
$assets = @($manifest.assets)
$jobs = @()
if ($Target -eq 'all') {
    foreach ($cat in ($assets | ForEach-Object { $_.key.Split('/')[0] } | Select-Object -Unique)) {
        $jobs += , @{ Name = $cat; Args = @('--category', $cat); Chosen = @($assets | Where-Object { $_.key.StartsWith("$cat/") }) }
    }
} elseif (($Target.ToCharArray() | Where-Object { $_ -eq '/' }).Count -eq 2) {
    $jobs += , @{ Name = $Target; Args = @('--asset', $Target); Chosen = @($assets | Where-Object { $_.key -eq $Target }) }
} else {
    $pre = $Target.Trim('/')
    $jobs += , @{ Name = $pre; Args = @('--category', $pre); Chosen = @($assets | Where-Object { $_.key -eq $pre -or $_.key.StartsWith("$pre/") }) }
}
if ($jobs.Count -eq 0) { $jobs += , @{ Name = $Target; Args = @('--all'); Chosen = @() } }

$locks = Join-Path $Root 'coordination/locks'
$lock = Join-Path $locks 'heavy_blender.lock'
$want = Join-Path $locks 'want_blender.lock'
# D-033: flat sprite categories render on Cycles CPU (render.py) and may run at >= 1.0 GB free.
$cyclesCpu = @('props', 'creatures', 'characters', 'ships', 'icons')

function Test-Heavy($chosen) {
    if ($Preview) { return $false }
    if ($chosen.Count -gt 1) { return $true }
    foreach ($a in $chosen) {
        if ($a.size -and (($a.size | Measure-Object -Maximum).Maximum -gt 512)) { return $true }
        if ($a.animations) { return $true }      # a frame sheet is a batch of renders
    }
    return $false
}

function Get-GateMB($chosen) {
    # D-033's 1.0 GB gate for Cycles-CPU sprites was conditional on a peak <= 0.6 GB. Measured
    # 2026-10-31: 1.41-1.45 GB (Blender baseline dominates), so per D-033 every heavy job is
    # back on the D-026 1.5 GB gate. Cycles CPU stays for sprites (no GPU-texture crash risk).
    return 1500
}

function Request-Heavy($job) {
    # Returns $null when acquired, else the reason. While refused, want_blender.lock stays.
    $cutoff = (Get-Date).AddHours(-2)
    $others = Get-ChildItem $locks -Filter 'heavy_*.lock' -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne 'heavy_blender.lock' -and $_.LastWriteTime -gt $cutoff }
    $procs = Get-Process unity, blender -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -like '*\Hub\Editor\*' -or $_.Path -like '*Blender Foundation*' }
    $freeMB = [int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024)
    $gate = Get-GateMB $job.Chosen
    $reason = $null
    if ($others) { $reason = "HeavyJobLock busy: $($others.Name -join ', ')" }
    elseif ($procs) { $reason = "HeavyJobLock busy: running $(($procs | ForEach-Object { $_.ProcessName }) -join ', ')" }
    elseif ($freeMB -lt $gate) { $reason = "HeavyJobLock memory gate: $freeMB MB free (< $gate)" }
    if ($reason) {
        Set-Content -Path $want -Value "$((Get-Date).ToString('s')) blender waiting: $Target" -Encoding utf8
        return $reason
    }
    if (Test-Path $want) { Remove-Item $want -Force }        # acquired: stop signalling
    Set-Content -Path $lock -Value "$((Get-Date).ToString('s')) blender_render $($job.Name) (gate $gate MB, free $freeMB MB)" -Encoding utf8
    return $null
}

$script = Join-Path $Root 'blender/render.py'
$code = 0
for ($i = 0; $i -lt $jobs.Count; $i++) {
    $job = $jobs[$i]
    $heavy = Test-Heavy $job.Chosen
    if ($heavy) {
        $why = Request-Heavy $job
        if ($why) { Fail 3 $why }
    }
    $pyArgs = $job.Args + $(if ($Preview) { @('--preview') } else { @() })
    $t0 = Get-Date
    try {
        & $blender --background --factory-startup --python-exit-code 1 --python $script -- @pyArgs |
            ForEach-Object { if ($_ -match '^(MERIDIAN |Traceback|  File |\w+Error)') { Write-Host $_ } }
        if ($LASTEXITCODE -ne 0) { $code = $LASTEXITCODE }
    } finally {
        if ($heavy -and (Test-Path $lock)) { Remove-Item $lock -Force }
    }
    $mins = ((Get-Date) - $t0).TotalMinutes
    if ($mins -gt 20) { Write-Host ("blender_render: job '{0}' took {1:N1} min (> 20, D-026); split it further" -f $job.Name, $mins) }
    # Fairness (D-026): after each job, yield to a waiting UNITY if more jobs remain.
    $wantUnity = Get-Item (Join-Path $locks 'want_unity.lock') -ErrorAction SilentlyContinue
    if ($heavy -and $i -lt $jobs.Count - 1 -and $wantUnity -and $wantUnity.LastWriteTime -gt (Get-Date).AddMinutes(-30)) {
        Set-Content -Path $want -Value "$((Get-Date).ToString('s')) blender waiting: $Target (yielded after $($job.Name))" -Encoding utf8
        Fail 3 "yielded to UNITY after '$($job.Name)'; re-run to continue"
    }
}
exit $code
