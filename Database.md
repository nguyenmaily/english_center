# DATABASE SCHEMA - ENGLISH CENTER

## 📊 TỔNG SỐ BẢNG: **32 BẢNG**

---

## 1. AUTHENTICATION APP (5 bảng)

### 1.1. `roles`
**Mô tả**: Bảng lưu các vai trò trong hệ thống

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `name` (Text, Unique) - Tên vai trò
- `description` (Text, Nullable) - Mô tả
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- → `user_accounts` (role_id)
- → `role_permissions` (role_id - OneToOne)

---

### 1.2. `permissions`
**Mô tả**: Bảng lưu các quyền trong hệ thống

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `name` (Text, Unique) - Tên quyền
- `description` (Text, Nullable) - Mô tả
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- → `role_permissions` (permission_id)

---

### 1.3. `role_permissions`
**Mô tả**: Bảng trung gian liên kết Role và Permission

**Thuộc tính**:
- `role_id` (UUID, PK, FK) - Foreign key đến `roles`
- `permission_id` (UUID, FK) - Foreign key đến `permissions`
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `roles` (OneToOne)
- ← `permissions` (ForeignKey)

---

### 1.4. `user_accounts`
**Mô tả**: Bảng lưu thông tin tài khoản người dùng

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `username` (Text, Unique) - Tên đăng nhập
- `password_hash` (Text) - Mật khẩu đã hash
- `email` (Email, Unique) - Email
- `status` (Char, max_length=20) - Trạng thái: 'active', 'inactive', 'suspended'
- `avatar_url` (Text, Nullable) - URL avatar
- `role_id` (UUID, FK, Nullable) - Foreign key đến `roles`
- `full_name` (Text, Nullable) - Họ tên đầy đủ
- `phone` (Text, Nullable) - Số điện thoại
- `sex` (Char, max_length=10) - Giới tính: 'male', 'female', 'other'
- `dob` (Date, Nullable) - Ngày sinh
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `roles` (role_id)
- → `students` (user_account_id - OneToOne)
- → `teachers` (user_account_id - OneToOne)
- → `managers` (user_account_id - OneToOne)
- → `admins` (user_account_id - OneToOne)
- → `password_reset_tokens` (user_id)

---

### 1.5. `password_reset_tokens`
**Mô tả**: Bảng lưu token reset mật khẩu

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `user_id` (UUID, FK) - Foreign key đến `user_accounts`
- `token` (Text, Unique) - Token reset
- `created_at` (DateTime) - Thời gian tạo
- `expires_at` (DateTime) - Thời gian hết hạn
- `is_used` (Boolean) - Đã sử dụng chưa

**Quan hệ**:
- ← `user_accounts` (user_id)

---

## 2. USERS APP (4 bảng)

### 2.1. `admins`
**Mô tả**: Bảng lưu thông tin quản trị viên toàn hệ thống (khác với managers chỉ quản lý 1 campus)

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `user_account_id` (UUID, FK, Unique) - Foreign key đến `user_accounts` (OneToOne)

**Quan hệ**:
- ← `user_accounts` (user_account_id - OneToOne)

**Indexes**:
- `user_account_id`

**Lưu ý**: Admin có quyền toàn hệ thống, không bị giới hạn bởi campus như Manager

---

### 2.2. `students`
**Mô tả**: Bảng lưu thông tin học viên

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `user_account_id` (UUID, FK, Unique) - Foreign key đến `user_accounts` (OneToOne)
- `commitment_status` (Char, max_length=20) - Trạng thái cam kết: 'not_committed', 'committed', 'canceled'
- `target_score` (Integer, Nullable) - Điểm mục tiêu (IELTS/TOEIC)

**Quan hệ**:
- ← `user_accounts` (user_account_id - OneToOne)
- → `enrollments` (student_id)
- → `submissions` (student_id)
- → `attendances` (student_id)
- → `exam_results` (student_id - UUID, không phải FK)
- → `student_progress` (student_id - UUID, không phải FK)
- → `leave_requests` (student_id - UUID, không phải FK)
- → `reserve_requests` (student_id - UUID, không phải FK)

**Indexes**:
- `commitment_status`
- `user_account_id`

---

