# HƯỚNG DẪN TÍCH HỢP VNPAY

## Tổng quan

VNPay là cổng thanh toán trực tuyến phổ biến tại Việt Nam. Document này hướng dẫn cách tích hợp VNPay vào hệ thống đăng ký lớp học.

---

## Cấu trúc Code

### 1. File: `enrollment/payment_gateway.py`

**Chức năng:** 
- Tạo payment URL từ VNPay
- Verify payment response từ VNPay callback

**Class chính:**
- `VNPayGateway`: Class xử lý tất cả logic liên quan đến VNPay
- `create_vnpay_payment_url()`: Helper function để tạo payment URL

**Các method quan trọng:**
- `create_payment_url()`: Tạo payment URL với các tham số cần thiết
- `verify_payment_response()`: Verify signature và response từ VNPay
- `_create_secure_hash()`: Tạo secure hash (HMAC SHA512) để bảo mật

### 2. File: `enrollment/payment_views.py`

**Chức năng:**
- Xử lý callback từ VNPay (return URL và IPN URL)

**Views:**
- `VNPayReturnView`: Xử lý return URL (sau khi thanh toán, VNPay redirect về)
- `VNPayIPNView`: Xử lý IPN URL (VNPay gọi để notify về kết quả thanh toán)

---

## Cấu hình Settings

Cần thêm các biến sau vào `settings.py` hoặc `.env`:

```python
# VNPay Configuration
VNPAY_TMN_CODE = 'your_tmn_code'  # Mã merchant từ VNPay
VNPAY_HASH_SECRET = 'your_hash_secret'  # Secret key từ VNPay

# Sandbox URL (dùng khi test)
VNPAY_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'

# Production URL (dùng khi deploy)
# VNPAY_URL = 'https://www.vnpayment.vn/paymentv2/vpcpay.html'

# Callback URLs
VNPAY_RETURN_URL = 'http://localhost:8000/api/enrollment/payments/vnpay/return/'
VNPAY_IPN_URL = 'http://localhost:8000/api/enrollment/payments/vnpay/notify/'
```

**Lưu ý:**
- Khi deploy production, cần thay đổi `VNPAY_RETURN_URL` và `VNPAY_IPN_URL` thành domain thực tế
- `VNPAY_RETURN_URL` và `VNPAY_IPN_URL` phải được đăng ký trong VNPay merchant portal

---

## Cách đăng ký tài khoản VNPay Sandbox (Free)

### Bước 1: Truy cập trang đăng ký

1. Mở trình duyệt và truy cập: **https://sandbox.vnpayment.vn/devreg/**
2. Bạn sẽ thấy form đăng ký merchant môi trường test

### Bước 2: Điền thông tin đăng ký

Form đăng ký có các trường sau:

#### **Tên website** (Website name)
- Nhập tên website/dự án của bạn
- Ví dụ: `English Center`, `Trung tâm Anh ngữ ABC`
- **Lưu ý:** Có thể dùng tên bất kỳ, không cần domain thật

#### **Địa chỉ URL** (URL address)
- Nhập URL của website
- **⚠️ QUAN TRỌNG:** VNPay sandbox KHÔNG chấp nhận `http://127.0.0.1:8000`
- **Các lựa chọn hợp lệ:**
  
  **Option 1: Dùng localhost (khuyến nghị cho test)**
  - `http://localhost:8000`
  - ✅ Được chấp nhận
  
  **Option 2: Dùng ngrok (nếu cần callback)**
  - Cài đặt ngrok: https://ngrok.com/
  - Chạy: `ngrok http 8000`
  - Copy URL từ ngrok (ví dụ: `https://abc123.ngrok.io`)
  - Nhập vào form: `https://abc123.ngrok.io`
  - ✅ Hoạt động tốt với callback URLs
  
  **Option 3: Dùng domain thật (nếu có)**
  - `https://yourdomain.com`
  - ✅ Tốt nhất cho production
  
