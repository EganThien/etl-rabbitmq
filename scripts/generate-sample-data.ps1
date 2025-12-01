<#
Generate synthetic rows and append to existing CSVs in `src/main/resources/data`.

Usage:
  .\generate-sample-data.ps1 -EmployeeCount 500 -OrderCount 2000 -InvalidRatio 0.05

Parameters:
  -EmployeeCount: number of employee rows to append (default 100)
  -OrderCount: number of order_detail rows to append (default 500)
  -InvalidRatio: fraction of rows that should be intentionally invalid (0..1)

Notes:
  - Script appends to existing CSVs. It attempts to preserve header if present.
  - Invalid rows will produce e.g. empty fullName or malformed email or zero quantity.
  - Ensure you have a backup of CSVs if you need to revert.
#>

param(
    [int]$EmployeeCount = 100,
    [int]$OrderCount = 500,
    [double]$InvalidRatio = 0.05
)

Set-StrictMode -Version Latest
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $scriptDir\..

$dataDir = Join-Path $PWD 'src\main\resources\data'
$empFile = Join-Path $dataDir 'employee.csv'
$odFile = Join-Path $dataDir 'order_detail.csv'

function Ensure-FileHeader($filePath, $headerLine) {
    if (-not (Test-Path $filePath)) {
        Write-Host "Creating $filePath with header"
        New-Item -ItemType File -Path $filePath -Force | Out-Null
        Add-Content -Path $filePath -Value $headerLine -Encoding UTF8
    } else {
        $first = Get-Content -Path $filePath -TotalCount 1 -ErrorAction SilentlyContinue
        if ($null -eq $first -or $first.Trim() -ne $headerLine.Trim()) {
            # If file exists but header missing, insert header at top
            Write-Host "Inserting header into existing $filePath"
            $rest = Get-Content -Path $filePath -ErrorAction SilentlyContinue
            Set-Content -Path $filePath -Value $headerLine -Encoding UTF8
            if ($rest) { Add-Content -Path $filePath -Value $rest -Encoding UTF8 }
        }
    }
}

Ensure-FileHeader -filePath $empFile -headerLine 'employeeId,fullName,email'
Ensure-FileHeader -filePath $odFile -headerLine 'orderId,productId,quantity,price'

# find starting indices based on existing rows
$existingEmpCount = (Get-Content $empFile -ErrorAction SilentlyContinue | Measure-Object -Line).Lines - 1
if ($existingEmpCount -lt 0) { $existingEmpCount = 0 }
$existingOrderCount = (Get-Content $odFile -ErrorAction SilentlyContinue | Measure-Object -Line).Lines - 1
if ($existingOrderCount -lt 0) { $existingOrderCount = 0 }

Write-Host "Existing rows - employees: $existingEmpCount, orders: $existingOrderCount"

function RandInt($min, $max) { return Get-Random -Minimum $min -Maximum ($max + 1) }
function RandDouble($min, $max) { return [math]::Round((Get-Random) * ($max - $min) + $min, 2) }

# append employees
$empAppended = 0
for ($i = 1; $i -le $EmployeeCount; $i++) {
    $idx = $existingEmpCount + $i
    $empId = "E$idx"
    # random invalidation
    $r = Get-Random
    $isInvalid = ($r -lt $InvalidRatio)
    if ($isInvalid) {
        # create invalid row: either empty fullName or bad email
        if ((Get-Random -Maximum 2) -eq 0) {
            $fullName = ''
            $email = "$empId@example.com"
        } else {
            $fullName = "User $idx"
            $email = "invalid-email-$idx"
        }
    } else {
        $fullName = "Nguyen Van $idx"
        $email = "$empId@example.com"
    }
    $line = "$empId,$fullName,$email"
    Add-Content -Path $empFile -Value $line -Encoding UTF8
    $empAppended++
}

