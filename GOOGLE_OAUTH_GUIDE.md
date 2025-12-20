# Google OAuth Integration Guide - English Center

## 📋 Tổng quan

Hệ thống đã được tích hợp Google OAuth để cho phép user đăng ký và đăng nhập bằng tài khoản Google. Flow hoạt động hoàn toàn tự động - nếu user chưa có tài khoản, hệ thống sẽ tự động tạo tài khoản mới với role `student`.

---

## 🔧 Setup Google OAuth Credentials

### Bước 1: Tạo OAuth 2.0 Client ID

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Chọn hoặc tạo một project mới
3. Vào **APIs & Services** → **Credentials**
4. Click **Create Credentials** → **OAuth 2.0 Client ID**
5. Nếu chưa có OAuth consent screen, bạn cần tạo:
   - **User Type**: External (hoặc Internal nếu dùng Google Workspace)
   - **App name**: English Center
   - **User support email**: Email của bạn
   - **Developer contact**: Email của bạn
   - **Scopes**: Thêm `email`, `profile`, `openid`
   - **Test users**: Thêm email test (nếu ở chế độ Testing)

6. Tạo OAuth Client:
   - **Application type**: Web application
   - **Name**: English Center OAuth Client
   - **Authorized redirect URIs**: 
     ```
     http://localhost:8000/api/auth/google/callback/
     https://yourdomain.com/api/auth/google/callback/
     ```

7. Lưu **Client ID** và **Client Secret**

### Bước 2: Cấu hình trong Django

**Option 1: Sử dụng Environment Variables (Khuyến khích)**

Tạo file `.env` trong thư mục root:
```env
GOOGLE_OAUTH2_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=your_client_secret_here
```

Cài đặt `python-decouple` (đã có trong requirements.txt):
```python
# settings.py
from decouple import config

GOOGLE_OAUTH2_CLIENT_ID = config('GOOGLE_OAUTH2_CLIENT_ID', default='')
GOOGLE_OAUTH2_CLIENT_SECRET = config('GOOGLE_OAUTH2_CLIENT_SECRET', default='')
```

**Option 2: Thêm trực tiếp vào settings.py (Chỉ dùng cho development)**

```python
# settings.py
GOOGLE_OAUTH2_CLIENT_ID = 'your_client_id_here.apps.googleusercontent.com'
GOOGLE_OAUTH2_CLIENT_SECRET = 'your_client_secret_here'
```

⚠️ **Lưu ý**: Không commit credentials vào Git!

---

## 🚀 API Endpoints

### 1. Lấy Google OAuth URL

**Endpoint:** `GET /api/auth/google/login/`

**Query Parameters (optional):**
- `redirect_uri`: Custom redirect URI (mặc định: `http://yourdomain/api/auth/google/callback/`)

**Request Example:**
```bash
curl -X GET "http://localhost:8000/api/auth/google/login/?redirect_uri=http://localhost:8000/api/auth/google/callback/"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&response_type=code&scope=openid+email+profile&access_type=offline&prompt=consent",
    "redirect_uri": "http://localhost:8000/api/auth/google/callback/"
  },
  "error": null
}
```

### 2. Xử lý Google OAuth Callback

**Endpoint:** `POST /api/auth/google/callback/`

**Request Body:**
```json
{
  "code": "4/0AeanS...",
  "redirect_uri": "http://localhost:8000/api/auth/google/callback/"
}
```

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/auth/google/callback/" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "4/0AeanS...",
    "redirect_uri": "http://localhost:8000/api/auth/google/callback/"
  }'
```

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": "uuid-here",
      "username": "john.doe",
      "email": "john.doe@gmail.com",
      "fullname": "John Doe",
      "role": "student",
      "role_id": "uuid-here",
      "status": "active",
      "urlImage": "https://lh3.googleusercontent.com/...",
      "phone": null,
      "sex": "other",
      "dob": null
    }
  },
  "error": null
}
```

**Response (Error):**
```json
{
  "success": false,
  "data": null,
  "error": {
    "message": "Email not provided by Google."
  }
}
```

---

## 💻 Frontend Integration Examples

### JavaScript (Vanilla JS)

