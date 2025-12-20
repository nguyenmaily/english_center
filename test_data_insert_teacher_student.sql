-- ============================================================
-- SCRIPT INSERT DỮ LIỆU TEST CHO ROLE TEACHER VÀ STUDENT
-- ============================================================
-- Mục đích: Tạo dữ liệu mẫu để test các chức năng của Teacher và Student
-- Chạy script này sau khi đã có các bảng trong database
-- ============================================================

-- Xóa dữ liệu cũ (nếu cần - CẨN THẬN!)
-- BEGIN;
-- DELETE FROM attendances;
-- DELETE FROM submissions;
-- DELETE FROM assignments;
-- DELETE FROM leave_requests;
-- DELETE FROM reserve_requests;
-- DELETE FROM enrollments;
-- DELETE FROM sessions;
-- DELETE FROM classes;
-- DELETE FROM students;
-- DELETE FROM teachers;
-- DELETE FROM user_accounts WHERE role_id IN (SELECT id FROM roles WHERE name IN ('teacher', 'student'));
-- COMMIT;

-- ============================================================
-- 1. ROLES (nếu chưa có)
-- ============================================================
-- Lưu ý: Nếu roles đã tồn tại, script sẽ bỏ qua
INSERT INTO roles (id, name, description, created_at, updated_at)
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'student', 'Học viên', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000002', 'teacher', 'Giáo viên', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000003', 'manager', 'Quản lý', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000004', 'admin', 'Quản trị viên', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;  -- Sửa từ (id) thành (name) vì unique constraint là trên name

