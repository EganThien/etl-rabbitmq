# BÁO CÁO ĐỒ ÁN - PHẦN 3

# CHƯƠNG 3: PHÂN TÍCH VÀ THIẾT KẾ

## 3.1. PHÂN TÍCH YÊU CẦU

### 3.1.1. Yêu cầu chức năng (Functional Requirements)

#### FR1: Upload và xử lý file CSV

**Mô tả:**  
Hệ thống phải cho phép user upload file CSV chứa dữ liệu employees và orders.

**Chi tiết:**
- Upload qua web interface
- Support file encoding UTF-8
- Validate file format trước khi xử lý
- Hiển thị progress và kết quả

**Acceptance Criteria:**
- ✓ File CSV được parse thành công
- ✓ Mỗi row được gửi vào RabbitMQ
- ✓ Hiển thị số records đã xử lý

#### FR2: Extract dữ liệu từ CSV

**Mô tả:**  
Producer đọc file CSV và gửi từng record vào RabbitMQ queue.

**Chi tiết:**
- Parse CSV với OpenCSV library
- Convert mỗi row thành JSON
- Gửi vào queue tương ứng (employee.queue, order.queue)

**Input:**
```csv
employee_id,full_name,email,phone
E001,John Doe,john@example.com,+84901234567
```

**Output (JSON message):**
```json
{
  "employee_id": "E001",
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "+84901234567"
}
```

#### FR3: Consumer nhận và lưu vào Staging

**Mô tả:**  
Consumer nhận messages từ RabbitMQ và insert vào staging tables.

**Chi tiết:**
- Subscribe vào RabbitMQ queue
- Parse JSON message
- Insert vào staging_employee hoặc staging_order_detail
- Acknowledge message sau khi xử lý thành công

**Database Schema - Staging Tables:**

```sql
CREATE TABLE staging_employee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(50),
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_payload TEXT,
    validation_errors JSON
);

CREATE TABLE staging_order_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(50),
    product_id VARCHAR(50),
    quantity INT,
    price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_payload TEXT,
    validation_errors JSON
);
```

#### FR4: Transform và Validate dữ liệu

**Mô tả:**  
Transform process đọc từ staging, validate theo business rules, và chuyển dữ liệu hợp lệ sang main tables.

**Validation Rules:**

**Employee:**
1. `email` - Phải đúng format email
2. `phone` - Phải đúng format E.164
3. `full_name` - Không được rỗng

**Order:**
1. `product_id` - Không được rỗng
2. `quantity` - Phải > 0
3. `price` - Phải >= 0

**Flow:**
```
1. Read all records from staging
2. For each record:
   a. Apply validation rules
   b. If valid → Insert to main table
   c. If invalid → Update validation_errors in staging
```

**Validation Errors Format:**
```json
[
  {
    "field": "email",
    "message": "Invalid email format"
  },
  {
    "field": "phone",
    "message": "Invalid phone number format"
  }
]
```

#### FR5: Load dữ liệu vào Main Database

**Mô tả:**  
Dữ liệu đã validate thành công được chuyển vào main tables.

**Database Schema - Main Tables:**

