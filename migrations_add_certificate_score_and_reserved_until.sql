-- Migration: Add score to student_certificates and reserved_until to enrollments
-- Run this SQL script to update the database schema

-- 1. Add score column to student_certificates table
ALTER TABLE student_certificates 
ADD COLUMN IF NOT EXISTS score DECIMAL(5,2) NULL;

-- Add comment
COMMENT ON COLUMN student_certificates.score IS 'Điểm số chứng chỉ (ví dụ: IELTS 6.5, TOEIC 750)';

-- 2. Add reserved_until column to enrollments table
ALTER TABLE enrollments 
ADD COLUMN IF NOT EXISTS reserved_until TIMESTAMP NULL;

-- Add comment
COMMENT ON COLUMN enrollments.reserved_until IS 'Thời hạn giữ chỗ (sau thời điểm này sẽ tự động hủy nếu chưa thanh toán)';

-- 3. Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_enrollments_reserved_until ON enrollments(reserved_until) WHERE reserved_until IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_student_certificates_score ON student_certificates(score) WHERE score IS NOT NULL;

-- 4. Update invoice_status to use new enum values (optional - if you want to use the new statuses)
-- Note: This is optional, existing 'pending', 'paid', 'overdue', 'canceled' will still work
-- New statuses: 'reserved', 'expired' can be added if needed


