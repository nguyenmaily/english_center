#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple script to setup all test data
Run: python setup_data_simple.py
"""
import os
import django
import sys
import uuid

# Fix encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'english_center.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from authentication.models import Role, Permission, RolePermission
from users.models import Student, Teacher, Manager
from campus.models import Campus
from courses.models import Course

User = get_user_model()

print("=" * 60)
print("SETUP ALL TEST DATA")
print("=" * 60)

try:
    with transaction.atomic():
        # 1. Create Roles
        print("\n[1/6] Creating Roles...")
        roles = {}
        for name in ['student', 'teacher', 'manager', 'admin']:
            role, _ = Role.objects.get_or_create(name=name, defaults={'description': f'{name.title()} user'})
            roles[name] = role
            print(f"  OK: {name}")
        
        # 2. Create Permissions
        print("\n[2/6] Creating Permissions...")
        perms = {}
        perm_names = [
            'view_profile', 'edit_profile', 'view_all_users', 'edit_all_users',
            'view_courses', 'manage_courses', 'view_classes', 'manage_classes',
            'manage_finance', 'generate_reports', 'manage_roles'
        ]
        for name in perm_names:
            perm, _ = Permission.objects.get_or_create(name=name, defaults={'description': f'Can {name.replace("_", " ")}'})
            perms[name] = perm
            print(f"  OK: {name}")
        
        # 3. Assign Permissions
        print("\n[3/6] Assigning Permissions...")
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM role_permissions')
        
        role_perms_map = {
            'student': ['view_profile', 'edit_profile', 'view_courses', 'view_classes'],
            'teacher': ['view_profile', 'edit_profile', 'view_courses', 'view_classes', 'manage_classes', 'manage_courses'],
            'manager': ['view_profile', 'edit_profile', 'view_all_users', 'view_courses', 'view_classes', 'manage_classes', 'manage_courses', 'generate_reports'],
            'admin': list(perms.keys())
        }
        
        for role_name, perm_names_list in role_perms_map.items():
            role = roles[role_name]
            for perm_name in perm_names_list:
                perm = perms[perm_name]
                with connection.cursor() as cursor:
                    cursor.execute(
                        'INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s) ON CONFLICT (role_id, permission_id) DO NOTHING',
                        [str(role.id), str(perm.id)]
                    )
            print(f"  OK: {role_name} - {len(perm_names_list)} permissions")
        
        # 4. Create Campuses
        print("\n[4/6] Creating Campuses...")
        from django.db import connection
        with connection.cursor() as cursor:
            # Check if exists
            cursor.execute("SELECT id FROM campuses WHERE name = %s", ['Co so Quan 1'])
            row = cursor.fetchone()
            if row:
                campus1_id = row[0]
            else:
                campus1_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO campuses (id, name, address, hotline, email, status, facilities) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    [campus1_id, 'Co so Quan 1', '123 Nguyen Hue, Quan 1', '0281234567', 'q1@englishcenter.com', 'active', '[]']
                )
            
            cursor.execute("SELECT id FROM campuses WHERE name = %s", ['Co so Quan 3'])
            row = cursor.fetchone()
            if row:
                campus2_id = row[0]
            else:
                campus2_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO campuses (id, name, address, hotline, email, status, facilities) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    [campus2_id, 'Co so Quan 3', '456 Le Van Sy, Quan 3', '0282345678', 'q3@englishcenter.com', 'active', '[]']
                )
        
        print("  OK: Campuses created")
        
        # 5. Create Users
        print("\n[5/6] Creating Users...")
        
        # Admin
        admin, _ = User.objects.get_or_create(
            username='admin.ly',
            defaults={'email': 'admin@englishcenter.com', 'fullname': 'Administrator', 'roleid': roles['admin'], 'status': 'active'}
        )
        admin.set_password('admin')
        admin.save()
        print("  OK: admin.ly / admin")
        
        # Manager
        manager, _ = User.objects.get_or_create(
            username='ql.hoangc',
            defaults={'email': 'manager@englishcenter.com', 'fullname': 'Hoang C', 'roleid': roles['manager'], 'status': 'active'}
        )
        manager.set_password('manager')
        manager.save()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM campuses WHERE name = %s", ['Co so Quan 1'])
            campus1_id = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM managers WHERE user_account_id = %s", [str(manager.id)])
            if not cursor.fetchone():
                cursor.execute("INSERT INTO managers (id, user_account_id, campus_id) VALUES (%s, %s, %s)", 
                              [str(uuid.uuid4()), str(manager.id), campus1_id])
        print("  OK: ql.hoangc / manager")
        
        # Teachers
        teacher1, _ = User.objects.get_or_create(
            username='gv.nguyena',
            defaults={'email': 'gv.nguyena@englishcenter.com', 'fullname': 'Nguyen A', 'roleid': roles['teacher'], 'status': 'active'}
        )
        teacher1.set_password('teacher')
        teacher1.save()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM campuses WHERE name = %s", ['Co so Quan 1'])
            campus1_id = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM teachers WHERE user_account_id = %s", [str(teacher1.id)])
            if not cursor.fetchone():
                cursor.execute("INSERT INTO teachers (id, user_account_id, level, specialization, campus_id) VALUES (%s, %s, %s, %s, %s)",
                              [str(uuid.uuid4()), str(teacher1.id), 'Senior', 'IELTS Speaking', campus1_id])
        print("  OK: gv.nguyena / teacher")
        
        teacher2, _ = User.objects.get_or_create(
            username='gv.tranb',
            defaults={'email': 'gv.tranb@englishcenter.com', 'fullname': 'Tran B', 'roleid': roles['teacher'], 'status': 'active'}
        )
        teacher2.set_password('teacher')
        teacher2.save()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM campuses WHERE name = %s", ['Co so Quan 1'])
            campus1_id = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM teachers WHERE user_account_id = %s", [str(teacher2.id)])
            if not cursor.fetchone():
                cursor.execute("INSERT INTO teachers (id, user_account_id, level, specialization, campus_id) VALUES (%s, %s, %s, %s, %s)",
                              [str(uuid.uuid4()), str(teacher2.id), 'Expert', 'TOEIC', campus1_id])
        print("  OK: gv.tranb / teacher")
        
        # Students
        student1, _ = User.objects.get_or_create(
            username='hv.minhd',
            defaults={'email': 'hv.minhd@englishcenter.com', 'fullname': 'Minh D', 'roleid': roles['student'], 'status': 'active'}
        )
        student1.set_password('student')
        student1.save()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM students WHERE user_account_id = %s", [str(student1.id)])
            if not cursor.fetchone():
                cursor.execute("INSERT INTO students (id, user_account_id, target_score, commitment_status) VALUES (%s, %s, %s, %s)",
                              [str(uuid.uuid4()), str(student1.id), '7.0', 'committed'])
        print("  OK: hv.minhd / student")
        
        student2, _ = User.objects.get_or_create(
            username='hv.linh e',
            defaults={'email': 'hv.linh e@englishcenter.com', 'fullname': 'Linh E', 'roleid': roles['student'], 'status': 'active'}
        )
        student2.set_password('student')
        student2.save()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM students WHERE user_account_id = %s", [str(student2.id)])
            if not cursor.fetchone():
                cursor.execute("INSERT INTO students (id, user_account_id, target_score, commitment_status) VALUES (%s, %s, %s, %s)",
                              [str(uuid.uuid4()), str(student2.id), '6.5', 'committed'])
        print("  OK: hv.linh e / student")
        
        # 6. Create Courses
        print("\n[6/6] Creating Courses...")
        with connection.cursor() as cursor:
            courses_data = [
                ('IELTS Foundation', 'Beginner', 'IELTS basic course', 30, 5000000, None),
                ('IELTS Intermediate', 'Intermediate', 'IELTS intermediate course', 40, 7000000, 5.0),
                ('TOEIC 500+', 'Intermediate', 'TOEIC course from 500 points', 35, 6000000, None),
            ]
            for name, level, desc, sessions, fee, min_score in courses_data:
                cursor.execute("SELECT id FROM courses WHERE name = %s", [name])
                row = cursor.fetchone()
                if not row:
                    course_id = str(uuid.uuid4())
                    cursor.execute(
                        "INSERT INTO courses (id, name, level, description, total_sessions, fee, min_entry_score) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        [course_id, name, level, desc, sessions, fee, min_score]
                    )
        print("  OK: Courses created")
        
        print("\n" + "=" * 60)
        print("SETUP COMPLETED!")
        print("=" * 60)
        print("\nLogin Credentials:")
        print("  Admin: admin.ly / admin")
        print("  Manager: ql.hoangc / manager")
        print("  Teacher: gv.nguyena / teacher")
        print("  Teacher: gv.tranb / teacher")
        print("  Student: hv.minhd / student")
        print("  Student: hv.linh e / student")
        print("=" * 60)
        
except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

