# BÁO CÁO ĐỒ ÁN - PHẦN 2

# CHƯƠNG 3: PHÂN TÍCH VÀ THIẾT KẾ

## 3.1. Phân tích yêu cầu

### 3.1.1. Yêu cầu chức năng

**FR1: Extract Data**
- Hệ thống phải đọc được file CSV (employee, order)
- Parse CSV thành Java Objects
- Publish lên RabbitMQ queues

**FR2: Validate Data**
- Validate theo rules: NOT NULL, Email format, Phone format, Quantity > 0
- Lưu errors dạng JSON trong staging tables
- Có thể re-validate sau khi sửa lỗi

**FR3: Transform Data**
- Chuẩn hóa tên (Title Case)
- Chuẩn hóa email (lowercase)
- Chuẩn hóa phone (E.164 format)
- Log audit trail cho mọi thay đổi

**FR4: Load Data**
- Insert dữ liệu đã clean vào main tables
- Lưu original data để rollback
- Delete dữ liệu valid khỏi staging

**FR5: Dashboard**
- Upload CSV files
- Xem staging data và errors
- Trigger transform
- Xem main data
- Xem audit trail

### 3.1.2. Yêu cầu phi chức năng

**NFR1: Performance**
- Xử lý tối thiểu 300 records/second
- Transform trong vòng 10s cho 1000 records

**NFR2: Scalability**
- Có thể thêm Consumers để tăng throughput
- Horizontal scaling

**NFR3: Fault Tolerance**
- Message không bị mất khi Consumer die
- Dùng RabbitMQ persistent messages + manual ACK

**NFR4: Maintainability**
- Code modular, dễ extend
- Validation rules trong database (không hard-code)

**NFR5: Observability**
- Dashboard hiển thị metrics
- Audit trail đầy đủ

### 3.1.3. Use Cases

**Actor: Data Operator**

**UC1: Upload CSV**
1. User chọn file type (Employee/Order)
2. User upload file CSV
3. System parse và insert vào staging
4. System hiển thị kết quả

**UC2: View Validation Errors**
1. User truy cập dashboard
2. System hiển thị records có errors
3. User xem chi tiết errors (JSON)

**UC3: Run Transform**
1. User click "Run Transform"
2. System chạy Stage 1 (Validation)
3. System chạy Stage 2 (Transform + Load)
4. System hiển thị kết quả (số records thành công, lỗi)

**UC4: View Audit Trail**
1. User truy cập History page
2. System hiển thị field-level changes
3. User xem original value → transformed value

## 3.2. Thiết kế cơ sở dữ liệu

### 3.2.1. Data Source (Staging Tables)

Staging tables lưu dữ liệu tạm thời từ CSV, bao gồm cả dữ liệu lỗi.

**staging_employee**

| Column | Type | Ý nghĩa |
|--------|------|---------|
| id | INT PRIMARY KEY | ID tự tăng |
| employee_id | VARCHAR(20) | Mã nhân viên |
| full_name | VARCHAR(100) | Họ tên |
| email | VARCHAR(100) | Email |
| phone | VARCHAR(20) | Số điện thoại |
| batch_id | VARCHAR(50) | ID batch upload |
| validation_errors | JSON | Lỗi validation (nếu có) |
| created_at | TIMESTAMP | Thời gian tạo |

**validation_errors format:**
```json
[
  {"field": "email", "message": "Email không đúng định dạng"},
  {"field": "phone", "message": "Số điện thoại không hợp lệ"}
]
```

**staging_order_detail**

| Column | Type | Ý nghĩa |
|--------|------|---------|
| id | INT PRIMARY KEY | ID tự tăng |
| order_id | VARCHAR(20) | Mã đơn hàng |
| product_id | VARCHAR(20) | Mã sản phẩm |
| quantity | INT | Số lượng |
| price | DECIMAL(15,2) | Giá |
| batch_id | VARCHAR(50) | ID batch upload |
| validation_errors | JSON | Lỗi validation |
| created_at | TIMESTAMP | Thời gian tạo |

### 3.2.2. Data Quality (Data Lake)

Main tables lưu dữ liệu đã clean và chuẩn hóa.

**main_employee**

