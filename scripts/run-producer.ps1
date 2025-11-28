# Run producer one-off
# Usage: .\scripts\run-producer.ps1

# Read RabbitMQ creds from .env (defaults to guest/guest)
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
		$portOk = Test-NetConnection -ComputerName 'localhost' -Port 5672 -InformationLevel Quiet
		if ($portOk) {
			try {
				$url = 'http://localhost:15672/api/overview'
				# Build credentials safely to avoid PowerShell variable parsing issues
				$creds = "${rabbitUser}:${rabbitPass}"
				$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($creds))
				$resp = Invoke-RestMethod -Uri $url -Method Get -Headers @{ Authorization = "Basic $b64" } -ErrorAction Stop
				Write-Host "RabbitMQ management API ready"
				return $true
			} catch {
				Write-Host "AMQP port open but management API not ready yet..."
			}
		}
		Start-Sleep -Seconds 2
	}
	throw "RabbitMQ did not become ready within $timeoutSec seconds"
}

Write-Host "Waiting for RabbitMQ to become ready..."
Wait-ForRabbitMq -timeoutSec 120

docker compose run --rm app-producer
Write-Host "Producer completed."