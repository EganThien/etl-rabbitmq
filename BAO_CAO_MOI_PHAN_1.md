# BÁO CÁO ĐỒ ÁN

---

## **HỆ THỐNG ETL VỚI RABBITMQ VÀ MYSQL**
### **ỨNG DỤNG TWO-STAGE VALIDATION VÀ DATA QUALITY MANAGEMENT**

---

**Sinh viên thực hiện:** [Tên sinh viên]  
**MSSV:** [Mã số sinh viên]  
**Lớp:** [Tên lớp]  
**Khoa:** Công nghệ Thông tin

**Giảng viên hướng dẫn:** [Tên giảng viên]

---

**TP. Hồ Chí Minh, tháng 12 năm 2025**

---
---

# MỤC LỤC

**CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI**
- 1.1. Giới thiệu đề tài
- 1.2. Mục tiêu đồ án
- 1.3. Phạm vi nghiên cứu
- 1.4. Ý nghĩa của đề tài

**CHƯƠNG 2: CƠ SỞ LÝ THUYẾT**
- 2.1. Tổng quan về ETL
- 2.2. Message Queue và RabbitMQ
- 2.3. Data Quality và Validation
- 2.4. Design Patterns trong ETL

**CHƯƠNG 3: PHÂN TÍCH VÀ THIẾT KẾ**
- 3.1. Phân tích yêu cầu
- 3.2. Thiết kế cơ sở dữ liệu
- 3.3. Thiết kế ràng buộc và validate
- 3.4. Thiết kế hệ thống ETL

**CHƯƠNG 4: TRIỂN KHAI HỆ THỐNG**
- 4.1. Kiến trúc tổng thể
- 4.2. Các lớp code chính
- 4.3. Giao diện hệ thống
- 4.4. Kết quả đạt được

**KẾT LUẬN**

---
---

# CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI

## 1.1. Giới thiệu đề tài

Trong thời đại chuyển đổi số, dữ liệu là tài sản quan trọng nhất của doanh nghiệp. Tuy nhiên, dữ liệu thường đến từ nhiều nguồn khác nhau với chất lượng không đồng đều. Việc tích hợp, làm sạch và chuẩn hóa dữ liệu trở thành một thách thức lớn.

**ETL (Extract, Transform, Load)** là quy trình xử lý dữ liệu gồm ba giai đoạn:
1. **Extract (Trích xuất)**: Thu thập dữ liệu từ các nguồn
2. **Transform (Chuyển đổi)**: Làm sạch, chuẩn hóa dữ liệu
3. **Load (Tải)**: Đưa dữ liệu vào hệ thống đích

Đồ án này xây dựng một hệ thống ETL hiện đại sử dụng:
- **RabbitMQ Message Queue**: Xử lý bất đồng bộ, tách biệt các thành phần
- **Two-Stage Validation**: Kiểm tra dữ liệu 2 lần (Consumer + Transform)
- **Rules Engine**: Quản lý validation rules linh hoạt trong database
- **Audit Trail**: Theo dõi mọi thay đổi dữ liệu

Hệ thống xử lý dữ liệu nhân viên và đơn hàng từ file CSV, validate theo các quy tắc được cấu hình, chuẩn hóa dữ liệu và lưu vào database MySQL.

## 1.2. Mục tiêu đồ án

### 1.2.1. Mục tiêu chung

Xây dựng hệ thống ETL hoàn chỉnh với kiến trúc Message Queue, có khả năng:
- Xử lý dữ liệu từ file CSV tự động
- Validate và phát hiện lỗi dữ liệu theo rules có thể cấu hình
- Transform và chuẩn hóa dữ liệu theo chuẩn
- Đảm bảo không mất dữ liệu (fault tolerance)
- Có khả năng mở rộng (scalability)

### 1.2.2. Mục tiêu cụ thể

**Về kiến trúc:**
- Thiết kế kiến trúc phân tán với Message Queue (RabbitMQ)
- Áp dụng Design Patterns (Producer-Consumer, Strategy, DAO)
- Đảm bảo loose coupling giữa các components

**Về xử lý dữ liệu:**
- Implement Two-Stage Transform (Data Cleansing + Data Enrichment)
- Xây dựng Rules Engine linh hoạt, lưu rules trong database
- Áp dụng Regular Expression để validate
- Chuẩn hóa dữ liệu (E.164 cho phone, lowercase cho email, Title Case cho tên)

