#!/usr/bin/env python
"""
Script để set password cho các user test sau khi chạy test_data_insert_teacher_student.sql
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'english_center.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 50)
print("SETTING PASSWORDS FOR TEST USERS")
print("=" * 50)

# Set password cho teachers
print("\n[TEACHERS]")
for username in ['teacher1', 'teacher2', 'teacher3']:
    try:
        user = User.objects.get(username=username)
        user.set_password('teacher123')
        user.save()
        print(f"✓ Đã set password cho {username} (password: teacher123)")
    except User.DoesNotExist:
        print(f"✗ Không tìm thấy {username}")

# Set password cho students
print("\n[STUDENTS]")
for username in ['student1', 'student2', 'student3', 'student4']:
    try:
        user = User.objects.get(username=username)
        user.set_password('student123')
        user.save()
        print(f"✓ Đã set password cho {username} (password: student123)")
    except User.DoesNotExist:
        print(f"✗ Không tìm thấy {username}")

print("\n" + "=" * 50)
print("HOÀN TẤT!")
print("=" * 50)
print("\nThông tin đăng nhập:")
print("\nTEACHERS:")
print("  - teacher1 / teacher123")
print("  - teacher2 / teacher123")
print("  - teacher3 / teacher123")
print("\nSTUDENTS:")
print("  - student1 / student123")
print("  - student2 / student123")
print("  - student3 / student123")
print("  - student4 / student123")
print("=" * 50)
