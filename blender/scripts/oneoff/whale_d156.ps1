# D-156 (LEAD 20:4x): a one-off for creatures/jupiter/vortex_whale only. tools/blender_render.ps1's lock / want / stamp /
# log formats, with a start gate of 1300 MB free (waits up to 7 min for it, read every 2 s) and a watchdog that kills
# Blender if its working set passes 900 MB (or free RAM falls under 300 MB, D-045). One kill ends the exception.
$ErrorActionPreference = 'Stop'
$Root = 'C:\dev\universegame'
$Key = 'creatures/jupiter/vortex_whale'
$Gate = 1300; $Cap = 900
$paths = Get-Content (Join-Path $Root 'tools/paths.json') -Raw | ConvertFrom-Json
$blender = $paths.blenderExe
$locks = Join-Path $Root 'coordination/locks'
$lock = Join-Path $locks 'heavy_blender.lock'
$want = Join-Path $locks 'want_blender.lock'
$stamp = Join-Path $Root 'blender/preview/last_heavy.txt'
$logDir = Join-Path $Root 'logs'
$utf8 = New-Object System.Text.UTF8Encoding($false)
function Log([string]$line) {
    $p = Join-Path $logDir "blender_$((Get-Date).ToString('yyyy-MM-dd')).log"
    [System.IO.File]::AppendAllText($p, "$((Get-Date).ToString('s')) $line`n", $utf8)
}
function FreeMB { [int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024) }

$deadline = (Get-Date).AddMinutes(7)
while ($true) {
    $others = Get-ChildItem $locks -Filter 'heavy_*.lock' -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne 'heavy_blender.lock' }
    if ($others) { Write-Host "d156: another lock appeared ($($others.Name -join ', ')); not starting"; exit 3 }
    $f = FreeMB
    if ($f -ge $Gate) { break }
    if ((Get-Date) -gt $deadline) { Write-Host "d156: free RAM stayed under $Gate MB for 7 min (last $f MB); not starting"; exit 3 }
    Set-Content -Path $want -Value "$((Get-Date).ToString('s')) blender waiting: $Key (D-156 one-off gate $Gate MB)" -Encoding utf8
    Start-Sleep -Seconds 2
}
if (Test-Path $want) { Remove-Item $want -Force }
Set-Content -Path $lock -Value "$((Get-Date).ToString('s')) blender_render $Key (D-156 one-off: gate $Gate MB, free $f MB, cap $Cap MB)" -Encoding utf8
Log "GATE $Key | gate $Gate MB, free $f MB | D-156: a one-off gate for the whale (LEAD 20:4x), watchdog cap $Cap MB on Blender's working set"
Write-Host "d156: gate $Gate MB, free $f MB, cap $Cap MB; starting $(Get-Date -Format HH:mm:ss)"
$t0 = Get-Date
$out = Join-Path $env:TEMP "d156_$PID.log"
$script = Join-Path $Root 'blender/render.py'
$code = 0; $killed = $null; $peakWS = 0; $minFree = $f
try {
    $argList = @('--background', '--factory-startup', '--python-exit-code', '1', '--python', "`"$script`"", '--', '--asset', $Key)
    $p = Start-Process -FilePath $blender -ArgumentList $argList -NoNewWindow -PassThru -RedirectStandardOutput $out
    while (-not $p.HasExited) {
        Start-Sleep -Milliseconds 500
        try { $p.Refresh(); $ws = [int]($p.WorkingSet64 / 1MB) } catch { $ws = 0 }
        if ($ws -gt $peakWS) { $peakWS = $ws }
        $fr = FreeMB
        if ($fr -lt $minFree) { $minFree = $fr }
        if ($ws -gt $Cap) { Stop-Process -Id $p.Id -Force; $killed = "working set $ws MB > cap $Cap MB"; break }
        if ($fr -lt 300) { Stop-Process -Id $p.Id -Force; $killed = "free RAM $fr MB < 300 (D-045)"; break }
    }
    $p.WaitForExit()
    Get-Content $out -ErrorAction SilentlyContinue | ForEach-Object { if ($_ -match '^(MERIDIAN |Traceback|  File |\w+Error)') { Write-Host $_ } }
    Remove-Item $out -ErrorAction SilentlyContinue
    if ($killed) { $code = 4 } elseif ($p.ExitCode -ne 0) { $code = $p.ExitCode }
} finally {
    if (Test-Path $lock) { Remove-Item $lock -Force }
    Set-Content -Path $stamp -Value "$((Get-Date).ToString('s')) $Key" -Encoding utf8
}
$secs = ((Get-Date) - $t0).TotalSeconds
if ($killed) {
    Log "D-156 STOPPED $Key | $killed | the one-off exception ends (LEAD 20:4x)"
    Write-Host "d156: STOPPED: $killed"
} else {
    Log ("D-156 JOB $Key | exit {0} | {1:N0} s | Blender working set peak {2} MB (cap {3}), free RAM low {4} MB" -f $code, $secs, $peakWS, $Cap, $minFree)
}
Write-Host ("d156: exit {0} in {1:N0} s; Blender working-set peak {2} MB (cap {3}); free RAM low {4} MB" -f $code, $secs, $peakWS, $Cap, $minFree)
exit $code
