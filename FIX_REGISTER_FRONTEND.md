# 🔧 Hướng Dẫn Sửa Lỗi 400 - Đăng Ký Tài Khoản

## ⚡ Tóm tắt nhanh

**Lỗi:** API `/api/auth/register/` trả về 400 Bad Request  
**Nguyên nhân:** Frontend thiếu field `password_confirm` trong request  
**File cần sửa:** `assets/js/register.js` (dòng 95-102)

---

## 🎯 Sửa ngay

### **File:** `C:\Frontend\assets\js\register.js`

**Dòng 95-102, thay đổi:**

```javascript
// ❌ TRƯỚC (SAI):
body: JSON.stringify({
    fullname: fullname,
    username: username,
    email: email,
    phone: phone,
    password: password,
    role: role,
}),

// ✅ SAU (ĐÚNG):
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

## 📋 Backend yêu cầu các field sau:

```json
{
    "username": "string (required)",
    "email": "string (required)",
    "password": "string (required)",
    "password_confirm": "string (required)",  ← THIẾU
    "role": "string (required, phải là 'student')",
    "fullname": "string (optional)",
    "phone": "string (optional)",
    "sex": "string (optional)",
    "dob": "date (optional)"
}
```

---

## 🧪 Test sau khi sửa

1. Mở trang đăng ký
2. Điền đầy đủ thông tin
3. Nhập password và confirm password giống nhau
4. Click "Đăng ký"
5. **Expected:** Đăng ký thành công, chuyển đến trang login

---

## 📄 Chi tiết đầy đủ

Xem file `BUG_REPORT_REGISTER_400.md` để biết thêm chi tiết về:
- So sánh backend vs frontend
- Các trường hợp lỗi khác
- Cải thiện xử lý lỗi
- Test cases

