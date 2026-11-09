<#
.SYNOPSIS
  BLENDER's light / numpy run under heavy_blender.lock: tools/blender_locked.ps1 -Job "<what>" -PyArgs <script>,<args...>
.DESCRIPTION
  For review sheets and other scripts-only runs that tools/blender_render.ps1 does not wrap (CLAUDE.md rule 6, D-073, D-109):
    1. lists coordination/locks and aborts (exit 3) on any heavy_* / want_* file, another role's or a stale one of mine;
    2. aborts under -MinFreeGB of free physical memory (0.3 for light sheets; pass 1.5 for the painted sheets);
    3. writes coordination/locks/heavy_blender.lock (ISO time + the job);
    4. runs Blender's bundled python -I <PyArgs> from the repo root (no blender.exe, no bpy), with a working-set watchdog
       (-CapMB) and a timeout (-TimeoutSec; keep one lock <= 15 min);
    5. deletes the lock in `finally` and prints the lock times, the peak working set, the exit code and the output's tail.
  Read free RAM in its own call BEFORE this one (the gate is judged before a job is chosen); this script re-checks only the floor.
  No 2>&1 on it in PowerShell 5.1. Exit codes: the script's own, or 3 when refused.
.EXAMPLE
  tools/blender_locked.ps1 -Job "B-229 hints sheet" -PyArgs blender/scripts/build_hints_v3.py,blender/preview/review_b229_hints_preview.png -CapMB 600
#>
param(
    [Parameter(Mandatory = $true)][string]$Job,
    [Parameter(Mandatory = $true)][string[]]$PyArgs,
    [int]$CapMB = 300,
    [int]$TimeoutSec = 420,
    [double]$MinFreeGB = 0.3
)
$repo = Split-Path -Parent $PSScriptRoot
$locks = Join-Path $repo 'coordination\locks'
$mine = Join-Path $locks 'heavy_blender.lock'
$out = Join-Path $env:TEMP ("blender_locked_{0}.out" -f $PID)
$err = Join-Path $env:TEMP ("blender_locked_{0}.err" -f $PID)

# Blender's own python (tools/paths.json names blender.exe; its python sits beside it under <version>\python\bin)
$py = $null
$pathsFile = Join-Path $repo 'tools\paths.json'
if (Test-Path $pathsFile) {
    $raw = Get-Content $pathsFile -Raw
    try { $paths = $raw | ConvertFrom-Json } catch { $paths = ($raw -replace '(?<!\\)\\(?![\\"])', '\\') | ConvertFrom-Json }
    if ($paths.blenderExe -and (Test-Path $paths.blenderExe)) {
        $py = Get-ChildItem (Split-Path -Parent $paths.blenderExe) -Recurse -Filter python.exe -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -like '*\python\bin\python.exe' } | Select-Object -First 1 -ExpandProperty FullName
    }
}
if (-not $py) { "blender_locked: Blender's python.exe not found from tools/paths.json"; exit 2 }

$others = Get-ChildItem $locks -File | Where-Object { $_.Name -like 'heavy_*' -or $_.Name -like 'want_*' }
if ($others) {
    "ABORT: locks on file: " + (($others | ForEach-Object { $_.Name }) -join ', ')
    exit 3
}
$free = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 2)
if ($free -lt $MinFreeGB) {
    "ABORT: free RAM $free GB is under $MinFreeGB GB"
    exit 3
}
$t0 = Get-Date
Set-Content -Path $mine -Value ("{0} blender {1}" -f $t0.ToString('s'), $Job) -Encoding ascii
"lock taken {0} (free {1} GB): {2}" -f $t0.ToString('HH:mm:ss'), $free, $Job
$code = 1
$peak = 0
try {
    $p = Start-Process -FilePath $py -ArgumentList (@('-I') + $PyArgs) -WorkingDirectory $repo -NoNewWindow -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
    $null = $p.Handle
    while (-not $p.HasExited) {
        Start-Sleep -Milliseconds 400
        try {
            $p.Refresh()
            $ws = [int]($p.WorkingSet64 / 1MB)
            if ($ws -gt $peak) { $peak = $ws }
            if ($ws -gt $CapMB) {
                Stop-Process -Id $p.Id -Force
                "WATCHDOG: stopped at $ws MB (cap $CapMB MB)"
                break
            }
        } catch {}
        if (((Get-Date) - $t0).TotalSeconds -gt $TimeoutSec) {
            Stop-Process -Id $p.Id -Force
            "TIMEOUT: stopped after $TimeoutSec s"
            break
        }
    }
    $p.WaitForExit()
    $code = $p.ExitCode
}
finally {
    Remove-Item $mine -Force -ErrorAction SilentlyContinue
    "lock released {0} ({1:n0} s, peak {2} MB, exit {3})" -f (Get-Date).ToString('HH:mm:ss'), ((Get-Date) - $t0).TotalSeconds, $peak, $code
}
"--- stdout"
if (Test-Path $out) { Get-Content $out | Select-Object -Last 40 }
"--- stderr"
if (Test-Path $err) { Get-Content $err | Select-Object -Last 30 }
Remove-Item $out, $err -Force -ErrorAction SilentlyContinue
exit $code
