# TEACHER UI SCREENS AND APIs - CHI TIẾT CÁC MÀN HÌNH VÀ API

Tài liệu này mô tả chi tiết các màn hình và API cần thiết cho role Teacher trong ứng dụng English Center.

---

## 📱 TỔNG QUAN CÁC MÀN HÌNH

TabBar của Teacher gồm 6 màn hình chính:
1. **TRÌNH ĐỘ CỦA TÔI** - Xem thông tin trình độ
2. **ĐĂNG KÝ LỚP HỌC** - Đăng ký/hủy đăng ký lớp
3. **LỊCH DẠY CỦA TÔI** - Xem thời khóa biểu theo tuần
4. **QUẢN LÝ BÀI TẬP** - Quản lý bài tập và chấm điểm
5. **LỚP DẠY CỦA TÔI** - Quản lý lớp và buổi học
6. **ĐƠN XIN NGHỈ** - Duyệt đơn xin nghỉ của học viên

---

## 1. TRÌNH ĐỘ CỦA TÔI

### 1.1. Màn hình chính: Xem thông tin trình độ

**Mô tả:**
- Hiển thị thông tin trình độ của giáo viên (chỉ xem, không chỉnh sửa)
- Bao gồm: Level (Junior/Senior/Expert), Specialization (IELTS Speaking, TOEIC), Campus

**UI Components:**
- Header: "TRÌNH ĐỘ CỦA TÔI"
- Card hiển thị:
  - Level: Badge/Text (Junior/Senior/Expert)
  - Specialization: Text field
  - Campus: Tên cơ sở (nếu có)

**API:**

#### GET /api/users/teachers/my-level/
**Mô tả:** Lấy thông tin trình độ của giáo viên hiện tại

**Request:**
- Method: GET
- Headers: Authorization: Bearer {token}

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "level": "senior",
    "specialization": "IELTS Speaking",
    "campus": {
      "id": "uuid",
      "name": "Cơ sở Quận 1"
    }
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Only teachers can access this endpoint"
}
```

---

## 2. ĐĂNG KÝ LỚP HỌC

### 2.1. Màn hình chính: Danh sách lớp chưa có giáo viên

**Mô tả:**
- Hiển thị danh sách các lớp học chưa được gán giáo viên
- Giáo viên có thể chọn lớp muốn dạy và đăng ký
- Có thể hủy đăng ký nếu lớp chưa có học viên đăng ký

**UI Components:**
- Header: "ĐĂNG KÝ LỚP HỌC"
- Search bar (tùy chọn)
- Danh sách lớp:
  - Card mỗi lớp hiển thị:
    - Tên lớp
    - Tên khóa học
    - Ngày bắt đầu/kết thúc
    - Lịch học (weekday, time_slot)
    - Cơ sở
    - Số học viên hiện tại / Giới hạn
    - Button "Đăng ký"
- Pull to refresh

**API:**

#### GET /api/users/teachers/available-classes/
**Mô tả:** Lấy danh sách lớp học chưa có giáo viên

**Request:**
- Method: GET
- Headers: Authorization: Bearer {token}

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "IELTS Foundation - Lớp 1",
      "course_name": "IELTS Foundation",
      "start_date": "2024-01-15",
      "end_date": "2024-04-15",
      "weekday": [2, 4, 6],
      "time_slot": "18:30-20:30",
      "campus": {
        "id": "uuid",
        "name": "Cơ sở Quận 1"
      },
      "current_student_count": 0,
      "limit_slot": 20
    }
  ]
}
```

### 2.2. Màn hình: Chi tiết lớp (trước khi đăng ký)

**Mô tả:**
- Hiển thị thông tin chi tiết lớp học
- Button "Đăng ký lớp này"
- Hiển thị lịch học chi tiết

**UI Components:**
- Header với nút back
- Thông tin lớp chi tiết
- Lịch học (tuần)
- Button "Đăng ký lớp này" (primary)
- Loading state khi đang đăng ký

**API:**

#### POST /api/users/teachers/register-class/
**Mô tả:** Đăng ký dạy lớp (có check trùng lịch)