**Về chất lượng dữ liệu:**
- Phát hiện và lưu chi tiết các lỗi validation
- Cho phép sửa lỗi và re-validate
- Ghi audit trail đầy đủ (field-level changes)
- Tính toán metrics về data quality

**Về giao diện:**
- Dashboard để monitor dữ liệu
- Upload CSV dễ dàng
- Xem và quản lý validation errors
- Xem lịch sử transform

## 1.3. Phạm vi nghiên cứu

### 1.3.1. Phạm vi nghiệp vụ

Hệ thống tập trung xử lý **dữ liệu nhân viên (Employee)** và **đơn hàng (Order)**:

**Input:**
- File CSV chứa thông tin nhân viên: Employee ID, Full Name, Email, Phone
- File CSV chứa thông tin đơn hàng: Order ID, Product ID, Quantity, Price

**Processing:**
- **Validation**: Email format, Phone format (Vietnam), Quantity > 0, Price > 0
- **Transformation**: 
  - Tên: NGUYEN VAN A → Nguyễn Văn A (Title Case)
  - Email: ADMIN@MAIL.COM → admin@mail.com (lowercase)
  - Phone: 0901234567 → +84901234567 (E.164 format)
- **Error Handling**: Lưu errors dạng JSON, cho phép re-validate

**Output:**
- Dữ liệu đã clean trong main tables
- Audit trail về các thay đổi
- Metrics về data quality

### 1.3.2. Phạm vi kỹ thuật

**Technologies:**
- **Backend**: Java 11, Maven
- **Message Queue**: RabbitMQ 3.x
- **Database**: MySQL 8.0
- **Frontend**: Flask (Python), Bootstrap
- **DevOps**: Docker, Docker Compose

**Không bao gồm:**
- Authentication/Authorization phức tạp
- Real-time streaming (chỉ batch processing)
- Machine Learning cho data prediction
- Advanced scheduling (Airflow/Luigi)

## 1.4. Ý nghĩa của đề tài

### 1.4.1. Ý nghĩa thực tiễn

Hệ thống giải quyết bài toán thực tế trong doanh nghiệp:
- **Data Integration**: Tích hợp dữ liệu từ nhiều nguồn CSV vào database tập trung
- **Data Quality**: Tự động phát hiện và xử lý dữ liệu lỗi
- **Data Migration**: Di chuyển dữ liệu giữa các hệ thống với validation
- **Audit & Compliance**: Theo dõi lịch sử thay đổi dữ liệu

### 1.4.2. Ý nghĩa học thuật

Đề tài giúp sinh viên:
- Hiểu sâu về kiến trúc hệ thống phân tán
- Áp dụng Design Patterns vào bài toán thực tế
- Làm việc với Message Queue (RabbitMQ)
- Xử lý Data Quality và Validation
- Full-stack development (Java Backend + Python Frontend + MySQL)

### 1.4.3. Kiến trúc có thể tái sử dụng

Các thành phần có thể apply cho nhiều use cases:
- **Rules Engine**: Áp dụng cho bất kỳ entity type nào
- **Two-Stage Transform**: Pattern cho mọi data pipeline
- **Message Queue architecture**: Scale cho high-volume processing
- **Audit Trail**: Track changes trong bất kỳ system nào

---
---

# CHƯƠNG 2: CƠ SỞ LÝ THUYẾT

## 2.1. Tổng quan về ETL

### 2.1.1. Khái niệm ETL

**ETL (Extract, Transform, Load)** là quy trình xử lý dữ liệu gồm ba giai đoạn:

**1. Extract (Trích xuất)**
- Thu thập dữ liệu từ các nguồn khác nhau: CSV, Database, API, Excel
- Đọc và parse dữ liệu
- Trong đồ án: Đọc file CSV, parse thành Java Objects

**2. Transform (Chuyển đổi)**
- **Data Cleansing**: Làm sạch, loại bỏ dữ liệu lỗi
- **Data Validation**: Kiểm tra tính hợp lệ
- **Data Normalization**: Chuẩn hóa format (email lowercase, phone E.164)
- **Data Enrichment**: Bổ sung thông tin
- Trong đồ án: Two-Stage Transform (Validation + Normalization)

**3. Load (Tải)**
- Đưa dữ liệu đã xử lý vào hệ thống đích
- Insert/Update vào database
- Trong đồ án: Load vào MySQL main tables

