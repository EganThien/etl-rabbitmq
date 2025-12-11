# CHƯƠNG 3: PHÂN TÍCH VÀ THIẾT KẾ (Phần 2)

## 3.3 Thiết kế ràng buộc và validate

### 3.3.1 Constraints (Ràng buộc dữ liệu)

Hệ thống áp dụng nhiều lớp ràng buộc để đảm bảo tính toàn vẹn dữ liệu:

**1. Database Constraints**

Các ràng buộc cấp độ database được định nghĩa trực tiếp trong schema:

```sql
-- Primary Key Constraint
ALTER TABLE main_employee 
ADD CONSTRAINT pk_employee PRIMARY KEY (id);

-- Unique Constraint
ALTER TABLE main_employee 
ADD CONSTRAINT uk_employee_id UNIQUE (employee_id);

-- Foreign Key Constraint
ALTER TABLE rule_stage_mapping
ADD CONSTRAINT fk_rule_id 
FOREIGN KEY (rule_id) REFERENCES validation_rules(id);

-- Check Constraint
ALTER TABLE staging_order_detail
ADD CONSTRAINT chk_quantity CHECK (quantity > 0);
```

**2. Application-level Constraints**

Các ràng buộc được implement trong application code thông qua validation rules:

- **NOT NULL**: Employee ID, Full Name không được rỗng
- **Data Type**: Quantity phải là integer, Price phải là decimal
- **Range**: Quantity > 0, Price > 0
- **Format**: Email, Phone phải đúng format chuẩn

### 3.3.2 Validation Rules

Hệ thống sử dụng **Rules Engine** để quản lý validation rules linh hoạt. Các rules được lưu trong database và có thể enable/disable động.

**Bảng 3.9 - Danh sách Validation Rules**

| Rule Code | Rule Name | Entity | Field | Logic | Stage |
|-----------|-----------|--------|-------|-------|-------|
| R1 | Employee ID Not Empty | Employee | employee_id | not_empty | 1 |
| R2 | Full Name Not Empty | Employee | full_name | not_empty | 1 |
| R3 | Email Valid Format | Employee | email | regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$` | 1 |
| R4 | Phone Valid Format | Employee | phone | regex: `^(\\+84|84|0)[0-9]{9,10}$` | 1 |
| R5 | Normalize Full Name | Employee | full_name | title_case | 2 |
| R6 | Normalize Email | Employee | email | lowercase_trim | 2 |
| R7 | Normalize Phone E.164 | Employee | phone | e164_format | 2 |
| R10 | Order ID Not Empty | Order | order_id | not_empty | 1 |
| R11 | Product ID Not Empty | Order | product_id | not_empty | 1 |
| R12 | Quantity Positive | Order | quantity | positive_integer | 1 |
| R13 | Price Positive | Order | price | positive_number | 1 |
| R14 | Normalize Product ID | Order | product_id | uppercase_trim | 2 |
| R15 | Round Price | Order | price | round_2_decimals | 2 |

**Rule Types:**

1. **Validation Rules** (Stage 1 - Data Cleansing):
   - Kiểm tra tính hợp lệ của dữ liệu
   - Trả về error nếu không pass
   - Ví dụ: R1-R4, R10-R13

2. **Transformation Rules** (Stage 2 - Data Enrichment):
   - Biến đổi/chuẩn hóa dữ liệu
   - Không raise error, chỉ transform
   - Ví dụ: R5-R7, R14-R15

### 3.3.3 Regular Expression Patterns

Regular Expression đóng vai trò quan trọng trong validation. Hệ thống sử dụng các pattern sau:

**Bảng 3.10 - Regular Expression Patterns**

| Pattern | Regex | Mô tả | Ví dụ hợp lệ |
|---------|-------|-------|--------------|
| Email | `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$` | Email chuẩn RFC 5322 | user@example.com |
| Phone (VN) | `^(\\+84|84|0)[0-9]{9,10}$` | SĐT Việt Nam | +84901234567, 0901234567 |
| Employee ID | `^NV[0-9]{3,6}$` | Mã NV: NV + số | NV001, NV123456 |
| Order ID | `^ORD[0-9]{3,8}$` | Mã đơn hàng | ORD001, ORD12345678 |
| Product ID | `^PROD[0-9]{3,6}$` | Mã sản phẩm | PROD001, PROD999 |

**[Hình 3.6 - Validation Rules Flow]**

```
┌─────────────────────────────────────────────────┐
│         VALIDATION FLOW                         │
├─────────────────────────────────────────────────┤
│                                                 │
│  Input Record                                   │
│       ↓                                         │
│  ┌─────────────────────────────────────┐      │
│  │  RecordValidator                    │      │
│  │  ┌───────────────────────────────┐  │      │
│  │  │  For each Validation Rule:   │  │      │
│  │  │  1. Get field value          │  │      │
│  │  │  2. Apply rule logic         │  │      │
│  │  │  3. Collect RuleResult       │  │      │
│  │  └───────────────────────────────┘  │      │
│  └─────────────────────────────────────┘      │
│       ↓                                         │
│  All Rules Pass?                                │
│       ↓                 ↓                       │
│      YES               NO                       │
│       ↓                 ↓                       │
│  validation_errors  validation_errors           │
│  = NULL             = JSON([...])               │
│       ↓                 ↓                       │
│  Insert to Staging Table                        │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 3.3.4 Validation Flow chi tiết

