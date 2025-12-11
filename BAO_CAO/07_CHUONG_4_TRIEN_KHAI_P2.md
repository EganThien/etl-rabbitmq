# CHƯƠNG 4: TRIỂN KHAI HIỆN THỰC (Phần 2)

## 4.5 Kết quả chạy chương trình

### 4.5.1 Khởi động hệ thống

**Bước 1: Start Docker Containers**

```powershell
docker-compose up -d
```

**Output:**
```
[+] Running 4/4
 ✔ Network etl-rabbitmq_default      Created
 ✔ Container etl-rabbitmq-mysql-1    Started
 ✔ Container etl-rabbitmq-rabbitmq-1 Started
 ✔ Container etl-rabbitmq-dashboard-1 Started
```

**Bước 2: Load Database Schema**

```powershell
.\scripts\load-schema.ps1
```

**Output:**
```
Loading create_tables.sql...
Tables created successfully
Loading rules_configuration.sql...
Rules loaded successfully
```

### 4.5.2 Producer Extract Results

**Chạy Producer:**

```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.producer.CSVProducer"
```

**Output:**
```
[INFO] Scanning for projects...
[INFO] -----------------------------------------------------------
[INFO] Building etl-rabbitmq 1.0-SNAPSHOT
[INFO] -----------------------------------------------------------

Connecting to RabbitMQ...
Declaring queue: employee-queue
Reading CSV: employee.csv
Loaded 15 employees from CSV

Publishing messages to RabbitMQ...
Published employee: NV001
Published employee: NV002
Published employee: NV003
...
Published employee: NV015

✓ All 15 messages published successfully
Connection closed
```

**Verification - RabbitMQ Management UI:**

```
Queue: employee-queue
Ready: 15 messages
Unacked: 0 messages
Total: 15 messages
Publish rate: 15/s
```

### 4.5.3 Consumer Validate Results

**Chạy Consumer:**

```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.consumer.EmployeeConsumer"
```

**Output:**
```
Starting Employee Consumer...
Connected to RabbitMQ
Subscribed to queue: employee-queue
Waiting for messages...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[✓] Processing: NV001 - Nguyễn Văn A
    Validation: PASS
    Inserted to staging_employee (id=1)

[✗] Processing: NV002 - Trần Thị B
    Validation: FAIL
    Errors:
      - email: Email không đúng định dạng (invalid@)
      - phone: Số điện thoại không hợp lệ (0123)
    Inserted to staging_employee (id=2) with errors

[✓] Processing: NV003 - Lê Văn C
    Validation: PASS
    Inserted to staging_employee (id=3)

[✗] Processing: NV004 - Phạm Thị D
    Validation: FAIL
    Errors:
      - employeeId: Mã nhân viên không được rỗng
    Inserted to staging_employee (id=4) with errors

... (continued)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
  Total processed: 15 records
  Valid: 10 records
  Errors: 5 records
  Success rate: 66.67%

Consumer running. Press CTRL+C to stop.
```

**Verification - Database:**

```sql
-- Check staging data
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN validation_errors IS NULL THEN 1 ELSE 0 END) as valid,
    SUM(CASE WHEN validation_errors IS NOT NULL THEN 1 ELSE 0 END) as errors
FROM staging_employee;
```

**Result:**
```
+-------+-------+--------+
| total | valid | errors |
+-------+-------+--------+
|    15 |    10 |      5 |
+-------+-------+--------+
```

### 4.5.4 Transform Results

**Chạy Transform qua Dashboard:**

**Step 1: Access Dashboard**
- Navigate to: http://localhost:5000
- Click button "Chạy Transform"

