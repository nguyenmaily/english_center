-- Migration: Add 'practice' value to exam_type_enum
-- Run this SQL script to update the enum type in the database

-- 1. Add 'practice' value to exam_type_enum
ALTER TYPE exam_type_enum ADD VALUE IF NOT EXISTS 'practice';

-- Note: 
-- - IF NOT EXISTS chỉ hoạt động từ PostgreSQL 9.5+
-- - Nếu gặp lỗi, có thể enum đã có giá trị 'practice' rồi
-- - Kiểm tra enum hiện tại: SELECT unnest(enum_range(NULL::exam_type_enum));

