# THIẾT KẾ GIAO DIỆN - XEM LỊCH HỌC / LỊCH DẠY

## LUỒNG ĐI TỔNG QUAN

```
┌─────────────────────────────────────────────────────────┐
│  HỌC SINH (STUDENT)                                    │
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │  Màn hình: Lịch học của tôi                   │     │
│  │  GET /api/sessions/my-schedule/               │     │
│  └───────────────────────────────────────────────┘     │
│              │                                         │
│              ├─→ Xem tất cả buổi học                 │
│              ├─→ Filter theo khoảng thời gian         │
│              └─→ Xem chi tiết từng buổi học           │
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │  Màn hình: Các buổi học sắp tới               │     │
│  │  GET /api/sessions/my-upcoming/              │     │
│  └───────────────────────────────────────────────┘     │
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │  Màn hình: Lịch học của một lớp cụ thể        │     │
│  │  GET /api/enrollment/enrollments/{id}/schedule/│     │
│  └───────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  GIÁO VIÊN (TEACHER)                                    │
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │  Màn hình: Danh sách lớp đang dạy             │     │
│  │  GET /api/classes/my/?teacher_id={id}        │     │
│  └───────────────────────────────────────────────┘     │
│              │                                         │
│              └─→ Xem chi tiết lớp → Xem sessions      │
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │  Màn hình: Các buổi học hôm nay               │     │
│  │  GET /api/sessions/my-today/?teacher_id={id}  │     │
│  └───────────────────────────────────────────────┘     │
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │  Màn hình: Thống kê buổi học                  │     │
│  │  GET /api/sessions/my-stats/?teacher_id={id} │     │
│  └───────────────────────────────────────────────┘     │
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │  Màn hình: Lịch dạy đầy đủ (CẦN BỔ SUNG)     │     │
│  │  GET /api/sessions/my-teaching-schedule/     │     │
│  └───────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## PHẦN 1: HỌC SINH - XEM LỊCH HỌC

### 1.1. Màn hình: Lịch học của tôi (Tổng quan)

**Route:** `/student/my-schedule` hoặc `/student/schedule`

**Chức năng:**
- Hiển thị tất cả các buổi học của học sinh từ tất cả các lớp đã đăng ký
- Có thể filter theo khoảng thời gian (start_date, end_date)
- Hiển thị theo dạng calendar hoặc list

**UI Components:**
- Header: "LỊCH HỌC CỦA TÔI"
- Filter bar:
  - Date picker: Chọn khoảng thời gian (start_date, end_date)
  - Button "Hôm nay", "Tuần này", "Tháng này"
- View toggle: Calendar view / List view
- Danh sách buổi học:
  - Group theo ngày hoặc hiển thị flat list
  - Mỗi buổi học hiển thị:
    - Ngày, giờ (study_date, start_time - end_time)
    - Tên lớp
    - Tên khóa học
    - Giáo viên
    - Phòng học (nếu có)
    - Skill/Kỹ năng (nếu có)
    - Trạng thái: Sắp tới / Đang diễn ra / Đã kết thúc

**API Endpoint:**

**GET /api/sessions/my-schedule/**

**Request:**
```
Method: GET
Headers: Authorization: Bearer {token}
Query Params:
  - student_id: uuid (required)
  - start_date: YYYY-MM-DD (optional)
  - end_date: YYYY-MM-DD (optional)