**Output (Console):**
```
Starting Two-Stage Transform...
Batch ID: transform_20240115_143052

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 1: DATA CLEANSING (Validation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Loading validation rules...
  Loaded 4 rules: [R1, R2, R3, R4]

Querying staging records (validation_errors = NULL)...
  Found 10 valid records to re-validate

Re-validating records...
  [1/10] NV001 - Nguyễn Văn A: ✓ PASS
  [2/10] NV003 - Lê Văn C: ✓ PASS
  [3/10] NV005 - Hoàng Văn E: ✗ FAIL (email format)
  [4/10] NV006 - Vũ Thị F: ✓ PASS
  [5/10] NV007 - Đỗ Văn G: ✓ PASS
  [6/10] NV008 - Bùi Thị H: ✓ PASS
  [7/10] NV009 - Đinh Văn I: ✗ FAIL (phone format)
  [8/10] NV011 - Mai Thị K: ✓ PASS
  [9/10] NV013 - Chu Văn M: ✓ PASS
  [10/10] NV015 - Dương Thị O: ✓ PASS

Stage 1 Summary:
  Records validated: 10
  Still valid: 8
  New errors found: 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STAGE 2: DATA ENRICHMENT (Transformation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Loading transformation rules...
  Loaded 3 rules: [R5, R6, R7]

Querying valid records only...
  Found 8 records to transform

Applying transformations...
  [1/8] NV001 - Nguyễn Văn A
    full_name: NGUYEN VAN A → Nguyễn Văn A
    email: ADMIN@MAIL.COM → admin@mail.com
    phone: 0901234567 → +84901234567
    ✓ Inserted to main_employee
  
  [2/8] NV003 - Lê Văn C
    full_name: LE VAN C → Lê Văn C
    email: C@MAIL.COM → c@mail.com
    phone: 0903456789 → +84903456789
    ✓ Inserted to main_employee

  ... (continued for all 8 records)

Stage 2 Summary:
  Records transformed: 8
  Field changes logged: 24
  Inserted to main_employee: 8
  Deleted from staging: 8

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Transform completed successfully!
Batch ID: transform_20240115_143052
Total time: 2.34 seconds
```

**Dashboard Response:**

```json
{
  "success": true,
  "batch_id": "transform_20240115_143052",
  "employees": 8,
  "orders": 0,
  "errors": 7,
  "time_elapsed": "2.34s"
}
```

### 4.5.5 Final Database State

**Main Tables (Clean Data):**

```sql
SELECT * FROM main_employee;
```

**Result:**
```
+----+-------------+---------------+-------------------+----------------+
| id | employee_id | full_name     | email             | phone          |
+----+-------------+---------------+-------------------+----------------+
|  1 | NV001       | Nguyễn Văn A  | admin@mail.com    | +84901234567   |
|  2 | NV003       | Lê Văn C      | c@mail.com        | +84903456789   |
|  3 | NV006       | Vũ Thị F      | f@mail.com        | +84906789012   |
|  4 | NV007       | Đỗ Văn G      | g@mail.com        | +84907890123   |
|  5 | NV008       | Bùi Thị H     | h@mail.com        | +84908901234   |
|  6 | NV011       | Mai Thị K     | k@mail.com        | +84911234567   |
|  7 | NV013       | Chu Văn M     | m@mail.com        | +84913456789   |
|  8 | NV015       | Dương Thị O   | o@mail.com        | +84915678901   |
+----+-------------+---------------+-------------------+----------------+
8 rows in set
```

**Staging Tables (Error Records):**

```sql
SELECT employee_id, full_name, validation_errors 
FROM staging_employee 
WHERE validation_errors IS NOT NULL;
```

**Result:**
```
+-------------+------------+------------------------------------------------+
| employee_id | full_name  | validation_errors                              |
+-------------+------------+------------------------------------------------+
| NV002       | Trần Thị B | [{"field":"email","message":"Email không đúng  |
|             |            | định dạng"},{"field":"phone","message":"SĐT    |
|             |            | không hợp lệ"}]                                |
+-------------+------------+------------------------------------------------+
| NV004       | Phạm Thị D | [{"field":"employeeId","message":"Mã NV rỗng"}]|
+-------------+------------+------------------------------------------------+
| NV005       | Hoàng Văn E| [{"field":"email","message":"Email sai format"}]|
+-------------+------------+------------------------------------------------+
| NV009       | Đinh Văn I | [{"field":"phone","message":"Phone sai format"}]|
+-------------+------------+------------------------------------------------+
... (3 more rows)
7 rows in set
```

---

## 4.6 Kiểm thử hệ thống

### 4.6.1 Unit Testing

**Test Case 1: Validation Rules**

