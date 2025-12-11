# 🎯 HƯỚNG DẪN SỬ DỤNG SCRIPT LOAD CSV

## 📁 Các file CSV mẫu đã có sẵn:

### Employees (Nhân viên):
- `employee_valid.csv` - 10 nhân viên HỢP LỆ
- `employee_invalid.csv` - 10 nhân viên KHÔNG HỢP LỆ
- `employee.csv` - File gốc (mixed)

### Orders (Đơn hàng):
- `order_valid.csv` - 10 đơn hàng HỢP LỆ  
- `order_invalid.csv` - 10 đơn hàng KHÔNG HỢP LỆ
- `order_detail.csv` - File gốc (mixed)

---

## 🚀 CÁCH SỬ DỤNG SCRIPT

### 1. Xem danh sách file có sẵn:

```powershell
.\scripts\load-csv.ps1
```

Sẽ hiển thị:
```
=== ETL CSV Loader ===

No CSV files specified. Available sample files:
  Employee files:
    - employee.csv
    - employee_invalid.csv
    - employee_valid.csv
  Order files:
    - order_detail.csv
    - order_invalid.csv
    - order_valid.csv

Usage examples:
  .\scripts\load-csv.ps1 -EmployeeFile 'employee_valid.csv'
  .\scripts\load-csv.ps1 -OrderFile 'order_invalid.csv'
  ...
```

---

### 2. Load chỉ Employees:

```powershell
# Load valid employees
.\scripts\load-csv.ps1 -EmployeeFile "employee_valid.csv" -RunTransform

# Load invalid employees  
.\scripts\load-csv.ps1 -EmployeeFile "employee_invalid.csv" -RunTransform
```

---

### 3. Load chỉ Orders:

```powershell
# Load valid orders
.\scripts\load-csv.ps1 -OrderFile "order_valid.csv" -RunTransform

# Load invalid orders
.\scripts\load-csv.ps1 -OrderFile "order_invalid.csv" -RunTransform
```

---

### 4. Load cả Employees và Orders:

```powershell
# Load both valid
.\scripts\load-csv.ps1 -EmployeeFile "employee_valid.csv" -OrderFile "order_valid.csv" -RunTransform

# Load both invalid
.\scripts\load-csv.ps1 -EmployeeFile "employee_invalid.csv" -OrderFile "order_invalid.csv" -RunTransform

# Mix: valid employees + invalid orders
.\scripts\load-csv.ps1 -EmployeeFile "employee_valid.csv" -OrderFile "order_invalid.csv" -RunTransform
```

---

### 5. Xóa dữ liệu cũ trước khi load:

```powershell
# Clear data first
.\scripts\load-csv.ps1 -EmployeeFile "employee_valid.csv" -ClearData -RunTransform
```

**Flag `-ClearData`** sẽ:
- TRUNCATE staging_employee
- TRUNCATE staging_order_detail
- TRUNCATE main_employee
- TRUNCATE main_order_detail

---

### 6. Load nhưng chưa Transform (load vào staging only):

```powershell
# Load to staging without transform
.\scripts\load-csv.ps1 -EmployeeFile "employee_valid.csv"

# Run transform manually later
docker run --rm --network etl-rabbitmq_default \
  -e MYSQL_HOST=mysql -e MYSQL_USER=etl -e MYSQL_PASSWORD=etlpass \
  etl-rabbitmq:latest transform
```

---

### 7. Load file CSV từ đường dẫn bất kỳ:

```powershell
# Load from absolute path
.\scripts\load-csv.ps1 -EmployeeFile "D:\MyData\my_employees.csv" -RunTransform

# Load from relative path
.\scripts\load-csv.ps1 -EmployeeFile "..\data\custom_employees.csv" -RunTransform
```

---

## 📝 FORMAT FILE CSV

### Employee CSV Format:
```
EmployeeID,FullName,Email,Phone
E001,Alice Smith,alice@example.com,+84901234567
E002,John Doe,john.doe@company.com,+84912345678
```

**Lưu ý:**
- Không có header row (không cần dòng tiêu đề)
- 4 columns: EmployeeID, FullName, Email, Phone
- Email phải hợp lệ (có @, domain)
- Phone phải theo format E.164: `^\+?[1-9]\d{1,14}$`

### Order CSV Format:
```
OrderID,ProductID,ProductName,Quantity,Price
O2001,P201,Laptop Dell XPS,5,1299.99
O2002,P202,iPhone 15 Pro,3,999.00
```

**Lưu ý:**
- Không có header row
- 5 columns: OrderID, ProductID, ProductName, Quantity, Price
- ProductID không được trống
- Quantity phải > 0

---

## 🎨 XEM KẾT QUẢ TRÊN DASHBOARD

Sau khi load xong, mở Dashboard:

**URL:** http://localhost:8080

Bạn sẽ thấy:

### **Thẻ màu ở trên:**

1. **Total Checked** - Tổng số records đã xử lý
2. **Staging** - Records còn trong staging (thường là invalid)
3. **Main** - Records đã chuyển sang main (valid)
4. **Passed (màu XANH)** - Số records HỢP LỆ 
5. **Errors (màu ĐỎ)** - Số records CÓ LỖI

