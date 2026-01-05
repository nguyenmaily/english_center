# Hướng dẫn tạo Gmail App Password

## Vấn đề
Gmail không cho phép dùng mật khẩu thông thường để đăng nhập từ ứng dụng bên ngoài. Bạn cần tạo **App Password** (mật khẩu ứng dụng).

## Các bước tạo App Password

### Bước 1: Bật 2-Step Verification (Xác minh 2 bước)

1. Truy cập: https://myaccount.google.com/security
2. Tìm phần **"2-Step Verification"** (Xác minh 2 bước)
3. Click **"Get started"** hoặc **"Bắt đầu"**
4. Làm theo hướng dẫn để bật 2-Step Verification
   - Nhập số điện thoại
   - Nhập mã xác minh được gửi đến điện thoại
   - Xác nhận

### Bước 2: Tạo App Password

1. Truy cập: https://myaccount.google.com/apppasswords
   - Hoặc vào: https://myaccount.google.com/security → Tìm "App passwords" (Mật khẩu ứng dụng)

2. Nếu chưa thấy "App passwords":
   - Đảm bảo đã bật 2-Step Verification (Bước 1)
   - Đợi vài phút sau khi bật 2-Step Verification
   - Refresh trang

3. Tạo App Password mới:
   - Chọn **"Mail"** trong dropdown "Select app"
   - Chọn **"Other (Custom name)"** trong dropdown "Select device"
   - Nhập tên: **"English Center"**
   - Click **"Generate"** (Tạo)

4. Copy App Password:
   - Gmail sẽ hiển thị mật khẩu 16 ký tự
   - Format: `xxxx xxxx xxxx xxxx` (có khoảng trắng)
   - **QUAN TRỌNG:** Copy toàn bộ, bao gồm cả khoảng trắng hoặc bỏ khoảng trắng đều được

### Bước 3: Cập nhật settings.py

Mở file `english_center/english_center/settings.py` và cập nhật:

```python
EMAIL_HOST_USER = 'nt718599@gmail.com'  # Email của bạn
EMAIL_HOST_PASSWORD = 'xxxx xxxx xxxx xxxx'  # Dán App Password vào đây (có thể bỏ khoảng trắng)
DEFAULT_FROM_EMAIL = 'nt718599@gmail.com'  # Email của bạn
```

**Lưu ý:**
- App Password có 16 ký tự
- Có thể có hoặc không có khoảng trắng
- Không phải mật khẩu Gmail thông thường

### Bước 4: Khởi động lại Django server

```bash
# Dừng server hiện tại (Ctrl+C)
# Khởi động lại
python manage.py runserver
```

### Bước 5: Test gửi email

1. Vào trang "Quên mật khẩu"
2. Nhập email
3. Click "Gửi Mã OTP"
4. Kiểm tra hộp thư email (cả spam folder)

## Troubleshooting

### Lỗi: "App passwords" không hiển thị
- **Nguyên nhân:** Chưa bật 2-Step Verification hoặc mới bật chưa đủ lâu
- **Giải pháp:** 
  - Đảm bảo đã bật 2-Step Verification
  - Đợi 5-10 phút
  - Refresh trang
  - Thử đăng nhập lại Google Account

### Lỗi: "Authentication failed" sau khi dùng App Password
- **Nguyên nhân:** 
  - App Password không đúng
  - Copy thiếu ký tự
  - Có khoảng trắng thừa
- **Giải pháp:**
  - Tạo App Password mới
  - Copy cẩn thận, không copy thiếu
  - Thử bỏ khoảng trắng: `xxxxxxxxxxxxxxxx` (16 ký tự liền)

### Lỗi: "Connection refused" hoặc "Connection timeout"
- **Nguyên nhân:** 
  - Firewall chặn
  - Internet không ổn định
  - SMTP settings sai
- **Giải pháp:**
  - Kiểm tra internet
  - Kiểm tra firewall/antivirus
  - Thử dùng `EMAIL_USE_SSL=True` và `EMAIL_PORT=465` thay vì TLS

## Ví dụ cấu hình đúng

```python
# Gmail với App Password
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'  # App Password (16 ký tự)
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

## Lưu ý bảo mật

⚠️ **QUAN TRỌNG:**
- App Password chỉ hiển thị 1 lần khi tạo
- Nếu quên, phải tạo App Password mới
- Không chia sẻ App Password với người khác
- Có thể xóa App Password cũ trong Google Account nếu không dùng nữa

