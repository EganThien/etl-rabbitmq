# CHƯƠNG 2: CƠ SỞ LÝ THUYẾT

---

## 2.1. BIỂU THỨC CHÍNH QUY (REGULAR EXPRESSION)

### 2.1.1. Khái niệm

**Regular Expression (Regex)** là một chuỗi ký tự đặc biệt dùng để mô tả một pattern (mẫu) tìm kiếm trong văn bản. Regex được sử dụng rộng rãi trong validation dữ liệu, tìm kiếm và thay thế văn bản.

### 2.1.2. Các thành phần cơ bản

| Ký hiệu | Ý nghĩa | Ví dụ |
|---------|---------|-------|
| `^` | Bắt đầu chuỗi | `^Hello` match "Hello world" |
| `$` | Kết thúc chuỗi | `world$` match "Hello world" |
| `.` | Bất kỳ ký tự nào | `a.c` match "abc", "a1c" |
| `*` | 0 hoặc nhiều lần | `ab*c` match "ac", "abc", "abbc" |
| `+` | 1 hoặc nhiều lần | `ab+c` match "abc", "abbc" |
| `?` | 0 hoặc 1 lần | `colou?r` match "color", "colour" |
| `[]` | Tập ký tự | `[abc]` match "a", "b", hoặc "c" |
| `\d` | Chữ số (0-9) | `\d+` match "123" |
| `\w` | Ký tự chữ và số | `\w+` match "hello123" |
| `\s` | Khoảng trắng | `\s+` match spaces, tabs |

### 2.1.3. Ứng dụng trong đồ án

**1. Validation Email:**
```java
^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
```
- `[a-zA-Z0-9._%+-]+`: Local part (trước @)
- `@`: Ký tự @
- `[a-zA-Z0-9.-]+`: Domain name
- `\.`: Dấu chấm
- `[a-zA-Z]{2,}`: Extension (.com, .vn, etc.)

**2. Validation Phone Number (Vietnam):**
```java
^(\+84|84|0)[0-9]{9,10}$
```
- `(\+84|84|0)`: Bắt đầu với +84, 84, hoặc 0
- `[0-9]{9,10}`: 9-10 chữ số tiếp theo

**3. Validation Product ID:**
```java
^PROD[0-9]{3,6}$
```
- `PROD`: Prefix cố định
- `[0-9]{3,6}`: 3-6 chữ số

---

## 2.2. DESIGN PATTERNS TRONG ETL

### 2.2.1. Strategy Pattern

**Mục đích**: Định nghĩa một họ các thuật toán, đóng gói từng thuật toán và làm cho chúng có thể thay thế lẫn nhau.

**Ứng dụng trong đồ án**: Validation Rules

```java
// Strategy interface
public interface ValidationRule<T> {
    RuleResult validate(T object);
}

// Concrete strategies
public class EmailRule<T> implements ValidationRule<T> {
    public RuleResult validate(T object) {
        String email = fieldExtractor.apply(object);
        if (email.matches(EMAIL_REGEX)) {
            return RuleResult.ok();
        }
        return RuleResult.fail("Email không hợp lệ");
    }
}

public class PhoneNumberRule<T> implements ValidationRule<T> {
    public RuleResult validate(T object) {
        // Logic validate phone
    }
}
```

**Lợi ích**:
- Dễ dàng thêm rule mới
- Tuân thủ Open/Closed Principle
- Code dễ test và maintain

### 2.2.2. Factory Pattern

**Mục đích**: Tạo đối tượng mà không cần chỉ định class cụ thể.

**Ứng dụng trong đồ án**: Database Connection

```java
public class DbUtil {
    public static Connection getConnection() {
        String host = System.getenv("MYSQL_HOST");
        String user = System.getenv("MYSQL_USER");
        String pass = System.getenv("MYSQL_PASSWORD");
        
        String url = String.format(
            "jdbc:mysql://%s:3306/etl_db", host
        );
        return DriverManager.getConnection(url, user, pass);
    }
}
```

### 2.2.3. DAO Pattern