### 2.3. `teachers`
**Mô tả**: Bảng lưu thông tin giảng viên

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `user_account_id` (UUID, FK, Unique) - Foreign key đến `user_accounts` (OneToOne)
- `level` (Text, Nullable) - Cấp độ: 'Junior', 'Senior', 'Expert'
- `specialization` (Text, Nullable) - Chuyên môn: 'IELTS Speaking', 'TOEIC', etc.
- `campus_id` (UUID, FK, Nullable) - Foreign key đến `campuses`

**Quan hệ**:
- ← `user_accounts` (user_account_id - OneToOne)
- ← `campuses` (campus_id)
- → `classes` (teacher_id)
- → `sessions` (teacher_id)

**Indexes**:
- `campus_id`
- `user_account_id`

---

### 2.4. `managers`
**Mô tả**: Bảng lưu thông tin quản lý

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `user_account_id` (UUID, FK, Unique) - Foreign key đến `user_accounts` (OneToOne)
- `campus_id` (UUID, FK, Nullable) - Foreign key đến `campuses`

**Quan hệ**:
- ← `user_accounts` (user_account_id - OneToOne)
- ← `campuses` (campus_id)
- → `classes` (manager_id)

**Indexes**:
- `campus_id`
- `user_account_id`

---

## 3. COURSES APP (2 bảng)

### 3.1. `courses`
**Mô tả**: Bảng lưu thông tin khóa học

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `name` (Text, Unique) - Tên khóa học
- `level` (Text, Nullable) - Cấp độ
- `description` (Text, Nullable) - Mô tả
- `total_sessions` (Integer, default=0) - Tổng số buổi học
- `min_entry_score` (Integer, Nullable) - Điểm đầu vào tối thiểu
- `min_exit_score` (Integer, Nullable) - Điểm đầu ra tối thiểu
- `fee` (Decimal, max_digits=12, decimal_places=2, default=0) - Học phí
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- → `skills` (course_id)
- → `classes` (course_id)

---

### 3.2. `skills`
**Mô tả**: Bảng lưu các kỹ năng trong khóa học

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `course_id` (UUID, FK) - Foreign key đến `courses`
- `name` (Text) - Tên kỹ năng
- `description` (Text, Nullable) - Mô tả
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `courses` (course_id)
- → `sessions` (skill_id)

---

## 4. CLASSES APP (1 bảng)

### 4.1. `classes`
**Mô tả**: Bảng lưu thông tin lớp học

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `course_id` (UUID, FK) - Foreign key đến `courses`
- `name` (Text) - Tên lớp
- `start_date` (Date, Nullable) - Ngày bắt đầu
- `end_date` (Date, Nullable) - Ngày kết thúc
- `current_student_count` (Integer, default=0) - Số học viên hiện tại
- `status` (Char, max_length=20) - Trạng thái: 'planned', 'ongoing', 'completed', 'cancelled'
- `weekday` (Array[SmallInteger]) - Các ngày trong tuần (1=Monday, 7=Sunday)
- `time_slot` (Text, Nullable) - Khung giờ học
- `teacher_id` (UUID, FK, Nullable) - Foreign key đến `teachers`
- `campus_id` (UUID, FK, Nullable) - Foreign key đến `campuses`
- `manager_id` (UUID, FK, Nullable) - Foreign key đến `managers`
- `limit_slot` (Integer, Nullable) - Số lượng tối đa
- `is_public` (Boolean, default=False) - Công khai
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `courses` (course_id)
- ← `teachers` (teacher_id)
- ← `campuses` (campus_id)
- ← `managers` (manager_id)
- → `enrollments` (class_id)
- → `sessions` (class_id)
- → `leave_requests` (class_id - UUID, không phải FK)
- → `reserve_requests` (class_id - UUID, không phải FK)

**Indexes**:
- `status`
- `start_date`
- `course_id`
- `teacher_id`
- `campus_id`
- `is_public`

---

## 5. CLASS SESSIONS APP (2 bảng)

