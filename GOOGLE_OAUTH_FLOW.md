# Luồng Đăng Nhập Google OAuth - Chi Tiết

## Tổng Quan

Hệ thống sử dụng Google OAuth 2.0 để cho phép người dùng đăng nhập bằng tài khoản Google của họ. Luồng này bao gồm 2 endpoint chính:
1. **GET `/api/auth/google/login/`** - Lấy URL xác thực Google
2. **GET/POST `/api/auth/google/callback/`** - Xử lý callback từ Google và tạo JWT token

---

## 1. Cấu Hình

### 1.1. Settings Cần Thiết

Trong `english_center/settings.py`, cần cấu hình các biến sau:

```python
# Google OAuth Credentials
GOOGLE_OAUTH2_CLIENT_ID = 'your-google-client-id'
GOOGLE_OAUTH2_CLIENT_SECRET = 'your-google-client-secret'

# Frontend URLs (optional)
FRONTEND_URL = 'http://localhost:5500'  # URL của frontend
FRONTEND_LOGIN_PAGE = '/login.html'      # Trang login của frontend
```

**Lưu ý:** Các settings này có thể được lấy từ file `.env` hoặc environment variables.

### 1.1.1. Cấu Hình Hiện Tại (Từ File .env)

Dự án hiện tại sử dụng file `.env` để lưu trữ thông tin Google OAuth:

```

**Cách đọc trong settings.py:**
```python
from decouple import config

GOOGLE_OAUTH2_CLIENT_ID = config('GOOGLE_OAUTH2_CLIENT_ID', default=None)
GOOGLE_OAUTH2_CLIENT_SECRET = config('GOOGLE_OAUTH2_CLIENT_SECRET', default=None)
```

**⚠️ Cảnh báo bảo mật:**
- File `.env` chứa thông tin nhạy cảm, không nên commit lên Git
- Đảm bảo file `.env` đã được thêm vào `.gitignore`
- Trong production, nên sử dụng environment variables hoặc secret management service

### 1.2. Google Cloud Console Setup

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo OAuth 2.0 Client ID
3. Cấu hình **Authorized redirect URIs**:
   - Development: `http://localhost:8000/api/auth/google/callback/`
   - Production: `https://yourdomain.com/api/auth/google/callback/`

---

## 2. Luồng Đăng Nhập Chi Tiết

### 2.1. Bước 1: Lấy Google OAuth URL

**Endpoint:** `GET /api/auth/google/login/`

**Query Parameters:**
- `redirect_uri` (optional): URI callback sau khi Google xác thực. Mặc định: `{scheme}://{host}/api/auth/google/callback/`
- `frontend_redirect_uri` (optional): URL frontend để redirect về sau khi OAuth thành công

**Request Example:**
```
GET /api/auth/google/login/?frontend_redirect_uri=http://localhost:5500/login.html
```

**Response Success (200 OK):**
```json
{
  "success": true,
  "data": {
    "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&response_type=code&scope=openid%20email%20profile&access_type=offline&prompt=consent&state=http://localhost:5500/login.html",
    "redirect_uri": "http://localhost:8000/api/auth/google/callback/",
    "frontend_redirect_uri": "http://localhost:5500/login.html"
  },
  "error": null
}
```

**Response Error (500 Internal Server Error):**
```json
{
  "success": false,
  "data": null,
  "error": {
    "message": "Google OAuth not configured. Please set GOOGLE_OAUTH2_CLIENT_ID in settings."
  }
}
```

**Xử Lý Trong Code:**

```python
# authentication/views.py - GoogleLoginView.get()

1. Lấy redirect_uri từ query params hoặc dùng default
2. Lấy frontend_redirect_uri từ query params (optional)
3. Kiểm tra GOOGLE_OAUTH2_CLIENT_ID có tồn tại không
4. Tạo OAuth URL với các parameters:
   - client_id: Google Client ID
   - redirect_uri: Backend callback URL
   - response_type: 'code'
   - scope: 'openid email profile'
   - access_type: 'offline' (để lấy refresh token)
   - prompt: 'consent' (yêu cầu user consent)
   - state: frontend_redirect_uri (nếu có)
5. Trả về auth_url cho frontend
```