```javascript
// 1. Lấy Google OAuth URL
async function getGoogleAuthUrl() {
  try {
    const response = await fetch('http://localhost:8000/api/auth/google/login/');
    const data = await response.json();
    
    if (data.success) {
      // Redirect user đến Google login
      window.location.href = data.data.auth_url;
    } else {
      console.error('Error:', data.error);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

// 2. Xử lý callback từ Google
async function handleGoogleCallback(code) {
  try {
    const response = await fetch('http://localhost:8000/api/auth/google/callback/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code: code,
        redirect_uri: 'http://localhost:8000/api/auth/google/callback/'
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Lưu tokens
      localStorage.setItem('access_token', data.data.access_token);
      localStorage.setItem('refresh_token', data.data.refresh_token);
      
      // Lưu user info
      localStorage.setItem('user', JSON.stringify(data.data.user));
      
      // Redirect đến trang chủ
      window.location.href = '/dashboard';
    } else {
      console.error('Error:', data.error);
      alert('Đăng nhập thất bại: ' + data.error.message);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

// 3. Kiểm tra URL có code từ Google không
window.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  
  if (code) {
    // Xử lý callback
    handleGoogleCallback(code);
  }
});

// 4. Button đăng nhập với Google
document.getElementById('google-login-btn').addEventListener('click', () => {
  getGoogleAuthUrl();
});
```

### React Example

```jsx
import React, { useEffect, useState } from 'react';

const GoogleLogin = () => {
  const [loading, setLoading] = useState(false);

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/auth/google/login/');
      const data = await response.json();
      
      if (data.success) {
        // Redirect đến Google
        window.location.href = data.data.auth_url;
      } else {
        alert('Error: ' + data.error.message);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Có lỗi xảy ra');
    } finally {
      setLoading(false);
    }
  };

  // Xử lý callback
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    
    if (code) {
      handleGoogleCallback(code);
    }
  }, []);

  const handleGoogleCallback = async (code) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/google/callback/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: code,
          redirect_uri: window.location.origin + '/api/auth/google/callback/'
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Lưu tokens
        localStorage.setItem('access_token', data.data.access_token);
        localStorage.setItem('refresh_token', data.data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.data.user));
        
        // Redirect
        window.location.href = '/dashboard';
      } else {
        alert('Đăng nhập thất bại: ' + data.error.message);
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <button 
      onClick={handleGoogleLogin} 
      disabled={loading}
      className="google-login-btn"
    >
      {loading ? 'Đang xử lý...' : 'Đăng nhập với Google'}
    </button>
  );
};

export default GoogleLogin;
```

### Vue.js Example

```vue
<template>
  <button @click="handleGoogleLogin" :disabled="loading">
    {{ loading ? 'Đang xử lý...' : 'Đăng nhập với Google' }}
  </button>
</template>

<script>
export default {
  data() {
    return {
      loading: false
    };
  },
  mounted() {
    // Xử lý callback
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    
    if (code) {
      this.handleGoogleCallback(code);
    }
  },
  methods: {
    async handleGoogleLogin() {
      this.loading = true;
      try {
        const response = await fetch('http://localhost:8000/api/auth/google/login/');
        const data = await response.json();
        
        if (data.success) {
          window.location.href = data.data.auth_url;
        } else {
          alert('Error: ' + data.error.message);
        }
      } catch (error) {
        console.error('Error:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async handleGoogleCallback(code) {
      try {
        const response = await fetch('http://localhost:8000/api/auth/google/callback/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code: code,
            redirect_uri: window.location.origin + '/api/auth/google/callback/'
          })
        });
        
        const data = await response.json();
        
        if (data.success) {
          localStorage.setItem('access_token', data.data.access_token);
          localStorage.setItem('refresh_token', data.data.refresh_token);
          localStorage.setItem('user', JSON.stringify(data.data.user));
          
          this.$router.push('/dashboard');
        } else {
          alert('Đăng nhập thất bại: ' + data.error.message);
        }
      } catch (error) {
        console.error('Error:', error);
      }
    }
  }
};
</script>
```

---

## 🔄 Flow hoạt động