**Request:**
- Method: POST
- Headers: Authorization: Bearer {token}
- Body:
```json
{
  "class_id": "uuid"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Đăng ký lớp thành công",
  "data": {
    "class_id": "uuid",
    "class_name": "IELTS Foundation - Lớp 1"
  }
}
```

**Response (Error - Trùng lịch):**
```json
{
  "success": false,
  "error": "Bạn đã có lớp vào thời gian này"
}
```

**Response (Error - Lớp đã có giáo viên):**
```json
{
  "success": false,
  "error": "Class already has a teacher"
}
```

**Response (Error - Trạng thái không hợp lệ):**
```json
{
  "success": false,
  "error": "Chỉ có thể đăng ký lớp ở trạng thái planned. Lớp hiện tại: ongoing"
}
```

**Flow sau khi đăng ký thành công:**
- Hiển thị thông báo thành công
- Tự động chuyển sang màn hình "LỊCH DẠY CỦA TÔI" (giống role Student)

### 2.3. Màn hình: Danh sách lớp đã đăng ký (để hủy)

**Mô tả:**
- Hiển thị danh sách lớp giáo viên đã đăng ký
- Chỉ hiển thị lớp chưa có học viên đăng ký
- Có button "Hủy đăng ký"

**UI Components:**
- Header: "LỚP ĐÃ ĐĂNG KÝ"
- Danh sách lớp:
  - Card mỗi lớp
  - Button "Hủy đăng ký" (danger)
  - Hiển thị số học viên: "Chưa có học viên" hoặc "Đã có X học viên"

**API:**

#### POST /api/users/teachers/cancel-class-registration/
**Mô tả:** Hủy đăng ký lớp (chỉ được nếu lớp chưa có học viên)

**Request:**
- Method: POST
- Headers: Authorization: Bearer {token}
- Body:
```json
{
  "class_id": "uuid"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Hủy đăng ký lớp thành công"
}
```

**Response (Error - Đã có học viên):**
```json
{
  "success": false,
  "error": "Không thể hủy đăng ký vì lớp đã có 5 học viên đăng ký"
}
```

---

## 3. LỊCH DẠY CỦA TÔI

### 3.1. Màn hình chính: Thời khóa biểu theo tuần

**Mô tả:**
- Hiển thị lịch dạy của giáo viên theo tuần (từ thứ 2 đến chủ nhật)
- Có thể chuyển tuần trước/sau
- Hiển thị các buổi học trong tuần

**UI Components:**
- Header: "LỊCH DẠY CỦA TÔI"
- Week selector:
  - Button "<" (tuần trước)
  - Text hiển thị: "Tuần XX/YYYY (DD/MM - DD/MM)"
  - Button ">" (tuần sau)
  - Button "Hôm nay" (về tuần hiện tại)
- Calendar view (7 cột: Mon-Sun):
  - Mỗi ngày hiển thị:
    - Ngày (DD)
    - Các buổi học trong ngày:
      - Card buổi học:
        - Tên lớp
        - Thời gian (HH:mm - HH:mm)
        - Phòng học
        - Badge trạng thái (nếu có)
- Empty state: "Không có buổi học nào trong tuần này"

**API:**

#### GET /api/users/teachers/my-schedule/
**Mô tả:** Lấy lịch dạy theo tuần

**Request:**
- Method: GET
- Headers: Authorization: Bearer {token}
- Query params:
  - `week_start` (optional): YYYY-MM-DD (mặc định là thứ 2 của tuần hiện tại)

**Response:**
```json
{
  "success": true,
  "data": {
    "week_start": "2024-01-15",
    "week_end": "2024-01-21",
    "sessions": [
      {
        "id": "uuid",
        "class_name": "IELTS Foundation - Lớp 1",
        "course_name": "IELTS Foundation",
        "date": "2024-01-15",
        "start_time": "18:30:00",
        "end_time": "20:30:00",
        "room": "Phòng 101"
      }
    ]
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid week_start format. Use YYYY-MM-DD"
}
```

---

## 4. QUẢN LÝ BÀI TẬP

### 4.1. Màn hình chính: Danh sách bài tập

**Mô tả:**
- Hiển thị danh sách tất cả bài tập của giáo viên
- Có thể xem chi tiết, sửa (nếu chưa quá deadline), xem danh sách bài nộp

