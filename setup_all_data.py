#!/usr/bin/env python
"""
Script tổng hợp để tạo lại toàn bộ dữ liệu test
Chạy: python setup_all_data.py
"""
import os
import django
import uuid
from datetime import date, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'english_center.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from authentication.models import Role, Permission, RolePermission
from users.models import Student, Teacher, Manager
from campus.models import Campus
from courses.models import Course, Skill
from classes.models import Class
from class_sessions.models import Session

User = get_user_model()

print("=" * 60)
print("SETUP ALL TEST DATA")
print("=" * 60)

# ============================================================
# 1. TẠO ROLES
# ============================================================
print("\n[1/8] Creating Roles...")
roles_data = [
    {'name': 'student', 'description': 'Student user'},
    {'name': 'teacher', 'description': 'Teacher user'},
    {'name': 'manager', 'description': 'Manager user'},
    {'name': 'admin', 'description': 'Administrator user'},
]

roles_dict = {}
for role_data in roles_data:
    role, created = Role.objects.get_or_create(
        name=role_data['name'],
        defaults={'description': role_data['description']}
    )
    roles_dict[role_data['name']] = role
    if created:
        print(f"  [OK] Created role: {role.name}")
    else:
        print(f"  [SKIP] Role already exists: {role.name}")

# ============================================================
# 2. TẠO PERMISSIONS
# ============================================================
print("\n[2/8] Creating Permissions...")
permissions_data = [
    {'name': 'view_profile', 'description': 'Can view own profile'},
    {'name': 'edit_profile', 'description': 'Can edit own profile'},
    {'name': 'view_all_users', 'description': 'Can view all users'},
    {'name': 'edit_all_users', 'description': 'Can edit all users'},
    {'name': 'view_courses', 'description': 'Can view courses'},
    {'name': 'manage_courses', 'description': 'Can manage courses'},
    {'name': 'view_classes', 'description': 'Can view classes'},
    {'name': 'manage_classes', 'description': 'Can manage classes'},
    {'name': 'manage_finance', 'description': 'Can manage finance'},
    {'name': 'generate_reports', 'description': 'Can generate reports'},
    {'name': 'manage_roles', 'description': 'Can manage roles and permissions'},
]

permissions_dict = {}
for perm_data in permissions_data:
    permission, created = Permission.objects.get_or_create(
        name=perm_data['name'],
        defaults={'description': perm_data['description']}
    )
    permissions_dict[perm_data['name']] = permission
    if created:
        print(f"  [OK] Created permission: {permission.name}")
    else:
        print(f"  [SKIP] Permission already exists: {permission.name}")

# ============================================================
# 3. GÁN PERMISSIONS CHO ROLES
# ============================================================
print("\n[3/8] Assigning Permissions to Roles...")
role_permissions = {
    'student': [
        'view_profile',
        'edit_profile',
        'view_courses',
        'view_classes',
    ],
    'teacher': [
        'view_profile',
        'edit_profile',
        'view_courses',
        'view_classes',
        'manage_classes',
        'manage_courses',
    ],
    'manager': [
        'view_profile',
        'edit_profile',
        'view_all_users',
        'view_courses',
        'view_classes',
        'manage_classes',
        'manage_courses',
        'generate_reports',
    ],
    'admin': list(permissions_dict.keys())  # Tất cả permissions
}

for role_name, perm_names in role_permissions.items():
    role = roles_dict[role_name]
    # Xóa permissions cũ
    RolePermission.objects.filter(role=role).delete()
    
    for perm_name in perm_names:
        if perm_name in permissions_dict:
            permission = permissions_dict[perm_name]
            RolePermission.objects.get_or_create(role=role, permission=permission)
    
    print(f"  [OK] Assigned {len(perm_names)} permissions to role: {role_name}")

# ============================================================
# 4. TẠO CAMPUSES
# ============================================================
print("\n[4/8] Creating Campuses...")
campuses_data = [
    {
        'name': 'Cơ sở Quận 1',
        'address': '123 Nguyễn Huệ, Quận 1, TP.HCM',
        'hotline': '0281234567',
        'email': 'q1@englishcenter.com',
        'status': 'active'
    },
    {
        'name': 'Cơ sở Quận 3',
        'address': '456 Lê Văn Sỹ, Quận 3, TP.HCM',
        'hotline': '0282345678',
        'email': 'q3@englishcenter.com',
        'status': 'active'
    },
]

campuses_dict = {}
for campus_data in campuses_data:
    campus, created = Campus.objects.get_or_create(
        name=campus_data['name'],
        defaults=campus_data
    )
    campuses_dict[campus_data['name']] = campus
    if created:
        print(f"  [OK] Created campus: {campus.name}")
    else:
        print(f"  [SKIP] Campus already exists: {campus.name}")

# ============================================================
# 5. TẠO USERS VÀ PROFILES
# ============================================================
print("\n[5/8] Creating Users and Profiles...")

# Admin user
admin_role = roles_dict['admin']
admin_user, created = User.objects.get_or_create(
    username='admin.ly',
    defaults={
        'email': 'admin@englishcenter.com',
        'fullname': 'Administrator',
        'roleid': admin_role,
        'status': 'active'
    }
)
if created:
    admin_user.set_password('admin')
    admin_user.save()
    print(f"  [OK] Created admin user: admin.ly / admin")
else:
    admin_user.set_password('admin')
    admin_user.save()
    print(f"  [OK] Updated admin user password")