-- ============================================================
-- 2. CAMPUSES (nếu chưa có)
-- ============================================================
INSERT INTO campuses (id, name, address, phone, created_at, updated_at)
VALUES 
    ('10000000-0000-0000-0000-000000000001', 'Cơ sở Quận 1', '123 Nguyễn Huệ, Quận 1, TP.HCM', '0281234567', NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000002', 'Cơ sở Quận 3', '456 Lê Văn Sỹ, Quận 3, TP.HCM', '0282345678', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- 3. USER ACCOUNTS - TEACHERS
-- ============================================================
-- Password hash cho "teacher123" (bcrypt)
INSERT INTO user_accounts (id, username, password_hash, email, status, role_id, full_name, phone, sex, dob, created_at, updated_at)
VALUES 
    -- Teacher 1
    ('20000000-0000-0000-0000-000000000001', 'teacher1', 'pbkdf2_sha256$600000$dummy$dummy', 'teacher1@englishcenter.com', 'active', 
     (SELECT id FROM roles WHERE name = 'teacher'), 'Nguyễn Văn Giáo', '0901234567', 'male', '1985-05-15', NOW(), NOW()),
    
    -- Teacher 2
    ('20000000-0000-0000-0000-000000000002', 'teacher2', 'pbkdf2_sha256$600000$dummy$dummy', 'teacher2@englishcenter.com', 'active',
     (SELECT id FROM roles WHERE name = 'teacher'), 'Trần Thị Dạy', '0902345678', 'female', '1990-08-20', NOW(), NOW()),
    
    -- Teacher 3 (chưa có lớp)
    ('20000000-0000-0000-0000-000000000003', 'teacher3', 'pbkdf2_sha256$600000$dummy$dummy', 'teacher3@englishcenter.com', 'active',
     (SELECT id FROM roles WHERE name = 'teacher'), 'Lê Văn Mới', '0903456789', 'male', '1992-03-10', NOW(), NOW())
ON CONFLICT (username) DO UPDATE SET
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    role_id = EXCLUDED.role_id,
    status = EXCLUDED.status;

-- ============================================================
-- 4. TEACHERS
-- ============================================================
INSERT INTO teachers (id, user_account_id, level, specialization, campus_id)
VALUES 
    ('30000000-0000-0000-0000-000000000001', '20000000-0000-0000-0000-000000000001', 'senior', 'IELTS Speaking', '10000000-0000-0000-0000-000000000001'),
    ('30000000-0000-0000-0000-000000000002', '20000000-0000-0000-0000-000000000002', 'expert', 'TOEIC', '10000000-0000-0000-0000-000000000001'),
    ('30000000-0000-0000-0000-000000000003', '20000000-0000-0000-0000-000000000003', 'junior', 'IELTS Writing', '10000000-0000-0000-0000-000000000002')
ON CONFLICT (id) DO UPDATE SET
    level = EXCLUDED.level,
    specialization = EXCLUDED.specialization;

-- ============================================================
-- 5. USER ACCOUNTS - STUDENTS
-- ============================================================
INSERT INTO user_accounts (id, username, password_hash, email, status, role_id, full_name, phone, sex, dob, created_at, updated_at)
VALUES 
    -- Student 1
    ('40000000-0000-0000-0000-000000000001', 'student1', 'pbkdf2_sha256$600000$dummy$dummy', 'student1@englishcenter.com', 'active',
     (SELECT id FROM roles WHERE name = 'student'), 'Phạm Văn Học', '0911234567', 'male', '2000-01-15', NOW(), NOW()),
    
    -- Student 2
    ('40000000-0000-0000-0000-000000000002', 'student2', 'pbkdf2_sha256$600000$dummy$dummy', 'student2@englishcenter.com', 'active',
     (SELECT id FROM roles WHERE name = 'student'), 'Nguyễn Thị Sinh', '0912345678', 'female', '2001-05-20', NOW(), NOW()),
    
    -- Student 3
    ('40000000-0000-0000-0000-000000000003', 'student3', 'pbkdf2_sha256$600000$dummy$dummy', 'student3@englishcenter.com', 'active',
     (SELECT id FROM roles WHERE name = 'student'), 'Lê Văn Viên', '0913456789', 'male', '1999-08-10', NOW(), NOW()),
    
    -- Student 4
    ('40000000-0000-0000-0000-000000000004', 'student4', 'pbkdf2_sha256$600000$dummy$dummy', 'student4@englishcenter.com', 'active',
     (SELECT id FROM roles WHERE name = 'student'), 'Trần Thị Học', '0914567890', 'female', '2002-03-25', NOW(), NOW())
ON CONFLICT (username) DO UPDATE SET
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    role_id = EXCLUDED.role_id,
    status = EXCLUDED.status;

-- ============================================================
-- 6. STUDENTS
-- ============================================================
INSERT INTO students (id, user_account_id, commitment_status, target_score)
VALUES 
    ('50000000-0000-0000-0000-000000000001', '40000000-0000-0000-0000-000000000001', 'committed', 7),
    ('50000000-0000-0000-0000-000000000002', '40000000-0000-0000-0000-000000000002', 'committed', 750),
    ('50000000-0000-0000-0000-000000000003', '40000000-0000-0000-0000-000000000003', 'committed', 6.5),
    ('50000000-0000-0000-0000-000000000004', '40000000-0000-0000-0000-000000000004', 'not_committed', 8)
ON CONFLICT (id) DO UPDATE SET
    commitment_status = EXCLUDED.commitment_status,
    target_score = EXCLUDED.target_score;

-- ============================================================
-- 7. COURSES
-- ============================================================
INSERT INTO courses (id, name, level, description, total_sessions, min_entry_score, min_exit_score, fee, created_at, updated_at)
VALUES 
    ('60000000-0000-0000-0000-000000000001', 'IELTS Foundation', 'foundation', 'Khóa học IELTS cơ bản', 36, 4.0, 5.5, 5000000, NOW(), NOW()),
    ('60000000-0000-0000-0000-000000000002', 'IELTS Intermediate', 'intermediate', 'Khóa học IELTS trung cấp', 36, 5.5, 6.5, 6000000, NOW(), NOW()),
    ('60000000-0000-0000-0000-000000000003', 'TOEIC Intermediate', 'intermediate', 'Khóa học TOEIC trung cấp', 30, 400, 600, 4500000, NOW(), NOW()),
    ('60000000-0000-0000-0000-000000000004', 'TOEIC Advanced', 'advanced', 'Khóa học TOEIC nâng cao', 30, 600, 800, 5500000, NOW(), NOW())
ON CONFLICT (name) DO UPDATE SET
    level = EXCLUDED.level,
    fee = EXCLUDED.fee,
    description = EXCLUDED.description;

-- ============================================================
-- 8. CLASSES
-- ============================================================
-- Lớp có giáo viên (để test chức năng của teacher)
INSERT INTO classes (id, name, start_date, end_date, current_student_count, status, course_id, weekday, time_slot, teacher_id, campus_id, limit_slot, is_public, created_at, updated_at)
VALUES 
    -- Lớp 1: IELTS Foundation - Đang diễn ra - Có giáo viên - Có học viên
    ('70000000-0000-0000-0000-000000000001', 'IELTS Foundation - Lớp 1', '2024-01-15', '2024-04-15', 3, 'ongoing',
     '60000000-0000-0000-0000-000000000001', ARRAY[2, 4, 6], '18:30-20:30',
     '30000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 20, true, NOW(), NOW()),
    
    -- Lớp 2: TOEIC Intermediate - Đang diễn ra - Có giáo viên - Có học viên
    ('70000000-0000-0000-0000-000000000002', 'TOEIC Intermediate - Lớp 1', '2024-01-10', '2024-03-10', 2, 'ongoing',
     '60000000-0000-0000-0000-000000000003', ARRAY[3, 5], '19:00-21:00',
     '30000000-0000-0000-0000-000000000002', '10000000-0000-0000-0000-000000000001', 15, true, NOW(), NOW()),
    
    -- Lớp 3: IELTS Intermediate - Sắp diễn ra - Có giáo viên - Chưa có học viên
    ('70000000-0000-0000-0000-000000000003', 'IELTS Intermediate - Lớp 1', '2024-02-01', '2024-05-01', 0, 'planned',
     '60000000-0000-0000-0000-000000000002', ARRAY[2, 4], '18:00-20:00',
     '30000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 20, true, NOW(), NOW()),
    
    -- Lớp 4: IELTS Foundation - Sắp diễn ra - CHƯA CÓ GIÁO VIÊN (để test đăng ký)
    ('70000000-0000-0000-0000-000000000004', 'IELTS Foundation - Lớp 2', '2024-02-15', '2024-05-15', 0, 'planned',
     '60000000-0000-0000-0000-000000000001', ARRAY[3, 5], '18:30-20:30',
     NULL, '10000000-0000-0000-0000-000000000001', 20, true, NOW(), NOW()),
    
    -- Lớp 5: TOEIC Advanced - Sắp diễn ra - CHƯA CÓ GIÁO VIÊN (để test đăng ký)
    ('70000000-0000-0000-0000-000000000005', 'TOEIC Advanced - Lớp 1', '2024-02-20', '2024-05-20', 0, 'planned',
     '60000000-0000-0000-0000-000000000004', ARRAY[2, 4, 6], '19:00-21:00',
     NULL, '10000000-0000-0000-0000-000000000002', 15, true, NOW(), NOW()),
    
    -- Lớp 6: IELTS Foundation - Sắp diễn ra - Có giáo viên - Chưa có học viên (để test hủy đăng ký)
    ('70000000-0000-0000-0000-000000000006', 'IELTS Foundation - Lớp 3', '2024-03-01', '2024-06-01', 0, 'planned',
     '60000000-0000-0000-0000-000000000001', ARRAY[3, 5], '18:00-20:00',
     '30000000-0000-0000-0000-000000000003', '10000000-0000-0000-0000-000000000002', 20, true, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    status = EXCLUDED.status,
    teacher_id = EXCLUDED.teacher_id,
    current_student_count = EXCLUDED.current_student_count;

-- ============================================================
-- 9. SESSIONS (Buổi học)
-- ============================================================
-- Tạo sessions cho lớp 1 (đang diễn ra)
-- Lưu ý: Bảng sessions KHÔNG có created_at và updated_at
INSERT INTO sessions (id, class_id, study_date, start_time, end_time, teacher_id)
SELECT 
    gen_random_uuid(),
    '70000000-0000-0000-0000-000000000001',
    date_val,
    '18:30:00'::time,
    '20:30:00'::time,
    '30000000-0000-0000-0000-000000000001'
FROM generate_series(
    '2024-01-15'::date,
    '2024-04-15'::date,
    '1 day'::interval
) AS date_val
WHERE EXTRACT(DOW FROM date_val) IN (2, 4, 6)  -- Thứ 3, 5, 7
ON CONFLICT DO NOTHING;

-- Tạo sessions cho lớp 2 (đang diễn ra)
INSERT INTO sessions (id, class_id, study_date, start_time, end_time, teacher_id)
SELECT 
    gen_random_uuid(),
    '70000000-0000-0000-0000-000000000002',
    date_val,
    '19:00:00'::time,
    '21:00:00'::time,
    '30000000-0000-0000-0000-000000000002'
FROM generate_series(
    '2024-01-10'::date,
    '2024-03-10'::date,
    '1 day'::interval
) AS date_val
WHERE EXTRACT(DOW FROM date_val) IN (3, 5)  -- Thứ 4, 6
ON CONFLICT DO NOTHING;

-- Tạo 1 session hôm nay cho lớp 1 (để test điểm danh)
INSERT INTO sessions (id, class_id, study_date, start_time, end_time, teacher_id)
VALUES 
    ('80000000-0000-0000-0000-000000000001', '70000000-0000-0000-0000-000000000001', CURRENT_DATE, '18:30:00', '20:30:00',
     '30000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO UPDATE SET
    study_date = CURRENT_DATE;

-- Tạo 1 session tuần tới cho lớp 1 (sắp diễn ra)
INSERT INTO sessions (id, class_id, study_date, start_time, end_time, teacher_id)
VALUES 
    ('80000000-0000-0000-0000-000000000002', '70000000-0000-0000-0000-000000000001', CURRENT_DATE + INTERVAL '7 days', '18:30:00', '20:30:00',
     '30000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO UPDATE SET
    study_date = CURRENT_DATE + INTERVAL '7 days';

-- Tạo 1 session tuần trước cho lớp 1 (đã diễn ra)
INSERT INTO sessions (id, class_id, study_date, start_time, end_time, teacher_id, check_in, check_out)
VALUES 
    ('80000000-0000-0000-0000-000000000003', '70000000-0000-0000-0000-000000000001', CURRENT_DATE - INTERVAL '7 days', '18:30:00', '20:30:00',
     '30000000-0000-0000-0000-000000000001', '18:25:00', '20:35:00')
ON CONFLICT (id) DO UPDATE SET
    study_date = CURRENT_DATE - INTERVAL '7 days';

-- ============================================================
-- 10. ENROLLMENTS (Học viên đăng ký lớp)
-- ============================================================
INSERT INTO enrollments (id, student_id, class_id, invoice_status, amount, due_date, created_at, updated_at)
VALUES 
    -- Student 1 đăng ký lớp 1
    ('90000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', '70000000-0000-0000-0000-000000000001', 'paid', 5000000, CURRENT_DATE + INTERVAL '2 days', NOW(), NOW()),
    
    -- Student 2 đăng ký lớp 1
    ('90000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000002', '70000000-0000-0000-0000-000000000001', 'paid', 5000000, CURRENT_DATE + INTERVAL '2 days', NOW(), NOW()),
    
    -- Student 3 đăng ký lớp 1
    ('90000000-0000-0000-0000-000000000003', '50000000-0000-0000-0000-000000000003', '70000000-0000-0000-0000-000000000001', 'paid', 5000000, CURRENT_DATE + INTERVAL '2 days', NOW(), NOW()),
    
    -- Student 1 đăng ký lớp 2
    ('90000000-0000-0000-0000-000000000004', '50000000-0000-0000-0000-000000000001', '70000000-0000-0000-0000-000000000002', 'paid', 4500000, CURRENT_DATE + INTERVAL '2 days', NOW(), NOW()),
    
    -- Student 2 đăng ký lớp 2
    ('90000000-0000-0000-0000-000000000005', '50000000-0000-0000-0000-000000000002', '70000000-0000-0000-0000-000000000002', 'paid', 4500000, CURRENT_DATE + INTERVAL '2 days', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    invoice_status = EXCLUDED.invoice_status;

-- ============================================================
-- 11. ASSIGNMENTS (Bài tập)
-- ============================================================
INSERT INTO assignments (id, title, description, due_date, status, url_file, session_id, created_at, updated_at)
VALUES 
    -- Bài tập cho session hôm nay (lớp 1)
    ('a0000000-0000-0000-0000-000000000001', 'Bài tập Unit 1', 'Làm bài tập về thì hiện tại đơn', CURRENT_DATE + INTERVAL '5 days', 'published', NULL,
     '80000000-0000-0000-0000-000000000001', NOW(), NOW()),
    
    -- Bài tập cho session tuần trước (lớp 1)
    ('a0000000-0000-0000-0000-000000000002', 'Bài tập Unit 2', 'Làm bài tập về thì quá khứ đơn', CURRENT_DATE - INTERVAL '2 days', 'closed', NULL,
     '80000000-0000-0000-0000-000000000003', NOW(), NOW()),
    
    -- Bài tập cho lớp 2
    ('a0000000-0000-0000-0000-000000000003', 'Bài tập TOEIC Part 1', 'Làm bài tập TOEIC Listening Part 1', CURRENT_DATE + INTERVAL '7 days', 'published', NULL,
     (SELECT id FROM sessions WHERE class_id = '70000000-0000-0000-0000-000000000002' LIMIT 1), NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    status = EXCLUDED.status;

-- ============================================================
-- 12. SUBMISSIONS (Bài nộp)
-- ============================================================
-- Lưu ý: Status hợp lệ: submitted, graded, resubmitted, late, missing
INSERT INTO submissions (id, assignment_id, student_id, submitted_at, status, content, result, correct_count, total_question, created_at, updated_at)
VALUES 
    -- Student 1 nộp bài tập Unit 1 (chưa chấm)
    ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', 
     CURRENT_TIMESTAMP - INTERVAL '1 day', 'submitted', 'Nội dung bài làm của student 1', NULL, NULL, NULL, NOW(), NOW()),
    
    -- Student 2 nộp bài tập Unit 1 (chưa chấm)
    ('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000002',
     CURRENT_TIMESTAMP - INTERVAL '2 hours', 'submitted', 'Nội dung bài làm của student 2', NULL, NULL, NULL, NOW(), NOW()),
    
    -- Student 3 nộp bài tập Unit 2 (đã chấm - đạt)
    ('b0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000003',
     CURRENT_TIMESTAMP - INTERVAL '5 days', 'graded', 'Nội dung bài làm của student 3', 85.5, 17, 20, NOW(), NOW()),
    
    -- Student 1 nộp bài tập Unit 2 (yêu cầu nộp lại - status vẫn là submitted, content chứa yêu cầu)
    ('b0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000001',
     CURRENT_TIMESTAMP - INTERVAL '4 days', 'submitted', 'Bài làm chưa đạt yêu cầu. Vui lòng làm lại phần...', NULL, NULL, NULL, NOW(), NOW()),
    
    -- Student 2 nộp lại bài tập Unit 2 (đã nộp lại sau khi được yêu cầu)
    ('b0000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000002',
     CURRENT_TIMESTAMP - INTERVAL '3 days', 'resubmitted', 'Nội dung bài làm lại của student 2', NULL, NULL, NULL, NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    status = EXCLUDED.status,
    result = EXCLUDED.result;

-- ============================================================
-- 13. LEAVE REQUESTS (Đơn xin nghỉ)
-- ============================================================
INSERT INTO leave_requests (id, student_id, class_id, session_date, session_time, status, created_at, updated_at)
VALUES 
    -- Đơn xin nghỉ chờ duyệt (lớp 1)
    ('c0000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', '70000000-0000-0000-0000-000000000001',
     CURRENT_DATE + INTERVAL '3 days', '18:30:00', 'pending', NOW(), NOW()),
    
    -- Đơn xin nghỉ đã được giáo viên duyệt (lớp 1) - status: approved
    ('c0000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000002', '70000000-0000-0000-0000-000000000001',
     CURRENT_DATE + INTERVAL '5 days', '18:30:00', 'approved', NOW(), NOW()),
    
    -- Đơn xin nghỉ bị từ chối (lớp 1)
    ('c0000000-0000-0000-0000-000000000003', '50000000-0000-0000-0000-000000000003', '70000000-0000-0000-0000-000000000001',
     CURRENT_DATE + INTERVAL '7 days', '18:30:00', 'rejected', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    status = EXCLUDED.status;

-- ============================================================
-- 14. ATTENDANCES (Điểm danh)
-- ============================================================
INSERT INTO attendances (id, student_id, session_id, status)
VALUES 
    -- Điểm danh cho session tuần trước (lớp 1)
    ('d0000000-0000-0000-0000-000000000001', '50000000-0000-0000-0000-000000000001', '80000000-0000-0000-0000-000000000003', 'present'),
    ('d0000000-0000-0000-0000-000000000002', '50000000-0000-0000-0000-000000000002', '80000000-0000-0000-0000-000000000003', 'late'),
    ('d0000000-0000-0000-0000-000000000003', '50000000-0000-0000-0000-000000000003', '80000000-0000-0000-0000-000000000003', 'absent')
ON CONFLICT (id) DO UPDATE SET
    status = EXCLUDED.status;

-- ============================================================
-- 15. ANSWER KEYS (Đáp án bài tập - nếu cần)
-- ============================================================
INSERT INTO answer_keys (id, assignment_id, question_number, correct_option, description, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    'a0000000-0000-0000-0000-000000000001',
    q_num,
    CASE (q_num % 4)
        WHEN 0 THEN 'A'
        WHEN 1 THEN 'B'
        WHEN 2 THEN 'C'
        ELSE 'D'
    END,
    'Đáp án đúng cho câu ' || q_num,
    NOW(),
    NOW()
FROM generate_series(1, 20) AS q_num
ON CONFLICT DO NOTHING;

-- ============================================================
-- 16. STUDENT ANSWERS (Câu trả lời của học viên - nếu cần)
-- ============================================================
-- Lưu ý: is_correct là boolean, cần cast từ integer
INSERT INTO student_answers (id, submission_id, question_number, selected_option, is_correct, updated_at)
SELECT 
    gen_random_uuid(),
    'b0000000-0000-0000-0000-000000000001',
    q_num,
    (q_num % 4) + 1,
    CASE 
        WHEN (q_num % 4) = 0 THEN true  -- Câu 4, 8, 12, 16, 20 đúng
        ELSE false
    END,
    NOW()
FROM generate_series(1, 20) AS q_num
ON CONFLICT DO NOTHING;

-- ============================================================
-- VERIFICATION - Kiểm tra dữ liệu đã insert
-- ============================================================
-- SELECT 'Teachers' as table_name, COUNT(*) as count FROM teachers
-- UNION ALL
-- SELECT 'Students', COUNT(*) FROM students
-- UNION ALL
-- SELECT 'Classes', COUNT(*) FROM classes
-- UNION ALL
-- SELECT 'Sessions', COUNT(*) FROM sessions
-- UNION ALL
-- SELECT 'Enrollments', COUNT(*) FROM enrollments
-- UNION ALL
-- SELECT 'Assignments', COUNT(*) FROM assignments
-- UNION ALL
-- SELECT 'Submissions', COUNT(*) FROM submissions
-- UNION ALL
-- SELECT 'Leave Requests', COUNT(*) FROM leave_requests
-- UNION ALL
-- SELECT 'Attendances', COUNT(*) FROM attendances;

-- ============================================================
-- THÔNG TIN ĐĂNG NHẬP TEST
-- ============================================================
-- TEACHERS:
--   teacher1 / teacher123 (Nguyễn Văn Giáo - Senior - IELTS Speaking)
--   teacher2 / teacher123 (Trần Thị Dạy - Expert - TOEIC)
--   teacher3 / teacher123 (Lê Văn Mới - Junior - IELTS Writing)
--
-- STUDENTS:
--   student1 / student123 (Phạm Văn Học)
--   student2 / student123 (Nguyễn Thị Sinh)
--   student3 / student123 (Lê Văn Viên)
--   student4 / student123 (Trần Thị Học)
--
-- LƯU Ý: Password hash trong script này là dummy. 
--        Cần đổi mật khẩu thực tế sau khi chạy script hoặc
--        sử dụng Django management command để tạo user với password đúng.
-- ============================================================

COMMIT;

