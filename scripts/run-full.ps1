# Run full pipeline: build + start services, load schema, run producer, then transform
# Usage: open PowerShell in project root and run: .\scripts\run-full.ps1

# Ensure script runs from repository root
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)
Set-Location -Path $projectRoot

Write-Host "Building Java application with Maven..."
mvn clean package -DskipTests
if ($LASTEXITCODE -ne 0) {
    throw "Maven build failed"
}

Write-Host "Building Docker images and starting services..."
docker compose up --build -d

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
			$res = & docker exec mysql mysqladmin ping -h127.0.0.1 -u root -p$rootpass 2>&1
			if ($res -and $res -match 'mysqld is alive') {
				Write-Host "MySQL is ready"
				return $true
			}
		} catch {
		# ignore and retry
	}
	Write-Host "Waiting for MySQL to be ready..."
	Start-Sleep -Seconds 3
}
	throw "MySQL did not become ready within $timeoutSec seconds"
}

Write-Host "Waiting for MySQL to become ready..."
Start-Sleep -Seconds 10
Wait-ForMySql -timeoutSec 180# Read RabbitMQ creds from .env (defaults to guest/guest)
$rabbitUser = 'guest'
$rabbitPass = 'guest'
if (Test-Path .\.env) {
	$envLines = Get-Content .\.env | Where-Object {$_ -and ($_ -notmatch '^\s*#') }
	foreach ($line in $envLines) {
		if ($line -match '^\s*RABBITMQ_DEFAULT_USER\s*=\s*(.*)') { $rabbitUser = $matches[1].Trim() }
		if ($line -match '^\s*RABBITMQ_DEFAULT_PASS\s*=\s*(.*)') { $rabbitPass = $matches[1].Trim() }
	}
}

function Wait-ForRabbitMq([int]$timeoutSec = 60) {
	$start = Get-Date
	while ((Get-Date) - $start -lt (New-TimeSpan -Seconds $timeoutSec)) {
		# check AMQP port on localhost
		$portOk = Test-NetConnection -ComputerName 'localhost' -Port 5672 -InformationLevel Quiet
		if ($portOk) {
			# try management API
			try {
				$url = 'http://localhost:15672/api/overview'
				$creds = "${rabbitUser}:$rabbitPass"
				$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($creds))
				$resp = Invoke-RestMethod -Uri $url -Method Get -Headers @{ Authorization = "Basic $b64" } -ErrorAction Stop
				Write-Host "RabbitMQ management API ready"
				return $true
			} catch {
				Write-Host "AMQP port open but management API not ready yet..."
			}
		}
		Write-Host "Waiting for RabbitMQ to be ready..."
		Start-Sleep -Seconds 2
	}
	throw "RabbitMQ did not become ready within $timeoutSec seconds"
}

Write-Host "Waiting for RabbitMQ to become ready..."
Wait-ForRabbitMq -timeoutSec 120

Write-Host "Loading database schema into MySQL container (uses root password from .env - edit script if different)..."
Get-Content .\src\main\resources\sql\create_tables.sql | docker exec -i mysql sh -c "mysql -u root -prootpassword etl_db"

Write-Host "Running producer (one-off)..."
docker compose run --rm app-producer

Write-Host "Give consumers a moment to process messages (sleeping 5 seconds)..."
Start-Sleep -Seconds 5

Write-Host "Running transform (staging -> main)..."
docker compose run --rm app-transform

Write-Host "Done. Check RabbitMQ Management UI at http://localhost:15672 and inspect MySQL tables in 'etl_db'."