- **Lưu ý:** 
  - ❌ **KHÔNG dùng** `http://127.0.0.1:8000` - sẽ báo lỗi "Không đúng định dạng Url"
  - ✅ **Nên dùng** `http://localhost:8000` cho test local
  - Khi deploy production, cần cập nhật URL thật

#### **Email đăng ký** (Registration email)
- Nhập email của bạn (dùng email thật để nhận thông tin)
- Ví dụ: `your-email@gmail.com`
- **Lưu ý:** Email này sẽ dùng để đăng nhập vào merchant portal

#### **Mật khẩu** (Password)
- Tạo mật khẩu mạnh (ít nhất 8 ký tự)
- **Lưu ý:** Nhớ mật khẩu này để đăng nhập sau

#### **Nhập lại mật khẩu** (Re-enter password)
- Nhập lại mật khẩu vừa tạo (phải khớp)

#### **Mã xác nhận** (Captcha)
- Nhập mã xác nhận hiển thị trong hình
- Nếu không thấy rõ, click vào icon refresh (↻) để làm mới

### Bước 3: Submit form

1. Kiểm tra lại tất cả thông tin đã điền
2. Click nút **"Đăng ký"** (Register)
3. Chờ xử lý (thường mất vài giây)

### Bước 4: Xác nhận email (nếu có)

- VNPay có thể gửi email xác nhận đến địa chỉ email bạn đã đăng ký
- Kiểm tra inbox (và spam folder) và click link xác nhận nếu có

### Bước 5: Đăng nhập vào Merchant Portal

1. Truy cập: **https://sandbox.vnpayment.vn/merchant/**
2. Đăng nhập bằng:
   - **Email**: Email bạn đã đăng ký
   - **Mật khẩu**: Mật khẩu bạn đã tạo

### Bước 6: Lấy thông tin cấu hình

Sau khi đăng nhập vào merchant portal, bạn cần lấy 2 thông tin quan trọng:

#### **1. TMN Code (Terminal Code)**
- Đây là mã merchant của bạn
- Thường hiển thị ở trang dashboard hoặc phần "Thông tin merchant"
- Ví dụ: `ABC123`, `XYZ789`
- **Lưu ý:** Copy và lưu lại mã này

#### **2. Hash Secret (Secret Key)**
- Đây là secret key để tạo secure hash
- Thường hiển thị ở phần "Cấu hình" hoặc "API Settings"
- Ví dụ: `your_secret_key_here_123456`
- **Lưu ý:** 
  - Đây là thông tin bảo mật, không chia sẻ công khai
  - Copy và lưu lại key này

### Bước 7: Lưu thông tin vào file .env

**✅ KHUYẾN NGHỊ:** Lưu thông tin bảo mật vào file `.env` thay vì hardcode trong `settings.py`

#### **1. Tạo file `.env` (nếu chưa có)**

Tạo file `.env` ở thư mục gốc của project (cùng cấp với `manage.py`):

```bash
# Trong thư mục english_center/
touch .env
```

#### **2. Thêm thông tin VNPay vào `.env`**

Mở file `.env` và thêm các dòng sau:

```env
# VNPay Configuration
VNPAY_TMN_CODE=ABC123
VNPAY_HASH_SECRET=your_secret_key_here_123456
VNPAY_URL=https://sandbox.vnpayment.vn/paymentv2/vpcpay.html
VNPAY_RETURN_URL=http://localhost:8000/api/enrollment/payments/vnpay/return/
VNPAY_IPN_URL=http://localhost:8000/api/enrollment/payments/vnpay/notify/
```

**Lưu ý:**
- Thay `ABC123` bằng TMN Code thực tế của bạn
- Thay `your_secret_key_here_123456` bằng Hash Secret thực tế của bạn
- Không có khoảng trắng xung quanh dấu `=`
- Không cần dấu ngoặc kép (trừ khi giá trị có khoảng trắng)

#### **3. Đảm bảo `.env` đã được thêm vào `.gitignore`**

Kiểm tra file `.gitignore` có dòng sau:

```gitignore
# Environment variables
.env
.env.local
.env.*.local
```

