# TÀI LIỆU MÀN HÌNH VÀ API CHO STUDENT

Tài liệu này liệt kê chi tiết các màn hình (screens) và API endpoints tương ứng cho từng chức năng trong tabbar của học viên.

---

## 📱 TABBAR STRUCTURE

Tabbar có **5 nhóm chính**:
1. **Trình độ**
2. **Kiểm tra**
3. **Bài tập**
4. **Lớp học**
5. **Yêu cầu**

---

## 1. NHÓM TRÌNH ĐỘ

### 1.1. Màn hình: "Trình độ của tôi"

**Mô tả**: Hiển thị thông tin trình độ hiện tại của học viên

**API Endpoint**:
```
GET /api/users/students/my-level/
```

**Headers**:
```
Authorization: Bearer <token>
```

**Response**:
```json
{
  "success": true,
  "data": {
    "total_score": 750.0,
    "reading_score": 375.0,
    "listening_score": 375.0,
    "speaking_score": 150.0,
    "writing_score": 150.0,
    "certificate_type": "toeic",
    "valid_from": "2024-01-15",
    "valid_until": "2024-07-15",
    "certificate_image_url": "https://...",
    "source": "final_test" // hoặc "certificate", "placement_test"
  },
  "message": "Chưa có điểm xác định trình độ..." // (nếu chưa có)
}
```

**Logic hiển thị**:
- **Case 1** (ưu tiên cao nhất): Test cuối khóa trong 6 tháng
- **Case 2**: Chứng chỉ đã verified (còn hiệu lực)
- **Case 3**: Test đầu vào trong 6 tháng

**UI Components**:
- Card hiển thị tổng điểm
- 4 cards nhỏ hiển thị điểm từng kỹ năng
- Badge hiển thị loại chứng chỉ
- Hiển thị ngày hiệu lực
- Hiển thị ảnh chứng chỉ (nếu có)
- Badge hiển thị nguồn điểm (Test cuối khóa / Chứng chỉ / Test đầu vào)

---

## 2. NHÓM KIỂM TRA

### 2.1. Màn hình: "Bài kiểm tra của tôi"

**Mô tả**: Danh sách các bài test của học viên (chưa làm và đã làm)

**API Endpoint**:
```
GET /api/users/students/my-exams/
```

**Headers**:
```
Authorization: Bearer <token>
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "exam_instance_id": "uuid",
      "title": "TOEIC Practice Test 1",
      "exam_type": "practice",
      "status": "completed", // in_progress, completed, graded
      "score": 750.0,
      "submitted_at": "2024-01-15T10:30:00Z",
      "created_at": "2024-01-15T09:00:00Z"
    }
  ]
}
```

**UI Components**:
- List/Grid hiển thị danh sách bài test
- Badge trạng thái (Chưa làm / Đang làm / Đã hoàn thành)
- Filter theo trạng thái (optional)
- Click vào item → Navigate đến màn "Chi tiết bài test"

**Navigation**:
- Click vào bài test → Màn "Chi tiết bài test" (nếu chưa làm) hoặc "Kết quả bài test" (nếu đã làm)

---

### 2.2. Màn hình: "Kết quả kiểm tra"

**Mô tả**: Danh sách các bài test đã làm, có filter theo loại

**API Endpoint**:
```
GET /api/users/students/my-exam-results/?exam_type=placement
```

**Query Parameters**:
- `exam_type` (optional): `placement`, `midterm`, `final`, `practice`

**Headers**:
```
Authorization: Bearer <token>
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "exam_instance_id": "uuid",
      "title": "Placement Test - January 2024",
      "exam_type": "placement",
      "score": 6.5,
      "submitted_at": "2024-01-10T14:00:00Z",
      "teacher_comment": "Good performance"
    }
  ]
}
```

**UI Components**:
- Filter tabs: Tất cả / Đầu vào / Giữa khóa / Cuối khóa / Tự do
- List hiển thị kết quả
- Click vào item → Navigate đến màn "Chi tiết kết quả"

**Navigation**:
- Click vào kết quả → Màn "Chi tiết kết quả bài test"

---

### 2.3. Màn hình: "Làm test" (Test tự do)

**Mô tả**: Danh sách các bài test tự do để học viên luyện tập

