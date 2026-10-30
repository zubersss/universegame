# Batch test runner. Owner: UNITY.
# Usage: tools/unity_test.ps1 [EditMode|PlayMode] [-Filter <regex>] [-Assembly "A;B"]
# Default assemblies: ours for the mode plus LEAD's MERIDIAN.Tests.LeadQA (U-021).
# Writes logs/tests_<date>_<mode>.xml and appends a summary to coordination/reports/unity/tests_<date>.md.
param(
    [ValidateSet('EditMode', 'PlayMode')][string]$Mode = 'EditMode',
    [string]$Filter = '',
    [string]$Assembly = ''
)
. (Join-Path $PSScriptRoot 'unity_common.ps1')

$date = Get-Date -Format 'yyyy-MM-dd'
$time = Get-Date -Format 'HH:mm'
$xml = Join-Path $LogDir "tests_${date}_$Mode.xml"
$reportDir = Join-Path $RepoRoot 'coordination\reports\unity'
$report = Join-Path $reportDir "tests_$date.md"
New-Item -ItemType Directory -Force $reportDir | Out-Null
Remove-Item $xml -Force -ErrorAction SilentlyContinue

try { Enter-HeavyJobLock "unity_test $Mode" } catch { Write-Host "BLOCKED: $_"; exit 2 }
try {
    # Only MERIDIAN assemblies; packages ship stub tests of their own.
    $assembly = if ($Assembly) { $Assembly } elseif ($Mode -eq 'EditMode') { 'MERIDIAN.Tests.Unit;MERIDIAN.Tests.LeadQA' } else { 'MERIDIAN.Tests.Play;MERIDIAN.Tests.LeadQA' }
    $unityArgs = @('-runTests', '-testPlatform', $Mode, '-testResults', $xml, '-assemblyNames', $assembly)
    if ($Filter) { $unityArgs += @('-testFilter', $Filter) }
    $r = Invoke-UnityBatch $unityArgs "unity_test_${date}_$Mode.log"
} finally { Exit-HeavyJobLock }

$errors = Get-CompileErrors $r.Log
if (-not (Test-Path $xml)) {
    $reason = if ($errors.Count) { "compile errors: $($errors[0])" } else { "no results file (Unity exit $($r.ExitCode)); see $($r.Log)" }
    if (-not (Test-Path $report)) { "# UNITY test reports $date`n" | Set-Content -Encoding utf8 $report }
    "`n## $time $Mode - FAILED TO RUN`n- $reason" | Add-Content -Encoding utf8 $report
    Write-Host "FAILED: $reason"; exit 1
}

[xml]$doc = Get-Content $xml -Raw
$run = $doc.'test-run'
$total = [int]$run.total; $passed = [int]$run.passed; $failed = [int]$run.failed; $skipped = [int]$run.skipped
$failedNames = @($doc.SelectNodes("//test-case[@result='Failed']") | ForEach-Object {
    $msg = ($_.failure.message.'#cdata-section' -replace '\s+', ' ').Trim()
    if ($msg.Length -gt 160) { $msg = $msg.Substring(0, 160) + '...' }
    "$($_.fullname) - $msg"
})

if (-not (Test-Path $report)) { "# UNITY test reports $date`n" | Set-Content -Encoding utf8 $report }
$lines = @("", "## $time $Mode - $passed/$total passed, $failed failed, $skipped skipped")
if ($Filter) { $lines += "- filter: ``$Filter``" }
$suites = @($doc.SelectNodes("//test-suite[@type='Assembly']"))
foreach ($s in $suites) {
    $name = [IO.Path]::GetFileNameWithoutExtension($s.name)
    $lines += "- $name : $($s.passed)/$($s.total) passed, $($s.failed) failed, $($s.skipped) skipped"
}
$lines += $failedNames | ForEach-Object { "- FAIL $_" }
$lines | Add-Content -Encoding utf8 $report

Write-Host "$Mode : $passed/$total passed, $failed failed, $skipped skipped"
$lines | Where-Object { $_ -like '- MERIDIAN*' } | ForEach-Object { Write-Host "  $_" }
$failedNames | ForEach-Object { Write-Host "  FAIL $_" }
Write-Host "XML: $xml"; Write-Host "Report: $report"
if ($failed -gt 0 -or $total -eq 0) { exit 1 }
exit 0
