# CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI

---

## 1.1. GIỚI THIỆU ĐỀ TÀI

Trong bối cảnh chuyển đổi số và phát triển nhanh chóng của công nghệ thông tin, việc xử lý và quản lý dữ liệu từ nhiều nguồn khác nhau đã trở thành một nhu cầu thiết yếu đối với các doanh nghiệp và tổ chức. Các hệ thống thông tin hiện đại thường phải đối mặt với thách thức tích hợp dữ liệu từ nhiều hệ thống kế thừa (legacy systems), file CSV, Excel, API bên ngoài và các nguồn dữ liệu không đồng nhất khác.

ETL (Extract, Transform, Load) là một quy trình quan trọng trong Data Integration và Data Warehousing, cho phép trích xuất dữ liệu từ nhiều nguồn, chuyển đổi dữ liệu theo các quy tắc nghiệp vụ, và tải dữ liệu vào hệ thống đích. Tuy nhiên, các giải pháp ETL truyền thống thường gặp các vấn đề về:

- **Xử lý tuần tự**: Khó mở rộng khi khối lượng dữ liệu tăng
- **Mất dữ liệu**: Khi có lỗi xảy ra trong quá trình xử lý
- **Thiếu tính linh hoạt**: Khó thay đổi quy tắc validation và transformation
- **Thiếu truy vết**: Không theo dõi được lịch sử thay đổi dữ liệu

Đồ án này nghiên cứu và xây dựng một **Hệ thống ETL phân tán** sử dụng kiến trúc Message Queue với RabbitMQ, áp dụng mô hình Two-Stage Processing (Data Cleansing và Data Enrichment), kết hợp với Rules Engine linh hoạt và Audit Trail đầy đủ.

---

## 1.2. LÝ DO CHỌN ĐỀ TÀI

### 1.2.1. Tính thực tiễn

Trong thực tế doanh nghiệp, việc xử lý dữ liệu từ nhiều nguồn là một bài toán phổ biến:

- **Tích hợp hệ thống**: Kết nối giữa các phòng ban, chi nhánh với hệ thống trung tâm
- **Migration dữ liệu**: Chuyển đổi từ hệ thống cũ sang hệ thống mới
- **Data Warehouse**: Xây dựng kho dữ liệu phục vụ phân tích và báo cáo
- **Master Data Management**: Quản lý dữ liệu chuẩn của tổ chức

### 1.2.2. Tính kỹ thuật

Đề tài cho phép áp dụng nhiều kiến thức và công nghệ hiện đại:

- **Message Queue Architecture**: Kiến trúc phân tán với RabbitMQ
- **Microservices Pattern**: Tách biệt các thành phần độc lập
- **Design Patterns**: Strategy, Factory, DAO patterns
- **Data Quality Management**: Validation, normalization, audit trail
- **Full-stack Development**: Backend (Java), Frontend (Python Flask), Database (MySQL)
- **DevOps**: Docker, Docker Compose, containerization

### 1.2.3. Tính học thuật

Đề tài giúp sinh viên:

- Hiểu sâu về kiến trúc hệ thống phân tán
- Nắm vững quy trình ETL và Data Integration
- Áp dụng các Design Patterns vào bài toán thực tế
- Phát triển kỹ năng xử lý lỗi và đảm bảo chất lượng dữ liệu
- Làm việc với nhiều công nghệ và framework khác nhau

---

## 1.3. PHẠM VI ĐỒ ÁN

### 1.3.1. Phạm vi nghiệp vụ

Hệ thống tập trung giải quyết bài toán ETL cho **dữ liệu nhân sự và đơn hàng**:

**Input:**
- File CSV chứa thông tin nhân viên (Employee ID, Full Name, Email, Phone)
- File CSV chứa thông tin đơn hàng (Order ID, Product ID, Quantity, Price)

**Processing:**
- Validation: Kiểm tra tính hợp lệ của dữ liệu (email format, phone format, quantity > 0, etc.)
- Transformation: Chuẩn hóa dữ liệu (Title Case cho tên, lowercase cho email, E.164 cho phone)
- Error Handling: Phát hiện và lưu trữ dữ liệu lỗi, cho phép sửa và re-validate

**Output:**
- Dữ liệu đã clean và normalize trong database chính
- Audit trail đầy đủ về các thay đổi
- Dashboard để monitor và quản lý

### 1.3.2. Phạm vi kỹ thuật

**Technologies:**
- **Backend**: Java 11, Maven
- **Message Broker**: RabbitMQ 3.x
- **Database**: MySQL 8.0
- **Frontend Dashboard**: Flask (Python), Bootstrap 5
- **Containerization**: Docker, Docker Compose

**Không bao gồm:**
- Authentication/Authorization (chỉ basic setup)
- Real-time streaming (focus vào batch processing)
- Machine Learning cho data quality prediction
- Advanced scheduling (không dùng Airflow/Luigi)

---

## 1.4. MỤC TIÊU ĐỒ ÁN

### 1.4.1. Mục tiêu chung

Xây dựng một hệ thống ETL hoàn chỉnh, áp dụng kiến trúc phân tán với Message Queue, có khả năng:

- ✅ Xử lý dữ liệu từ file CSV một cách tự động
- ✅ Validate và phát hiện lỗi dữ liệu theo các quy tắc cấu hình được
- ✅ Transform và chuẩn hóa dữ liệu theo chuẩn doanh nghiệp
- ✅ Đảm bảo không mất dữ liệu (fault tolerance)
- ✅ Có khả năng mở rộng (scalability)
- ✅ Cung cấp giao diện quản lý trực quan

