# Settings.py - Tổng kết & Giải thích

## ❌ **ĐÃ SỬA: Phần THỪA (Duplicate)**

### **Trước (Bị duplicate):**
```python
# Line 186-187: Đã có
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Line 175: Đã có  
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Line 313-318: BỊ DUPLICATE ❌
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### **Sau (Đã xóa duplicate):**
Chỉ giữ lại ở vị trí ban đầu (lines 175, 186-187)

---

## ✅ **ĐÃ BỔ SUNG: Phần THIẾU**

### **1. Swagger/API Documentation Settings**
```python
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
}
```
**Mục đích:** Cấu hình cho drf-yasg (Swagger UI) để test API dễ dàng

**Sử dụng:** 
- Truy cập `http://localhost:8000/swagger/`
- Click "Authorize" → Nhập `Bearer <your-token>`
- Test API trực tiếp trên browser

---

### **2. Logging Configuration**
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {...},  # Log ra console
        'file': {...},     # Log ra file
    },
    'loggers': {
        'django': {...},   # Django logs
    }
}
```

**Mục đích:** Ghi log để debug và monitor

**Sử dụng:**
```python
import logging
logger = logging.getLogger(__name__)

logger.info("User logged in")
logger.error("Something went wrong", exc_info=True)
```

**Logs lưu tại:** `english_center/logs/django.log`

---

### **3. Security Settings (Production)**
```python
# SECURE_SSL_REDIRECT = True        # Redirect HTTP → HTTPS
# SESSION_COOKIE_SECURE = True      # Cookie chỉ gửi qua HTTPS
# CSRF_COOKIE_SECURE = True         # CSRF cookie qua HTTPS
# SECURE_BROWSER_XSS_FILTER = True  # Chống XSS
# SECURE_CONTENT_TYPE_NOSNIFF = True # Chống MIME sniffing
# X_FRAME_OPTIONS = 'DENY'          # Chống clickjacking
```

**Mục đích:** Bảo vệ production server

**Khi nào enable:** Khi deploy lên production với HTTPS/SSL

---

## 📋 **CẤU TRÚC SETTINGS HOÀN CHỈNH**

```
settings.py
├── Basic Settings
│   ├── SECRET_KEY
│   ├── DEBUG = True (Dev) / False (Prod)
│   ├── ALLOWED_HOSTS
│   └── INSTALLED_APPS
│
├── Database
│   └── PostgreSQL config
│
├── Authentication
│   ├── AUTH_USER_MODEL = 'authentication.UserAccount'
│   └── AUTHENTICATION_BACKENDS
│
├── REST Framework
│   ├── JWT Authentication
│   ├── Pagination
│   └── Filters
│
├── JWT Configuration
│   ├── ACCESS_TOKEN_LIFETIME = 60 min
│   └── REFRESH_TOKEN_LIFETIME = 7 days
│
├── CORS Configuration
│   ├── CORS_ALLOW_ALL_ORIGINS = DEBUG
│   ├── CORS_ALLOWED_ORIGINS (whitelist)
│   └── CORS_ALLOW_CREDENTIALS = True
│
├── Static & Media Files
│   ├── STATIC_URL, STATIC_ROOT
│   ├── STATICFILES_DIRS
│   └── MEDIA_URL, MEDIA_ROOT
│
├── Internationalization
│   ├── LANGUAGE_CODE = 'vi'
│   └── TIME_ZONE = 'Asia/Ho_Chi_Minh'
│
├── API Documentation
│   └── SWAGGER_SETTINGS (drf-yasg)
│
├── Email
│   └── EMAIL_BACKEND (console/SMTP)
│
├── Logging
│   └── LOGGING (console + file)
│
└── Security (Production)
    └── SSL/HTTPS settings
