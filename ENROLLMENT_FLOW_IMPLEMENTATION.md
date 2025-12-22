# TÀI LIỆU CHI TIẾT: IMPLEMENTATION FLOW ĐĂNG KÝ LỚP HỌC

## TỔNG QUAN

Flow đăng ký lớp học gồm 6 bước, mỗi bước có logic và API riêng. Document này mô tả chi tiết logic implementation dựa trên các câu trả lời đã được xác nhận.

---

## BƯỚC 1: KIỂM TRA ĐIỂM XÁC ĐỊNH TRÌNH ĐỘ

### 1.1. API: GET /api/users/students/my-level/

**Mục đích:** Kiểm tra học viên đã có điểm xác định trình độ chưa

**Logic:**
1. Lấy `student` từ `request.user.student_profile`
2. Query `StudentCertificate` với:
   - `student = student`
   - `status = 'VERIFIED'`
   - `expired_date >= today`
   - Sắp xếp theo `test_date DESC`
3. Lấy điểm LR và SW riêng biệt:
   ```python
   current_lr = StudentCertificate.objects.filter(
       student=student,
       skill_group='LR',
       status='VERIFIED',
       expired_date__gte=today
   ).order_by('-test_date').first()
   
   current_sw = StudentCertificate.objects.filter(
       student=student,
       skill_group='SW',
       status='VERIFIED',
       expired_date__gte=today
   ).order_by('-test_date').first()
   ```

**Response Format:**
```json
{
  "success": true,
  "data": {
    "lr": {
      "score": 850,
      "test_date": "2024-01-01",
      "expired_date": "2026-01-01",
      "source_type": "certificate"
    },
    "sw": {
      "score": 300,
      "test_date": "2024-02-01",
      "expired_date": "2024-08-01",
      "source_type": "entry_test"
    }
  }
}
```

**Nếu không có điểm hoặc hết hạn:**
```json
{
  "success": true,
  "data": {
    "lr": null,
    "sw": null
  },
  "message": "Vui lòng cập nhật trình độ của bạn để chọn khóa học phù hợp"
}
```

**Frontend Logic:**
- Nếu cả `lr` và `sw` đều `null` → Hiển thị màn "Chưa có điểm xác định trình độ"
- Nếu có ít nhất 1 điểm → Chuyển Bước 2
- **QUAN TRỌNG:** Không bắt buộc phải có cả 2, chỉ check khi chọn course cụ thể

### 1.2. Cập nhật chứng chỉ

**API:** `POST /api/proficiency/upload-certificate/` (dùng endpoint hiện có)

**Request Body:** (theo format hiện tại - TOEIC LR/SW)
```json
{
  "skill_group": "LR",
  "score_1": 450,
  "score_2": 400,
  "total_score": 850,
  "test_date": "2024-01-01",
  "proof_image": "file"
}
```

**Logic:** Đã có trong `proficiency/views.py` - UploadCertificateView

### 1.3. Placement Test

**API:** `GET /api/tests/exam-instances/placement-tests/?student_id={student_id}`

**Logic:**
1. Filter `ExamInstance` với `exam_type = 'placement'`
2. Phân biệt 2 bài test: LR và SW
   - Có thể dựa vào `title` hoặc `description` của exam
   - Hoặc có field riêng để phân biệt
3. Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "Placement Test - Listening & Reading",
      "exam_type": "placement",
      "skill_group": "LR",
      "duration": 120,
      "total_questions": 100
    },
    {
      "id": "uuid",
      "title": "Placement Test - Speaking & Writing",
      "exam_type": "placement",
      "skill_group": "SW",
      "duration": 60,
      "total_questions": 50
    }
  ]
}
```

**Các API khác:**
- `POST /api/tests/exam-instances/{id}/start/?student_id={student_id}` - Đã có
- `POST /api/tests/exam-results/{id}/finish/` - Đã có

**Sau khi hoàn thành placement test:**
- Kết quả tự động cập nhật vào `StudentCertificate` qua signal
- Signal: `proficiency/signals.py` - `update_proficiency_from_final_test`
- Cần update signal để xử lý placement test (exam_type = 'placement')

---

## BƯỚC 2: CHỌN KHÓA HỌC

### 2.1. API: GET /api/courses/courses/

**Logic tính `is_eligible`:**
1. Lấy `skill` từ `course.skill` (từ migration Course-Skill)
2. Xác định `skill_group` từ `skill.skill_group` (property trong Skill model)
3. Lấy điểm học viên từ `StudentCertificate`:
   ```python
   student_cert = StudentCertificate.objects.filter(
       student=student,
       skill_group=skill_group,  # LR hoặc SW
       status='VERIFIED',
       expired_date__gte=today
   ).order_by('-test_date').first()
   ```
4. So sánh:
   - Nếu `course.min_entry_score` là `null` → `is_eligible = true`
   - Nếu `student_cert` là `null` → `is_eligible = false`
   - Nếu `student_cert.total_score >= course.min_entry_score` → `is_eligible = true`
   - Ngược lại → `is_eligible = false`

**Response Format:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "TOEIC Intermediate",
      "description": "...",
      "level": "intermediate",
      "min_entry_score": 450,
      "fee": 5000000,
      "skill": {
        "id": "uuid",
        "name": "Listening-Reading",
        "skill_group": "LR"
      },
      "is_eligible": true
    }
  ]
}
```