### 5.1. `sessions`
**Mô tả**: Bảng lưu thông tin buổi học

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `class_id` (UUID, FK) - Foreign key đến `classes`
- `skill_id` (UUID, FK, Nullable) - Foreign key đến `skills`
- `room_id` (UUID, FK, Nullable) - Foreign key đến `rooms`
- `teacher_id` (UUID, FK, Nullable) - Foreign key đến `teachers`
- `study_date` (Date, Nullable) - Ngày học
- `start_time` (Time, Nullable) - Giờ bắt đầu
- `end_time` (Time, Nullable) - Giờ kết thúc
- `check_in` (Time, Nullable) - Giờ check-in
- `check_out` (Time, Nullable) - Giờ check-out
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `classes` (class_id)
- ← `skills` (skill_id)
- ← `rooms` (room_id)
- ← `teachers` (teacher_id)
- → `assignments` (session_id)
- → `attendances` (session_id)

---

### 5.2. `attendances`
**Mô tả**: Bảng lưu thông tin điểm danh học viên

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `student_id` (UUID, FK) - Foreign key đến `students`
- `session_id` (UUID, FK) - Foreign key đến `sessions`
- `status` (Char, max_length=20) - Trạng thái: 'present', 'absent', 'late', 'excused'

**Quan hệ**:
- ← `students` (student_id)
- ← `sessions` (session_id)

**Indexes**:
- `student_id`
- `session_id`
- `status`

**Constraints**:
- Unique together: (`student_id`, `session_id`) - Mỗi học viên chỉ có 1 điểm danh cho 1 buổi học

---

## 6. ENROLLMENT APP (2 bảng)

### 6.1. `enrollments`
**Mô tả**: Bảng lưu thông tin đăng ký học

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `student_id` (UUID, FK) - Foreign key đến `students`
- `class_id` (UUID, FK) - Foreign key đến `classes`
- `due_date` (Date, Nullable) - Hạn thanh toán
- `amount` (Decimal, max_digits=12, decimal_places=2, default=0) - Số tiền
- `invoice_status` (Char, max_length=32, default='pending') - Trạng thái: 'pending', 'paid', 'overdue', 'canceled'
- `notes` (Text, Nullable) - Ghi chú
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `students` (student_id)
- ← `classes` (class_id)
- → `payments` (enrollment_id)

**Constraints**:
- Unique together: (`student_id`, `class_id`)

---

### 6.2. `payments`
**Mô tả**: Bảng lưu lịch sử thanh toán

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `enrollment_id` (UUID, FK) - Foreign key đến `enrollments`
- `amount` (Decimal, max_digits=12, decimal_places=2) - Số tiền
- `payment_method` (Char, max_length=32) - Phương thức: 'cash', 'bank_transfer', 'vnpay', 'momo', 'other'
- `status` (Char, max_length=32) - Trạng thái: 'pending', 'success', 'failed', 'cancelled', 'refunded'
- `transaction_id` (Char, max_length=255, Nullable) - ID giao dịch từ payment gateway
- `gateway_response` (JSON, Nullable) - Response từ payment gateway
- `notes` (Text, Nullable) - Ghi chú
- `paid_at` (DateTime, Nullable) - Thời điểm thanh toán thành công
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `enrollments` (enrollment_id)

**Indexes**:
- `enrollment_id`
- `status`
- `payment_method`
- `transaction_id`
- `created_at`

---

## 7. ASSIGNMENTS APP (4 bảng)

### 7.1. `assignments`
**Mô tả**: Bảng lưu thông tin bài tập

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `session_id` (UUID, FK) - Foreign key đến `sessions`
- `title` (Text) - Tiêu đề
- `description` (Text, Nullable) - Mô tả
- `due_date` (Date, Nullable) - Hạn nộp
- `status` (Char, max_length=20) - Trạng thái: 'draft', 'published', 'closed'
- `url_file` (Char, max_length=500, Nullable) - URL file
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `sessions` (session_id)
- → `answer_keys` (assignment_id)
- → `submissions` (assignment_id)

---

### 7.2. `answer_keys`
**Mô tả**: Bảng lưu đáp án đúng của bài tập

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `assignment_id` (UUID, FK) - Foreign key đến `assignments`
- `question_number` (Integer) - Số câu hỏi
- `correct_option` (Char, max_length=10) - Đáp án đúng
- `description` (Text, Nullable) - Mô tả
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `assignments` (assignment_id)

---

