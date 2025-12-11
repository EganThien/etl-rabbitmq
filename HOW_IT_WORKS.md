# 🎯 CƠ CHẾ HOẠT ĐỘNG CỦA ETL PIPELINE VÀ DASHBOARD

## 📊 Dashboard Hiển Thị Gì?

### **Các thẻ đếm ở trên:**

1. **Total Checked**: 8 → 20 (tổng số records đã xử lý)
   - 10 employees + 10 orders = 20 records

2. **Staging**: 4 → 9 
   - Records KHÔNG HỢP LỆ còn lại trong staging tables
   - 5 invalid employees + 4 invalid orders = 9 records

3. **Main**: 4 → 11
   - Records HỢP LỆ đã chuyển sang main tables
   - 5 valid employees + 6 valid orders = 11 records

4. **Passed** (màu xanh): —
   - Đây là số records hợp lệ (should be 11)
   - Nếu không hiển thị số, có thể do dashboard logic chưa đếm đúng

5. **Errors** (màu đỏ): 
   - Đây là số records có validation errors (should be 9)
   - 5 employee errors + 4 order errors = 9 errors

---

## 🔄 QUY TRÌNH HOẠT ĐỘNG

### **Bước 1: Producer đọc CSV**
```
CSV Files (employee.csv, order_detail.csv)
    ↓
CSVProducer.java đọc từng dòng
    ↓
Publish messages lên RabbitMQ queues
```

### **Bước 2: Consumers nhận messages**
```
RabbitMQ Queues
    ↓
EmployeeConsumer + OrderConsumer
    ↓
Lưu vào Staging Tables (staging_employee, staging_order_detail)
```

### **Bước 3: Transform & Validation**
```
Staging Tables
    ↓
TransformLoad.java
    ├─→ Validate với Rules:
    │   - EmailRule (Apache Commons EmailValidator)
    │   - PhoneNumberRule (regex: ^\+?[1-9]\d{1,14}$)
    │   - NotEmptyRule (product_id không trống)
    │   - QuantityRule (quantity > 0)
    │
    ├─→ Records HỢP LỆ → Main Tables
    │   - main_employee
    │   - main_order_detail
    │
    └─→ Records KHÔNG HỢP LỆ → Giữ lại Staging
        - Thêm validation_errors JSON vào staging tables
```

### **Bước 4: Dashboard hiển thị**
```
Flask Dashboard (port 8080)
    ↓
Query MySQL
    ├─→ Main tables → "Dữ Liệu Đã Transform" (màu xanh/trắng)
    └─→ Staging errors → "Lỗi Validation" (màu đỏ)
```

---

## 🎨 MÀU SẮC TRÊN DASHBOARD

### **Màu XANH (Green) - Passed**
- Thẻ "Passed" màu xanh lá cây
- Hiển thị số lượng records HỢP LỆ đã vào main tables
- **Dự kiến**: 11 records (5 employees + 6 orders)

### **Màu ĐỎ (Red) - Errors**  
- Thẻ "Errors" màu đỏ
- Hiển thị số lượng records CÓ LỖI validation
- **Dự kiến**: 9 errors (5 employee errors + 4 order errors)

### **Màu TRẮNG/XÁM - Neutral**
- Total Checked, Staging, Main - màu trắng/xám
- Chỉ hiển thị thông tin thống kê

---

## 📋 DỮ LIỆU MẪU ĐÃ THÊM

### **✅ 5 EMPLOYEES HỢP LỆ (sẽ vào main_employee):**

| ID | Name | Email | Phone | Status |
|----|------|-------|-------|--------|
| E001 | Alice Smith | alice@example.com | +84901234567 | ✅ Valid |
| E002 | John Doe | john.doe@company.com | +84912345678 | ✅ Valid |
| E003 | Maria Garcia | maria.garcia@test.com | +84923456789 | ✅ Valid |
| E004 | Chen Wei | chen.wei@email.com | +84934567890 | ✅ Valid |
| E005 | Sarah Johnson | sarah.j@work.com | +84945678901 | ✅ Valid |

