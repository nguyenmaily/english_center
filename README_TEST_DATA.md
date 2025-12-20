# HƯỚNG DẪN SỬ DỤNG DỮ LIỆU TEST

Tài liệu này hướng dẫn cách chạy script để tạo dữ liệu test cho role Teacher và Student.

---

## 📋 YÊU CẦU

- PostgreSQL database đã được setup
- Django project đã được migrate
- Các bảng đã được tạo trong database

---

## 🚀 CÁCH CHẠY

### Bước 1: Chạy script SQL

```bash
# Kết nối vào PostgreSQL
psql -U your_username -d your_database_name -f test_data_insert_teacher_student.sql

# Hoặc nếu dùng psql với connection string
psql postgresql://user:password@localhost:5432/dbname -f test_data_insert_teacher_student.sql
```

### Bước 2: Set password cho các user test

**Cách 1: Dùng Django shell**

```bash
python manage.py shell
```

Sau đó chạy:

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Set password cho teachers
for username in ['teacher1', 'teacher2', 'teacher3']:
    try:
        user = User.objects.get(username=username)
        user.set_password('123456')
        user.save()
        print(f"✓ Đã set password cho {username}")
    except User.DoesNotExist:
        print(f"✗ Không tìm thấy {username}")

# Set password cho students
for username in ['student1', 'student2', 'student3', 'student4']:
    try:
        user = User.objects.get(username=username)
        user.set_password('123456')
        user.save()
        print(f"✓ Đã set password cho {username}")
    except User.DoesNotExist:
        print(f"✗ Không tìm thấy {username}")
