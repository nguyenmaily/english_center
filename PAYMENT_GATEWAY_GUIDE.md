# Hướng dẫn tích hợp Payment Gateway (VNPay & MoMo)

## 📋 Tổng quan

Hệ thống đã được tích hợp với 2 payment gateway:
- **VNPay**: Thanh toán qua cổng VNPay
- **MoMo**: Thanh toán qua ví điện tử MoMo

## 🔧 Cấu hình

### 1. Cấu hình VNPay

Thêm vào `settings.py` hoặc `.env`:

```python
# VNPay Configuration
VNPAY_TMN_CODE = 'YOUR_TMN_CODE'  # Mã website của bạn trên VNPay
VNPAY_SECRET_KEY = 'YOUR_SECRET_KEY'  # Secret key từ VNPay
VNPAY_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'  # Sandbox
# VNPAY_URL = 'https://www.vnpayment.vn/paymentv2/vpcpay.html'  # Production
VNPAY_RETURN_URL = 'http://localhost:8000/api/enrollment/payments/vnpay/return/'
```

### 2. Cấu hình MoMo

Thêm vào `settings.py` hoặc `.env`:

```python
# MoMo Configuration
MOMO_PARTNER_CODE = 'YOUR_PARTNER_CODE'  # Mã đối tác từ MoMo
MOMO_ACCESS_KEY = 'YOUR_ACCESS_KEY'  # Access key từ MoMo
MOMO_SECRET_KEY = 'YOUR_SECRET_KEY'  # Secret key từ MoMo
MOMO_ENDPOINT = 'https://test-payment.momo.vn/v2/gateway/api/create'  # Sandbox
# MOMO_ENDPOINT = 'https://payment.momo.vn/v2/gateway/api/create'  # Production
MOMO_RETURN_URL = 'http://localhost:8000/api/enrollment/payments/momo/return/'
MOMO_NOTIFY_URL = 'http://localhost:8000/api/enrollment/payments/momo/notify/'
```

## 🚀 Luồng thanh toán

### Bước 1: Học viên đăng ký lớp

```http
POST /api/enrollment/enrollments/
{
  "student_id": "uuid",
  "class_id": "uuid",
  "amount": 5000000,
  "due_date": "2024-02-01"
}
```

### Bước 2: Tạo payment URL

```http
POST /api/enrollment/enrollments/{enrollment_id}/create-payment/
{
  "payment_method": "vnpay",  // hoặc "momo"
  "return_url": "http://localhost:3000/payment-success"  // optional
}
```

Response:
```json
{
  "payment_id": "uuid",
  "payment_url": "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?...",
  "transaction_id": "ENR_xxx_1234567890",
  "expires_at": "2024-01-15T10:30:00Z"
}
```

### Bước 3: Redirect học viên đến payment_url

Frontend redirect user đến `payment_url` để thanh toán.

### Bước 4: Payment Gateway callback

Sau khi thanh toán, payment gateway sẽ gọi callback:
- VNPay: `GET/POST /api/enrollment/payments/vnpay/return/`
- MoMo: `POST /api/enrollment/payments/momo/return/` hoặc `/notify/`

Hệ thống sẽ tự động:
- Verify payment
- Cập nhật Payment status
- Cập nhật Enrollment invoice_status thành "paid"

## 📊 API Endpoints

### 1. Tạo payment URL
```
POST /api/enrollment/enrollments/{id}/create-payment/
```

### 2. Xem lịch sử thanh toán
```
GET /api/enrollment/enrollments/{id}/payment-history/
```

### 3. Xem payments theo enrollment
```
GET /api/enrollment/payments/by-enrollment/?enrollment_id={id}
```

### 4. Payment callbacks (tự động)
```
GET/POST /api/enrollment/payments/vnpay/return/
POST /api/enrollment/payments/momo/return/
POST /api/enrollment/payments/momo/notify/
```

## 🔄 Tự động chuyển pending → overdue

Chạy management command để tự động cập nhật:

```bash
# Dry run (chỉ xem, không cập nhật)
python manage.py update_overdue_enrollments --dry-run

# Thực sự cập nhật
python manage.py update_overdue_enrollments
```

### Cấu hình cron job (Linux/Mac)

Thêm vào crontab để chạy tự động mỗi ngày:

```bash
# Chạy lúc 00:00 mỗi ngày
0 0 * * * cd /path/to/english_center && python manage.py update_overdue_enrollments
```

### Cấu hình Celery (nếu dùng)

Tạo task trong `enrollment/tasks.py`:

```python
from celery import shared_task
from django.core.management import call_command

@shared_task
def update_overdue_enrollments():
    call_command('update_overdue_enrollments')
```

Cấu hình trong `celery.py`:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'update-overdue-enrollments': {
        'task': 'enrollment.tasks.update_overdue_enrollments',
        'schedule': crontab(hour=0, minute=0),  # Mỗi ngày lúc 00:00
    },
}
```

## 📝 Model Payment

Model `Payment` lưu lịch sử thanh toán với các trường:

- `enrollment`: ForeignKey đến Enrollment
- `amount`: Số tiền thanh toán
- `payment_method`: Phương thức (vnpay, momo, cash, bank_transfer)
- `status`: Trạng thái (pending, success, failed, cancelled, refunded)
- `transaction_id`: ID giao dịch từ payment gateway
- `gateway_response`: JSON response từ gateway
- `paid_at`: Thời điểm thanh toán thành công

## ⚠️ Lưu ý

1. **Sandbox vs Production**: 
   - Đổi URL và credentials khi chuyển sang production
   - Test kỹ với sandbox trước

2. **Security**:
   - Không commit secret keys vào git
   - Dùng environment variables hoặc `.env`
   - Verify signature/hash từ payment gateway

3. **Error Handling**:
   - Luôn verify payment trước khi cập nhật status
   - Log tất cả payment transactions
   - Có cơ chế retry cho failed payments

4. **Testing**:
   - Test với sandbox credentials trước
   - Test các trường hợp: success, failed, cancelled
   - Test callback từ payment gateway

## 🔍 Debug

Xem logs để debug:

```python
import logging
logger = logging.getLogger('enrollment.services')
```

Check payment status:
```http
GET /api/enrollment/payments/{payment_id}/
```

Xem enrollment payment info:
```http
GET /api/enrollment/enrollments/{id}/payment-info/
```