### 7.3. `submissions`
**Mô tả**: Bảng lưu bài nộp của học viên

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `assignment_id` (UUID, FK) - Foreign key đến `assignments`
- `student_id` (UUID, FK) - Foreign key đến `students`
- `submitted_at` (DateTime) - Thời gian nộp
- `status` (Char, max_length=20) - Trạng thái: 'submitted', 'graded', 'resubmit_required'
- `content` (Text, Nullable) - Nội dung
- `result` (Decimal, max_digits=5, decimal_places=2, Nullable) - Điểm số
- `correct_count` (Integer, Nullable) - Số câu đúng
- `total_question` (Integer, Nullable) - Tổng số câu
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `assignments` (assignment_id)
- ← `students` (student_id)
- → `student_answers` (submission_id)

**Constraints**:
- Unique together: (`assignment_id`, `student_id`)

---

### 7.4. `student_answers`
**Mô tả**: Bảng lưu câu trả lời của học viên

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `submission_id` (UUID, FK) - Foreign key đến `submissions`
- `question_number` (Integer) - Số câu hỏi
- `selected_option` (Integer, Nullable) - Lựa chọn
- `is_correct` (Integer, Nullable) - Đúng/Sai (0/1)
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `submissions` (submission_id)

---

## 8. CAMPUS APP (3 bảng)

### 8.1. `campuses`
**Mô tả**: Bảng lưu thông tin cơ sở

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `name` (Text) - Tên cơ sở
- `address` (Text, Nullable) - Địa chỉ
- `phone` (Text, Nullable) - Số điện thoại
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- → `rooms` (campus_id)
- → `teachers` (campus_id)
- → `managers` (campus_id)
- → `classes` (campus_id)

---

### 8.2. `rooms`
**Mô tả**: Bảng lưu thông tin phòng học

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `campus_id` (UUID, FK) - Foreign key đến `campuses`
- `name` (Text) - Tên phòng
- `is_under_repair` (Boolean, default=False) - Đang sửa chữa
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `campuses` (campus_id)
- → `equipment` (room_id)
- → `sessions` (room_id)

---

### 8.3. `equipment`
**Mô tả**: Bảng lưu thông tin thiết bị

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `room_id` (UUID, FK) - Foreign key đến `rooms`
- `name` (Text) - Tên thiết bị
- `status` (Char, max_length=20) - Trạng thái: 'working', 'broken', 'maintenance'
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `rooms` (room_id)

---

## 9. TESTS APP (9 bảng)

### 9.1. `question_groups`
**Mô tả**: Bảng lưu nhóm câu hỏi

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `part` (Text) - Phần (Part 1, 2, 3, etc.)
- `skill` (Text) - Kỹ năng (Listening, Reading, etc.)
- `context` (Text, Nullable) - Ngữ cảnh
- `audio_file` (Text, Nullable) - File audio
- `image_file` (Text, Nullable) - File hình ảnh
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- → `questions` (group_id - UUID, không phải FK)

---

### 9.2. `questions`
**Mô tả**: Bảng lưu câu hỏi

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `group_id` (UUID, Nullable) - ID nhóm (UUID, không phải FK) → `question_groups`
- `text` (Text) - Nội dung câu hỏi
- `option_a` (Text, Nullable) - Lựa chọn A
- `option_b` (Text, Nullable) - Lựa chọn B
- `option_c` (Text, Nullable) - Lựa chọn C
- `option_d` (Text, Nullable) - Lựa chọn D
- `correct_answer` (Text) - Đáp án đúng
- `difficulty` (Char, max_length=20, default='medium') - Độ khó: 'easy', 'medium', 'hard'
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `question_groups` (group_id - UUID, không phải FK)
- → `exam_instance_questions` (question_id - UUID, không phải FK)
- → `exam_answers` (question_id - UUID, không phải FK)

---

### 9.3. `exam_blueprints`
**Mô tả**: Bảng lưu mẫu đề thi

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `exam_type` (Char, max_length=50) - Loại đề: 'placement', 'midterm', 'final'
- `title` (Text) - Tiêu đề
- `duration` (Integer) - Thời lượng (phút)
- `total_questions` (Integer) - Tổng số câu hỏi
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- → `exam_rules` (blueprint_id - UUID, không phải FK)
- → `exam_instances` (blueprint_id - UUID, không phải FK)

---

