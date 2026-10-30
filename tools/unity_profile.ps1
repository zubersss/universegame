# BudgetGate profile run (U-014): runs BudgetGateTests with graphics and writes
# coordination/reports/unity/perf_<date>.md with every Bible §11.1 row. Owner: UNITY.
# Usage: tools/unity_profile.ps1
. (Join-Path $PSScriptRoot 'unity_common.ps1')

$date = Get-Date -Format 'yyyy-MM-dd'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$xml = Join-Path $LogDir "profile_$stamp.xml"
$report = Join-Path $RepoRoot "coordination\reports\unity\perf_$date.md"

try { Enter-HeavyJobLock 'unity_profile' } catch { Write-Host "BLOCKED: $_"; exit 2 }
try {
    $env:MERIDIAN_PROFILE_REPORT = $report
    $unityArgs = @('-runTests', '-testPlatform', 'PlayMode', '-assemblyNames', 'MERIDIAN.Tests.Play',
        '-testFilter', 'Meridian.Tests.BudgetGateTests', '-testResults', $xml)
    $r = Invoke-UnityBatch $unityArgs "unity_profile_$stamp.log" -Graphics
} finally {
    Remove-Item Env:\MERIDIAN_PROFILE_REPORT -ErrorAction SilentlyContinue
    Exit-HeavyJobLock
}

Write-Host "Log: $($r.Log)"
if (-not (Test-Path $xml)) { Write-Host 'PROFILE FAILED: no results file'; exit 1 }
[xml]$doc = Get-Content $xml -Raw
$passed = $doc.'test-run'.passed -eq '1'
if (Test-Path $report) { Write-Host "Report: $report" } else { Write-Host 'Report not written (test failed before the end)' }
if ($passed) { Write-Host 'BUDGETGATE GREEN'; exit 0 }
$msg = $doc.SelectSingleNode('//test-case/failure/message')
Write-Host "BUDGETGATE RED: $($msg.InnerText)"
exit 1