# append orders
$orderAppended = 0
for ($j = 1; $j -le $OrderCount; $j++) {
    $idx = $existingOrderCount + $j
    $orderId = "O$idx"
    # pick a product id
    $productId = "P" + (RandInt 1 100)
    $r2 = Get-Random
    $isInvalidOrder = ($r2 -lt $InvalidRatio)
    if ($isInvalidOrder) {
        # invalid: quantity zero
        $quantity = 0
    } else {
        $quantity = RandInt 1 10
    }
    $price = RandDouble 1 200
    $line = "$orderId,$productId,$quantity,$price"
    Add-Content -Path $odFile -Value $line -Encoding UTF8
    $orderAppended++
}

Write-Host "Appended $empAppended employee rows to $empFile"
Write-Host "Appended $orderAppended order rows to $odFile"

Pop-Location
<#
Generate sample CSV rows for employee.csv and order_detail.csv

Usage examples:
  # generate 500 employees and 2000 orders (default invalid ratio 5%)
  .\scripts\generate-sample-data.ps1 -EmployeeCount 500 -OrderCount 2000

  # generate with 10% invalid rows
  .\scripts\generate-sample-data.ps1 -EmployeeCount 100 -OrderCount 500 -InvalidRatio 0.1

This script will create a timestamped backup of each CSV before appending.
#>

param(
    [int]$EmployeeCount = 100,
    [int]$OrderCount = 500,
    [double]$InvalidRatio = 0.05
)

Set-StrictMode -Version Latest
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $scriptDir\..

function Backup-File([string]$path) {
    if (Test-Path $path) {
        $now = Get-Date -Format "yyyyMMdd_HHmmss"
        $dest = "$path.$now.bak"
        Copy-Item $path $dest -Force
        Write-Host "Backed up $path -> $dest"
    }
}

function Append-Employees([int]$n, [double]$invalidRatio) {
    $f = "src\main\resources\data\employee.csv"
    if (-not (Test-Path $f)) { Write-Error "Employee CSV not found: $f"; return }
    Backup-File $f

    $rand = New-Object System.Random
    $lines = @()
    $startIndex = (Get-Content $f | Measure-Object -Line).Lines
    for ($i=1; $i -le $n; $i++) {
        $idx = $startIndex + $i
        $empId = "E" + $idx.ToString("D6")
        $first = @("Nguyen","Tran","Le","Pham","Hoang","Pham","Vu","Dao","Bui","Do")[$rand.Next(0,10)]
        $last = @("Van","Thi","Quang","Minh","Anh","Lan","Huong","Hieu","Long","Hoa")[$rand.Next(0,10)]
        $full = "$first $last $idx"
        #  introduce invalid emails with probability invalidRatio
        if ($rand.NextDouble() -lt $invalidRatio) {
            $email = "invalid-email-$idx"
        } else {
            $email = "$first.$last$idx@example.com" -replace "\s+",""
        }
        $lines += "$empId,$full,$email"
    }
    $lines | Out-File -FilePath $f -Encoding UTF8 -Append
    Write-Host "Appended $n employee rows to $f"
}

function Append-Orders([int]$n, [double]$invalidRatio) {
    $f = "src\main\resources\data\order_detail.csv"
    if (-not (Test-Path $f)) { Write-Error "Order CSV not found: $f"; return }
    Backup-File $f

    $rand = New-Object System.Random
    $lines = @()
    $startIndex = (Get-Content $f | Measure-Object -Line).Lines
    for ($i=1; $i -le $n; $i++) {
        $idx = $startIndex + $i
        $orderId = "O" + $idx.ToString("D8")
        $productId = "P" + ($rand.Next(1,200)).ToString("D4")
        # quantity: sometimes zero to simulate invalid
        if ($rand.NextDouble() -lt $invalidRatio) { $qty = 0 } else { $qty = $rand.Next(1,20) }
        $price = "{0:N2}" -f ($rand.NextDouble() * 500 + 1)
        $lines += "$orderId,$productId,$qty,$price"
    }
    $lines | Out-File -FilePath $f -Encoding UTF8 -Append
    Write-Host "Appended $n order_detail rows to $f"
}

try {
    Append-Employees -n $EmployeeCount -invalidRatio $InvalidRatio
    Append-Orders -n $OrderCount -invalidRatio $InvalidRatio
} finally {
    Pop-Location
}