### **Dữ Liệu Đã Transform (bên trái):**
- Dropdown chọn: Employees / Orders
- Hiển thị list records hợp lệ đã vào main tables

### **Lỗi Validation (bên phải - màu đỏ):**
- Dropdown chọn: Employees / Orders  
- Hiển thị list records có lỗi với chi tiết:
  - `[email] email is not a valid email`
  - `[phone] phone is not a valid phone number`
  - `[productId] productId must not be empty`
  - `[quantity] quantity must be greater than 0`

---

## 🧪 TEST SCENARIOS

### Scenario 1: Chỉ có valid data
```powershell
.\scripts\load-csv.ps1 -EmployeeFile "employee_valid.csv" -OrderFile "order_valid.csv" -ClearData -RunTransform
```
**Kết quả:**
- Passed (xanh): 20 (10 emp + 10 ord)
- Errors (đỏ): 0
- Main: 20
- Staging: 0

### Scenario 2: Chỉ có invalid data
```powershell
.\scripts\load-csv.ps1 -EmployeeFile "employee_invalid.csv" -OrderFile "order_invalid.csv" -ClearData -RunTransform
```
**Kết quả:**
- Passed (xanh): 0
- Errors (đỏ): 20 (10 emp + 10 ord)
- Main: 0
- Staging: 20

### Scenario 3: Mix valid + invalid
```powershell
# Load valid first
.\scripts\load-csv.ps1 -EmployeeFile "employee_valid.csv" -OrderFile "order_valid.csv" -ClearData -RunTransform

# Add invalid
.\scripts\load-csv.ps1 -EmployeeFile "employee_invalid.csv" -OrderFile "order_invalid.csv" -RunTransform
```
**Kết quả:**
- Passed (xanh): 20 (10 valid emp + 10 valid ord)
- Errors (đỏ): 20 (10 invalid emp + 10 invalid ord)
- Main: 20
- Staging: 20

---

## 🔍 VALIDATION RULES

### Email Rule:
- Dùng Apache Commons EmailValidator
- Phải có @
- Phải có domain
- Format chuẩn: `user@domain.com`

### Phone Rule:
- Regex: `^\+?[1-9]\d{1,14}$`
- Format E.164 quốc tế
- Có thể bắt đầu với +
- 7-15 digits
- Ví dụ hợp lệ: `+84901234567`, `84901234567`, `0901234567`

### ProductID Rule (NotEmpty):
- ProductID không được trống
- Phải có giá trị

### Quantity Rule:
- Quantity phải > 0
- Không chấp nhận số âm hoặc 0

---

## 💡 TIPS & TRICKS

### Tip 1: Tạo CSV custom của bạn
```csv
E999,Test User,test@example.com,+84999999999
E998,Another User,another@test.com,+84988888888
```

Load:
```powershell
.\scripts\load-csv.ps1 -EmployeeFile "D:\my_custom.csv" -RunTransform
```

### Tip 2: Load nhiều lần để tích lũy data
```powershell
# Load batch 1
.\scripts\load-csv.ps1 -EmployeeFile "employee_valid.csv" -RunTransform

# Load batch 2 (không xóa data cũ)
.\scripts\load-csv.ps1 -EmployeeFile "employee_invalid.csv" -RunTransform

# Load batch 3
.\scripts\load-csv.ps1 -OrderFile "order_valid.csv" -RunTransform
```

### Tip 3: Check staging trước khi transform
```powershell
# Load vào staging
.\scripts\load-csv.ps1 -EmployeeFile "employee_valid.csv"

# Check trong MySQL
docker exec -i mysql mysql -u root -prootpassword etl_db -e "SELECT * FROM staging_employee;"

# Transform sau
docker run --rm --network etl-rabbitmq_default \
  -e MYSQL_HOST=mysql -e MYSQL_USER=etl -e MYSQL_PASSWORD=etlpass \
  etl-rabbitmq:latest transform
```

### Tip 4: Export data từ main tables
```powershell
# Export to CSV
docker exec mysql mysql -u root -prootpassword etl_db \
  -e "SELECT * FROM main_employee INTO OUTFILE '/tmp/export.csv' FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';"
```

---

## 🐛 TROUBLESHOOTING

### Lỗi: "File not found"
**Giải pháp:** Dùng đường dẫn đầy đủ hoặc relative path từ project root

### Lỗi: "MySQL connection failed"
**Giải pháp:** 
```powershell
# Check Docker containers running
docker ps | Select-String mysql

# Restart MySQL
docker restart mysql
```

### Dashboard không update
**Giải pháp:** Nhấn F5 hoặc click nút "Refresh" trên Dashboard

### Data không vào main tables
**Giải pháp:** Check validation errors trong staging:
```sql
SELECT * FROM staging_employee WHERE validation_errors IS NOT NULL;
```

---

## 📚 TÀI LIỆU THAM KHẢO

- **HOW_IT_WORKS.md** - Cơ chế hoạt động chi tiết
- **QUICKSTART.md** - Hướng dẫn khởi động nhanh
- **README.md** - Tổng quan dự án
- **RELEASE_NOTES.md** - Tính năng v0.2.0

---

**Happy CSV Loading! 🎉**

Refresh Dashboard để thấy màu xanh (Passed) và màu đỏ (Errors) hiển thị rõ ràng!
