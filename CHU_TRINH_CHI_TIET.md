# 🔄 CHU TRÌNH CHI TIẾT HỆ THỐNG ETL - RABBITMQ

> **Hệ thống ETL phân tán với RabbitMQ Message Queue, Two-Stage Data Validation & Transformation**

---

## 📋 MỤC LỤC

1. [Tổng Quan Kiến Trúc](#1-tổng-quan-kiến-trúc)
2. [Các Thành Phần Chính](#2-các-thành-phần-chính)
3. [Luồng Dữ Liệu Chi Tiết](#3-luồng-dữ-liệu-chi-tiết)
4. [Stage 1: Extract & Publish](#4-stage-1-extract--publish)
5. [Stage 2: Consume & Validate](#5-stage-2-consume--validate)
6. [Stage 3: Two-Stage Transform](#6-stage-3-two-stage-transform)
7. [Dashboard & Monitoring](#7-dashboard--monitoring)
8. [Quy Trình Xử Lý Lỗi](#8-quy-trình-xử-lý-lỗi)
9. [Cấu Trúc Database](#9-cấu-trúc-database)
10. [Flow Chart Tổng Thể](#10-flow-chart-tổng-thể)

---

## 1. 🏗️ TỔNG QUAN KIẾN TRÚC

### Kiến Trúc Tổng Thể

```
┌─────────────────────────────────────────────────────────────────────┐
│                        🌐 ETL ECOSYSTEM                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐             │
│  │   CSV    │───▶│   Producer   │───▶│  RabbitMQ    │             │
│  │  Files   │    │   (Java)     │    │  Queues      │             │
│  └──────────┘    └──────────────┘    └──────┬───────┘             │
│                                               │                      │
│                                               ▼                      │
│                         ┌─────────────────────────────┐             │
│                         │      Consumers (Java)        │             │
│                         │  ┌──────────┬──────────┐   │             │
│                         │  │ Employee │  Order   │   │             │
│                         │  │ Consumer │ Consumer │   │             │
│                         │  └────┬─────┴─────┬────┘   │             │
│                         └───────┼───────────┼─────────┘             │
│                                 │           │                        │
│                                 ▼           ▼                        │
│                         ┌─────────────────────────────┐             │
│                         │   MySQL - Staging Tables    │             │
│                         │  • staging_employee          │             │
│                         │  • staging_order_detail      │             │
│                         │  • validation_errors (JSON)  │             │
│                         └────────────┬─────────────────┘             │
│                                      │                               │
│                                      ▼                               │
│                         ┌─────────────────────────────┐             │
│                         │   Transform Engine (2-Stage)│             │
│                         │  Stage 1: Data Cleansing    │             │
│                         │  Stage 2: Data Enrichment   │             │
│                         └────────────┬─────────────────┘             │
│                                      │                               │
│                                      ▼                               │
│                         ┌─────────────────────────────┐             │
│                         │    MySQL - Main Tables      │             │
│                         │  • main_employee            │             │
│                         │  • main_order_detail        │             │
│                         │  • audit_trail              │             │
│                         └─────────────────────────────┘             │
│                                      ▲                               │
│                                      │                               │
│                         ┌────────────┴─────────────┐                │
│                         │  Flask Dashboard (Python)│                │
│                         │  • Upload CSV            │                │
│                         │  • Monitor Status        │                │
│                         │  • View Errors           │                │
│                         │  • Trigger Transform     │                │
│                         │  • Export Data           │                │
│                         └──────────────────────────┘                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Công Nghệ Sử Dụng

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Producer** | Java 11+ | Đọc CSV và publish messages |
| **Message Broker** | RabbitMQ 3.x | Message queue phân tán |
| **Consumers** | Java 11+ | Consume messages và validate |
| **Database** | MySQL 8.0 | Lưu trữ staging & main data |
| **Transform** | Java 11+ | Two-stage data transformation |
| **Dashboard** | Flask (Python) | Web UI monitoring & control |
| **Orchestration** | Docker Compose | Container management |

---

## 2. 🧩 CÁC THÀNH PHẦN CHÍNH

### 2.1 Producer (Java)
**File**: `src/main/java/com/example/etl/producer/CSVProducer.java`

**Nhiệm vụ**:
- Đọc file CSV từ `src/main/resources/data/`
- Parse CSV thành Java Objects
- Serialize thành JSON
- Publish lên RabbitMQ queues

**Input**: 
- `employee.csv` → queue `employee-queue`
- `order_detail.csv` → queue `order-queue`

**Output**: JSON messages trong RabbitMQ

```java
// Ví dụ message Employee
{
  "employeeId": "NV001",
  "fullName": "Nguyễn Văn A",
  "email": "nguyenvana@example.com",
  "phone": "+84901234567"
}
```

### 2.2 RabbitMQ Message Broker

**Queues**:
- `employee-queue`: Chứa messages nhân viên
- `order-queue`: Chứa messages đơn hàng

**Features**:
- Persistent messages (survive broker restart)
- Durable queues
- Manual acknowledgment
- Message retry mechanism

**Management UI**: http://localhost:15672

### 2.3 Consumers (Java)

#### Employee Consumer
**File**: `src/main/java/com/example/etl/consumer/EmployeeConsumer.java`

**Workflow**:
1. Subscribe to `employee-queue`
2. Receive message
3. Deserialize JSON → Employee object
4. **Validate** using Rules Engine:
   - R1: Employee ID not empty
   - R2: Full Name not empty
   - R3: Email valid format (regex)
   - R4: Phone valid format (regex)
5. **Insert to staging_employee**:
   - ✅ Valid: Insert với `validation_errors = NULL`
   - ❌ Invalid: Insert với `validation_errors = JSON array`
6. **ACK** message to RabbitMQ

#### Order Consumer
**File**: `src/main/java/com/example/etl/consumer/OrderConsumer.java`

**Workflow**: Tương tự Employee Consumer
- Validate: Order ID, Product ID, Quantity > 0, Price > 0
- Insert to `staging_order_detail`

### 2.4 Validation Rules Engine

**File**: `src/main/java/com/example/etl/rules/`

**Kiến trúc**:
```java
RecordValidator<T>
  ├── ValidationRule<T> (interface)
  │   ├── NotEmptyRule
  │   ├── EmailRule (regex)
  │   ├── PhoneNumberRule (regex)
  │   └── QuantityRule (> 0)
  └── RuleResult (ok/failed + message)
```

**Example Rule**:
```java
validator.addRule(new EmailRule<>(
    e -> e.getEmail(), 
    "email"
));
```

### 2.5 Transform Engine (Two-Stage)

**File**: `src/main/java/com/example/etl/transform/TransformLoad.java`

**Database-Driven Rules**:
```sql
SELECT * FROM validation_rules WHERE is_enabled = TRUE
SELECT * FROM transform_stages WHERE is_enabled = TRUE
SELECT * FROM rule_stage_mapping ORDER BY execution_order
```

**Stage 1: Data Cleansing** (Validation)
- Apply validation rules từ database
- Mark records với errors
- Update `validation_errors` column

**Stage 2: Data Enrichment** (Transformation)
- Apply transformation rules
- Normalize data:
  - `title_case`: Nguyễn Văn A
  - `lowercase_trim`: email@example.com
  - `e164_format`: +84901234567
- Log transformations to audit trail
- Insert to main tables
- Delete from staging

### 2.6 Flask Dashboard

**File**: `dashboard/app.py`

**Features**:

1. **Upload CSV** (`/upload`)
   - Drag & drop interface
   - Auto-detect file type
   - Direct insert to staging

2. **Main Dashboard** (`/`)
   - View valid data (main tables)
   - View error data (staging with validation_errors)
   - Real-time counts

3. **Transform Control**
   - Manual trigger transform
   - View progress
   - See results

4. **History & Audit** (`/history`)
   - Transform history
   - Audit trail (field-level changes)
   - Data quality metrics

5. **Rules Management** (`/rules`)
   - Enable/disable rules
   - View rule configuration
   - Edit rule parameters

6. **Export** (`/export/employee`, `/export/order`)
   - Export normalized data to CSV

---

## 3. 🌊 LUỒNG DỮ LIỆU CHI TIẾT

### 3.1 Luồng Chính (Happy Path)

```
┌─────────────┐
│  CSV File   │
│  employee.  │
│    csv      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 1: EXTRACT & PUBLISH                               │
│                                                          │
│  CSVProducer.java                                        │
│  • Đọc CSV line by line                                 │
│  • Parse → Employee object                              │
│  • Validate format cơ bản                               │
│  • Serialize → JSON                                     │
│  • Publish to RabbitMQ                                  │
│                                                          │
│  connection.createChannel()                             │
│  channel.basicPublish("employee-queue", json)           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────┐
          │   RabbitMQ       │
          │ employee-queue   │
          │ [▓▓▓▓▓▓▓▓]      │  ← Messages queued
          └────────┬─────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 2: CONSUME & VALIDATE                              │
│                                                          │
│  EmployeeConsumer.java                                   │
│  • Subscribe to queue                                    │
│  • Receive message                                       │
│  • Deserialize JSON → Employee                          │
│  • Run validation rules:                                │
│    ┌─────────────────────────────────┐                 │
│    │ RecordValidator.validateAll()   │                 │
│    │  R1: employeeId not empty       │                 │
│    │  R2: fullName not empty         │                 │
│    │  R3: email matches regex        │                 │
│    │  R4: phone matches regex        │                 │
│    └─────────────────────────────────┘                 │
│                                                          │
│  • Prepare SQL insert:                                  │
│    IF all rules pass:                                   │
│      validation_errors = NULL                           │
│    ELSE:                                                │
│      validation_errors = JSON([                         │
│        {field: "email", message: "Invalid format"}      │
│      ])                                                 │
│                                                          │
│  • Execute INSERT INTO staging_employee                 │
│  • ACK message to RabbitMQ                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  MySQL Database      │
          │  staging_employee    │
          │ ┌──────────────────┐ │
          │ │ id  emp_id  name │ │
          │ │ 1   NV001   ...  │ │  ✅ validation_errors: NULL
          │ │ 2   NV002   ...  │ │  ❌ validation_errors: [{"field":...}]
          │ └──────────────────┘ │
          └──────────┬───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ STEP 3: TWO-STAGE TRANSFORM                             │
│                                                          │
│  TransformLoad.java / Dashboard API                      │
│                                                          │
│  ╔══════════════════════════════════════════════════╗   │
│  ║  STAGE 1: DATA CLEANSING (Validation)           ║   │
│  ╚══════════════════════════════════════════════════╝   │
│                                                          │
│  • Load rules: get_active_rules_by_stage(1, 'employee') │
│  • Query staging: WHERE validation_errors IS NULL       │
│  • For each record:                                     │
│    - Apply validation rules from DB                     │
│    - IF errors found:                                   │
│        UPDATE staging_employee                          │
│        SET validation_errors = JSON(errors)             │
│        Continue to next record                          │
│                                                          │
│  ╔══════════════════════════════════════════════════╗   │
│  ║  STAGE 2: DATA ENRICHMENT (Transformation)      ║   │
│  ╚══════════════════════════════════════════════════╝   │
│                                                          │
│  • Load rules: get_active_rules_by_stage(2, 'employee') │
│  • Query staging: WHERE validation_errors IS NULL       │
│  • For each valid record:                               │
│    - Store original_data                                │
│    - Apply transformation rules:                        │
│      ┌─────────────────────────────────┐               │
│      │ R5: Normalize Full Name         │               │
│      │    "NGUYEN VAN A"                │               │
│      │    → "Nguyễn Văn A"             │               │
│      │                                  │               │
│      │ R6: Normalize Email              │               │
│      │    "  ADMIN@MAIL.COM  "         │               │
│      │    → "admin@mail.com"           │               │
│      │                                  │               │
│      │ R7: Normalize Phone (E.164)     │               │
│      │    "0901234567"                  │               │
│      │    → "+84901234567"             │               │
│      └─────────────────────────────────┘               │
│                                                          │
│    - Log transformations to audit trail                 │
│    - INSERT INTO main_employee (transformed_data)       │
│    - DELETE FROM staging_employee WHERE id = ...        │
│                                                          │
│  • Commit transaction                                   │
│  • Update metrics                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  MySQL Database      │
          │  main_employee       │
          │ ┌──────────────────┐ │
          │ │ Normalized Data  │ │  ← Clean, enriched data
          │ └──────────────────┘ │
          │                      │
          │  data_transformation_│
          │  audit               │
          │ ┌──────────────────┐ │
          │ │ Field Changes    │ │  ← Audit trail
          │ └──────────────────┘ │
          └──────────────────────┘
```

### 3.2 Luồng Xử Lý Lỗi (Error Path)

```
┌─────────────┐
│ Invalid CSV │
│   Record    │
└──────┬──────┘
       │
       ▼
┌────────────────────────┐
│  Consumer Validation   │
│  Rules Failed          │
└──────┬─────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│ INSERT staging_employee                 │
│ SET validation_errors = JSON([          │
│   {                                     │
│     "field": "email",                   │
│     "message": "Email không hợp lệ"     │
│   },                                    │
│   {                                     │
│     "field": "phone",                   │
│     "message": "SĐT không đúng format"  │
│   }                                     │
│ ])                                      │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Dashboard Error View    │
│ • Show validation errors│
│ • Allow manual edit     │
│ • Re-validate after fix │
└─────────────────────────┘
```

---

## 4. 📤 STAGE 1: EXTRACT & PUBLISH

### 4.1 CSV File Format

**Employee CSV** (`employee.csv`):
```csv
EmployeeID,FullName,Email,Phone
NV001,Nguyễn Văn A,nguyenvana@example.com,0901234567
NV002,Trần Thị B,tranthib@example.com,+84912345678
NV003,Lê Văn C,invalid-email,0123  ← Invalid
```

**Order Detail CSV** (`order_detail.csv`):
```csv
OrderID,ProductID,ProductName,Quantity,Price
ORD001,PROD001,Laptop Dell,2,15000000
ORD002,PROD002,Mouse Logitech,-1,250000  ← Invalid quantity
```

### 4.2 Producer Implementation

```java
// CSVProducer.java - Simplified flow
public class CSVProducer {
    public static void main(String[] args) {
        // 1. Connect to RabbitMQ
        Connection conn = RabbitUtil.getConnection();
        Channel channel = conn.createChannel();
        
        // 2. Declare queues
        channel.queueDeclare("employee-queue", 
            true,  // durable
            false, // not exclusive
            false, // not auto-delete
            null);
        
        // 3. Read CSV
        List<Employee> employees = readEmployeeCSV();
        
        // 4. Publish messages
        for (Employee emp : employees) {
            String json = new ObjectMapper()
                .writeValueAsString(emp);
            
            channel.basicPublish(
                "",  // default exchange
                "employee-queue",
                MessageProperties.PERSISTENT_TEXT_PLAIN,
                json.getBytes()
            );
            
            System.out.println("Published: " + emp.getEmployeeId());
        }
        
        // 5. Close connections
        channel.close();
        conn.close();
    }
}
```

### 4.3 Message Format

**Employee Message**:
```json
{
  "employeeId": "NV001",
  "fullName": "Nguyễn Văn A",
  "email": "nguyenvana@example.com",
  "phone": "0901234567"
}
```

**Order Message**:
```json
{
  "orderId": "ORD001",
  "productId": "PROD001",
  "quantity": 2,
  "price": 15000000.0
}
```

---

## 5. 🔽 STAGE 2: CONSUME & VALIDATE

### 5.1 Consumer Architecture

```
┌─────────────────────────────────────────────┐
│         EmployeeConsumer.java               │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────┐      │
│  │  1. Subscribe to Queue           │      │
│  │     channel.basicConsume(...)    │      │
│  └────────────┬─────────────────────┘      │
│               │                             │
│               ▼                             │
│  ┌──────────────────────────────────┐      │
│  │  2. Receive Message              │      │
│  │     DeliverCallback triggered    │      │
│  └────────────┬─────────────────────┘      │
│               │                             │
│               ▼                             │
│  ┌──────────────────────────────────┐      │
│  │  3. Deserialize JSON             │      │
│  │     ObjectMapper.readValue()     │      │
│  └────────────┬─────────────────────┘      │
│               │                             │
│               ▼                             │
│  ┌──────────────────────────────────┐      │
│  │  4. Validate Record              │      │
│  │  ┌────────────────────────────┐  │      │
│  │  │ RecordValidator<Employee>  │  │      │
│  │  │ • NotEmptyRule(empId)      │  │      │
│  │  │ • NotEmptyRule(fullName)   │  │      │
│  │  │ • EmailRule(email)         │  │      │
│  │  │ • PhoneNumberRule(phone)   │  │      │
│  │  └────────────┬───────────────┘  │      │
│  └───────────────┼──────────────────┘      │
│                  │                          │
│                  ▼                          │
│  ┌──────────────────────────────────┐      │
│  │  5. Insert to Staging DB         │      │
│  │     • validation_errors = NULL   │      │
│  │       (if all rules pass)        │      │
│  │     • validation_errors = JSON   │      │
│  │       (if any rule fails)        │      │
│  └────────────┬─────────────────────┘      │
│               │                             │
│               ▼                             │
│  ┌──────────────────────────────────┐      │
│  │  6. ACK Message                  │      │
│  │     channel.basicAck(tag, false) │      │
│  └──────────────────────────────────┘      │
│                                             │
└─────────────────────────────────────────────┘
```

### 5.2 Validation Rules Detail

**Rule Engine Implementation**:

```java
// Setup validator
RecordValidator<Employee> validator = new RecordValidator<>();

// R1: Employee ID not empty
validator.addRule(new NotEmptyRule<>(
    e -> e.getEmployeeId(),
    "employeeId"
));

// R2: Full Name not empty  
validator.addRule(new NotEmptyRule<>(
    e -> e.getFullName(),
    "fullName"
));

// R3: Email format
validator.addRule(new EmailRule<>(
    e -> e.getEmail(),
    "email"
));

// R4: Phone format
validator.addRule(new PhoneNumberRule<>(
    e -> e.getPhone(),
    "phone"
));

// Execute validation
List<RuleResult> results = validator.validateAll(employee);
```

**Rule Results**:
```java
// All pass
[
  RuleResult{ok=true, field="employeeId"},
  RuleResult{ok=true, field="fullName"},
  RuleResult{ok=true, field="email"},
  RuleResult{ok=true, field="phone"}
]

// Some fail
[
  RuleResult{ok=true, field="employeeId"},
  RuleResult{ok=true, field="fullName"},
  RuleResult{ok=false, field="email", 
             message="Email không đúng định dạng"},
  RuleResult{ok=false, field="phone", 
             message="Số điện thoại không hợp lệ"}
]
```

### 5.3 Database Insert Logic

```java
if (allRulesPass) {
    // Insert valid record
    String sql = "INSERT INTO staging_employee " +
                 "(employee_id, full_name, email, phone) " +
                 "VALUES (?, ?, ?, ?)";
    ps.setString(1, emp.getEmployeeId());
    ps.setString(2, emp.getFullName());
    ps.setString(3, emp.getEmail());
    ps.setString(4, emp.getPhone());
    ps.executeUpdate();
} else {
    // Insert invalid record with errors
    String sql = "INSERT INTO staging_employee " +
                 "(employee_id, full_name, email, phone, " +
                 "validation_errors) " +
                 "VALUES (?, ?, ?, ?, ?)";
    ps.setString(1, emp.getEmployeeId());
    ps.setString(2, emp.getFullName());
    ps.setString(3, emp.getEmail());
    ps.setString(4, emp.getPhone());
    
    // Build JSON errors
    List<Map<String, String>> errors = new ArrayList<>();
    for (RuleResult r : results) {
        if (!r.isOk()) {
            Map<String, String> err = new HashMap<>();
            err.put("field", r.getField());
            err.put("message", r.getMessage());
            errors.add(err);
        }
    }
    String errorsJson = new ObjectMapper()
        .writeValueAsString(errors);
    ps.setString(5, errorsJson);
    ps.executeUpdate();
}
```

---

## 6. 🔄 STAGE 3: TWO-STAGE TRANSFORM

### 6.1 Transform Architecture

```
┌──────────────────────────────────────────────────────────┐
│              TWO-STAGE TRANSFORM ENGINE                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ╔════════════════════════════════════════════════════╗ │
│  ║           STAGE 1: DATA CLEANSING                  ║ │
│  ║           (Database-Driven Validation)             ║ │
│  ╚════════════════════════════════════════════════════╝ │
│                                                          │
│  1. Load Rules from Database                            │
│     SELECT * FROM validation_rules r                    │
│     JOIN rule_stage_mapping rsm ON r.id = rsm.rule_id   │
│     JOIN transform_stages s ON rsm.stage_id = s.id      │
│     WHERE s.stage_number = 1                            │
│       AND r.is_enabled = TRUE                           │
│     ORDER BY rsm.execution_order                        │
│                                                          │
│  2. Query Staging Records                               │
│     SELECT * FROM staging_employee                      │
│     WHERE validation_errors IS NULL                     │
│                                                          │
│  3. Apply Validation Rules                              │
│     For each record:                                    │
│       For each rule in order:                           │
│         - Apply validation logic                        │
│         - Collect errors                                │
│                                                          │
│  4. Mark Invalid Records                                │
│     IF errors found:                                    │
│       UPDATE staging_employee                           │
│       SET validation_errors = JSON(errors)              │
│       WHERE id = ?                                      │
│                                                          │
│  ────────────────────────────────────────────────────  │
│                                                          │
│  ╔════════════════════════════════════════════════════╗ │
│  ║         STAGE 2: DATA ENRICHMENT                   ║ │
│  ║         (Transformation & Normalization)           ║ │
│  ╚════════════════════════════════════════════════════╝ │
│                                                          │
│  1. Load Transform Rules                                │
│     SELECT * FROM validation_rules r                    │
│     WHERE s.stage_number = 2                            │
│       AND r.rule_type = 'transformation'                │
│                                                          │
│  2. Query Valid Records                                 │
│     SELECT * FROM staging_employee                      │
│     WHERE validation_errors IS NULL                     │
│                                                          │
│  3. Apply Transformations                               │
│     For each record:                                    │
│       original_data = record                            │
│       transformed_data = record                         │
│                                                          │
│       For each transform rule:                          │
│         field_value = get_field(record, rule.field)     │
│         new_value = apply_transform(field_value, rule)  │
│         transformed_data[field] = new_value             │
│                                                          │
│         IF new_value != original_value:                 │
│           log_field_transformation(...)                 │
│                                                          │
│  4. Load to Main Tables                                 │
│     INSERT INTO main_employee                           │
│       (employee_id, full_name, email, phone,            │
│        batch_id, original_data)                         │
│     VALUES (transformed_data, JSON(original_data))      │
│                                                          │
│  5. Cleanup Staging                                     │
│     DELETE FROM staging_employee                        │
│     WHERE id = ? AND validation_errors IS NULL          │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 6.2 Transformation Rules

**Database Configuration** (`validation_rules` table):

| rule_code | rule_name | rule_type | field_name | validation_logic | execution_order |
|-----------|-----------|-----------|------------|------------------|-----------------|
| R5 | Normalize Full Name | transformation | full_name | title_case | 10 |
| R6 | Normalize Email | transformation | email | lowercase_trim | 11 |
| R7 | Normalize Phone E.164 | transformation | phone | e164_format | 12 |
| R14 | Normalize Product ID | transformation | product_id | uppercase_trim | 10 |
| R15 | Round Price | transformation | price | round_2_decimals | 11 |

**Transformation Logic**:

```python
def apply_transformation_rule(rule, field_value):
    logic = rule['validation_logic']
    
    if logic == 'title_case':
        # "NGUYEN VAN A" → "Nguyễn Văn A"
        return normalize_name(field_value)
    
    elif logic == 'lowercase_trim':
        # "  ADMIN@MAIL.COM  " → "admin@mail.com"
        return str(field_value).strip().lower()
    
    elif logic == 'e164_format':
        # "0901234567" → "+84901234567"
        # "84901234567" → "+84901234567"
        # "+84901234567" → "+84901234567" (no change)
        return normalize_phone(field_value)
    
    elif logic == 'uppercase_trim':
        return str(field_value).strip().upper()
    
    elif logic == 'round_2_decimals':
        return round(float(field_value), 2)
    
    return field_value
```

### 6.3 Audit Trail

**Every transformation is logged**:

```sql
INSERT INTO data_transformation_audit
  (batch_id, entity_type, entity_id, field_name, 
   original_value, transformed_value, transform_rule)
VALUES
  ('transform_20251207_120815', 'employee', 'NV001', 
   'phone', '0901234567', '+84901234567', 'R7');
```

**Audit Trail Query**:
```sql
SELECT * FROM data_transformation_audit
WHERE entity_id = 'NV001'
ORDER BY created_at DESC;
```

**Result**:
| field_name | original_value | transformed_value | transform_rule | created_at |
|------------|---------------|-------------------|----------------|------------|
| phone | 0901234567 | +84901234567 | R7 | 2025-12-07 12:08:15 |
| email | Admin@Mail.COM | admin@mail.com | R6 | 2025-12-07 12:08:15 |
| full_name | NGUYEN VAN A | Nguyễn Văn A | R5 | 2025-12-07 12:08:15 |

---

## 7. 📊 DASHBOARD & MONITORING

### 7.1 Dashboard Pages

```
┌─────────────────────────────────────────────┐
│         FLASK DASHBOARD STRUCTURE           │
├─────────────────────────────────────────────┤
│                                             │
│  GET /                                      │
│  ├─ Main Dashboard                          │
│  ├─ View Valid Data (main tables)           │
│  ├─ View Error Data (staging + errors)      │
│  └─ Trigger Transform                       │
│                                             │
│  GET /upload                                │
│  ├─ Upload CSV Files                        │
│  ├─ Drag & Drop Interface                   │
│  ├─ Direct Insert to Staging                │
│  └─ Process ETL Pipeline                    │
│                                             │
│  GET /history                               │
│  ├─ Transform History                       │
│  ├─ Audit Trail (field changes)             │
│  ├─ Data Quality Metrics                    │
│  └─ Processing Logs                         │
│                                             │
│  GET /rules                                 │
│  ├─ View Validation Rules                   │
│  ├─ Enable/Disable Rules                    │
│  └─ Edit Rule Configuration                 │
│                                             │
│  GET /edit-errors/employee                  │
│  ├─ Edit Invalid Records                    │
│  ├─ Fix Validation Errors                   │
│  └─ Re-validate & Re-process                │
│                                             │
└─────────────────────────────────────────────┘
```

### 7.2 API Endpoints

**Data APIs**:
- `GET /api/main/employee?limit=50` - Valid employee data
- `GET /api/main/order?limit=50` - Valid order data
- `GET /api/staging/employee/errors?limit=100` - Error employees
- `GET /api/staging/order/errors?limit=100` - Error orders

**Control APIs**:
- `POST /api/run-transform-v2` - Trigger transform
- `POST /api/upload-csv` - Upload CSV file
- `POST /api/process-etl` - Process uploaded files

**Management APIs**:
- `GET /api/validation-rules` - Get all rules
- `POST /api/toggle-rule/{rule_code}` - Enable/disable rule
- `GET /api/transform-history` - Transform logs
- `GET /api/audit-trail?batch_id=xxx` - Field-level audit

**Export APIs**:
- `GET /export/employee` - Export employees to CSV
- `GET /export/order` - Export orders to CSV

### 7.3 Real-time Monitoring

**Status Cards**:
```
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Staging Data    │  │  Valid Data      │  │  Error Data      │
│  ───────────     │  │  ───────────     │  │  ───────────     │
│  Employees: 25   │  │  Employees: 100  │  │  Employees: 15   │
│  Orders: 30      │  │  Orders: 200     │  │  Orders: 5       │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

**Transform Button**:
```
┌──────────────────────────────────────┐
│  🌀 Chạy Transform                   │
│                                      │
│  Click để chuyển dữ liệu từ staging │
│  sang main database với validation   │
│  & transformation rules              │
└──────────────────────────────────────┘
```

---

## 8. ⚠️ QUY TRÌNH XỬ LÝ LỖI

### 8.1 Error Detection Flow

```
Record → Consumer Validation → Staging (with errors)
                                    ↓
                            Transform Stage 1
                                    ↓
                          Mark validation_errors
                                    ↓
                            Dashboard Display
                                    ↓
                            Manual Edit
                                    ↓
                            Re-validate
                                    ↓
                          Stage 2 Transform
                                    ↓
                            Main Tables
```

### 8.2 Error Data Structure

**Staging Table with Errors**:
```sql
SELECT id, employee_id, full_name, email, phone, validation_errors
FROM staging_employee
WHERE validation_errors IS NOT NULL;
```

**Result**:
| id | employee_id | full_name | email | phone | validation_errors |
|----|-------------|-----------|-------|-------|-------------------|
| 5 | NV005 | Nguyễn A | invalid | 012 | `[{"field":"email","message":"Email không đúng định dạng"},{"field":"phone","message":"Số điện thoại không hợp lệ"}]` |

### 8.3 Error Correction Workflow

**Dashboard Edit Interface**:
```
┌─────────────────────────────────────────────────────┐
│  Edit Employee: NV005                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Employee ID: [NV005               ] (read-only)   │
│                                                     │
│  Full Name:   [Nguyễn Văn A        ]               │
│                                                     │
│  Email:       [invalid             ] ❌            │
│  ⚠️ Email không đúng định dạng                      │
│  → Fix: [nguyenvana@example.com   ]               │
│                                                     │
│  Phone:       [012                 ] ❌            │
│  ⚠️ Số điện thoại không hợp lệ                      │
│  → Fix: [0901234567               ]               │
│                                                     │
│  [Re-validate]  [Save & Re-process]                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Re-validation Process**:
1. User fixes errors in form
2. Click "Re-validate"
3. Run validation rules again
4. IF pass:
   - Clear `validation_errors`
   - Record ready for transform
5. IF still fail:
   - Show new errors
   - Allow further editing

---

## 9. 🗄️ CẤU TRÚC DATABASE

### 9.1 Schema Overview

```sql
-- ============================================
--  STAGING TABLES (Temporary, with errors)
-- ============================================

CREATE TABLE staging_employee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    batch_id VARCHAR(50),
    validation_errors JSON,  -- Stores error array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_validation (validation_errors((1))),
    INDEX idx_batch (batch_id)
);

CREATE TABLE staging_order_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    product_id VARCHAR(20),
    quantity INT,
    price DECIMAL(15,2),
    batch_id VARCHAR(50),
    validation_errors JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
--  MAIN TABLES (Clean, normalized data)
-- ============================================

CREATE TABLE main_employee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    batch_id VARCHAR(50),
    original_data JSON,  -- Backup of pre-transform data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
               ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_phone (phone)
);

CREATE TABLE main_order_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL,
    product_id VARCHAR(20),
    quantity INT NOT NULL,
    price DECIMAL(15,2) NOT NULL,
    batch_id VARCHAR(50),
    original_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order (order_id),
    INDEX idx_product (product_id)
);

-- ============================================
--  RULES ENGINE TABLES
-- ============================================

CREATE TABLE validation_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rule_code VARCHAR(20) NOT NULL UNIQUE,
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,  -- validation, transformation
    entity_type VARCHAR(20) NOT NULL,  -- employee, order
    field_name VARCHAR(50),
    rule_description TEXT,
    validation_logic TEXT,  -- regex, function name, etc.
    error_message VARCHAR(255),
    is_enabled BOOLEAN DEFAULT TRUE,
    severity VARCHAR(20) DEFAULT 'ERROR',
    execution_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
               ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE transform_stages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stage_number INT NOT NULL UNIQUE,
    stage_name VARCHAR(50) NOT NULL,
    stage_description TEXT,
    is_enabled BOOLEAN DEFAULT TRUE,
    execution_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rule_stage_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id INT NOT NULL,
    stage_id INT NOT NULL,
    execution_order INT DEFAULT 0,
    FOREIGN KEY (rule_id) REFERENCES validation_rules(id),
    FOREIGN KEY (stage_id) REFERENCES transform_stages(id),
    UNIQUE KEY unique_rule_stage (rule_id, stage_id)
);

-- ============================================
--  AUDIT & LOGGING TABLES
-- ============================================

CREATE TABLE data_transformation_audit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id VARCHAR(50),
    entity_type VARCHAR(20),  -- employee, order
    entity_id VARCHAR(50),  -- NV001, ORD001
    field_name VARCHAR(50),  -- email, phone, etc.
    original_value TEXT,
    transformed_value TEXT,
    transform_rule VARCHAR(20),  -- R5, R6, R7
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_batch (batch_id),
    INDEX idx_entity (entity_type, entity_id)
);

CREATE TABLE transform_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id VARCHAR(50) UNIQUE,
    entity_type VARCHAR(20),
    total_records INT,
    valid_records INT,
    error_records INT,
    processing_time_ms INT,
    status VARCHAR(20),  -- success, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    INDEX idx_batch (batch_id),
    INDEX idx_status (status)
);

CREATE TABLE data_quality_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric_date DATE,
    entity_type VARCHAR(20),
    total_records INT,
    valid_records INT,
    error_records INT,
    valid_rate DECIMAL(5,2),
    error_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_date_entity (metric_date, entity_type)
);
```

### 9.2 Data Flow Between Tables

```
┌─────────────────────┐
│   CSV Files         │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  RabbitMQ Queues    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  staging_employee                       │
│  • Raw data from consumers              │
│  • validation_errors JSON               │
│  • May contain invalid records          │
└──────┬──────────────────────────────────┘
       │
       │ Transform Stage 1 (Validation)
       │ - Re-validate with DB rules
       │ - Mark errors
       │
       ▼
┌─────────────────────────────────────────┐
│  staging_employee (updated)             │
│  • validation_errors populated          │
└──────┬──────────────────────────────────┘
       │
       │ Transform Stage 2 (Enrichment)
       │ - Apply transformations
       │ - Normalize data
       │
       ▼
┌─────────────────────────────────────────┐
│  main_employee                          │
│  • Clean, normalized data               │
│  • original_data JSON (backup)          │
└─────────────────────────────────────────┘
       │
       │ Audit logging
       │
       ▼
┌─────────────────────────────────────────┐
│  data_transformation_audit              │
│  • Field-level change log               │
│  • Traceability                         │
└─────────────────────────────────────────┘
```

---

## 10. 📈 FLOW CHART TỔNG THỂ

### 10.1 Complete System Flow

```
                    ┌─────────────────────┐
                    │   USER UPLOADS CSV  │
                    │   via Dashboard     │
                    └──────────┬──────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │  Option 1: Producer (Java)     │
              │  • Read CSV                    │
              │  • Publish to RabbitMQ         │
              │                                │
              │  Option 2: Dashboard (Python)  │
              │  • Upload CSV                  │
              │  • Direct insert to staging    │
              └────────────┬───────────────────┘
                           │
                           ▼
           ┌───────────────────────────────────────┐
           │         RabbitMQ Queues               │
           │  ┌────────────┬──────────────┐       │
           │  │ employee   │   order      │       │
           │  │   queue    │   queue      │       │
           │  └─────┬──────┴───────┬──────┘       │
           └────────┼──────────────┼───────────────┘
                    │              │
                    ▼              ▼
        ┌─────────────────┐  ┌─────────────────┐
        │  Employee       │  │  Order          │
        │  Consumer       │  │  Consumer       │
        │  (Java)         │  │  (Java)         │
        └────────┬────────┘  └────────┬────────┘
                 │                    │
                 │ Validate           │ Validate
                 │ (Java Rules)       │ (Java Rules)
                 │                    │
                 ▼                    ▼
        ┌──────────────────────────────────────┐
        │      MySQL - Staging Tables          │
        │  ┌──────────────┬─────────────────┐  │
        │  │ staging_     │ staging_order_  │  │
        │  │ employee     │ detail          │  │
        │  │              │                 │  │
        │  │ ✅ Valid:    │ ✅ Valid:       │  │
        │  │ errors=NULL  │ errors=NULL     │  │
        │  │              │                 │  │
        │  │ ❌ Invalid:  │ ❌ Invalid:     │  │
        │  │ errors=JSON  │ errors=JSON     │  │
        │  └──────────────┴─────────────────┘  │
        └───────────────┬──────────────────────┘
                        │
                        │ USER TRIGGERS TRANSFORM
                        │ (Dashboard or Manual)
                        │
                        ▼
        ┌──────────────────────────────────────────┐
        │    TRANSFORM ENGINE (Two-Stage)          │
        │                                          │
        │  ╔══════════════════════════════════╗   │
        │  ║  STAGE 1: DATA CLEANSING         ║   │
        │  ║  • Load validation rules from DB ║   │
        │  ║  • Query staging (errors=NULL)   ║   │
        │  ║  • Apply validation rules        ║   │
        │  ║  • Mark errors in staging        ║   │
        │  ╚══════════════════════════════════╝   │
        │                                          │
        │  ╔══════════════════════════════════╗   │
        │  ║  STAGE 2: DATA ENRICHMENT        ║   │
        │  ║  • Load transform rules from DB  ║   │
        │  ║  • Query valid records           ║   │
        │  ║  • Apply transformations         ║   │
        │  ║  • Normalize data                ║   │
        │  ║  • Log to audit trail            ║   │
        │  ║  • Insert to main tables         ║   │
        │  ║  • Delete from staging           ║   │
        │  ╚══════════════════════════════════╝   │
        └───────────────┬──────────────────────────┘
                        │
                        ▼
        ┌──────────────────────────────────────────┐
        │       MySQL - Main Tables                │
        │  ┌──────────────┬─────────────────────┐  │
        │  │ main_        │ main_order_detail   │  │
        │  │ employee     │                     │  │
        │  │              │                     │  │
        │  │ ✅ Clean     │ ✅ Clean            │  │
        │  │ ✅ Normalized│ ✅ Normalized       │  │
        │  │ ✅ Enriched  │ ✅ Enriched         │  │
        │  └──────────────┴─────────────────────┘  │
        │                                          │
        │  ┌────────────────────────────────────┐  │
        │  │ data_transformation_audit          │  │
        │  │ • Field-level change log           │  │
        │  └────────────────────────────────────┘  │
        │                                          │
        │  ┌────────────────────────────────────┐  │
        │  │ transform_history                  │  │
        │  │ • Batch processing logs            │  │
        │  └────────────────────────────────────┘  │
        └──────────────────────────────────────────┘
                        │
                        ▼
        ┌──────────────────────────────────────────┐
        │       Dashboard Visualization            │
        │  • View valid data                       │
        │  • View error data                       │
        │  • Edit & re-validate errors             │
        │  • Export to CSV                         │
        │  • Monitor metrics                       │
        │  • View audit trail                      │
        └──────────────────────────────────────────┘
```

### 10.2 Detailed Transform Sequence Diagram

```
User        Dashboard      Transform      MySQL        Audit
 │              │              │            │            │
 │   Click      │              │            │            │
 │  Transform   │              │            │            │
 ├─────────────▶│              │            │            │
 │              │              │            │            │
 │              │ POST /api/   │            │            │
 │              │ run-transform│            │            │
 │              ├─────────────▶│            │            │
 │              │              │            │            │
 │              │              │ Load rules │            │
 │              │              │ (Stage 1)  │            │
 │              │              ├───────────▶│            │
 │              │              │◀───────────┤            │
 │              │              │            │            │
 │              │              │ Query      │            │
 │              │              │ staging    │            │
 │              │              ├───────────▶│            │
 │              │              │◀───────────┤            │
 │              │              │            │            │
 │              │              │ For each record:       │
 │              │              │ - Validate │            │
 │              │              │ - Mark errors          │
 │              │              ├───────────▶│            │
 │              │              │            │            │
 │              │              │ Load rules │            │
 │              │              │ (Stage 2)  │            │
 │              │              ├───────────▶│            │
 │              │              │◀───────────┤            │
 │              │              │            │            │
 │              │              │ Query valid│            │
 │              │              │ records    │            │
 │              │              ├───────────▶│            │
 │              │              │◀───────────┤            │
 │              │              │            │            │
 │              │              │ For each record:       │
 │              │              │ - Transform│            │
 │              │              │ - Log audit├───────────▶│
 │              │              │ - Insert main          │
 │              │              ├───────────▶│            │
 │              │              │ - Delete staging       │
 │              │              ├───────────▶│            │
 │              │              │            │            │
 │              │              │ Update     │            │
 │              │              │ metrics    │            │
 │              │              ├───────────▶│            │
 │              │              │            │            │
 │              │  Response    │            │            │
 │              │  JSON result │            │            │
 │              │◀─────────────┤            │            │
 │              │              │            │            │
 │  Show result │              │            │            │
 │  Reload page │              │            │            │
 │◀─────────────┤              │            │            │
 │              │              │            │            │
```

---

## 📚 TỔNG KẾT

### Điểm Mạnh Của Hệ Thống

✅ **Phân tán & Scalable**: RabbitMQ cho phép scale horizontal  
✅ **Fault Tolerant**: Message persistence, ACK mechanism  
✅ **Data Quality**: Two-stage validation & transformation  
✅ **Audit Trail**: Full traceability của data changes  
✅ **Flexible Rules**: Database-driven rules, dễ customize  
✅ **User-friendly**: Web dashboard trực quan  
✅ **Error Handling**: Comprehensive error detection & correction  

### Use Cases

1. **Data Migration**: Di chuyển data giữa hệ thống cũ → mới
2. **Data Integration**: Tích hợp data từ nhiều nguồn
3. **Data Cleansing**: Làm sạch data không chuẩn
4. **ETL Pipeline**: Extract-Transform-Load cho Data Warehouse
5. **Master Data Management**: Quản lý data tập trung

### Mở Rộng Trong Tương Lai

🔮 **Potential Enhancements**:
- Real-time streaming với Kafka
- Machine Learning cho data quality prediction
- API Gateway cho external integrations
- Advanced scheduling với Apache Airflow
- Data versioning & time travel queries

---

**Document Version**: 1.0  
**Last Updated**: December 7, 2025  
**Author**: ETL Team  
**Tech Stack**: Java 11, RabbitMQ, MySQL, Flask, Docker
