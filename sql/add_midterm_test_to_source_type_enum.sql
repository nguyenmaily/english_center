-- ============================================================================
-- SQL Script: Thêm giá trị 'midterm_test' vào enum source_type_enum
-- Mô tả: Cho phép phân biệt giữa test giữa khóa và test cuối khóa
-- ============================================================================

-- Thêm giá trị mới vào enum (PostgreSQL cho phép ALTER TYPE ... ADD VALUE)
ALTER TYPE source_type_enum ADD VALUE IF NOT EXISTS 'midterm_test';

-- Cập nhật comment
COMMENT ON TYPE source_type_enum IS 'certificate: Chứng chỉ; entry_test: Test đầu vào; midterm_test: Test giữa khóa; final_test: Test cuối khóa';

-- Cập nhật comment cho cột source_type
COMMENT ON COLUMN student_certificates.source_type IS 'certificate: Chứng chỉ; entry_test: Test đầu vào; midterm_test: Test giữa khóa; final_test: Test cuối khóa';

