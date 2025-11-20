# Stop and remove all containers for this compose setup
# Usage: .\scripts\stop-all.ps1

docker compose down
Write-Host "Stopped and removed containers."