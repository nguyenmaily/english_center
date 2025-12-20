-- SQL Script để xóa bảng enrollment_enrollment
-- Bảng này là bảng cũ/duplicate của enrollments
-- Đã được thay thế bằng bảng enrollments với cấu trúc tốt hơn

-- LƯU Ý: 
-- 1. Backup database trước khi chạy script này
-- 2. Kiểm tra xem bảng có data không (đã kiểm tra: không có data)
-- 3. Kiểm tra xem có code nào đang sử dụng bảng này không

-- Kiểm tra xem bảng có tồn tại không
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'enrollment_enrollment'
    ) THEN
        -- Xóa bảng
        DROP TABLE IF EXISTS public.enrollment_enrollment CASCADE;
        RAISE NOTICE 'Bảng enrollment_enrollment đã được xóa thành công';
    ELSE
        RAISE NOTICE 'Bảng enrollment_enrollment không tồn tại';
    END IF;
END $$;