**API Endpoint**:
```
GET /api/users/students/practice-tests/
```

**Headers**:
```
Authorization: Bearer <token>
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "TOEIC Full Test - Practice 1",
      "duration": 120, // phút
      "total_questions": 200,
      "status": "published",
      "has_attempted": true,
      "last_score": 750.0,
      "generated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**UI Components**:
- List/Grid hiển thị danh sách test tự do
- Badge "Đã làm" nếu `has_attempted = true`
- Hiển thị điểm lần làm gần nhất
- Button "Làm bài" / "Làm lại"

**Navigation Flow**:
1. Click "Làm bài" → Màn "Chọn loại test"
   - Options: Đầy đủ / Theo kỹ năng / Theo Part
2. Chọn loại → Màn "Chọn kỹ năng/Part" (nếu cần)
3. Chọn kỹ năng/Part → Màn "Làm bài test"
4. Hoàn thành → Màn "Kết quả bài test"

**API Endpoints cho flow làm test**:
```
# Bắt đầu làm test
POST /api/tests/exam-instances/{id}/start/?student_id={student_id}

# Nộp bài và tính điểm
POST /api/tests/exam-results/{id}/finish/
```

---

## 3. NHÓM BÀI TẬP

### 3.1. Màn hình: "Bài tập của tôi"

**Mô tả**: Danh sách các bài tập được giao (đã làm và chưa làm)

**API Endpoint**:
```
GET /api/assignment/my-homework/
```

**Query Parameters**:
- `status` (optional): `draft`, `published`, `closed`
- `session` (optional): UUID của session

**Headers**:
```
Authorization: Bearer <token>
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "Bài tập Unit 1",
      "description": "...",
      "due_date": "2024-01-20",
      "status": "published",
      "session": {
        "id": "uuid",
        "class_name": "TOEIC Intermediate - Class A"
      },
      "has_submission": true, // đã nộp chưa
      "submission_status": "graded" // submitted, graded, resubmit_required
    }
  ]
}
```

**UI Components**:
- List hiển thị bài tập
- Badge trạng thái deadline (Sắp đến hạn / Quá hạn)
- Badge trạng thái nộp bài (Chưa nộp / Đã nộp / Đã chấm)
- Filter theo trạng thái
- Click vào item → Navigate đến màn "Chi tiết bài tập"

**Navigation**:
- Click vào bài tập → Màn "Chi tiết bài tập"
  - Nếu chưa nộp: Hiển thị đề bài + Button "Làm bài" (enable/disable theo deadline)
  - Nếu đã nộp: Hiển thị đề bài + Button "Xem bài nộp" (enable)

**API Endpoints cho chi tiết bài tập**:
```
# Xem chi tiết bài tập
GET /api/assignment/my-homework/{id}/

# Bắt đầu làm bài
GET /api/assignment/my-homework/{id}/start/

# Nộp bài
POST /api/assignment/my-homework/{id}/submit/

# Xem kết quả
GET /api/assignment/my-homework/{id}/result/
```

---

### 3.2. Màn hình: "Bài đã nộp"

**Mô tả**: Danh sách các bài tập đã nộp với điểm và đánh giá

**API Endpoint**:
```
GET /api/assignment/submissions/
```

**Headers**:
```
Authorization: Bearer <token>
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "assignment": {
        "id": "uuid",
        "title": "Bài tập Unit 1",
        "due_date": "2024-01-20"
      },
      "status": "graded", // submitted, graded, resubmit_required
      "result": 8.5,
      "correct_count": 17,
      "total_question": 20,
      "submitted_at": "2024-01-18T10:00:00Z",
      "teacher_comment": "Good work!"
    }
  ]
}
```

**UI Components**:
- List hiển thị bài đã nộp
- Hiển thị điểm số
- Hiển thị đánh giá của giáo viên
- Badge trạng thái (Đã nộp / Đã chấm / Yêu cầu nộp lại)
- Click vào item → Navigate đến màn "Chi tiết bài nộp"

**Navigation**:
- Click vào bài nộp → Màn "Chi tiết bài nộp"
  - Hiển thị nội dung đã nộp
  - Hiển thị điểm và đánh giá
  - Button "Nộp lại" (nếu status = resubmit_required)

**API Endpoints**:
```
# Xem chi tiết bài nộp
GET /api/assignment/submissions/{id}/

