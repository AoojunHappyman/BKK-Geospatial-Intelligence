$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$pgCtl = Join-Path $projectRoot '.local/pgsql/bin/pg_ctl.exe'
$pgData = Join-Path $projectRoot '.local/pgdata'
if (-not (Test-Path -LiteralPath "$pgData/PG_VERSION")) { throw 'Initialize PostgreSQL and run the ETL first. See README.md.' }
& $pgCtl -D $pgData status | Out-Null
if ($LASTEXITCODE -ne 0) {
  & $pgCtl -D $pgData -l "$projectRoot/.local/postgres.log" -o '-h 127.0.0.1 -p 55432' -w start
  if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL failed to start.' }
}
$env:DATABASE_URL = 'postgresql://bkk@127.0.0.1:55432/bkk'
function Test-Endpoint([string]$url) {
  try { return (Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 3).StatusCode -eq 200 } catch { return $false }
}
if (-not (Test-Endpoint 'http://127.0.0.1:8000/api/health')) {
  $apiProcess = Start-Process -FilePath (Get-Command python).Source -ArgumentList '-X utf8 scripts/run_api.py' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput "$projectRoot/.local/api.log" -RedirectStandardError "$projectRoot/.local/api-error.log"
  $apiProcess.Id | Set-Content "$projectRoot/.local/api.pid"
}
if (-not (Test-Endpoint 'http://127.0.0.1:5173')) {
  $nodePath = (Get-Command node).Source
  $webProcess = Start-Process -FilePath $nodePath -ArgumentList 'node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort' -WorkingDirectory "$projectRoot/frontend" -WindowStyle Hidden -PassThru -RedirectStandardOutput "$projectRoot/.local/web.log" -RedirectStandardError "$projectRoot/.local/web-error.log"
  $webProcess.Id | Set-Content "$projectRoot/.local/web.pid"
}
for ($attempt = 0; $attempt -lt 20; $attempt++) {
  if ((Test-Endpoint 'http://127.0.0.1:8000/api/health') -and (Test-Endpoint 'http://127.0.0.1:5173')) {
    Write-Output 'BKK Geospatial Intelligence: http://127.0.0.1:5173 | API: http://127.0.0.1:8000/docs'
    exit 0
  }
  Start-Sleep -Seconds 1
}
throw 'Services did not become ready. Inspect .local/*-error.log.'
