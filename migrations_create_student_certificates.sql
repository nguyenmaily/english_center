-- Migration: Create student_certificates table
-- Run this SQL script to create the student_certificates table in the database

-- 1. Create student_certificates table
CREATE TABLE IF NOT EXISTS student_certificates (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Key to students table
    student_id UUID NOT NULL,
    
    -- Certificate Information
    certificate_type VARCHAR(20) NOT NULL DEFAULT 'other',
    certificate_name TEXT NOT NULL,
    
    -- Scores
    score DECIMAL(5,2) NULL,
    reading_score DECIMAL(5,2) NULL,
    listening_score DECIMAL(5,2) NULL,
    speaking_score DECIMAL(5,2) NULL,
    writing_score DECIMAL(5,2) NULL,
    
    -- Image and Dates
    image_url TEXT NULL,
    issued_date DATE NULL,
    expiry_date DATE NULL,
    
    -- Verification
    verification_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    verified_by_id UUID NULL,
    verified_at TIMESTAMP NULL,
    
    -- Notes
    notes TEXT NULL,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraint
    CONSTRAINT fk_student_certificates_student 
        FOREIGN KEY (student_id) 
        REFERENCES students(id) 
        ON DELETE CASCADE,
    
    -- Foreign Key Constraint for verified_by
    -- Lưu ý: Chỉ quản lý (manager) mới có quyền verify chứng chỉ
    -- Logic kiểm tra quyền được xử lý ở application level (views/permissions)
    CONSTRAINT fk_student_certificates_verified_by 
        FOREIGN KEY (verified_by_id) 
        REFERENCES user_accounts(id) 
        ON DELETE SET NULL,
    
    -- Check constraints
    CONSTRAINT chk_certificate_type 
        CHECK (certificate_type IN ('ielts', 'toeic', 'toefl', 'cambridge', 'other')),
    
    CONSTRAINT chk_verification_status 
        CHECK (verification_status IN ('pending', 'verified', 'rejected')),
    
    CONSTRAINT chk_score_range 
        CHECK (
            (score IS NULL) OR 
            (certificate_type = 'ielts' AND score >= 0 AND score <= 9) OR
            (certificate_type = 'toeic' AND score >= 0 AND score <= 990) OR
            (certificate_type = 'toefl' AND score >= 0 AND score <= 120) OR
            (certificate_type IN ('cambridge', 'other'))
        ),
    
    CONSTRAINT chk_skill_scores_range 
        CHECK (
            (reading_score IS NULL OR (reading_score >= 0 AND reading_score <= 9)) AND
            (listening_score IS NULL OR (listening_score >= 0 AND listening_score <= 9)) AND
            (speaking_score IS NULL OR (speaking_score >= 0 AND speaking_score <= 9)) AND
            (writing_score IS NULL OR (writing_score >= 0 AND writing_score <= 9))
        ),
    
    CONSTRAINT chk_dates 
        CHECK (expiry_date IS NULL OR issued_date IS NULL OR expiry_date >= issued_date)
);

-- 2. Add comments for columns
COMMENT ON TABLE student_certificates IS 'Bảng lưu thông tin chứng chỉ của học viên';
COMMENT ON COLUMN student_certificates.id IS 'Primary key (UUID)';
COMMENT ON COLUMN student_certificates.student_id IS 'Foreign key đến bảng students';
COMMENT ON COLUMN student_certificates.certificate_type IS 'Loại chứng chỉ: ielts, toeic, toefl, cambridge, other';
COMMENT ON COLUMN student_certificates.certificate_name IS 'Tên chứng chỉ (ví dụ: IELTS Academic, TOEIC Listening & Reading)';
COMMENT ON COLUMN student_certificates.score IS 'Tổng điểm chứng chỉ (ví dụ: IELTS 6.5, TOEIC 750)';
COMMENT ON COLUMN student_certificates.reading_score IS 'Điểm kỹ năng đọc';
COMMENT ON COLUMN student_certificates.listening_score IS 'Điểm kỹ năng nghe';
COMMENT ON COLUMN student_certificates.speaking_score IS 'Điểm kỹ năng nói';
COMMENT ON COLUMN student_certificates.writing_score IS 'Điểm kỹ năng viết';
COMMENT ON COLUMN student_certificates.image_url IS 'URL hình ảnh chứng chỉ (lưu trên cloud storage hoặc local)';
COMMENT ON COLUMN student_certificates.issued_date IS 'Ngày cấp chứng chỉ';
COMMENT ON COLUMN student_certificates.expiry_date IS 'Ngày hết hạn chứng chỉ (nếu có)';
COMMENT ON COLUMN student_certificates.verification_status IS 'Trạng thái xác minh: pending, verified, rejected';
COMMENT ON COLUMN student_certificates.verified_by_id IS 'Foreign key đến user_accounts (người xác minh - chỉ quản lý/manager mới có quyền verify)';
COMMENT ON COLUMN student_certificates.verified_at IS 'Thời điểm xác minh';
COMMENT ON COLUMN student_certificates.notes IS 'Ghi chú về chứng chỉ';
COMMENT ON COLUMN student_certificates.created_at IS 'Thời gian tạo';
COMMENT ON COLUMN student_certificates.updated_at IS 'Thời gian cập nhật';

-- 3. Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_student_certificates_student_id ON student_certificates(student_id);
CREATE INDEX IF NOT EXISTS idx_student_certificates_certificate_type ON student_certificates(certificate_type);
CREATE INDEX IF NOT EXISTS idx_student_certificates_verification_status ON student_certificates(verification_status);
CREATE INDEX IF NOT EXISTS idx_student_certificates_issued_date ON student_certificates(issued_date);
CREATE INDEX IF NOT EXISTS idx_student_certificates_expiry_date ON student_certificates(expiry_date);
CREATE INDEX IF NOT EXISTS idx_student_certificates_verified_by_id ON student_certificates(verified_by_id);
CREATE INDEX IF NOT EXISTS idx_student_certificates_score ON student_certificates(score) WHERE score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_student_certificates_reading_score ON student_certificates(reading_score) WHERE reading_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_student_certificates_listening_score ON student_certificates(listening_score) WHERE listening_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_student_certificates_speaking_score ON student_certificates(speaking_score) WHERE speaking_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_student_certificates_writing_score ON student_certificates(writing_score) WHERE writing_score IS NOT NULL;

-- 4. Create trigger to update updated_at automatically
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

-- 5. Grant permissions (adjust as needed for your database user)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON student_certificates TO your_app_user;