**UI Components:**
- Header: "QUẢN LÝ BÀI TẬP"
- Search bar (tùy chọn)
- Filter (tùy chọn): Theo trạng thái, theo lớp
- Danh sách bài tập:
  - Card mỗi bài tập:
    - Tên bài tập
    - Tên lớp
    - Deadline (nếu có)
    - Trạng thái (Draft/Published/Closed)
    - Số bài đã nộp / Tổng số học viên
    - Button "Xem chi tiết"
    - Button "Danh sách bài nộp"
- Pull to refresh

**API:**

#### GET /api/assignment/
**Mô tả:** Lấy danh sách bài tập của giáo viên

**Request:**
- Method: GET
- Headers: Authorization: Bearer {token}
- Query params (optional):
  - `session`: Filter theo session_id
  - `status`: Filter theo status (draft, published, closed)
  - `search`: Tìm kiếm theo title, description

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "Bài tập Unit 1",
    "description": "Làm bài tập về thì hiện tại đơn",
    "due_date": "2024-01-20",
    "status": "published",
    "session": {
      "id": "uuid",
      "study_date": "2024-01-15",
      "class_session": {
        "id": "uuid",
        "name": "IELTS Foundation - Lớp 1"
      }
    },
    "created_at": "2024-01-10T10:00:00Z"
  }
]
```

### 4.2. Màn hình: Chi tiết bài tập

**Mô tả:**
- Hiển thị thông tin chi tiết bài tập
- Có thể sửa bài tập (nếu chưa quá deadline)
- Button "Danh sách bài nộp"

**UI Components:**
- Header với nút back
- Thông tin bài tập:
  - Tên bài tập
  - Mô tả
  - Deadline
  - Trạng thái
  - File đính kèm (nếu có)
- Button "Sửa bài tập" (nếu chưa quá deadline)
- Button "Danh sách bài nộp" (primary)
- Button "Xóa bài tập" (danger, nếu chưa có bài nộp)

**API:**

#### GET /api/assignment/{id}/
**Mô tả:** Lấy chi tiết bài tập

**Request:**
- Method: GET
- Headers: Authorization: Bearer {token}

**Response:**
```json
{
  "id": "uuid",
  "title": "Bài tập Unit 1",
  "description": "Làm bài tập về thì hiện tại đơn",
  "due_date": "2024-01-20",
  "status": "published",
  "url_file": "https://...",
  "session": {
    "id": "uuid",
    "study_date": "2024-01-15",
    "class_session": {
      "id": "uuid",
      "name": "IELTS Foundation - Lớp 1"
    }
  },
  "answer_keys": [
    {
      "id": "uuid",
      "question_number": 1,
      "correct_option": "A",
      "description": "Đáp án đúng"
    }
  ]
}
```

#### PUT /api/assignment/{id}/
**Mô tả:** Cập nhật bài tập (chỉ được nếu chưa quá deadline)

**Request:**
- Method: PUT
- Headers: Authorization: Bearer {token}
- Body:
```json
{
  "title": "Bài tập Unit 1 (Updated)",
  "description": "Mô tả mới",
  "due_date": "2024-01-25",
  "url_file": "https://..."
}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Bài tập Unit 1 (Updated)",
  ...
}
```

### 4.3. Màn hình: Danh sách bài nộp

**Mô tả:**
- Hiển thị danh sách bài nộp của học viên
- Có thể chấm điểm, nhận xét, yêu cầu nộp lại
- Hiển thị thống kê

**UI Components:**
- Header: "Danh sách bài nộp - [Tên bài tập]"
- Thống kê:
  - Tổng số học viên
  - Số bài đã nộp
  - Số bài đã chấm
  - Điểm trung bình
- Filter:
  - Tất cả
  - Đã nộp
  - Đã chấm
  - Cần nộp lại
- Danh sách bài nộp:
  - Card mỗi bài nộp:
    - Tên học viên
    - Thời gian nộp
    - Trạng thái (Đã nộp/Đã chấm/Cần nộp lại)
    - Điểm (nếu đã chấm)
    - Button "Chấm điểm"

**API:**

#### GET /api/assignment/{id}/submissions/
**Mô tả:** Lấy danh sách bài nộp và thống kê

**Request:**
- Method: GET
- Headers: Authorization: Bearer {token}

**Response:**
```json
{
  "total_students": 30,
  "submitted_count": 25,
  "graded_count": 20,
  "average_score": 78.5,
  "submissions": [
    {
      "id": "uuid",
      "student": {
        "id": "uuid",
        "name": "Nguyễn Văn A"
      },
      "submitted_at": "2024-01-18T10:00:00Z",
      "status": "submitted",
      "result": null,
      "content": "Nội dung bài làm"
    }
  ]
}
```

### 4.4. Màn hình: Chấm điểm bài nộp

**Mô tả:**
- Hiển thị chi tiết bài nộp của học viên
- Có thể chấm điểm, nhận xét, yêu cầu nộp lại
- Logic: Chỉ được yêu cầu nộp lại 1 lần cho mỗi học viên ở mỗi bài tập

**UI Components:**
- Header với nút back
- Thông tin học viên:
  - Tên học viên
  - Thời gian nộp
- Nội dung bài làm:
  - Hiển thị câu trả lời của học viên
  - So sánh với đáp án (nếu có)
- Form chấm điểm:
  - Input điểm (0-100)
  - Textarea nhận xét
  - Radio buttons:
    - "Đạt" (graded)
    - "Yêu cầu nộp lại" (resubmit_required) - chỉ hiển thị nếu chưa yêu cầu nộp lại
  - Button "Lưu"
- Hiển thị cảnh báo nếu đã yêu cầu nộp lại trước đó

**API:**

#### GET /api/assignment/teacher-submissions/{id}/
**Mô tả:** Lấy chi tiết bài nộp

**Request:**
- Method: GET
- Headers: Authorization: Bearer {token}

**Response:**
```json
{
  "id": "uuid",
  "student": {
    "id": "uuid",
    "name": "Nguyễn Văn A"
  },
  "assignment": {
    "id": "uuid",
    "title": "Bài tập Unit 1"
  },
  "submitted_at": "2024-01-18T10:00:00Z",
  "status": "submitted",
  "result": null,
  "content": "Nội dung bài làm",
  "student_answers": [
    {
      "question_number": 1,
      "selected_option": 2,
      "is_correct": 1
    }
  ]
}
```

#### PATCH /api/assignment/teacher-submissions/{id}/grade/
**Mô tả:** Chấm điểm bài nộp

**Request:**
- Method: PATCH
- Headers: Authorization: Bearer {token}
- Body:
```json
{
  "result": 85.5,
  "status": "graded",
  "content": "Bài làm tốt, cần cải thiện phần..."
}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "graded",
  "result": 85.5,
  "content": "Bài làm tốt, cần cải thiện phần..."
}
```

#### PATCH /api/assignment/teacher-submissions/{id}/request-resubmit/
**Mô tả:** Yêu cầu học viên nộp lại (chỉ được 1 lần)

**Request:**
- Method: PATCH
- Headers: Authorization: Bearer {token}
- Body:
```json
{
  "content": "Bài làm chưa đạt yêu cầu. Vui lòng làm lại phần..."
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Yêu cầu nộp lại đã được gửi",
  "data": {
    "id": "uuid",
    "status": "resubmit_required",
    "content": "Bài làm chưa đạt yêu cầu..."
  }
}
```

**Response (Error - Đã yêu cầu nộp lại):**
```json
{
  "success": false,
  "error": "Bạn chỉ có thể yêu cầu nộp lại 1 lần cho mỗi học viên ở mỗi bài tập"
}
```

**Response (Error - Đã chấm điểm):**
```json
{
  "success": false,
  "error": "Không thể yêu cầu nộp lại vì bài tập đã được chấm điểm"
}
```

---

## 5. LỚP DẠY CỦA TÔI

### 5.1. Màn hình chính: Danh sách lớp đang dạy

**Mô tả:**
- Hiển thị danh sách tất cả lớp giáo viên đang giảng dạy
- Có thể xem chi tiết từng lớp

**UI Components:**
- Header: "LỚP DẠY CỦA TÔI"
- Search bar (tùy chọn)
- Filter (tùy chọn): Theo trạng thái lớp
- Danh sách lớp:
  - Card mỗi lớp:
    - Tên lớp
    - Tên khóa học
    - Trạng thái (Planned/Ongoing/Completed)
    - Số học viên / Giới hạn
    - Ngày bắt đầu/kết thúc
    - Button "Xem chi tiết"
- Pull to refresh

**API:**

#### GET /api/users/teachers/my-classes/
**Mô tả:** Lấy danh sách lớp đang dạy

**Request:**
- Method: GET
- Headers: Authorization: Bearer {token}

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "IELTS Foundation - Lớp 1",
      "course_name": "IELTS Foundation",
      "start_date": "2024-01-15",
      "end_date": "2024-04-15",
      "status": "ongoing",
      "current_student_count": 15,
      "limit_slot": 20,
      "campus": {
        "id": "uuid",
        "name": "Cơ sở Quận 1"
      }
    }
  ]
}
```

