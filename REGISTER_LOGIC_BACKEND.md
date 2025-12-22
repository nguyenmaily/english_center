# 📋 Logic Đăng Ký Tài Khoản - Backend

## 🎯 Tổng Quan

Endpoint: `POST /api/auth/register/`  
View: `RegisterView` (authentication/views.py)  
Serializer: `UserRegistrationSerializer` (authentication/serializers.py)

---

## 🔄 Luồng Xử Lý Chi Tiết

### **Bước 1: Nhận Request** 
📍 `RegisterView.create()` - dòng 355

```python
def create(self, request, *args, **kwargs):
    serializer = self.get_serializer(data=request.data)
```

- Nhận request POST từ frontend
- Lấy dữ liệu từ `request.data`
- Khởi tạo `UserRegistrationSerializer` với dữ liệu

---

### **Bước 2: Validation** 
📍 `UserRegistrationSerializer` - dòng 128-152

#### **2.1. Validate từng field riêng lẻ:**

**a) Validate Username** (dòng 128-131):
```python
def validate_username(self, value):
    if UserAccount.objects.filter(username=value).exists():
        raise serializers.ValidationError("Username already exists.")
    return value
```
- ✅ Kiểm tra username chưa tồn tại trong database
- ❌ Nếu đã tồn tại → Lỗi: "Username already exists."

**b) Validate Email** (dòng 133-136):
```python
def validate_email(self, value):
    if UserAccount.objects.filter(email=value).exists():
        raise serializers.ValidationError("Email already registered.")
    return value
```
- ✅ Kiểm tra email chưa được đăng ký
- ❌ Nếu đã tồn tại → Lỗi: "Email already registered."

**c) Validate Password** (dòng 117):
```python
password = serializers.CharField(write_only=True, validators=[validate_password])
```
- ✅ Sử dụng Django's `validate_password` validator
- ❌ Nếu không đáp ứng yêu cầu → Lỗi từ Django password validator

#### **2.2. Validate toàn bộ (validate method)** (dòng 138-152):

```python
def validate(self, attrs):
    # Kiểm tra password khớp
    if attrs['password'] != attrs['password_confirm']:
        raise serializers.ValidationError({"password": "Passwords don't match."})
    
    # Validate role - Kiểm tra trong database bằng name
    role_name = attrs['role']
    try:
        Role.objects.get(name=role_name)
    except Role.DoesNotExist:
        raise serializers.ValidationError({
            "role": "Invalid role. Must be one of: student, teacher, manager, admin"
        })
    
    return attrs
```

**Kiểm tra:**
- ✅ `password` và `password_confirm` phải khớp nhau
- ✅ `role` phải tồn tại trong bảng `roles` (student, teacher, manager, admin)
- ❌ Nếu không khớp → Lỗi validation

---

### **Bước 3: Kiểm Tra Validation Kết Quả**
📍 `RegisterView.create()` - dòng 357

```python
serializer.is_valid(raise_exception=True)
```

- ✅ Nếu validation thành công → Tiếp tục
- ❌ Nếu validation fail → Raise exception → Trả về 400 Bad Request với error details

---

### **Bước 4: Kiểm Tra Role**
📍 `RegisterView.create()` - dòng 359-365

```python
role_name = serializer.validated_data.get('role', '').lower()
if role_name != 'student':
    return Response({
        'success': False,
        'error': 'Only students can self-register.'
    }, status=status.HTTP_403_FORBIDDEN)
```

**Logic:**
- ✅ Chỉ cho phép đăng ký với role = "student"
- ❌ Nếu role khác → Trả về 403 Forbidden: "Only students can self-register."

**Lý do:** Chỉ học viên mới được tự đăng ký, các role khác (teacher, manager, admin) phải được tạo bởi admin.

---

### **Bước 5: Tạo User Account**
📍 `UserRegistrationSerializer.create()` - dòng 156-168

