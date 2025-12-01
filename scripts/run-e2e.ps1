<#
Run end-to-end smoke for the ETL demo (PowerShell).

What it does:
- Start docker compose (RabbitMQ + MySQL) in detached mode
- Wait for services to be up (simple sleep loop)
- Start employee-consumer and order-consumer as background processes (log files in scripts/logs)
- Run producer (publishes CSV -> queues)
- Run transform (moves valid rows from staging -> main)

Usage:
  .\scripts\run-e2e.ps1

Notes:
- Requires Docker Desktop (docker compose) and Maven + Java available in PATH.
#>

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

Write-Host "Starting end-to-end smoke run..."

# Start docker compose
Write-Host "Bringing up Docker services..."
docker compose up -d

Write-Host "Waiting 10 seconds for services to initialize..."
Start-Sleep -Seconds 10

# Prepare logs dir
$logs = Join-Path $RepoRoot "scripts\logs"
if (-not (Test-Path $logs)) { New-Item -ItemType Directory -Path $logs | Out-Null }

# Start consumers in background
$empLog = Join-Path $logs "employee-consumer.log"
$ordLog = Join-Path $logs "order-consumer.log"

Write-Host "Starting employee consumer (background)..."
$empScript = "cd '$RepoRoot'; mvn exec:java -Dexec.mainClass='com.example.etl.Application' -Dexec.args='employee-consumer' 2>&1 | Out-File -FilePath '$empLog' -Encoding utf8"
Start-Process -FilePath powershell -ArgumentList "-NoProfile","-Command",$empScript -WindowStyle Hidden

Start-Sleep -Milliseconds 500

Write-Host "Starting order consumer (background)..."
$ordScript = "cd '$RepoRoot'; mvn exec:java -Dexec.mainClass='com.example.etl.Application' -Dexec.args='order-consumer' 2>&1 | Out-File -FilePath '$ordLog' -Encoding utf8"
Start-Process -FilePath powershell -ArgumentList "-NoProfile","-Command",$ordScript -WindowStyle Hidden

Start-Sleep -Seconds 2

Write-Host "Running producer (publishing CSV messages)..."
& mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="producer"

Write-Host "Sleeping 3 seconds to allow consumers to process messages..."
Start-Sleep -Seconds 3

Write-Host "Running transform (staging -> main)..."
& mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="transform"

Write-Host "E2E run complete. Check the dashboard at http://localhost:8080 (if dashboard is running) or check logs in scripts/logs"
Write-Host "Employee consumer log: $empLog"
Write-Host "Order consumer log: $ordLog"

Write-Host "To stop background consumers: find and stop the Java processes or run `docker compose down` to stop containers (consumers started locally will keep running until closed)."
