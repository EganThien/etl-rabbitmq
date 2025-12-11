# 🚀 Hướng dẫn chạy nhanh ETL Pipeline

## Yêu cầu
- ✅ Docker Desktop đã cài đặt và **đang chạy**
- ✅ Java 11+ và Maven
- ✅ PowerShell

---

## Cách 1: Chạy Full Pipeline (Khuyến nghị)

### Bước 1: Khởi động Docker Desktop
```powershell
# Mở Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

Đợi 30-60 giây cho Docker Desktop sẵn sàng (biểu tượng Docker trên taskbar không còn loading).

### Bước 2: Chạy toàn bộ pipeline
```powershell
cd d:\1.ProjectTuHoc\DA_TichHopHeThong\etl-rabbitmq
.\scripts\run-full.ps1
```

**Script này sẽ tự động:**
1. Build Java application với Maven
2. Khởi động Docker Compose (RabbitMQ + MySQL + Dashboard)
3. Load database schema
4. Chạy Producer (đọc CSV → publish lên RabbitMQ)
5. Chạy Consumers (consume messages → staging tables)
6. Chạy Transform (validate + move staging → main tables)

### Bước 3: Xem Dashboard
Mở trình duyệt tại: **http://localhost:8080**

Dashboard sẽ hiển thị:
- **Dữ liệu đã Transform** (màu xanh) - Records hợp lệ đã chuyển vào main tables
- **Lỗi Ghi Nhận** (màu đỏ) - Records không hợp lệ với chi tiết validation errors

### Bước 4: Xem logs (optional)
```powershell
# Xem logs của consumers
docker compose logs -f app-employee-consumer
docker compose logs -f app-order-consumer

# Xem logs của transform
docker compose logs app-transform

# Xem logs của dashboard
docker compose logs -f etl-dashboard
```

---

## Cách 2: Chạy từng bước (Manual)

### 1. Khởi động services
```powershell
cd d:\1.ProjectTuHoc\DA_TichHopHeThong\etl-rabbitmq
docker compose up -d rabbitmq mysql etl-dashboard
```

### 2. Đợi services sẵn sàng (30 giây)
```powershell
Start-Sleep -Seconds 30
```

### 3. Load schema
```powershell
.\scripts\load-schema.ps1
```

### 4. Build Java application
```powershell
mvn clean package -DskipTests
```

### 5. Chạy Producer (publish CSV → RabbitMQ)
```powershell
.\scripts\run-producer.ps1
```

### 6. Chạy Consumers (trong terminal riêng)
```powershell
# Terminal 1
.\scripts\run-consumers.ps1
```

### 7. Chạy Transform (validate + load)
```powershell
# Terminal 2
.\scripts\run-transform.ps1
```

### 8. Xem Dashboard
Mở: **http://localhost:8080**

---

## Cách 3: E2E Testing Script

Chạy toàn bộ flow với một lệnh (tương tự run-full.ps1):

```powershell
.\scripts\run-e2e.ps1
```

---

## 🔍 Kiểm tra dữ liệu trong database

### Kết nối MySQL
```powershell
docker exec -it mysql mysql -u etl_user -petl_password etl_db
```

### Query staging tables
```sql
-- Xem dữ liệu staging
SELECT * FROM staging_employee LIMIT 10;
SELECT * FROM staging_order_detail LIMIT 10;
```

### Query main tables (sau khi transform)
```sql
-- Xem dữ liệu đã transform
SELECT id, firstName, email, phone, is_valid FROM main_employee LIMIT 10;
SELECT * FROM main_order_detail LIMIT 10;
```

### Xem validation errors
```sql
-- Xem records có lỗi validation
SELECT id, firstName, email, phone, validation_errors 
FROM main_employee 
WHERE is_valid = FALSE;