**Mục đích**: Tách biệt logic truy cập dữ liệu khỏi business logic.

**Ứng dụng trong đồ án**: Database Operations

```java
public class EmployeeDAO {
    public void insertStaging(Employee emp, String errors) {
        String sql = "INSERT INTO staging_employee " +
                     "(employee_id, full_name, email, phone, " +
                     "validation_errors) VALUES (?, ?, ?, ?, ?)";
        // Execute SQL
    }
    
    public List<Employee> getValidRecords() {
        String sql = "SELECT * FROM staging_employee " +
                     "WHERE validation_errors IS NULL";
        // Execute and return results
    }
}
```

### 2.2.4. Observer Pattern (Message Queue)

**Mục đích**: Định nghĩa mối quan hệ một-nhiều giữa các đối tượng.

**Ứng dụng trong đồ án**: RabbitMQ Producer-Consumer

```java
// Producer (Subject)
channel.basicPublish("", "employee-queue", null, message);

// Consumer (Observer)
channel.basicConsume("employee-queue", false, 
    (consumerTag, delivery) -> {
        // Process message
        channel.basicAck(delivery.getEnvelope().getDeliveryTag());
    },
    consumerTag -> {}
);
```

---

## 2.3. FRAMEWORK VÀ CÔNG NGHỆ SỬ DỤNG

### 2.3.1. RabbitMQ

**Giới thiệu:**
RabbitMQ là một message broker mã nguồn mở, implement giao thức AMQP (Advanced Message Queuing Protocol). Nó cho phép các ứng dụng giao tiếp với nhau thông qua message queue.

**Các khái niệm cơ bản:**

1. **Producer**: Ứng dụng gửi message
2. **Queue**: Bộ đệm lưu trữ messages
3. **Consumer**: Ứng dụng nhận message
4. **Exchange**: Định tuyến messages đến queues
5. **Binding**: Liên kết giữa exchange và queue

**Đặc điểm nổi bật:**
- ✅ Persistent messages: Message được lưu trên disk
- ✅ Manual ACK: Consumer xác nhận khi xử lý xong
- ✅ Dead Letter Queue: Xử lý messages failed
- ✅ Message TTL: Tự động xóa messages cũ
- ✅ Clustering: Hỗ trợ high availability

**Bảng 2.1 - So sánh các Message Queue**

| Tiêu chí | RabbitMQ | Apache Kafka | Redis |
|----------|----------|--------------|-------|
| **Use Case** | Task queues, RPC | Streaming, logs | Cache, pub/sub |
| **Throughput** | 20k-40k msg/s | 1M+ msg/s | 100k+ msg/s |
| **Latency** | ~1ms | ~10ms | <1ms |
| **Persistence** | Yes | Yes | Optional |
| **Order Guarantee** | Queue-level | Partition-level | No |
| **Message Size** | < 128MB | < 1MB (default) | < 512MB |
| **Learning Curve** | Medium | High | Low |

**Lý do chọn RabbitMQ:**
- ✅ Phù hợp với batch processing
- ✅ Message routing linh hoạt
- ✅ Dễ setup và sử dụng
- ✅ Persistent và reliable

### 2.3.2. MySQL

**Giới thiệu:**
MySQL là hệ quản trị cơ sở dữ liệu quan hệ mã nguồn mở, phổ biến nhất thế giới.

**Lý do chọn MySQL:**
- ✅ ACID compliance: Đảm bảo tính toàn vẹn dữ liệu
- ✅ JSON support: Lưu validation_errors dạng JSON
- ✅ Transactions: Đảm bảo consistency
- ✅ Indexes: Truy vấn nhanh
- ✅ Open source: Free và có community lớn

**Các tính năng sử dụng:**
- **JSON Column**: Lưu `validation_errors` dạng JSON
- **Foreign Keys**: Đảm bảo referential integrity
- **Transactions**: Batch insert/update
- **Views**: Simplify complex queries
- **Stored Procedures**: Business logic trong DB

### 2.3.3. Java