# Manager user
manager_role = roles_dict['manager']
manager_user, created = User.objects.get_or_create(
    username='ql.hoangc',
    defaults={
        'email': 'manager@englishcenter.com',
        'fullname': 'Hoàng C',
        'roleid': manager_role,
        'status': 'active'
    }
)
if created:
    manager_user.set_password('manager')
    manager_user.save()
    manager_profile, _ = Manager.objects.get_or_create(
        user_account=manager_user,
        defaults={'campus': campuses_dict['Cơ sở Quận 1']}
    )
    print(f"  [OK] Created manager user: ql.hoangc / manager")
else:
    manager_user.set_password('manager')
    manager_user.save()
    print(f"  [OK] Updated manager user password")

# Teacher users
teacher_role = roles_dict['teacher']
teachers_data = [
    {'username': 'gv.nguyena', 'fullname': 'Nguyễn A', 'level': 'Senior', 'specialization': 'IELTS Speaking'},
    {'username': 'gv.tranb', 'fullname': 'Trần B', 'level': 'Expert', 'specialization': 'TOEIC'},
]

for teacher_data in teachers_data:
    teacher_user, created = User.objects.get_or_create(
        username=teacher_data['username'],
        defaults={
            'email': f"{teacher_data['username']}@englishcenter.com",
            'fullname': teacher_data['fullname'],
            'roleid': teacher_role,
            'status': 'active'
        }
    )
    if created:
        teacher_user.set_password('teacher')
        teacher_user.save()
        teacher_profile, _ = Teacher.objects.get_or_create(
            user_account=teacher_user,
            defaults={
                'level': teacher_data['level'],
                'specialization': teacher_data['specialization'],
                'campus': campuses_dict['Cơ sở Quận 1']
            }
        )
        print(f"  [OK] Created teacher: {teacher_data['username']} / teacher")
    else:
        teacher_user.set_password('teacher')
        teacher_user.save()
        print(f"  [OK] Updated teacher password: {teacher_data['username']}")

# Student users
student_role = roles_dict['student']
students_data = [
    {'username': 'hv.minhd', 'fullname': 'Minh D', 'target_score': '7.0', 'commitment_status': 'committed'},
    {'username': 'hv.linh e', 'fullname': 'Linh E', 'target_score': '6.5', 'commitment_status': 'committed'},
]

for student_data in students_data:
    student_user, created = User.objects.get_or_create(
        username=student_data['username'],
        defaults={
            'email': f"{student_data['username']}@englishcenter.com",
            'fullname': student_data['fullname'],
            'roleid': student_role,
            'status': 'active'
        }
    )
    if created:
        student_user.set_password('student')
        student_user.save()
        student_profile, _ = Student.objects.get_or_create(
            user_account=student_user,
            defaults={
                'target_score': student_data['target_score'],
                'commitment_status': student_data['commitment_status']
            }
        )
        print(f"  [OK] Created student: {student_data['username']} / student")
    else:
        student_user.set_password('student')
        student_user.save()
        print(f"  [OK] Updated student password: {student_data['username']}")

# ============================================================
# 6. TẠO COURSES
# ============================================================
print("\n[6/8] Creating Courses...")
courses_data = [
    {
        'name': 'IELTS Foundation',
        'level': 'Beginner',
        'description': 'Khóa học IELTS cơ bản',
        'total_sessions': 30,
        'fee': 5000000,
        'min_entry_score': None
    },
    {
        'name': 'IELTS Intermediate',
        'level': 'Intermediate',
        'description': 'Khóa học IELTS trung cấp',
        'total_sessions': 40,
        'fee': 7000000,
        'min_entry_score': 5.0
    },
    {
        'name': 'TOEIC 500+',
        'level': 'Intermediate',
        'description': 'Khóa học TOEIC từ 500 điểm',
        'total_sessions': 35,
        'fee': 6000000,
        'min_entry_score': None
    },
]

courses_dict = {}
for course_data in courses_data:
    course, created = Course.objects.get_or_create(
        name=course_data['name'],
        defaults=course_data
    )
    courses_dict[course_data['name']] = course
    if created:
        print(f"  [OK] Created course: {course.name}")
    else:
        print(f"  [SKIP] Course already exists: {course.name}")

# ============================================================
# 7. TẠO CLASSES
# ============================================================
print("\n[7/8] Creating Classes...")
today = date.today()
classes_data = [
    {
        'name': 'IELTS Foundation - Lớp 1',
        'course': courses_dict['IELTS Foundation'],
        'start_date': today + timedelta(days=7),
        'end_date': today + timedelta(days=100),
        'weekday': [2, 4, 6],  # T2, T4, T6
        'time_slot': '18:30-20:30',
        'limit_slot': 20,
        'status': 'planned',
        'is_public': True,
        'campus': campuses_dict['Cơ sở Quận 1'],
        'teacher': Teacher.objects.filter(user_account__username='gv.nguyena').first(),
    },
]

for class_data in classes_data:
    class_obj, created = Class.objects.get_or_create(
        name=class_data['name'],
        defaults=class_data
    )
    if created:
        print(f"  [OK] Created class: {class_obj.name}")
    else:
        print(f"  [SKIP] Class already exists: {class_obj.name}")

# ============================================================
# 8. HOÀN TẤT
# ============================================================
print("\n[8/8] Completed!")
print("\n" + "=" * 60)
print("LOGIN CREDENTIALS:")
print("=" * 60)
print("\nAdmin:")
print("  - admin.ly / admin")
print("\nManager:")
print("  - ql.hoangc / manager")
print("\nTeachers:")
print("  - gv.nguyena / teacher")
print("  - gv.tranb / teacher")
print("\nStudents:")
print("  - hv.minhd / student")
print("  - hv.linh e / student")
print("\n" + "=" * 60)
print("SETUP COMPLETED!")
print("=" * 60)