### 5.2. Màn hình: Chi tiết lớp - Danh sách buổi học

**Mô tả:**
- Hiển thị danh sách buổi học của lớp
- Phân loại theo 3 trạng thái: Đã diễn ra, Đang diễn ra, Sắp diễn ra
- Có thể xem chi tiết từng buổi học

**UI Components:**
- Header: "[Tên lớp]" với nút back
- Tabs/Sections:
  - "Đã diễn ra" (past_sessions)
  - "Đang diễn ra" (current_sessions)
  - "Sắp diễn ra" (upcoming_sessions)
- Mỗi section hiển thị danh sách buổi học:
  - Card mỗi buổi học:
    - Ngày học (DD/MM/YYYY)
    - Thời gian (HH:mm - HH:mm)
    - Phòng học
    - Kỹ năng (nếu có)
    - Trạng thái check-in/check-out (nếu có)
    - Button "Xem chi tiết"

**API:**

#### GET /api/users/teachers/classes/{class_id}/sessions/
**Mô tả:** Lấy danh sách buổi học của lớp (phân loại theo trạng thái)

**Request:**
- Method: GET
- Headers: Authorization: Bearer {token}

**Response:**
```json
{
  "success": true,
  "data": {
    "class_id": "uuid",
    "class_name": "IELTS Foundation - Lớp 1",
    "past_sessions": [
      {
        "id": "uuid",
        "study_date": "2024-01-10",
        "start_time": "18:30:00",
        "end_time": "20:30:00",
        "room": "Phòng 101",
        "skill": "Speaking",
        "check_in": "18:25:00",
        "check_out": "20:35:00",
        "status": "past"
      }
    ],
    "current_sessions": [
      {
        "id": "uuid",
        "study_date": "2024-01-15",
        "start_time": "18:30:00",
        "end_time": "20:30:00",
        "room": "Phòng 101",
        "skill": "Listening",
        "check_in": null,
        "check_out": null,
        "status": "current"
      }
    ],
    "upcoming_sessions": [
      {
        "id": "uuid",
        "study_date": "2024-01-17",
        "start_time": "18:30:00",
        "end_time": "20:30:00",
        "room": "Phòng 101",
        "skill": null,
        "check_in": null,
        "check_out": null,
        "status": "upcoming"
      }
    ]
  }
}
```

