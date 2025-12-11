# CHƯƠNG 4: TRIỂN KHAI HIỆN THỰC

## 4.1 Môi trường triển khai

### 4.1.1 Công nghệ sử dụng

**Backend:**
- Java 11+ với Maven build tool
- Spring Framework (dependency injection, connection pooling)
- Jackson (JSON serialization/deserialization)
- RabbitMQ Java Client
- MySQL Connector/J (JDBC driver)

**Frontend:**
- Flask (Python 3.11) web framework
- Bootstrap 5.3 (responsive UI)
- JavaScript (vanilla JS, fetch API)

**Infrastructure:**
- Docker & Docker Compose (containerization)
- MySQL 8.0 (relational database)
- RabbitMQ 3.x với Management Plugin

**Development Tools:**
- VS Code / IntelliJ IDEA
- Maven (build & dependency management)
- Git (version control)

### 4.1.2 Cấu trúc thư mục dự án

```
etl-rabbitmq/
├── src/
│   ├── main/
│   │   ├── java/com/example/etl/
│   │   │   ├── Application.java
│   │   │   ├── producer/
│   │   │   │   └── CSVProducer.java
│   │   │   ├── consumer/
│   │   │   │   ├── EmployeeConsumer.java
│   │   │   │   └── OrderConsumer.java
│   │   │   ├── transform/
│   │   │   │   └── TransformLoad.java
│   │   │   ├── models/
│   │   │   │   ├── Employee.java
│   │   │   │   └── OrderDetail.java
│   │   │   ├── rules/
│   │   │   │   ├── RecordValidator.java
│   │   │   │   └── impl/
│   │   │   └── utils/
│   │   │       ├── DbUtil.java
│   │   │       └── RabbitUtil.java
│   │   └── resources/
│   │       ├── data/
│   │       │   ├── employee.csv
│   │       │   └── order_detail.csv
│   │       └── sql/
│   │           ├── create_tables.sql
│   │           └── rules_configuration.sql
│   └── test/
├── dashboard/
│   ├── app.py
│   ├── upload.html
│   ├── history.html
│   ├── rules.html
│   └── requirements.txt
├── scripts/
│   ├── load-schema.ps1
│   └── run-full.ps1
├── docker-compose.yml
├── Dockerfile
└── pom.xml
```

---

## 4.2 Giao diện người dùng

### 4.2.1 Dashboard chính

**[Hình 4.1 - Giao diện Dashboard chính]**

Dashboard cung cấp tổng quan về hệ thống ETL:

**Các thành phần chính:**

1. **Status Cards (Thẻ trạng thái)**
   - Staging Data: Số lượng records đang chờ transform
   - Valid Data: Records đã clean trong main tables
   - Error Data: Records có validation errors

2. **Transform Button**
   - Nút "Chạy Transform" kích hoạt two-stage transform
   - Hiển thị progress và kết quả real-time

3. **Data Tables**
   - Tab "✓ Dữ Liệu Hợp Lệ": Hiển thị records từ main tables
   - Tab "✗ Dữ Liệu Lỗi": Hiển thị records với validation_errors

4. **Navigation Menu**
   - Upload: Tải lên CSV files
   - History: Xem lịch sử transform và audit trail
   - Rules: Quản lý validation rules
   - Export: Xuất dữ liệu ra CSV

**Đặc điểm:**
- Responsive design với Bootstrap 5
- Real-time updates qua AJAX
- Color-coded status (green cho valid, red cho errors)
- Expandable error details

### 4.2.2 Giao diện Upload CSV

**[Hình 4.2 - Giao diện Upload CSV]**

Giao diện upload cho phép user tải file CSV lên hệ thống:

**Features:**
- Drag & drop interface
- File type detection tự động (Employee vs Order)
- Progress indicator
- Preview uploaded files
- Batch processing option
- Clear data before upload option
- Auto-trigger transform checkbox