```

---

## 🎯 **CHECKLIST ĐẦY ĐỦ**

### **Development (Hiện tại):**
- [x] ✅ DEBUG = True
- [x] ✅ ALLOWED_HOSTS có localhost
- [x] ✅ CORS_ALLOW_ALL_ORIGINS = True (theo DEBUG)
- [x] ✅ Database: PostgreSQL
- [x] ✅ JWT: 60 min access token
- [x] ✅ Timezone: Asia/Ho_Chi_Minh
- [x] ✅ Email: Console backend
- [x] ✅ Logging: Console output
- [x] ✅ Static/Media: Configured
- [x] ✅ Swagger: Có thể enable

### **Production (Cần làm khi deploy):**
- [ ] 🔲 DEBUG = False
- [ ] 🔲 SECRET_KEY từ environment variable
- [ ] 🔲 ALLOWED_HOSTS = ['yourdomain.com']
- [ ] 🔲 CORS_ALLOWED_ORIGINS whitelist
- [ ] 🔲 Email: SMTP config
- [ ] 🔲 Logging: File + monitoring
- [ ] 🔲 Security settings: Enable HTTPS
- [ ] 🔲 Static files: Serve qua nginx/CDN
- [ ] 🔲 Database: Production credentials

---

## 🚀 **NEXT STEPS**

### **1. Tạo folder logs (Optional):**
```bash
cd english_center
mkdir logs
```

### **2. Test Swagger UI (Optional):**
Uncomment trong `urls.py`:
```python
from drf_yasg.views import get_schema_view
# ... 
urlpatterns += [
    path('swagger/', schema_view.with_ui('swagger')),
]
```

### **3. Chạy server:**
```bash
python manage.py runserver
```

### **4. Check logs:**
```bash
# Console logs: Tự động hiện khi chạy server
# File logs: 
tail -f logs/django.log  # Linux/Mac
Get-Content logs/django.log -Tail 50 -Wait  # Windows PowerShell
```

---

## ⚙️ **CÁC SETTINGS QUAN TRỌNG GIẢI THÍCH**

### **1. DEBUG**
```python
DEBUG = True  # Development
DEBUG = False # Production
```
- `True`: Hiển thị error details, allow localhost nếu ALLOWED_HOSTS rỗng
- `False`: Ẩn error, bắt buộc phải có ALLOWED_HOSTS

### **2. CORS_ALLOW_ALL_ORIGINS**
```python
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Tự động theo DEBUG
```
- `True`: Mọi domain đều gọi API được (Development)
- `False`: Chỉ CORS_ALLOWED_ORIGINS mới gọi được (Production)

### **3. JWT TOKEN LIFETIME**
```python
ACCESS_TOKEN_LIFETIME = timedelta(minutes=60)  # Token hết hạn sau 60 phút
REFRESH_TOKEN_LIFETIME = timedelta(days=7)     # Refresh sau 7 ngày
```
- Access token ngắn → An toàn hơn
- Refresh token dài → User không phải login liên tục

### **4. TIMEZONE**
```python
TIME_ZONE = 'Asia/Ho_Chi_Minh'  # UTC+7
USE_TZ = True  # Enable timezone support
```
- Database lưu UTC
- Django tự động convert sang Asia/Ho_Chi_Minh khi hiển thị

---

## 📝 **PRODUCTION DEPLOYMENT CHECKLIST**

Khi deploy lên production server:

```python
# 1. Set environment variables
DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# 2. Update hosts
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# 3. CORS whitelist
CORS_ALLOWED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
]

# 4. Database credentials từ env
DATABASES = {
    'default': {
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
    }
}

# 5. Enable security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# 6. Email SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
```

---

## 🎉 **KẾT LUẬN**

File `settings.py` hiện tại:
- ✅ **Không còn duplicate**
- ✅ **Đầy đủ config cho Development**
- ✅ **Sẵn sàng cho Production** (chỉ cần uncomment)
- ✅ **Có logging để debug**
- ✅ **Có security settings**
- ✅ **Clean & organized**

**Sẵn sàng để chạy!** 🚀

