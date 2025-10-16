# 🧪 API TEST GUIDE - English Center

## 📋 **DANH SÁCH TEST API CHO TẤT CẢ APPS**

### **🔧 Cấu hình cơ bản:**
- **Base URL:** `http://localhost:8000/api`
- **Content-Type:** `application/json`
- **Method:** GET, POST, PUT, PATCH, DELETE

---

## **1️⃣ CLASSES APP** - Quản lý lớp học

### **📚 Test Cases:**

#### **1.1 Lấy danh sách lớp học**
```http
GET /api/classes/
```

#### **1.2 Tạo lớp học mới (Manager)**
```http
POST /api/classes/
Content-Type: application/json

{
    "name": "IELTS-F2-2025",
    "start_date": "2025-11-01",
    "end_date": "2026-02-28",
    "course_id": "uuid-của-course", 
    "weekday": [2, 4, 6],
    "time_slot": "18:30-20:30",
    "campus_id": "uuid-của-campus",
    "manager_id": "uuid-của-manager",
    "limit_slot": 25,
    "is_public": true
}
```

#### **1.3 Xem chi tiết lớp học**
```http
GET /api/classes/{class_id}/
```

#### **1.4 Cập nhật lớp học (PATCH - khuyến nghị)**
```http
PATCH /api/classes/{class_id}/
Content-Type: application/json

{
    "name": "IELTS-F2-2025 Updated",
    "limit_slot": 30
}
```

#### **1.4.1 Cập nhật lớp học (PUT - cần tất cả fields)**
```http
PUT /api/classes/{class_id}/
Content-Type: application/json

{
    "name": "IELTS-F2-2025 Updated",
    "course_id": "uuid-của-course",
    "limit_slot": 30
}
```

#### **1.5 Xóa lớp học**
```http
DELETE /api/classes/{class_id}/
```

#### **1.6 Lấy danh sách buổi học của lớp**
```http
GET /api/classes/{class_id}/sessions/
```

#### **1.7 Giảng viên đăng ký dạy lớp**
```http
POST /api/classes/{class_id}/register-teacher/
Content-Type: application/json

{
    "teacher_id": "uuid-của-teacher"
}
```

#### **1.8 Lấy lớp học của giảng viên**
```http
GET /api/classes/my/
```

#### **1.9 Admin/Manager gán giảng viên**
```http
POST /api/classes/{class_id}/assign-teacher/
Content-Type: application/json

{
    "teacher_id": "uuid-của-teacher"
}
```

#### **1.10 Xóa giảng viên khỏi lớp**
```http
DELETE /api/classes/{class_id}/teacher/
```

---

## **2️⃣ ENROLLMENT APP** - Đăng ký + Thanh toán

### **📚 Test Cases:**

#### **2.1 Lấy danh sách đăng ký**
```http
GET /api/enrollments/
```

#### **2.2 Học viên đăng ký lớp**
```http
POST /api/enrollments/
Content-Type: application/json

{
    "student_id": "uuid-của-student",
    "class_id": "uuid-của-class",
    "amount": 6000000,
    "due_date": "2025-11-15",
    "notes": "Thanh toán đợt 1"
}
```

#### **2.3 Xem thông tin thanh toán**
```http
GET /api/enrollments/{enrollment_id}/payment-info/
```

#### **2.4 Xem lịch học của học viên**
```http
GET /api/enrollments/my-classes/
```

#### **2.5 Cập nhật thông tin thanh toán**
```http
PATCH /api/enrollments/{enrollment_id}/update-payment/
Content-Type: application/json

{
    "invoice_status": "paid",
    "amount": 6000000
}
```

#### **2.6 Thống kê thanh toán**
```http
GET /api/enrollments/payment-stats/
```

---

## **3️⃣ CLASS_SESSIONS APP** - Buổi học + Điểm danh + Bài tập

### **📚 Test Cases:**