### 2.1.2. ETL truyền thống vs. Hiện đại

**ETL Truyền thống:**
```
CSV → ETL Tool (Sequential) → Database
```
- Xử lý tuần tự, khó scale
- Tight coupling giữa các thành phần
- Khó maintain và extend

**ETL Hiện đại (đồ án này):**
```
CSV → Producer → RabbitMQ → Consumer → Staging → Transform → Main DB
```
- Xử lý bất đồng bộ
- Loose coupling
- Dễ scale (thêm consumers)
- Fault tolerant

### 2.1.3. Vai trò của ETL trong Data Integration

**Trong doanh nghiệp:**
- Tích hợp dữ liệu từ nhiều hệ thống (ERP, CRM, HR)
- Xây dựng Data Warehouse cho phân tích
- Master Data Management

**Trong đồ án:**
- Tích hợp dữ liệu nhân viên từ file CSV vào database
- Đảm bảo data quality trước khi load
- Theo dõi lịch sử thay đổi

## 2.2. Message Queue và RabbitMQ

### 2.2.1. Khái niệm Message Queue

**Message Queue** là hệ thống trung gian cho phép các ứng dụng giao tiếp thông qua messages.

**Thành phần:**
- **Producer**: Ứng dụng gửi message
- **Queue**: Bộ đệm lưu trữ messages
- **Consumer**: Ứng dụng nhận và xử lý message

**Lợi ích:**
- **Asynchronous**: Producer không phải đợi Consumer xử lý
- **Decoupling**: Producer và Consumer độc lập, không cần biết nhau
- **Load Balancing**: Nhiều Consumers xử lý song song
- **Fault Tolerance**: Message không mất khi Consumer die

### 2.2.2. RabbitMQ

**Giới thiệu:**
RabbitMQ là message broker mã nguồn mở, implement giao thức AMQP (Advanced Message Queuing Protocol).

**Đặc điểm:**
- **Durable Queues**: Queue không mất khi broker restart
- **Persistent Messages**: Message được lưu trên disk
- **Manual ACK**: Consumer xác nhận khi xử lý xong message
- **Dead Letter Queue**: Xử lý messages failed
- **Management UI**: Giám sát queues, messages, connections

**So sánh với các Message Queue khác:**

| Tiêu chí | RabbitMQ | Kafka | Redis |
|----------|----------|-------|-------|
| Use Case | Task queues | Streaming | Cache |
| Throughput | 20k-40k msg/s | 1M+ msg/s | 100k+ |
| Latency | ~1ms | ~10ms | <1ms |
| Persistence | Yes | Yes | Optional |
| Learning Curve | Medium | High | Low |

**Lý do chọn RabbitMQ:**
- Phù hợp với batch processing
- Message routing linh hoạt
- Dễ setup và sử dụng
- Persistent và reliable

### 2.2.3. Producer-Consumer Pattern trong đồ án

**Producer (CSVProducer):**
- Đọc file CSV (employee.csv, order.csv)
- Parse CSV → Java Objects
- Serialize thành JSON
- Publish lên RabbitMQ queues

**Queue:**
- `employee-queue`: Chứa employee messages
- `order-queue`: Chứa order messages
- Durable, persistent

**Consumer (EmployeeConsumer, OrderConsumer):**
- Subscribe queue
- Nhận message
- Validate record
- Insert vào staging tables
- ACK message

**Message Format:**
```json
{
  "employeeId": "NV001",
  "fullName": "Nguyễn Văn A",
  "email": "admin@example.com",
  "phone": "0901234567"
}
```

## 2.3. Data Quality và Validation

### 2.3.1. Tầm quan trọng của Data Quality

**Data Quality** là độ phù hợp của dữ liệu cho mục đích sử dụng.

**Các chiều của Data Quality:**
- **Accuracy**: Dữ liệu chính xác, đúng sự thật
- **Completeness**: Dữ liệu đầy đủ, không thiếu
- **Consistency**: Dữ liệu nhất quán giữa các nguồn
- **Timeliness**: Dữ liệu được cập nhật kịp thời
- **Validity**: Dữ liệu tuân theo format, rules

**Hậu quả của dữ liệu kém chất lượng:**
- Quyết định sai
- Tốn chi phí sửa lỗi
- Mất niềm tin của khách hàng
- Vi phạm compliance

### 2.3.2. Validation Strategies

