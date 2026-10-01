$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
foreach ($service in @('api','web')) {
  $pidFile = Join-Path $projectRoot ".local/$service.pid"
  if (Test-Path -LiteralPath $pidFile) {
    $servicePid = [int](Get-Content -LiteralPath $pidFile)
    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$servicePid"
    $expectedCommand = if ($service -eq 'api') { 'scripts/run_api.py' } else { 'node_modules/vite/bin/vite.js' }
    if ($processInfo -and $processInfo.CommandLine.Contains($expectedCommand)) { Stop-Process -Id $servicePid }
    Remove-Item -LiteralPath $pidFile
  }
}
& "$projectRoot/.local/pgsql/bin/pg_ctl.exe" -D "$projectRoot/.local/pgdata" -m fast -w stop