#### **3.1 Lấy danh sách buổi học**
```http
GET /api/sessions/
```

#### **3.2 Tạo buổi học mới**
```http
POST /api/sessions/
Content-Type: application/json

{
    "study_date": "2025-10-20",
    "start_time": "18:30",
    "end_time": "20:30",
    "skill_id": "uuid-của-skill",
    "class_id": "uuid-của-class",
    "room_id": "uuid-của-room",
    "teacher_id": "uuid-của-teacher"
}
```

#### **3.3 Xem lịch học của học viên**
```http
GET /api/sessions/my-schedule/?start_date=2025-10-01&end_date=2025-10-31
```

#### **3.4 Xem buổi học sắp tới**
```http
GET /api/sessions/my-upcoming/
```

#### **3.5 Xem buổi học hôm nay của giảng viên**
```http
GET /api/sessions/my-today/
```

#### **3.6 Lấy bài tập của buổi học**
```http
GET /api/sessions/{session_id}/assignments/
```

#### **3.7 Thống kê buổi dạy của giảng viên**
```http
GET /api/sessions/my-stats/?start_date=2025-10-01&end_date=2025-10-31
```

#### **3.8 Lấy danh sách điểm danh**
```http
GET /api/attendances/
```

#### **3.9 Điểm danh học viên**
```http
POST /api/attendances/
Content-Type: application/json

{
    "student_id": "uuid-của-student",
    "session_id": "uuid-của-session",
    "status": "present"
}
```

#### **3.10 Cập nhật điểm danh**
```http
PATCH /api/attendances/{attendance_id}/
Content-Type: application/json

{
    "status": "late"
}
```

#### **3.11 Xem điểm danh của học viên**
```http
GET /api/attendances/my/
```

---

## **4️⃣ REQUESTS APP** - Yêu cầu nghỉ/đặt chỗ

### **📚 Test Cases:**

#### **4.1 Lấy danh sách yêu cầu nghỉ**
```http
GET /api/leave-requests/
```

#### **4.2 Tạo yêu cầu nghỉ**
```http
POST /api/leave-requests/
Content-Type: application/json

{
    "student_id": "uuid-của-student",
    "class_id": "uuid-của-class",
    "session_date": "2025-10-25",
    "session_time": "18:30"
}
```

#### **4.3 Xem yêu cầu nghỉ của học viên**
```http
GET /api/leave-requests/my/
```

#### **4.4 Giảng viên duyệt yêu cầu nghỉ**
```http
PATCH /api/leave-requests/{request_id}/teacher-approval/
Content-Type: application/json

{
    "action": "approve"
}
```

#### **4.5 Manager duyệt yêu cầu nghỉ**
```http
PATCH /api/leave-requests/{request_id}/manager-approval/
Content-Type: application/json

{
    "action": "approve"
}
```

#### **4.6 Lấy danh sách yêu cầu đặt chỗ**
```http
GET /api/reserve-requests/
```

#### **4.7 Tạo yêu cầu đặt chỗ**
```http
POST /api/reserve-requests/
Content-Type: application/json

{
    "student_id": "uuid-của-student",
    "class_id": "uuid-của-class",
    "start_date": "2025-11-01",
    "end_date": "2025-11-15"
}
```

---

## **5️⃣ TESTS APP** - Test và đánh giá

### **📚 Test Cases:**

#### **5.1 Lấy danh sách nhóm câu hỏi**
```http
GET /api/question-groups/
```

#### **5.2 Tạo nhóm câu hỏi**
```http
POST /api/question-groups/
Content-Type: application/json

{
    "part": "1",
    "skill": "listening",
    "context": "Nghe đoạn hội thoại",
    "audio_file": "https://example.com/audio.mp3"
}
```

#### **5.3 Lấy danh sách câu hỏi**
```http
GET /api/questions/
```

