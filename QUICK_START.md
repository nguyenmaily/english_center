# Quick Start - Chạy Frontend & Backend

## ✅ Đã sửa trong Settings.py:

### 1. **ALLOWED_HOSTS**
```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
```

### 2. **CORS - Cho phép Frontend gọi API**
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5500",   # Live Server
    "http://localhost:8080",   # Python HTTP Server  
    "http://localhost:3000",   # React (nếu dùng sau)
]
```

### 3. **Timezone**
```python
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
```

---

## 🚀 Cách chạy:

### **Bước 1: Tạo Superuser (lần đầu tiên)**
```bash
cd english_center
python manage.py createsuperuser
```
Nhập:
- Username: `admin`
- Email: `admin@example.com`
- Password: `admin123` (hoặc gì bạn muốn)

### **Bước 2: Chạy Backend**
```bash
cd english_center
python manage.py runserver
```
✅ Backend chạy tại: `http://localhost:8000`

### **Bước 3: Chạy Frontend**

**Cách 1: Live Server (VSCode) - KHUYẾN NGHỊ**
1. Cài extension "Live Server" trong VSCode
2. Right-click `frontend/index.html`
3. Chọn "Open with Live Server"
4. Tự động mở: `http://127.0.0.1:5500`

**Cách 2: Python HTTP Server**
```bash
# Terminal mới (giữ backend chạy)
cd frontend
python -m http.server 8080
```
✅ Frontend chạy tại: `http://localhost:8080`

### **Bước 4: Login**
1. Mở browser: `http://localhost:5500` hoặc `http://localhost:8080`
2. Nhập username/password vừa tạo
3. Click "Đăng nhập"
4. Vào Dashboard ✨

---

## 🎯 URLs quan trọng:

### Backend:
- API Root: `http://localhost:8000/api/`
- Admin: `http://localhost:8000/admin/`
- Classes API: `http://localhost:8000/api/classes/`
- Sessions API: `http://localhost:8000/api/sessions/`

### Frontend:
- Login: `http://localhost:5500/index.html`
- Dashboard: `http://localhost:5500/dashboard.html`
- Classes: `http://localhost:5500/classes.html`

---

## 🐛 Troubleshooting:

### Lỗi CORS
```
Access to fetch ... has been blocked by CORS policy
```
**Giải pháp:**
1. Kiểm tra `CORS_ALLOWED_ORIGINS` đã có port frontend chưa
2. Restart Django server
3. Hard refresh browser (Ctrl+Shift+R)

### Lỗi 401 Unauthorized
```json
{"detail": "Authentication credentials were not provided"}
```
**Giải pháp:**
1. Đăng xuất và đăng nhập lại
2. Check token trong localStorage (F12 → Application → Local Storage)
3. Token hết hạn sau 60 phút

### Database error
```
django.db.utils.OperationalError: FATAL: database "english_center_db" does not exist
```
**Giải pháp:**
1. Kiểm tra PostgreSQL đã chạy chưa
2. Kiểm tra database name trong settings.py
3. Chạy migrations: `python manage.py migrate`

---

## 📝 Kiểm tra nhanh:

### 1. Backend OK?
```bash
curl http://localhost:8000/api/
```
Nếu thấy response JSON → OK

### 2. Login API OK?
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```
Nếu nhận được `access` token → OK

### 3. Frontend OK?
Mở browser: `http://localhost:5500`
Nếu thấy trang login → OK

---

## ✨ Settings hiện tại (Đơn giản & Hoạt động):

```python
# Development mode
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'english_center_db',
        'USER': 'postgres',
        'PASSWORD': 'nhungtran2708',
    }
}

# CORS - Cho phép frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://localhost:8080",
    "http://localhost:3000",
]

# JWT - Token 60 phút
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# Timezone
TIME_ZONE = 'Asia/Ho_Chi_Minh'
LANGUAGE_CODE = 'vi'
```

---

## 🎉 Done!

Sau khi làm 4 bước trên, bạn có thể:
- ✅ Login vào frontend
- ✅ Xem dashboard với stats
- ✅ Xem danh sách classes
- ✅ Call API từ frontend

**Enjoy coding!** 🚀