**OAuth URL Parameters:**
- `client_id`: Google OAuth Client ID
- `redirect_uri`: URL backend sẽ nhận callback từ Google
- `response_type`: `code` (Authorization Code Flow)
- `scope`: `openid email profile` (quyền truy cập)
- `access_type`: `offline` (để nhận refresh token)
- `prompt`: `consent` (yêu cầu user đồng ý)
- `state`: frontend_redirect_uri (để redirect về frontend sau khi xác thực)

---

### 2.2. Bước 2: User Xác Thực Với Google

Frontend redirect user đến `auth_url` từ bước 1. User sẽ:
1. Đăng nhập vào tài khoản Google (nếu chưa đăng nhập)
2. Xem và đồng ý với các quyền được yêu cầu
3. Google redirect về `redirect_uri` với authorization code

**Google Redirect URL:**
```
GET /api/auth/google/callback/?code=4/0AeanS...&state=http://localhost:5500/login.html
```

**Query Parameters từ Google:**
- `code`: Authorization code (dùng một lần, hết hạn sau vài phút)
- `state`: Giá trị đã truyền trong bước 1 (chứa frontend_redirect_uri)
- `error` (nếu có): Lỗi từ Google (user từ chối, lỗi server, ...)

---

### 2.3. Bước 3: Xử Lý Callback - Exchange Code for Token

**Endpoint:** `GET /api/auth/google/callback/` hoặc `POST /api/auth/google/callback/`

#### 3.1. GET Request (Google Redirect)

**Request:**
```
GET /api/auth/google/callback/?code=4/0AeanS...&state=http://localhost:5500/login.html
```

**Xử Lý:**
1. Lấy `code` từ query params
2. Lấy `redirect_uri` từ query params hoặc dùng default
3. Lấy `frontend_redirect_uri` từ `state` parameter
4. Gọi `_process_oauth_callback()` để xử lý
5. Nếu thành công:
   - Redirect về `frontend_redirect_uri` với tokens trong query params
   - Format: `{frontend_redirect_uri}?token={access_token}&refresh_token={refresh_token}&success=true`
6. Nếu thất bại:
   - Redirect về `frontend_redirect_uri` với error trong query params
   - Format: `{frontend_redirect_uri}?error={error_message}&success=false`

#### 3.2. POST Request (Frontend Gửi Code)

**Request Body:**
```json
{
  "code": "4/0AeanS...",
  "redirect_uri": "http://localhost:8000/api/auth/google/callback/"
}
```

**Response Success (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "id": "uuid",
      "username": "user123",
      "email": "user@example.com",
      "fullname": "User Name",
      "urlImage": "https://...",
      "status": "active",
      "roleid": "role-uuid",
      ...
    }
  },
  "error": null
}
```

**Response Error (400 Bad Request):**
```json
{
  "success": false,
  "data": null,
  "error": {
    "message": "Authorization code not provided."
  }
}
```

---

### 2.4. Bước 4: Xử Lý OAuth Callback Chi Tiết

**Method:** `_process_oauth_callback(code, redirect_uri, request)`

#### 4.1. Exchange Authorization Code for Access Token

**API Call:**
```
POST https://oauth2.googleapis.com/token
Content-Type: application/x-www-form-urlencoded