**⚠️ QUAN TRỌNG:** 
- **KHÔNG commit** file `.env` lên Git
- File `.env` chứa thông tin bảo mật, chỉ lưu local

#### **4. Tạo file `.env.example` (optional nhưng khuyến nghị)**

Tạo file `.env.example` để làm mẫu cho team (KHÔNG chứa giá trị thật):

```env
# VNPay Configuration
VNPAY_TMN_CODE=your_tmn_code_here
VNPAY_HASH_SECRET=your_hash_secret_here
VNPAY_URL=https://sandbox.vnpayment.vn/paymentv2/vpcpay.html
VNPAY_RETURN_URL=http://localhost:8000/api/enrollment/payments/vnpay/return/
VNPAY_IPN_URL=http://localhost:8000/api/enrollment/payments/vnpay/notify/
```

File này **CÓ THỂ commit** lên Git vì không chứa thông tin thật.

### Bước 7: Cấu hình Callback URLs (nếu cần)

Trong merchant portal, tìm phần "Cấu hình" hoặc "API Settings" và cấu hình:

#### **Return URL**
- URL để VNPay redirect về sau khi thanh toán
- Ví dụ cho local:
  - `http://localhost:8000/api/enrollment/payments/vnpay/return/`
- Ví dụ cho production:
  - `https://yourdomain.com/api/enrollment/payments/vnpay/return/`

#### **IPN URL (Instant Payment Notification)**
- URL để VNPay gọi để notify về kết quả thanh toán
- Ví dụ cho local:
  - `http://localhost:8000/api/enrollment/payments/vnpay/notify/`
- Ví dụ cho production:
  - `https://yourdomain.com/api/enrollment/payments/vnpay/notify/`

**Lưu ý:**
- Với localhost, VNPay sandbox thường không yêu cầu cấu hình callback URLs trước
- Khi deploy production, bắt buộc phải cấu hình callback URLs

### Bước 8: Cấu hình Django Settings để đọc từ .env

**✅ ĐÃ TỰ ĐỘNG CẤU HÌNH:** File `settings.py` đã được cập nhật để đọc VNPay config từ `.env`

Bạn chỉ cần:
1. Tạo file `.env` (nếu chưa có) ở thư mục gốc project
2. Thêm thông tin VNPay vào `.env` (xem Bước 7)
3. Khởi động lại Django server

**Lưu ý:** Không cần sửa `settings.py` nữa, code đã tự động đọc từ `.env`!

---

## Tóm tắt các bước đã làm:

### ✅ Đã hoàn thành:
1. ✅ Đăng ký tài khoản VNPay sandbox
2. ✅ Lấy TMN Code và Hash Secret
3. ✅ Lưu thông tin vào file `.env`
4. ✅ Cấu hình Django đọc từ `.env` (đã tự động)

### 📝 Bạn cần làm:
1. Tạo file `.env` (copy từ `.env.example`)
2. Điền TMN Code và Hash Secret vào `.env`
3. Test kết nối

---

## Cách test (sau khi đã cấu hình):

```python
# VNPay Configuration
VNPAY_TMN_CODE = 'ABC123'  # Thay bằng TMN Code của bạn
VNPAY_HASH_SECRET = 'your_secret_key_here'  # Thay bằng Hash Secret của bạn

# Sandbox URL (dùng cho test)
VNPAY_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'

# Callback URLs (cho local development)
VNPAY_RETURN_URL = 'http://localhost:8000/api/enrollment/payments/vnpay/return/'
VNPAY_IPN_URL = 'http://localhost:8000/api/enrollment/payments/vnpay/notify/'
```

**Hoặc dùng `.env` file:**

```env
VNPAY_TMN_CODE=ABC123
VNPAY_HASH_SECRET=your_secret_key_here
VNPAY_URL=https://sandbox.vnpayment.vn/paymentv2/vpcpay.html
VNPAY_RETURN_URL=http://localhost:8000/api/enrollment/payments/vnpay/return/
VNPAY_IPN_URL=http://localhost:8000/api/enrollment/payments/vnpay/notify/
```

### Bước 9: Test kết nối

