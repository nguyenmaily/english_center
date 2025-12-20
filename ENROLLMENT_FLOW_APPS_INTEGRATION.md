# CÁC APP CẦN KẾT HỢP CHO LUỒNG ĐĂNG KÝ MỚI

## 📦 DANH SÁCH APP CẦN KẾT HỢP

### 1. **authentication** (App chính)
**Vai trò**: Xác thực và đăng ký
- **Models sử dụng**: `UserAccount`, `Role`
- **Endpoints liên quan**:
  - `POST /api/auth/register/` - Đăng ký student
- **Tương tác với**:
  - → `users` (tạo Student profile sau khi register)

---

### 2. **users** (App chính)
**Vai trò**: Quản lý thông tin học viên và tiến độ
- **Models sử dụng**: 
  - `Student` - Thông tin học viên
  - `StudentProgress` - Tiến độ học tập (placement_score)
- **Endpoints cần tạo**:
  - `GET /api/students/{id}/placement-result` - Xem kết quả placement test
- **Tương tác với**:
  - ← `authentication` (tạo Student sau register)
  - ← `tests` (cập nhật placement_score)
  - → `enrollment` (validate student khi enroll)
  - → `courses` (cung cấp placement_score để filter courses)

---

### 3. **tests** (App chính)
**Vai trò**: Quản lý placement test và kết quả
- **Models sử dụng**:
  - `ExamBlueprint` - Mẫu đề thi
  - `ExamInstance` - Đề thi cụ thể (placement test)
  - `ExamResult` - Kết quả thi
  - `ExamAnswer` - Câu trả lời
  - `Question`, `QuestionGroup` - Câu hỏi
- **Endpoints cần tạo/cải thiện**:
  - `GET /api/tests/placement-tests/` - Lấy danh sách placement tests
  - `POST /api/tests/exam-instances/{id}/start?student_id={id}` - Bắt đầu test (đã có, cần customize)
  - `POST /api/tests/exam-results/{id}/finish` - Nộp bài và tính điểm (đã có, cần cải thiện)
- **Logic cần thêm**:
  - Tự động cập nhật `StudentProgress.placement_score` sau khi finish exam
  - Filter ExamInstance có `exam_type = 'placement'` và `status = 'published'`
- **Tương tác với**:
  - → `users` (cập nhật StudentProgress.placement_score)
  - → `enrollment` (cung cấp exam_result_id để track)

---

### 4. **courses** (App chính)
**Vai trò**: Quản lý khóa học và gợi ý courses
- **Models sử dụng**:
  - `Course` - Khóa học
  - `Skill` - Kỹ năng trong khóa học
- **Endpoints cần tạo**:
  - `GET /api/courses/recommended?student_id={id}` - Lấy courses phù hợp
  - `GET /api/courses/{id}/eligible-classes?student_id={id}` - Lấy classes có thể đăng ký
- **Endpoints cần cải thiện**:
  - `GET /api/courses/` - Đã có filter `max_entry_score`, cần tích hợp với placement_score
- **Logic cần thêm**:
  - Filter courses: `min_entry_score <= placement_score` hoặc `min_entry_score IS NULL`
  - Tính `match_score` (% phù hợp)
  - Sort theo match_score
- **Tương tác với**:
  - ← `users` (lấy placement_score từ StudentProgress)
  - → `classes` (lấy classes của course)
  - → `enrollment` (validate course khi enroll)

---

### 5. **classes** (App chính)
**Vai trò**: Quản lý lớp học và eligible classes
- **Models sử dụng**:
  - `Class` - Lớp học
- **Endpoints cần tạo**:
  - `GET /api/courses/{id}/eligible-classes?student_id={id}` - (trong courses app nhưng query Class)
- **Endpoints cần cải thiện**:
  - `GET /api/classes/` - Đã có filter cho student, cần thêm logic eligible
- **Logic cần thêm**:
  - Filter classes: status='planned', có teacher, chưa đầy
  - Tính available_slots
- **Tương tác với**:
  - ← `courses` (lấy classes của course)
  - ← `users` (lấy Teacher info)
  - ← `campus` (lấy Campus info)
  - → `enrollment` (validate class khi enroll)
  - → `class_sessions` (lấy sessions của class)

---

### 6. **enrollment** (App chính)
**Vai trò**: Quản lý đăng ký và thanh toán
- **Models sử dụng**:
  - `Enrollment` - Đăng ký
  - `Payment` - Thanh toán
- **Endpoints cần cải thiện**:
  - `POST /api/enrollment/enrollments/` - Thêm validation placement_score
  - `GET /api/enrollment/enrollments/{id}/schedule` - Xem schedule sau enrollment
  - `GET /api/enrollment/enrollments/my-classes/` - Cải thiện schedule view