### 5.3. Màn hình: Chi tiết buổi học

**Mô tả:**
- Hiển thị thông tin chi tiết buổi học
- Có 2 button chính: "Tạo bài tập" và "Điểm danh"
- Logic button:
  - Buổi đã diễn ra: 2 button DISABLE
  - Buổi đang diễn ra: 2 button ENABLE
  - Buổi sắp diễn ra: Chỉ button "Tạo bài tập" ENABLE

**UI Components:**
- Header: "Buổi học - [Ngày]" với nút back
- Thông tin buổi học:
  - Ngày học
  - Thời gian
  - Phòng học
  - Kỹ năng
  - Trạng thái check-in/check-out
- Actions:
  - Button "Tạo bài tập" (primary)
    - Enable: Buổi đang diễn ra hoặc sắp diễn ra
    - Disable: Buổi đã diễn ra
  - Button "Điểm danh" (secondary)
    - Enable: Chỉ buổi đang diễn ra
    - Disable: Buổi đã diễn ra hoặc sắp diễn ra

**API:**

#### GET /api/class-sessions/{session_id}/
**Mô tả:** Lấy chi tiết buổi học (có thể dùng API có sẵn)

### 5.4. Màn hình: Tạo bài tập cho buổi học

**Mô tả:**
- Form tạo bài tập mới cho buổi học
- Có thể upload file, nhập deadline

