# CHƯƠNG 3: PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG

---

## 3.1. PHÂN TÍCH YÊU CẦU

### 3.1.1. Actors (Tác nhân)

**Bảng 3.1 - Mô tả các Actor**

| Actor | Mô tả | Vai trò |
|-------|-------|---------|
| **Data Operator** | Nhân viên xử lý dữ liệu | - Upload file CSV<br>- Trigger transform<br>- Xem và sửa lỗi validation<br>- Export dữ liệu |
| **System Administrator** | Quản trị hệ thống | - Quản lý validation rules<br>- Monitor system health<br>- Xem audit logs<br>- Configure system |
| **Business Analyst** | Phân tích nghiệp vụ | - Xem data quality metrics<br>- Xem transform history<br>- Generate reports |
| **ETL System** | Hệ thống tự động | - Producer (đọc CSV)<br>- Consumers (validate)<br>- Transform engine<br>- Scheduler |

### 3.1.2. Use Cases

**Bảng 3.2 - Danh sách Use Cases**

| ID | Use Case | Actor | Mô tả |
|----|----------|-------|-------|
| **UC01** | Upload CSV File | Data Operator | Upload file CSV lên hệ thống |
| **UC02** | Process CSV to Queue | ETL System | Producer đọc CSV và publish lên RabbitMQ |
| **UC03** | Consume và Validate | ETL System | Consumer nhận message, validate và insert staging |
| **UC04** | View Staging Data | Data Operator | Xem dữ liệu trong staging tables |
| **UC05** | View Validation Errors | Data Operator | Xem chi tiết các lỗi validation |
| **UC06** | Edit Error Records | Data Operator | Sửa dữ liệu lỗi và re-validate |
| **UC07** | Run Transform | Data Operator | Trigger transform từ staging sang main |
| **UC08** | View Main Data | Data Operator | Xem dữ liệu đã clean trong main tables |
| **UC09** | View Audit Trail | Data Operator/Analyst | Xem lịch sử thay đổi dữ liệu |
| **UC10** | Manage Rules | System Administrator | Enable/disable validation rules |
| **UC11** | View Metrics | Business Analyst | Xem data quality metrics |
| **UC12** | Export Data | Data Operator | Export dữ liệu đã clean ra CSV |

**[Hình 3.1 - Use Case Diagram]**

```
                    ┌─────────────────┐
                    │  Data Operator  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    UC01: Upload       UC04: View          UC07: Run
        CSV           Staging Data        Transform
        │                    │                    │
        │              UC05: View           UC08: View
        │            Validation             Main Data
        │              Errors                    │
        │                    │              UC09: View
        │              UC06: Edit            Audit Trail
        │              Errors                    │
        │                                   UC12: Export
        │                                    Data
        └────────────────────┬──────────────────┘
                             │
                    ┌────────┴────────┐
                    │   ETL System    │
                    │  (Automated)    │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    UC02: Process      UC03: Consume        UC07: Run
    CSV to Queue      and Validate         Transform
                                            (2-Stage)
```

### 3.1.3. Use Case Chi tiết: Upload và Transform CSV

**UC01: Upload CSV File**

**Pre-conditions:**
- User đã đăng nhập vào dashboard
- File CSV đúng format (có header)

**Main Flow:**
1. User truy cập trang Upload (`/upload`)
2. User chọn file type (Employee hoặc Order)
3. User kéo thả hoặc chọn file CSV
4. User nhập tên file (optional)
5. User click "Tải lên"
6. System validate file (extension, size)
7. System parse CSV và insert vào staging tables
8. System trả về kết quả (số records inserted, skipped, errors)

**Post-conditions:**
- Dữ liệu đã được insert vào staging tables
- Batch ID được generate

**Alternative Flow:**
- 6a. File không hợp lệ → Show error message
- 7a. Parse error → Log error và skip row
- 7b. Database error → Rollback transaction

**UC07: Run Transform**

**Pre-conditions:**
- Có dữ liệu trong staging tables
- Validation rules đã được configure

**Main Flow:**
1. User click "Chạy Transform" trên dashboard
2. System bắt đầu Transform Engine
3. **Stage 1 - Data Cleansing:**
   - Load validation rules từ database
   - Query staging records (validation_errors IS NULL)
   - Apply validation rules
   - Mark invalid records với JSON errors