| Column | Type | Ý nghĩa |
|--------|------|---------|
| id | INT PRIMARY KEY | ID tự tăng |
| employee_id | VARCHAR(20) UNIQUE | Mã nhân viên (unique) |
| full_name | VARCHAR(100) | Họ tên đã chuẩn hóa |
| email | VARCHAR(100) | Email đã chuẩn hóa |
| phone | VARCHAR(20) | Phone format E.164 |
| batch_id | VARCHAR(50) | Batch ID transform |
| original_data | JSON | Dữ liệu gốc (backup) |
| created_at | TIMESTAMP | Thời gian tạo |
| updated_at | TIMESTAMP | Thời gian cập nhật |

**main_order_detail**

| Column | Type | Ý nghĩa |
|--------|------|---------|
| id | INT PRIMARY KEY | ID tự tăng |
| order_id | VARCHAR(20) | Mã đơn hàng |
| product_id | VARCHAR(20) | Mã sản phẩm đã chuẩn hóa |
| quantity | INT | Số lượng |
| price | DECIMAL(15,2) | Giá đã làm tròn |
| batch_id | VARCHAR(50) | Batch ID |
| original_data | JSON | Dữ liệu gốc |
| created_at | TIMESTAMP | Thời gian tạo |

**audit_trail**

| Column | Type | Ý nghĩa |
|--------|------|---------|
| id | INT PRIMARY KEY | ID tự tăng |
| entity_type | VARCHAR(50) | employee/order |
| entity_id | INT | ID của record |
| field_name | VARCHAR(50) | Tên field thay đổi |
| old_value | TEXT | Giá trị cũ |
| new_value | TEXT | Giá trị mới |
| transform_rule | VARCHAR(50) | Rule áp dụng |
| batch_id | VARCHAR(50) | Batch ID |
| created_at | TIMESTAMP | Thời gian thay đổi |

### 3.2.3. Rules Tables

**validation_rules**

| Column | Type | Ý nghĩa |
|--------|------|---------|
| id | INT PRIMARY KEY | ID tự tăng |
| rule_code | VARCHAR(20) UNIQUE | Mã rule (R1, R2...) |
| rule_name | VARCHAR(100) | Tên rule |
| entity_type | VARCHAR(50) | employee/order |
| field_name | VARCHAR(50) | Field áp dụng |
| rule_type | VARCHAR(50) | validation/transformation |
| rule_logic | VARCHAR(50) | not_empty/regex/title_case |
| rule_value | TEXT | Giá trị (regex pattern) |
| error_message | VARCHAR(200) | Message hiển thị khi lỗi |
| is_active | BOOLEAN | Enable/disable |
| execution_order | INT | Thứ tự thực thi |

**transform_stages**

| id | stage_name | stage_type | description |
|----|------------|------------|-------------|
| 1 | Data Cleansing | validation | Kiểm tra tính hợp lệ |
| 2 | Data Enrichment | transformation | Chuẩn hóa dữ liệu |

**rule_stage_mapping**

| rule_id | stage_id | 
|---------|----------|
| 1 (R1) | 1 (Stage 1) |
| 2 (R2) | 1 |
| 5 (R5) | 2 (Stage 2) |

**Ví dụ Validation Rules:**

| Rule Code | Rule Name | Entity | Field | Logic | Stage |
|-----------|-----------|--------|-------|-------|-------|
| R1 | Employee ID Not Empty | employee | employee_id | not_empty | 1 |
| R2 | Full Name Not Empty | employee | full_name | not_empty | 1 |
| R3 | Email Valid Format | employee | email | regex | 1 |
| R4 | Phone Valid Format | employee | phone | regex | 1 |
| R5 | Normalize Full Name | employee | full_name | title_case | 2 |
| R6 | Normalize Email | employee | email | lowercase_trim | 2 |
| R7 | Normalize Phone E.164 | employee | phone | e164_format | 2 |

## 3.3. Thiết kế ràng buộc và validate

### 3.3.1. Constraint 1: Database Constraints

**Primary Key:**
```sql
ALTER TABLE main_employee ADD PRIMARY KEY (id);
```

**Unique Constraint:**
```sql
ALTER TABLE main_employee ADD UNIQUE (employee_id);
```

**Foreign Key:**
```sql
ALTER TABLE rule_stage_mapping 
ADD FOREIGN KEY (rule_id) REFERENCES validation_rules(id);
```

