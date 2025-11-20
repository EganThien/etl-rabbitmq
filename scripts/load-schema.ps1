cd D:\1.ProjectTuHoc\DA_TichHopHeThong\etl-rabbitmq
# Load DB schema into MySQL container
# Usage: .\scripts\load-schema.ps1

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
			# Try using docker compose exec (works when running in the compose project)
			Write-Host "Checking MySQL readiness via 'docker compose exec'..."
			$res = & docker compose exec -T mysql mysql -u root -p$rootpass -e "SELECT 1;" 2>&1
			if ($LASTEXITCODE -eq 0) {
				Write-Host "MySQL is ready (docker compose exec)"
				return $true
			}
		} catch {
			# ignore and try fallback
		}

		try {
			# Fallback: find a container whose name contains 'mysql' and use docker exec
			$cid = (& docker ps -q --filter "name=mysql") -split "\r?\n" | Where-Object { $_ -ne '' } | Select-Object -First 1
			if ($cid) {
				Write-Host "Checking MySQL readiness via 'docker exec' on container id $cid..."
				$res2 = & docker exec $cid mysql -u root -p$rootpass -e "SELECT 1;" 2>&1
				if ($LASTEXITCODE -eq 0) {
					Write-Host "MySQL is ready (docker exec $cid)"
					return $true
				}
			} else {
				Write-Host "No running container with name containing 'mysql' found yet. Showing 'docker compose ps' to help debugging:"
				& docker compose ps
			}
		} catch {
			# ignore
		}

		Write-Host "Waiting for MySQL to be ready..."
		Start-Sleep -Seconds 5
	}
	throw "MySQL did not become ready within $timeoutSec seconds"
}

Write-Host "Waiting for MySQL to become ready..."
Wait-ForMySql -timeoutSec 300

Get-Content .\src\main\resources\sql\create_tables.sql | docker exec -i mysql sh -c "mysql -u root -p$rootpass etl_db"
Write-Host "Schema loaded into MySQL (database: etl_db)."