**Permissions:**
- `view_courses` - Có thể public (mọi người xem được)

---

## BƯỚC 3: CHỌN LỚP HỌC

### 3.1. API: GET /api/courses/courses/{course_id}/eligible-classes/

**Logic "eligible":**
1. Filter classes:
   - `course_id = course_id`
   - `status = 'planned'` (chỉ lớp chưa bắt đầu)
   - `teacher_id IS NOT NULL` (phải có giáo viên)
   - `current_student_count < limit_slot` (còn slot)
   - Nếu `limit_slot IS NULL` → coi là không giới hạn (luôn eligible nếu có giáo viên)

2. Filter theo campus (optional):
   - Query param: `campus_id`
   - Nếu có → filter thêm `campus_id = campus_id`

3. Tính `is_available`:
   ```python
   is_available = (
       cls.status == 'planned' and
       cls.teacher_id is not None and
       (cls.limit_slot is None or cls.current_student_count < cls.limit_slot)
   )
   ```

**Response Format:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "TOEIC Intermediate - Class A",
      "teacher_name": "Nguyễn Văn A",
      "teacher_id": "uuid",
      "start_date": "2024-02-01",
      "end_date": "2024-05-01",
      "current_student_count": 15,
      "limit_slot": 20,
      "available_slots": 5,
      "status": "planned",
      "is_available": true,
      "fee": 5000000,
      "campus": {
        "id": "uuid",
        "name": "Campus A"
      },
      "weekday": [2, 4, 6],
      "time_slot": "18:00-20:00"
    }
  ]
}
```

**Permissions:**
- `view_classes` - Có thể public

---

## BƯỚC 4: XÁC NHẬN THÔNG TIN LỚP

### 4.1. API: GET /api/classes/{id}/

**Response cần thêm:**
- `fee` từ `course.fee`
- `available_slots` (đã có trong serializer)
- `teacher_name` (đã có trong serializer)
- Thông tin thanh toán: `due_date` (2 ngày từ khi tạo enrollment)

**Response Format:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "TOEIC Intermediate - Class A",
    "course": {
      "id": "uuid",
      "name": "TOEIC Intermediate",
      "fee": 5000000
    },
    "teacher_name": "Nguyễn Văn A",
    "campus": {
      "id": "uuid",
      "name": "Campus A"
    },
    "start_date": "2024-02-01",
    "end_date": "2024-05-01",
    "current_student_count": 15,
    "limit_slot": 20,
    "available_slots": 5,
    "weekday": [2, 4, 6],
    "time_slot": "18:00-20:00"
  }
}
```

---

## BƯỚC 5: THANH TOÁN

### 5.1. API: POST /api/enrollment/enrollments/

**Request Body:**
```json
{
  "class_id": "uuid",
  "payment_method": "cash"  // hoặc "vnpay"
}
```

**Logic xử lý:**
1. Validate:
   - `class_id` phải tồn tại
   - Class phải có `status = 'planned'` (không cho đăng ký `ongoing`, `finished`, `canceled`)
   - Class phải còn slot
   - Class phải có giáo viên
   - **Kiểm tra trùng lịch học:** Học viên tại 1 thời điểm chỉ có thể học 1 lớp
     ```python
     # Lấy tất cả enrollments của học viên (trừ canceled)
     existing_enrollments = Enrollment.objects.filter(
         student_id=student.id
     ).exclude(
         invoice_status='canceled'
     ).select_related('class_id')
     
     # Lấy các lớp học từ enrollments
     existing_classes = Class.objects.filter(
         id__in=[e.class_id for e in existing_enrollments]
     )
     
     # Lấy lớp mới muốn đăng ký
     new_class = Class.objects.get(id=class_id)
     
     # Kiểm tra trùng thời gian
     for existing_class in existing_classes:
         # Trùng nếu: (new_start <= existing_end) AND (new_end >= existing_start)
         if (new_class.start_date and existing_class.end_date and
             new_class.end_date and existing_class.start_date):
             if (new_class.start_date <= existing_class.end_date and 
                 new_class.end_date >= existing_class.start_date):
                 # TRÙNG LỊCH → KHÔNG CHO ĐĂNG KÝ
                 return Response({
                     'success': False,
                     'error': f'Bạn đã đăng ký lớp "{existing_class.name}" '
                              f'({existing_class.start_date} - {existing_class.end_date}). '
                              f'Không thể đăng ký lớp "{new_class.name}" '
                              f'({new_class.start_date} - {new_class.end_date}) vì trùng lịch học.'
                 }, status=status.HTTP_400_BAD_REQUEST)
     ```