**Check Constraint:**
```sql
ALTER TABLE staging_order_detail 
ADD CHECK (quantity > 0);
```

### 3.3.2. Biểu thức chính quy (Regex Patterns)

**Email Validation:**
```
^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
```
- Match: `user@example.com`, `admin@company.vn`
- Not match: `invalid@`, `@domain.com`

**Phone Validation (Vietnam):**
```
^(\+84|84|0)[0-9]{9,10}$
```
- Match: `+84901234567`, `0901234567`, `84901234567`
- Not match: `0123` (quá ngắn), `abc123` (có chữ)

**Employee ID:**
```
^NV[0-9]{3,6}$
```
- Match: `NV001`, `NV123456`
- Not match: `NV12` (quá ngắn), `EMP001` (sai prefix)

### 3.3.3. Rule 1: Validation Rules (Stage 1)

**Mục đích:** Kiểm tra tính hợp lệ của dữ liệu, phát hiện lỗi.

**R1: Employee ID Not Empty**
- Field: `employee_id`
- Logic: `not_empty`
- Error: "Mã nhân viên không được rỗng"

**R2: Full Name Not Empty**
- Field: `full_name`
- Logic: `not_empty`
- Error: "Họ tên không được rỗng"

**R3: Email Valid Format**
- Field: `email`
- Logic: `regex`
- Pattern: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- Error: "Email không đúng định dạng"

**R4: Phone Valid Format**
- Field: `phone`
- Logic: `regex`
- Pattern: `^(\+84|84|0)[0-9]{9,10}$`
- Error: "Số điện thoại không hợp lệ"

**Validation Flow:**
```
Input Record
    ↓
RecordValidator
    ↓
Apply R1, R2, R3, R4 theo thứ tự
    ↓
All Pass? → validation_errors = NULL
    ↓
Any Fail? → validation_errors = JSON([...])
    ↓
Insert to Staging Table
```

### 3.3.4. Transform Rules (Stage 2)

**Mục đích:** Chuẩn hóa dữ liệu, không raise error.

**R5: Normalize Full Name**
- Field: `full_name`
- Logic: `title_case`
- Transform: `NGUYEN VAN A` → `Nguyễn Văn A`

**R6: Normalize Email**
- Field: `email`
- Logic: `lowercase_trim`
- Transform: `  ADMIN@MAIL.COM  ` → `admin@mail.com`

**R7: Normalize Phone E.164**
- Field: `phone`
- Logic: `e164_format`
- Transform: `0901234567` → `+84901234567`

**R14: Normalize Product ID**
- Field: `product_id`
- Logic: `uppercase_trim`
- Transform: `prod001` → `PROD001`

**R15: Round Price**
- Field: `price`
- Logic: `round_2_decimals`
- Transform: `15000000.456` → `15000000.46`

## 3.4. Thiết kế hệ thống ETL

### 3.4.1. Extract Data

**Data Source 1: employee.csv**
```
employee_id,full_name,email,phone
NV001,NGUYEN VAN A,ADMIN@MAIL.COM,0901234567
NV002,Tran Thi B,invalid@,0123
```

**Data Source 2: order_detail.csv**
```
order_id,product_id,quantity,price
ORD001,prod001,2,15000000.50
ORD002,prod002,-1,0
```

**Extract Process:**
1. CSVProducer đọc file CSV
2. Parse CSV → Java Objects (Employee, OrderDetail)
3. Serialize thành JSON
4. Publish lên RabbitMQ

**Producer (CSVProducer):**
```
readCSV(file) 
    → Parse 
    → for each record:
        serialize to JSON
        publish to RabbitMQ queue
```

### 3.4.2. Validate via RabbitMQ

**RabbitMQ Queue:**
- `employee-queue`: Durable, persistent
- `order-queue`: Durable, persistent

**Message Format:**
```json
{
  "employeeId": "NV001",
  "fullName": "NGUYEN VAN A",
  "email": "ADMIN@MAIL.COM",
  "phone": "0901234567"
}
```

**Consumer (EmployeeConsumer, OrderConsumer):**
```
Subscribe queue
    ↓
Receive message
    ↓
Deserialize JSON → Java Object
    ↓
Validate với RecordValidator
    ↓
All Pass? → Insert staging (errors = NULL)
Any Fail? → Insert staging (errors = JSON)
    ↓
ACK message (manual)
```