```

**Response:**
```json
[
  {
    "id": "uuid",
    "study_date": "2024-02-01",
    "start_time": "18:00",
    "end_time": "20:00",
    "duration": "02:00",
    "class_session": {
      "id": "uuid",
      "name": "IELTS Foundation - Lớp 1"
    },
    "class_session_name": "IELTS Foundation - Lớp 1",
    "teacher": {
      "id": "uuid",
      "name": "Nguyễn Văn A"
    },
    "teacher_name": "Nguyễn Văn A",
    "room": {
      "id": "uuid",
      "name": "Phòng 101"
    },
    "room_name": "Phòng 101",
    "skill": null,
    "check_in": null,
    "check_out": null,
    "is_checked_in": false,
    "is_checked_out": false,
    "attendance_summary": null
  }
]
```

**Logic Backend:**
1. Lấy `student_id` từ query params
2. Tìm tất cả `class_id` mà học sinh đã đăng ký (từ bảng `enrollments`)
3. Lấy tất cả `sessions` của các lớp đó
4. Filter theo `start_date` và `end_date` nếu có
5. Sắp xếp theo `study_date`, `start_time`

---

### 1.2. Màn hình: Các buổi học sắp tới

**Route:** `/student/upcoming-sessions`

**Chức năng:**
- Hiển thị các buổi học từ hôm nay trở đi
- Giúp học sinh biết lịch học gần nhất

**UI Components:**
- Header: "CÁC BUỔI HỌC SẮP TỚI"
- Danh sách buổi học (tương tự màn 1.1)
- Badge "Hôm nay" cho các buổi học hôm nay
- Countdown timer cho buổi học tiếp theo

**API Endpoint:**

**GET /api/sessions/my-upcoming/**

**Request:**
```
Method: GET
Headers: Authorization: Bearer {token}
Query Params:
  - student_id: uuid (required)
```

**Response:**
```json
[
  {
    "id": "uuid",
    "study_date": "2024-02-01",
    "start_time": "18:00",
    "end_time": "20:00",
    "class_session_name": "IELTS Foundation - Lớp 1",
    "teacher_name": "Nguyễn Văn A",
    "room_name": "Phòng 101"
  }
]
```

**Logic Backend:**
1. Lấy `student_id` từ query params
2. Tìm tất cả `class_id` mà học sinh đã đăng ký
3. Lấy `sessions` với `study_date >= today`
4. Sắp xếp theo `study_date`, `start_time`

---

### 1.3. Màn hình: Lịch học chi tiết của một lớp

**Route:** `/student/class/{class_id}/schedule` hoặc `/enrollment/{enrollment_id}/schedule`

**Chức năng:**
- Hiển thị lịch học chi tiết của một lớp cụ thể
- Hiển thị theo tuần (by_week) hoặc theo ngày (by_date)
- Tự động tính toán schedule nếu sessions chưa được tạo trong DB

**UI Components:**
- Header với nút Back
- Thông tin lớp:
  - Tên lớp
  - Tên khóa học + Level badge
  - Giáo viên
  - Cơ sở
  - Ngày bắt đầu/kết thúc
- Tabs: "Theo tuần" / "Theo ngày"
- Summary:
  - Tổng số buổi học
  - Số buổi đã hoàn thành
  - Số buổi sắp tới
  - Buổi học tiếp theo
- Danh sách sessions:
  - Group theo tuần hoặc ngày
  - Mỗi session hiển thị: ngày, giờ, skill, room

**API Endpoint:**

**GET /api/enrollment/enrollments/{enrollment_id}/schedule/**

**Request:**
```
Method: GET
Headers: Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "enrollment_id": "uuid",
    "class": {
      "id": "uuid",
      "name": "IELTS Foundation - Lớp 1",
      "course": {
        "id": "uuid",
        "name": "IELTS Foundation",
        "level": "intermediate"
      },
      "teacher": {
        "id": "uuid",
        "name": "Nguyễn Văn A"
      },
      "campus": {
        "id": "uuid",
        "name": "Cơ sở Quận 1"
      },
      "start_date": "2024-02-01",
      "end_date": "2024-05-01",
      "weekday": [2, 4, 6],
      "time_slot": "18:00-20:00"
    },
    "schedule": {
      "by_week": [
        {
          "week": 1,
          "start_date": "2024-02-01",
          "end_date": "2024-02-07",
          "sessions": [
            {
              "id": "uuid",
              "study_date": "2024-02-01",
              "start_time": "18:00",
              "end_time": "20:00",
              "skill": null,
              "room": null,
              "teacher": {
                "id": "uuid",
                "name": "Nguyễn Văn A"
              }
            }
          ]
        }
      ],
      "by_date": [
        {
          "date": "2024-02-01",
          "sessions": [
            {
              "id": "uuid",
              "study_date": "2024-02-01",
              "start_time": "18:00",
              "end_time": "20:00"
            }
          ]
        }
      ]
    },
    "summary": {
      "total_sessions": 36,
      "completed_sessions": 0,
      "upcoming_sessions": 36,
      "next_session": {
        "date": "2024-02-01",
        "start_time": "18:00",
        "end_time": "20:00",
        "skill": null,
        "room": null
      }
    },
    "note": "Sessions chưa được tạo trong database, schedule được tính toán dựa trên thông tin lớp"
  }
}
```

**Logic Backend:**
1. Kiểm tra quyền: chỉ học sinh đã đăng ký mới xem được
2. Lấy `enrollment` và `class` object
3. Kiểm tra sessions trong DB:
   - Nếu có sessions → Dùng sessions từ DB
   - Nếu không có → Tính toán từ `class.weekday`, `class.time_slot`, `class.start_date`, `class.end_date`
4. Group sessions theo tuần (by_week) và theo ngày (by_date)
5. Tính summary: tổng số buổi, số buổi đã hoàn thành, số buổi sắp tới, buổi học tiếp theo

**Lưu ý quan trọng:**
- API tự động tính toán schedule nếu sessions chưa được tạo trong DB
- Schedule được tính dựa trên:
  - `weekday`: [2, 4, 6] = Thứ 3, 5, 7
  - `time_slot`: "18:00-20:00"
  - `start_date` và `end_date`

---

## PHẦN 2: GIÁO VIÊN - XEM LỊCH DẠY

### 2.1. Màn hình: Danh sách lớp đang dạy

**Route:** `/teacher/my-classes`

**Chức năng:**
- Hiển thị danh sách tất cả lớp giáo viên đang dạy
- Filter theo trạng thái: planned, ongoing, finished
- Xem chi tiết từng lớp và lịch dạy của lớp đó

**UI Components:**
- Header: "LỊCH DẠY CỦA TÔI"
- Filter tabs: "Tất cả" / "Sắp bắt đầu" / "Đang dạy" / "Đã kết thúc"
- Danh sách lớp dạng Card/List:
  - Tên lớp
  - Tên khóa học + Level badge
  - Ngày bắt đầu/kết thúc
  - Lịch học (weekday + time_slot)
  - Số học viên hiện tại / Giới hạn
  - Trạng thái lớp
  - Button "Xem chi tiết" → Navigate đến màn chi tiết lớp

**API Endpoint:**

**GET /api/classes/my/**

**Request:**
```
Method: GET
Headers: Authorization: Bearer {token}
Query Params:
  - teacher_id: uuid (required)