2. Lấy `amount` từ `course.fee`:
   ```python
   class_obj = Class.objects.get(id=class_id)
   amount = class_obj.course.fee
   ```

3. Xử lý theo `payment_method`:
   - **`cash`:**
     - `invoice_status = 'pending'`
     - `due_date = today + 2 ngày`
     - `payment_url = null`
   
   - **`vnpay`:**
     - `invoice_status = 'pending'`
     - `due_date = today + 2 ngày`
     - Tạo payment URL từ VNPay API
     - `payment_url = "https://sandbox.vnpayment.vn/..."`

4. Tạo enrollment:
   ```python
   enrollment = Enrollment.objects.create(
       student_id=student.id,
       class_id=class_id,
       amount=amount,
       invoice_status='pending',
       due_date=due_date
   )
   ```

**Response Format:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "invoice_status": "pending",
    "amount": 5000000,
    "due_date": "2024-01-17",
    "payment_url": "https://...",  // null nếu cash
    "confirmation": {
      "message": "Học viên Nguyễn Văn A đã đăng ký thành công lớp TOEIC Intermediate - Class A vào thời điểm 2024-01-15 10:30:00",
      "student_name": "Nguyễn Văn A",
      "class_name": "TOEIC Intermediate - Class A",
      "enrollment_date": "2024-01-15T10:30:00Z",
      "pdf_url": "/api/enrollment/enrollments/{id}/confirmation-pdf/"
    }
  }
}
```

### 5.2. VNPay Integration

**Cần implement:**
- Tạo payment URL từ VNPay
- Callback URLs:
  - `GET /api/enrollment/payments/vnpay/return/` - Return URL (sau khi thanh toán)
  - `POST /api/enrollment/payments/vnpay/notify/` - IPN URL (VNPay gọi để notify)

**Logic callback:**
1. Verify signature từ VNPay
2. Kiểm tra `vnp_ResponseCode`:
   - `00` = thành công
   - Khác = thất bại
3. Update `invoice_status`:
   - Thành công → `'paid'`
   - Thất bại → `'pending'` (hoặc `'failed'`)

**File cần tạo:**
- `enrollment/payment_gateway.py` - VNPay integration
- `enrollment/payment_views.py` - Callback views
- `VNPAY_INTEGRATION.md` - Hướng dẫn setup

---

## BƯỚC 6: HOÀN THÀNH ĐĂNG KÝ - SCHEDULE

### 6.1. API: GET /api/enrollment/enrollments/{enrollment_id}/schedule/

**Logic tính schedule:**

1. **Kiểm tra sessions trong DB:**
   ```python
   sessions = Session.objects.filter(class_session_id=class_id).order_by('study_date', 'start_time')
   ```

2. **Nếu có sessions trong DB:**
   - Dùng sessions từ DB
   - Format theo `by_week`

3. **Nếu không có sessions trong DB:**
   - Tính toán từ thông tin class:
     - `weekday` (ví dụ: [2, 4, 6] = Thứ 3, 5, 7)
     - `time_slot` (ví dụ: "18:00-20:00")
     - `start_date`
     - `end_date`
   - Logic tính:
     ```python
     from datetime import timedelta
     
     current_date = class_obj.start_date
     sessions = []
     
     while current_date <= class_obj.end_date:
         # weekday: 1=Mon, 2=Tue, ..., 7=Sun
         # Python weekday(): 0=Mon, 1=Tue, ..., 6=Sun
         if (current_date.weekday() + 1) in class_obj.weekday:
             sessions.append({
                 'study_date': current_date,
                 'start_time': start_time,  # từ time_slot
                 'end_time': end_time,      # từ time_slot
                 'skill': None,
                 'room': None,
                 'teacher': {
                     'id': class_obj.teacher.id,
                     'name': teacher_name
                 }
             })
         current_date += timedelta(days=1)
     ```

**Format response `by_week`:**
```json
{
  "success": true,
  "data": {
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
              "id": "uuid",  // null nếu tính toán
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
      ]
    },
    "summary": {
      "total_sessions": 36,
      "completed_sessions": 0,  // study_date < today
      "upcoming_sessions": 36,  // study_date >= today
      "next_session": {
        "date": "2024-02-01",
        "start_time": "18:00",
        "end_time": "20:00",
        "skill": null,
        "room": null
      }  // null nếu không có session sắp tới
    }
  }
}
```

**Logic tính summary:**
```python
today = timezone.now().date()

total_sessions = len(sessions)
completed_sessions = sum(1 for s in sessions if s['study_date'] < today)
upcoming_sessions = sum(1 for s in sessions if s['study_date'] >= today)