### 9.4. `exam_rules`
**Mô tả**: Bảng lưu quy tắc tạo đề thi

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `blueprint_id` (UUID) - ID mẫu đề (UUID, không phải FK) → `exam_blueprints`
- `part` (Text) - Phần
- `skill` (Text) - Kỹ năng
- `difficulty` (Char, max_length=20) - Độ khó: 'easy', 'medium', 'hard'
- `num_questions` (Integer) - Số câu hỏi
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `exam_blueprints` (blueprint_id - UUID, không phải FK)

---

### 9.5. `exam_instances`
**Mô tả**: Bảng lưu đề thi cụ thể

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `blueprint_id` (UUID, Nullable) - ID mẫu đề (UUID, không phải FK) → `exam_blueprints`
- `title` (Text) - Tiêu đề
- `status` (Char, max_length=20, default='draft') - Trạng thái: 'draft', 'published', 'archived'
- `generated_at` (DateTime) - Thời gian tạo
- `created_by` (UUID, Nullable) - Người tạo (UUID, không phải FK)

**Quan hệ**:
- ← `exam_blueprints` (blueprint_id - UUID, không phải FK)
- → `exam_instance_questions` (exam_instance_id - UUID, không phải FK)
- → `exam_results` (exam_instance_id - UUID, không phải FK)

---

### 9.6. `exam_instance_questions`
**Mô tả**: Bảng trung gian liên kết đề thi và câu hỏi

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `exam_instance_id` (UUID) - ID đề thi (UUID, không phải FK) → `exam_instances`
- `question_id` (UUID) - ID câu hỏi (UUID, không phải FK) → `questions`
- `order_number` (Integer, Nullable) - Thứ tự

**Quan hệ**:
- ← `exam_instances` (exam_instance_id - UUID, không phải FK)
- ← `questions` (question_id - UUID, không phải FK)

**Constraints**:
- Unique together: (`exam_instance_id`, `question_id`)

---

### 9.7. `exam_results`
**Mô tả**: Bảng lưu kết quả thi

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `exam_instance_id` (UUID) - ID đề thi (UUID, không phải FK) → `exam_instances`
- `student_id` (UUID) - ID học viên (UUID, không phải FK) → `students`
- `score` (Decimal, max_digits=5, decimal_places=2, Nullable) - Điểm số
- `submitted_at` (DateTime) - Thời gian nộp
- `status` (Char, max_length=20, default='in_progress') - Trạng thái: 'in_progress', 'completed', 'graded'
- `teacher_comment` (Text, Nullable) - Nhận xét của giáo viên
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `exam_instances` (exam_instance_id - UUID, không phải FK)
- ← `students` (student_id - UUID, không phải FK)
- → `exam_answers` (result_id - UUID, không phải FK)

**Constraints**:
- Unique together: (`exam_instance_id`, `student_id`)

---

### 9.8. `exam_answers`
**Mô tả**: Bảng lưu câu trả lời của học viên trong bài thi

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `result_id` (UUID) - ID kết quả (UUID, không phải FK) → `exam_results`
- `question_id` (UUID) - ID câu hỏi (UUID, không phải FK) → `questions`
- `selected_answer` (Text, Nullable) - Câu trả lời đã chọn
- `is_correct` (Boolean, Nullable) - Đúng/Sai
- `created_at` (DateTime) - Thời gian tạo

**Quan hệ**:
- ← `exam_results` (result_id - UUID, không phải FK)
- ← `questions` (question_id - UUID, không phải FK)

---

### 9.9. `student_progress`
**Mô tả**: Bảng lưu tiến độ học tập của học viên

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `student_id` (UUID, Unique) - ID học viên (UUID, không phải FK) → `students`
- `placement_score` (Decimal, max_digits=5, decimal_places=2, Nullable) - Điểm placement test
- `midterm_score` (Decimal, max_digits=5, decimal_places=2, Nullable) - Điểm giữa kỳ
- `final_score` (Decimal, max_digits=5, decimal_places=2, Nullable) - Điểm cuối kỳ
- `final_status` (Char, max_length=20, Nullable) - Trạng thái: 'pass', 'fail', 'retake_required', 'certified'
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `students` (student_id - UUID, không phải FK)

**Constraints**:
- Unique: `student_id`

---

## 10. REQUESTS APP (2 bảng)

