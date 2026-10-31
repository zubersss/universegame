# Self-test of the D-026 HeavyJobLock rules in unity_common.ps1, against a temporary lock folder
# (never the real coordination/locks/). No Unity process is started. Owner: UNITY.
# Usage: tools/unity_lock_selftest.ps1   (exit 0 = all checks pass)
. (Join-Path $PSScriptRoot 'unity_common.ps1')
$ErrorActionPreference = 'Stop'

$tmp = Join-Path ([IO.Path]::GetTempPath()) ("meridian_locktest_" + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Force $tmp | Out-Null
$script:LockDir = $tmp
$script:LockFile = Join-Path $tmp 'heavy_unity.lock'
$script:WantFile = Join-Path $tmp 'want_unity.lock'
$script:ReleaseStamp = Join-Path $tmp 'unity_last_release.txt'
# Ignore real processes so the rules can be tested while Blender or an Editor runs.
function Test-UnityEditorRunning { return $false }
function Get-Process { param($Name, $ErrorAction) return $null }

$fail = 0
function Check([string]$name, [bool]$ok) { if ($ok) { Write-Host "PASS $name" } else { Write-Host "FAIL $name"; $script:fail++ } }
function TryEnter { try { Enter-HeavyJobLock 'selftest'; return $null } catch { return "$_" } }

# 1. Another role holds the lock → refuse and leave want_unity.lock.
'x' | Set-Content (Join-Path $tmp 'heavy_blender.lock')
$err = TryEnter
Check 'refuses while another role holds the lock' ($err -like '*held by heavy_blender.lock*')
Check 'writes want_unity.lock while waiting' (Test-Path $WantFile)
Remove-Item (Join-Path $tmp 'heavy_blender.lock')

# 2. Lock free → acquire, want removed; Exit removes the lock and stamps the release.
$script:MinFreeGB = 0
$err = TryEnter
Check 'acquires when clear' ($null -eq $err -and (Test-Path $LockFile))
Check 'deletes want_unity.lock on acquire' (-not (Test-Path $WantFile))
Exit-HeavyJobLock
Check 'Exit removes heavy_unity.lock' (-not (Test-Path $LockFile))
Check 'Exit stamps the release time' (Test-Path $ReleaseStamp)

# 3. D-037: another role waiting (< 30 min) with no UNITY request → yield, however long ago UNITY released.
'x' | Set-Content (Join-Path $tmp 'want_blender.lock')
(Get-Item (Join-Path $tmp 'want_blender.lock')).LastWriteTime = (Get-Date).AddMinutes(-1)
(Get-Date).AddMinutes(-10).ToString('o') | Set-Content $ReleaseStamp
$err = TryEnter
Check 'yields to a waiting role (strict turns, D-037)' ($err -like '*yielding to want_blender.lock*D-037*')
$err = TryEnter
Check 'keeps yielding while that role has not taken the lock' ($err -like '*yielding to want_blender.lock*')

# 3b. That role takes the lock (deletes its want) and runs; UNITY waits on the lock, then goes.
Remove-Item (Join-Path $tmp 'want_blender.lock')
'x' | Set-Content (Join-Path $tmp 'heavy_blender.lock')
$err = TryEnter
Check 'waits while that role runs its job' ($err -like '*held by heavy_blender.lock*')
Remove-Item (Join-Path $tmp 'heavy_blender.lock')
$err = TryEnter
Check 'goes once that role has had its turn' ($null -eq $err)
Exit-HeavyJobLock

# 4. Waiting role's want older than 30 min → ignored.
'x' | Set-Content (Join-Path $tmp 'want_blender.lock')
(Get-Item (Join-Path $tmp 'want_blender.lock')).LastWriteTime = (Get-Date).AddMinutes(-31)
Remove-Item $WantFile -ErrorAction SilentlyContinue
$err = TryEnter
Check 'ignores a want file older than 30 min' ($null -eq $err)
Exit-HeavyJobLock

# 5. Both waiting: the older request goes first (no deadlock).
'x' | Set-Content $WantFile
(Get-Item $WantFile).LastWriteTime = (Get-Date).AddMinutes(-5)
(Get-Item (Join-Path $tmp 'want_blender.lock')).LastWriteTime = (Get-Date).AddMinutes(-2)
$err = TryEnter
Check 'goes first when its own request is older' ($null -eq $err)
Exit-HeavyJobLock
Remove-Item (Join-Path $tmp 'want_blender.lock')

# 6. Memory gate: refuse below the threshold and print the number.
$script:MinFreeGB = 1e6
(Get-Date).AddMinutes(-3).ToString('o') | Set-Content $ReleaseStamp
$err = TryEnter
Check 'refuses below the free-RAM threshold and reports GB' ($err -match 'only [0-9.]+ GB free RAM')
Check 'memory refusal also leaves want_unity.lock' (Test-Path $WantFile)
Write-Host "free RAM now: $(Get-FreeMemoryGB) GB"

# 7. Inside unity_check.ps1 (MERIDIAN_LOCK_HELD=1) the inner scripts neither take nor release the lock.
$script:MinFreeGB = 0
'x' | Set-Content $LockFile
$env:MERIDIAN_LOCK_HELD = '1'
'y' | Set-Content (Join-Path $tmp 'want_blender.lock')
$err = TryEnter
Check 'held mode: inner Enter neither blocks nor rewrites the lock' ($null -eq $err -and (Get-Content $LockFile -Raw).Trim() -eq 'x')
Exit-HeavyJobLock
Check 'held mode: inner Exit keeps the outer lock' (Test-Path $LockFile)
Remove-Item Env:MERIDIAN_LOCK_HELD
Exit-HeavyJobLock
Check 'outer Exit releases it' (-not (Test-Path $LockFile))

Remove-Item $tmp -Recurse -Force
if ($fail -gt 0) { Write-Host "$fail check(s) failed"; exit 1 }
Write-Host 'All D-026/D-037 lock checks pass.'
exit 0