1. Khởi động Django server:
   ```bash
   python manage.py runserver
   ```

2. Test tạo enrollment với `payment_method = 'vnpay'`:
   ```bash
   POST /api/enrollment/enrollments/
   {
     "class_id": "uuid",
     "payment_method": "vnpay"
   }
   ```

3. Kiểm tra response có `payment_url`:
   ```json
   {
     "success": true,
     "data": {
       "payment_url": "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?..."
     }
   }
   ```

4. Mở `payment_url` trong browser và test thanh toán

---

## Lưu ý quan trọng

### ✅ Sandbox (Test Environment)
- **Miễn phí** - Không cần phí đăng ký
- **Không cần giấy tờ** - Chỉ cần email
- **Test cards** - VNPay cung cấp thẻ test để test thanh toán
- **Không có tiền thật** - Tất cả giao dịch đều là test

### ⚠️ Production (Môi trường thật)
- **Cần đăng ký riêng** - Không dùng sandbox account
- **Cần giấy tờ pháp lý** - Doanh nghiệp/cá nhân
- **Có phí** - Tùy theo gói dịch vụ
- **Có tiền thật** - Giao dịch thật sẽ trừ tiền thật

### 🔒 Bảo mật
- **Không commit** TMN Code và Hash Secret vào Git
- Dùng `.env` file và thêm vào `.gitignore`
- Chỉ share thông tin này với team member cần thiết

---

## Troubleshooting

### ❌ Lỗi "Không đúng định dạng Url" (Incorrect URL format)

**Nguyên nhân:**
- VNPay sandbox không chấp nhận URL dạng `http://127.0.0.1:8000`
- URL phải có định dạng hợp lệ

**Giải pháp:**
1. **Thay đổi URL trong form:**
   - ❌ **KHÔNG dùng:** `http://127.0.0.1:8000`
   - ✅ **Dùng:** `http://localhost:8000`
   
2. **Hoặc dùng ngrok (nếu cần callback):**
   ```bash
   # Cài ngrok (nếu chưa có)
   # Windows: Download từ https://ngrok.com/
   # Mac: brew install ngrok
   # Linux: Download từ https://ngrok.com/
   
   # Chạy ngrok
   ngrok http 8000
   ```
   - Copy URL từ ngrok (ví dụ: `https://abc123.ngrok.io`)
   - Nhập vào form: `https://abc123.ngrok.io`

3. **Hoặc dùng domain thật (nếu có):**
   - `https://yourdomain.com`

### Lỗi "Email đã tồn tại"
- Email này đã được đăng ký trước đó
- Dùng email khác hoặc đăng nhập với email cũ

### Không nhận được email xác nhận
- Kiểm tra spam folder
- Với sandbox, có thể không cần xác nhận email
- Thử đăng nhập trực tiếp vào merchant portal

### Không tìm thấy TMN Code hoặc Hash Secret
- Đăng nhập vào merchant portal: https://sandbox.vnpayment.vn/merchant/
- Tìm phần "Thông tin merchant" hoặc "API Settings"
- Nếu không thấy, liên hệ support VNPay

### Callback không hoạt động với localhost
- VNPay sandbox có thể không gọi được localhost
- Dùng ngrok để expose local server:
  ```bash
  ngrok http 8000
  ```
- Cập nhật callback URLs với ngrok URL:
  ```
  VNPAY_RETURN_URL=https://your-ngrok-url.ngrok.io/api/enrollment/payments/vnpay/return/
  VNPAY_IPN_URL=https://your-ngrok-url.ngrok.io/api/enrollment/payments/vnpay/notify/
  ```

---

## Tài liệu tham khảo

- **VNPay Sandbox Registration**: https://sandbox.vnpayment.vn/devreg/
- **VNPay Merchant Portal**: https://sandbox.vnpayment.vn/merchant/
- **VNPay API Documentation**: https://sandbox.vnpayment.vn/apis/

---

## Flow Thanh toán

### 1. Student đăng ký lớp học

