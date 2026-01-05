# Cấu hình Email để gửi OTP

## Vấn đề
Hiện tại hệ thống đang sử dụng `console.EmailBackend` nên OTP chỉ hiển thị trong terminal/console thay vì gửi email thật.

## Giải pháp
Đã cập nhật `settings.py` để sử dụng SMTP backend. Bạn cần cấu hình thông tin SMTP trong file `.env`.

## Cách cấu hình

### 1. Tạo/Chỉnh sửa file `.env`

Tạo hoặc mở file `.env` trong thư mục `english_center/` (cùng cấp với `manage.py`).

### 2. Thêm cấu hình email vào `.env`

Thêm các dòng sau vào file `.env`:

```env
# Email Configuration (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### 3. Cấu hình cho Gmail

Nếu sử dụng Gmail, bạn cần:

#### Bước 1: Bật 2-Step Verification
1. Vào [Google Account Settings](https://myaccount.google.com/)
2. Security → 2-Step Verification → Bật

#### Bước 2: Tạo App Password
1. Vào [App Passwords](https://myaccount.google.com/apppasswords)
2. Chọn "Mail" và "Other (Custom name)"
3. Nhập tên: "English Center"
4. Copy App Password (16 ký tự, không có khoảng trắng)
5. Dùng App Password này cho `EMAIL_HOST_PASSWORD` trong `.env`

**Lưu ý:** Không dùng mật khẩu Gmail thông thường, phải dùng App Password!

### 4. Cấu hình cho các email provider khác

#### Outlook/Hotmail
```env
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=your-email@outlook.com
```

#### Yahoo Mail
```env
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@yahoo.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@yahoo.com
```

#### Custom SMTP Server
```env
EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### 5. Khởi động lại Django server

Sau khi cấu hình xong, khởi động lại Django server:

```bash
python manage.py runserver
```

### 6. Test gửi email

1. Vào trang "Quên mật khẩu"
2. Nhập email của bạn
3. Click "Gửi Mã OTP"
4. Kiểm tra hộp thư email (cả spam folder)

## Troubleshooting

### Lỗi: "SMTPAuthenticationError"
- Kiểm tra lại `EMAIL_HOST_USER` và `EMAIL_HOST_PASSWORD`
- Với Gmail: Đảm bảo đã dùng App Password, không phải mật khẩu thông thường
- Kiểm tra 2-Step Verification đã bật

### Lỗi: "Connection refused"
- Kiểm tra `EMAIL_HOST` và `EMAIL_PORT` đúng chưa
- Kiểm tra firewall/antivirus có chặn kết nối SMTP không
- Thử dùng `EMAIL_USE_SSL=True` và `EMAIL_PORT=465` thay vì TLS

### Email không đến
- Kiểm tra spam folder
- Kiểm tra `DEFAULT_FROM_EMAIL` đúng chưa
- Xem log Django server để biết lỗi chi tiết

## Lưu ý bảo mật

⚠️ **QUAN TRỌNG:**
- File `.env` chứa thông tin bảo mật, **KHÔNG commit** lên Git
- Đảm bảo `.env` đã có trong `.gitignore`
- Không chia sẻ file `.env` với người khác

## Ví dụ file `.env` hoàn chỉnh

```env
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=englishcenter@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
DEFAULT_FROM_EMAIL=englishcenter@gmail.com

# Các cấu hình khác...
VNPAY_TMN_CODE=your_tmn_code
VNPAY_HASH_SECRET=your_hash_secret
```