### 10.1. `leave_requests`
**Mô tả**: Bảng lưu yêu cầu nghỉ học

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `student_id` (UUID) - ID học viên (UUID, không phải FK) → `students`
- `class_id` (UUID) - ID lớp (UUID, không phải FK) → `classes`
- `session_date` (Date, Nullable) - Ngày buổi học
- `session_time` (Time, Nullable) - Giờ buổi học
- `status` (Char, max_length=32, default='pending') - Trạng thái
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `students` (student_id - UUID, không phải FK)
- ← `classes` (class_id - UUID, không phải FK)

---

### 10.2. `reserve_requests`
**Mô tả**: Bảng lưu yêu cầu bảo lưu

**Thuộc tính**:
- `id` (UUID, PK) - Primary key
- `student_id` (UUID) - ID học viên (UUID, không phải FK) → `students`
- `class_id` (UUID) - ID lớp (UUID, không phải FK) → `classes`
- `start_date` (Date, Nullable) - Ngày bắt đầu
- `end_date` (Date, Nullable) - Ngày kết thúc
- `status` (Char, max_length=32, default='pending') - Trạng thái
- `created_at` (DateTime) - Thời gian tạo
- `updated_at` (DateTime) - Thời gian cập nhật

**Quan hệ**:
- ← `students` (student_id - UUID, không phải FK)
- ← `classes` (class_id - UUID, không phải FK)

---

## 📊 SƠ ĐỒ QUAN HỆ TỔNG QUAN

### Quan hệ có Foreign Key (Đúng):
```
user_accounts
  ├── role_id → roles
  │
  ├── students (OneToOne)
  │   ├── enrollments → classes
  │   │   └── payments
  │   └── submissions → assignments
  │       └── student_answers
  │
  ├── teachers (OneToOne)
  │   ├── classes
  │   └── sessions
  │
  └── managers (OneToOne)
      └── classes

campuses
  ├── rooms
  │   └── equipment
  │       └── sessions
  ├── teachers
  ├── managers
  └── classes

courses
  ├── skills
  │   └── sessions
  └── classes
      ├── enrollments
      └── sessions
          └── assignments
              ├── answer_keys
              └── submissions
                  └── student_answers
```

### Quan hệ thiếu Foreign Key (Chỉ có UUID):
```
question_groups
  └── questions (group_id - UUID)

exam_blueprints
  ├── exam_rules (blueprint_id - UUID)
  └── exam_instances (blueprint_id - UUID)
      └── exam_instance_questions (exam_instance_id - UUID)
          ├── questions (question_id - UUID)
          └── exam_results (exam_instance_id - UUID)
              ├── students (student_id - UUID)
              └── exam_answers (result_id - UUID)
                  └── questions (question_id - UUID)

students
  ├── exam_results (student_id - UUID)
  ├── student_progress (student_id - UUID)
  ├── leave_requests (student_id - UUID)
  └── reserve_requests (student_id - UUID)

classes
  ├── leave_requests (class_id - UUID)
  └── reserve_requests (class_id - UUID)
```

---

## ⚠️ VẤN ĐỀ PHÁT HIỆN

### 1. Tests App - Thiếu Foreign Keys (9 quan hệ)
- `Question.group_id` → Nên là FK đến `QuestionGroup`
- `ExamRule.blueprint_id` → Nên là FK đến `ExamBlueprint`
- `ExamInstance.blueprint_id` → Nên là FK đến `ExamBlueprint`
- `ExamInstanceQuestion.exam_instance_id` → Nên là FK đến `ExamInstance`
- `ExamInstanceQuestion.question_id` → Nên là FK đến `Question`
- `ExamResult.exam_instance_id` → Nên là FK đến `ExamInstance`
- `ExamResult.student_id` → Nên là FK đến `Student`
- `ExamAnswer.result_id` → Nên là FK đến `ExamResult`
- `ExamAnswer.question_id` → Nên là FK đến `Question`
- `StudentProgress.student_id` → Nên là FK đến `Student`

### 2. Requests App - Thiếu Foreign Keys (4 quan hệ)
- `LeaveRequest.student_id` → Nên là FK đến `Student`
- `LeaveRequest.class_id` → Nên là FK đến `Class`
- `ReserveRequest.student_id` → Nên là FK đến `Student`
- `ReserveRequest.class_id` → Nên là FK đến `Class`

### 3. Thiếu quan hệ Placement Test → Course
- `ExamResult` không có quan hệ với `Course`
- `Enrollment` không lưu `exam_result_id` được dùng để đăng ký

