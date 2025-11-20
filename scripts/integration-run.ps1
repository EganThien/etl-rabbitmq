<# Integration-run: simplified, ASCII-only and robust orchestration script #>

param(
    [switch]$RunProducer,
    [switch]$RunTransform,
    [int]$WaitSeconds = 10
)

Set-StrictMode -Version Latest
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location (Join-Path $scriptDir '..')

Write-Host "Working directory: $(Get-Location)"

Write-Host "Bringing up docker-compose services (build if needed)..."
docker compose up -d --build

Write-Host "Invoking schema loader (waits for MySQL and loads schema)..."
$loadSchemaScript = Join-Path $scriptDir 'load-schema.ps1'
if (Test-Path $loadSchemaScript) {
    & $loadSchemaScript
} else {
    Write-Warning "Could not find $loadSchemaScript - please apply schema manually."
}

# Run migration to add validation_errors column if needed
$migrateScript = Join-Path $scriptDir 'migrate-validation-errors.ps1'
if (Test-Path $migrateScript) {
    Write-Host "Running DB migration to ensure validation_errors columns exist..."
    & $migrateScript
} else {
    Write-Host "No migration script found ($migrateScript). Skipping ALTER for existing DBs."
}

if ($RunProducer) {
    Write-Host "Running producer (one-off)..."
    $producerScript = Join-Path $scriptDir 'run-producer.ps1'
    if (Test-Path $producerScript) {
        & $producerScript
    } else {
        Write-Warning "Could not find $producerScript - run producer manually."
    }
} else {
    Write-Host "Skipping producer (use -RunProducer to enable)."
}

Write-Host "Waiting $WaitSeconds seconds for messages to be processed..."
Start-Sleep -Seconds $WaitSeconds

if ($RunTransform) {
    Write-Host "Running transform (staging -> main)..."
    $transformScript = Join-Path $scriptDir 'run-transform.ps1'
    if (Test-Path $transformScript) {
        & $transformScript
    } else {
        Write-Warning "Could not find $transformScript - run transform manually."
    }
} else {
    Write-Host "Skipping transform (use -RunTransform to enable)."
}

Write-Host "Current docker-compose status:"
docker compose ps

Write-Host "Note: to inspect DB counts, run the mysql client inside the mysql container or use the dashboard."
Write-Host "Example: docker compose exec -T mysql bash -lc \"mysql -uroot -p\$MYSQL_ROOT_PASSWORD -D\$MYSQL_DATABASE -e 'SELECT \"staging_employee\" as t, COUNT(*) FROM staging_employee;'\""

Write-Host "Tail last 200 lines of app logs (producer/consumers/transform) - adjust service names if needed:"
try {
    docker compose logs --tail=200 app-producer app-employee-consumer app-order-consumer app-transform
} catch {
    Write-Warning "Could not tail some app logs; printing available service logs instead."
    docker compose logs --tail=200
}

Pop-Location
Write-Host "Integration run complete. Review outputs above for confirmation."