**UI Components:**
- Header: "Tạo bài tập" với nút back
- Form:
  - Input: Tên bài tập (required)
  - Textarea: Mô tả
  - Date picker: Deadline
  - File upload: File đính kèm
  - Button "Tạo bài tập" (primary)
  - Button "Hủy" (secondary)

**API:**

#### POST /api/assignment/
**Mô tả:** Tạo bài tập mới

**Request:**
- Method: POST
- Headers: Authorization: Bearer {token}
- Body:
```json
{
  "title": "Bài tập Unit 1",
  "description": "Làm bài tập về thì hiện tại đơn",
  "due_date": "2024-01-20",
  "session_id": "uuid",
  "url_file": "https://..."
}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Bài tập Unit 1",
  "description": "Làm bài tập về thì hiện tại đơn",
  "due_date": "2024-01-20",
  "status": "draft",
  "session": "uuid"
}
```

### 5.5. Màn hình: Điểm danh

**Mô tả:**
- Hiển thị danh sách học viên của lớp
- Giáo viên chọn trạng thái điểm danh cho từng học viên
- Submit để lưu

**UI Components:**
- Header: "Điểm danh - [Ngày]" với nút back
- Thông tin buổi học:
  - Ngày học
  - Thời gian
  - Tên lớp
- Danh sách học viên:
  - Mỗi học viên:
    - Tên học viên
    - Radio buttons hoặc Dropdown:
      - "Có mặt" (present)
      - "Vắng" (absent)
      - "Muộn" (late)
      - "Có phép" (excused)
    - Hiển thị trạng thái hiện tại (nếu đã điểm danh)
- Button "Lưu điểm danh" (primary, bottom)
- Loading state khi đang submit

**API:**

#### GET /api/users/teachers/sessions/{session_id}/attendance/
**Mô tả:** Lấy danh sách học viên để điểm danh

**Request:**
- Method: GET
- Headers: Authorization: Bearer {token}

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "session_date": "2024-01-15",
    "class_name": "IELTS Foundation - Lớp 1",
    "students": [
      {
        "student_id": "uuid",
        "student_name": "Nguyễn Văn A",
        "current_status": "present"
      },
      {
        "student_id": "uuid",
        "student_name": "Trần Thị B",
        "current_status": null
      }
    ]
  }
}
```

**Error Response (Không phải giáo viên của lớp):**
```json
{
  "success": false,
  "error": "You are not the teacher of this class"
}
```

#### POST /api/users/teachers/sessions/{session_id}/attendance/
**Mô tả:** Điểm danh học viên

**Request:**
- Method: POST
- Headers: Authorization: Bearer {token}
- Body:
```json
{
  "attendances": [
    {
      "student_id": "uuid",
      "status": "present"
    },
    {
      "student_id": "uuid",
      "status": "late"
    },
    {
      "student_id": "uuid",
      "status": "absent"
    },
    {
      "student_id": "uuid",
      "status": "excused"
    }
  ]
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Điểm danh thành công: 2 mới, 2 cập nhật",
  "data": {
    "created_count": 2,
    "updated_count": 2
  }
}
```

**Response (Error - Không phải buổi học đang diễn ra):**
```json
{
  "success": false,
  "error": "Chỉ có thể điểm danh cho buổi học đang diễn ra"
}
```

**Response (Error - Không phải giáo viên):**
```json
{
  "success": false,
  "error": "You are not the teacher of this class"
}
```

---

## 6. ĐƠN XIN NGHỈ

### 6.1. Màn hình chính: Danh sách đơn xin nghỉ

**Mô tả:**
- Hiển thị danh sách đơn xin nghỉ của học viên trong các lớp giáo viên đang dạy
- Có thể duyệt hoặc từ chối đơn
- Có thể xem lịch sử đơn đã duyệt/từ chối

**UI Components:**
- Header: "ĐƠN XIN NGHỈ"
- Filter:
  - Tất cả
  - Chờ duyệt (pending)
  - Đã duyệt (teacher_approved)
  - Đã từ chối (rejected)
- Danh sách đơn:
  - Card mỗi đơn:
    - Tên học viên
    - Tên lớp
    - Ngày xin nghỉ
    - Thời gian (nếu có)
    - Trạng thái (Badge)
    - Thời gian tạo đơn
    - Actions:
      - Button "Đồng ý" (success, chỉ hiển thị nếu pending)
      - Button "Từ chối" (danger, chỉ hiển thị nếu pending)
      - Button "Xem chi tiết"
- Pull to refresh

**API:**

#### GET /api/users/teachers/leave-requests/
**Mô tả:** Lấy danh sách đơn xin nghỉ

**Request:**
- Method: GET
- Headers: Authorization: Bearer {token}
- Query params (optional):
  - `status`: Filter theo status (pending, teacher_approved, rejected)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "student": {
        "id": "uuid",
        "name": "Nguyễn Văn A"
      },
      "class_name": "IELTS Foundation - Lớp 1",
      "session_date": "2024-01-20",
      "session_time": "18:30:00",
      "status": "pending",
      "created_at": "2024-01-18T10:00:00Z",
      "updated_at": "2024-01-18T10:00:00Z"
    }
  ]
}
```

