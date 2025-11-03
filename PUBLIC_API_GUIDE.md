# 🌐 Public API - Landing Page

Public API endpoints cho phép truy cập **KHÔNG CẦN AUTHENTICATION** - Dùng cho landing page.

## 🔓 Đặc điểm

- ✅ **Không cần token** - Truy cập trực tiếp
- ✅ **Không ảnh hưởng API hiện tại** - Hoàn toàn độc lập
- ✅ **Dùng raw SQL** - Hiệu năng cao, không cần permissions
- ✅ **Read-only** - Chỉ GET, không POST/PUT/DELETE

## 📋 Danh sách API

### 1. **GET /api/public/stats/**

Trả về số liệu thống kê tổng quan.

**Request:**
```bash
curl http://localhost:8000/api/public/stats/
```

**Response:**
```json
{
  "classes": 80,
  "students": 200,
  "teachers": 105,
  "courses": 20,
  "satisfaction_rate": 98
}
```

**Cách hoạt động:**
```python
# core/views.py
cursor.execute("SELECT COUNT(*) FROM classes")
cursor.execute("SELECT COUNT(*) FROM students")
cursor.execute("SELECT COUNT(*) FROM teachers")
cursor.execute("SELECT COUNT(*) FROM courses")
```

---

### 2. **GET /api/public/courses/**

Trả về danh sách khóa học công khai.

**Request:**
```bash
# Lấy 6 khóa học đầu tiên (mặc định)
curl http://localhost:8000/api/public/courses/

# Lấy 10 khóa học
curl http://localhost:8000/api/public/courses/?limit=10
```

**Response:**
```json
{
  "count": 6,
  "results": [
    {
      "id": "uuid-1",
      "name": "Giao Tiếp Cơ Bản",
      "description": "Khóa học cho người mới bắt đầu",
      "level": "Beginner",
      "total_sessions": 48,
      "fee": 5000000,
      "min_entry_score": null
    },
    ...
  ]
}
```

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | integer | 6 | Số lượng khóa học trả về |

**Cách hoạt động:**
```python
# core/views.py
cursor.execute("""
    SELECT id, name, description, level, total_sessions, fee, min_entry_score
    FROM courses
    ORDER BY name
    LIMIT %s
""", [limit])
```

---

### 3. **GET /api/public/classes/**

Trả về danh sách lớp học **CÔNG KHAI** (is_public=true).

**Request:**
```bash
# Lấy 10 lớp công khai đầu tiên (mặc định)
curl http://localhost:8000/api/public/classes/

# Lấy 20 lớp công khai
curl http://localhost:8000/api/public/classes/?limit=20
```

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": "uuid-1",
      "name": "Class A1",
      "start_date": "2025-01-15",
      "end_date": "2025-06-15",
      "time_slot": "18:30-20:30",
      "weekday": "2,4,6",
      "limit_slot": 20,
      "status": "ongoing",
      "course_name": "Giao Tiếp Cơ Bản",
      "campus_name": "Cơ sở Quận 1"
    },
    ...
  ]
}
```

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | integer | 10 | Số lượng lớp trả về |

**Cách hoạt động:**
```python
# core/views.py
cursor.execute("""
    SELECT c.*, co.name as course_name, ca.name as campus_name
    FROM classes c
    LEFT JOIN courses co ON c.course_id = co.id
    LEFT JOIN campuses ca ON c.campus_id = ca.id
    WHERE c.is_public = true
    ORDER BY c.start_date DESC
    LIMIT %s
""", [limit])
```

---

## 🚀 Cách sử dụng trong Frontend

### JavaScript Fetch

```javascript
// Load stats
const response = await fetch('http://localhost:8000/api/public/stats/');
const data = await response.json();
console.log(data);
// { classes: 80, students: 200, teachers: 105, courses: 20 }

// Load courses
const coursesResp = await fetch('http://localhost:8000/api/public/courses/?limit=6');
const courses = await coursesResp.json();
console.log(courses.results);
// [{ id: '...', name: 'Giao Tiếp Cơ Bản', ... }]
```

### Sử dụng trong Landing Page

```javascript
// frontend/assets/js/landing.js
async function loadStats() {
    const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.PUBLIC_STATS}`);
    const data = await response.json();
    
    // Update UI
    document.getElementById('studentsCount').textContent = data.students;
    document.getElementById('teachersCount').textContent = data.teachers;
    // ...
}

loadStats();
```

