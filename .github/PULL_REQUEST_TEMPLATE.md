## Mô tả

Tóm tắt các thay đổi chính (1-2 câu):

- ...

## Checklist

- [ ] Đã chạy `mvn test` và tất cả test pass locally
- [ ] Đã thêm migration DB (nếu schema thay đổi) và document cách áp dụng
- [ ] README.md / CHANGELOG.md đã cập nhật (hướng dẫn migration & run)
- [ ] Đã chạy end-to-end smoke test (script `scripts/run-e2e.ps1` hoặc bằng tay)
- [ ] Có commit riêng cho migration / scripts / docs nếu cần
- [ ] CI workflow (GitHub Actions) đã thêm hoặc không bị lỗi
- [ ] Đã review code / unit tests cho thay đổi logic quan trọng
- [ ] Đã thêm test cho chức năng mới (nếu có)

## Hướng dẫn kiểm thử nhanh

1. Nếu cập nhật schema, chạy migration: `migrations/001-add-phone.sql` hoặc lệnh ALTER TABLE tương ứng.
2. Chạy tests:
```
mvn test
```
3. Chạy end-to-end smoke (PowerShell):
```
.\scripts\run-e2e.ps1
```

## Ghi chú
- Đề nghị reviewer kiểm tra thay đổi migration và chạy E2E trên môi trường dev.