```sql
CREATE TABLE main_employee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE,
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE main_order_detail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(50),
    product_id VARCHAR(50),
    quantity INT,
    price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Business Logic:**
- Chỉ insert records đã pass validation
- Không có validation_errors
- Có thể duplicate check (optional)

#### FR6: Dashboard hiển thị kết quả

**Mô tả:**  
Web dashboard hiển thị tổng quan và chi tiết về dữ liệu đã xử lý.

**Features:**

1. **Summary Cards:**
   - Total Records - Tổng số records trong hệ thống
   - Staging - Records đang chờ xử lý
   - Main DB - Records đã pass validation
   - Passed - Chi tiết records hợp lệ
   - Errors - Chi tiết records có lỗi

2. **Passed Records View:**
   - Click vào thẻ xanh "Passed"
   - Hiển thị 2 tables: Valid Employees, Valid Orders
   - Show: ID, Name, Email, Phone / Order ID, Product, Qty, Price

3. **Error Records View:**
   - Click vào thẻ đỏ "Errors"
   - Hiển thị records có lỗi với chi tiết validation errors
   - Group by: Employee Errors, Order Errors
   - Show: All fields + validation error messages

4. **Main Data View:**
   - Tab riêng cho Employees và Orders
   - Hiển thị dữ liệu từ main tables
   - Pagination

5. **Staging Errors View:**
   - Tab riêng cho lỗi validation
   - Filter by entity (employee/order)
   - Chi tiết từng lỗi

### 3.1.2. Yêu cầu phi chức năng (Non-Functional Requirements)

#### NFR1: Performance

**Throughput:**
- Xử lý tối thiểu 100 records/second
- Upload file < 10MB trong vòng 5 giây

**Response Time:**
- Dashboard load < 2 giây
- API response < 500ms

**Scalability:**
- Support multiple consumers
- Có thể scale horizontal

#### NFR2: Reliability

**Data Integrity:**
- Không mất dữ liệu trong quá trình xử lý
- Transaction support cho database operations

**Error Handling:**
- Graceful degradation khi có lỗi
- Retry mechanism cho failed operations
- Log errors đầy đủ

**Message Queue:**
- Message persistence
- Acknowledgment mechanism

#### NFR3: Maintainability

**Code Quality:**
- Clean code principles
- SOLID principles
- Design patterns
- Comprehensive comments

**Testing:**
- Unit test coverage > 70%
- Integration tests
- E2E tests

**Documentation:**
- README với setup instructions
- API documentation
- Architecture diagrams

#### NFR4: Usability

**Dashboard:**
- Intuitive UI/UX
- Responsive design
- Clear error messages
- Easy navigation

**CSV Upload:**
- Drag-and-drop support
- File rename capability
- Progress indicator
- Clear instructions

#### NFR5: Security

**Data:**
- Input validation
- SQL injection prevention
- XSS prevention

**Access:**
- Basic authentication (if needed)
- CORS configuration

## 3.2. THIẾT KẾ KIẾN TRÚC HỆ THỐNG

### 3.2.1. Kiến trúc tổng quan

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│  ┌────────────────┐         ┌───────────────────────────┐  │
│  │  CSV Upload    │         │  Dashboard (Flask/Python) │  │
│  │  Interface     │         │  - Summary Cards          │  │
│  └────────┬───────┘         │  - Data Viewer            │  │
│           │                 │  - Error Viewer           │  │
│           │                 └───────────┬───────────────┘  │
└───────────┼─────────────────────────────┼──────────────────┘
            │                             │
            ▼                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER (Java)                   │
│  ┌──────────────┐     ┌─────────────┐    ┌──────────────┐ │
│  │  Producer    │────▶│  RabbitMQ   │───▶│  Consumer    │ │
│  │  (CSV Read)  │     │  - employee │    │  - Employee  │ │
│  │              │     │    .queue   │    │  - Order     │ │
│  └──────────────┘     │  - order    │    └──────┬───────┘ │
│                       │    .queue   │           │         │
│                       └─────────────┘           │         │
│                                                 ▼         │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              Transform & Validate                     │ │
│  │  - RecordValidator                                    │ │
│  │  - ValidationRules (Email, Phone, Quantity)          │ │
│  │  - Error Builder                                      │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER (MySQL)                       │
│  ┌──────────────────────┐       ┌─────────────────────────┐│
│  │  Staging Tables      │       │   Main Tables           ││
│  │  - staging_employee  │       │   - main_employee       ││
│  │  - staging_order_    │       │   - main_order_detail   ││
│  │    detail            │       │                         ││
│  │  (All data +errors)  │       │   (Valid data only)     ││
│  └──────────────────────┘       └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 3.2.2. Component Diagram

```
┌──────────────────┐
│   CSV Files      │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────┐
│              Producer Component                  │
│  ┌────────────────┐      ┌──────────────────┐  │
│  │  CSV Parser    │──────│  Message Builder │  │
│  │  (OpenCSV)     │      │  (Jackson)       │  │
│  └────────────────┘      └──────────────────┘  │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
         ┌──────────────────┐
         │   RabbitMQ       │
         │   Message Queue  │
         └────────┬─────────┘
                  │
      ┌───────────┴───────────┐
      ▼                       ▼
┌─────────────────┐   ┌─────────────────┐
│Employee Consumer│   │ Order Consumer  │
│  - Listen queue │   │  - Listen queue │
│  - Deserialize  │   │  - Deserialize  │
│  - Insert DB    │   │  - Insert DB    │
└────────┬────────┘   └────────┬────────┘
         │                     │
         └─────────┬───────────┘
                   ▼
         ┌──────────────────┐
         │ Staging Database │
         └────────┬─────────┘
                  │
                  ▼
     ┌─────────────────────────────┐
     │    Transform Component      │
     │  ┌────────────────────────┐ │
     │  │  RecordValidator       │ │
     │  │  - EmailRule           │ │
     │  │  - PhoneNumberRule     │ │
     │  │  - QuantityRule        │ │
     │  │  - NotEmptyRule        │ │
     │  └────────────────────────┘ │
     └──────────┬──────────────────┘
                │
      ┌─────────┴─────────┐
      ▼                   ▼
