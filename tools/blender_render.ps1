<#
.SYNOPSIS
  Render MERIDIAN art: tools/blender_render.ps1 <key|category|all> [-Preview]
.DESCRIPTION
  Wraps: blender --background --factory-startup --python blender/render.py -- --asset|--category|--all [--preview]
  A key has three parts (props/common/calibration); one or two parts is a category prefix.
  Full renders above 512 px or of more than one asset are heavy jobs: they honor
  HeavyJobLock (CLAUDE.md rule 6) and refuse to start while Unity's Editor or another
  Blender runs, or below 1.5 GB free RAM (D-026). Exit codes: 0 ok, 1 render/contract
  failure, 2 bad usage, 3 HeavyJobLock busy (lock, process or memory gate).
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

# Resolve the target against the manifest to decide whether this is a heavy job.
$manifest = Get-Content (Join-Path $Root 'blender/manifest.json') -Raw | ConvertFrom-Json
$assets = @($manifest.assets)
if ($Target -eq 'all') {
    $pyArgs = @('--all'); $chosen = $assets
} elseif (($Target.ToCharArray() | Where-Object { $_ -eq '/' }).Count -eq 2) {
    $pyArgs = @('--asset', $Target); $chosen = @($assets | Where-Object { $_.key -eq $Target })
} else {
    $pre = $Target.Trim('/')
    $pyArgs = @('--category', $pre); $chosen = @($assets | Where-Object { $_.key -eq $pre -or $_.key.StartsWith("$pre/") })
}
if ($Preview) { $pyArgs += '--preview' }

$heavy = $false
if (-not $Preview) {
    if ($chosen.Count -gt 1) { $heavy = $true }
    foreach ($a in $chosen) {
        if ($a.size -and (($a.size | Measure-Object -Maximum).Maximum -gt 512)) { $heavy = $true }
        if ($a.animations) { $heavy = $true }   # a frame sheet is a batch of renders
    }
}

$lock = Join-Path $Root 'coordination/locks/heavy_blender.lock'
if ($heavy) {
    $cutoff = (Get-Date).AddHours(-2)
    $others = Get-ChildItem (Join-Path $Root 'coordination/locks') -Filter 'heavy_*.lock' -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne 'heavy_blender.lock' -and $_.LastWriteTime -gt $cutoff }
    if ($others) { Fail 3 "HeavyJobLock busy: $($others.Name -join ', ')" }
    $procs = Get-Process unity, blender -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -like '*\Hub\Editor\*' -or $_.Path -like '*Blender Foundation*' }
    if ($procs) { Fail 3 "HeavyJobLock busy: running $(($procs | ForEach-Object { $_.ProcessName }) -join ', ')" }
    # D-026 memory gate: no heavy job below 1.5 GB free RAM.
    $freeMB = [int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024)
    if ($freeMB -lt 1500) { Fail 3 "HeavyJobLock memory gate: $freeMB MB free (< 1500, D-026)" }
    Set-Content -Path $lock -Value "$((Get-Date).ToString('s')) blender_render $Target" -Encoding utf8
}

try {
    $script = Join-Path $Root 'blender/render.py'
    & $blender --background --factory-startup --python-exit-code 1 --python $script -- @pyArgs |
        ForEach-Object { if ($_ -match '^(MERIDIAN |Traceback|  File |\w+Error)') { Write-Host $_ } }
    $code = $LASTEXITCODE
} finally {
    if ($heavy -and (Test-Path $lock)) { Remove-Item $lock -Force }
}
exit $code