```
┌─────────┐
│ Frontend│
└────┬────┘
     │ 1. GET /api/auth/google/login/
     ▼
┌─────────┐
│ Backend │ → Trả về Google OAuth URL
└────┬────┘
     │
     ▼
┌─────────┐
│  Google │ → User đăng nhập Google
└────┬────┘
     │ 2. Redirect với code
     ▼
┌─────────┐
│ Frontend│ → Nhận code từ URL
└────┬────┘
     │ 3. POST /api/auth/google/callback/ với code
     ▼
┌─────────┐
│ Backend │ → Verify code với Google
└────┬────┘
     │ → Lấy user info từ Google
     │ → Tìm/Create user trong DB
     │ → Generate JWT tokens
     ▼
┌─────────┐
│ Frontend│ ← Nhận tokens + user info
└─────────┘
```

---

## 📝 Logic xử lý

### Đăng nhập (User đã tồn tại)
1. Google trả về email
2. Backend tìm user theo email
3. Cập nhật thông tin (avatar, fullname nếu thiếu)
4. Trả về JWT tokens

### Đăng ký (User chưa tồn tại)
1. Google trả về email, name, picture
2. Backend tạo username từ email (phần trước @)
3. Nếu username trùng → thêm số đếm (user1, user2, ...)
4. Tạo UserAccount với role `student`
5. Tạo Student profile với `commitment_status = NOT_COMMITTED`
6. Trả về JWT tokens

---

## ⚠️ Lưu ý quan trọng

1. **Redirect URI phải khớp chính xác** với URI đã đăng ký trong Google Console
2. **OAuth users tự động có role `student`** - không thể đăng ký với role khác qua OAuth
3. **Username được tạo tự động** từ email (có thể trùng → tự động thêm số)
4. **Password ngẫu nhiên** được tạo cho OAuth users (không dùng để đăng nhập)
5. **Email phải được Google verify** - nếu không có email, đăng nhập sẽ thất bại
6. **Avatar từ Google** được lưu vào `urlImage` field

---

## 🧪 Testing

### Test với Postman/Thunder Client

1. **Lấy OAuth URL:**
   ```
   GET http://localhost:8000/api/auth/google/login/
   ```

2. **Copy `auth_url` từ response** → Mở trong browser

3. **Đăng nhập Google** → Copy `code` từ redirect URL

4. **Gửi callback request:**
   ```
   POST http://localhost:8000/api/auth/google/callback/
   Content-Type: application/json
   
   {
     "code": "paste_code_here",
     "redirect_uri": "http://localhost:8000/api/auth/google/callback/"
   }
   ```

### Test với cURL

```bash
# 1. Lấy OAuth URL
curl -X GET "http://localhost:8000/api/auth/google/login/"

# 2. Mở auth_url trong browser, đăng nhập, copy code

# 3. Gửi callback
curl -X POST "http://localhost:8000/api/auth/google/callback/" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "YOUR_CODE_HERE",
    "redirect_uri": "http://localhost:8000/api/auth/google/callback/"
  }'
```

---

## 🐛 Troubleshooting

### Lỗi: "Google OAuth not configured"
- **Nguyên nhân**: Chưa set `GOOGLE_OAUTH2_CLIENT_ID` và `GOOGLE_OAUTH2_CLIENT_SECRET`
- **Giải pháp**: Kiểm tra environment variables hoặc settings.py

### Lỗi: "redirect_uri_mismatch"
- **Nguyên nhân**: Redirect URI không khớp với URI đã đăng ký trong Google Console
- **Giải pháp**: Kiểm tra lại Authorized redirect URIs trong Google Console

### Lỗi: "Email not provided by Google"
- **Nguyên nhân**: Google không trả về email (có thể do scope hoặc user chưa verify email)
- **Giải pháp**: Đảm bảo scope có `email` và user đã verify email với Google

### Lỗi: "Student role not found"
- **Nguyên nhân**: Chưa có role `student` trong database
- **Giải pháp**: Chạy migration hoặc tạo role `student` thủ công

---

## 📚 Tài liệu tham khảo

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
- [Django REST Framework JWT](https://django-rest-framework-simplejwt.readthedocs.io/)

---

## ✅ Checklist Setup

- [ ] Tạo Google Cloud Project
- [ ] Tạo OAuth 2.0 Client ID
- [ ] Thêm Authorized redirect URIs
- [ ] Cấu hình credentials trong Django (env variables hoặc settings)
- [ ] Test endpoint `/api/auth/google/login/`
- [ ] Test full flow với browser
- [ ] Verify user được tạo đúng trong database
- [ ] Test với frontend integration

---

**Chúc bạn tích hợp thành công! 🎉**


