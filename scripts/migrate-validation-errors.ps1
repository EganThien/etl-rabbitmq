<#
Add `validation_errors` column to staging tables if missing.

Usage: .\scripts\migrate-validation-errors.ps1
#>

Set-StrictMode -Version Latest
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location (Join-Path $scriptDir '..')

# Read MYSQL_ROOT_PASSWORD from .env if present
$rootpass = 'rootpassword'
if (Test-Path .\.env) {
    $envLines = Get-Content .\.env | Where-Object {$_ -and ($_ -notmatch '^\s*#') }
    foreach ($line in $envLines) {
        if ($line -match '^\s*MYSQL_ROOT_PASSWORD\s*=\s*(.*)') { $rootpass = $matches[1].Trim() }
    }
}

function Wait-ForMySql([int]$timeoutSec = 60) {
    $start = Get-Date
    while ((Get-Date) - $start -lt (New-TimeSpan -Seconds $timeoutSec)) {
        try {
            $res = & docker exec mysql mysql -u root -p$rootpass -e "SELECT 1;" 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "MySQL is ready"
                return $true
            }
        } catch {
        }
        Write-Host "Waiting for MySQL to be ready..."
        Start-Sleep -Seconds 2
    }
    throw "MySQL did not become ready within $timeoutSec seconds"
}

Write-Host "Waiting for MySQL to become ready..."
Wait-ForMySql -timeoutSec 120

# Use ALTER ... ADD COLUMN IF NOT EXISTS (MySQL 8+). If not supported, the statement will be ignored by the server.
$sql = "ALTER TABLE staging_employee ADD COLUMN IF NOT EXISTS validation_errors TEXT NULL; ALTER TABLE staging_order_detail ADD COLUMN IF NOT EXISTS validation_errors TEXT NULL;"

Write-Host "Applying migration to add validation_errors columns..."
$sql | docker exec -i mysql sh -c "mysql -u root -p$rootpass etl_db"

Write-Host "Migration completed."

Pop-Location
