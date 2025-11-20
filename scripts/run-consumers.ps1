# Start consumers (run in background)
# Usage: .\scripts\run-consumers.ps1

# Read RabbitMQ creds and MySQL root password from .env
$rabbitUser = 'guest'
$rabbitPass = 'guest'
$rootpass = 'rootpassword'
if (Test-Path .\.env) {
	$envLines = Get-Content .\.env | Where-Object {$_ -and ($_ -notmatch '^\s*#') }
	foreach ($line in $envLines) {
		if ($line -match '^\s*RABBITMQ_DEFAULT_USER\s*=\s*(.*)') { $rabbitUser = $matches[1].Trim() }
		if ($line -match '^\s*RABBITMQ_DEFAULT_PASS\s*=\s*(.*)') { $rabbitPass = $matches[1].Trim() }
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
		}
		Write-Host "Waiting for MySQL to be ready..."
		Start-Sleep -Seconds 2
	}
	throw "MySQL did not become ready within $timeoutSec seconds"
}

function Wait-ForRabbitMq([int]$timeoutSec = 60) {
	$start = Get-Date
	while ((Get-Date) - $start -lt (New-TimeSpan -Seconds $timeoutSec)) {
		$portOk = Test-NetConnection -ComputerName 'localhost' -Port 5672 -InformationLevel Quiet
		if ($portOk) {
			try {
				$url = 'http://localhost:15672/api/overview'
				$creds = "$rabbitUser:$rabbitPass"
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

Write-Host "Waiting for RabbitMQ and MySQL readiness..."
Wait-ForRabbitMq -timeoutSec 120
Wait-ForMySql -timeoutSec 120

docker compose up -d app-employee-consumer app-order-consumer
Write-Host "Consumers started in background. Use 'docker compose logs -f <service>' to follow logs." 