code={code}
&client_id={GOOGLE_OAUTH2_CLIENT_ID}
&client_secret={GOOGLE_OAUTH2_CLIENT_SECRET}
&redirect_uri={redirect_uri}
&grant_type=authorization_code
```

**Response từ Google:**
```json
{
  "access_token": "ya29.a0AfH6SMC...",
  "expires_in": 3599,
  "refresh_token": "1//0g...",
  "scope": "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
  "token_type": "Bearer",
  "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Xử Lý:**
- Sử dụng `urllib` thay vì `requests` để tránh conflict với app `requests` trong project
- Timeout: 30 giây
- Retry logic: Tối đa 2 lần retry với exponential backoff (2s, 4s)
- Xử lý lỗi:
  - HTTPError: Trả về error message từ Google
  - URLError/TimeoutError: Retry hoặc trả về connection timeout error

#### 4.2. Lấy Thông Tin User Từ Google

**API Call:**
```
GET https://www.googleapis.com/oauth2/v2/userinfo
Authorization: Bearer {access_token}
```

**Response từ Google:**
```json
{
  "id": "123456789",
  "email": "user@example.com",
  "verified_email": true,
  "name": "User Name",
  "given_name": "User",
  "family_name": "Name",
  "picture": "https://lh3.googleusercontent.com/...",
  "locale": "vi"
}
```

**Xử Lý:**
- Timeout: 30 giây
- Retry logic: Tối đa 2 lần retry với exponential backoff
- Xử lý encoding: Decode UTF-8 với error handling (errors='replace')
- Validate: Kiểm tra `email` có tồn tại không

#### 4.3. Clean và Normalize Dữ Liệu

**Function:** `clean_text(text)`

**Xử Lý:**
1. Chuyển bytes sang string nếu cần
2. Normalize Unicode (NFKD)
3. Loại bỏ các ký tự không hợp lệ (không thể encode UTF-8)
4. Chỉ giữ lại printable characters và whitespace
5. Fallback: Nếu vẫn lỗi, chỉ giữ lại ASCII characters

**Áp Dụng Cho:**
- `email`
- `full_name`
- `first_name`
- `last_name`

#### 4.4. Tìm Hoặc Tạo User

##### 4.4.1. Tìm User Theo Email

**Query Strategy:**
1. **Bước 1:** Dùng raw SQL để query user theo email (tránh lỗi encoding)
   ```sql
   SELECT id FROM user_accounts WHERE email = %s
   ```
2. **Bước 2:** Nếu tìm thấy user_id, thử dùng ORM để lấy user object
3. **Bước 3:** Nếu ORM lỗi do encoding:
   - Dùng raw SQL để lấy thông tin user
   - Tạo UserAccount object từ raw data (không save)
   - Đánh dấu `user._use_raw_update = True` để dùng raw SQL UPDATE sau này

**Error Handling:**
- Nếu lỗi encoding: Tiếp tục tạo user mới
- Nếu lỗi khác: Re-raise exception

##### 4.4.2. Update User Nếu Đã Tồn Tại

**Các Trường Có Thể Update:**
- `urlImage` (avatar): Nếu user chưa có avatar và Google có picture
- `fullname`: Nếu user chưa có fullname và Google có name

**Update Strategy:**
1. Nếu user có `_use_raw_update = True`:
   - Dùng raw SQL UPDATE
   ```sql
   UPDATE user_accounts 
   SET avatar_url = %s, full_name = %s 
   WHERE id = %s
   ```
2. Nếu không:
   - Dùng ORM `save(update_fields=[...])`
3. Nếu lỗi encoding khi save:
   - Clean fullname lại
   - Dùng raw SQL UPDATE

##### 4.4.3. Tạo User Mới

**Tạo Username:**
1. Lấy phần trước `@` từ email làm base username
2. Kiểm tra username đã tồn tại chưa (dùng raw SQL)
3. Nếu đã tồn tại, thêm số vào cuối: `username1`, `username2`, ...

**Lấy Role:**
- Mặc định: Role `student`
- Query bằng ORM: `Role.objects.get(name='student')`
- Nếu không tìm thấy: Trả về error

**Tạo Password:**
- Tạo password ngẫu nhiên 32 bytes: `secrets.token_urlsafe(32)`
- **Lưu ý:** OAuth users không dùng password này để đăng nhập, chỉ dùng Google OAuth

**Tạo UserAccount:**
```python
user = UserAccount.objects.create_user(
    username=username,
    email=email,
    password=random_password,
    roleid=student_role,
    fullname=full_name,
    urlImage=picture_url,
    status='active'
)
```

**Error Handling:**
- Nếu lỗi encoding khi create:
  - Thử lại với fullname chỉ là ASCII
  - Fallback: Dùng username làm fullname

**Tạo Student Profile:**
```python
Student.objects.create(
    user_account=user,
    commitment_status=Student.CommitmentStatus.NOT_COMMITTED,
    target_score=None
)
```

#### 4.5. Kiểm Tra User Status

**Validation:**
- Kiểm tra `user.status == 'active'`
- Nếu không active: Trả về error `"Account is not active."`

#### 4.6. Generate JWT Tokens

**Sử dụng SimpleJWT:**
```python
from rest_framework_simplejwt.tokens import RefreshToken

refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)
refresh_token = str(refresh)
```

**Token Payload:**
- `access_token`: JWT token để authenticate các API requests
- `refresh_token`: JWT token để refresh access_token khi hết hạn

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAi...",
    "refresh_token": "eyJ0eXAi...",
    "user": {
      "id": "uuid",
      "username": "user123",
      "email": "user@example.com",
      "fullname": "User Name",
      "urlImage": "https://...",
      "status": "active",
      "roleid": "role-uuid",
      ...
    }
  },
  "error": null
}
```

---

## 3. Error Handling

### 3.1. Các Lỗi Có Thể Xảy Ra

#### 3.1.1. Configuration Errors

**Error:** `Google OAuth not configured`
- **Nguyên nhân:** Thiếu `GOOGLE_OAUTH2_CLIENT_ID` hoặc `GOOGLE_OAUTH2_CLIENT_SECRET`
- **Giải pháp:** Cấu hình settings

#### 3.1.2. Google API Errors

**Error:** `Failed to get access token from Google`
- **Nguyên nhân:** 
  - Authorization code không hợp lệ hoặc đã hết hạn
  - Client ID/Secret không đúng
  - Redirect URI không khớp
- **Giải pháp:** Kiểm tra lại cấu hình Google Cloud Console

**Error:** `Failed to get user info from Google`
- **Nguyên nhân:** Access token không hợp lệ hoặc đã hết hạn
- **Giải pháp:** Retry với code mới

**Error:** `Connection timeout when connecting to Google`
- **Nguyên nhân:** Mất kết nối internet hoặc Google API down
- **Giải pháp:** Retry sau vài giây

#### 3.1.3. Database Errors

**Error:** `Encoding/UTF-8 errors`
- **Nguyên nhân:** Dữ liệu từ Google có ký tự không hợp lệ cho PostgreSQL
- **Giải pháp:** 
  - Code tự động clean và normalize dữ liệu
  - Fallback: Dùng raw SQL để tránh ORM encoding issues

**Error:** `Student role not found`
- **Nguyên nhân:** Database chưa có role `student`
- **Giải pháp:** Chạy `python manage.py setup_auth_data` để tạo roles và permissions

#### 3.1.4. User Errors

**Error:** `Email not provided by Google`
- **Nguyên nhân:** User không cấp quyền email hoặc Google không trả về email
- **Giải pháp:** Yêu cầu user cấp quyền email

**Error:** `Account is not active`
- **Nguyên nhân:** User account bị inactive hoặc suspended
- **Giải pháp:** Admin cần activate account

### 3.2. Retry Logic

**Access Token Request:**
- Max retries: 2
- Wait time: Exponential backoff (2s, 4s)
- Timeout: 30 giây mỗi request

**User Info Request:**
- Max retries: 2
- Wait time: Exponential backoff (2s, 4s)
- Timeout: 30 giây mỗi request

---

## 4. Security Considerations

### 4.1. Authorization Code

- Code chỉ dùng một lần
- Code hết hạn sau vài phút
- Code phải được exchange ngay lập tức

### 4.2. Access Token

- Access token được lưu ở frontend (localStorage/sessionStorage)
- Token có thời hạn (thường 1 giờ)
- Token phải được gửi trong header: `Authorization: Bearer {token}`

### 4.3. Refresh Token

- Refresh token được lưu ở frontend
- Dùng để lấy access token mới khi hết hạn
- Refresh token có thời hạn dài hơn (thường 7-30 ngày)

### 4.4. State Parameter

- State parameter được dùng để truyền `frontend_redirect_uri`
- Google sẽ trả về state trong callback
- **Lưu ý:** Nên validate state để tránh CSRF attacks (code hiện tại chưa implement)

### 4.5. Password

- OAuth users có password ngẫu nhiên
- Password không được dùng để đăng nhập thông thường
- Chỉ dùng Google OAuth để đăng nhập

---

## 5. Frontend Integration

### 5.1. Luồng Frontend

1. **User click "Đăng nhập bằng Google"**
2. **Frontend gọi:** `GET /api/auth/google/login/?frontend_redirect_uri={current_url}`
3. **Frontend nhận `auth_url` và redirect user đến Google**
4. **User xác thực với Google**
5. **Google redirect về:** `/api/auth/google/callback/?code=...&state=...`
6. **Backend xử lý và redirect về frontend với tokens:**
   ```
   {frontend_redirect_uri}?token={access_token}&refresh_token={refresh_token}&success=true
   ```
7. **Frontend lấy tokens từ URL và lưu vào localStorage/sessionStorage**
8. **Frontend redirect đến trang chủ hoặc dashboard**

### 5.2. Error Handling Frontend

**Nếu có error:**
```
{frontend_redirect_uri}?error={error_message}&success=false
```

**Frontend cần:**
1. Kiểm tra `success` parameter
2. Nếu `success=false`, hiển thị error message
3. Nếu `success=true`, lưu tokens và redirect

### 5.3. Example Frontend Code (JavaScript)

```javascript
// 1. Lấy Google OAuth URL
async function loginWithGoogle() {
  const frontendRedirectUri = window.location.origin + '/login.html';
  const response = await fetch(
    `/api/auth/google/login/?frontend_redirect_uri=${encodeURIComponent(frontendRedirectUri)}`
  );
  const data = await response.json();
  
  if (data.success) {
    // Redirect đến Google
    window.location.href = data.data.auth_url;
  } else {
    alert('Error: ' + data.error.message);
  }
}

