-- ============================================================
-- MIGRATION SCRIPT: Đổi quan hệ Course-Skill
-- Từ: Skill.course_id (1 Course có nhiều Skills)
-- Sang: Course.skill_id (1 Course có 1 Skill)
-- ============================================================
-- 
-- ⚠️ QUAN TRỌNG: Backup database trước khi chạy script này!
-- 
-- Logic migrate:
-- - 1 course chỉ có 1 skill (LR hoặc SW)
-- - Lấy skill đầu tiên của mỗi course (theo thứ tự tạo)
-- - Course không có skill → skill_id = NULL
-- - 1 skill có thể thuộc nhiều courses
-- ============================================================

BEGIN;

-- ============================================================
-- BƯỚC 1: Kiểm tra dữ liệu hiện tại
-- ============================================================
-- Chạy các query này để xem dữ liệu trước khi migrate:

-- Xem courses có bao nhiêu skills
-- SELECT c.id, c.name, COUNT(s.id) as skills_count
-- FROM courses c
-- LEFT JOIN skills s ON s.course_id = c.id
-- GROUP BY c.id, c.name
-- ORDER BY skills_count DESC;

-- Xem courses có nhiều hơn 1 skill (cần xử lý)
-- SELECT c.id, c.name, COUNT(s.id) as skills_count
-- FROM courses c
-- INNER JOIN skills s ON s.course_id = c.id
-- GROUP BY c.id, c.name
-- HAVING COUNT(s.id) > 1;

-- ============================================================
-- BƯỚC 2: Thêm skill_id vào bảng courses
-- ============================================================
ALTER TABLE courses 
ADD COLUMN skill_id UUID REFERENCES skills(id);

-- Tạo index để tăng hiệu suất
CREATE INDEX idx_courses_skill_id ON courses(skill_id);

-- ============================================================
-- BƯỚC 3: Migrate dữ liệu từ skills.course_id sang courses.skill_id
-- ============================================================
-- Logic: Lấy skill đầu tiên của mỗi course (theo thứ tự tạo - id)
UPDATE courses c
SET skill_id = (
    SELECT s.id 
    FROM skills s 
    WHERE s.course_id = c.id 
    ORDER BY s.created_at ASC, s.id ASC
    LIMIT 1
)
WHERE EXISTS (
    SELECT 1 FROM skills s WHERE s.course_id = c.id
);

-- ============================================================
-- BƯỚC 4: Kiểm tra dữ liệu sau khi migrate
-- ============================================================
-- Chạy các query này để verify:

-- Xem courses đã có skill_id chưa
-- SELECT c.id, c.name, c.skill_id, s.name as skill_name
-- FROM courses c
-- LEFT JOIN skills s ON s.id = c.skill_id
-- ORDER BY c.name;

-- Xem courses chưa có skill_id (nếu có)
-- SELECT c.id, c.name
-- FROM courses c
-- WHERE c.skill_id IS NULL;

-- Xem skills không còn thuộc course nào (sẽ bị orphan sau khi xóa course_id)
-- SELECT s.id, s.name
-- FROM skills s
-- WHERE NOT EXISTS (
--     SELECT 1 FROM courses c WHERE c.skill_id = s.id
-- );

-- ============================================================
-- BƯỚC 5: Xóa foreign key constraint và column course_id khỏi skills
-- ============================================================
-- Lưu ý: PostgreSQL cần drop constraint trước khi drop column

-- Tìm tên constraint (thường là: skills_course_id_fkey)
-- SELECT constraint_name 
-- FROM information_schema.table_constraints 
-- WHERE table_name = 'skills' 
-- AND constraint_type = 'FOREIGN KEY'
-- AND constraint_name LIKE '%course_id%';

-- Drop foreign key constraint (thay 'skills_course_id_fkey' bằng tên thực tế)
-- ALTER TABLE skills DROP CONSTRAINT IF EXISTS skills_course_id_fkey;

-- Drop column course_id
ALTER TABLE skills DROP COLUMN IF EXISTS course_id;

-- ============================================================
-- BƯỚC 6: Cleanup (tùy chọn)
-- ============================================================
-- Nếu muốn set NOT NULL cho skill_id (sau khi đảm bảo tất cả courses đều có skill):
-- ALTER TABLE courses ALTER COLUMN skill_id SET NOT NULL;

-- ============================================================
-- ROLLBACK SCRIPT (nếu cần rollback)
-- ============================================================
-- Nếu cần rollback, chạy script sau:

-- BEGIN;
-- 
-- -- Thêm lại course_id vào skills
-- ALTER TABLE skills 
-- ADD COLUMN course_id UUID REFERENCES courses(id);
-- 
-- -- Migrate dữ liệu ngược lại
-- UPDATE skills s
-- SET course_id = (
--     SELECT c.id 
--     FROM courses c 
--     WHERE c.skill_id = s.id 
--     LIMIT 1
-- )
-- WHERE EXISTS (
--     SELECT 1 FROM courses c WHERE c.skill_id = s.id
-- );
-- 
-- -- Xóa skill_id khỏi courses
-- ALTER TABLE courses DROP COLUMN IF EXISTS skill_id;
-- 
-- COMMIT;

-- ============================================================
-- COMMIT
-- ============================================================
COMMIT;

-- ============================================================
-- VERIFICATION QUERIES (chạy sau khi commit)
-- ============================================================

-- 1. Kiểm tra courses có skill_id
-- SELECT COUNT(*) as total_courses,
--        COUNT(skill_id) as courses_with_skill,
--        COUNT(*) - COUNT(skill_id) as courses_without_skill
-- FROM courses;

-- 2. Kiểm tra skills không còn course_id
-- SELECT COUNT(*) as total_skills
-- FROM skills;

-- 3. Kiểm tra quan hệ 1-nhiều (1 skill có nhiều courses)
-- SELECT s.id, s.name, COUNT(c.id) as courses_count
-- FROM skills s
-- LEFT JOIN courses c ON c.skill_id = s.id
-- GROUP BY s.id, s.name
-- ORDER BY courses_count DESC;

