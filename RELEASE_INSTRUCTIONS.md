RELEASE INSTRUCTIONS

Mục tiêu: tạo file zip gửi cho giảng viên hoặc upload lên GitHub release.

1) Tạo file zip (đã thực hiện tự động trong repo bằng script PowerShell). Nếu muốn làm tay:

# Từ thư mục dự án trên Windows PowerShell
cd D:\1.ProjectTuHoc\DA_TichHopHeThong\etl-rabbitmq
$files = Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch '\\target\\' -and $_.Name -ne '.env' }
Compress-Archive -Path ($files | ForEach-Object { $_.FullName }) -DestinationPath etl-rabbitmq-release.zip -Force

2) Nội dung nên có trong zip:
- Source code (src/), `pom.xml`, `Dockerfile`, `docker-compose.yml`
- scripts/ (PowerShell orchestration)
- dashboard/ (Flask app)
- README.md, PROGRESS.md, INSTRUCTOR_CHECKLIST.md, RELEASE_INSTRUCTIONS.md

3) Để upload lên GitHub (thủ công):
- Tạo repo mới trên GitHub.
- Thêm remote (nếu chưa có): git remote add origin <url>
- git push -u origin main
- Trên GitHub: tạo Release, attach `etl-rabbitmq-release.zip`.

Lưu ý bảo mật: không commit `.env` chứa mật khẩu thật. Thêm `.env` vào `.gitignore` nếu cần.