### 4. Thiếu bảng `student_certificates`
- Không có bảng lưu chứng chỉ của học viên

---

## 11. BẢNG THỪA/THIẾU TRONG DATABASE

### 11.1. Bảng có trong Database nhưng THIẾU trong Models:

#### `admins`
**Mô tả**: Bảng lưu thông tin quản trị viên toàn hệ thống (khác với managers chỉ quản lý 1 campus)

**Thuộc tính** (theo database):
- `id` (UUID, PK) - Primary key
- `user_account_id` (UUID, FK) - Foreign key đến `user_accounts` (OneToOne)

**Quan hệ**:
- ← `user_accounts` (user_account_id - OneToOne)

**Đề xuất**: Tạo model `Admin` trong app `users`, tương tự `Manager` nhưng không có `campus_id`

---

#### `attendances`
**Mô tả**: Bảng lưu thông tin điểm danh học viên

**Thuộc tính** (theo database):
- `id` (UUID, PK) - Primary key
- `student_id` (UUID) - ID học viên (UUID, không phải FK) → `students`
- `session_id` (UUID) - ID buổi học (UUID, không phải FK) → `sessions`
- `status` (Enum) - Trạng thái: 'late', 'present', 'absent', 'excused'

**Quan hệ**:
- ← `students` (student_id - UUID, không phải FK)
- ← `sessions` (session_id - UUID, không phải FK)

**Đề xuất**: 
- Tạo model `Attendance` trong app `class_sessions`
- Thêm Foreign Key cho `student_id` và `session_id`
- Thêm index cho `session_id` và `student_id` để query nhanh

---

### 11.2. Bảng có trong Database nhưng CÓ THỂ XÓA:

#### `enrollment_enrollment`
**Mô tả**: Bảng cũ/duplicate của `enrollments`

**Thuộc tính**:
- `id` (UUID, PK)
- `student_name` (Text) - Tên học viên (denormalized)
- `student_email` (Text) - Email học viên (denormalized)
- `class_code` (Text) - Mã lớp (denormalized)
- `enrolled_at` (DateTime) - Thời gian đăng ký
- `status` (Text) - Trạng thái

**Phân tích**:
- Không có data
- Không rõ có đang được sử dụng không
- Cấu trúc denormalized (lưu thông tin trực tiếp thay vì dùng FK)
- `enrollments` là bảng mới với cấu trúc chuẩn hơn (dùng FK)

**Đề xuất**: 
- **XÓA BẢNG** vì:
  1. Không có data
  2. Cấu trúc không chuẩn (denormalized)
  3. Đã có `enrollments` thay thế với cấu trúc tốt hơn

---

### 11.3. Bảng Django System (Không cần quan tâm):

Các bảng mặc định của Django:
- `auth_group`
- `auth_group_permissions`
- `auth_permission`
- `auth_user`
- `auth_user_groups`
- `auth_user_user_permissions`
- `django_admin_log`
- `django_content_type`
- `django_migrations`
- `django_session`

**Lưu ý**: Các bảng này là của Django framework, không cần tạo models vì Django tự quản lý.

---

## 📝 TỔNG KẾT

### Tổng số bảng trong Database: **43 bảng**
- **Bảng Django system**: 10 bảng (không cần quan tâm)
- **Bảng có trong Models**: 30 bảng
- **Bảng thiếu trong Models**: 2 bảng (`admins`, `attendances`)
- **Bảng thừa nên xóa**: 1 bảng (`enrollment_enrollment`)

### Tổng số bảng thực tế cần quản lý: **32 bảng** (sau khi xóa `enrollment_enrollment`)

### Vấn đề cần xử lý:
1. **Tạo model cho `admins`** - Quản trị viên toàn hệ thống
2. **Tạo model cho `attendances`** - Điểm danh học viên
3. **Xóa bảng `enrollment_enrollment`** - Bảng cũ/duplicate
4. **Thêm Foreign Keys** - 14 quan hệ thiếu (Tests + Requests apps)
5. **Tạo bảng `student_certificates`** - Lưu chứng chỉ học viên

### Bảng có Foreign Key đúng: 23 bảng
### Bảng thiếu Foreign Key: 9 bảng (Tests + Requests apps)
### Quan hệ thiếu: 14 quan hệ cần thêm Foreign Key

