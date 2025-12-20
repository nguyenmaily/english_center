-- ============================================================
-- SCRIPT SETUP TẤT CẢ DỮ LIỆU TEST
-- ============================================================
-- Chạy: psql -U your_username -d your_database -f setup_all_data.sql
-- ============================================================

BEGIN;

-- ============================================================
-- 1. XÓA DỮ LIỆU CŨ (NẾU CẦN)
-- ============================================================
-- Uncomment các dòng dưới nếu muốn xóa data cũ
-- DELETE FROM role_permissions;
-- DELETE FROM permissions;
-- DELETE FROM roles;
-- DELETE FROM user_accounts;
-- DELETE FROM campuses;
-- DELETE FROM courses;
-- DELETE FROM classes;

-- ============================================================
-- 2. TẠO ROLES
-- ============================================================
INSERT INTO roles (id, name, description, created_at, updated_at)
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'student', 'Student user', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000002', 'teacher', 'Teacher user', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000003', 'manager', 'Manager user', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000004', 'admin', 'Administrator user', NOW(), NOW())
ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description;

-- ============================================================
-- 3. TẠO PERMISSIONS
-- ============================================================
INSERT INTO permissions (id, name, description, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'view_profile', 'Can view own profile', NOW(), NOW()),
    (gen_random_uuid(), 'edit_profile', 'Can edit own profile', NOW(), NOW()),
    (gen_random_uuid(), 'view_all_users', 'Can view all users', NOW(), NOW()),
    (gen_random_uuid(), 'edit_all_users', 'Can edit all users', NOW(), NOW()),
    (gen_random_uuid(), 'view_courses', 'Can view courses', NOW(), NOW()),
    (gen_random_uuid(), 'manage_courses', 'Can manage courses', NOW(), NOW()),
    (gen_random_uuid(), 'view_classes', 'Can view classes', NOW(), NOW()),
    (gen_random_uuid(), 'manage_classes', 'Can manage classes', NOW(), NOW()),
    (gen_random_uuid(), 'manage_finance', 'Can manage finance', NOW(), NOW()),
    (gen_random_uuid(), 'generate_reports', 'Can generate reports', NOW(), NOW()),
    (gen_random_uuid(), 'manage_roles', 'Can manage roles and permissions', NOW(), NOW())
ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description;

-- ============================================================
-- 4. GÁN PERMISSIONS CHO ROLES
-- ============================================================
-- Xóa role_permissions cũ
DELETE FROM role_permissions;

-- Student permissions
INSERT INTO role_permissions (role_id, permission_id, created_at, updated_at)
SELECT 
    r.id,
    p.id,
    NOW(),
    NOW()
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'student'
  AND p.name IN ('view_profile', 'edit_profile', 'view_courses', 'view_classes')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Teacher permissions
INSERT INTO role_permissions (role_id, permission_id, created_at, updated_at)
SELECT 
    r.id,
    p.id,
    NOW(),
    NOW()
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'teacher'
  AND p.name IN ('view_profile', 'edit_profile', 'view_courses', 'view_classes', 'manage_classes', 'manage_courses')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Manager permissions
INSERT INTO role_permissions (role_id, permission_id, created_at, updated_at)
SELECT 
    r.id,
    p.id,
    NOW(),
    NOW()
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'manager'
  AND p.name IN ('view_profile', 'edit_profile', 'view_all_users', 'view_courses', 'view_classes', 'manage_classes', 'manage_courses', 'generate_reports')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Admin permissions (tất cả)