### **❌ 5 EMPLOYEES KHÔNG HỢP LỆ (giữ lại staging):**

| ID | Name | Email | Phone | Lỗi |
|----|------|-------|-------|-----|
| E006 | Bob Invalid | bob_at_company | 123 | ❌ Email thiếu @, Phone quá ngắn |
| E007 | Li Chen | li@test | +8499 | ❌ Email thiếu domain, Phone thiếu digits |
| E008 | Bad Email | notanemail | 456 | ❌ Email không hợp lệ, Phone quá ngắn |
| E009 | Short Phone | good@email.com | 12 | ❌ Phone quá ngắn |
| E010 | No Domain | missing@ | +84908639483 | ❌ Email thiếu domain |

### **✅ 6 ORDERS HỢP LỆ (sẽ vào main_order_detail):**

| Order ID | Product ID | Quantity | Price | Status |
|----------|-----------|----------|-------|--------|
| O1001 | P001 | 5 | 1500.00 | ✅ Valid |
| O1002 | P002 | 10 | 250.50 | ✅ Valid |
| O1003 | P003 | 3 | 99.99 | ✅ Valid |
| O1004 | P004 | 1 | 2500.00 | ✅ Valid |
| O1005 | P005 | 20 | 15.75 | ✅ Valid |
| O1006 | P006 | 7 | 450.00 | ✅ Valid |

### **❌ 4 ORDERS KHÔNG HỢP LỆ (giữ lại staging):**

| Order ID | Product ID | Quantity | Price | Lỗi |
|----------|-----------|----------|-------|-----|
| O1007 | (empty) | 5 | 100.00 | ❌ Product ID trống |
| O1008 | P008 | -5 | 50.00 | ❌ Quantity âm |
| O1009 | (empty) | 3 | 75.00 | ❌ Product ID trống |
| O1010 | P010 | -10 | 200.00 | ❌ Quantity âm |

---

## 🔍 VALIDATION ERRORS JSON

Ví dụ validation_errors trong staging_employee:

```json
[
  {
    "field": "email",
    "rule": "EmailRule", 
    "message": "Email must be valid"
  },
  {
    "field": "phone",
    "rule": "PhoneNumberRule",
    "message": "Phone must match international format (E.164)"
  }
]
```

Ví dụ validation_errors trong staging_order_detail:

```json
[
  {
    "field": "product_id",
    "rule": "NotEmptyRule",
    "message": "productId must not be empty"
  }
]
```

hoặc

```json
[
  {
    "field": "quantity",
    "rule": "QuantityRule",
    "message": "quantity must be greater than 0"
  }
]
```

---

## 📈 CÁCH XEM DỮ LIỆU CHI TIẾT

### **1. Xem records hợp lệ trong main tables:**

```sql
-- Employees hợp lệ
SELECT * FROM main_employee;

-- Orders hợp lệ  
SELECT * FROM main_order_detail;
```

### **2. Xem validation errors trong staging:**

```sql
-- Employee errors
SELECT id, employee_id, full_name, email, phone, validation_errors
FROM staging_employee
WHERE validation_errors IS NOT NULL;

-- Order errors
SELECT id, order_id, product_id, quantity, validation_errors
FROM staging_order_detail  
WHERE validation_errors IS NOT NULL;
```

### **3. Đếm số lượng:**

```sql
-- Tổng hợp
SELECT 
  'Main Employees' as type, COUNT(*) as count FROM main_employee
UNION ALL
SELECT 'Main Orders', COUNT(*) FROM main_order_detail
UNION ALL
SELECT 'Employee Errors', COUNT(*) FROM staging_employee WHERE validation_errors IS NOT NULL
UNION ALL
SELECT 'Order Errors', COUNT(*) FROM staging_order_detail WHERE validation_errors IS NOT NULL;
```

---

## 🎯 KẾT QUẢ DỰ KIẾN TRÊN DASHBOARD

Sau khi refresh trang (F5 hoặc nhấn Refresh):

### **Summary Cards:**
- **Total Checked**: 20
- **Staging**: 9 (records có lỗi)
- **Main**: 11 (records hợp lệ)
- **Passed** (xanh): 11
- **Errors** (đỏ): 9