**Consumer Validation (Real-time)**

1. Consumer nhận message từ RabbitMQ
2. Deserialize JSON → Java Object
3. Tạo RecordValidator với các rules:
   ```java
   RecordValidator<Employee> validator = new RecordValidator<>();
   validator.addRule(new NotEmptyRule<>(e -> e.getEmployeeId(), "employeeId"));
   validator.addRule(new EmailRule<>(e -> e.getEmail(), "email"));
   ```
4. Validate record: `List<RuleResult> results = validator.validateAll(emp);`
5. Kiểm tra kết quả:
   - Nếu tất cả pass: Insert với `validation_errors = NULL`
   - Nếu có fail: Build JSON errors và insert

**Transform Validation (Batch - Stage 1)**

1. Load validation rules từ database (Stage 1)
2. Query records từ staging: `WHERE validation_errors IS NULL`
3. For each record:
   - Apply validation rules theo thứ tự `execution_order`
   - Nếu fail: Update `validation_errors` column
4. Commit transaction

**Ví dụ JSON Validation Errors:**

```json
[
  {
    "field": "email",
    "message": "Email không đúng định dạng"
  },
  {
    "field": "phone",
    "message": "Số điện thoại không hợp lệ"
  }
]
```

---

## 3.4 Thiết kế hệ thống ETL

### 3.4.1 Extract (Trích xuất dữ liệu)

**Phương pháp Extract:**

Hệ thống hỗ trợ 2 phương pháp extract:

1. **Batch Processing (Producer)**
   - Đọc file CSV từ `src/main/resources/data/`
   - Parse CSV → Java Objects
   - Publish messages lên RabbitMQ
   - Phù hợp cho: Large batch files, scheduled imports

2. **Direct Upload (Dashboard)**
   - User upload CSV qua web interface
   - Python backend parse và insert trực tiếp vào staging
   - Phù hợp cho: Ad-hoc imports, manual data entry

**Extract Architecture:**

```java
// Producer extract logic
public class CSVProducer {
    public void extractAndPublish(String csvFile) throws Exception {
        List<Employee> employees = readCSV(csvFile);
        
        for (Employee emp : employees) {
            String json = objectMapper.writeValueAsString(emp);
            channel.basicPublish("", QUEUE_NAME, 
                MessageProperties.PERSISTENT_TEXT_PLAIN,
                json.getBytes()
            );
        }
    }
    
    private List<Employee> readCSV(String file) {
        // CSV parsing logic
        try (CSVReader reader = new CSVReader(new FileReader(file))) {
            // Skip header
            reader.readNext();
            
            List<Employee> result = new ArrayList<>();
            String[] line;
            while ((line = reader.readNext()) != null) {
                Employee emp = new Employee();
                emp.setEmployeeId(line[0]);
                emp.setFullName(line[1]);
                emp.setEmail(line[2]);
                emp.setPhone(line[3]);
                result.add(emp);
            }
            return result;
        }
    }
}
```

### 3.4.2 Message Queue (RabbitMQ)

**Vai trò của RabbitMQ:**

1. **Decoupling**: Tách biệt Producer và Consumer
2. **Asynchronous Processing**: Xử lý bất đồng bộ
3. **Load Balancing**: Phân phối messages tới nhiều consumers
4. **Fault Tolerance**: Messages không bị mất khi consumer die
5. **Scalability**: Dễ dàng scale horizontal