**Request:**
```json
POST /api/enrollment/enrollments/
{
  "class_id": "uuid",
  "payment_method": "vnpay"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "invoice_status": "pending",
    "amount": 5000000,
    "due_date": "2024-01-17",
    "payment_url": "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?...",
    "confirmation": {
      "message": "...",
      "pdf_download_url": "/api/enrollment/enrollments/{id}/confirmation-pdf/"
    }
  }
}
```

### 2. Student click vào `payment_url`

- Frontend redirect student đến VNPay payment page
- Student nhập thông tin thẻ và thanh toán

### 3. VNPay xử lý thanh toán

- VNPay xử lý giao dịch
- Nếu thành công → Redirect về `VNPAY_RETURN_URL`
- Đồng thời gọi `VNPAY_IPN_URL` để notify server

### 4. Callback xử lý

**Return URL (GET):**
- VNPay redirect student về `GET /api/enrollment/payments/vnpay/return/`
- Server verify signature và cập nhật `invoice_status = 'paid'`
- Response cho student biết kết quả

**IPN URL (POST):**
- VNPay gọi `POST /api/enrollment/payments/vnpay/notify/`
- Server verify signature và cập nhật `invoice_status = 'paid'`
- Response cho VNPay biết đã nhận được notification

---

## Security

### 1. Secure Hash

VNPay sử dụng **HMAC SHA512** để tạo secure hash:
- Tất cả params được sắp xếp theo alphabet
- Tạo query string
- Dùng `hash_secret` để tạo HMAC SHA512
- Thêm `vnp_SecureHash` vào query string

### 2. Verify Response

Khi nhận callback từ VNPay:
1. Lấy `vnp_SecureHash` từ params
2. Tính lại secure hash từ các params còn lại
3. So sánh 2 hash → Nếu khớp → Valid

---

## Testing

### 1. Sandbox Testing

VNPay cung cấp sandbox để test:
- URL: https://sandbox.vnpayment.vn/
- Test cards: VNPay sẽ cung cấp danh sách thẻ test

### 2. Test Flow

1. Tạo enrollment với `payment_method = 'vnpay'`
2. Lấy `payment_url` từ response
3. Mở `payment_url` trong browser
4. Dùng test card để thanh toán
5. Kiểm tra callback được gọi đúng
6. Kiểm tra `invoice_status` được cập nhật thành `'paid'`

---

## Troubleshooting

### 1. Lỗi "Invalid signature"

**Nguyên nhân:**
- `VNPAY_HASH_SECRET` không đúng
- Params không được sắp xếp đúng thứ tự
- Secure hash tính sai

**Giải pháp:**
- Kiểm tra `VNPAY_HASH_SECRET` trong settings
- Kiểm tra code tạo secure hash trong `payment_gateway.py`

### 2. Callback không được gọi

**Nguyên nhân:**
- Callback URLs chưa được cấu hình trong VNPay merchant portal
- Server không accessible từ internet (nếu test local)

**Giải pháp:**
- Cấu hình callback URLs trong VNPay merchant portal
- Dùng ngrok hoặc similar tool để expose local server

### 3. Payment URL không hoạt động

**Nguyên nhân:**
- `VNPAY_TMN_CODE` không đúng
- `VNPAY_URL` không đúng (sandbox vs production)

**Giải pháp:**
- Kiểm tra `VNPAY_TMN_CODE` trong settings
- Kiểm tra `VNPAY_URL` (sandbox cho test, production cho deploy)

---

## Production Deployment

### Checklist:

1. ✅ Đổi `VNPAY_URL` sang production URL
2. ✅ Cập nhật `VNPAY_RETURN_URL` và `VNPAY_IPN_URL` với domain thực tế
3. ✅ Đăng ký callback URLs trong VNPay merchant portal
4. ✅ Test toàn bộ flow trên production
5. ✅ Monitor logs để đảm bảo callbacks được xử lý đúng

---

## Tài liệu tham khảo

- VNPay Documentation: https://sandbox.vnpayment.vn/apis/
- VNPay Merchant Portal: https://sandbox.vnpayment.vn/merchant/

---

**Status:** ✅ Đã implement - Sẵn sàng test và deploy