next_session = next(
    (s for s in sessions if s['study_date'] >= today),
    None
)
```

**Note:** Không cần field `note` trong response

### 6.2. PDF Confirmation - Xác nhận đăng ký

**API:** `GET /api/enrollment/enrollments/{enrollment_id}/confirmation-pdf/`

**Mục đích:** Download PDF xác nhận đăng ký lớp học

**Logic:**
1. Lấy enrollment từ `enrollment_id`
2. Verify student có quyền xem (chỉ student đã đăng ký mới xem được)
3. Tạo PDF với nội dung:
   - Tiêu đề: "XÁC NHẬN ĐĂNG KÝ LỚP HỌC"
   - Thông tin học viên: Tên, Email, SĐT
   - Thông tin lớp: Tên lớp, Khóa học, Giáo viên, Campus
   - Thông tin đăng ký: Ngày đăng ký, Số tiền, Phương thức thanh toán
   - Thông tin lớp học: Ngày bắt đầu, Ngày kết thúc, Lịch học
   - Footer: Chữ ký, con dấu (nếu có)

**Response:**
- Content-Type: `application/pdf`
- Headers:
  ```
  Content-Disposition: attachment; filename="xac-nhan-dang-ky-{enrollment_id}.pdf"
  ```

**Thư viện cần dùng:**
- `reportlab` hoặc `weasyprint` để tạo PDF
- Hoặc `xhtml2pdf` nếu dùng HTML template

**Template PDF:**
```
═══════════════════════════════════════════════════════════
        XÁC NHẬN ĐĂNG KÝ LỚP HỌC
═══════════════════════════════════════════════════════════

Học viên: Nguyễn Văn A
Email: nguyenvana@example.com
Số điện thoại: 0123456789

Đã đăng ký thành công lớp học:

Tên lớp: TOEIC Intermediate - Class A
Khóa học: TOEIC Intermediate
Giáo viên: Trần Thị B
Cơ sở: Campus A

Thông tin đăng ký:
- Ngày đăng ký: 15/01/2024 10:30:00
- Số tiền: 5,000,000 VNĐ
- Phương thức thanh toán: Tiền mặt
- Trạng thái: Chờ thanh toán
- Hạn thanh toán: 17/01/2024

Thông tin lớp học:
- Ngày bắt đầu: 01/02/2024
- Ngày kết thúc: 01/05/2024
- Lịch học: Thứ 3, 5, 7 (18:00 - 20:00)

═══════════════════════════════════════════════════════════
Ngày in: 15/01/2024
Mã đăng ký: {enrollment_id}
═══════════════════════════════════════════════════════════
```

**Response trong POST enrollment:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "invoice_status": "pending",
    "amount": 5000000,
    "due_date": "2024-01-17",
    "payment_url": null,
    "confirmation": {
      "message": "Học viên Nguyễn Văn A đã đăng ký thành công lớp TOEIC Intermediate - Class A vào thời điểm 15/01/2024 10:30:00",
      "student_name": "Nguyễn Văn A",
      "class_name": "TOEIC Intermediate - Class A",
      "enrollment_date": "2024-01-15T10:30:00Z",
      "pdf_download_url": "/api/enrollment/enrollments/{id}/confirmation-pdf/"
    }
  }
}
```

---

## PERMISSIONS & AUTHENTICATION

### Permissions cần thiết:

1. **Student only:**
   - `GET /api/users/students/my-level/` - `manage_proficiency_profile`
   - `POST /api/enrollment/enrollments/` - `manage_enrollments` (hoặc tạo mới)
   - `GET /api/enrollment/enrollments/{id}/schedule/` - `view_enrollments` (hoặc tạo mới)

2. **Public hoặc authenticated:**
   - `GET /api/courses/courses/` - `view_courses`
   - `GET /api/courses/courses/{id}/` - `view_courses`
   - `GET /api/courses/courses/{course_id}/eligible-classes/` - `view_classes`
   - `GET /api/classes/{id}/` - `view_classes`

3. **Cần tạo permissions mới:**
   - `manage_enrollments` - Cho phép student đăng ký lớp
   - `view_enrollments` - Cho phép xem enrollment của mình

### Authentication:
- Tất cả API đều cần `IsAuthenticated`
- `student_id` lấy từ `request.user.student_profile.id` (không cần query param)

---

## VALIDATIONS

### Validation khi đăng ký:

1. **Class status:**
   - ❌ Không cho đăng ký: `status IN ('ongoing', 'finished', 'canceled')`
   - ✅ Chỉ cho đăng ký: `status = 'planned'`

2. **Class capacity:**
   - Kiểm tra `current_student_count < limit_slot`
   - Nếu `limit_slot IS NULL` → không giới hạn

3. **Teacher:**
   - Class phải có `teacher_id`

4. **Duplicate enrollment:**
   - ✅ **CÓ** check duplicate - học viên chỉ có thể đăng ký 1 lớp duy nhất 1 lần
   - Model đã có `unique_together = ('student_id', 'class_id')` - **GIỮ LẠI**
   - **Lưu ý quan trọng:** 
     - Học viên **KHÔNG** thể đăng ký cùng 1 lớp 2 lần
     - Nhưng học viên **CÓ THỂ** đăng ký 1 khóa học nhiều lần (nếu có nhiều lớp khác nhau của cùng 1 khóa học)
     - Ví dụ: Khóa "TOEIC Intermediate" có 3 lớp A, B, C → Học viên có thể đăng ký cả 3 lớp