**Queue Configuration:**

```java
// Declare durable queues
channel.queueDeclare(
    "employee-queue",  // Queue name
    true,              // Durable (survive broker restart)
    false,             // Not exclusive
    false,             // Not auto-delete
    null               // No additional arguments
);
```

**Message Format:**

Employee Message:
```json
{
  "employeeId": "NV001",
  "fullName": "Nguyễn Văn A",
  "email": "nguyenvana@example.com",
  "phone": "0901234567"
}
```

Order Message:
```json
{
  "orderId": "ORD001",
  "productId": "PROD001",
  "quantity": 2,
  "price": 15000000.0
}
```

**[Hình 3.7 - Pipeline ETL tổng thể]**

```
┌──────────────────────────────────────────────────────────────┐
│                    ETL PIPELINE                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  CSV Files                                                   │
│     ↓                                                        │
│  ┌──────────────────┐                                       │
│  │    EXTRACT       │                                       │
│  │  • Producer      │                                       │
│  │  • Dashboard     │                                       │
│  └────────┬─────────┘                                       │
│           ↓                                                  │
│  ┌──────────────────┐                                       │
│  │   MESSAGE QUEUE  │                                       │
│  │  • RabbitMQ      │                                       │
│  │  • Persistent    │                                       │
│  │  • Durable       │                                       │
│  └────────┬─────────┘                                       │
│           ↓                                                  │
│  ┌──────────────────┐                                       │
│  │    VALIDATE      │                                       │
│  │  • Consumers     │                                       │
│  │  • Rules Engine  │                                       │
│  │  • Error Detect  │                                       │
│  └────────┬─────────┘                                       │
│           ↓                                                  │
│  ┌──────────────────┐                                       │
│  │ STAGING DATABASE │                                       │
│  │  • With errors   │                                       │
│  │  • JSON errors   │                                       │
│  └────────┬─────────┘                                       │
│           ↓                                                  │
│  ┌──────────────────────────────────┐                      │
│  │      TRANSFORM (2-Stage)         │                      │
│  │  ┌────────────────────────────┐  │                      │
│  │  │ Stage 1: Data Cleansing    │  │                      │
│  │  │ • Re-validate with DB rules│  │                      │
│  │  │ • Mark errors              │  │                      │
│  │  └────────────┬───────────────┘  │                      │
│  │               ↓                   │                      │
│  │  ┌────────────────────────────┐  │                      │
│  │  │ Stage 2: Data Enrichment   │  │                      │
│  │  │ • Apply transformations    │  │                      │
│  │  │ • Normalize data           │  │                      │
│  │  │ • Log audit trail          │  │                      │
│  │  └────────────┬───────────────┘  │                      │
│  └───────────────┼──────────────────┘                      │
│                  ↓                                           │
│  ┌──────────────────┐                                       │
│  │      LOAD        │                                       │
│  │  • Main Tables   │                                       │
│  │  • Clean Data    │                                       │
│  │  • Normalized    │                                       │
│  └──────────────────┘                                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 3.4.3 Validate (Kiểm tra dữ liệu)

Validate được thực hiện ở 2 điểm:

**1. Consumer-level Validation (Real-time)**

```java
public class EmployeeConsumer {
    private RecordValidator<Employee> validator;
    
    public void processMessage(Employee emp) {
        // Validate record
        List<RuleResult> results = validator.validateAll(emp);
        boolean allPass = results.stream().allMatch(RuleResult::isOk);
        
        if (allPass) {
            // Insert valid record
            insertToStaging(emp, null);
        } else {
            // Build errors JSON
            String errors = buildErrorsJSON(results);
            insertToStaging(emp, errors);
        }
    }
}
```

**2. Transform-level Validation (Batch - Stage 1)**

```python
# Dashboard Transform API
def run_transform_stage_1():
    # Load rules from database
    rules = get_active_rules_by_stage(1, 'employee')
    
    # Query staging records
    records = query_staging_valid_records()
    
    for record in records:
        errors = []
        for rule in rules:
            error = apply_validation_rule(rule, record)
            if error:
                errors.append(error)
        
        if errors:
            update_staging_errors(record.id, json.dumps(errors))