```java
@Test
public void testEmailValidation() {
    EmailRule<Employee> rule = new EmailRule<>(e -> e.getEmail(), "email");
    
    // Valid case
    Employee validEmp = new Employee();
    validEmp.setEmail("user@example.com");
    RuleResult result = rule.validate(validEmp);
    assertTrue(result.isOk());
    
    // Invalid case
    Employee invalidEmp = new Employee();
    invalidEmp.setEmail("invalid@");
    RuleResult result2 = rule.validate(invalidEmp);
    assertFalse(result2.isOk());
    assertEquals("Email không đúng định dạng", result2.getMessage());
}
```

**Test Results:**
```
Running EmailRuleTest...
  ✓ testEmailValidation - PASSED
  ✓ testEmailEdgeCases - PASSED
  ✓ testEmailNullValue - PASSED

Running PhoneRuleTest...
  ✓ testVietnamesePhone - PASSED
  ✓ testE164Format - PASSED
  ✓ testInvalidFormats - PASSED

All unit tests: 6/6 PASSED
```

### 4.6.2 Integration Testing

**Test Case 2: End-to-End ETL Flow**

```powershell
.\scripts\run-e2e.ps1
```

**Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
E2E Integration Test
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/7] Cleanup - Truncate all tables
  ✓ staging_employee truncated
  ✓ main_employee truncated
  ✓ audit_trail truncated

[2/7] Extract - Run Producer
  ✓ Loaded 15 records from CSV
  ✓ Published 15 messages to RabbitMQ

[3/7] Validate - Run Consumer (wait 5s)
  ✓ Consumer processed 15 messages
  ✓ 10 valid, 5 errors

[4/7] Transform Stage 1 - Data Cleansing
  ✓ Re-validated 10 records
  ✓ Found 2 additional errors
  ✓ 8 records remain valid

[5/7] Transform Stage 2 - Data Enrichment
  ✓ Transformed 8 records
  ✓ Applied 24 field changes
  ✓ Inserted 8 to main_employee

[6/7] Verify Database State
  ✓ main_employee: 8 rows
  ✓ staging_employee: 7 error rows
  ✓ audit_trail: 24 change logs

[7/7] Verify Data Quality
  ✓ All emails lowercase
  ✓ All phones E.164 format
  ✓ All names title case
  ✓ No duplicates in main_employee

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
E2E Test Result: ✓ PASSED (all 7 steps)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4.6.3 Performance Testing

**Test Case 3: Bulk Load Performance**

```powershell
.\scripts\performance-test.ps1 -Records 10000
```

**Output:**
```
Performance Test: 10,000 records

Extract Phase:
  CSV Read: 1.2s
  Publish to RabbitMQ: 3.4s
  Total: 4.6s (2174 records/s)

Validate Phase:
  Consumer processing: 8.7s
  DB inserts: 2.1s
  Total: 10.8s (926 records/s)

Transform Phase:
  Stage 1 (Validation): 3.5s
  Stage 2 (Enrichment): 5.2s
  Total: 8.7s (1149 records/s)

Overall ETL:
  Total time: 24.1s
  Throughput: 415 records/s
  Valid records: 8,245 (82.45%)
  Error records: 1,755 (17.55%)
```

**Bảng 4.1 - Performance Metrics**

| Metric | Value | Unit |
|--------|-------|------|
| Total Records | 10,000 | records |
| Total Processing Time | 24.1 | seconds |
| Throughput | 415 | records/s |
| Extract Rate | 2,174 | records/s |
| Validate Rate | 926 | records/s |
| Transform Rate | 1,149 | records/s |
| Success Rate | 82.45% | % |

### 4.6.4 Stress Testing

**Test Case 4: Concurrent Processing**

Chạy 5 Consumers đồng thời:

```powershell
.\scripts\stress-test.ps1 -Consumers 5 -Records 50000
```

**Output:**
```
Stress Test: 5 concurrent consumers, 50,000 records

Starting consumers...
  Consumer 1: Started (PID 4521)
  Consumer 2: Started (PID 4522)
  Consumer 3: Started (PID 4523)
  Consumer 4: Started (PID 4524)
  Consumer 5: Started (PID 4525)

Publishing 50,000 messages...
  Progress: [████████████████████] 100% (50000/50000)
  Time: 18.3s

Processing messages...
  Consumer 1: 10,234 processed
  Consumer 2: 9,876 processed
  Consumer 3: 10,102 processed
  Consumer 4: 9,945 processed
  Consumer 5: 9,843 processed
  Total: 50,000 processed
  Time: 42.7s
  Throughput: 1,171 records/s

CPU Usage: 68%
Memory Usage: 2.4 GB
```