### **Dữ Liệu Đã Transform (bên trái):**
- Dropdown chọn: Employees / Orders
- Hiển thị list 11 records hợp lệ
- Ví dụ: Alice Smith, John Doe, Maria Garcia...

### **Lỗi Validation (bên phải - màu đỏ):**
- Dropdown chọn: Employees / Orders
- Hiển thị list 9 records có lỗi với chi tiết:
  - **id: 6** - Bob Invalid
    - `[email] Email must be valid`
    - `[phone] Phone must match international format`
  - **id: 7** - Li Chen
    - `[email] Email must be valid`
    - `[phone] Phone must match international format`
  - **id: 4** (Order O1007)
    - `[productId] productId must not be empty`
  - **id: 5** (Order O1008)
    - `[quantity] quantity must be greater than 0`

---

## 🔧 LÀM THẾ NÀO ĐỂ THÊM DỮ LIỆU?

### **Cách 1: Insert trực tiếp vào staging**

```powershell
# Run file SQL đã tạo
Get-Content .\scripts\insert-sample-data.sql | docker exec -i mysql mysql -u root -prootpassword etl_db

# Chạy Transform
docker run --rm --network etl-rabbitmq_default \
  -e MYSQL_HOST=mysql -e MYSQL_USER=etl -e MYSQL_PASSWORD=etlpass \
  etl-rabbitmq:latest transform

# Refresh Dashboard
```

### **Cách 2: Sửa file CSV và chạy Producer**

```powershell
# 1. Sửa file employee.csv hoặc order_detail.csv
# 2. Chạy Producer
java -cp target/etl-rabbitmq-0.2.0.jar com.example.etl.Application producer

# 3. Consumers tự động consume (đang chạy trong Docker)
# 4. Chạy Transform
docker run --rm --network etl-rabbitmq_default \
  -e MYSQL_HOST=mysql -e MYSQL_USER=etl -e MYSQL_PASSWORD=etlpass \
  etl-rabbitmq:latest transform

# 5. Refresh Dashboard
```

### **Cách 3: Tạo script PowerShell tự động**

```powershell
# .\scripts\add-more-data.ps1
$employees = @"
INSERT INTO staging_employee (employee_id, full_name, email, phone) VALUES
('E011', 'Test User', 'test@example.com', '+84956789012'),
('E012', 'Invalid User', 'bad-email', '99');
"@

$employees | docker exec -i mysql mysql -u root -prootpassword etl_db

docker run --rm --network etl-rabbitmq_default \
  -e MYSQL_HOST=mysql -e MYSQL_USER=etl -e MYSQL_PASSWORD=etlpass \
  etl-rabbitmq:latest transform
  
Write-Host "Data added! Refresh dashboard: http://localhost:8080"
```

---

## 🐛 TROUBLESHOOTING

### **Không thấy màu xanh "Passed":**
- Kiểm tra query trong `dashboard/app.py` function `get_errors_count()`
- Có thể cần thêm function `get_passed_count()` để đếm records hợp lệ

### **Errors card không hiển thị số:**
- Dashboard đang query nhưng không hiển thị
- Check console logs: `docker logs etl-rabbitmq-etl-dashboard-1`

### **Data không update:**
- Nhấn F5 để refresh trang
- Hoặc click nút "Refresh" trên Dashboard

### **Muốn xóa hết và bắt đầu lại:**

```sql
TRUNCATE staging_employee;
TRUNCATE staging_order_detail;
TRUNCATE main_employee;
TRUNCATE main_order_detail;
```

---

## 📚 TÀI LIỆU THAM KHẢO

- **QUICKSTART.md**: Hướng dẫn chạy nhanh
- **README.md**: Tổng quan dự án
- **RELEASE_NOTES.md**: Chi tiết tính năng v0.2.0
- **CHANGELOG.md**: Lịch sử thay đổi

---

**Refresh Dashboard và bạn sẽ thấy 11 records màu xanh (hợp lệ) và 9 errors màu đỏ!** 🎉
