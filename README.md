# Quản lý Dữ liệu Nhân sự (ETL Demo)

Plain-Java ETL demo: CSV → RabbitMQ → Staging → Transform → MySQL, with a small Data Quality dashboard.

Mục tiêu: Mô phỏng pipeline ETL đọc CSV → publish lên RabbitMQ → consumer validate → lưu Staging DB → transform → load Main DB.

YÃªu cáº§u trÆ°á»›c khi cháº¡y:
- Java 11+
- Maven
- Docker Desktop (Ä‘Ã£ cÃ i) vÃ  docker compose

Cháº¡y stack (RabbitMQ + MySQL):

```powershell
cd etl-rabbitmq
docker compose up -d
```

Kiá»ƒm tra RabbitMQ Management UI: http://localhost:15672 (user/pass tá»« `.env`)

CÃ i dependencies & build:

```powershell
mvn -v
mvn clean package -DskipTests
```

Cháº¡y á»©ng dá»¥ng (vÃ­ dá»¥ cháº¡y Producer/Consumer tá»« IDE hoáº·c jar):

```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.Application"
```

VÃ­ dá»¥ cháº¡y Producer (publish CSV -> queues):

```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="producer"
```

VÃ­ dá»¥ cháº¡y Employee Consumer (consume employee messages -> staging DB):

```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="employee-consumer"
```

VÃ­ dá»¥ cháº¡y Order Consumer (consume order messages -> staging DB):

```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="order-consumer"
```

VÃ­ dá»¥ cháº¡y Transform & Load (staging -> main):

```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="transform"
```

Run full pipeline with Docker Compose
-----------------------------------
You can build the application image and run the whole pipeline (RabbitMQ, MySQL, producer, consumers, transform) using docker compose. This will build the Java app image (multi-stage) and start the services.

Start full stack (build image and run all services):
```powershell
docker compose up --build -d
```

Notes:
- `app-producer` will run once (command `producer`) and exit; consumers (`app-employee-consumer`, `app-order-consumer`) run continuously.
- To run only the producer (one-off):
```powershell
docker compose run --rm app-producer
```
- To view logs for consumers:
```powershell
docker compose logs -f app-employee-consumer
docker compose logs -f app-order-consumer
```
- To run transform container once:
```powershell
docker compose run --rm app-transform
```

Dashboard (optional)
-------------------
I added a small read-only dashboard service that shows RabbitMQ queue sizes and table counts. After starting the stack, open:

http://localhost:8080

To run the dashboard with the rest of the stack (it is included in `docker compose up --build -d`), or start it separately:

```powershell
docker compose up --build -d etl-dashboard
```

File quan trá»ng:
- `docker-compose.yml` : khá»Ÿi RabbitMQ vÃ  MySQL
- `src/main/resources/data` : sample CSV
- `src/main/resources/sql/create_tables.sql` : script táº¡o báº£ng

Schema note — `phone` column
--------------------------------
Tôi đã thêm trường `phone` cho bảng `staging_employee` và `main_employee` (kiểu `VARCHAR(50)`). Nếu bạn đang nâng cấp một database hiện có, chạy migration SQL sau trước khi chạy pipeline:

```sql
ALTER TABLE staging_employee ADD COLUMN phone VARCHAR(50);
ALTER TABLE main_employee ADD COLUMN phone VARCHAR(50);
```

CSV format
----------
`employee.csv` có thể có 3 hoặc 4 cột. Các cột hiện được đọc theo thứ tự:
- `employee_id`, `full_name`, `email`, `[phone]` (phone là tuỳ chọn nếu file có cột thứ 4).

Validation
----------
- `EmailRule` sử dụng Apache Commons `EmailValidator` để kiểm tra email chặt chẽ hơn.
- `PhoneNumberRule` kiểm tra số điện thoại (hỗ trợ dấu `+`, số, khoảng trắng, gạch nối, ngoặc). Nếu bạn muốn chuẩn E.164, tôi có thể chuyển logic.

Quick run (tóm tắt)
-------------------
1. Khởi DB schema (trong MySQL):
```powershell
# copy/create DB schema
mysql -u root -p < src/main/resources/sql/create_tables.sql
```
2. Khởi stack (RabbitMQ + MySQL):
```powershell
docker compose up -d
```
3. Publish CSV -> queues (producer):
```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="producer"
```
4. Start consumers (nếu chạy ngoài Docker):
```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="employee-consumer"
mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="order-consumer"
```
5. Chạy transform/load:
```powershell
mvn exec:java -Dexec.mainClass="com.example.etl.Application" -Dexec.args="transform"
```

Tiáº¿p theo: TÃ´i sáº½ táº¡o skeleton Maven project vÃ  cÃ¡c class Java cÆ¡ báº£n.
 f231e4a (ETL demo: add project files, scripts and docs)
