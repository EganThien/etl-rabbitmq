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

function Start-Consumer($name, $args, $outfile) {
    Write-Host "Starting consumer $name (logs -> $outfile)"
    $psArgs = "-NoProfile -Command `"cd `"$RepoRoot`"; mvn exec:java -Dexec.mainClass=\"com.example.etl.Application\" -Dexec.args=\"$args\" 2>&1 | Out-File -FilePath \"$outfile\" -Encoding utf8`""
    Start-Process -FilePath pwsh -ArgumentList $psArgs -WindowStyle Hidden | Out-Null
}

# Use pwsh if available; fallback to powershell
if (Get-Command pwsh -ErrorAction SilentlyContinue) { $shell = 'pwsh' } else { $shell = 'powershell' }

# Start consumers in background
$empLog = Join-Path $logs "employee-consumer.log"
$ordLog = Join-Path $logs "order-consumer.log"
Write-Host "Starting employee consumer..."
Start-Process -FilePath $shell -ArgumentList "-NoProfile","-Command","cd `"$RepoRoot`"; mvn exec:java -Dexec.mainClass=\"com.example.etl.Application\" -Dexec.args=\"employee-consumer\" 2>&1 | Out-File -FilePath \"$empLog\" -Encoding utf8" -WindowStyle Hidden | Out-Null
Start-Sleep -Milliseconds 500
Write-Host "Starting order consumer..."
Start-Process -FilePath $shell -ArgumentList "-NoProfile","-Command","cd `"$RepoRoot`"; mvn exec:java -Dexec.mainClass=\"com.example.etl.Application\" -Dexec.args=\"order-consumer\" 2>&1 | Out-File -FilePath \"$ordLog\" -Encoding utf8" -WindowStyle Hidden | Out-Null

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