**Giới thiệu:**
Java là ngôn ngữ lập trình hướng đối tượng, platform-independent, được sử dụng rộng rãi trong enterprise applications.

**Các thư viện sử dụng:**

1. **Jackson (JSON Processing)**
```xml
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>2.15.0</version>
</dependency>
```

2. **RabbitMQ Java Client**
```xml
<dependency>
    <groupId>com.rabbitmq</groupId>
    <artifactId>amqp-client</artifactId>
    <version>5.18.0</version>
</dependency>
```

3. **MySQL Connector**
```xml
<dependency>
    <groupId>mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.33</version>
</dependency>
```

### 2.3.4. Flask (Python)

**Giới thiệu:**
Flask là micro web framework cho Python, nhẹ và dễ sử dụng, phù hợp cho việc xây dựng dashboard và REST APIs.

**Các thư viện sử dụng:**
- **Flask**: Web framework
- **mysql-connector-python**: MySQL driver
- **requests**: HTTP client
- **werkzeug**: File upload handling

**Lý do chọn Flask:**
- ✅ Lightweight: Không có boilerplate code
- ✅ Flexible: Dễ customize
- ✅ Python: Dễ xử lý data transformation
- ✅ Large ecosystem: Nhiều extensions

### 2.3.5. Docker & Docker Compose

**Docker:**
Platform để đóng gói ứng dụng và dependencies thành containers.

**Docker Compose:**
Tool để định nghĩa và chạy multi-container applications.

**Lợi ích:**
- ✅ **Consistent environment**: Dev = Prod
- ✅ **Easy deployment**: docker-compose up
- ✅ **Isolation**: Mỗi service trong container riêng
- ✅ **Portability**: Chạy được mọi nơi có Docker

**Bảng 2.2 - Framework và Công nghệ**

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Backend | Java | 11+ | Producer, Consumers, Transform |
| Message Broker | RabbitMQ | 3.x | Message Queue |
| Database | MySQL | 8.0 | Data storage |
| Dashboard | Flask | 2.3+ | Web UI |
| Containerization | Docker | 24.x | Deployment |
| Build Tool | Maven | 3.x | Java build |
| Version Control | Git | 2.x | Source control |

---

## 2.4. KIẾN TRÚC TỔNG QUAN ETL

### 2.4.1. Extract (Trích xuất)

**Mục đích**: Thu thập dữ liệu từ các nguồn khác nhau.

**Trong đồ án:**
- Đọc file CSV từ `resources/data/`
- Parse CSV thành Java Objects (Employee, OrderDetail)
- Basic validation (không null, không empty)
- Serialize thành JSON
- Publish lên RabbitMQ queues

**Code minh họa:**
```java
// Đọc CSV
BufferedReader reader = new BufferedReader(
    new FileReader("employee.csv")
);
String line;
while ((line = reader.readLine()) != null) {
    String[] parts = line.split(",");
    Employee emp = new Employee(
        parts[0], parts[1], parts[2], parts[3]
    );
    
    // Serialize và publish
    String json = objectMapper.writeValueAsString(emp);
    channel.basicPublish("", "employee-queue", 
        MessageProperties.PERSISTENT_TEXT_PLAIN,
        json.getBytes()
    );
}
```

**[Hình 2.1 - Kiến trúc ETL chi tiết - Extract Phase]**

### 2.4.2. Transform (Chuyển đổi)

**Mục đích**: Làm sạch, chuẩn hóa và biến đổi dữ liệu.

**Trong đồ án - Two-Stage Processing:**

**Stage 1: Data Cleansing (Validation)**
- Load validation rules từ database
- Query staging records (validation_errors IS NULL)
- Apply validation rules
- Mark invalid records với JSON errors
- Commit changes

**Stage 2: Data Enrichment (Transformation)**
- Load transformation rules từ database
- Query valid records từ staging
- Apply transformations:
  - Title Case cho tên
  - Lowercase cho email
  - E.164 format cho phone
  - Uppercase cho product ID
- Log changes to audit trail
- Insert to main tables
- Delete from staging