```

### 3.4.4 Transform (Chuyển đổi dữ liệu)

**Two-Stage Transform Architecture:**

**[Hình 3.8 - Two-Stage Transform Process]**

```
┌───────────────────────────────────────────────────────┐
│         TWO-STAGE TRANSFORM                           │
├───────────────────────────────────────────────────────┤
│                                                       │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  STAGE 1: DATA CLEANSING (Validation)        ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                       │
│  Input: staging_employee (validation_errors = NULL)   │
│                                                       │
│  Process:                                             │
│  1. Load validation rules (Stage 1) from DB          │
│  2. For each record:                                 │
│     • Apply rules in execution_order                 │
│     • Collect validation errors                      │
│  3. Mark invalid records:                            │
│     • UPDATE validation_errors = JSON([...])         │
│                                                       │
│  Output: Records with errors marked                   │
│                                                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                       │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  STAGE 2: DATA ENRICHMENT (Transformation)   ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                       │
│  Input: staging_employee (validation_errors = NULL)   │
│        (Only valid records from Stage 1)             │
│                                                       │
│  Process:                                             │
│  1. Load transformation rules (Stage 2) from DB      │
│  2. For each valid record:                           │
│     • Store original_data                            │
│     • Apply transformation rules:                    │
│       - Normalize name (title_case)                  │
│       - Normalize email (lowercase_trim)             │
│       - Normalize phone (E.164 format)               │
│     • Log changes to audit trail                     │
│  3. INSERT INTO main_employee (transformed_data)     │
│  4. DELETE FROM staging_employee WHERE id = ?        │
│                                                       │
│  Output: Clean, normalized data in main tables       │
│                                                       │
└───────────────────────────────────────────────────────┘
```

**Transformation Logic:**

```python
# Bảng 3.11 - Transformation Logic Mapping
transformation_logic = {
    'title_case': lambda x: normalize_name(x),
    # "NGUYEN VAN A" → "Nguyễn Văn A"
    
    'lowercase_trim': lambda x: x.strip().lower(),
    # "  ADMIN@MAIL.COM  " → "admin@mail.com"
    
    'e164_format': lambda x: normalize_phone(x),
    # "0901234567" → "+84901234567"
    
    'uppercase_trim': lambda x: x.strip().upper(),
    # "prod001" → "PROD001"
    
    'round_2_decimals': lambda x: round(float(x), 2)
    # 15000000.456 → 15000000.46
}
```

### 3.4.5 Load (Tải dữ liệu)

**Load Process:**

1. **Prepare Data**
   - Transformed data đã được normalize
   - Original data được backup trong JSON column

2. **Insert to Main Tables**
   ```java
   String sql = "INSERT INTO main_employee " +
                "(employee_id, full_name, email, phone, " +
                "batch_id, original_data) " +
                "VALUES (?, ?, ?, ?, ?, ?) " +
                "ON DUPLICATE KEY UPDATE " +
                "full_name = VALUES(full_name), " +
                "email = VALUES(email)";
   ```

3. **Log Audit Trail**
   ```java
   for (FieldChange change : changes) {
       insertAuditLog(batch_id, entity_id, 
           change.field, change.oldValue, 
           change.newValue, change.rule);
   }
   ```

4. **Cleanup Staging**
   ```java
   String deleteSql = "DELETE FROM staging_employee " +
                      "WHERE id = ? AND validation_errors IS NULL";
   ```

5. **Update Metrics**
   ```java
   updateDailyMetrics(entity_type, 
       totalRecords, validRecords, errorRecords);
   ```

**Data Quality Assurance:**

- **Idempotency**: Rerun transform không tạo duplicate
- **Traceability**: Mọi thay đổi được log
- **Rollback**: Có thể restore từ original_data
- **Monitoring**: Metrics theo dõi data quality

---

**Tóm tắt Chương 3 (Phần 2):**

Phần 2 của Chương 3 đã trình bày chi tiết:
- Thiết kế ràng buộc và validation với Rules Engine
- Regular Expression patterns cho validation
- Kiến trúc ETL pipeline hoàn chỉnh (Extract-Queue-Validate-Transform-Load)
- Two-Stage Transform process với Data Cleansing và Data Enrichment
- Load process với audit trail và data quality assurance

Chương tiếp theo sẽ trình bày phần triển khai hiện thực với code cụ thể và giao diện hệ thống.