5. **Time conflict validation - Trùng lịch học:**
   - ✅ **QUAN TRỌNG:** Học viên tại 1 thời điểm chỉ có thể học 1 lớp
   - **Logic kiểm tra:**
     ```python
     # Lấy tất cả enrollments của học viên (trừ canceled)
     existing_enrollments = Enrollment.objects.filter(
         student_id=student.id
     ).exclude(
         invoice_status='canceled'  # hoặc status nào đó nếu có
     ).select_related('class_id')
     
     # Lấy các lớp học từ enrollments
     existing_classes = [e.class_id for e in existing_enrollments]
     
     # Lấy lớp mới muốn đăng ký
     new_class = Class.objects.get(id=class_id)
     
     # Kiểm tra trùng thời gian
     for existing_class in existing_classes:
         # Trùng nếu: (new_start <= existing_end) AND (new_end >= existing_start)
         if (new_class.start_date <= existing_class.end_date and 
             new_class.end_date >= existing_class.start_date):
             # TRÙNG LỊCH → KHÔNG CHO ĐĂNG KÝ
             raise ValidationError(
                 f"Bạn đã đăng ký lớp '{existing_class.name}' "
                 f"({existing_class.start_date} - {existing_class.end_date}). "
                 f"Không thể đăng ký lớp '{new_class.name}' "
                 f"({new_class.start_date} - {new_class.end_date}) vì trùng lịch học."
             )
     ```
   
   - **Ví dụ:**
     - Lớp A: 7/11/2025 - 7/1/2026
     - Lớp B: 5/1/2026 - 5/3/2026 → ❌ **KHÔNG được đăng ký** (trùng: 5/1/2026 nằm trong 7/11/2025 - 7/1/2026)
     - Lớp C: 8/1/2026 - 8/3/2026 → ✅ **ĐƯỢC đăng ký** (không trùng: 8/1/2026 >= 8/1/2026, sau khi lớp A kết thúc)
   
   - **Lưu ý:**
     - Chỉ check các enrollment có `invoice_status != 'canceled'` (hoặc status tương ứng)
     - Nếu lớp không có `start_date` hoặc `end_date` → bỏ qua validation này (hoặc xử lý riêng)
     - Có thể cho phép đăng ký nếu lớp cũ đã kết thúc (end_date < today)

---

## SESSIONS CREATION LOGIC

### Phân tích từ codebase:

1. **Hiện tại:** Sessions có thể được tạo:
   - Thủ công bởi admin/manager
   - Tự động qua `_maybe_generate_sessions` trong `ClassViewSet.perform_update`

2. **Logic đề xuất:**
   - **Không tự động tạo sessions khi đăng ký**
   - Sessions chỉ được tạo khi:
     - Admin/Manager tạo thủ công
     - Hoặc khi class chuyển sang `status = 'ongoing'`
   - **Schedule API sẽ tính toán từ class info nếu chưa có sessions**

3. **Lý do:**
   - Sessions liên quan đến điểm danh và bài tập
   - Cần quản lý chặt chẽ
   - Có thể thay đổi (thêm/bớt session)

---

## TÓM TẮT CÁC API CẦN TẠO/SỬA

### APIs cần tạo mới:

1. ✅ `GET /api/users/students/my-level/` - Kiểm tra điểm trình độ
2. ✅ `GET /api/tests/exam-instances/placement-tests/?student_id={student_id}` - Lấy placement tests
3. ✅ `GET /api/courses/courses/{course_id}/eligible-classes/` - Lấy lớp học eligible
4. ✅ `GET /api/enrollment/enrollments/{enrollment_id}/schedule/` - Lấy schedule
5. ✅ `GET /api/enrollment/enrollments/{enrollment_id}/confirmation-pdf/` - Download PDF xác nhận đăng ký
6. ✅ `GET /api/enrollment/payments/vnpay/return/` - VNPay return URL
7. ✅ `POST /api/enrollment/payments/vnpay/notify/` - VNPay IPN URL

### APIs cần sửa:

1. ✅ `GET /api/courses/courses/` - Thêm `is_eligible` và logic tính
2. ✅ `POST /api/enrollment/enrollments/` - Thêm `payment_method`, xử lý VNPay
3. ✅ `GET /api/classes/{id}/` - Thêm `fee`, `available_slots`

### Signals cần sửa:

1. ✅ `proficiency/signals.py` - Xử lý placement test (exam_type = 'placement')

---

## NEXT STEPS

Sau khi bạn duyệt document này, tôi sẽ:
1. ✅ Implement tất cả APIs
2. ✅ Tạo VNPay integration
3. ✅ Update signals
4. ✅ Tạo permissions mới
5. ✅ Test toàn bộ flow

---

**Status:** ⏳ Chờ duyệt
**Ngày tạo:** [Ngày hiện tại]

---

## PHẦN FRONTEND - Ý TƯỞNG UI/UX

### Tổng quan