# Nộp lại bài
POST /api/assignment/submissions/{id}/resubmit/
```

---

## 4. NHÓM LỚP HỌC

### 4.1. Màn hình: "Lớp học của tôi"

**Mô tả**: Danh sách các lớp học (đã hoàn thành, đang diễn ra, sắp diễn ra)

**API Endpoint**:
```
GET /api/users/students/my-classes/?status=ongoing
```

**Query Parameters**:
- `status` (optional): `completed`, `ongoing`, `planned`

**Headers**:
```
Authorization: Bearer <token>
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "TOEIC Intermediate - Class A",
      "course_name": "TOEIC Intermediate",
      "teacher_name": "Nguyễn Văn A",
      "start_date": "2024-01-15",
      "end_date": "2024-04-15",
      "status": "ongoing", // completed, ongoing, planned
      "enrollment_date": "2024-01-10"
    }
  ]
}
```

**UI Components**:
- Tabs: Tất cả / Đã hoàn thành / Đang diễn ra / Sắp diễn ra
- List/Grid hiển thị lớp học
- Badge trạng thái
- Click vào item → Navigate đến màn "Chi tiết lớp học"

**Navigation**:
- Click vào lớp → Màn "Chi tiết lớp học"

**API Endpoint cho chi tiết lớp học**:
```
GET /api/classes/{id}/
```

**Màn hình: "Chi tiết lớp học"**

**UI Components**:
- Thông tin lớp: Tên, Khóa học, Giáo viên, Lịch học
- Danh sách học viên (chỉ thông tin của học viên đó)
- Button "Bài tập của lớp" → Navigate đến màn "Bài tập của lớp"
- Button "Điểm danh" → Navigate đến màn "Điểm danh của tôi"

---

### 4.2. Màn hình: "Đăng ký lớp học"

**Mô tả**: Flow đăng ký lớp học (6 bước)

**Flow chi tiết**:

#### **Bước 1: Kiểm tra điểm xác định trình độ**

**API Endpoint**:
```
GET /api/users/students/my-level/
```

**Logic**:
- Nếu có điểm → Chuyển Bước 2
- Nếu chưa có điểm → Hiển thị màn "Chưa có điểm xác định trình độ"
  - Message: "Vui lòng cập nhật trình độ của bạn để chọn khóa học phù hợp"
  - Button "Làm test" → Navigate đến màn "Test đầu vào"
  - Button "Cập nhật chứng chỉ" → Navigate đến màn "Cập nhật chứng chỉ"

**Màn hình: "Cập nhật chứng chỉ"**

**API Endpoint**:
```
POST /api/users/students/{student_id}/certificates/
```

**Request Body**:
```json
{
  "certificate_type": "ielts", // ielts, toeic, toefl, cambridge, other
  "certificate_name": "IELTS Academic",
  "score": 6.5,
  "reading_score": 6.5,
  "listening_score": 7.0,
  "speaking_score": 6.0,
  "writing_score": 6.5,
  "image_url": "https://...",
  "issued_date": "2024-01-01",
  "expiry_date": "2025-01-01",
  "notes": ""
}
```

**Màn hình: "Test đầu vào"**

**API Endpoints**:
```
# Lấy danh sách placement tests
GET /api/tests/exam-instances/placement-tests/?student_id={student_id}

# Bắt đầu làm test
POST /api/tests/exam-instances/{id}/start/?student_id={student_id}