```python
def create(self, validated_data):
    validated_data.pop('password_confirm')  # Xóa field không cần thiết
    role_name = validated_data.pop('role')  # Lấy role name ra
    
    # Get role object từ database
    role = Role.objects.get(name=role_name)
    
    # Create user với CustomUserManager
    user = UserAccount.objects.create_user(
        roleid=role,  # Gán role
        **validated_data  # Các field khác: username, email, password, fullname, phone, sex, dob
    )
    return user
```

**Chi tiết:**

**5.1. Xử lý dữ liệu:**
- Xóa `password_confirm` (không lưu vào database)
- Lấy `role` name ra và tìm Role object từ database

**5.2. Tạo User qua CustomUserManager** (authentication/models.py - dòng 70-83):

```python
def _create_user(self, username, email, password, **extra_fields):
    # Loại bỏ các field không cần thiết từ AbstractUser
    extra_fields.pop('is_staff', None)
    extra_fields.pop('is_superuser', None)
    extra_fields.pop('is_active', None)
    extra_fields.pop('date_joined', None)
    extra_fields.pop('last_login', None)
    
    # Validate username
    if not username:
        raise ValueError('The username must be set')
    
    # Normalize email
    email = self.normalize_email(email)
    
    # Tạo user instance
    user = self.model(username=username, email=email, **extra_fields)
    
    # Hash password (Django tự động hash)
    user.set_password(password)
    
    # Lưu vào database
    user.save(using=self._db)
    return user
```

**Kết quả:**
- ✅ Tạo record trong bảng `user_accounts`
- ✅ Password được hash tự động bởi Django
- ✅ User có `status = 'active'` (default)
- ✅ User có `roleid` được gán

---

### **Bước 6: Tạo Student Profile**
📍 `RegisterView.create()` - dòng 371-375

```python
Student.objects.create(
    user_account=user,  # Link với user vừa tạo
    commitment_status=Student.CommitmentStatus.NOT_COMMITTED,  # Mặc định: chưa cam kết
    target_score=None  # Chưa có mục tiêu điểm số
)
```

**Chi tiết:**
- ✅ Tạo record trong bảng `students`
- ✅ Link với `user_account` vừa tạo (OneToOne relationship)
- ✅ `commitment_status = 'not_committed'` (mặc định)
- ✅ `target_score = None` (chưa có mục tiêu)

---

### **Bước 7: Trả Về Response**
📍 `RegisterView.create()` - dòng 377-386

```python
return Response({
    'success': True,
    'message': 'Student account registered successfully',
    'user': {
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'role': 'student'
    }
}, status=status.HTTP_201_CREATED)
```

**Response format:**
```json
{
    "success": true,
    "message": "Student account registered successfully",
    "user": {
        "id": "uuid-string",
        "username": "nguyenvana",
        "email": "nguyenvana@example.com",
        "role": "student"
    }
}
```

**Status Code:** `201 Created`

---

## 📊 Sơ Đồ Luồng

```
POST /api/auth/register/
    ↓
RegisterView.create()
    ↓
UserRegistrationSerializer(data=request.data)
    ↓
┌─────────────────────────────────┐
│ VALIDATION                       │
├─────────────────────────────────┤
│ ✓ validate_username()            │
│   → Check unique                 │
│ ✓ validate_email()               │
│   → Check unique                 │
│ ✓ validate_password()            │
│   → Django password validator    │
│ ✓ validate()                     │
│   → Check password match        │
│   → Check role exists            │
└─────────────────────────────────┘
    ↓
serializer.is_valid()
    ↓
┌─────────────────────────────────┐
│ CHECK ROLE = "student"           │
│ → Only students can register     │
└─────────────────────────────────┘
    ↓
serializer.save()
    ↓
┌─────────────────────────────────┐
│ UserRegistrationSerializer       │
│ .create()                        │
├─────────────────────────────────┤
│ 1. Remove password_confirm      │
│ 2. Get Role object               │
│ 3. UserAccount.objects           │
│    .create_user()                │
│    → Hash password               │
│    → Save to user_accounts      │
└─────────────────────────────────┘
    ↓
Student.objects.create()
    ↓
┌─────────────────────────────────┐
│ Create Student Profile           │
│ → Link to user_account           │
│ → commitment_status =            │
│   NOT_COMMITTED                  │
│ → target_score = None            │
└─────────────────────────────────┘
    ↓
Return 201 Created
```

