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
} elseif ($Target.Contains(',')) {
    # Comma-separated asset keys: one Blender process, one lock hold (one job under D-037).
    $keys = @($Target.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    $missing = @($keys | Where-Object { $k = $_; -not ($assets | Where-Object { $_.key -eq $k }) })
    if ($missing.Count -gt 0) { Fail 2 "unknown asset key(s): $($missing -join ', ')" }
    $jobs += , @{ Name = "$($keys.Count) assets"; Args = @('--asset', ($keys -join ',')); Chosen = @($assets | Where-Object { $keys -contains $_.key }) }
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
$stamp = Join-Path $Root 'blender/preview/last_heavy.txt'      # end time of BLENDER's last heavy job (gitignored)
# D-033: flat sprite categories render on Cycles CPU (render.py) and may run at >= 1.0 GB free.
$cyclesCpu = @('props', 'creatures', 'characters', 'ships', 'icons')

function Test-Heavy($chosen) {
    if ($Preview) { return $false }
    if ($chosen.Count -gt 1) { return $true }
    foreach ($a in $chosen) { if ($a.model) { return $true } }   # v2 models: Cycles bakes + Eevee turntable
    foreach ($a in $chosen) { if ($a.style -eq 'v3') { return $true } }   # D-091: v3 sheet/rig batches are heavy (previews stay light)
    foreach ($a in $chosen) {
        if ($a.size -and (($a.size | Measure-Object -Maximum).Maximum -gt 512)) { return $true }
        if ($a.animations) { return $true }      # a frame sheet is a batch of renders
    }
    return $false
}

# D-045: numpy-only generators (no scene render; measured whole-process peak <= 1.0 GB) may
# run at >= 1.2 GB free with a 0.3 GB watchdog. An explicit list: gen_backdrop3d is also a
# "generator" but renders EEVEE scenes, so "generator, no source" alone is not enough.
# build_title.py measured 1015-1033 MB whole-process (full-frame float compositing) -> over 1.0 GB, excluded.
$numpyGenerators = @('scripts/gen_fx.py')

function Test-NumpyOnly($chosen) {
    if ($chosen.Count -eq 0) { return $false }
    foreach ($a in $chosen) {
        # Listed generator, or an entry the manifest marks "numpy_only" (e.g. gen_backdrop3d banks presets,
        # gen_terrain: measured 0.53-0.68 GB, no scene opened).
        if ($a.source -or -not $a.generator -or (($numpyGenerators -notcontains $a.generator) -and -not $a.numpy_only)) { return $false }
    }
    return $true
}

function Get-GateMB($chosen) {
    # D-033's 1.0 GB gate for Cycles-CPU sprites was conditional on a peak <= 0.6 GB. Measured
    # 2026-10-31: 1.41-1.45 GB (Blender baseline dominates), so per D-033 every heavy job is
    # back on the D-026 1.5 GB gate. Cycles CPU stays for sprites (no GPU-texture crash risk).
    if (Test-NumpyOnly $chosen) { return 1200 }                 # D-045
    foreach ($a in $chosen) { if ($a.model -and -not $a.atlas -and [int]$a.texture -ge 2048) { return 2000 } }   # D-066: 2048^2 bakes peak 1.77-1.89 GB (atlas models do not bake)
    return 1500
}

function Request-Heavy($job) {
    # Returns $null when acquired, else the reason. While refused, want_blender.lock stays.
    $cutoff = (Get-Date).AddHours(-2)
    $others = Get-ChildItem $locks -Filter 'heavy_*.lock' -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne 'heavy_blender.lock' -and $_.LastWriteTime -gt $cutoff }
    $procs = Get-Process unity, blender -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -like '*\Hub\Editor\*' -or $_.Path -like '*Blender Foundation*' }
    # D-059 turn guard (strict turns, D-037): if BLENDER finished a heavy job within the last
    # 30 min and another role's want is younger than 30 min, that role goes next. Refuse WITHOUT
    # filing want_blender.lock (D-039: no re-filing right after your own job).
    $recentRun = (Test-Path $stamp) -and ((Get-Item $stamp).LastWriteTime -gt (Get-Date).AddMinutes(-30))
    $waiting = Get-ChildItem $locks -Filter 'want_*.lock' -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne 'want_blender.lock' -and $_.LastWriteTime -gt (Get-Date).AddMinutes(-30) }
    # Exception: my own want was filed after my last job (I waited through another role's turn,
    # D-039) and before every other want -> it's my turn under D-037, even if they re-filed.
    $myWant = Get-Item $want -ErrorAction SilentlyContinue
    $waitedMyTurn = $myWant -and $recentRun -and $waiting -and
        ($myWant.LastWriteTime -gt (Get-Item $stamp).LastWriteTime) -and
        -not ($waiting | Where-Object { $_.LastWriteTime -le $myWant.LastWriteTime })
    if ($recentRun -and $waiting -and -not $waitedMyTurn) {
        return "turn guard (D-059): $($waiting.Name -join ', ') waiting and BLENDER ran at $((Get-Item $stamp).LastWriteTime.ToString('HH:mm:ss')); their turn"
    }
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
        if ($heavy -and (Test-NumpyOnly $job.Chosen)) {
            # D-045 watchdog: poll free RAM while the job runs; stop it under 0.3 GB.
            $out = Join-Path $env:TEMP "blender_render_$PID.log"
            $argList = @('--background', '--factory-startup', '--python-exit-code', '1', '--python', "`"$script`"", '--') + $pyArgs
            $p = Start-Process -FilePath $blender -ArgumentList $argList -NoNewWindow -PassThru -RedirectStandardOutput $out
            $killed = $false
            while (-not $p.HasExited) {
                Start-Sleep -Milliseconds 1000
                $f = [int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024)
                if ($f -lt 300) { Stop-Process -Id $p.Id -Force; $killed = $true; break }
            }
            $p.WaitForExit()
            Get-Content $out -ErrorAction SilentlyContinue |
                ForEach-Object { if ($_ -match '^(MERIDIAN |Traceback|  File |\w+Error)') { Write-Host $_ } }
            Remove-Item $out -ErrorAction SilentlyContinue
            if ($killed) { Write-Host "blender_render: STOPPED '$($job.Name)': free RAM fell under 300 MB (D-045 watchdog)"; $code = 4 }
            elseif ($p.ExitCode -ne 0) { $code = $p.ExitCode }
        } else {
            & $blender --background --factory-startup --python-exit-code 1 --python $script -- @pyArgs |
                ForEach-Object { if ($_ -match '^(MERIDIAN |Traceback|  File |\w+Error)') { Write-Host $_ } }
            if ($LASTEXITCODE -ne 0) { $code = $LASTEXITCODE }
        }
    } finally {
        if ($heavy -and (Test-Path $lock)) {
            Remove-Item $lock -Force
            Set-Content -Path $stamp -Value "$((Get-Date).ToString('s')) $($job.Name)" -Encoding utf8   # D-059 turn guard
        }
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