**Workflow:**
1. User drag-drop hoặc select file CSV
2. System detect file type based on headers
3. Parse CSV và validate format
4. Insert trực tiếp vào staging tables
5. Display upload results (rows inserted, errors)
6. Option để chạy transform ngay

### 4.2.3 Giao diện Rules Management

**[Hình 4.3 - Giao diện Rules Management]**

Giao diện quản lý validation và transformation rules:

**Features:**
- Danh sách tất cả rules (R1-R15)
- Enable/Disable toggle switches
- Rule details (type, entity, field, logic)
- Execution order
- Edit rule parameters
- Add new custom rules

**Rule Information Display:**
- Rule Code: R1, R2, R3...
- Rule Name: Descriptive name
- Type: validation | transformation
- Entity: employee | order
- Field: Tên field áp dụng
- Logic: not_empty | regex | title_case...
- Status: Active | Inactive

### 4.2.4 Giao diện History & Audit Trail

**[Hình 4.4 - Giao diện History & Audit Trail]**

Giao diện theo dõi lịch sử và audit:

**Sections:**

1. **Transform History**
   - Batch ID
   - Timestamp
   - Records processed (valid/error)
   - Processing time
   - Status (success/failed)

2. **Audit Trail (Field-level changes)**
   - Entity ID
   - Field name
   - Original value
   - Transformed value
   - Transform rule applied
   - Timestamp

3. **Data Quality Metrics**
   - Chart: Valid rate vs Error rate over time
   - Daily metrics table
   - Trend analysis

### 4.2.5 RabbitMQ Management Console

**[Hình 4.5 - RabbitMQ Management Console]**

RabbitMQ cung cấp management UI tại http://localhost:15672

**Monitoring:**
- Queues list với message counts
- Message rates (publish/deliver)
- Consumer status
- Connection details
- Channel information

---

## 4.3 Các bước xử lý chính của ETL

### 4.3.1 Extract Phase

**Bước 1: Đọc CSV File**

```java
public List<Employee> readEmployeeCSV(String filePath) {
    List<Employee> employees = new ArrayList<>();
    
    try (CSVReader reader = new CSVReader(new FileReader(filePath))) {
        reader.readNext(); // Skip header
        
        String[] line;
        while ((line = reader.readNext()) != null) {
            Employee emp = new Employee();
            emp.setEmployeeId(line[0].trim());
            emp.setFullName(line[1].trim());
            emp.setEmail(line[2].trim());
            emp.setPhone(line[3].trim());
            employees.add(emp);
        }
    }
    return employees;
}
```

**Bước 2: Publish lên RabbitMQ**

```java
public void publishMessages(List<Employee> employees) throws Exception {
    Connection conn = RabbitUtil.getConnection();
    Channel channel = conn.createChannel();
    
    for (Employee emp : employees) {
        String json = objectMapper.writeValueAsString(emp);
        channel.basicPublish("", "employee-queue",
            MessageProperties.PERSISTENT_TEXT_PLAIN,
            json.getBytes());
    }
    channel.close();
    conn.close();
}
```

### 4.3.2 Validate Phase

**Bước 1: Consumer Subscribe Queue**

```java
public void startConsuming() throws Exception {
    Channel channel = RabbitUtil.getConnection().createChannel();
    channel.queueDeclare("employee-queue", true, false, false, null);
    
    DeliverCallback callback = (consumerTag, delivery) -> {
        String message = new String(delivery.getBody());
        processMessage(message, delivery.getEnvelope().getDeliveryTag());
    };
    
    channel.basicConsume("employee-queue", false, callback, 
        consumerTag -> {});
}
```

**Bước 2: Validate Record**

```java
private void processMessage(String json, long deliveryTag) {
    Employee emp = objectMapper.readValue(json, Employee.class);
    
    // Setup validator
    RecordValidator<Employee> validator = new RecordValidator<>();
    validator.addRule(new NotEmptyRule<>(e -> e.getEmployeeId()));
    validator.addRule(new EmailRule<>(e -> e.getEmail()));
    validator.addRule(new PhoneNumberRule<>(e -> e.getPhone()));
    
    // Validate
    List<RuleResult> results = validator.validateAll(emp);
    boolean allPass = results.stream().allMatch(RuleResult::isOk);
    
    // Insert to staging
    insertToStaging(emp, allPass ? null : buildErrorsJSON(results));
    
    // ACK message
    channel.basicAck(deliveryTag, false);
}
```

