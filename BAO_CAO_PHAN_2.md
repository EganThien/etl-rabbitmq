# BÁO CÁO ĐỒ ÁN - PHẦN 2

# CHƯƠNG 2: NGHIÊN CỨU VỀ BIỂU THỨC CHÍNH QUY, DESIGN PATTERNS, FRAMEWORK

## 2.1. BIỂU THỨC CHÍNH QUY (REGULAR EXPRESSIONS)

### 2.1.1. Giới thiệu về Regex

Regular Expression (Regex) là một chuỗi ký tự đặc biệt dùng để mô tả pattern tìm kiếm trong text. Trong đồ án, regex được sử dụng để validate format của email và phone number.

### 2.1.2. Email Validation

**Pattern sử dụng:**
```
^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$
```

**Giải thích chi tiết:**

| Thành phần | Ý nghĩa |
|------------|---------|
| `^` | Bắt đầu chuỗi |
| `[A-Za-z0-9+_.-]+` | Local part: chữ cái, số, +, _, ., - (ít nhất 1 ký tự) |
| `@` | Ký tự @ bắt buộc |
| `[A-Za-z0-9.-]+` | Domain: chữ cái, số, ., - (ít nhất 1 ký tự) |
| `\.` | Dấu chấm (escaped) |
| `[A-Za-z]{2,}` | TLD: ít nhất 2 chữ cái (com, vn, org...) |
| `$` | Kết thúc chuỗi |

**Ví dụ:**
- ✅ Valid: `john.doe@company.com`, `user_123@test.vn`
- ❌ Invalid: `invalid@`, `@domain.com`, `user@domain`

**Implementation trong đồ án:**
```java
// Sử dụng Apache Commons Validator
EmailValidator validator = EmailValidator.getInstance();
boolean isValid = validator.isValid(email);
```

### 2.1.3. Phone Number Validation

**Pattern sử dụng (E.164 format):**
```
^\+?[1-9]\d{1,14}$
```

**Giải thích:**

| Thành phần | Ý nghĩa |
|------------|---------|
| `^` | Bắt đầu chuỗi |
| `\+?` | Dấu + tùy chọn (country code) |
| `[1-9]` | Số đầu tiên từ 1-9 (không phải 0) |
| `\d{1,14}` | 1-14 chữ số tiếp theo |
| `$` | Kết thúc chuỗi |

**Ví dụ:**
- ✅ Valid: `+84901234567`, `84912345678`, `0901234567`
- ❌ Invalid: `123`, `abc123`, `+1234567890123456` (quá dài)

**Implementation:**
```java
public class PhoneNumberRule implements ValidationRule {
    private static final String PHONE_PATTERN = "^\\+?[1-9]\\d{1,14}$";
    private static final Pattern pattern = Pattern.compile(PHONE_PATTERN);
    
    @Override
    public boolean test(String value) {
        return pattern.matcher(value).matches();
    }
}
```

### 2.1.4. Ứng dụng Regex trong đồ án

1. **Email validation** - Đảm bảo định dạng email hợp lệ
2. **Phone validation** - Kiểm tra số điện thoại theo chuẩn quốc tế
3. **Data cleaning** - Loại bỏ ký tự đặc biệt không mong muốn

## 2.2. DESIGN PATTERNS

### 2.2.1. Strategy Pattern

**Định nghĩa:**  
Strategy là behavioral design pattern cho phép định nghĩa một họ các thuật toán, đóng gói từng thuật toán và làm chúng có thể thay thế lẫn nhau.

**Ứng dụng trong đồ án:**

```java
// Interface chung cho tất cả validation rules
public interface ValidationRule {
    boolean test(String value);
    String getErrorMessage();
}

// Concrete strategies
public class EmailRule implements ValidationRule {
    @Override
    public boolean test(String value) {
        return EmailValidator.getInstance().isValid(value);
    }
    
    @Override
    public String getErrorMessage() {
        return "Invalid email format";
    }
}

public class PhoneNumberRule implements ValidationRule {
    @Override
    public boolean test(String value) {
        return value.matches("^\\+?[1-9]\\d{1,14}$");
    }
    
    @Override
    public String getErrorMessage() {
        return "Invalid phone number format";
    }
}

public class QuantityRule implements ValidationRule {
    @Override
    public boolean test(String value) {
        try {
            return Integer.parseInt(value) > 0;
        } catch (NumberFormatException e) {
            return false;
        }
    }
    
    @Override
    public String getErrorMessage() {
        return "Quantity must be greater than 0";
    }
}
```