- **Endpoints đã có (giữ nguyên)**:
  - `POST /api/enrollment/enrollments/{id}/create-payment/` - Tạo payment URL
  - `GET /api/enrollment/payments/{gateway}/return/` - Payment callback
- **Logic cần thêm**:
  - Validate: `placement_score >= course.min_entry_score`
  - Tự động set `amount = course.fee`
  - Lưu `exam_result_id` (optional) vào Enrollment
- **Tương tác với**:
  - ← `users` (validate Student, lấy placement_score)
  - ← `classes` (validate Class)
  - ← `courses` (lấy course.fee, validate min_entry_score)
  - ← `tests` (lưu exam_result_id)
  - → `class_sessions` (lấy sessions để hiển thị schedule)
  - → `enrollment/services` (payment gateway)

---

### 7. **class_sessions** (App chính)
**Vai trò**: Quản lý buổi học và schedule
- **Models sử dụng**:
  - `Session` - Buổi học
  - `Attendance` - Điểm danh (mới thêm)
- **Endpoints cần tạo**:
  - `GET /api/enrollment/enrollments/{id}/schedule` - (trong enrollment app nhưng query Session)
- **Logic cần thêm**:
  - Group sessions theo tuần
  - Group sessions theo ngày
  - Tính summary: total, completed, upcoming, next session
- **Tương tác với**:
  - ← `classes` (lấy sessions của class)
  - ← `courses` (lấy Skill info)
  - ← `campus` (lấy Room info)
  - ← `users` (lấy Teacher info)
  - → `enrollment` (cung cấp schedule data)

---

### 8. **campus** (App phụ)
**Vai trò**: Cung cấp thông tin cơ sở và phòng học
- **Models sử dụng**:
  - `Campus` - Cơ sở
  - `Room` - Phòng học
- **Tương tác với**:
  - → `classes` (cung cấp campus info)
  - → `class_sessions` (cung cấp room info cho schedule)

---

### 9. **core** (App utility)
**Vai trò**: Base classes và utilities chung
- **Sử dụng**:
  - `BaseModel` - Base model với created_at, updated_at
  - `PermissionMixin` - Permission checking
  - `pagination.py` - Pagination
  - `renderers.py` - Response renderers

---

## 🔄 SƠ ĐỒ TƯƠNG TÁC GIỮA CÁC APP

```
┌─────────────────┐
│ authentication  │
│  (Register)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     users       │
│  (Student,      │
│   Progress)     │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│     tests       │  │    courses       │
│ (Placement Test)│  │ (Recommended)   │
└────────┬────────┘  └────────┬─────────┘
         │                    │
         │                    │
         └────────┬───────────┘
                  │
                  ▼
         ┌─────────────────┐
         │     classes     │
         │ (Eligible)      │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │   enrollment    │
         │ (Enroll, Pay)   │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ class_sessions  │
         │   (Schedule)    │
         └─────────────────┘
```

---

## 📋 CHI TIẾT TƯƠNG TÁC TỪNG BƯỚC

### Bước 1: Register
**App**: `authentication`
- Tạo `UserAccount`
- Tạo `Student` profile (trong `users` app)
- Tạo `StudentProgress` với `placement_score = null` (trong `users` app)

---

### Bước 2: Placement Test
**Apps**: `tests` + `users`

**Flow**:
1. `tests` app:
   - Query `ExamInstance` có `exam_type='placement'`, `status='published'`
   - Tạo `ExamResult` khi start
   - Tính điểm khi finish

2. `users` app:
   - Cập nhật `StudentProgress.placement_score` sau khi finish

**Tương tác**:
```
tests.views.finish_exam()
  └──> users.models.StudentProgress.placement_score = score
```

---

### Bước 3: Recommended Courses
**Apps**: `courses` + `users`

**Flow**:
1. `courses` app:
   - Query `StudentProgress.placement_score` từ `users` app
   - Filter `Course` có `min_entry_score <= placement_score`
   - Tính `match_score`
   - Sort và return

**Tương tác**:
```
courses.views.recommended_courses()
  └──> users.models.StudentProgress.objects.get(student_id=id)
  └──> courses.models.Course.objects.filter(min_entry_score__lte=score)
```

---

### Bước 4: Eligible Classes
**Apps**: `courses` + `classes` + `users` + `campus`

**Flow**:
1. `courses` app (endpoint):
   - Validate student có `placement_score >= course.min_entry_score`
   - Query `Class` từ `classes` app
   - Filter: status='planned', có teacher, chưa đầy
   - Join với `Teacher`, `Campus` để lấy thông tin