### 6.2. Màn hình: Chi tiết đơn xin nghỉ

**Mô tả:**
- Hiển thị thông tin chi tiết đơn xin nghỉ
- Có thể duyệt hoặc từ chối (nếu đang pending)

**UI Components:**
- Header: "Chi tiết đơn xin nghỉ" với nút back
- Thông tin đơn:
  - Tên học viên
  - Tên lớp
  - Ngày xin nghỉ
  - Thời gian (nếu có)
  - Trạng thái (Badge)
  - Thời gian tạo/cập nhật
- Actions (chỉ hiển thị nếu status = pending):
  - Button "Đồng ý" (success)
  - Button "Từ chối" (danger)
- Loading state khi đang xử lý

**API:**

#### PATCH /api/users/teachers/leave-requests/{request_id}/approval/
**Mô tả:** Duyệt/từ chối đơn xin nghỉ

**Request:**
- Method: PATCH
- Headers: Authorization: Bearer {token}
- Body:
```json
{
  "action": "approve"  // hoặc "reject"
}
```

**Response (Success - Approve):**
```json
{
  "success": true,
  "message": "Đơn xin nghỉ đã được giáo viên duyệt, đang chờ quản lý duyệt",
  "data": {
    "id": "uuid",
    "status": "teacher_approved"
  }
}
```

**Response (Success - Reject):**
```json
{
  "success": true,
  "message": "Đơn xin nghỉ đã bị từ chối",
  "data": {
    "id": "uuid",
    "status": "rejected"
  }
}
```

**Response (Error - Invalid action):**
```json
{
  "success": false,
  "error": "Invalid action. Use \"approve\" or \"reject\""
}
```

**Response (Error - Đã xử lý):**
```json
{
  "success": false,
  "error": "Leave request is already teacher_approved"
}
```

**Response (Error - Không phải giáo viên của lớp):**
```json
{
  "success": false,
  "error": "You are not the teacher of this class"
}
```

**Flow:**
- Nếu giáo viên **đồng ý**: Status → `teacher_approved` → Đơn được chuyển lên quản lý
- Nếu giáo viên **từ chối**: Status → `rejected` → Đơn bị từ chối luôn

---

## 📋 TÓM TẮT CÁC API

### Authentication
- Tất cả API đều yêu cầu: `Authorization: Bearer {token}`
- User phải có role `teacher`

### Base URL
- Tất cả API: `/api/...`

### API Endpoints

#### 1. Trình độ
- `GET /api/users/teachers/my-level/` - Xem thông tin trình độ

#### 2. Đăng ký lớp học
- `GET /api/users/teachers/available-classes/` - Danh sách lớp chưa có giáo viên
- `POST /api/users/teachers/register-class/` - Đăng ký lớp
- `POST /api/users/teachers/cancel-class-registration/` - Hủy đăng ký

#### 3. Lịch dạy
- `GET /api/users/teachers/my-schedule/` - Lịch dạy theo tuần