// 2. Xử lý callback từ backend
function handleOAuthCallback() {
  const urlParams = new URLSearchParams(window.location.search);
  const success = urlParams.get('success');
  const token = urlParams.get('token');
  const refreshToken = urlParams.get('refresh_token');
  const error = urlParams.get('error');
  
  if (success === 'true' && token) {
    // Lưu tokens
    localStorage.setItem('access_token', token);
    localStorage.setItem('refresh_token', refreshToken);
    
    // Redirect đến trang chủ
    window.location.href = '/';
  } else if (error) {
    alert('Login failed: ' + error);
  }
}

// Gọi khi trang login.html load
if (window.location.pathname === '/login.html') {
  handleOAuthCallback();
}
```

---

## 6. Testing

### 6.1. Test Cases

#### 6.1.1. Happy Path
1. User click "Đăng nhập bằng Google"
2. Redirect đến Google
3. User đăng nhập và đồng ý
4. Google redirect về callback
5. Backend tạo/tìm user và trả về tokens
6. Frontend lưu tokens và redirect

#### 6.1.2. User Đã Tồn Tại
1. User đã có account với email từ Google
2. Backend tìm thấy user
3. Update avatar/fullname nếu cần
4. Trả về tokens

#### 6.1.3. User Mới
1. User chưa có account
2. Backend tạo UserAccount với role student
3. Backend tạo Student profile
4. Trả về tokens

#### 6.1.4. Error Cases
- Google OAuth not configured
- Authorization code invalid/expired
- Email not provided
- User account inactive
- Connection timeout
- Encoding errors

### 6.2. Manual Testing

**Test với Postman/curl:**

1. **Lấy OAuth URL:**
```bash
curl "http://localhost:8000/api/auth/google/login/?frontend_redirect_uri=http://localhost:5500/login.html"
```

2. **Copy `auth_url` và mở trong browser**

3. **Sau khi Google redirect, copy `code` từ URL**

4. **Test callback với POST:**
```bash
curl -X POST "http://localhost:8000/api/auth/google/callback/" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "4/0AeanS...",
    "redirect_uri": "http://localhost:8000/api/auth/google/callback/"
  }'