```

**Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "name": "IELTS Foundation - Lớp 1",
      "start_date": "2024-02-01",
      "end_date": "2024-05-01",
      "status": "ongoing",
      "course": "uuid",
      "course_name": "IELTS Foundation",
      "teacher": "uuid",
      "teacher_name": "Nguyễn Văn A",
      "campus": "uuid",
      "campus_name": "Cơ sở Quận 1",
      "weekday": [2, 4, 6],
      "time_slot": "18:00-20:00",
      "current_student_count": 15,
      "limit_slot": 20,
      "enrollment_count": 15,
      "is_full": false,
      "available_slots": 5
    }
  ]
}
```

**Logic Backend:**
1. Lấy `teacher_id` từ query params
2. Filter `Class.objects.filter(teacher_id=teacher_id)`
3. Sắp xếp theo `start_date` (mới nhất trước)

---

### 2.2. Màn hình: Các buổi học hôm nay

**Route:** `/teacher/today-sessions`

**Chức năng:**
- Hiển thị các buổi học hôm nay của giáo viên
- Giúp giáo viên biết lịch dạy trong ngày
- Có thể check-in/check-out từ màn hình này

**UI Components:**
- Header: "LỊCH DẠY HÔM NAY"
- Date display: Hiển thị ngày hôm nay
- Danh sách buổi học:
  - Giờ bắt đầu/kết thúc
  - Tên lớp
  - Số học viên
  - Phòng học
  - Button "Check-in" / "Check-out" (nếu chưa check)
  - Badge trạng thái: "Chưa bắt đầu" / "Đang diễn ra" / "Đã kết thúc"