### 4.3.3 Transform Phase

**Stage 1: Data Cleansing**

```python
def transform_stage_1(entity_type):
    # Load validation rules
    rules = get_active_rules_by_stage(1, entity_type)
    
    # Query staging records
    records = query_staging(entity_type, 
                           where="validation_errors IS NULL")
    
    for record in records:
        errors = []
        for rule in rules:
            error = apply_validation_rule(rule, record)
            if error:
                errors.append(error)
        
        if errors:
            update_validation_errors(record['id'], 
                                    json.dumps(errors))
```

**Stage 2: Data Enrichment**

```python
def transform_stage_2(entity_type):
    # Load transformation rules
    rules = get_active_rules_by_stage(2, entity_type)
    
    # Query valid records only
    records = query_staging(entity_type, 
                           where="validation_errors IS NULL")
    
    for record in records:
        original_data = dict(record)
        transformed_data = dict(record)
        
        # Apply transformations
        for rule in rules:
            field = rule['field_name']
            old_value = transformed_data[field]
            new_value = apply_transformation(rule, old_value)
            
            if old_value != new_value:
                transformed_data[field] = new_value
                log_audit_trail(record['id'], field, 
                               old_value, new_value, rule['rule_code'])
        
        # Insert to main table
        insert_to_main(transformed_data, original_data)
        delete_from_staging(record['id'])
```

### 4.3.4 Load Phase

**Insert to Main Tables**

```java
public void loadToMain(Employee emp, String originalData) {
    String sql = "INSERT INTO main_employee " +
                 "(employee_id, full_name, email, phone, " +
                 "batch_id, original_data) " +
                 "VALUES (?, ?, ?, ?, ?, ?) " +
                 "ON DUPLICATE KEY UPDATE " +
                 "full_name = VALUES(full_name), " +
                 "email = VALUES(email), " +
                 "phone = VALUES(phone), " +
                 "updated_at = CURRENT_TIMESTAMP";
    
    try (PreparedStatement ps = conn.prepareStatement(sql)) {
        ps.setString(1, emp.getEmployeeId());
        ps.setString(2, emp.getFullName());
        ps.setString(3, emp.getEmail());
        ps.setString(4, emp.getPhone());
        ps.setString(5, emp.getBatchId());
        ps.setString(6, originalData);
        ps.executeUpdate();
    }
}
```

---

## 4.4 Một số đoạn code quan trọng

### 4.4.1 Code Extract (Producer)

**CSVProducer.java - Main Extract Logic**

```java
public class CSVProducer {
    private static final String EMPLOYEE_QUEUE = "employee-queue";
    private ObjectMapper objectMapper = new ObjectMapper();
    
    public void produce() throws Exception {
        Connection conn = RabbitUtil.getConnection();
        Channel channel = conn.createChannel();
        
        // Declare durable queue
        channel.queueDeclare(EMPLOYEE_QUEUE, true, false, false, null);
        
        // Read CSV
        List<Employee> employees = readCSV("employee.csv");
        System.out.println("Loaded " + employees.size() + " employees");
        
        // Publish messages
        for (Employee emp : employees) {
            String json = objectMapper.writeValueAsString(emp);
            channel.basicPublish("", EMPLOYEE_QUEUE,
                MessageProperties.PERSISTENT_TEXT_PLAIN,
                json.getBytes());
        }
        
        channel.close();
        conn.close();
        System.out.println("Published all messages");
    }
}
```

### 4.4.2 Code Validate (Consumer + Rules)

**EmployeeConsumer.java - Validation Logic**

