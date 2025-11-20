# Run transform (one-off)
# Usage: .\scripts\run-transform.ps1

docker compose run --rm app-transform
Write-Host "Transform completed."