# Nộp bài
POST /api/tests/exam-results/{id}/finish/
```

---

#### **Bước 2: Chọn khóa học**

**API Endpoint**:
```
GET /api/courses/courses/
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "TOEIC Intermediate",
      "description": "...",
      "min_entry_score": 5.0,
      "is_eligible": true // dựa trên trình độ của học viên
    }
  ]
}
```

**UI Components**:
- List hiển thị khóa học
- Badge "Đủ điều kiện" / "Không đủ điều kiện"
- Button "Đăng ký" (enable/disable theo `is_eligible`)
- Click vào khóa học → Navigate đến màn "Chi tiết khóa học"

**API Endpoint cho chi tiết khóa học**:
```
GET /api/courses/courses/{id}/
```

---

#### **Bước 3: Chọn lớp học**

**API Endpoint**:
```
GET /api/courses/courses/{course_id}/eligible-classes/
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "TOEIC Intermediate - Class A",
      "teacher_name": "Nguyễn Văn A",
      "start_date": "2024-02-01",
      "end_date": "2024-05-01",
      "current_student_count": 15,
      "limit_slot": 20,
      "status": "planned",
      "is_available": true // có slot và đã có giáo viên
    }
  ]
}
```

**UI Components**:
- List hiển thị lớp học
- Hiển thị số slot còn lại
- Badge trạng thái
- Button "Chọn lớp" (enable/disable theo `is_available`)
- Click vào lớp → Navigate đến Bước 4

---

#### **Bước 4: Xác nhận thông tin lớp**

**API Endpoint**:
```
GET /api/classes/{id}/
```

**UI Components**:
- Hiển thị thông tin lớp đầy đủ
- Button "Thanh toán" → Navigate đến Bước 5

---

#### **Bước 5: Thanh toán**

**API Endpoint**:
```
POST /api/enrollment/enrollments/
```

**Request Body**:
```json
{
  "class_id": "uuid",
  "payment_method": "cash" // hoặc "vnpay", "momo"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "invoice_status": "pending",
    "amount": 5000000,
    "due_date": "2024-01-17", // 2 ngày từ khi tạo
    "payment_url": "https://..." // nếu payment_method = vnpay/momo
  }
}
```

**UI Components**:
- Radio buttons: Tiền mặt / VNPay / MoMo
- Hiển thị số tiền
- Hiển thị thời hạn thanh toán (2 ngày)
- Button "Xác nhận thanh toán"
  - Nếu tiền mặt: Hiển thị thông báo "Vui lòng nộp tiền tại trung tâm"
  - Nếu VNPay/MoMo: Redirect đến payment gateway

**API Endpoint cho payment callback**:
```
GET /api/enrollment/payments/{gateway}/return/
POST /api/enrollment/payments/{gateway}/notify/
```

---

#### **Bước 6: Hoàn thành đăng ký**

**UI Components**:
- Thông báo "Đăng ký lớp thành công!"
- Button "Xem thời khóa biểu" → Navigate đến màn "Lịch học" hoặc hiển thị schedule ngay

**API Endpoint để xem schedule ngay sau khi đăng ký**:
```
GET /api/enrollment/enrollments/{enrollment_id}/schedule/
```

**Response**:
```json
{
  "enrollment_id": "uuid",
  "class": {
    "id": "uuid",
    "name": "TOEIC Intermediate - Class A",
    "course": {
      "id": "uuid",
      "name": "TOEIC Intermediate",
      "level": "intermediate"
    },
    "teacher": {
      "id": "uuid",
      "name": "Nguyễn Văn A"
    },
    "campus": {
      "id": "uuid",
      "name": "Campus A"
    },
    "start_date": "2024-02-01",
    "end_date": "2024-05-01",
    "weekday": [2, 4, 6], // Thứ 3, 5, 7
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
        "sessions": [...]
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
  "note": "Sessions chưa được tạo trong database, schedule được tính toán dựa trên thông tin lớp" // (nếu sessions chưa có)
}
```

**Lưu ý**: 
- API này tự động tính toán schedule dựa trên thông tin lớp (weekday, time_slot, start_date, end_date) nếu sessions chưa được tạo trong database
- Schedule sẽ hiển thị ngay sau khi đăng ký thành công, không cần chờ sessions được tạo

---

### 4.3. Màn hình: "Lịch học"

**Mô tả**: Thời khóa biểu theo tuần

**API Endpoint**:
```
GET /api/users/students/my-schedule/?week_start=2024-01-15
```

**Query Parameters**:
- `week_start` (optional): YYYY-MM-DD (mặc định là thứ 2 của tuần hiện tại)

**Headers**:
```
Authorization: Bearer <token>
```

**Response**:
```json
{
  "success": true,
  "data": {
    "week_start": "2024-01-15",
    "week_end": "2024-01-21",
    "sessions": [
      {
        "id": "uuid",
        "class_name": "TOEIC Intermediate - Class A",
        "course_name": "TOEIC Intermediate",
        "date": "2024-01-15", // study_date từ Session model
        "start_time": "18:00:00",
        "end_time": "20:00:00",
        "room": "Room 101"
      }
    ]
  }
}
```

**UI Components**:
- Calendar/Date picker để chọn tuần
- Hiển thị lịch học theo tuần (dạng calendar hoặc list)
- Mỗi buổi học hiển thị: Tên lớp, Thời gian, Phòng học
- Click vào buổi học → Navigate đến màn "Chi tiết buổi học" (optional)

---

### 4.4. Màn hình: "Khóa học"

**Mô tả**: Danh sách các khóa học trung tâm đang cung cấp

**API Endpoint**:
```
GET /api/courses/courses/
```

**Headers**:
```
Authorization: Bearer <token>
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "TOEIC Intermediate",
      "description": "...",
      "min_entry_score": 5.0,
      "duration_weeks": 12,
      "is_eligible": true // dựa trên trình độ của học viên
    }
  ]
}
```

**UI Components**:
- List/Grid hiển thị khóa học
- Badge "Đủ điều kiện" / "Không đủ điều kiện"
- Button "Đăng ký" (enable/disable theo `is_eligible`)
- Click vào khóa học → Navigate đến màn "Chi tiết khóa học"

**API Endpoint cho chi tiết khóa học**:
```
GET /api/courses/courses/{id}/
```

**Màn hình: "Chi tiết khóa học"**

**UI Components**:
- Thông tin khóa học đầy đủ
- Giới thiệu về khóa học
- Button "Đăng ký" (enable/disable theo điều kiện đầu vào)
- Click "Đăng ký" → Navigate đến màn "Đăng ký lớp học" (Bước 3)

---

## 5. NHÓM YÊU CẦU

### 5.1. Màn hình: "Đơn xin nghỉ"

**Mô tả**: Danh sách và tạo đơn xin nghỉ

**API Endpoint - Danh sách**:
```
GET /api/users/students/leave-requests/
```

**Headers**:
```
Authorization: Bearer <token>
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "class_name": "TOEIC Intermediate - Class A",
      "session_date": "2024-01-20",
      "session_time": "18:00:00",
      "status": "pending", // pending, approved, rejected
      "created_at": "2024-01-18T10:00:00Z",
      "updated_at": "2024-01-18T10:00:00Z"
    }
  ]
}
```

**UI Components**:
- List hiển thị đơn xin nghỉ
- Badge trạng thái (Chờ duyệt / Đã duyệt / Từ chối)
- Button "Tạo đơn mới" → Navigate đến màn "Tạo đơn xin nghỉ"
- Button "Hủy đơn" (nếu status = pending và chưa được giáo viên xem)

**Màn hình: "Tạo đơn xin nghỉ"**

**API Endpoint - Tạo đơn**:
```
POST /api/users/students/leave-requests/
```

**Request Body**:
```json
{
  "class_id": "uuid",
  "session_date": "2024-01-20",
  "session_time": "18:00:00",
  "reason": "Bị ốm"
}
```

**UI Components**:
- Dropdown chọn lớp
- Date picker chọn ngày
- Time picker chọn giờ (optional)
- Textarea nhập lý do
- Button "Gửi đơn"
- Validation: Tổng số buổi nghỉ không quá 10% tổng buổi

---

### 5.2. Màn hình: "Yêu cầu bảo lưu"

**Mô tả**: Danh sách và tạo yêu cầu bảo lưu

**API Endpoint - Danh sách**:
```
GET /api/users/students/reserve-requests/
```

**Headers**:
```
Authorization: Bearer <token>
```

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "class_name": "TOEIC Intermediate - Class A",
      "start_date": "2024-02-01",
      "end_date": "2024-05-01",
      "status": "pending", // pending, approved, rejected
      "created_at": "2024-01-18T10:00:00Z",
      "updated_at": "2024-01-18T10:00:00Z"
    }
  ]
}
```