4. **Stage 2 - Data Enrichment:**
   - Load transformation rules từ database
   - Query valid records
   - Apply transformations (normalize, format)
   - Log changes to audit trail
   - Insert to main tables
   - Delete from staging
5. System update metrics tables
6. System trả về kết quả (employees, orders transferred, errors)
7. Dashboard hiển thị kết quả và refresh data

**Post-conditions:**
- Dữ liệu valid đã được transform và insert vào main tables
- Dữ liệu invalid đã được mark errors trong staging
- Audit trail đã được log
- Metrics đã được update

### 3.1.4. Activity Diagram

**[Hình 3.2 - Activity Diagram: Luồng xử lý ETL]**

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  Upload CSV File │
└──────┬───────────┘
       │
       ▼
   ┌───────────┐
   │ Parse CSV │
   └─────┬─────┘
         │
         ▼
   ┌─────────────────┐
   │ Insert Staging  │
   └─────┬───────────┘
         │
         ▼
   ┌───────────────────┐
   │ Trigger Transform │
   └─────┬─────────────┘
         │
         ▼
   ╔═══════════════════╗
   ║ STAGE 1: Validate ║
   ╚═══════┬═══════════╝
           │
           ▼
    ┌──────────────┐
    │ Apply Rules  │
    └──────┬───────┘
           │
       ┌───┴───┐
       │       │
   Valid?    Invalid
       │       │
       │       ▼
       │  ┌─────────────┐
       │  │ Mark Errors │
       │  └─────────────┘
       │
       ▼
   ╔════════════════════╗
   ║ STAGE 2: Transform ║
   ╚═══════┬════════════╝
           │
           ▼
    ┌───────────────┐
    │ Apply         │
    │ Transformations│
    └──────┬────────┘
           │
           ▼
    ┌───────────────┐
    │ Log Audit     │
    │ Trail         │
    └──────┬────────┘
           │
           ▼
    ┌──────────────────┐
    │ Insert Main DB   │
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────┐
    │ Delete Staging   │
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────┐
    │ Update Metrics   │
    └──────┬───────────┘
           │
           ▼
      ┌────────┐
      │  END   │
      └────────┘
```

### 3.1.5. Sequence Diagram

**[Hình 3.3 - Sequence Diagram: Upload và Transform]**

```
User    Dashboard    Producer    RabbitMQ    Consumer    Staging DB    Transform    Main DB
 │           │           │           │           │            │            │           │
 │  Upload   │           │           │           │            │            │           │
 ├──────────>│           │           │           │            │            │           │
 │           │ Read CSV  │           │           │            │            │           │
 │           ├──────────>│           │           │            │            │           │
 │           │           │ Publish   │           │            │            │           │
 │           │           ├──────────>│           │            │            │           │
 │           │           │           │ Deliver   │            │            │           │
 │           │           │           ├──────────>│            │            │           │
 │           │           │           │           │ Validate   │            │           │
 │           │           │           │           │────────┐   │            │           │
 │           │           │           │           │        │   │            │           │
 │           │           │           │           │<───────┘   │            │           │
 │           │           │           │           │ Insert     │            │           │
 │           │           │           │           ├───────────>│            │           │
 │           │           │           │ ACK       │            │            │           │
 │           │           │           │<──────────┤            │            │           │
 │           │           │           │           │            │            │           │
 │  Trigger  │           │           │           │            │            │           │
 │ Transform │           │           │           │            │            │           │
 ├──────────>│           │           │           │            │            │           │
 │           │           │           │           │            │ Stage 1    │           │
 │           │           │           │           │            │ Validate   │           │
 │           │           │           │           │            │───────────>│           │
 │           │           │           │           │            │ Mark Errors│           │
 │           │           │           │           │            │<───────────┤           │
 │           │           │           │           │            │            │           │
 │           │           │           │           │            │ Stage 2    │           │
 │           │           │           │           │            │ Transform  │           │
 │           │           │           │           │            │───────────>│           │
 │           │           │           │           │            │            │ Insert    │
 │           │           │           │           │            │            ├──────────>│
 │           │           │           │           │            │ Delete     │           │
 │           │           │           │           │            │<───────────┤           │
 │           │ Result    │           │           │            │            │           │
 │<──────────┤           │           │           │            │            │           │
 │           │           │           │           │            │            │           │