**Validation tại Consumer:**
- Dùng Strategy Pattern
- RecordValidator chứa list ValidationRules
- Apply từng rule theo thứ tự
- Collect RuleResults
- Build JSON errors nếu có lỗi

### 3.4.3. Transform (Two-Stage)

**Stage 1: Data Cleansing (Validation)**

**Input:** Records từ staging có `validation_errors = NULL`

**Process:**
1. Load validation rules từ database (Stage 1)
2. Query staging records: `WHERE validation_errors IS NULL`
3. For each record:
   - Apply validation rules theo `execution_order`
   - Nếu fail: Update `validation_errors` = JSON
4. Commit transaction

**Stage 2: Data Enrichment (Transformation)**

**Input:** Records từ staging có `validation_errors = NULL` (sau Stage 1)

**Process:**
1. Load transformation rules từ database (Stage 2)
2. Query valid records
3. For each record:
   - Store `original_data` (JSON backup)
   - Apply transformation rules:
     - R5: Normalize name
     - R6: Normalize email
     - R7: Normalize phone
   - Log changes to `audit_trail`:
     - field_name
     - old_value
     - new_value
     - transform_rule
   - INSERT INTO main tables
   - DELETE FROM staging
4. Update metrics

**Transform Flow:**
```
┌─────────────────────────────────────┐
│  STAGE 1: DATA CLEANSING            │
├─────────────────────────────────────┤
│  Input: staging (errors = NULL)     │
│  Process:                           │
│    - Load rules (Stage 1)           │
│    - Re-validate                    │
│    - Mark invalid records           │
│  Output: Updated staging            │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  STAGE 2: DATA ENRICHMENT           │
├─────────────────────────────────────┤
│  Input: staging (errors = NULL)     │
│  Process:                           │
│    - Load rules (Stage 2)           │
│    - Apply transformations          │
│    - Log audit trail                │
│    - Insert to main                 │
│    - Delete from staging            │
│  Output: Clean data in main         │
└─────────────────────────────────────┘
```

### 3.4.4. Kiến trúc tổng thể

```
┌────────────────────────────────────────────────────┐
│              ETL PIPELINE                          │
├────────────────────────────────────────────────────┤
│                                                    │
│  CSV Files                                         │
│      ↓                                             │
│  ┌─────────────┐                                  │
│  │  EXTRACT    │                                  │
│  │  (Producer) │                                  │
│  └──────┬──────┘                                  │
│         ↓                                          │
│  ┌─────────────┐                                  │
│  │  RabbitMQ   │                                  │
│  │  Queues     │                                  │
│  └──────┬──────┘                                  │
│         ↓                                          │
│  ┌─────────────┐                                  │
│  │  VALIDATE   │                                  │
│  │  (Consumer) │                                  │
│  └──────┬──────┘                                  │
│         ↓                                          │
│  ┌─────────────┐                                  │
│  │  STAGING DB │                                  │
│  │  (+ errors) │                                  │
│  └──────┬──────┘                                  │
│         ↓                                          │
│  ┌────────────────────────────┐                  │
│  │  TRANSFORM (2-Stage)       │                  │
│  │  ┌──────────────────────┐  │                  │
│  │  │ Stage 1: Validation  │  │                  │
│  │  └──────────────────────┘  │                  │
│  │  ┌──────────────────────┐  │                  │
│  │  │ Stage 2: Transform   │  │                  │
│  │  └──────────────────────┘  │                  │
│  └──────────┬─────────────────┘                  │
│             ↓                                      │
│  ┌─────────────┐                                  │
│  │  MAIN DB    │                                  │
│  │  (Clean)    │                                  │
│  └─────────────┘                                  │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Các thành phần:**
1. **CSV Files**: Nguồn dữ liệu
2. **Producer**: Đọc CSV, publish messages
3. **RabbitMQ**: Message broker (employee-queue, order-queue)
4. **Consumer**: Validate, insert staging
5. **Staging DB**: Dữ liệu tạm (có errors)
6. **Transform**: Two-stage (Validation + Transformation)
7. **Main DB**: Dữ liệu clean

**[Kết thúc Phần 2 - Tiếp tục Phần 3 với Chương 4 + Kết luận]**