**UI Components**:
- List hiển thị yêu cầu bảo lưu
- Badge trạng thái
- Button "Tạo yêu cầu mới" → Navigate đến màn "Tạo yêu cầu bảo lưu"

**Màn hình: "Tạo yêu cầu bảo lưu"**

**API Endpoint - Tạo yêu cầu**:
```
POST /api/users/students/reserve-requests/
```

**Request Body**:
```json
{
  "class_id": "uuid",
  "start_date": "2024-02-01",
  "end_date": "2024-05-01",
  "reason": "Công việc bận"
}
```

**UI Components**:
- Dropdown chọn lớp
- Date picker chọn thời gian bảo lưu (start_date, end_date)
- Textarea nhập lý do
- Button "Gửi yêu cầu"
- Validation: Chưa học quá 20% lớp hiện tại

**Lưu ý**:
- Yêu cầu bảo lưu có thời hạn 3 tháng từ khi được duyệt
- Học viên sẽ nhận thông báo nhắc đăng ký lớp mới nếu sắp hết hạn (trước 10 ngày)

---

## 📋 TÓM TẮT API ENDPOINTS

### Trình độ
- `GET /api/users/students/my-level/` - Trình độ của tôi
- `POST /api/users/students/{student_id}/certificates/` - Cập nhật chứng chỉ