#### **5.4 Tạo câu hỏi**
```http
POST /api/questions/
Content-Type: application/json

{
    "group_id": "uuid-của-group",
    "text": "Câu hỏi mẫu?",
    "option_a": "Đáp án A",
    "option_b": "Đáp án B",
    "option_c": "Đáp án C",
    "option_d": "Đáp án D",
    "correct_answer": "B",
    "difficulty": "medium"
}
```

#### **5.5 Lấy danh sách mẫu đề thi**
```http
GET /api/exam-blueprints/
```

#### **5.6 Tạo mẫu đề thi**
```http
POST /api/exam-blueprints/
Content-Type: application/json

{
    "exam_type": "placement",
    "title": "Bài kiểm tra đầu vào",
    "duration": 60,
    "total_questions": 50
}
```

#### **5.7 Lấy danh sách quy tắc đề thi**
```http
GET /api/exam-rules/
```

#### **5.8 Tạo quy tắc đề thi**
```http
POST /api/exam-rules/
Content-Type: application/json

{
    "blueprint_id": "uuid-của-blueprint",
    "part": "1",
    "skill": "listening",
    "difficulty": "easy",
    "num_questions": 10
}
```

#### **5.9 Lấy danh sách đề thi**
```http
GET /api/exam-instances/
```

#### **5.10 Tạo đề thi từ mẫu**
```http
POST /api/exam-instances/generate/
Content-Type: application/json

{
    "blueprint_id": "uuid-của-blueprint",
    "name": "Đề Placement 02"
}
```

#### **5.11 Học viên bắt đầu làm bài**
```http
POST /api/exam-instances/{exam_id}/start/
Content-Type: application/json

{
    "student_id": "uuid-của-student"
}
```

#### **5.12 Nộp câu trả lời**
```http
POST /api/exam-results/{result_id}/submit-answer/
Content-Type: application/json

{
    "question_id": "uuid-của-question",
    "answer": "B"
}
```

#### **5.13 Hoàn thành bài thi**
```http
POST /api/exam-results/{result_id}/finish/
```

#### **5.14 Xem kết quả của học viên**
```http
GET /api/exam-results/student/{student_id}/
```

#### **5.15 Lấy danh sách tiến độ học viên**
```http
GET /api/student-progress/
```

#### **5.16 Cập nhật tiến độ học viên**
```http
PATCH /api/student-progress/{progress_id}/
Content-Type: application/json

{
    "placement_score": 80.5,
    "final_status": "pass"
}
```

---

## **🔍 SAMPLE DATA IDs (Từ data bạn đã insert):**

### **Users:**
- Admin: `admin.ly` 
- Teacher: `gv.nguyena`, `gv.tranb`
- Manager: `ql.hoangc`
- Students: `hv.minhd`, `hv.linh e`

### **Classes:**
- `IELTS-F1-2025` (ongoing)
- `TOEIC-A2-2025` (planned)

### **Courses:**
- `IELTS Foundation`
- `TOEIC Advanced`

### **Sessions:**
- 2025-10-16 (Listening)
- 2025-10-18 (Reading)
- 2025-10-21 (TOEIC RC)

---

## **📝 LƯU Ý KHI TEST:**

1. **Thay thế UUID:** Sử dụng UUID thực từ database thay vì placeholder
2. **Authentication:** Có thể cần thêm token nếu có authentication
3. **Validation:** Kiểm tra response status codes (200, 201, 400, 404, 500)
4. **Data Integrity:** Đảm bảo foreign key relationships đúng
5. **Error Handling:** Test các trường hợp lỗi (invalid data, missing fields)

---

## **🚀 QUICK TEST COMMANDS:**

```bash
# Test basic connectivity
curl http://localhost:8000/api/classes/
curl http://localhost:8000/api/enrollments/
curl http://localhost:8000/api/sessions/
curl http://localhost:8000/api/leave-requests/
curl http://localhost:8000/api/questions/
```

**Happy Testing! 🎉**

