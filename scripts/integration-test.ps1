# Integration test (Docker Compose based)
# Starts the stack, runs producer, waits, runs transform, checks main tables have data
# Exit code 0 = success, non-zero = failure

Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Definition)

Write-Host "Starting docker-compose (build) and services..."
Write-Host "Packaging Java app (mvn package) from project root..."
Push-Location ..
mvn -B -DskipTests package
Pop-Location

Write-Host "Starting docker-compose (build) and services..."
Write-Host "Building images (etl-app, etl-dashboard) first..."
docker compose build etl-app etl-dashboard

Write-Host "Starting docker-compose services..."
docker compose up -d

# reuse readiness helpers
. .\run-full.ps1  # we call to load the helper functions defined there (Wait-ForMySql, Wait-ForRabbitMq)

Write-Host "Waiting for RabbitMQ & MySQL readiness from integration script..."
Wait-ForRabbitMq -timeoutSec 120
Wait-ForMySql -timeoutSec 120

Write-Host "Loading DB schema..."
.\load-schema.ps1

Write-Host "Running producer (one-off)..."
docker compose run --rm app-producer
Write-Host "Waiting for staging data to appear (consumers processing)..."

# Read MYSQL credentials from .env for later checks
$mysqlUser = 'etl'
$mysqlPass = 'etlpass'
$mysqlDb = 'etl_db'
if (Test-Path .\.env) {
    $envLines = Get-Content .\.env | Where-Object {$_ -and ($_ -notmatch '^\s*#') }
    foreach ($line in $envLines) {
        if ($line -match '^\s*MYSQL_USER\s*=\s*(.*)') { $mysqlUser = $matches[1].Trim() }
        if ($line -match '^\s*MYSQL_PASSWORD\s*=\s*(.*)') { $mysqlPass = $matches[1].Trim() }
        if ($line -match '^\s*MYSQL_DATABASE\s*=\s*(.*)') { $mysqlDb = $matches[1].Trim() }
    }
}

function Get-StagingCounts() {
    $cmd = "mysql -u $mysqlUser -p$mysqlPass -e ""USE $mysqlDb; SELECT 'staging_employee', COUNT(*) FROM staging_employee; SELECT 'staging_order_detail', COUNT(*) FROM staging_order_detail;"""
    $res = docker exec -i mysql sh -c $cmd
    return $res
}

function Wait-ForStagingData([int]$timeoutSec = 60) {
    $start = Get-Date
    while ((Get-Date) - $start -lt (New-TimeSpan -Seconds $timeoutSec)) {
        $out = Get-StagingCounts
        if ($out -match "staging_employee\s+([0-9]+)") { $emp = [int]$matches[1] } else { $emp = 0 }
        if ($out -match "staging_order_detail\s+([0-9]+)") { $ord = [int]$matches[1] } else { $ord = 0 }
        Write-Host "staging_employee=$emp, staging_order_detail=$ord"
        if ($emp -gt 0 -and $ord -gt 0) { return @{ employee=$emp; order=$ord } }
        Start-Sleep -Seconds 2
    }
    throw "Staging data did not appear within $timeoutSec seconds"
}

Try {
    $staging = Wait-ForStagingData -timeoutSec 120
    Write-Host "Staging has data: $($staging.employee) employees, $($staging.order) orders"
} Catch {
    Write-Host "Timed out waiting for staging data: $_" -ForegroundColor Red
    Exit 3
}

Write-Host "Running transform (staging -> main)..."
docker compose run --rm app-transform

function Get-MainCounts() {
    $cmd = "mysql -u $mysqlUser -p$mysqlPass -e ""USE $mysqlDb; SELECT 'main_employee', COUNT(*) FROM main_employee; SELECT 'main_order_detail', COUNT(*) FROM main_order_detail;"""
    $res = docker exec -i mysql sh -c $cmd
    return $res
}

function Wait-ForMainData([int]$timeoutSec = 60) {
    $start = Get-Date
    while ((Get-Date) - $start -lt (New-TimeSpan -Seconds $timeoutSec)) {
        $out = Get-MainCounts
        if ($out -match "main_employee\s+([0-9]+)") { $emp = [int]$matches[1] } else { $emp = 0 }
        if ($out -match "main_order_detail\s+([0-9]+)") { $ord = [int]$matches[1] } else { $ord = 0 }
        Write-Host "main_employee=$emp, main_order_detail=$ord"
        if ($emp -gt 0 -and $ord -gt 0) { return @{ employee=$emp; order=$ord } }
        Start-Sleep -Seconds 2
    }
    throw "Main data did not appear within $timeoutSec seconds"
}

Try {
    $main = Wait-ForMainData -timeoutSec 120
    Write-Host "Integration test passed: main_employee=$($main.employee), main_order_detail=$($main.order)"
    Exit 0
} Catch {
    Write-Host "Integration test failed: $_" -ForegroundColor Red
    Exit 2
}