INSERT INTO role_permissions (role_id, permission_id, created_at, updated_at)
SELECT 
    r.id,
    p.id,
    NOW(),
    NOW()
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'admin'
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- ============================================================
-- 5. TẠO CAMPUSES
-- ============================================================
INSERT INTO campuses (id, name, address, hotline, email, status, created_at, updated_at)
VALUES 
    ('10000000-0000-0000-0000-000000000001', 'Co so Quan 1', '123 Nguyen Hue, Quan 1, TP.HCM', '0281234567', 'q1@englishcenter.com', 'active', NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000002', 'Co so Quan 3', '456 Le Van Sy, Quan 3, TP.HCM', '0282345678', 'q3@englishcenter.com', 'active', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    address = EXCLUDED.address,
    hotline = EXCLUDED.hotline,
    email = EXCLUDED.email,
    status = EXCLUDED.status;

-- ============================================================
-- 6. TẠO USERS (password sẽ được set bằng Django)
-- ============================================================
-- Admin user
INSERT INTO user_accounts (id, username, password_hash, email, status, role_id, full_name, created_at, updated_at)
VALUES 
    ('20000000-0000-0000-0000-000000000001', 'admin.ly', 'pbkdf2_sha256$600000$temp$temp', 'admin@englishcenter.com', 'active', 
     (SELECT id FROM roles WHERE name = 'admin'), 'Administrator', NOW(), NOW())
ON CONFLICT (username) DO UPDATE SET 
    email = EXCLUDED.email,
    role_id = EXCLUDED.role_id,
    status = EXCLUDED.status;

-- Manager user
INSERT INTO user_accounts (id, username, password_hash, email, status, role_id, full_name, created_at, updated_at)
VALUES 
    ('20000000-0000-0000-0000-000000000002', 'ql.hoangc', 'pbkdf2_sha256$600000$temp$temp', 'manager@englishcenter.com', 'active',
     (SELECT id FROM roles WHERE name = 'manager'), 'Hoang C', NOW(), NOW())
ON CONFLICT (username) DO UPDATE SET 
    email = EXCLUDED.email,
    role_id = EXCLUDED.role_id,
    status = EXCLUDED.status;

-- Teacher users
INSERT INTO user_accounts (id, username, password_hash, email, status, role_id, full_name, created_at, updated_at)
VALUES 
    ('20000000-0000-0000-0000-000000000003', 'gv.nguyena', 'pbkdf2_sha256$600000$temp$temp', 'gv.nguyena@englishcenter.com', 'active',
     (SELECT id FROM roles WHERE name = 'teacher'), 'Nguyen A', NOW(), NOW()),
    ('20000000-0000-0000-0000-000000000004', 'gv.tranb', 'pbkdf2_sha256$600000$temp$temp', 'gv.tranb@englishcenter.com', 'active',
     (SELECT id FROM roles WHERE name = 'teacher'), 'Tran B', NOW(), NOW())
ON CONFLICT (username) DO UPDATE SET 
    email = EXCLUDED.email,
    role_id = EXCLUDED.role_id,
    status = EXCLUDED.status;

-- Student users
INSERT INTO user_accounts (id, username, password_hash, email, status, role_id, full_name, created_at, updated_at)
VALUES 
    ('20000000-0000-0000-0000-000000000005', 'hv.minhd', 'pbkdf2_sha256$600000$temp$temp', 'hv.minhd@englishcenter.com', 'active',
     (SELECT id FROM roles WHERE name = 'student'), 'Minh D', NOW(), NOW()),
    ('20000000-0000-0000-0000-000000000006', 'hv.linh e', 'pbkdf2_sha256$600000$temp$temp', 'hv.linh e@englishcenter.com', 'active',
     (SELECT id FROM roles WHERE name = 'student'), 'Linh E', NOW(), NOW())
ON CONFLICT (username) DO UPDATE SET 
    email = EXCLUDED.email,
    role_id = EXCLUDED.role_id,
    status = EXCLUDED.status;

-- ============================================================
-- 7. TẠO TEACHER PROFILES
-- ============================================================
INSERT INTO teachers (id, user_account_id, level, specialization, campus_id, created_at, updated_at)
VALUES 
    ('30000000-0000-0000-0000-000000000001', 
     (SELECT id FROM user_accounts WHERE username = 'gv.nguyena'),
     'Senior', 'IELTS Speaking',
     (SELECT id FROM campuses WHERE name = 'Co so Quan 1'),
     NOW(), NOW()),
    ('30000000-0000-0000-0000-000000000002',
     (SELECT id FROM user_accounts WHERE username = 'gv.tranb'),
     'Expert', 'TOEIC',
     (SELECT id FROM campuses WHERE name = 'Co so Quan 1'),
     NOW(), NOW())
ON CONFLICT (user_account_id) DO UPDATE SET
    level = EXCLUDED.level,
    specialization = EXCLUDED.specialization,
    campus_id = EXCLUDED.campus_id;

-- ============================================================
-- 8. TẠO MANAGER PROFILE
-- ============================================================
INSERT INTO managers (id, user_account_id, campus_id, created_at, updated_at)
VALUES 
    ('40000000-0000-0000-0000-000000000001',
     (SELECT id FROM user_accounts WHERE username = 'ql.hoangc'),
     (SELECT id FROM campuses WHERE name = 'Co so Quan 1'),
     NOW(), NOW())
ON CONFLICT (user_account_id) DO UPDATE SET
    campus_id = EXCLUDED.campus_id;

-- ============================================================
-- 9. TẠO STUDENT PROFILES
-- ============================================================
INSERT INTO students (id, user_account_id, target_score, commitment_status, created_at, updated_at)
VALUES 
    ('50000000-0000-0000-0000-000000000001',
     (SELECT id FROM user_accounts WHERE username = 'hv.minhd'),
     '7.0', 'committed',
     NOW(), NOW()),
    ('50000000-0000-0000-0000-000000000002',
     (SELECT id FROM user_accounts WHERE username = 'hv.linh e'),
     '6.5', 'committed',
     NOW(), NOW())
ON CONFLICT (user_account_id) DO UPDATE SET
    target_score = EXCLUDED.target_score,
    commitment_status = EXCLUDED.commitment_status;

-- ============================================================
-- 10. TẠO COURSES
-- ============================================================
INSERT INTO courses (id, name, level, description, total_sessions, fee, min_entry_score, created_at, updated_at)
VALUES 
    ('60000000-0000-0000-0000-000000000001', 'IELTS Foundation', 'Beginner', 'IELTS basic course', 30, 5000000, NULL, NOW(), NOW()),
    ('60000000-0000-0000-0000-000000000002', 'IELTS Intermediate', 'Intermediate', 'IELTS intermediate course', 40, 7000000, 5.0, NOW(), NOW()),
    ('60000000-0000-0000-0000-000000000003', 'TOEIC 500+', 'Intermediate', 'TOEIC course from 500 points', 35, 6000000, NULL, NOW(), NOW())
ON CONFLICT (name) DO UPDATE SET
    level = EXCLUDED.level,
    description = EXCLUDED.description,
    total_sessions = EXCLUDED.total_sessions,
    fee = EXCLUDED.fee,
    min_entry_score = EXCLUDED.min_entry_score;

COMMIT;

-- ============================================================
-- HOÀN TẤT!
-- ============================================================
-- Sau khi chạy script SQL này, chạy lệnh sau để set passwords:
-- python manage.py fix_passwords
-- ============================================================