---

## 🔍 Các Trường Hợp Lỗi

### **1. Validation Error (400 Bad Request)**

**a) Username đã tồn tại:**
```json
{
    "username": ["Username already exists."]
}
```

**b) Email đã đăng ký:**
```json
{
    "email": ["Email already registered."]
}
```

**c) Password không khớp:**
```json
{
    "password": ["Passwords don't match."]
}
```

**d) Password không đáp ứng yêu cầu:**
```json
{
    "password": ["This password is too short. It must contain at least 8 characters."]
}
```

**e) Role không hợp lệ:**
```json
{
    "role": ["Invalid role. Must be one of: student, teacher, manager, admin"]
}
```

**f) Thiếu field bắt buộc:**
```json
{
    "username": ["This field is required."],
    "email": ["This field is required."],
    "password": ["This field is required."],
    "password_confirm": ["This field is required."],
    "role": ["This field is required."]
}
```

---

### **2. Forbidden Error (403 Forbidden)**

**Role không phải "student":**
```json
{
    "success": false,
    "error": "Only students can self-register."
}
```

---

## 📝 Các Field Trong Request

### **Bắt buộc:**
- ✅ `username` (string) - Tên đăng nhập, phải unique
- ✅ `email` (string) - Email, phải unique và đúng format
- ✅ `password` (string) - Mật khẩu, phải đáp ứng Django password validator
- ✅ `password_confirm` (string) - Xác nhận mật khẩu, phải khớp với password
- ✅ `role` (string) - Vai trò, phải là "student" và tồn tại trong database

### **Tùy chọn:**
- ⚪ `fullname` (string) - Họ và tên
- ⚪ `phone` (string) - Số điện thoại
- ⚪ `sex` (string) - Giới tính: "male", "female", "other" (default: "other")
- ⚪ `dob` (date) - Ngày sinh (format: YYYY-MM-DD)

---

## 🗄️ Database Changes

Sau khi đăng ký thành công, 2 bảng được tạo/cập nhật:

### **1. Bảng `user_accounts`:**
```sql
INSERT INTO user_accounts (
    id, username, email, password_hash, 
    status, role_id, full_name, phone, 
    sex, dob, created_at, updated_at
) VALUES (
    uuid, 'username', 'email@example.com', 
    'hashed_password', 'active', role_uuid, 
    'Full Name', '0123456789', 'other', 
    NULL, NOW(), NOW()
);
```

### **2. Bảng `students`:**
```sql
INSERT INTO students (
    id, user_account_id, commitment_status, 
    target_score, created_at, updated_at
) VALUES (
    uuid, user_uuid, 'not_committed', 
    NULL, NOW(), NOW()
);
```

---

## 🔐 Bảo Mật

1. **Password Hashing:**
   - Password được hash tự động bởi Django's `set_password()`
   - Không lưu plain text password

2. **Validation:**
   - Username và email phải unique
   - Password phải đáp ứng Django password validator
   - Role phải tồn tại trong database

3. **Permission:**
   - Chỉ cho phép đăng ký role "student"
   - Các role khác phải được tạo bởi admin

---

## 📌 Tóm Tắt

1. **Nhận request** → Parse dữ liệu
2. **Validate** → Username, email, password, role
3. **Kiểm tra role** → Chỉ cho phép "student"
4. **Tạo UserAccount** → Hash password, lưu vào database
5. **Tạo Student profile** → Link với user_account
6. **Trả về response** → 201 Created với thông tin user

**Tổng thời gian:** ~100-200ms (tùy database)