Flow đăng ký lớp học sẽ là một **wizard/stepper** gồm 6 bước. Mỗi bước có UI riêng với navigation rõ ràng, validation real-time, và feedback cho người dùng.

---

## BƯỚC 1: KIỂM TRA ĐIỂM XÁC ĐỊNH TRÌNH ĐỘ

### UI/UX Ý tưởng:

**1.1. Màn hình chính - Check Level:**
- **Layout:** Card trung tâm với icon lớn (bi-clipboard-check hoặc bi-graph-up)
- **Hiển thị:**
  - Nếu có điểm: 2 cards lớn hiển thị điểm LR và SW
    - Card màu xanh nếu còn hạn
    - Card màu vàng nếu sắp hết hạn (cảnh báo)
    - Card màu xám nếu đã hết hạn
  - Nếu không có điểm: Card cảnh báo màu cam với icon warning
- **Buttons:**
  - "Tiếp tục đăng ký" (nếu có điểm) → Chuyển Bước 2
  - "Cập nhật chứng chỉ" → Mở modal hoặc navigate
  - "Làm test đầu vào" → Navigate đến placement test

**1.2. Modal/Page "Cập nhật chứng chỉ":**
- Form upload ảnh với preview
- Dropdown chọn skill_group (LR/SW)
- Input điểm số với validation
- Progress indicator khi đang xử lý OCR
- Thông báo kết quả:
  - ✅ "Chứng chỉ đã được xác thực tự động"
  - ⏳ "Đang chờ admin duyệt" (nếu không khớp)

**1.3. Màn hình "Test đầu vào":**
- List 2 cards: "Placement Test - LR" và "Placement Test - SW"
- Mỗi card có:
  - Badge trạng thái (Có thể làm / Đã làm / Đang chờ)
  - Button "Bắt đầu làm bài"
  - Hiển thị điểm nếu đã làm
- Click "Bắt đầu" → Navigate đến trang làm bài test

---

## BƯỚC 2: CHỌN KHÓA HỌC

### UI/UX Ý tưởng:

**2.1. Layout:**
- **Header:** Breadcrumb (Trang chủ > Đăng ký lớp học > Chọn khóa học)
- **Filter sidebar (optional):**
  - Filter theo level (Beginner, Intermediate, Advanced)
  - Filter theo skill (LR, SW)
  - Search box
- **Main content:** Grid cards hiển thị khóa học

**2.2. Course Card Design:**
- **Header:** Tên khóa học (font lớn, bold)
- **Badge:** 
  - ✅ "Đủ điều kiện" (màu xanh) nếu `is_eligible = true`
  - ❌ "Không đủ điều kiện" (màu đỏ) nếu `is_eligible = false`
  - Hiển thị lý do: "Yêu cầu điểm tối thiểu: 450" (nếu không đủ)
- **Content:**
  - Mô tả ngắn
  - Level badge
  - Skill badge (LR/SW)
  - Học phí (format: 5,000,000 VNĐ)
- **Footer:**
  - Button "Xem chi tiết" (luôn enable)
  - Button "Đăng ký" (enable/disable theo `is_eligible`)
- **Hover effect:** Shadow, scale nhẹ

**2.3. Course Detail Modal/Page:**
- Full mô tả khóa học
- Danh sách kỹ năng sẽ học
- Thông tin về giáo viên
- Lịch học mẫu
- Button "Chọn lớp học" → Chuyển Bước 3

**2.4. Empty State:**
- Nếu không có khóa học nào: Icon + message "Chưa có khóa học phù hợp"

---

## BƯỚC 3: CHỌN LỚP HỌC

### UI/UX Ý tưởng:

**3.1. Layout:**
- **Header:** 
  - Tên khóa học đã chọn (badge)
  - Button "Quay lại chọn khóa học"
- **Filter:**
  - Dropdown chọn Campus
  - Toggle "Chỉ hiển thị lớp còn slot"
- **Main content:** List/Grid các lớp học

**3.2. Class Card Design:**
- **Header:** Tên lớp + Badge trạng thái (planned)
- **Info section:**
  - 📅 Lịch học: "Thứ 3, 5, 7 | 18:00 - 20:00"
  - 👨‍🏫 Giáo viên: Tên giáo viên
  - 📍 Campus: Tên campus
  - 📅 Thời gian: "01/02/2024 - 01/05/2024"
  - 👥 Số slot: "15/20" với progress bar
- **Footer:**
  - Button "Chọn lớp" (enable/disable theo `is_available`)
  - Badge "Đã đầy" nếu không còn slot
  - Badge "Chưa có giáo viên" nếu thiếu giáo viên

**3.3. Empty State:**
- Nếu không có lớp eligible: 
  - Icon + message "Không có lớp học phù hợp"
  - Button "Quay lại chọn khóa học khác"

**3.4. Loading State:**
- Skeleton cards khi đang load

---

## BƯỚC 4: XÁC NHẬN THÔNG TIN LỚP

### UI/UX Ý tưởng:

**4.1. Layout:**
- **Card lớn** hiển thị thông tin đầy đủ
- **2 sections:**
  - Bên trái: Thông tin lớp học
  - Bên phải: Thông tin thanh toán

**4.2. Thông tin lớp học:**
- Tên lớp (heading lớn)
- Khóa học (badge)
- Giáo viên (với avatar nếu có)
- Campus (với địa chỉ)
- Lịch học (calendar icon + text)
- Thời gian (start_date - end_date)
- Số slot còn lại (highlight)

**4.3. Thông tin thanh toán:**
- Học phí: **5,000,000 VNĐ** (font lớn, bold)
- Phương thức thanh toán: Radio buttons
  - 💵 Tiền mặt
  - 💳 VNPay
- Thời hạn thanh toán: "2 ngày từ khi đăng ký"
- Button "Xác nhận thanh toán" (primary, lớn)

**4.4. Validation:**
- Disable button nếu chưa chọn payment_method
- Hiển thị tooltip/alert nếu thiếu thông tin

---

## BƯỚC 5: THANH TOÁN

### UI/UX Ý tưởng:

**5.1. Processing State:**
- Loading spinner khi đang tạo enrollment
- Message: "Đang xử lý đăng ký..."

**5.2. Success State - Tiền mặt:**
- ✅ Icon checkmark lớn (màu xanh)
- Message: "Đăng ký thành công!"
- Thông tin enrollment:
  - Mã đăng ký
  - Thời hạn thanh toán
  - Địa chỉ nộp tiền
- **Actions:**
  - Button "Tải PDF xác nhận" (download PDF)
  - Button "Xem lịch học" → Chuyển Bước 6
  - Button "Về trang chủ"

**5.3. Success State - VNPay:**
- ✅ Icon checkmark
- Message: "Đang chuyển hướng đến cổng thanh toán..."
- Auto redirect sau 2-3 giây
- Hoặc button "Thanh toán ngay" nếu không auto redirect
- Hiển thị QR code nếu có

**5.4. Error Handling:**
- ❌ Icon error (màu đỏ)
- Message lỗi cụ thể:
  - "Lớp đã đầy"
  - "Bạn đã đăng ký lớp này rồi"
  - "Trùng lịch học với lớp khác"
- Button "Thử lại" hoặc "Chọn lớp khác"

---

## BƯỚC 6: HOÀN THÀNH ĐĂNG KÝ - SCHEDULE

### UI/UX Ý tưởng:

**6.1. Layout:**
- **Header:** 
  - Tên lớp học
  - Badge "Đã đăng ký"
- **Tabs:**
  - Tab "Lịch học" (active)
  - Tab "Thông tin lớp"
  - Tab "Tài liệu" (nếu có)

**6.2. Schedule View - By Week:**
- **Timeline theo tuần:**
  - Mỗi tuần là 1 card
  - Header: "Tuần 1 (01/02 - 07/02)"
  - List sessions trong tuần:
    - Mỗi session là 1 row với:
      - 📅 Ngày (badge)
      - ⏰ Thời gian (18:00 - 20:00)
      - 👨‍🏫 Giáo viên
      - 📍 Phòng (nếu có)
- **Navigation:**
  - Button "Tuần trước" / "Tuần sau"
  - Hoặc dropdown chọn tuần

**6.3. Summary Card:**
- **Stats:**
  - Tổng số buổi học: 36
  - Đã hoàn thành: 0 (màu xám)
  - Sắp tới: 36 (màu xanh)
- **Next Session:**
  - Card highlight buổi học tiếp theo
  - Countdown timer (nếu sắp đến)
  - Button "Xem chi tiết"

**6.4. Empty State (nếu chưa có sessions):**
- Message: "Lịch học sẽ được cập nhật sớm"
- Hiển thị thông tin lớp (weekday, time_slot) để học viên biết lịch

**6.5. Actions:**
- Button "Tải PDF xác nhận" (icon download)
- Button "Thêm vào lịch" (Google Calendar, iCal)
- Button "Chia sẻ" (nếu cần)

---

## COMPONENTS TÁI SỬ DỤNG

### 1. Stepper/Wizard Component:
- Progress bar ở top
- Hiển thị 6 bước: "Kiểm tra điểm" → "Chọn khóa" → "Chọn lớp" → "Xác nhận" → "Thanh toán" → "Hoàn thành"
- Active step highlight
- Completed steps có checkmark

### 2. Course Card Component:
- Reusable cho nhiều màn hình
- Props: course data, isEligible, onClick

### 3. Class Card Component:
- Reusable
- Props: class data, isAvailable, onClick

### 4. Alert/Notification Component:
- Success (xanh)
- Warning (vàng)
- Error (đỏ)
- Info (xanh dương)
- Auto dismiss sau 5 giây

### 5. Loading Skeleton:
- Skeleton cho course cards
- Skeleton cho class cards
- Skeleton cho schedule

### 6. Modal Component:
- Course detail modal
- Confirmation modal
- Payment method selection modal

---

## RESPONSIVE DESIGN