```

---

## 7. Logging

### 7.1. Log Messages

Code sử dụng Python `logging` module để log các bước quan trọng:

**Log Levels:**
- `INFO`: Các bước bình thường (tìm user, tạo user, ...)
- `WARNING`: Các vấn đề có thể xử lý được (encoding errors, retry, ...)
- `ERROR`: Các lỗi nghiêm trọng (API errors, database errors, ...)

**Log Format:**
```
[OAUTH] {message}
```

**Ví dụ:**
```
[OAUTH] Starting OAuth callback processing for code: 4/0AeanS...
[OAUTH] Attempting to get access token from Google (attempt 1/3)
[OAUTH] Successfully got access token from Google
[OAUTH] Attempting to get user info from Google (attempt 1/3)
[OAUTH] Successfully got user info from Google
[OAUTH] Looking for user with email: user@example.com
[OAUTH] Step 1: Querying user by email with raw SQL
[OAUTH] Step 2: User found with id: uuid, trying to get user with ORM
[OAUTH] Step 3: User retrieved with ORM: user123
[OAUTH] Updating existing user: user123
[OAUTH] User saved successfully with ORM
```

### 7.2. Debugging

**Để debug, kiểm tra:**
1. Django logs (console hoặc log file)
2. Google Cloud Console - OAuth consent screen logs
3. Network requests trong browser DevTools
4. Database queries (dùng Django Debug Toolbar hoặc logging)

---

## 8. Tóm Tắt Luồng

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │ 1. GET /api/auth/google/login/
       ▼
┌─────────────┐
│   Backend   │
│ GoogleLogin │
│    View     │
└──────┬──────┘
       │ 2. Return auth_url
       ▼
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │ 3. Redirect to Google
       ▼
┌─────────────┐
│   Google    │
│  OAuth 2.0 │
└──────┬──────┘
       │ 4. User login & consent
       │ 5. Redirect with code
       ▼
┌─────────────┐
│   Backend   │
│GoogleCallback│
│    View     │
└──────┬──────┘
       │ 6. Exchange code for token
       │ 7. Get user info
       │ 8. Find/Create user
       │ 9. Generate JWT tokens
       │ 10. Redirect to frontend
       ▼
┌─────────────┐
│   Frontend  │
│ (with tokens│
│  in URL)    │
└─────────────┘
```

