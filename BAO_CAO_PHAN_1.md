# BÁO CÁO ĐỒ ÁN TÍCH HỢP HỆ THỐNG
## HỆ THỐNG ETL VỚI RABBITMQ VÀ VALIDATION

---

## TRANG BÌA

**ĐỒ ÁN:** Tích Hợp Hệ Thống  
**ĐỀ TÀI:** Hệ Thống ETL Xử Lý Dữ Liệu Nhân Sự với RabbitMQ và Data Quality Validation

**Danh sách thành viên tham gia:**
- [Tên sinh viên]
- [MSSV]

**Giảng viên hướng dẫn:** [Tên giảng viên]

**Thời gian thực hiện:** Tháng 11-12/2025

---

# CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI

## 1.1. GIỚI THIỆU VỀ ĐỀ TÀI

### 1.1.1. Bối cảnh

Trong môi trường doanh nghiệp hiện đại, việc xử lý và tích hợp dữ liệu từ nhiều nguồn khác nhau là một thách thức lớn. Dữ liệu thường không đồng nhất về format, chất lượng và có thể chứa nhiều lỗi. Việc xây dựng một hệ thống ETL (Extract, Transform, Load) hiệu quả giúp:

- Tự động hóa quy trình xử lý dữ liệu
- Đảm bảo chất lượng dữ liệu trước khi đưa vào hệ thống chính
- Xử lý bất đồng bộ với khả năng mở rộng cao
- Theo dõi và báo cáo lỗi dữ liệu một cách trực quan

### 1.1.2. Mục tiêu đồ án

**Mục tiêu chính:**
- Xây dựng hệ thống ETL hoàn chỉnh xử lý dữ liệu nhân sự và đơn hàng
- Tích hợp message queue (RabbitMQ) để xử lý bất đồng bộ
- Triển khai validation rules đảm bảo data quality
- Xây dựng dashboard theo dõi và quản lý dữ liệu

**Mục tiêu cụ thể:**
1. Đọc và xử lý dữ liệu từ file CSV
2. Gửi dữ liệu qua RabbitMQ message queue
3. Consumer nhận và lưu vào staging database
4. Validate dữ liệu theo business rules
5. Chuyển dữ liệu hợp lệ vào main database
6. Hiển thị kết quả và lỗi trên web dashboard

### 1.1.3. Phạm vi đồ án

**Trong phạm vi:**
- Xử lý 2 loại dữ liệu: Employee (Nhân viên) và Order (Đơn hàng)
- Validation rules: Email format, Phone number format, Quantity validation
- Message queue: RabbitMQ với 2 queues riêng biệt
- Database: MySQL với staging và main tables
- Web interface: Upload CSV, hiển thị kết quả validation

**Ngoài phạm vi:**
- Xử lý file lớn (>100MB)
- Real-time streaming data
- Data encryption
- User authentication/authorization
- Production deployment với high availability

## 1.2. LÝ DO CHỌN ĐỀ TÀI

### 1.2.1. Tính thực tiễn

ETL là quy trình thiết yếu trong mọi tổ chức xử lý dữ liệu. Việc hiểu rõ và thực hành ETL pipeline giúp:
- Nắm vững kiến thức về data integration
- Hiểu về asynchronous processing
- Làm việc với message queue trong thực tế
- Xây dựng data quality framework

### 1.2.2. Tính ứng dụng cao

Hệ thống có thể áp dụng cho:
- Import dữ liệu nhân sự từ các hệ thống cũ
- Tích hợp dữ liệu từ partners/vendors
- Migration data giữa các hệ thống
- Data cleansing và quality control

### 1.2.3. Công nghệ phổ biến

Các công nghệ sử dụng đều là industry standard:
- **Java**: Ngôn ngữ backend phổ biến
- **RabbitMQ**: Message broker được sử dụng rộng rãi
- **MySQL**: Database quan hệ phổ biến nhất
- **Docker**: Container platform tiêu chuẩn
- **Maven**: Build tool chuẩn cho Java

## 1.3. MỤC TIÊU NGHIÊN CỨU

### 1.3.1. Về kiến thức

- Hiểu rõ kiến trúc và quy trình ETL
- Nắm vững message queue pattern và asynchronous processing
- Áp dụng validation rules và data quality principles
- Triển khai microservices architecture với Docker

### 1.3.2. Về kỹ năng

- Lập trình Java với design patterns
- Tích hợp RabbitMQ trong ứng dụng Java
- Làm việc với MySQL database
- Xây dựng REST API với Flask (Python)
- Containerization với Docker và Docker Compose
- Unit testing và integration testing

### 1.3.3. Về sản phẩm

- Hệ thống ETL hoàn chỉnh, có thể chạy độc lập
- Source code có cấu trúc rõ ràng, dễ maintain
- Documentation đầy đủ
- Test coverage đảm bảo chất lượng
- Dashboard trực quan, dễ sử dụng

---

# KẾT LUẬN CHƯƠNG 1

Chương 1 đã giới thiệu tổng quan về đồ án, bao gồm bối cảnh, mục tiêu, phạm vi và lý do chọn đề tài. Đồ án tập trung vào việc xây dựng một hệ thống ETL hoàn chỉnh với message queue và data validation, ứng dụng các công nghệ phổ biến trong ngành. Hệ thống không chỉ có tính học thuật mà còn có thể ứng dụng thực tế trong các doanh nghiệp.

Chương tiếp theo sẽ đi sâu vào nghiên cứu về các biểu thức chính quy, design patterns và framework được sử dụng trong đồ án.

---

**Trang:** 1-8  
**Phần:** CHƯƠNG 1 - TỔNG QUAN ĐỀ TÀI
