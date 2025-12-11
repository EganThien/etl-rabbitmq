# HƯỚNG DẪN CHUYỂN ĐỔI SANG WORD

## File đã hoàn thành

✅ **BAO_CAO_HOAN_CHINH.md** 
- Kích thước: 118.57 KB
- Số dòng: 3,435 dòng
- Nội dung: Gộp đầy đủ 9 file (Trang bìa → Kết luận)

---

## Phương pháp 1: Sử dụng Pandoc (Khuyến nghị)

### Bước 1: Cài đặt Pandoc

Download và cài đặt Pandoc từ: https://pandoc.org/installing.html

### Bước 2: Chuyển đổi sang Word

```powershell
cd d:\1.ProjectTuHoc\DA_TichHopHeThong\etl-rabbitmq

pandoc BAO_CAO_HOAN_CHINH.md -o BAO_CAO_HOAN_CHINH.docx `
  --toc `
  --number-sections `
  --highlight-style tango `
  -V geometry:margin=2.5cm `
  -V fontsize=13pt `
  -V mainfont="Times New Roman" `
  -V linestretch=1.4
```

### Bước 3: Format lại trong Word

1. **Font chính**
   - Body text: Times New Roman 13pt hoặc Segoe UI 13pt
   - Line spacing: 1.3-1.4

2. **Headings**
   - Heading 1 (Chương): 18pt, Bold, Uppercase
   - Heading 2 (Mục): 16pt, Bold
   - Heading 3 (Mục con): 14pt, Bold

3. **Table of Contents**
   - References → Table of Contents → Insert
   - Chọn style phù hợp

4. **Code blocks**
   - Font: Consolas 11pt
   - Shading: Light Gray
   - Border: 1pt solid

5. **Tables**
   - Style: Grid Table 4 - Accent 1
   - Header row: Bold

---

## Phương pháp 2: Import trực tiếp vào Word

### Bước 1: Mở Word

File → Open → Chọn `BAO_CAO_HOAN_CHINH.md`

Word sẽ tự động convert markdown

### Bước 2: Apply Styles

1. **Trang bìa**
   - Center align
   - Font size 18-24pt cho tiêu đề chính
   - Font size 14pt cho thông tin sinh viên

2. **Danh mục**
   - Insert → Table of Contents
   - Update lại sau khi format xong

3. **Body text**
   - Select All (Ctrl+A)
   - Font: Times New Roman 13pt
   - Line spacing: 1.4

4. **Headings**
   - Apply Heading styles (Heading 1, 2, 3)
   - Modify styles theo yêu cầu

---

## Phương pháp 3: Sử dụng Online Converter

### Bước 1: Truy cập

https://www.vertopal.com/en/convert/md-to-docx

hoặc

https://cloudconvert.com/md-to-docx

### Bước 2: Upload và Convert

1. Upload file `BAO_CAO_HOAN_CHINH.md`
2. Click "Convert"
3. Download file .docx

### Bước 3: Format lại

Làm tương tự Phương pháp 2

---

## Checklist sau khi chuyển sang Word

### Nội dung

- [ ] Trang bìa đầy đủ thông tin
- [ ] Table of Contents có page numbers
- [ ] Danh mục ký hiệu viết tắt
- [ ] Danh mục hình ảnh/bảng biểu
- [ ] Tất cả 4 chương + Kết luận
- [ ] Tài liệu tham khảo
- [ ] Phụ lục

### Format

- [ ] Font chính: Times New Roman 13-14pt
- [ ] Line spacing: 1.3-1.4
- [ ] Margin: 2.5cm (all sides)
- [ ] Headings có số thứ tự (1., 1.1, 1.1.1)
- [ ] Code blocks có background màu xám nhạt
- [ ] Tables có border và header row
- [ ] Page numbers (footer, right align)

### Hình ảnh

- [ ] Thay placeholder [Hình X.X - ...] bằng screenshot thực tế:
  - Dashboard UI
  - Upload interface
  - Rules management
  - RabbitMQ Management Console
  - Database diagrams (ERD)
  - Architecture diagrams
  - Transform flow diagrams

### Code blocks

- [ ] Syntax highlighting (nếu có)
- [ ] Font: Consolas hoặc Courier New 11pt
- [ ] Background: Shading light gray (5%)
- [ ] Border: 1pt solid

---

## Tips Format Word cho báo cáo học thuật

### 1. Trang bìa

```
[Logo trường - nếu có]

TRƯỜNG ĐẠI HỌC [TÊN TRƯỜNG]
KHOA CÔNG NGHỆ THÔNG TIN

━━━━━━━━━━━━━━━━━━

BÁO CÁO ĐỒ ÁN TỐT NGHIỆP

HỆ THỐNG ETL PHÂN TÁN
VỚI RABBITMQ MESSAGE QUEUE 
VÀ TWO-STAGE DATA VALIDATION

━━━━━━━━━━━━━━━━━━

GVHD: [Tên giảng viên]

Nhóm thực hiện:
[Tên SV1] - MSSV: [Mã]
[Tên SV2] - MSSV: [Mã]

Lớp: [Tên lớp]

TP. Hồ Chí Minh, tháng 12 năm 2025
```

### 2. Header & Footer

**Header** (từ trang 2 trở đi):
- Left: "ĐỒ ÁN HỆ THỐNG ETL PHÂN TÁN"
- Right: "[Tên trường - Khoa CNTT]"
- Font: 11pt, Italic

**Footer**:
- Center: Page numbers
- Font: 11pt

### 3. Table of Contents

```
MỤC LỤC

CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI ................................ 1
  1.1. Giới thiệu đề tài .................................... 1
  1.2. Lý do chọn đề tài .................................... 2
  ...

CHƯƠNG 2: CƠ SỞ LÝ THUYẾT .................................. 15
  2.1. Biểu thức chính quy .................................. 15
  2.2. Design Patterns ...................................... 18
  ...

[Auto-generate bằng References → Table of Contents]
```

### 4. Spacing

- Sau Heading 1: 18pt space after
- Sau Heading 2: 12pt space after
- Sau Heading 3: 6pt space after
- Paragraph: 6pt space after

---

## Lệnh Pandoc nâng cao

### Convert với custom template

```powershell
pandoc BAO_CAO_HOAN_CHINH.md -o BAO_CAO_FINAL.docx `
  --reference-doc=template.docx `
  --toc --toc-depth=3 `
  --number-sections `
  --highlight-style tango `
  --lua-filter=pagebreak.lua
```

### Tạo template.docx

1. Tạo file Word mới
2. Định nghĩa styles: Heading 1, 2, 3, Normal, Code
3. Set font, size, spacing
4. Save as `template.docx`
5. Sử dụng với `--reference-doc=template.docx`

---

## Các công cụ hỗ trợ

1. **Pandoc** (CLI): https://pandoc.org/
2. **Typora** (GUI Markdown editor): https://typora.io/
3. **VSCode Extension**: 
   - Markdown All in One
   - Docs to Markdown
4. **Online Converters**:
   - https://www.vertopal.com/
   - https://cloudconvert.com/

---

## Lưu ý cuối cùng

1. **Backup**: Lưu file .md gốc trước khi convert
2. **Review**: Kiểm tra kỹ sau khi convert (tables, code blocks, special characters)
3. **Images**: Thêm screenshots thực tế thay cho placeholders
4. **References**: Kiểm tra format tài liệu tham khảo
5. **Print Preview**: Xem trước trước khi in/nộp

---

**Chúc bạn hoàn thành tốt báo cáo!** 🎓