SELECT id, productName, quantity, validation_errors
FROM main_order_detail
WHERE is_valid = FALSE;
```

---

## 🎯 Kết quả mong đợi

### Dashboard sẽ hiển thị:

**Dữ liệu Đã Transform (màu xanh):**
```json
{
  "id": 101,
  "firstName": "Alice",
  "email": "aliceexample.com",
  "phone": "0901234567"
}
```

**Lỗi Ghi Nhận (màu đỏ) - 17 lỗi:**
- `[Product] name` - Tên sản phẩm trống
- `[Product] email` - Email không hợp lệ
- `[Product] phone` - Số điện thoại sai định dạng
- `[Product] sku` - SKU không đúng định dạng
- `[Product] name` - Tên sản phẩm trùng lặp
- `[Product] price` - Giá âm (Transform Failed)
- `[User] email` - Email không hợp lệ
- `[User] firstName` - Tên trống
- `[User] phone` - Số điện thoại sai định dạng

---

## 🛑 Dừng services

```powershell
docker compose down
```

Hoặc dùng script:
```powershell
.\scripts\stop-all.ps1
```

---

## 📊 Kiểm tra RabbitMQ Management UI

URL: http://localhost:15672  
User: `guest` (hoặc kiểm tra `.env`)  
Pass: `guest` (hoặc kiểm tra `.env`)

**Queues:**
- `employee.queue` - Employee messages
- `order_detail.queue` - Order detail messages

---

## 🐛 Troubleshooting

### Docker không chạy
```powershell
# Kiểm tra Docker status
docker ps
```
Nếu lỗi: "The system cannot find the file specified" → Mở Docker Desktop và đợi sẵn sàng.

### Port đã được sử dụng
Kiểm tra ports: 5672 (RabbitMQ), 15672 (RabbitMQ Management), 3306 (MySQL), 8080 (Dashboard)

```powershell
# Windows
netstat -ano | findstr ":8080"
```

### Dashboard không hiển thị dữ liệu
1. Kiểm tra Docker containers đang chạy: `docker ps`
2. Kiểm tra logs: `docker compose logs etl-dashboard`
3. Verify MySQL có dữ liệu: `docker exec -it mysql mysql -u etl_user -petl_password etl_db -e "SELECT COUNT(*) FROM main_employee;"`

### Maven build failed
```powershell
# Clean và rebuild
mvn clean compile
mvn clean package -DskipTests
```

---

## 📝 Tóm tắt các lệnh quan trọng

| Mục đích | Lệnh |
|----------|------|
| Chạy full pipeline | `.\scripts\run-full.ps1` |
| Chạy E2E test | `.\scripts\run-e2e.ps1` |
| Xem dashboard | http://localhost:8080 |
| Dừng services | `docker compose down` |
| Xem logs | `docker compose logs -f <service-name>` |
| Load schema | `.\scripts\load-schema.ps1` |
| Chạy producer | `.\scripts\run-producer.ps1` |
| Chạy consumers | `.\scripts\run-consumers.ps1` |
| Chạy transform | `.\scripts\run-transform.ps1` |

---

## 🎓 Flow của ETL Pipeline

```
┌─────────────┐
│  CSV Files  │ (employee.csv, order_detail.csv)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Producer   │ (CSVProducer.java)
└──────┬──────┘
       │ Publish messages
       ▼
┌─────────────┐
│  RabbitMQ   │ (employee.queue, order_detail.queue)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Consumers  │ (EmployeeConsumer, OrderDetailConsumer)
└──────┬──────┘
       │ Insert to staging
       ▼
┌─────────────────┐
│ Staging Tables  │ (staging_employee, staging_order_detail)
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│ Transform   │ (TransformLoad.java + Validators)
└──────┬──────┘
       │ Validate + Mark errors
       ▼
┌─────────────────┐
│  Main Tables    │ (main_employee, main_order_detail)
└──────┬──────────┘
       │
       ▼
┌─────────────┐
│  Dashboard  │ (Flask app on port 8080)
└─────────────┘
```

---

## 🔐 Credentials mặc định

Tất cả credentials nằm trong file `.env` (hoặc docker-compose.yml):

```env
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=etl_db
MYSQL_USER=etl_user
MYSQL_PASSWORD=etl_password

RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
```

---

**Chúc bạn chạy thành công! 🎉**
