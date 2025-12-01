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
			# Prefer checking container id directly with mysqladmin ping
			$cid = (& docker ps -q --filter "name=mysql") -split "\r?\n" | Where-Object { $_ -ne '' } | Select-Object -First 1
			if ($cid) {
				Write-Host "Found mysql container id: $cid - checking with mysqladmin ping..."
				$pingOut = & docker exec $cid mysqladmin ping -u root -p$rootpass --silent 2>&1
				if ($LASTEXITCODE -eq 0) {
					Write-Host "MySQL is ready (docker exec mysqladmin ping)"
					return $true
				} else {
					Write-Host "mysqladmin ping failed: $pingOut"
				}
			} else {
				Write-Host "No running container with name containing 'mysql' found yet. Showing 'docker compose ps' to help debugging:"
				& docker compose ps
			}
		} catch {
			Write-Host "Error while checking mysql (docker exec): $_"
		}

		try {
			# Fallback to docker compose exec if available
			Write-Host "Checking MySQL readiness via 'docker compose exec'..."
			$res = & docker compose exec -T mysql mysqladmin ping -u root -p$rootpass --silent 2>&1
			if ($LASTEXITCODE -eq 0) {
				Write-Host "MySQL is ready (docker compose exec mysqladmin ping)"
				return $true
			} else {
				Write-Host "docker compose exec mysqladmin ping output: $res"
			}
		} catch {
			Write-Host "Error while checking mysql (docker compose exec): $_"
		}

		Write-Host "Waiting for MySQL to be ready..."
		Start-Sleep -Seconds 5
	}
	throw "MySQL did not become ready within $timeoutSec seconds"
}

Write-Host "Waiting for MySQL to become ready..."
Wait-ForMySql -timeoutSec 300

$cidFinal = (& docker ps -q --filter "name=mysql") -split "\r?\n" | Where-Object { $_ -ne '' } | Select-Object -First 1
if ($cidFinal) {
	Write-Host "Loading schema into container $cidFinal ..."
	Get-Content .\src\main\resources\sql\create_tables.sql | docker exec -i $cidFinal sh -c "mysql -u root -p$rootpass etl_db"
} else {
	Write-Host "No mysql container id found; attempting to use docker exec by name 'mysql'..."
	Get-Content .\src\main\resources\sql\create_tables.sql | docker exec -i mysql sh -c "mysql -u root -p$rootpass etl_db"
}
Write-Host "Schema loaded into MySQL (database: etl_db)."