```

---

## 3.2. THIẾT KẾ CƠ SỞ DỮ LIỆU

### 3.2.1. Tổng quan Database Schema

Hệ thống sử dụng MySQL với các nhóm tables sau:

1. **Staging Tables**: Lưu dữ liệu tạm thời từ CSV
2. **Main Tables**: Lưu dữ liệu đã clean và normalize
3. **Rules Tables**: Configuration cho validation và transformation
4. **Audit Tables**: Log lịch sử thay đổi dữ liệu
5. **Metrics Tables**: Thống kê chất lượng dữ liệu

**[Hình 3.4 - ERD Overview]**

### 3.2.2. Staging Tables (Data Source)

**Bảng 3.3 - Cấu trúc bảng staging_employee**

| Column | Type | Constraints | Mô tả |
|--------|------|-------------|-------|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | ID tự tăng |
| `employee_id` | VARCHAR(20) | NOT NULL | Mã nhân viên |
| `full_name` | VARCHAR(100) | | Họ tên đầy đủ |
| `email` | VARCHAR(100) | | Email |
| `phone` | VARCHAR(20) | | Số điện thoại |
| `batch_id` | VARCHAR(50) | INDEX | ID của batch upload |
| `validation_errors` | JSON | | Lỗi validation (nếu có) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |

**SQL Create Table:**
```sql
CREATE TABLE staging_employee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    batch_id VARCHAR(50),
    validation_errors JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_validation (validation_errors((1))),
    INDEX idx_batch (batch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Ý nghĩa các fields:**

- `validation_errors`: Lưu dạng JSON array, ví dụ:
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

- `batch_id`: Để group các records cùng một lần upload, format: `employee_20251207_143022`

**Bảng 3.4 - Cấu trúc bảng staging_order_detail**

| Column | Type | Constraints | Mô tả |
|--------|------|-------------|-------|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | ID tự tăng |
| `order_id` | VARCHAR(20) | NOT NULL | Mã đơn hàng |
| `product_id` | VARCHAR(20) | | Mã sản phẩm |
| `quantity` | INT | | Số lượng |
| `price` | DECIMAL(15,2) | | Giá |
| `batch_id` | VARCHAR(50) | INDEX | ID của batch upload |
| `validation_errors` | JSON | | Lỗi validation |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |

### 3.2.3. Main Tables (Data Warehouse)

**Bảng 3.5 - Cấu trúc bảng main_employee**

| Column | Type | Constraints | Mô tả |
|--------|------|-------------|-------|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | ID tự tăng |
| `employee_id` | VARCHAR(20) | NOT NULL, UNIQUE | Mã nhân viên (unique) |
| `full_name` | VARCHAR(100) | NOT NULL | Họ tên đã chuẩn hóa |
| `email` | VARCHAR(100) | INDEX | Email đã chuẩn hóa |
| `phone` | VARCHAR(20) | INDEX | Phone đã format E.164 |
| `batch_id` | VARCHAR(50) | | Batch ID khi transform |
| `original_data` | JSON | | Dữ liệu gốc (backup) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |
| `updated_at` | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP | Thời gian cập nhật |

**SQL Create Table:**
```sql
CREATE TABLE main_employee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    batch_id VARCHAR(50),
    original_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
               ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Ý nghĩa:**

- `employee_id`: UNIQUE để tránh duplicate
- `original_data`: Backup dữ liệu gốc trước khi transform, để có thể rollback nếu cần
- `updated_at`: Tự động update khi record thay đổi

**Bảng 3.6 - Cấu trúc bảng main_order_detail**

| Column | Type | Constraints | Mô tả |
|--------|------|-------------|-------|
| `id` | INT | PRIMARY KEY, AUTO_INCREMENT | ID tự tăng |
| `order_id` | VARCHAR(20) | NOT NULL, INDEX | Mã đơn hàng |
| `product_id` | VARCHAR(20) | INDEX | Mã sản phẩm |
| `quantity` | INT | NOT NULL | Số lượng |
| `price` | DECIMAL(15,2) | NOT NULL | Giá đã chuẩn hóa |
| `batch_id` | VARCHAR(50) | | Batch ID |
| `original_data` | JSON | | Dữ liệu gốc |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Thời gian tạo |

**[Hình 3.5 - ERD: Main Tables]**