```

**Cách 2: Dùng script Python**

```bash
python manage.py shell < setup_test_users.py
```

Hoặc:

```bash
python setup_test_users.py
```

---

## 👥 THÔNG TIN ĐĂNG NHẬP TEST

### TEACHERS

| Username | Password | Tên | Level | Specialization | Campus |
|----------|----------|-----|-------|----------------|--------|
| teacher1 | 123456 | Nguyễn Văn Giáo | Senior | IELTS Speaking | Cơ sở Quận 1 |
| teacher2 | 123456 | Trần Thị Dạy | Expert | TOEIC | Cơ sở Quận 1 |
| teacher3 | 123456 | Lê Văn Mới | Junior | IELTS Writing | Cơ sở Quận 3 |

### STUDENTS

| Username | Password | Tên | Target Score | Status |
|----------|----------|-----|--------------|--------|
| student1 | 123456 | Phạm Văn Học | 7 (IELTS) | Committed |
| student2 | 123456 | Nguyễn Thị Sinh | 750 (TOEIC) | Committed |
| student3 | 123456 | Lê Văn Viên | 6.5 (IELTS) | Committed |
| student4 | 123456 | Trần Thị Học | 8 (IELTS) | Not Committed |

---

## 📊 DỮ LIỆU ĐÃ TẠO

### 1. Classes (Lớp học)

#### Lớp có giáo viên và học viên:
- **IELTS Foundation - Lớp 1** (ID: `70000000-0000-0000-0000-000000000001`)
  - Status: `ongoing` (Đang diễn ra)
  - Teacher: teacher1
  - Students: student1, student2, student3
  - Lịch: Thứ 3, 5, 7 - 18:30-20:30
  - Start: 2024-01-15, End: 2024-04-15

- **TOEIC Intermediate - Lớp 1** (ID: `70000000-0000-0000-0000-000000000002`)
  - Status: `ongoing` (Đang diễn ra)
  - Teacher: teacher2
  - Students: student1, student2
  - Lịch: Thứ 4, 6 - 19:00-21:00
  - Start: 2024-01-10, End: 2024-03-10

#### Lớp chưa có giáo viên (để test đăng ký):
- **IELTS Foundation - Lớp 2** (ID: `70000000-0000-0000-0000-000000000004`)
  - Status: `planned`
  - Teacher: NULL
  - Students: 0
  - Lịch: Thứ 4, 6 - 18:30-20:30
  - Start: 2024-02-15, End: 2024-05-15

- **TOEIC Advanced - Lớp 1** (ID: `70000000-0000-0000-0000-000000000005`)
  - Status: `planned`
  - Teacher: NULL
  - Students: 0
  - Lịch: Thứ 3, 5, 7 - 19:00-21:00
  - Start: 2024-02-20, End: 2024-05-20

#### Lớp có giáo viên nhưng chưa có học viên (để test hủy đăng ký):
- **IELTS Foundation - Lớp 3** (ID: `70000000-0000-0000-0000-000000000006`)
  - Status: `planned`
  - Teacher: teacher3
  - Students: 0
  - Lịch: Thứ 4, 6 - 18:00-20:00
  - Start: 2024-03-01, End: 2024-06-01

### 2. Sessions (Buổi học)

- **Session hôm nay** (ID: `80000000-0000-0000-0000-000000000001`)
  - Class: IELTS Foundation - Lớp 1
  - Date: Hôm nay
  - Time: 18:30-20:30
  - Status: `current` (Đang diễn ra) - Để test điểm danh

- **Session tuần trước** (ID: `80000000-0000-0000-0000-000000000003`)
  - Class: IELTS Foundation - Lớp 1
  - Date: 7 ngày trước
  - Time: 18:30-20:30
  - Status: `past` (Đã diễn ra)
  - Đã có điểm danh

- **Session tuần tới** (ID: `80000000-0000-0000-0000-000000000002`)
  - Class: IELTS Foundation - Lớp 1
  - Date: 7 ngày tới
  - Time: 18:30-20:30
  - Status: `upcoming` (Sắp diễn ra)

### 3. Assignments (Bài tập)

- **Bài tập Unit 1** (ID: `a0000000-0000-0000-0000-000000000001`)
  - Session: Session hôm nay
  - Status: `published`
  - Deadline: 5 ngày tới
  - Có 2 bài nộp (student1, student2) - chưa chấm

- **Bài tập Unit 2** (ID: `a0000000-0000-0000-0000-000000000002`)
  - Session: Session tuần trước
  - Status: `closed`
  - Deadline: 2 ngày trước
  - Có 2 bài nộp:
    - student3: đã chấm (graded, 85.5 điểm)
    - student1: yêu cầu nộp lại (resubmit_required)

### 4. Leave Requests (Đơn xin nghỉ)

- **Đơn 1**: student1 - Lớp 1 - Status: `pending` (Chờ duyệt)
- **Đơn 2**: student2 - Lớp 1 - Status: `teacher_approved` (Đã được giáo viên duyệt)
- **Đơn 3**: student3 - Lớp 1 - Status: `rejected` (Bị từ chối)

### 5. Attendances (Điểm danh)

- Session tuần trước:
  - student1: `present` (Có mặt)
  - student2: `late` (Muộn)
  - student3: `absent` (Vắng)

---

## 🧪 CÁC TEST CASE CÓ THỂ THỰC HIỆN

### Role TEACHER:

1. **TRÌNH ĐỘ CỦA TÔI**
   - Login: teacher1
   - API: `GET /api/users/teachers/my-level/`
   - Expected: Hiển thị level: senior, specialization: IELTS Speaking

2. **ĐĂNG KÝ LỚP HỌC**
   - Login: teacher3
   - API: `GET /api/users/teachers/available-classes/`
   - Expected: Thấy 2 lớp chưa có giáo viên (Lớp 2, Lớp 5)
   - API: `POST /api/users/teachers/register-class/` với class_id của Lớp 2
   - Expected: Đăng ký thành công
   - Test trùng lịch: Đăng ký Lớp 5 (cùng thời gian với Lớp 2)
   - Expected: Lỗi "Bạn đã có lớp vào thời gian này"

3. **HỦY ĐĂNG KÝ**
   - Login: teacher3
   - API: `POST /api/users/teachers/cancel-class-registration/` với Lớp 3
   - Expected: Hủy thành công (vì chưa có học viên)
   - Test với Lớp 1 (đã có học viên)
   - Expected: Lỗi "Không thể hủy đăng ký vì lớp đã có học viên"

4. **LỊCH DẠY CỦA TÔI**
   - Login: teacher1
   - API: `GET /api/users/teachers/my-schedule/?week_start=2024-01-15`
   - Expected: Thấy các sessions của Lớp 1

5. **QUẢN LÝ BÀI TẬP**
   - Login: teacher1
   - API: `GET /api/assignment/`
   - Expected: Thấy 2 bài tập (Unit 1, Unit 2)
   - API: `GET /api/assignment/a0000000-0000-0000-0000-000000000001/submissions/`
   - Expected: Thấy 2 bài nộp
   - API: `PATCH /api/assignment/teacher-submissions/b0000000-0000-0000-0000-000000000001/grade/`
   - Body: `{"result": 85.5, "status": "graded", "content": "Tốt"}`
   - Expected: Chấm điểm thành công
   - API: `PATCH /api/assignment/teacher-submissions/b0000000-0000-0000-0000-000000000002/request-resubmit/`
   - Expected: Yêu cầu nộp lại thành công
   - Test yêu cầu nộp lại lần 2
   - Expected: Lỗi "Bạn chỉ có thể yêu cầu nộp lại 1 lần"

6. **LỚP DẠY CỦA TÔI**
   - Login: teacher1
   - API: `GET /api/users/teachers/my-classes/`
   - Expected: Thấy Lớp 1
   - API: `GET /api/users/teachers/classes/70000000-0000-0000-0000-000000000001/sessions/`
   - Expected: Thấy 3 sections: past_sessions, current_sessions, upcoming_sessions
   - API: `GET /api/users/teachers/sessions/80000000-0000-0000-0000-000000000001/attendance/`
   - Expected: Thấy 3 học viên
   - API: `POST /api/users/teachers/sessions/80000000-0000-0000-0000-000000000001/attendance/`
   - Body: `{"attendances": [{"student_id": "...", "status": "present"}, ...]}`
   - Expected: Điểm danh thành công

7. **ĐƠN XIN NGHỈ**
   - Login: teacher1
   - API: `GET /api/users/teachers/leave-requests/`
   - Expected: Thấy 3 đơn xin nghỉ
   - API: `PATCH /api/users/teachers/leave-requests/c0000000-0000-0000-0000-000000000001/approval/`
   - Body: `{"action": "approve"}`
   - Expected: Status → `teacher_approved`
   - API: `PATCH /api/users/teachers/leave-requests/c0000000-0000-0000-0000-000000000001/approval/`
   - Body: `{"action": "reject"}`
   - Expected: Status → `rejected`

### Role STUDENT:

1. **TRÌNH ĐỘ CỦA TÔI**
   - Login: student1
   - API: `GET /api/users/students/my-level/`
   - Expected: Hiển thị trình độ (nếu có)

2. **BÀI TẬP**
   - Login: student1
   - API: `GET /api/assignment/my-homework/`
   - Expected: Thấy các bài tập
   - API: `GET /api/assignment/my-homework/a0000000-0000-0000-0000-000000000001/`
   - Expected: Thấy chi tiết bài tập
   - API: `POST /api/assignment/my-homework/a0000000-0000-0000-0000-000000000001/submit/`
   - Expected: Nộp bài thành công

3. **LỚP HỌC**
   - Login: student1
   - API: `GET /api/users/students/my-classes/`
   - Expected: Thấy 2 lớp (Lớp 1, Lớp 2)

4. **LỊCH HỌC**
   - Login: student1
   - API: `GET /api/users/students/my-schedule/?week_start=2024-01-15`
   - Expected: Thấy lịch học

5. **ĐƠN XIN NGHỈ**
   - Login: student1
   - API: `GET /api/users/students/leave-requests/`
   - Expected: Thấy đơn xin nghỉ của student1
   - API: `POST /api/users/students/leave-requests/`
   - Body: `{"class_id": "...", "session_date": "...", "reason": "..."}`
   - Expected: Tạo đơn thành công

---

## ⚠️ LƯU Ý

1. **Password**: Script SQL tạo user với password hash dummy. **BẮT BUỘC** phải chạy script set password sau khi insert SQL.

2. **UUID**: Các UUID trong script là cố định để dễ test. Nếu database đã có dữ liệu, có thể bị conflict.

3. **Dates**: Script sử dụng `CURRENT_DATE` và `CURRENT_TIMESTAMP` để tự động tính toán ngày. Đảm bảo timezone của database đúng.

4. **Foreign Keys**: Script sử dụng `ON CONFLICT DO NOTHING` hoặc `ON CONFLICT DO UPDATE` để tránh lỗi khi chạy lại.

5. **Cleanup**: Nếu muốn xóa dữ liệu test, uncomment phần DELETE ở đầu script SQL.

---

## 🔍 KIỂM TRA DỮ LIỆU

Sau khi chạy script, có thể kiểm tra bằng các query:

```sql
-- Đếm số lượng
SELECT 'Teachers' as table_name, COUNT(*) as count FROM teachers
UNION ALL
SELECT 'Students', COUNT(*) FROM students
UNION ALL
SELECT 'Classes', COUNT(*) FROM classes
UNION ALL
SELECT 'Sessions', COUNT(*) FROM sessions
UNION ALL
SELECT 'Enrollments', COUNT(*) FROM enrollments
UNION ALL
SELECT 'Assignments', COUNT(*) FROM assignments
UNION ALL
SELECT 'Submissions', COUNT(*) FROM submissions
UNION ALL
SELECT 'Leave Requests', COUNT(*) FROM leave_requests
UNION ALL
SELECT 'Attendances', COUNT(*) FROM attendances;

-- Kiểm tra lớp chưa có giáo viên
SELECT id, name, status, teacher_id 
FROM classes 
WHERE teacher_id IS NULL AND status = 'planned';

-- Kiểm tra lớp có học viên
SELECT c.id, c.name, COUNT(e.id) as student_count
FROM classes c
LEFT JOIN enrollments e ON e.class_id = c.id
WHERE e.invoice_status = 'paid'
GROUP BY c.id, c.name;
```

---

## 📝 GHI CHÚ

- Script này tạo dữ liệu đủ để test tất cả các chức năng của Teacher và Student
- Có thể mở rộng thêm dữ liệu nếu cần test các edge cases
- Nên backup database trước khi chạy script