**1. Syntactic Validation** (Kiểm tra cú pháp)
- Email đúng format: `user@domain.com`
- Phone đúng format: `+84901234567`
- Trong đồ án: Dùng Regular Expression

**2. Semantic Validation** (Kiểm tra ý nghĩa)
- Quantity > 0
- Price > 0
- Date không được trong tương lai

**3. Cross-field Validation**
- Total = Quantity × Price
- End date > Start date

### 2.3.3. Regular Expression (Regex)

**Khái niệm:**
Regex là chuỗi ký tự đặc biệt dùng để mô tả pattern tìm kiếm trong văn bản.

**Các ký tự cơ bản:**
- `^`: Bắt đầu chuỗi
- `$`: Kết thúc chuỗi
- `.`: Bất kỳ ký tự nào
- `*`: 0 hoặc nhiều lần
- `+`: 1 hoặc nhiều lần
- `[abc]`: a, b, hoặc c
- `\d`: Chữ số (0-9)
- `\w`: Chữ cái và số

**Regex trong đồ án:**

**Email:**
```
^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$
```
- `[a-zA-Z0-9._%+-]+`: Local part (trước @)
- `@`: Ký tự @
- `[a-zA-Z0-9.-]+`: Domain
- `\.`: Dấu chấm
- `[a-zA-Z]{2,}`: Extension (.com, .vn)

**Phone (Vietnam):**
```
^(\+84|84|0)[0-9]{9,10}$
```
- `(\+84|84|0)`: Bắt đầu +84, 84, hoặc 0
- `[0-9]{9,10}`: 9-10 chữ số

### 2.3.4. Two-Stage Validation trong đồ án

**Stage 1: Consumer Validation (Real-time)**
- Validate ngay khi nhận message từ RabbitMQ
- Các rule: NOT NULL, Email format, Phone format
- Insert vào staging với `validation_errors` JSON (nếu có lỗi)

**Stage 2: Transform Validation (Batch)**
- Re-validate lại dữ liệu từ staging
- Load rules từ database (linh hoạt hơn)
- Có thể add thêm rules mới mà không cần deploy lại code
- Apply transformation rules (normalize)

**Lợi ích của Two-Stage:**
- **Fail fast**: Phát hiện lỗi sớm ở Consumer
- **Flexibility**: Stage 2 dùng rules trong DB, dễ thay đổi
- **Double check**: Đảm bảo data quality cao hơn

## 2.4. Design Patterns trong ETL

### 2.4.1. Strategy Pattern

**Mục đích:** Định nghĩa họ các thuật toán, đóng gói từng thuật toán, làm cho chúng có thể thay thế lẫn nhau.

**Áp dụng trong đồ án: Validation Rules**

Thay vì hard-code validation logic:
```java
if (email.isEmpty() || !email.contains("@")) {
    // error
}
```

Sử dụng Strategy Pattern:
```java
interface ValidationRule {
    RuleResult validate(Object value);
}

class EmailRule implements ValidationRule {
    RuleResult validate(Object value) {
        // Validate email
    }
}

class PhoneRule implements ValidationRule {
    RuleResult validate(Object value) {
        // Validate phone
    }
}
```

**Lợi ích:**
- Dễ thêm rule mới
- Code dễ test
- Tuân thủ Open/Closed Principle

### 2.4.2. Producer-Consumer Pattern

**Mục đích:** Tách biệt việc tạo ra dữ liệu (Producer) và xử lý dữ liệu (Consumer).

**Áp dụng trong đồ án:**
- **Producer**: CSVProducer đọc CSV và publish messages
- **Queue**: RabbitMQ employee-queue, order-queue
- **Consumer**: EmployeeConsumer, OrderConsumer nhận và xử lý

**Lợi ích:**
- Asynchronous processing
- Scalability (thêm Consumers)
- Fault tolerance

### 2.4.3. DAO Pattern

**Mục đích:** Tách biệt logic truy cập dữ liệu khỏi business logic.

**Áp dụng trong đồ án:**
```java
class EmployeeDAO {
    void insertStaging(Employee emp, String errors);
    List<Employee> getValidRecords();
    void updateValidationErrors(int id, String errors);
}
```

**Lợi ích:**
- Dễ thay đổi database (MySQL → PostgreSQL)
- Code dễ test (mock DAO)
- Separation of concerns

---

**[Kết thúc Phần 1 - Tiếp tục Phần 2 với Chương 3]**
