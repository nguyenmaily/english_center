# 🐛 Báo Cáo Lỗi: 400 Bad Request khi đăng ký tài khoản

## 📋 Tóm tắt
API endpoint `/api/auth/register/` trả về lỗi **400 Bad Request** khi frontend gửi request đăng ký tài khoản.

---

## 🔍 Nguyên nhân

### **Vấn đề chính: Thiếu field `password_confirm` trong request body**

Backend yêu cầu field `password_confirm` nhưng frontend không gửi field này, dẫn đến validation error.

---

## 📊 So sánh Backend vs Frontend

### ✅ **Backend yêu cầu** (`authentication/serializers.py`):

```python
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)  # ← BẮT BUỘC
    role = serializers.CharField(write_only=True)
    
    class Meta:
        fields = [
            'username', 'email', 'password', 'password_confirm',  # ← CÓ password_confirm
            'fullname', 'phone', 'sex', 'dob', 'role'
        ]
    
    def validate(self, attrs):
        # Kiểm tra password khớp
        if attrs.get('password') != attrs.get('password_confirm'):  # ← VALIDATE password_confirm
            raise serializers.ValidationError({"password": "Passwords don't match."})
```

**Các field bắt buộc:**
- ✅ `username` (required)
- ✅ `email` (required)
- ✅ `password` (required)
- ✅ **`password_confirm`** (required) ← **THIẾU TRONG FRONTEND**
- ✅ `role` (required, phải là "student")
- ⚪ `fullname` (optional)
- ⚪ `phone` (optional)
- ⚪ `sex` (optional, default: "other")
- ⚪ `dob` (optional)

---

### ❌ **Frontend đang gửi** (`assets/js/register.js`):

```javascript
// Dòng 95-102
body: JSON.stringify({
    fullname: fullname,
    username: username,
    email: email,
    phone: phone,
    password: password,
    // password_confirm: confirmPassword,  ← THIẾU FIELD NÀY
    role: role,
}),
```

**Request body hiện tại:**
```json
{
    "fullname": "...",
    "username": "...",
    "email": "...",
    "phone": "...",
    "password": "...",
    "role": "student"
}
```

**Request body cần có:**
```json
{
    "fullname": "...",
    "username": "...",
    "email": "...",
    "phone": "...",
    "password": "...",
    "password_confirm": "...",  ← CẦN THÊM
    "role": "student"
}
```

---

## 🔧 Giải pháp

### **Bước 1: Sửa file `assets/js/register.js`**

**Vị trí:** Dòng 95-102

**Thay đổi:**
```javascript
// TRƯỚC (SAI):
body: JSON.stringify({
    fullname: fullname,
    username: username,
    email: email,
    phone: phone,
    password: password,
    role: role,
}),

// SAU (ĐÚNG):
body: JSON.stringify({
    fullname: fullname,
    username: username,
    email: email,
    phone: phone,
    password: password,
    password_confirm: confirmPassword,  // ← THÊM DÒNG NÀY
    role: role,
}),
```

---

### **Bước 2: Cải thiện xử lý lỗi (Tùy chọn nhưng khuyến nghị)**

**Vị trí:** Dòng 114-125

**Cải thiện để hiển thị lỗi chi tiết từ backend:**

```javascript
} else {
    // Hiển thị lỗi chi tiết từ backend
    let errorMessage = 'Đăng ký thất bại. Vui lòng thử lại!';
    
    if (data.error) {
        // Format response: { success: false, data: null, error: {...} }
        const errorObj = data.error;
        
        if (typeof errorObj === 'object') {
            // Xử lý object error: { field1: ["message1"], field2: ["message2"] }
            const errorMessages = Object.entries(errorObj)
                .map(([field, messages]) => {
                    const msg = Array.isArray(messages) ? messages[0] : messages;
                    // Format: "field: message"
                    const fieldName = field === 'password' ? 'Mật khẩu' : 
                                     field === 'email' ? 'Email' : 
                                     field === 'username' ? 'Tên đăng nhập' : field;
                    return `${fieldName}: ${msg}`;
                })
                .join('\n');
            
            errorMessage = errorMessages || errorMessage;
        } else if (typeof errorObj === 'string') {
            errorMessage = errorObj;
        }
    } else if (data.detail) {
        errorMessage = data.detail;
    } else if (data.message) {
        errorMessage = data.message;
    }
    
    showAlert(errorMessage, 'danger');
    console.error('Register error details:', data);
}
```

---

## 📝 Response format từ Backend

### **Khi thành công (201 Created):**
```json
{
    "success": true,
    "data": {
        "message": "Student account registered successfully",
        "user": {
            "id": "uuid",
            "username": "...",
            "email": "...",
            "role": "student"
        }
    },
    "error": null
}
```

### **Khi lỗi validation (400 Bad Request):**
```json
{
    "success": false,
    "data": null,
    "error": {
        "password_confirm": ["This field is required."],
        // hoặc
        "password": ["Passwords don't match."],
        // hoặc
        "email": ["Email already registered."],
        // hoặc
        "username": ["Username already exists."]
    }
}
```

### **Khi role không hợp lệ (403 Forbidden):**
```json
{
    "success": false,
    "data": null,
    "error": {
        "role": "Only students can self-register."
    }
}
```

---

## 🧪 Cách test

### **1. Test với Postman/Thunder Client:**

```http
POST http://localhost:8000/api/auth/register/
Content-Type: application/json

{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!@#",
    "password_confirm": "Test123!@#",
    "role": "student",
    "fullname": "Test User",
    "phone": "0123456789"
}
```

### **2. Test các trường hợp lỗi:**

**a) Thiếu `password_confirm`:**
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!@#",
    "role": "student"
}
```
→ **Expected:** 400 với error `{"password_confirm": ["This field is required."]}`

**b) Password không khớp:**
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!@#",
    "password_confirm": "Different123!@#",
    "role": "student"
}
```
→ **Expected:** 400 với error `{"password": ["Passwords don't match."]}`

**c) Email đã tồn tại:**
```json
{
    "username": "newuser",
    "email": "existing@example.com",
    "password": "Test123!@#",
    "password_confirm": "Test123!@#",
    "role": "student"
}
```
→ **Expected:** 400 với error `{"email": ["Email already registered."]}`

---

## 📌 Checklist cho Frontend

- [ ] Thêm field `password_confirm` vào request body (dùng giá trị từ `confirmPassword`)
- [ ] Test đăng ký với password khớp → phải thành công
- [ ] Test đăng ký với password không khớp → phải hiển thị lỗi rõ ràng
- [ ] Test đăng ký với email/username đã tồn tại → phải hiển thị lỗi rõ ràng
- [ ] Cải thiện xử lý lỗi để hiển thị chi tiết từ `data.error`
- [ ] Log error details vào console để debug

---

## 🔗 Tài liệu liên quan

- **Backend Serializer:** `authentication/serializers.py` (dòng 115-168)
- **Backend View:** `authentication/views.py` (dòng 348-400)
- **Frontend Script:** `assets/js/register.js` (dòng 88-103)

---

## ✅ Kết luận

**Nguyên nhân chính:** Frontend không gửi field `password_confirm` trong request body, trong khi backend serializer yêu cầu field này để validate password khớp.

**Giải pháp:** Thêm `password_confirm: confirmPassword` vào request body trong file `register.js`.

**Ưu tiên:** 🔴 **CAO** - Cần sửa ngay để chức năng đăng ký hoạt động.

