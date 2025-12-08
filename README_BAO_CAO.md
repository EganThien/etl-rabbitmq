# Hướng dẫn sử dụng Báo Cáo HTML

## Giới thiệu

File `BAO_CAO_FINAL.html` là phiên bản HTML được định dạng chuyên nghiệp của báo cáo đồ án ETL với RabbitMQ. File này có thể:
- Mở trực tiếp trong trình duyệt web
- Lưu thành PDF
- Copy và paste vào Microsoft Word với format được giữ nguyên

## Cách mở và xem báo cáo

### Option 1: Mở trong trình duyệt

1. Tìm file `BAO_CAO_FINAL.html` trong thư mục dự án
2. Double-click để mở bằng trình duyệt mặc định
3. Hoặc click chuột phải → **Open with** → chọn Chrome/Firefox/Edge

**Khuyến nghị:** Sử dụng Google Chrome để có trải nghiệm tốt nhất

### Option 2: Xem trên GitHub

Nếu file được push lên GitHub, bạn có thể xem trực tiếp bằng cách:
1. Vào repository trên GitHub
2. Click vào file `BAO_CAO_FINAL.html`
3. Click nút **Download** để tải về và xem

## Cách chuyển đổi sang PDF

### Cách 1: Print to PDF (Khuyên dùng)

1. Mở file `BAO_CAO_FINAL.html` trong Google Chrome
2. Nhấn `Ctrl + P` (hoặc `Cmd + P` trên Mac)
3. Trong hộp thoại Print:
   - **Destination:** Chọn "Save as PDF"
   - **Paper size:** A4
   - **Margins:** Default (hoặc Custom: 2cm)
   - **Scale:** 100%
   - **Options:** ✓ Background graphics
4. Click **Save** và chọn vị trí lưu file
5. Đặt tên file: `BAO_CAO_FINAL.pdf`

### Cách 2: Export từ trình duyệt

**Firefox:**
1. Mở file HTML
2. File → Print → Save as PDF

**Edge:**
1. Mở file HTML
2. Ctrl + P → Save as PDF

## Cách chuyển đổi sang Word (.docx)

### Cách 1: Copy/Paste (Đơn giản nhất)

1. Mở file `BAO_CAO_FINAL.html` trong Google Chrome
2. Nhấn `Ctrl + A` để chọn toàn bộ nội dung
3. Nhấn `Ctrl + C` để copy
4. Mở Microsoft Word (tạo document mới)
5. Nhấn `Ctrl + V` để paste
6. Lưu file: File → Save As → chọn định dạng `.docx`

**Lưu ý:** Format sẽ được giữ nguyên bao gồm:
- Font sizes và colors
- Tables với borders
- Code blocks với background
- Headings với styling
- Page breaks

### Cách 2: Qua PDF (Giữ format tốt hơn)

1. Chuyển HTML → PDF (theo hướng dẫn trên)
2. Mở file PDF bằng Microsoft Word
3. Word sẽ tự động convert PDF → Word
4. Lưu lại dưới dạng .docx

### Cách 3: Sử dụng Pandoc (Advanced)

Nếu bạn có Pandoc installed:

```bash
pandoc BAO_CAO_FINAL.html -o BAO_CAO_FINAL.docx
```

## Cách chỉnh sửa báo cáo

### Chỉnh sửa nội dung

1. Mở file `BAO_CAO_FINAL.md` (file Markdown gốc)
2. Chỉnh sửa nội dung cần thiết
3. Chạy lại script convert:

```bash
python3 /tmp/convert_md_to_html.py
```

Hoặc nếu script không còn, tạo lại:

```bash
# Contact repository maintainer for conversion script
```

### Chỉnh sửa styling (CSS)

Mở file `BAO_CAO_FINAL.html` và tìm thẻ `<style>` để thay đổi:

**Thay đổi màu tiêu đề chính:**
```css
h1.title {
    color: #003366;  /* Thay đổi màu này */
}
```

**Thay đổi font size:**
```css
body {
    font-size: 11pt;  /* Thay đổi size này */
}
```

