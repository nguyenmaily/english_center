-- ============================================================================
-- SQL Script: Tạo bảng student_certificates
-- Mô tả: Bảng lưu trữ tất cả các sự kiện thay đổi điểm số năng lực tiếng Anh
-- ============================================================================

-- Tạo các ENUM types
CREATE TYPE skill_group_enum AS ENUM ('LR', 'SW');
CREATE TYPE source_type_enum AS ENUM ('certificate', 'entry_test', 'final_test');
CREATE TYPE certificate_status_enum AS ENUM ('VERIFIED', 'PENDING', 'REJECTED');
CREATE TYPE verification_method_enum AS ENUM ('auto_ocr', 'manual_admin');

-- Tạo bảng student_certificates
CREATE TABLE IF NOT EXISTS student_certificates (
    id BIGSERIAL PRIMARY KEY,
    student_id UUID NOT NULL,
    skill_group skill_group_enum NOT NULL,
    source_type source_type_enum NOT NULL,
    score_1 INTEGER,  -- Listening hoặc Speaking
    score_2 INTEGER,  -- Reading hoặc Writing
    total_score INTEGER NOT NULL,
    test_date DATE NOT NULL,
    expired_date DATE NOT NULL,
    proof_image TEXT,  -- Link ảnh chứng chỉ (nullable)
    status certificate_status_enum NOT NULL DEFAULT 'PENDING',
    admin_id INTEGER,  -- ID Admin thực hiện duyệt (nullable)
    verification_method verification_method_enum NOT NULL DEFAULT 'auto_ocr',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key constraints
    CONSTRAINT fk_student_certificates_student 
        FOREIGN KEY (student_id) 
        REFERENCES students(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT fk_student_certificates_admin 
        FOREIGN KEY (admin_id) 
        REFERENCES user_accounts(id) 
        ON DELETE SET NULL,
    
    -- Check constraints
    CONSTRAINT chk_total_score_positive 
        CHECK (total_score >= 0),
    
    CONSTRAINT chk_lr_score_range 
        CHECK (
            (skill_group = 'LR' AND total_score >= 0 AND total_score <= 990) OR
            (skill_group = 'SW' AND total_score >= 0 AND total_score <= 400) OR
            (skill_group NOT IN ('LR', 'SW'))
        ),
    
    CONSTRAINT chk_expired_date_after_test_date 
        CHECK (expired_date >= test_date)
);

-- Tạo indexes để tối ưu truy vấn
CREATE INDEX idx_student_certificates_student_id ON student_certificates(student_id);
CREATE INDEX idx_student_certificates_skill_group ON student_certificates(skill_group);
CREATE INDEX idx_student_certificates_status ON student_certificates(status);
CREATE INDEX idx_student_certificates_test_date ON student_certificates(test_date DESC);
CREATE INDEX idx_student_certificates_expired_date ON student_certificates(expired_date);
CREATE INDEX idx_student_certificates_student_skill_status_expired ON student_certificates(student_id, skill_group, status, expired_date);

-- Tạo trigger để tự động cập nhật updated_at
CREATE OR REPLACE FUNCTION update_student_certificates_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_student_certificates_updated_at
    BEFORE UPDATE ON student_certificates
    FOR EACH ROW
    EXECUTE FUNCTION update_student_certificates_updated_at();

-- Comments cho documentation
COMMENT ON TABLE student_certificates IS 'Bảng lưu trữ tất cả các sự kiện thay đổi điểm số năng lực tiếng Anh của học viên';
COMMENT ON COLUMN student_certificates.skill_group IS 'LR: Listening-Reading; SW: Speaking-Writing';
COMMENT ON COLUMN student_certificates.source_type IS 'certificate: Chứng chỉ; entry_test: Test đầu vào; final_test: Test cuối khóa';
COMMENT ON COLUMN student_certificates.score_1 IS 'Listening (nếu skill_group=LR) hoặc Speaking (nếu skill_group=SW)';
COMMENT ON COLUMN student_certificates.score_2 IS 'Reading (nếu skill_group=LR) hoặc Writing (nếu skill_group=SW)';
COMMENT ON COLUMN student_certificates.total_score IS 'Điểm tổng dùng để xét lớp. LR: 0-990, SW: 0-400';
COMMENT ON COLUMN student_certificates.status IS 'VERIFIED: Đã xác thực; PENDING: Chờ duyệt; REJECTED: Từ chối';
COMMENT ON COLUMN student_certificates.verification_method IS 'auto_ocr: Tự động xác thực bằng OCR; manual_admin: Admin duyệt thủ công';