---

## 9. Code References

### 9.1. Views

- **GoogleLoginView:** `authentication/views.py:384-450`
- **GoogleCallbackView:** `authentication/views.py:453-986`
- **_process_oauth_callback:** `authentication/views.py:479-906`

### 9.2. Serializers

- **GoogleAuthSerializer:** `authentication/serializers.py:288-293`
- **GoogleCallbackSerializer:** `authentication/serializers.py:296-302`

### 9.3. URLs

- **Google Login:** `authentication/urls.py:27`
- **Google Callback:** `authentication/urls.py:28`

### 9.4. Models

- **UserAccount:** `authentication/models.py:95-150`
- **Student:** `users/models.py:177-250`
- **Role:** `authentication/models.py:9-23`

---

## 10. Best Practices

### 10.1. Security

1. ✅ Sử dụng HTTPS trong production
2. ✅ Validate redirect URIs
3. ⚠️ Nên implement state validation để tránh CSRF
4. ✅ Lưu tokens ở secure storage (httpOnly cookies tốt hơn localStorage)
5. ✅ Implement token refresh logic ở frontend

### 10.2. Error Handling

1. ✅ Retry logic cho network errors
2. ✅ Graceful fallback cho encoding errors
3. ✅ User-friendly error messages
4. ✅ Logging đầy đủ cho debugging

### 10.3. Performance

1. ✅ Timeout cho external API calls
2. ✅ Retry với exponential backoff
3. ✅ Raw SQL cho các query phức tạp (tránh ORM overhead)
4. ✅ Cache role lookup nếu cần

---

## 11. Troubleshooting

### 11.1. Common Issues

**Issue:** `Google OAuth not configured`
- **Fix:** Thêm `GOOGLE_OAUTH2_CLIENT_ID` và `GOOGLE_OAUTH2_CLIENT_SECRET` vào settings

**Issue:** `redirect_uri_mismatch`
- **Fix:** Kiểm tra redirect URI trong Google Cloud Console khớp với backend URL

**Issue:** `invalid_grant`
- **Fix:** Authorization code đã hết hạn hoặc đã được dùng. Lấy code mới.

**Issue:** `Encoding errors`
- **Fix:** Code đã tự động xử lý. Nếu vẫn lỗi, kiểm tra database encoding (UTF-8)

**Issue:** `Student role not found`
- **Fix:** Chạy `python manage.py setup_auth_data` để tạo roles

---

## 12. Future Improvements

1. **State Validation:** Implement CSRF protection với state parameter
2. **Token Storage:** Sử dụng httpOnly cookies thay vì localStorage
3. **Error Recovery:** Implement better error recovery cho encoding issues
4. **Caching:** Cache Google user info để giảm API calls
5. **Rate Limiting:** Implement rate limiting cho OAuth endpoints
6. **Multi-provider:** Support thêm Facebook, GitHub OAuth
7. **Account Linking:** Cho phép link nhiều OAuth providers vào một account

---

**Tài liệu này được tạo tự động dựa trên code hiện tại.**
**Cập nhật lần cuối:** 2025-12-20