**Lợi ích:**
- ✓ Dễ dàng thêm rule mới mà không sửa code cũ (Open/Closed Principle)
- ✓ Mỗi rule độc lập, dễ test
- ✓ Có thể combine nhiều rules cho 1 field

### 2.2.2. Builder Pattern

**Định nghĩa:**  
Builder pattern cho phép xây dựng các object phức tạp từng bước một.

**Ứng dụng:**

```java
public class ValidationError {
    private String field;
    private String message;
    private String value;
    
    private ValidationError(Builder builder) {
        this.field = builder.field;
        this.message = builder.message;
        this.value = builder.value;
    }
    
    public static class Builder {
        private String field;
        private String message;
        private String value;
        
        public Builder field(String field) {
            this.field = field;
            return this;
        }
        
        public Builder message(String message) {
            this.message = message;
            return this;
        }
        
        public Builder value(String value) {
            this.value = value;
            return this;
        }
        
        public ValidationError build() {
            return new ValidationError(this);
        }
    }
}

// Sử dụng
ValidationError error = new ValidationError.Builder()
    .field("email")
    .message("Invalid email format")
    .value("invalid@email")
    .build();
```

**Lợi ích:**
- ✓ Code dễ đọc, self-documenting
- ✓ Tránh constructor với nhiều parameters
- ✓ Immutable objects

### 2.2.3. Factory Pattern

**Ứng dụng trong Validator:**

```java
public class ValidatorFactory {
    public static RecordValidator<Employee> createEmployeeValidator() {
        RecordValidator<Employee> validator = new RecordValidator<>();
        
        validator.addRule("email", new EmailRule());
        validator.addRule("phone", new PhoneNumberRule());
        validator.addRule("full_name", new NotEmptyRule());
        
        return validator;
    }
    
    public static RecordValidator<OrderDetail> createOrderValidator() {
        RecordValidator<OrderDetail> validator = new RecordValidator<>();
        
        validator.addRule("product_id", new NotEmptyRule());
        validator.addRule("quantity", new QuantityRule());
        
        return validator;
    }
}
```

**Lợi ích:**
- ✓ Centralized configuration
- ✓ Dễ maintain khi thay đổi rules
- ✓ Reusable validators

### 2.2.4. Repository Pattern

**Ứng dụng trong Data Access:**

```java
public interface StagingDao {
    List<Employee> getAllEmployees();
    void insertEmployee(Employee employee);
    void updateValidationErrors(int id, List<ValidationError> errors);
}

public class StagingDaoImpl implements StagingDao {
    private Connection connection;
    
    @Override
    public List<Employee> getAllEmployees() {
        // Implementation
    }
    
    @Override
    public void insertEmployee(Employee employee) {
        // Implementation
    }
    
    @Override
    public void updateValidationErrors(int id, List<ValidationError> errors) {
        // Implementation
    }
}
```

**Lợi ích:**
- ✓ Tách biệt business logic và data access
- ✓ Dễ test với mock objects
- ✓ Dễ thay đổi database implementation

## 2.3. SPRING FRAMEWORK

### 2.3.1. Giới thiệu Spring Framework

Spring Framework là một framework mạnh mẽ cho Java enterprise applications. Tuy đồ án không sử dụng toàn bộ Spring, nhưng áp dụng các nguyên tắc của Spring.

### 2.3.2. Dependency Injection (DI)

**Khái niệm:**  
DI là kỹ thuật giúp giảm sự phụ thuộc giữa các components bằng cách inject dependencies từ bên ngoài.

**Ví dụ trong đồ án:**

