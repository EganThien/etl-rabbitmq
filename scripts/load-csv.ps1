# Script để chọn và load CSV files tùy ý vào ETL Pipeline
# Usage: .\scripts\load-csv.ps1 -EmployeeFile "path\to\employees.csv" -OrderFile "path\to\orders.csv"

param(
    [Parameter(HelpMessage="Path to employee CSV file")]
    [string]$EmployeeFile = "",
    
    [Parameter(HelpMessage="Path to order CSV file")]
    [string]$OrderFile = "",
    
    [Parameter(HelpMessage="Run transform after loading")]
    [switch]$RunTransform = $false,
    
    [Parameter(HelpMessage="Clear existing data before loading")]
    [switch]$ClearData = $false
)

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)
Set-Location -Path $projectRoot

Write-Host "=== ETL CSV Loader ===" -ForegroundColor Cyan

# Check if no files provided - show file picker
if ([string]::IsNullOrEmpty($EmployeeFile) -and [string]::IsNullOrEmpty($OrderFile)) {
    Write-Host "`nNo CSV files specified. Available sample files:" -ForegroundColor Yellow
    Write-Host "  Employee files:"
    Get-ChildItem "src\main\resources\data\employee*.csv" | ForEach-Object { Write-Host "    - $($_.Name)" -ForegroundColor Green }
    Write-Host "  Order files:"
    Get-ChildItem "src\main\resources\data\order*.csv" | ForEach-Object { Write-Host "    - $($_.Name)" -ForegroundColor Green }
    
    Write-Host "`nUsage examples:" -ForegroundColor Cyan
    Write-Host "  .\scripts\load-csv.ps1 -EmployeeFile 'src\main\resources\data\employee_valid.csv'"
    Write-Host "  .\scripts\load-csv.ps1 -OrderFile 'src\main\resources\data\order_invalid.csv'"
    Write-Host "  .\scripts\load-csv.ps1 -EmployeeFile 'employee_valid.csv' -OrderFile 'order_valid.csv' -RunTransform"
    Write-Host "  .\scripts\load-csv.ps1 -EmployeeFile 'employee_invalid.csv' -ClearData -RunTransform"
    exit 0
}

# Clear data if requested
if ($ClearData) {
    Write-Host "`nClearing existing data..." -ForegroundColor Yellow
    $clearSQL = @"
TRUNCATE staging_employee;
TRUNCATE staging_order_detail;
TRUNCATE main_employee;
TRUNCATE main_order_detail;
"@
    $clearSQL | docker exec -i mysql mysql -u root -prootpassword etl_db 2>&1 | Out-Null
    Write-Host "Data cleared successfully!" -ForegroundColor Green
}

# Process Employee CSV
if (-not [string]::IsNullOrEmpty($EmployeeFile)) {
    if (-not (Test-Path $EmployeeFile)) {
        # Try relative path
        $EmployeeFile = Join-Path "src\main\resources\data" $EmployeeFile
    }
    
    if (Test-Path $EmployeeFile) {
        Write-Host "`nProcessing Employee CSV: $EmployeeFile" -ForegroundColor Cyan
        $empCount = 0
        Get-Content $EmployeeFile | ForEach-Object {
            if ($_ -match ',') {
                $parts = $_ -split ','
                if ($parts.Length -ge 4) {
                    $empId = $parts[0].Trim()
                    $fullName = $parts[1].Trim()
                    $email = $parts[2].Trim()
                    $phone = $parts[3].Trim()
                    
                    $insertSQL = "INSERT INTO staging_employee (employee_id, full_name, email, phone) VALUES ('$empId', '$fullName', '$email', '$phone');"
                    $insertSQL | docker exec -i mysql mysql -u root -prootpassword etl_db 2>&1 | Out-Null
                    $empCount++
                    Write-Host "  Inserted: $empId - $fullName" -ForegroundColor Gray
                }
            }
        }
        Write-Host "Total employees inserted: $empCount" -ForegroundColor Green
    } else {
        Write-Host "Employee file not found: $EmployeeFile" -ForegroundColor Red
    }
}

# Process Order CSV
if (-not [string]::IsNullOrEmpty($OrderFile)) {
    if (-not (Test-Path $OrderFile)) {
        # Try relative path
        $OrderFile = Join-Path "src\main\resources\data" $OrderFile
    }
    
    if (Test-Path $OrderFile) {
        Write-Host "`nProcessing Order CSV: $OrderFile" -ForegroundColor Cyan
        $orderCount = 0
        Get-Content $OrderFile | ForEach-Object {
            if ($_ -match ',') {
                $parts = $_ -split ','
                if ($parts.Length -ge 5) {
                    $orderId = $parts[0].Trim()
                    $productId = $parts[1].Trim()
                    $productName = $parts[2].Trim()
                    $quantity = $parts[3].Trim()
                    $price = $parts[4].Trim()
                    
                    $insertSQL = "INSERT INTO staging_order_detail (order_id, product_id, quantity, price) VALUES ('$orderId', '$productId', $quantity, $price);"
                    $insertSQL | docker exec -i mysql mysql -u root -prootpassword etl_db 2>&1 | Out-Null
                    $orderCount++
                    Write-Host "  Inserted: $orderId - $productName (qty: $quantity)" -ForegroundColor Gray
                }
            }
        }
        Write-Host "Total orders inserted: $orderCount" -ForegroundColor Green
    } else {
        Write-Host "Order file not found: $OrderFile" -ForegroundColor Red
    }
}

# Show staging counts
Write-Host "`nStaging table counts:" -ForegroundColor Cyan
$countSQL = @"
SELECT 'Employees' as type, COUNT(*) as count FROM staging_employee
UNION ALL
SELECT 'Orders', COUNT(*) FROM staging_order_detail;
"@
$countSQL | docker exec -i mysql mysql -u root -prootpassword etl_db 2>&1 | Select-String -Pattern "type|Employees|Orders|[0-9]"

# Run transform if requested
if ($RunTransform) {
    Write-Host "`nRunning Transform & Validation..." -ForegroundColor Cyan
    docker run --rm --network etl-rabbitmq_default `
        -e MYSQL_HOST=mysql `
        -e MYSQL_USER=etl `
        -e MYSQL_PASSWORD=etlpass `
        etl-rabbitmq:latest transform
    
    Write-Host "`nTransform completed! Check dashboard: http://localhost:8080" -ForegroundColor Green
} else {
    Write-Host "`nData loaded to staging. Run transform manually:" -ForegroundColor Yellow
    Write-Host "  docker run --rm --network etl-rabbitmq_default -e MYSQL_HOST=mysql -e MYSQL_USER=etl -e MYSQL_PASSWORD=etlpass etl-rabbitmq:latest transform"
    Write-Host "Or re-run with -RunTransform flag" -ForegroundColor Yellow
}

Write-Host "`nDone! View results at http://localhost:8080" -ForegroundColor Green