### 1.4.2. Mục tiêu cụ thể

**1. Về kiến trúc hệ thống:**
- Thiết kế và triển khai kiến trúc microservices với message queue
- Đảm bảo loose coupling giữa các components
- Implement fault tolerance và error recovery mechanisms

**2. Về xử lý dữ liệu:**
- Implement two-stage transform (Data Cleansing + Data Enrichment)
- Xây dựng Rules Engine linh hoạt, có thể enable/disable rules không cần deploy lại
- Áp dụng Regular Expression để validate dữ liệu
- Chuẩn hóa dữ liệu theo các standards (E.164 cho phone, RFC 5322 cho email)

**3. Về chất lượng dữ liệu:**
- Phát hiện và lưu trữ chi tiết các lỗi validation
- Cho phép sửa lỗi và re-validate
- Ghi lại audit trail đầy đủ (field-level changes)
- Tính toán metrics về data quality

**4. Về giao diện và trải nghiệm:**
- Dashboard trực quan để monitor dữ liệu
- Upload CSV dễ dàng với drag & drop
- Xem và sửa lỗi validation
- Export dữ liệu đã chuẩn hóa
- Xem lịch sử transform và audit trail

**5. Về deployment và vận hành:**
- Containerize toàn bộ hệ thống với Docker
- Sử dụng Docker Compose để orchestration
- Cung cấp scripts để dễ dàng setup và test

---

## 1.5. TỔNG QUAN VỀ ETL

### 1.5.1. Khái niệm ETL

**ETL (Extract, Transform, Load)** là quy trình gồm ba giai đoạn chính:

1. **Extract (Trích xuất)**: Thu thập dữ liệu từ các nguồn khác nhau
2. **Transform (Chuyển đổi)**: Làm sạch, chuẩn hóa và biến đổi dữ liệu
3. **Load (Tải)**: Đưa dữ liệu vào hệ thống đích (Data Warehouse, Database)

### 1.5.2. Vai trò của ETL

**Trong Data Integration:**
- Kết nối các hệ thống khác nhau
- Đồng bộ dữ liệu giữa các nguồn
- Tích hợp dữ liệu từ nhiều nguồn vào một kho dữ liệu tập trung

**Trong Data Quality:**
- Phát hiện và xử lý dữ liệu lỗi
- Chuẩn hóa dữ liệu theo standards
- Đảm bảo tính nhất quán của dữ liệu

**Trong Business Intelligence:**
- Chuẩn bị dữ liệu cho phân tích
- Tạo dimensional models
- Tính toán các metrics và KPIs

### 1.5.3. Quy trình ETL truyền thống vs. Hiện đại

**ETL Truyền thống:**
```
CSV File → ETL Tool → Data Warehouse
         (Batch processing, sequential)
```

**ETL Hiện đại (Real-time/Near-real-time):**
```
Multiple Sources → Message Queue → Consumers → Staging → Transform → Data Lake/DW
                 (Distributed, parallel, fault-tolerant)
```

**[Hình 1.1 - Quy trình ETL tổng quan]**

### 1.5.4. Thách thức trong ETL

1. **Data Volume**: Xử lý hàng triệu, hàng tỷ records
2. **Data Variety**: Nhiều định dạng khác nhau (CSV, JSON, XML, API, Database)
3. **Data Velocity**: Cần xử lý nhanh, có thể real-time
4. **Data Quality**: Dữ liệu thường có lỗi, thiếu, không nhất quán
5. **Scalability**: Cần mở rộng khi dữ liệu tăng
6. **Fault Tolerance**: Không được mất dữ liệu khi có lỗi

### 1.5.5. Kiến trúc ETL trong đồ án

Đồ án áp dụng kiến trúc **Message-Queue-Based ETL** với các đặc điểm:

✅ **Asynchronous Processing**: Producer và Consumer hoạt động độc lập
✅ **Scalability**: Có thể thêm nhiều Consumers để tăng throughput
✅ **Fault Tolerance**: Message được persistent, không mất khi consumer die
✅ **Decoupling**: Producer không cần biết Consumer, dễ maintain
✅ **Two-Stage Transform**: Tách validation và transformation
✅ **Rules Engine**: Linh hoạt, có thể thay đổi rules không cần deploy

**[Hình 1.2 - Luồng dữ liệu trong hệ thống]**

```
CSV Files
   ↓
Producer (Java)
   ↓
RabbitMQ Queues
   ↓
Consumers (Java) → Staging DB (validation_errors)
   ↓
Transform Engine (Two-Stage)
   ├─ Stage 1: Data Cleansing (Validation)
   └─ Stage 2: Data Enrichment (Transformation)
   ↓
Main DB (clean data) + Audit Trail
   ↓
Dashboard (Flask) - Monitor & Control
```

---

## 1.6. TỔNG KẾT CHƯƠNG

Chương 1 đã trình bày tổng quan về đề tài, bao gồm lý do chọn đề tài, phạm vi, mục tiêu và các khái niệm cơ bản về ETL. Đồ án tập trung xây dựng một hệ thống ETL phân tán với Message Queue, áp dụng Two-Stage Processing và Rules Engine để đảm bảo chất lượng dữ liệu. 

Chương tiếp theo sẽ trình bày chi tiết về các cơ sở lý thuyết, các công nghệ và framework được sử dụng trong hệ thống.