```java
// Thay vì tạo dependency trong class
public class TransformLoad {
    private StagingDao stagingDao = new StagingDaoImpl(); // Tight coupling
    private MainDao mainDao = new MainDaoImpl();
}

// Sử dụng constructor injection
public class TransformLoad {
    private final StagingDao stagingDao;
    private final MainDao mainDao;
    
    public TransformLoad(StagingDao stagingDao, MainDao mainDao) {
        this.stagingDao = stagingDao;
        this.mainDao = mainDao;
    }
}

// Khởi tạo
StagingDao stagingDao = new StagingDaoImpl(connection);
MainDao mainDao = new MainDaoImpl(connection);
TransformLoad transform = new TransformLoad(stagingDao, mainDao);
```

**Lợi ích:**
- ✓ Loose coupling
- ✓ Dễ test (inject mock objects)
- ✓ Dễ thay đổi implementation

### 2.3.3. Inversion of Control (IoC)

**Nguyên tắc:**  
Framework điều khiển flow của chương trình, không phải application code.

**Áp dụng:**
- Message queue (RabbitMQ) điều khiển khi nào consumer nhận message
- Event-driven architecture
- Callback patterns

## 2.4. RABBITMQ MESSAGE BROKER

### 2.4.1. Giới thiệu RabbitMQ

RabbitMQ là message broker implement AMQP (Advanced Message Queuing Protocol). Nó cho phép các ứng dụng giao tiếp với nhau thông qua message queue.

### 2.4.2. Các khái niệm cơ bản

**Producer:**
- Ứng dụng gửi messages
- Trong đồ án: CSV Reader đọc file và gửi messages

**Queue:**
- Nơi lưu trữ messages
- Trong đồ án: `employee.queue`, `order.queue`

**Consumer:**
- Ứng dụng nhận và xử lý messages
- Trong đồ án: Employee Consumer, Order Consumer

**Exchange:**
- Định tuyến messages đến queues
- Types: direct, topic, fanout, headers

**Binding:**
- Liên kết giữa exchange và queue

### 2.4.3. Workflow trong đồ án

```
Producer → Exchange (direct) → Routing Key → Queue → Consumer
```

**Chi tiết:**

1. **Producer** đọc CSV và tạo message:
```java
String message = objectMapper.writeValueAsString(employee);
channel.basicPublish("", "employee.queue", null, message.getBytes());
```

2. **Queue** lưu trữ message tạm thời

3. **Consumer** nhận và xử lý:
```java
DeliverCallback deliverCallback = (consumerTag, delivery) -> {
    String message = new String(delivery.getBody(), "UTF-8");
    Employee employee = objectMapper.readValue(message, Employee.class);
    stagingDao.insert(employee);
};
channel.basicConsume("employee.queue", true, deliverCallback, consumerTag -> {});
```

### 2.4.4. Lợi ích của RabbitMQ

1. **Asynchronous Processing:**
   - Producer không cần đợi Consumer xử lý
   - Tăng throughput của hệ thống

2. **Decoupling:**
   - Producer và Consumer độc lập
   - Có thể deploy, scale riêng biệt

3. **Reliability:**
   - Message persistence
   - Acknowledgment mechanism
   - Retry logic

4. **Scalability:**
   - Có thể chạy nhiều consumers song song
   - Load balancing tự động

5. **Flexibility:**
   - Dễ thêm consumers mới
   - Dễ thay đổi routing logic

---

# KẾT LUẬN CHƯƠNG 2

Chương 2 đã trình bày chi tiết về các công nghệ và patterns được sử dụng trong đồ án:

1. **Regular Expressions** - Validate email và phone number
2. **Design Patterns** - Strategy, Builder, Factory, Repository
3. **Spring Framework principles** - DI, IoC
4. **RabbitMQ** - Message broker cho asynchronous processing

Các công nghệ này kết hợp tạo nên một hệ thống ETL robust, scalable và maintainable. Chương tiếp theo sẽ trình bày chi tiết về phân tích và thiết kế hệ thống.

---

**Trang:** 9-18  
**Phần:** CHƯƠNG 2 - NGHIÊN CỨU VỀ BIỂU THỨC CHÍNH QUY, DESIGN PATTERNS, FRAMEWORK
