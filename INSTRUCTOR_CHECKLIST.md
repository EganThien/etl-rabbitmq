INSTRUCTOR CHECKLIST

Mục tiêu: kiểm tra tiến độ dự án ETL (CSV -> RabbitMQ -> staging -> transform -> main)

Trước khi chấm:
- Bật Docker Desktop (hoặc Docker Engine).
- Mở PowerShell và chuyển vào thư mục dự án:
  cd D:\1.ProjectTuHoc\DA_TichHopHeThong\etl-rabbitmq
- Kiểm tra file `.env` (không commit mật khẩu thật).

Lệnh nhanh để chạy demo (theo thứ tự):
1) Khởi container
   docker compose up -d --build

2) Nạp schema (đã có script đợi MySQL):
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\load-schema.ps1

3) Chạy producer để publish sample CSV:
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-producer.ps1
   (hoặc: docker compose run --rm app-producer)

4) (Quan sát) Mở RabbitMQ UI: http://localhost:15672 (user/pass theo `.env`, default guest/guest)
   Mở Dashboard: http://localhost:8080

5) Kiểm tra staging dữ liệu:
   docker compose exec -T mysql mysql -u root -prootpassword -e "SELECT * FROM etl_db.staging_employee LIMIT 10;"

6) Chạy transform (chuyển staging -> main):
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-transform.ps1
   (hoặc: docker compose run --rm app-transform)

7) Kiểm tra bảng chính (main):
   docker compose exec -T mysql mysql -u root -prootpassword -e "SELECT COUNT(*) FROM etl_db.main_employee;"

Nội dung cần kiểm tra / tiêu chí chấm
- Rule engine và unit tests: chạy `mvn test` (đã có 8 test passing).
- Consumers: xác nhận staging lưu bản ghi và cột `validation_errors` tồn tại.
- Transform: xác nhận dữ liệu từ staging được chuyển sang `main_*` và staging được xóa.
- Dashboard: hiển thị recent staging rows và `validation_errors`.

Ghi chú cho giảng viên:
- Nếu môi trường có MySQL chạy ở host, cần thay `MYSQL_HOST` trong `.env` và đảm bảo `MYSQL_ROOT_PASSWORD` tương ứng.
- Nếu muốn reset DB mẫu, dừng compose, xóa volume `etl-rabbitmq_mysql-data`, sau đó `docker compose up -d` (chú ý: mất dữ liệu).

Liên hệ: tài liệu và script ở thư mục `scripts/`. Có thể kiểm tra logs bằng `docker compose logs --tail 200`.
