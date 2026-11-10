<#
.SYNOPSIS
  BLENDER's real Blender run (bpy) under heavy_blender.lock: tools/blender_scene.ps1 -Job "<what>" -Script <py> [-ScriptArgs a,b,...]
.DESCRIPTION
  For art v7 (D-205): scenes that blender_render.ps1's manifest path does not wrap (a pilot, a probe, a set). The sibling
  of tools/blender_locked.ps1 (which runs Blender's bundled python without bpy):
    1. lists coordination/locks and aborts (exit 3) on any heavy_* / want_* file, another role's or a stale one of mine;
    2. aborts under -MinFreeGB of free physical memory (2.4 by default: LEAD's gate for a 3D render on this 7.6 GB machine);
    3. aborts if a blender.exe is already running (one Blender at a time);
    4. writes coordination/locks/heavy_blender.lock (ISO time + the job);
    5. runs blender.exe --background --factory-startup --disable-autoexec --python-exit-code 1 --python <Script> -- <ScriptArgs>
       from the repo root, with a working-set watchdog (-CapMB) and a timeout (-TimeoutSec; keep one lock <= 15 min);
    6. deletes the lock in `finally`; prints the lock times, the peak working set, the exit code, every stdout line that
       starts with "V7 " (the script's own report) and the tails of stdout and stderr.
  Read free RAM in its own call BEFORE this one. No 2>&1 on it in PowerShell 5.1. Exit codes: Blender's, or 3 when refused.
  --disable-autoexec: a downloaded file must never run a script of its own (vendor files are glTF, which carries none).
.EXAMPLE
  tools/blender_scene.ps1 -Job "B-258 part 1 probe" -Script blender/scripts/v7_paint_pass.py -ScriptArgs probe
#>
param(
    [Parameter(Mandatory = $true)][string]$Job,
    [Parameter(Mandatory = $true)][string]$Script,
    [string[]]$ScriptArgs = @(),
    [int]$CapMB = 2400,
    [int]$TimeoutSec = 600,
    [double]$MinFreeGB = 2.4
)
$repo = Split-Path -Parent $PSScriptRoot
$locks = Join-Path $repo 'coordination\locks'
$mine = Join-Path $locks 'heavy_blender.lock'
$out = Join-Path $env:TEMP ("blender_scene_{0}.out" -f $PID)
$err = Join-Path $env:TEMP ("blender_scene_{0}.err" -f $PID)

$exe = $null
$pathsFile = Join-Path $repo 'tools\paths.json'
if (Test-Path $pathsFile) {
    $raw = Get-Content $pathsFile -Raw
    try { $paths = $raw | ConvertFrom-Json } catch { $paths = ($raw -replace '(?<!\\)\\(?![\\"])', '\\') | ConvertFrom-Json }
    if ($paths.blenderExe -and (Test-Path $paths.blenderExe)) { $exe = $paths.blenderExe }
}
if (-not $exe) { "blender_scene: blender.exe not found from tools/paths.json"; exit 2 }
if (-not (Test-Path $Script)) { $Script = Join-Path $repo $Script }
if (-not (Test-Path $Script)) { "blender_scene: no such script: $Script"; exit 2 }

$others = Get-ChildItem $locks -File | Where-Object { $_.Name -like 'heavy_*' -or $_.Name -like 'want_*' }
if ($others) {
    "ABORT: locks on file: " + (($others | ForEach-Object { $_.Name }) -join ', ')
    exit 3
}
if (Get-Process -Name blender -ErrorAction SilentlyContinue) { "ABORT: a blender.exe is already running"; exit 3 }
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
    $argv = @('--background', '--factory-startup', '--disable-autoexec', '--python-exit-code', '1', '--python', $Script, '--') + $ScriptArgs
    $p = Start-Process -FilePath $exe -ArgumentList $argv -WorkingDirectory $repo -NoNewWindow -PassThru `
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
"--- the script's report (V7 lines)"
if (Test-Path $out) { Get-Content $out | Where-Object { $_ -like 'V7 *' } | Select-Object -First 120 }
"--- stdout tail"
if (Test-Path $out) { Get-Content $out | Where-Object { $_ -notlike 'V7 *' } | Select-Object -Last 10 }
"--- stderr tail"
if (Test-Path $err) { Get-Content $err | Select-Object -Last 25 }
Remove-Item $out, $err -Force -ErrorAction SilentlyContinue
exit $code
