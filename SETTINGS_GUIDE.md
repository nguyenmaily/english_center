# Django Settings Guide - English Center

## ✅ Đã cấu hình xong

### 1. **CORS (Cross-Origin Resource Sharing)**

Cho phép frontend (HTML/JS) gọi API từ domain khác:

```python
# Development mode - Cho phép TẤT CẢ origins
CORS_ALLOW_ALL_ORIGINS = True  

# Khi deploy production, đổi thành:
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

### 2. **ALLOWED_HOSTS**

```python
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
]
```

### 3. **Timezone & Language**

```python
LANGUAGE_CODE = 'vi'  # Tiếng Việt
TIME_ZONE = 'Asia/Ho_Chi_Minh'  # UTC+7
```

### 4. **JWT Authentication**

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # Token hết hạn sau 60 phút
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # Refresh token hết hạn sau 7 ngày
    'ROTATE_REFRESH_TOKEN': True,                     # Tạo refresh token mới khi refresh
    'BLACKLIST_AFTER_ROTATION': True,                 # Blacklist refresh token cũ
}
```

## 🚀 Chạy Frontend & Backend

### Backend (Django)
```bash
cd english_center
python manage.py runserver
```
→ Chạy tại `http://localhost:8000`

### Frontend (HTML/JS)

**Option 1: Live Server (VSCode)**
- Install extension "Live Server"
- Right-click `index.html` → Open with Live Server
- Tự động mở tại `http://127.0.0.1:5500`

**Option 2: Python HTTP Server**
```bash
cd frontend
python -m http.server 8080
```
→ Mở browser: `http://localhost:8080`

## 🔐 Test API

### 1. Tạo superuser
```bash
python manage.py createsuperuser
```

### 2. Login qua API
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword"}'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "...",
    "username": "admin",
    "email": "admin@example.com"
  }
}
```

### 3. Gọi API với token
```bash
curl -X GET http://localhost:8000/api/classes/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

## 🐛 Troubleshooting

### CORS Error
```
Access to fetch at 'http://localhost:8000/api/...' from origin 'http://localhost:5500' 
has been blocked by CORS policy
```

**Giải pháp:**
1. Kiểm tra `CORS_ALLOW_ALL_ORIGINS = True` trong settings.py
2. Kiểm tra `corsheaders` đã cài: `pip install django-cors-headers`
3. Restart Django server

### 401 Unauthorized
```json
{"detail": "Authentication credentials were not provided."}
```

**Giải pháp:**
1. Kiểm tra token có được gửi trong header không
2. Token có bị hết hạn không (60 phút)
3. Đăng xuất và đăng nhập lại

### 404 Not Found
```
Not Found: /api/classes/
```

**Giải pháp:**
1. Kiểm tra URL endpoint trong `config.js`
2. Kiểm tra Django URLs đã register chưa
3. Xem Django console logs

## 📝 Các Settings Quan Trọng

### REST Framework
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # Require auth mặc định
    ],
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.CustomPagination',
    'PAGE_SIZE': 20,  # Số items mỗi page
}
```

### Database
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'english_center_db',
        'USER': 'postgres',
        'PASSWORD': 'yourpassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🔒 Security Notes

### Development vs Production

**Development (hiện tại):**
```python
DEBUG = True
CORS_ALLOW_ALL_ORIGINS = True
ALLOWED_HOSTS = ['*']
```

**Production (khi deploy):**
```python
DEBUG = False
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = ['https://yourdomain.com']
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECRET_KEY = os.environ.get('SECRET_KEY')  # From environment variable
```

## 📚 Tài liệu tham khảo

- Django CORS: https://pypi.org/project/django-cors-headers/
- Django REST Framework: https://www.django-rest-framework.org/
- Simple JWT: https://django-rest-framework-simplejwt.readthedocs.io/

## ✨ Next Steps

1. ✅ CORS đã enable
2. ✅ JWT authentication đã setup
3. ✅ Timezone đã set Asia/Ho_Chi_Minh
4. ✅ Allowed hosts đã config
5. 🔲 Cần tạo superuser để login
6. 🔲 Test API endpoints
7. 🔲 Deploy lên production server