**Code minh họa:**
```java
// Stage 1: Validation
for (Employee emp : stagingRecords) {
    List<RuleResult> results = validator.validateAll(emp);
    if (results.stream().anyMatch(r -> !r.isOk())) {
        String errorsJson = buildErrorsJson(results);
        updateValidationErrors(emp.getId(), errorsJson);
    }
}

// Stage 2: Transformation
for (Employee emp : validRecords) {
    String originalName = emp.getFullName();
    String transformedName = normalizeName(originalName);
    
    if (!originalName.equals(transformedName)) {
        logTransformation(emp.getId(), "full_name", 
            originalName, transformedName);
    }
    
    insertToMain(emp);
    deleteFromStaging(emp.getId());
}
```

**[Hình 2.2 - Two-Stage Transform Architecture]**

### 2.4.3. Load (Tải)

**Mục đích**: Đưa dữ liệu đã transform vào hệ thống đích.

**Trong đồ án:**
- Insert vào main tables (main_employee, main_order_detail)
- Lưu original_data dạng JSON (để có thể rollback)
- Update metrics tables
- Generate audit logs

**Chiến lược Load:**

1. **Batch Insert**: Insert nhiều records cùng lúc
```java
PreparedStatement ps = conn.prepareStatement(
    "INSERT INTO main_employee (...) VALUES (?, ?, ?)"
);
for (Employee emp : batch) {
    ps.setString(1, emp.getEmployeeId());
    ps.addBatch();
}
ps.executeBatch();
```

2. **Upsert**: Update nếu tồn tại, insert nếu chưa có
```sql
INSERT INTO main_employee (...) VALUES (...)
ON DUPLICATE KEY UPDATE 
    full_name = VALUES(full_name),
    email = VALUES(email);
```

3. **Transaction**: Đảm bảo atomicity
```java
conn.setAutoCommit(false);
try {
    // Multiple operations
    conn.commit();
} catch (Exception e) {
    conn.rollback();
}
```

---

## 2.5. MESSAGE QUEUE PATTERN

### 2.5.1. Producer-Consumer Pattern

**Đặc điểm:**
- Producer và Consumer hoạt động độc lập
- Giao tiếp thông qua message queue
- Asynchronous và non-blocking

**Lợi ích:**
- ✅ **Decoupling**: Producer không cần biết Consumer
- ✅ **Scalability**: Thêm consumers để tăng throughput
- ✅ **Load Balancing**: Messages phân phối đều
- ✅ **Fault Tolerance**: Message không mất khi consumer die

**[Hình 2.3 - Producer-Consumer Pattern với RabbitMQ]**

### 2.5.2. Message Acknowledgment

**Manual ACK Pattern:**
```java
channel.basicConsume(queueName, false, // autoAck = false
    (consumerTag, delivery) -> {
        try {
            // Process message
            processMessage(delivery.getBody());
            
            // ACK only after successful processing
            channel.basicAck(
                delivery.getEnvelope().getDeliveryTag(), 
                false
            );
        } catch (Exception e) {
            // NACK if processing failed
            channel.basicNack(
                delivery.getEnvelope().getDeliveryTag(), 
                false, 
                true // requeue
            );
        }
    }
);
```

**Ý nghĩa:**
- Message chỉ bị xóa khỏi queue khi consumer ACK
- Nếu consumer die trước khi ACK, message tự động requeue
- Đảm bảo không mất message

---

## 2.6. TỔNG KẾT CHƯƠNG

Chương 2 đã trình bày các cơ sở lý thuyết và công nghệ sử dụng trong đồ án:

- **Regular Expression**: Validation email, phone, product ID
- **Design Patterns**: Strategy, Factory, DAO, Observer patterns
- **Technologies**: RabbitMQ, MySQL, Java, Flask, Docker
- **ETL Architecture**: Extract, Transform (2-stage), Load
- **Message Queue Pattern**: Producer-Consumer, Manual ACK

Các kiến thức này là nền tảng để hiểu và triển khai hệ thống trong các chương tiếp theo.