---

## 4.7 Đánh giá và nhận xét

### 4.7.1 Ưu điểm của hệ thống

**1. Kiến trúc linh hoạt**
- Message Queue tách biệt Producer và Consumer
- Two-Stage Transform cho phép tùy chỉnh logic
- Rules Engine dễ dàng thêm/sửa rules

**2. Data Quality cao**
- Validation ở nhiều lớp (Consumer + Transform Stage 1)
- Transformation đảm bảo chuẩn hóa dữ liệu
- Audit Trail theo dõi mọi thay đổi

**3. Khả năng mở rộng tốt**
- Horizontal scaling: Thêm Consumers dễ dàng
- Vertical scaling: Tăng resources cho containers
- Batch processing hiệu quả với 415 records/s

**4. Fault Tolerance**
- RabbitMQ persistent messages (không mất data)
- Consumer manual ACK (xử lý lại nếu fail)
- Database transactions (ACID compliance)

**5. Monitoring & Observability**
- Dashboard real-time metrics
- RabbitMQ Management UI
- Audit Trail field-level changes

### 4.7.2 Hạn chế

**1. Performance bottlenecks**
- Transform Stage 2 chậm hơn Extract (1149 vs 2174 records/s)
- Single-threaded Java Transform (chưa parallel)

**2. Error handling**
- Validation errors chỉ log, không auto-retry
- No dead-letter queue cho failed messages

**3. Dashboard limitations**
- Python Flask không scale tốt cho high traffic
- No WebSocket (phải refresh để xem updates)

**4. Testing coverage**
- Unit tests chưa đầy đủ (chỉ cover validation rules)
- Missing integration tests cho edge cases

### 4.7.3 Bài học kinh nghiệm

**1. Thiết kế Database Schema**
- JSON column rất hữu ích cho validation_errors
- Nên có `original_data` column để rollback
- Index quan trọng cho performance (employee_id, batch_id)

**2. Message Queue Best Practices**
- Durable queues + Persistent messages = Data safety
- Manual ACK tốt hơn auto ACK (control over failure)
- Prefetch count = 1 để load balancing tốt hơn

**3. Validation Strategy**
- Fail fast ở Consumer (tiết kiệm resources)
- Database-driven rules linh hoạt hơn hard-coded
- Regex patterns cần test kỹ (nhiều edge cases)

**4. Transform Logic**
- Two-Stage tốt hơn single-pass (separation of concerns)
- Log mọi transformation (audit trail quan trọng)
- Batch inserts nhanh hơn nhiều so với single inserts

### 4.7.4 Hướng phát triển

**1. Tối ưu Performance**
- Parallel Transform với ExecutorService (Java)
- Batch processing lớn hơn (500 → 1000 records/batch)
- Redis cache cho validation rules

**2. Cải thiện Monitoring**
- Prometheus metrics + Grafana dashboards
- AlertManager cho critical errors
- Distributed tracing với Jaeger

**3. Advanced Features**
- Dead-letter queue cho failed messages
- Auto-retry với exponential backoff
- Machine Learning cho data quality prediction

**4. Scalability**
- Kubernetes deployment thay vì Docker Compose
- Horizontal Pod Autoscaler
- Distributed message queue (RabbitMQ cluster)

---

**Tóm tắt Chương 4:**

Chương 4 đã trình bày đầy đủ quá trình triển khai hiện thực hệ thống ETL:
- Môi trường và giao diện người dùng
- Code implementation cho từng phase ETL
- Kết quả chạy chương trình với output thực tế
- Kiểm thử toàn diện (Unit, Integration, Performance, Stress)
- Đánh giá ưu/nhược điểm và hướng phát triển

Hệ thống đã đạt được:
- ✅ Throughput: 415 records/s
- ✅ Success rate: 82.45%
- ✅ Data quality: 100% chuẩn hóa
- ✅ Fault tolerance: RabbitMQ persistent + manual ACK
- ✅ Observability: Dashboard + Audit Trail

Chương tiếp theo sẽ tổng kết toàn bộ đồ án với kết luận và hướng phát triển tương lai.