**Thay đổi màu bảng header:**
```css
table.data-table th {
    background: #0066CC;  /* Thay đổi màu background */
}
```

## Tính năng của file HTML

### ✅ Đã được format sẵn

- **Tiêu đề chính:** Font 18pt, bold, màu xanh đậm (#003366), căn giữa
- **CHƯƠNG:** Font 16pt, bold, uppercase, màu đỏ đậm (#CC0000)
- **Tiêu đề cấp 2:** Font 14pt, bold, màu xanh (#0066CC)
- **Tiêu đề cấp 3:** Font 12pt, bold, màu đen
- **Nội dung:** Font 11pt, Times New Roman, line-height 1.6

### ✅ Tables được format đẹp

- Border 1px solid
- Header: Background xanh, text trắng, bold, căn giữa
- Cells: Padding 8px
- Hover effect: Background xanh nhạt
- Không bị tràn trang

### ✅ Code blocks được highlight

- Font Consolas 9pt, monospace
- Background xám nhạt (#f5f5f5)
- Border trái màu xanh
- Không bị vỡ khi in

### ✅ Phân trang rõ ràng

- Mỗi CHƯƠNG tự động xuống trang mới
- Tables và code blocks không bị cắt ngang
- Tối ưu cho in A4

## Kiểm tra chất lượng

### Checklist trước khi submit

- [ ] File HTML mở được trong Chrome/Firefox/Edge
- [ ] Tất cả tables hiển thị đúng với borders
- [ ] Code blocks không bị vỡ layout
- [ ] Headings có màu sắc và font size đúng
- [ ] Phân trang hợp lý (mỗi chương 1 trang mới)
- [ ] In thử 1-2 trang để kiểm tra
- [ ] Copy vào Word giữ nguyên format
- [ ] PDF export ra đẹp, dễ đọc

## Troubleshooting

### Vấn đề: Tables bị vỡ khi in

**Giải pháp:**
- Mở Chrome DevTools (F12)
- Chọn Print Preview
- Kiểm tra scale: nên để 100%
- Nếu vẫn vỡ, giảm font-size table xuống 9pt

### Vấn đề: Mất màu sắc khi print

**Giải pháp:**
- Trong Print dialog, check option "Background graphics"
- Hoặc trong Chrome: More settings → Options → ✓ Background graphics

### Vấn đề: Copy vào Word bị mất format

**Giải pháp:**
- Sử dụng Chrome (không phải Firefox)
- Copy từ Chrome, paste vào Word
- Nếu vẫn mất, thử paste bằng Ctrl+Shift+V rồi format lại

### Vấn đề: File HTML không mở được

**Giải pháp:**
- Kiểm tra file encoding: phải là UTF-8
- Kiểm tra file size: nếu quá lớn (>5MB), có thể bị lỗi
- Thử mở bằng trình duyệt khác

## Thông tin thêm

### Fonts được sử dụng

- **Body text:** Times New Roman (serif)
- **Code blocks:** Consolas, Monaco, Courier New (monospace)
- **Headings:** Times New Roman (serif, bold)

### Colors được sử dụng

- **Tiêu đề chính:** #003366 (Navy Blue)
- **Chương:** #CC0000 (Red)
- **Section headings:** #0066CC (Blue)
- **Table headers:** #0066CC (Blue)
- **Code blocks:** #f5f5f5 (Light Gray background)

### Page layout

- **Paper size:** A4 (210mm × 297mm)
- **Margins:** 2cm (all sides)
- **Line height:** 1.6 (body text)
- **Font size:** 11pt (body), 18pt (title), 16pt (chapter)

## Liên hệ hỗ trợ

Nếu gặp vấn đề khi sử dụng file HTML hoặc cần hỗ trợ chỉnh sửa:
- Mở issue trên GitHub repository
- Liên hệ team phát triển qua email
- Tham khảo tài liệu Markdown gốc: `BAO_CAO_FINAL.md`

---

**Cập nhật lần cuối:** December 2025  
**Version:** 1.0  
**Tương thích:** Chrome 90+, Firefox 88+, Edge 90+, Microsoft Word 2016+