### Kiểm tra
- `GET /api/users/students/my-exams/` - Bài kiểm tra của tôi
- `GET /api/users/students/my-exam-results/` - Kết quả kiểm tra
- `GET /api/users/students/practice-tests/` - Test tự do
- `GET /api/tests/exam-instances/placement-tests/` - Danh sách placement tests
- `POST /api/tests/exam-instances/{id}/start/` - Bắt đầu làm test
- `POST /api/tests/exam-results/{id}/finish/` - Nộp bài test

### Bài tập
- `GET /api/assignment/my-homework/` - Bài tập của tôi
- `GET /api/assignment/my-homework/{id}/` - Chi tiết bài tập
- `GET /api/assignment/my-homework/{id}/start/` - Bắt đầu làm bài
- `POST /api/assignment/my-homework/{id}/submit/` - Nộp bài
- `GET /api/assignment/my-homework/{id}/result/` - Kết quả bài tập
- `GET /api/assignment/submissions/` - Bài đã nộp
- `GET /api/assignment/submissions/{id}/` - Chi tiết bài nộp
- `POST /api/assignment/submissions/{id}/resubmit/` - Nộp lại bài

### Lớp học
- `GET /api/users/students/my-classes/` - Lớp học của tôi
- `GET /api/classes/{id}/` - Chi tiết lớp học
- `GET /api/classes/{id}/sessions/` - Danh sách sessions của lớp
- `GET /api/users/students/my-schedule/` - Lịch học theo tuần
- `GET /api/enrollment/enrollments/{id}/schedule/` - Thời khóa biểu chi tiết sau khi đăng ký
- `GET /api/courses/courses/` - Danh sách khóa học
- `GET /api/courses/courses/{id}/` - Chi tiết khóa học
- `GET /api/courses/courses/{course_id}/eligible-classes/` - Lớp học đủ điều kiện
- `POST /api/enrollment/enrollments/` - Đăng ký lớp học
- `GET /api/enrollment/payments/{gateway}/return/` - Payment callback

### Yêu cầu
- `GET /api/users/students/leave-requests/` - Danh sách đơn xin nghỉ
- `POST /api/users/students/leave-requests/` - Tạo đơn xin nghỉ
- `GET /api/users/students/reserve-requests/` - Danh sách yêu cầu bảo lưu
- `POST /api/users/students/reserve-requests/` - Tạo yêu cầu bảo lưu

---

## 🔐 AUTHENTICATION

Tất cả các API endpoints đều yêu cầu authentication:
```
Authorization: Bearer <JWT_TOKEN>
```

Token được lấy từ:
```
POST /api/auth/login/
```

---

## 📝 LƯU Ý

1. **Phân quyền**: Học viên chỉ xem được thông tin của chính mình
2. **Validation**: Các validation logic (10% buổi nghỉ, 20% lớp học) được xử lý ở backend
3. **Thông báo**: Hệ thống có thông báo cho các sự kiện (test mới, bài tập mới, đơn được duyệt)
4. **Upload file**: Bài tập và chứng chỉ có upload file (sử dụng `image_url` hoặc `url_file`)