---

## 🔒 Bảo mật

### ✅ An toàn vì:

1. **Read-only**: Chỉ SELECT, không INSERT/UPDATE/DELETE
2. **Dữ liệu công khai**: Chỉ trả về thông tin công khai (số liệu, tên khóa học)
3. **Không có thông tin nhạy cảm**: Không trả về email, phone, password, v.v.
4. **Rate limiting**: Có thể thêm throttle nếu cần

### ⚠️ Lưu ý:

- Chỉ dùng cho landing page
- **KHÔNG** dùng để quản lý dữ liệu
- Nếu cần CRUD → Phải login và dùng API có authentication

---

## 📊 So sánh với API có Authentication

| Tính năng | Public API | Authenticated API |
|-----------|------------|-------------------|
| **Endpoint** | `/api/public/*` | `/api/courses/`, `/api/users/*` |
| **Authentication** | ❌ Không cần | ✅ Cần JWT token |
| **Permissions** | ❌ Không có | ✅ Role-based |
| **Methods** | GET only | GET, POST, PUT, DELETE |
| **Use case** | Landing page | Admin dashboard |
| **Data** | Public info only | Full data access |

---

## 🛠️ File liên quan

```
english_center/
├── core/
│   ├── views.py           ← Public API logic
│   └── urls.py            ← Public API routing
├── english_center/
│   └── urls.py            ← Include core.urls
└── PUBLIC_API_GUIDE.md    ← This file

frontend/
├── assets/
│   └── js/
│       ├── config.js      ← API endpoints config
│       └── landing.js     ← Load public API
└── home.html              ← Landing page
```

---

## 🧪 Test API

### Bằng cURL:

```bash
# Test stats
curl http://localhost:8000/api/public/stats/

# Test courses
curl http://localhost:8000/api/public/courses/?limit=3

# Test classes
curl http://localhost:8000/api/public/classes/?limit=5
```

### Bằng Browser:

```
Mở trực tiếp trong browser:
http://localhost:8000/api/public/stats/
http://localhost:8000/api/public/courses/
http://localhost:8000/api/public/classes/
```

### Bằng Postman:

```
GET http://localhost:8000/api/public/stats/
Headers: (không cần)
```

---

## 📈 Performance

### Tối ưu:

✅ **Raw SQL** - Không qua ORM, nhanh hơn  
✅ **Không JOIN phức tạp** - Chỉ JOIN cần thiết  
✅ **LIMIT** - Giới hạn kết quả trả về  
✅ **INDEX** - Đảm bảo các bảng đã có index  

### Có thể thêm Cache:

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # Cache 5 phút
@api_view(['GET'])
@permission_classes([AllowAny])
def public_stats(request):
    # ...
```

---

## 🔧 Mở rộng

### Thêm endpoint mới:

1. **Thêm function trong `core/views.py`:**

```python
@api_view(['GET'])
@permission_classes([AllowAny])
def public_teachers(request):
    """GET /api/public/teachers/ - Danh sách giáo viên"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT t.id, u.fullname, t.specialization, t.level
            FROM teachers t
            JOIN user_accounts u ON t.user_account_id = u.id
            LIMIT 10
        """)
        # ...
    return Response(data)
```

2. **Thêm route trong `core/urls.py`:**

```python
urlpatterns = [
    # ...
    path('public/teachers/', views.public_teachers, name='public-teachers'),
]
```

3. **Thêm vào `config.js`:**

```javascript
PUBLIC_TEACHERS: '/api/public/teachers/',
```

---

## ✅ Kết luận

Public API giúp:
- ✅ Landing page load dữ liệu thật từ database
- ✅ Không cần sửa API hiện tại (có authentication)
- ✅ Không ảnh hưởng đến bảo mật
- ✅ Dễ dàng mở rộng

**Happy Coding! 🚀**