### Mobile (< 768px):
- **Bước 1-3:** Full width cards, stack vertically
- **Bước 4:** Stack sections vertically
- **Bước 5:** Full width buttons
- **Bước 6:** Schedule hiển thị dạng list, không phải grid

### Tablet (768px - 1024px):
- 2 columns cho course/class cards
- Sidebar filter có thể collapse

### Desktop (> 1024px):
- 3-4 columns cho course/class cards
- Sidebar filter luôn hiển thị
- Schedule có thể hiển thị calendar view

---

## UX ENHANCEMENTS

### 1. Progress Saving:
- Lưu state vào localStorage
- Nếu refresh page → restore về bước đã làm
- Clear khi hoàn thành

### 2. Back Navigation:
- Button "Quay lại" ở mỗi bước
- Confirm nếu đã nhập dữ liệu

### 3. Validation Real-time:
- Validate ngay khi user nhập
- Hiển thị error message dưới field
- Disable submit nếu có lỗi

### 4. Loading States:
- Skeleton khi load data
- Spinner khi submit
- Progress bar cho upload file

### 5. Success Feedback:
- Animation khi thành công (confetti, checkmark)
- Sound notification (optional)
- Toast notification

### 6. Error Handling:
- Friendly error messages
- Retry button
- Support contact info

### 7. Accessibility:
- Keyboard navigation
- Screen reader support
- Focus indicators
- ARIA labels

---

## COLOR SCHEME

### Primary Colors:
- **Success/Đủ điều kiện:** `#28a745` (Bootstrap success)
- **Warning/Sắp hết hạn:** `#ffc107` (Bootstrap warning)
- **Error/Không đủ điều kiện:** `#dc3545` (Bootstrap danger)
- **Info/Neutral:** `#17a2b8` (Bootstrap info)

### Status Colors:
- **Planned:** Xanh dương
- **Ongoing:** Xanh lá
- **Completed:** Xám
- **Canceled:** Đỏ

---

## ANIMATIONS & TRANSITIONS

### 1. Page Transitions:
- Fade in/out khi chuyển bước
- Slide animation

### 2. Card Animations:
- Hover: Scale 1.02, shadow
- Click: Ripple effect
- Load: Fade in từ dưới lên

### 3. Button Animations:
- Loading spinner
- Success checkmark animation
- Error shake animation

---

## NAVIGATION FLOW

```
Dashboard/Home
    ↓
[Button "Đăng ký lớp học"]
    ↓
Bước 1: Kiểm tra điểm
    ├─ Có điểm → Bước 2
    ├─ Không có điểm → Modal "Cập nhật chứng chỉ" hoặc "Làm test"
    └─ Sau khi cập nhật → Bước 2
    ↓
Bước 2: Chọn khóa học
    ├─ Click "Xem chi tiết" → Modal
    └─ Click "Đăng ký" → Bước 3
    ↓
Bước 3: Chọn lớp học
    ├─ Filter theo campus
    └─ Click "Chọn lớp" → Bước 4
    ↓
Bước 4: Xác nhận
    ├─ Chọn payment method
    └─ Click "Xác nhận thanh toán" → Bước 5
    ↓
Bước 5: Thanh toán
    ├─ Cash → Success message + PDF download
    └─ VNPay → Redirect hoặc QR code
    ↓
Bước 6: Schedule
    └─ Hiển thị lịch học + Actions
```

---

## FILES CẦN TẠO

### HTML:
- `enroll_class.html` - Trang chính cho flow đăng ký

### JavaScript:
- `enroll_class.js` - Logic chính cho flow
- `enrollment_api.js` - API calls (optional, có thể dùng api.js chung)

### CSS:
- `enrollment.css` - Custom styles cho enrollment flow (optional)

---

## INTEGRATION VỚI CODEBASE HIỆN TẠI

### 1. Sử dụng lại:
- `assets/js/api.js` - API helper functions
- `assets/js/config.js` - API configuration
- `assets/css/style.css` - Base styles
- Bootstrap 5 components

### 2. Navigation:
- Thêm menu item "Đăng ký lớp học" vào sidebar (chỉ hiện với student)
- Link đến `enroll_class.html`

### 3. Authentication:
- Check authentication trước khi vào flow
- Redirect về login nếu chưa đăng nhập
- Check role = 'student'

---

## TESTING CONSIDERATIONS

### Test Cases:
1. ✅ Flow hoàn chỉnh từ đầu đến cuối
2. ✅ Validation ở mỗi bước
3. ✅ Error handling (network error, validation error)
4. ✅ Back navigation
5. ✅ Refresh page (state restore)
6. ✅ Mobile responsive
7. ✅ Payment flow (cash và VNPay)
8. ✅ PDF download

### Edge Cases:
- Không có khóa học nào
- Không có lớp eligible
- Trùng lịch học
- Lớp đã đầy khi đang đăng ký
- Payment timeout

---

**Status:** ✅ Ý tưởng hoàn chỉnh - Sẵn sàng implement