┌──────────────┐   ┌──────────────────┐
│ Main Database│   │ Update Staging   │
│ (Valid data) │   │ (Error details)  │
└──────────────┘   └──────────────────┘
```

### 3.2.3. Data Source (Nguồn dữ liệu)

**CSV Files:**

1. **employee_valid.csv:**
```csv
employee_id,full_name,email,phone
E001,Alice Smith,alice@example.com,+84901234567
E002,John Doe,john.doe@company.com,+84912345678
...
```

2. **employee_invalid.csv:**
```csv
employee_id,full_name,email,phone
E101,Bad Email,bademail@,+84901234567
E102,Bad Phone,user@test.com,123
...
```

3. **order_valid.csv:**
```csv
order_id,product_id,product_name,quantity,price
O2001,P201,Laptop,5,1299.99
O2002,P202,iPhone,3,999.00
...
```

4. **order_invalid.csv:**
```csv
order_id,product_id,product_name,quantity,price
O3001,,Laptop,5,1299.99
O3002,P202,iPhone,0,999.00
...
```

### 3.2.4. Data Quality (Data Lake)

**Data Quality Framework:**

```
┌───────────────────────────────────────────────────────┐
│              Data Quality Dimensions                  │
├───────────────────────────────────────────────────────┤
│  1. Completeness - Có đủ dữ liệu bắt buộc không?    │
│  2. Accuracy - Dữ liệu có chính xác không?           │
│  3. Consistency - Dữ liệu có nhất quán không?        │
│  4. Validity - Dữ liệu có hợp lệ theo rules không?   │
└───────────────────────────────────────────────────────┘
```

**Validation Constraints:**

| Field | Rule | Type | Message |
|-------|------|------|---------|
| email | Email format | Format | "Invalid email format" |
| phone | E.164 format | Format | "Invalid phone number" |
| full_name | Not empty | Completeness | "Full name cannot be empty" |
| product_id | Not empty | Completeness | "Product ID cannot be empty" |
| quantity | > 0 | Business Rule | "Quantity must be > 0" |
| price | >= 0 | Business Rule | "Price must be >= 0" |

### 3.2.5. Thiết kế các bước để validate

**Step 1: Load Data from Staging**
```java
List<Employee> employees = stagingDao.getAllEmployees();
```

**Step 2: Create Validator with Rules**
```java
RecordValidator<Employee> validator = new RecordValidator<>();
validator.addRule("email", new EmailRule());
validator.addRule("phone", new PhoneNumberRule());
validator.addRule("full_name", new NotEmptyRule());
```

**Step 3: Validate Each Record**
```java
for (Employee emp : employees) {
    List<ValidationError> errors = validator.validate(emp);
    
    if (errors.isEmpty()) {
        // Valid → proceed to Step 4
    } else {
        // Invalid → proceed to Step 5
    }
}
```

**Step 4: Insert Valid Records to Main**
```java
if (errors.isEmpty()) {
    mainDao.insertEmployee(emp);
    System.out.println("✓ Transferred: " + emp.getEmployeeId());
}
```

**Step 5: Update Staging with Errors**
```java
else {
    String errorsJson = objectMapper.writeValueAsString(errors);
    stagingDao.updateValidationErrors(emp.getId(), errorsJson);
    System.out.println("✗ Validation failed: " + emp.getEmployeeId());
}
```

**Constraint Implementation:**

```java
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

public class QuantityRule implements ValidationRule {
    @Override
    public boolean test(String value) {
        try {
            int qty = Integer.parseInt(value);
            return qty > 0;  // Constraint: quantity > 0
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

---

# KẾT LUẬN CHƯƠNG 3

Chương 3 đã trình bày chi tiết về phân tích và thiết kế hệ thống ETL:

1. **Phân tích yêu cầu:**
   - Functional Requirements: 6 chức năng chính
   - Non-Functional Requirements: Performance, Reliability, Maintainability, Usability, Security

2. **Thiết kế kiến trúc:**
   - 3-tier architecture: UI, Application, Data
   - Component diagram với Producer, RabbitMQ, Consumer, Transform
   - Data flow từ CSV → Queue → Staging → Validation → Main DB

3. **Data Quality:**
   - 4 dimensions: Completeness, Accuracy, Consistency, Validity
   - Validation constraints với rules cụ thể
   - 5 bước validate: Load → Create Validator → Validate → Insert/Update

Thiết kế này đảm bảo hệ thống có tính mở rộng, dễ maintain và đảm bảo data quality. Chương tiếp theo sẽ trình bày chi tiết về triển khai và kiểm thử hệ thống.

---

**Trang:** 19-30  
**Phần:** CHƯƠNG 3 - PHÂN TÍCH VÀ THIẾT KẾ