#### 4. Quản lý bài tập
- `GET /api/assignment/` - Danh sách bài tập
- `GET /api/assignment/{id}/` - Chi tiết bài tập
- `PUT /api/assignment/{id}/` - Sửa bài tập
- `POST /api/assignment/` - Tạo bài tập
- `GET /api/assignment/{id}/submissions/` - Danh sách bài nộp
- `GET /api/assignment/teacher-submissions/{id}/` - Chi tiết bài nộp
- `PATCH /api/assignment/teacher-submissions/{id}/grade/` - Chấm điểm
- `PATCH /api/assignment/teacher-submissions/{id}/request-resubmit/` - Yêu cầu nộp lại

#### 5. Lớp dạy
- `GET /api/users/teachers/my-classes/` - Danh sách lớp đang dạy
- `GET /api/users/teachers/classes/{class_id}/sessions/` - Danh sách buổi học
- `GET /api/users/teachers/sessions/{session_id}/attendance/` - Xem danh sách điểm danh
- `POST /api/users/teachers/sessions/{session_id}/attendance/` - Điểm danh

#### 6. Đơn xin nghỉ
- `GET /api/users/teachers/leave-requests/` - Danh sách đơn xin nghỉ
- `PATCH /api/users/teachers/leave-requests/{request_id}/approval/` - Duyệt/từ chối đơn

---

## 🔄 FLOW CHÍNH

### Flow đăng ký lớp học:
1. Giáo viên vào "ĐĂNG KÝ LỚP HỌC"
2. Xem danh sách lớp chưa có giáo viên
3. Click vào lớp → Xem chi tiết
4. Click "Đăng ký lớp này"
5. Hệ thống check trùng lịch
6. Nếu không trùng → Đăng ký thành công → Tự động chuyển sang "LỊCH DẠY CỦA TÔI"
7. Nếu trùng → Hiển thị lỗi "Bạn đã có lớp vào thời gian này"

### Flow quản lý bài tập:
1. Giáo viên vào "QUẢN LÝ BÀI TẬP"
2. Xem danh sách bài tập
3. Click vào bài tập → Xem chi tiết
4. Click "Danh sách bài nộp"
5. Xem danh sách bài nộp
6. Click vào bài nộp → Chấm điểm
7. Chọn: "Đạt" hoặc "Yêu cầu nộp lại" (chỉ được 1 lần)
8. Lưu

### Flow điểm danh:
1. Giáo viên vào "LỚP DẠY CỦA TÔI"
2. Chọn lớp → Xem danh sách buổi học
3. Click vào buổi học "Đang diễn ra"
4. Click "Điểm danh"
5. Chọn trạng thái cho từng học viên
6. Submit

### Flow duyệt đơn xin nghỉ:
1. Giáo viên vào "ĐƠN XIN NGHỈ"
2. Xem danh sách đơn xin nghỉ
3. Click vào đơn → Xem chi tiết
4. Chọn "Đồng ý" hoặc "Từ chối"
5. Nếu đồng ý → Status = `teacher_approved` → Chuyển lên quản lý
6. Nếu từ chối → Status = `rejected` → Đơn bị từ chối luôn

---

## ⚠️ LƯU Ý QUAN TRỌNG

1. **Check trùng lịch**: Khi đăng ký lớp, hệ thống phải check trùng lịch với các lớp đang dạy
2. **Giới hạn yêu cầu nộp lại**: Giáo viên chỉ có thể yêu cầu nộp lại 1 lần cho mỗi học viên ở mỗi bài tập
3. **Điểm danh**: Chỉ có thể điểm danh cho buổi học đang diễn ra (study_date == today)
4. **Tạo bài tập**: Có thể tạo bài tập cho buổi học đang diễn ra hoặc sắp diễn ra
5. **Hủy đăng ký**: Chỉ được hủy nếu lớp chưa có học viên đăng ký
6. **Đơn xin nghỉ**: 
   - Nếu giáo viên đồng ý → Đơn chuyển lên quản lý (2 bước duyệt)
   - Nếu giáo viên từ chối → Đơn bị từ chối luôn (1 bước)

---

## 📝 GHI CHÚ

- Tất cả các API đều trả về format `{success: true/false, data/error: ...}`
- Các màn hình nên có loading state và error handling
- Nên có pull-to-refresh cho các danh sách
- Các button nên có disabled state khi không thể thực hiện action