- Summary: Tổng số buổi học hôm nay

**API Endpoint:**

**GET /api/sessions/my-today/**

**Request:**
```
Method: GET
Headers: Authorization: Bearer {token}
Query Params:
  - teacher_id: uuid (required)
```

**Response:**
```json
[
  {
    "id": "uuid",
    "study_date": "2024-02-01",
    "start_time": "18:00",
    "end_time": "20:00",
    "class_session": {
      "id": "uuid",
      "name": "IELTS Foundation - Lớp 1"
    },
    "class_session_name": "IELTS Foundation - Lớp 1",
    "teacher_name": "Nguyễn Văn A",
    "room_name": "Phòng 101",
    "check_in": null,
    "check_out": null,
    "is_checked_in": false,
    "is_checked_out": false,
    "attendance_summary": {
      "total": 15,
      "present": 12,
      "absent": 2,
      "late": 1,
      "excused": 0
    }
  }
]
```

**Logic Backend:**
1. Lấy `teacher_id` từ query params
2. Filter `Session.objects.filter(teacher_id=teacher_id, study_date=today)`
3. Sắp xếp theo `start_time`

---

### 2.3. Màn hình: Thống kê buổi học

**Route:** `/teacher/session-stats`

**Chức năng:**
- Hiển thị thống kê về các buổi học của giáo viên
- Tỷ lệ check-in, check-out
- Có thể filter theo khoảng thời gian

**UI Components:**
- Header: "THỐNG KÊ BUỔI HỌC"
- Date range picker: Chọn khoảng thời gian
- Statistics cards:
  - Tổng số buổi học
  - Số buổi đã check-in
  - Số buổi đã check-out
  - Tỷ lệ check-in (%)
  - Tỷ lệ check-out (%)
- Chart: Biểu đồ thống kê theo tuần/tháng

**API Endpoint:**

**GET /api/sessions/my-stats/**

**Request:**
```
Method: GET
Headers: Authorization: Bearer {token}
Query Params:
  - teacher_id: uuid (required)
  - start_date: YYYY-MM-DD (optional)
  - end_date: YYYY-MM-DD (optional)
```

**Response:**
```json
{
  "total_sessions": 50,
  "checked_in": 45,
  "checked_out": 40,
  "check_in_rate": 90.0,
  "check_out_rate": 80.0
}
```

**Logic Backend:**
1. Lấy `teacher_id` từ query params
2. Filter sessions theo `teacher_id` và date range (nếu có)
3. Tính toán:
   - Tổng số sessions
   - Số sessions đã check-in (`check_in IS NOT NULL`)
   - Số sessions đã check-out (`check_out IS NOT NULL`)
   - Tỷ lệ check-in = (checked_in / total) * 100
   - Tỷ lệ check-out = (checked_out / total) * 100

---

### 2.4. Màn hình: Lịch dạy đầy đủ (CẦN BỔ SUNG)

**Route:** `/teacher/my-teaching-schedule`

**Chức năng:**
- Hiển thị tất cả các buổi học của giáo viên từ tất cả các lớp đang dạy
- Tương tự như màn hình "Lịch học của tôi" của học sinh
- Có thể filter theo khoảng thời gian
- Hiển thị theo dạng calendar hoặc list

**UI Components:**
- Header: "LỊCH DẠY ĐẦY ĐỦ"
- Filter bar:
  - Date picker: Chọn khoảng thời gian
  - Button "Hôm nay", "Tuần này", "Tháng này"
- View toggle: Calendar view / List view
- Danh sách buổi học:
  - Group theo ngày hoặc hiển thị flat list
  - Mỗi buổi học hiển thị:
    - Ngày, giờ
    - Tên lớp
    - Tên khóa học
    - Số học viên
    - Phòng học
    - Skill/Kỹ năng
    - Trạng thái check-in/check-out

**API Endpoint (CẦN IMPLEMENT):**

**GET /api/sessions/my-teaching-schedule/**

**Request:**
```
Method: GET
Headers: Authorization: Bearer {token}
Query Params:
  - teacher_id: uuid (required)
  - start_date: YYYY-MM-DD (optional)
  - end_date: YYYY-MM-DD (optional)
```

**Response (Đề xuất):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "study_date": "2024-02-01",
      "start_time": "18:00",
      "end_time": "20:00",
      "class_session": {
        "id": "uuid",
        "name": "IELTS Foundation - Lớp 1",
        "course": {
          "id": "uuid",
          "name": "IELTS Foundation",
          "level": "intermediate"
        }
      },
      "class_session_name": "IELTS Foundation - Lớp 1",
      "teacher_name": "Nguyễn Văn A",
      "room_name": "Phòng 101",
      "skill": null,
      "check_in": null,
      "check_out": null,
      "is_checked_in": false,
      "is_checked_out": false,
      "attendance_summary": {
        "total": 15,
        "present": 12,
        "absent": 2,
        "late": 1,
        "excused": 0
      }
    }
  ],
  "summary": {
    "total_sessions": 50,
    "upcoming_sessions": 30,
    "completed_sessions": 20,
    "today_sessions": 2
  }
}
```

**Logic Backend (CẦN IMPLEMENT):**
1. Lấy `teacher_id` từ query params
2. Lấy tất cả `sessions` của giáo viên: `Session.objects.filter(teacher_id=teacher_id)`
3. Filter theo `start_date` và `end_date` nếu có
4. Sắp xếp theo `study_date`, `start_time`
5. Tính summary: tổng số buổi, số buổi sắp tới, số buổi đã hoàn thành, số buổi hôm nay

**Implementation trong `class_sessions/views.py`:**
```python
@action(detail=False, methods=['get'], url_path='my-teaching-schedule')
def my_teaching_schedule(self, request):
    """Lịch dạy đầy đủ của teacher"""
    teacher_id = request.query_params.get('teacher_id')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not teacher_id:
        return Response({'detail': 'teacher_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Lấy tất cả sessions của teacher
    qs = Session.objects.filter(teacher_id=teacher_id)
    
    if start_date:
        qs = qs.filter(study_date__gte=start_date)
    if end_date:
        qs = qs.filter(study_date__lte=end_date)
    
    qs = qs.order_by('study_date', 'start_time')
    
    # Tính summary
    today = date.today()
    total_sessions = qs.count()
    upcoming_sessions = qs.filter(study_date__gte=today).count()
    completed_sessions = qs.filter(study_date__lt=today).count()
    today_sessions = qs.filter(study_date=today).count()
    
    serializer = SessionSerializer(qs, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data,
        'summary': {
            'total_sessions': total_sessions,
            'upcoming_sessions': upcoming_sessions,
            'completed_sessions': completed_sessions,
            'today_sessions': today_sessions
        }
    })
```

---

## PHẦN 3: NAVIGATION FLOW

```
Menu/Navigation Bar
    │
    ├─→ HỌC SINH
    │   ├─→ "Lịch học của tôi" → Màn 1.1: Lịch học tổng quan
    │   │                           │
    │   │                           └─→ Màn 1.3: Chi tiết lớp
    │   │
    │   ├─→ "Các buổi học sắp tới" → Màn 1.2: Upcoming sessions
    │   │
    │   └─→ "Lịch học lớp" → Màn 1.3: Chi tiết lớp (từ enrollment)
    │
    └─→ GIÁO VIÊN
        ├─→ "Lịch dạy của tôi" → Màn 2.1: Danh sách lớp
        │                           │
        │                           └─→ Màn 2.4: Lịch dạy đầy đủ (CẦN BỔ SUNG)
        │
        ├─→ "Lịch dạy hôm nay" → Màn 2.2: Today sessions
        │
        ├─→ "Thống kê buổi học" → Màn 2.3: Session stats
        │
        └─→ "Lịch dạy đầy đủ" → Màn 2.4: Full teaching schedule (CẦN BỔ SUNG)
```

---

## PHẦN 4: UI/UX NOTES

### 4.1. Loading States
- Skeleton loading khi load danh sách sessions
- Button loading khi đang filter hoặc refresh
- Progress indicator khi tính toán schedule từ class info

### 4.2. Empty States
- "Bạn chưa có buổi học nào" khi danh sách trống
- "Không có buổi học trong khoảng thời gian này" khi filter không có kết quả
- "Chưa có lịch học" khi sessions chưa được tạo

### 4.3. Error Handling
- Toast notification cho các error
- Alert dialog cho error quan trọng (ví dụ: không có quyền xem)
- Retry button khi load thất bại

### 4.4. Responsive Design
- Mobile: Card full width, stack layout
- Desktop: Grid layout, có thể hiển thị calendar view
- Tablet: 2 cột layout

### 4.5. Calendar View (Optional)
- Hiển thị lịch theo tuần/tháng
- Mỗi ngày hiển thị số buổi học
- Click vào ngày → Xem chi tiết các buổi học trong ngày
- Highlight các buổi học hôm nay

### 4.6. List View
- Group theo ngày
- Mỗi buổi học là một card
- Color coding:
  - Xanh lá: Buổi học sắp tới
  - Xanh dương: Buổi học hôm nay
  - Xám: Buổi học đã qua

---

## PHẦN 5: TÓM TẮT API ENDPOINTS

### Học sinh (Student)

| Endpoint | Method | Mô tả | Status |
|----------|--------|-------|--------|
| `/api/sessions/my-schedule/` | GET | Lịch học tổng quan | ✅ Đã có |
| `/api/sessions/my-upcoming/` | GET | Các buổi học sắp tới | ✅ Đã có |
| `/api/enrollment/enrollments/{id}/schedule/` | GET | Lịch học chi tiết của một lớp | ✅ Đã có |

### Giáo viên (Teacher)

| Endpoint | Method | Mô tả | Status |
|----------|--------|-------|--------|
| `/api/classes/my/` | GET | Danh sách lớp đang dạy | ✅ Đã có |
| `/api/sessions/my-today/` | GET | Các buổi học hôm nay | ✅ Đã có |
| `/api/sessions/my-stats/` | GET | Thống kê buổi học | ✅ Đã có |
| `/api/sessions/my-teaching-schedule/` | GET | Lịch dạy đầy đủ | ❌ **CẦN BỔ SUNG** |
| `/api/classes/{id}/sessions/` | GET | Sessions của một lớp cụ thể | ✅ Đã có |

---

## PHẦN 6: CẦN BỔ SUNG

### 6.1. API Endpoint mới cho giáo viên

**Endpoint:** `GET /api/sessions/my-teaching-schedule/`

**Lý do:**
- Hiện tại giáo viên chỉ có thể xem:
  - Danh sách lớp (`/api/classes/my/`)
  - Các buổi học hôm nay (`/api/sessions/my-today/`)
  - Thống kê (`/api/sessions/my-stats/`)
- Chưa có endpoint để xem tất cả các buổi học trong một khoảng thời gian (tương tự như `my-schedule` của học sinh)

**Implementation:**
- Thêm action `my_teaching_schedule` vào `SessionViewSet` trong `class_sessions/views.py`
- Logic tương tự `my_schedule` nhưng filter theo `teacher_id` thay vì `student_id`
- Trả về danh sách sessions với summary

### 6.2. Cải thiện Response Format

**Hiện tại:**
- `my-schedule` của học sinh trả về array trực tiếp
- `my-teaching-schedule` (cần bổ sung) nên có format nhất quán

**Đề xuất:**
- Tất cả endpoints trả về format:
```json
{
  "success": true,
  "data": [...],
  "summary": {...},
  "meta": {...}
}
```

### 6.3. Tính toán Schedule tự động

**Hiện tại:**
- `GET /api/enrollment/enrollments/{id}/schedule/` đã có logic tính toán schedule từ class info
- Có thể áp dụng tương tự cho giáo viên khi xem lịch dạy của một lớp cụ thể

**Đề xuất:**
- Thêm endpoint `GET /api/classes/{class_id}/schedule/` để giáo viên xem lịch dạy của một lớp
- Tự động tính toán nếu sessions chưa có trong DB

### 6.4. Filter và Search

**Cần bổ sung:**
- Filter theo trạng thái: upcoming, completed, today
- Filter theo lớp cụ thể
- Search theo tên lớp, tên khóa học
- Sort: theo ngày, theo giờ, theo lớp

### 6.5. Export Schedule

**Tính năng mới:**
- Export lịch học/lịch dạy ra file PDF hoặc Excel
- Format calendar (.ics) để import vào Google Calendar, Outlook

---

## PHẦN 7: TESTING CASES

### 7.1. Test cho Học sinh

1. **Test lấy lịch học tổng quan:**
   - Học sinh có nhiều lớp → Trả về tất cả sessions
   - Học sinh chưa đăng ký lớp nào → Trả về empty array
   - Filter theo date range → Chỉ trả về sessions trong khoảng thời gian

2. **Test lấy các buổi học sắp tới:**
   - Có buổi học hôm nay và tương lai → Trả về tất cả
   - Chỉ có buổi học quá khứ → Trả về empty array

3. **Test lấy lịch học chi tiết của một lớp:**
   - Sessions đã có trong DB → Trả về sessions từ DB
   - Sessions chưa có trong DB → Tính toán từ class info
   - Học sinh không có quyền xem → Trả về 403

### 7.2. Test cho Giáo viên

1. **Test lấy danh sách lớp:**
   - Giáo viên có nhiều lớp → Trả về tất cả lớp
   - Giáo viên chưa dạy lớp nào → Trả về empty array

2. **Test lấy các buổi học hôm nay:**
   - Có buổi học hôm nay → Trả về danh sách
   - Không có buổi học hôm nay → Trả về empty array

3. **Test lấy thống kê:**
   - Tính toán đúng tỷ lệ check-in/check-out
   - Filter theo date range → Tính toán đúng

4. **Test lấy lịch dạy đầy đủ (sau khi implement):**
   - Tương tự test của học sinh nhưng filter theo teacher_id

---

## PHẦN 8: IMPLEMENTATION CHECKLIST

### Backend

- [x] `GET /api/sessions/my-schedule/` - Lịch học của học sinh
- [x] `GET /api/sessions/my-upcoming/` - Các buổi học sắp tới
- [x] `GET /api/enrollment/enrollments/{id}/schedule/` - Lịch học chi tiết lớp
- [x] `GET /api/classes/my/` - Danh sách lớp của giáo viên
- [x] `GET /api/sessions/my-today/` - Các buổi học hôm nay của giáo viên
- [x] `GET /api/sessions/my-stats/` - Thống kê buổi học
- [ ] `GET /api/sessions/my-teaching-schedule/` - **CẦN BỔ SUNG**
- [ ] `GET /api/classes/{id}/schedule/` - Lịch dạy chi tiết của một lớp (optional)

### Frontend

- [ ] Màn hình "Lịch học của tôi" cho học sinh
- [ ] Màn hình "Các buổi học sắp tới" cho học sinh
- [ ] Màn hình "Lịch học chi tiết lớp" cho học sinh
- [ ] Màn hình "Lịch dạy của tôi" cho giáo viên
- [ ] Màn hình "Các buổi học hôm nay" cho giáo viên
- [ ] Màn hình "Thống kê buổi học" cho giáo viên
- [ ] Màn hình "Lịch dạy đầy đủ" cho giáo viên (sau khi có API)

---

## PHẦN 9: NOTES

1. **Tính toán Schedule tự động:**
   - Khi sessions chưa được tạo trong DB, API tự động tính toán từ class info
   - Logic tính toán dựa trên: weekday, time_slot, start_date, end_date
   - Đảm bảo học sinh và giáo viên có thể xem lịch ngay sau khi đăng ký/phân công lớp

2. **Performance:**
   - Sử dụng `select_related` và `prefetch_related` để tối ưu query
   - Cache schedule nếu cần (optional)

3. **Security:**
   - Kiểm tra quyền truy cập: học sinh chỉ xem được lịch học của mình
   - Giáo viên chỉ xem được lịch dạy của mình

4. **Consistency:**
   - Format response nhất quán giữa các endpoints
   - Error messages rõ ràng, dễ hiểu

---

**Tài liệu này sẽ được cập nhật khi có thay đổi hoặc bổ sung mới.**