```java
public class EmployeeConsumer {
    private RecordValidator<Employee> validator;
    
    public EmployeeConsumer() {
        validator = new RecordValidator<>();
        validator.addRule(new NotEmptyRule<>(
            e -> e.getEmployeeId(), "employeeId"));
        validator.addRule(new NotEmptyRule<>(
            e -> e.getFullName(), "fullName"));
        validator.addRule(new EmailRule<>(
            e -> e.getEmail(), "email"));
        validator.addRule(new PhoneNumberRule<>(
            e -> e.getPhone(), "phone"));
    }
    
    private void processMessage(String json, long tag) {
        Employee emp = objectMapper.readValue(json, Employee.class);
        List<RuleResult> results = validator.validateAll(emp);
        
        boolean allPass = results.stream().allMatch(RuleResult::isOk);
        String errors = allPass ? null : buildErrors(results);
        
        saveToStaging(emp, errors);
        channel.basicAck(tag, false);
    }
}
```

**RecordValidator.java - Rules Engine**

```java
public class RecordValidator<T> {
    private List<ValidationRule<T>> rules = new ArrayList<>();
    
    public void addRule(ValidationRule<T> rule) {
        rules.add(rule);
    }
    
    public List<RuleResult> validateAll(T record) {
        List<RuleResult> results = new ArrayList<>();
        for (ValidationRule<T> rule : rules) {
            results.add(rule.validate(record));
        }
        return results;
    }
}
```

### 4.4.3 Code Transform (Two-Stage)

**Dashboard app.py - Transform Endpoint**

```python
@app.route('/api/run-transform-v2', methods=['POST'])
def run_transform_v2():
    batch_id = f"transform_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Stage 1: Data Cleansing
    validation_rules = get_active_rules_by_stage(1, 'employee')
    staging_records = query_staging_valid()
    
    for record in staging_records:
        errors = []
        for rule in validation_rules:
            error = apply_validation_rule(rule, record)
            if error:
                errors.append(error)
        
        if errors:
            update_staging_errors(record['id'], json.dumps(errors))
    
    # Stage 2: Data Enrichment
    transform_rules = get_active_rules_by_stage(2, 'employee')
    valid_records = query_staging_valid()
    
    for record in valid_records:
        transformed = apply_transformations(record, transform_rules)
        insert_to_main(transformed)
        delete_from_staging(record['id'])
    
    return jsonify({'success': True, 'batch_id': batch_id})
```

### 4.4.4 Code Load (Database Operations)

**TransformLoad.java - Batch Insert**

```java
public void loadEmployeesToMain() throws Exception {
    String sql = "SELECT * FROM staging_employee " +
                 "WHERE validation_errors IS NULL";
    
    try (PreparedStatement sel = conn.prepareStatement(sql);
         ResultSet rs = sel.executeQuery()) {
        
        List<Employee> batch = new ArrayList<>();
        while (rs.next()) {
            Employee emp = mapResultSet(rs);
            batch.add(emp);
            
            if (batch.size() >= 500) {
                batchInsertToMain(batch);
                batch.clear();
            }
        }
        
        if (!batch.isEmpty()) {
            batchInsertToMain(batch);
        }
    }
}

private void batchInsertToMain(List<Employee> employees) {
    String sql = "INSERT INTO main_employee (...) VALUES (...)";
    try (PreparedStatement ps = conn.prepareStatement(sql)) {
        for (Employee emp : employees) {
            ps.setString(1, emp.getEmployeeId());
            // ... set other parameters
            ps.addBatch();
        }
        ps.executeBatch();
    }
}
```

---

**Tóm tắt Chương 4 (Phần 1):**

Chương 4 đã trình bày:
- Môi trường triển khai và công nghệ sử dụng
- Các giao diện người dùng (Dashboard, Upload, Rules, History)
- Các bước xử lý ETL chi tiết (Extract-Validate-Transform-Load)
- Code implementation cho từng phase

Phần 2 của Chương 4 sẽ trình bày kết quả chạy chương trình, kiểm thử và đánh giá hệ thống.