**Tương tác**:
```
courses.views.eligible_classes()
  └──> users.models.StudentProgress (validate score)
  └──> classes.models.Class.objects.filter(course_id=id, ...)
  └──> users.models.Teacher (select_related)
  └──> campus.models.Campus (select_related)
```

---

### Bước 5: Enrollment
**Apps**: `enrollment` + `users` + `classes` + `courses` + `tests`

**Flow**:
1. `enrollment` app:
   - Validate `Student` từ `users` app
   - Validate `Class` từ `classes` app
   - Lấy `Course` từ `class.course` (courses app)
   - Validate `placement_score >= course.min_entry_score` (users app)
   - Lưu `exam_result_id` (optional) từ `tests` app
   - Tự động set `amount = course.fee`
   - Tạo `Enrollment`

**Tương tác**:
```
enrollment.views.create_enrollment()
  └──> users.models.Student (validate)
  └──> classes.models.Class (validate)
  └──> courses.models.Course (get fee, validate min_entry_score)
  └──> users.models.StudentProgress (get placement_score)
  └──> tests.models.ExamResult (optional - lưu exam_result_id)
```

---

### Bước 6: Payment
**Apps**: `enrollment` + `enrollment/services`

**Flow**:
1. `enrollment` app:
   - Tạo `Payment` record
   - Gọi `VNPayService` hoặc `MoMoService`
   - Redirect đến payment gateway

**Tương tác**:
```
enrollment.views.create_payment()
  └──> enrollment.models.Payment (create)
  └──> enrollment.services.VNPayService (create_payment_url)
  └──> enrollment.services.MoMoService (create_payment_url)
```

---

### Bước 7: Schedule View
**Apps**: `enrollment` + `class_sessions` + `classes` + `courses` + `campus` + `users`

**Flow**:
1. `enrollment` app (endpoint):
   - Lấy `Enrollment` → `Class`
   - Query `Session` từ `class_sessions` app
   - Join với `Skill` (courses app), `Room` (campus app), `Teacher` (users app)
   - Group theo tuần/ngày
   - Tính summary

**Tương tác**:
```
enrollment.views.get_schedule()
  └──> enrollment.models.Enrollment (get)
  └──> classes.models.Class (get)
  └──> class_sessions.models.Session.objects.filter(class_id=class.id)
  └──> courses.models.Skill (select_related)
  └──> campus.models.Room (select_related)
  └──> users.models.Teacher (select_related)
```

---

## 🎯 TỔNG KẾT APP CẦN KẾT HỢP

### App chính (Bắt buộc):
1. ✅ **authentication** - Register
2. ✅ **users** - Student, StudentProgress
3. ✅ **tests** - Placement test
4. ✅ **courses** - Course recommendation
5. ✅ **classes** - Eligible classes
6. ✅ **enrollment** - Enrollment, Payment
7. ✅ **class_sessions** - Schedule

### App phụ (Hỗ trợ):
8. ✅ **campus** - Campus, Room info
9. ✅ **core** - Utilities, Permissions

### App không cần (cho luồng đăng ký):
- ❌ **assignments** - Chỉ dùng sau khi đã enroll
- ❌ **requests** - Chỉ dùng sau khi đã enroll
- ❌ **notifications** - Tùy chọn
- ❌ **reporting** - Tùy chọn

---

## 📝 FILES CẦN SỬA/TẠO

### tests/views.py
- Thêm endpoint `placement-tests/`
- Cải thiện `finish_exam()` để cập nhật `StudentProgress.placement_score`

### courses/views.py
- Thêm endpoint `recommended/`
- Thêm endpoint `{id}/eligible-classes/`
- Cải thiện `CourseListCreateView` để tích hợp placement_score

### enrollment/views.py
- Cải thiện `create()` để validate placement_score
- Thêm endpoint `{id}/schedule/`
- Cải thiện `my-classes/` để hiển thị schedule đẹp hơn

### enrollment/models.py
- Thêm field `placement_exam_result` (FK optional) vào `Enrollment`

### users/views.py (có thể cần tạo)
- Thêm endpoint `{id}/placement-result/` (optional)

---

## 🔗 DEPENDENCIES GIỮA CÁC APP

```
authentication → users
users → tests (cập nhật placement_score)
users → courses (cung cấp placement_score)
users → enrollment (validate student)
tests → enrollment (cung cấp exam_result_id)
courses → classes (lấy classes của course)
classes → enrollment (validate class)
classes → class_sessions (lấy sessions)
enrollment → class_sessions (lấy schedule)
enrollment → courses (validate course, lấy fee)
enrollment → campus (hiển thị campus info trong schedule)
class_sessions → courses (lấy skill info)
class_sessions → campus (lấy room info)
class_sessions → users (lấy teacher info)
```

---

Bạn có muốn tôi bắt đầu implement từng phần không?


