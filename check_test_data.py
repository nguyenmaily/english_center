"""
Script để kiểm tra tài khoản nào có dữ liệu để test các giao diện
"""
import os
import sys
import django
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'english_center.settings')
django.setup()

from django.db import connection
from users.models import Manager, Student, Teacher
from classes.models import Class
from requests.models import ReserveRequest, LeaveRequest
from class_sessions.models import Session
from enrollment.models import Enrollment

def check_reserve_requests():
    """Kiểm tra tài khoản nào có reserve requests"""
    print("\n" + "="*60)
    print("KIEM TRA YEU CAU BAO LUU (RESERVE REQUESTS)")
    print("="*60)
    
    with connection.cursor() as cursor:
        # Lấy tất cả reserve requests với thông tin student và class
        cursor.execute("""
            SELECT 
                rr.id,
                rr.student_id,
                rr.class_id,
                rr.status,
                ua.username,
                ua.full_name,
                c.name as class_name,
                c.campus_id
            FROM reserve_requests rr
            LEFT JOIN students s ON s.id = rr.student_id
            LEFT JOIN user_accounts ua ON ua.id = s.user_account_id
            LEFT JOIN classes c ON c.id = rr.class_id
            ORDER BY rr.created_at DESC
            LIMIT 20
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("[!] Khong co reserve requests nao trong database")
            return [], []
        
        print(f"[+] Tim thay {len(results)} reserve requests:\n")
        
        student_accounts = set()
        manager_accounts = set()
        
        for row in results:
            req_id, student_id, class_id, status, username, fullname, class_name, campus_id = row
            student_accounts.add((username, fullname))
            
            # Tìm manager của campus này
            if campus_id:
                cursor.execute("""
                    SELECT ua.username, ua.full_name
                    FROM managers m
                    JOIN user_accounts ua ON ua.id = m.user_account_id
                    WHERE m.campus_id = %s
                    LIMIT 1
                """, [campus_id])
                manager = cursor.fetchone()
                if manager:
                    manager_accounts.add((manager[0], manager[1]))
            
            status_text = {
                'pending': '[PENDING] Dang cho',
                'approved': '[APPROVED] Da duyet',
                'rejected': '[REJECTED] Tu choi'
            }.get(status, status)
            
            print(f"  - {status_text} | Hoc vien: {fullname or username} | Lop: {class_name or 'N/A'}")
        
        print(f"\n[+] Tai khoan STUDENT co reserve requests:")
        for username, fullname in sorted(student_accounts):
            print(f"   - {username} ({fullname})")
        
        print(f"\n[+] Tai khoan MANAGER co the phe duyet:")
        for username, fullname in sorted(manager_accounts):
            print(f"   - {username} ({fullname})")
        
        return list(student_accounts), list(manager_accounts)

def check_classes():
    """Kiểm tra tài khoản nào có lớp học"""
    print("\n" + "="*60)
    print("KIEM TRA LOP HOC (CLASSES)")
    print("="*60)
    
    with connection.cursor() as cursor:
        # Lấy classes với thông tin teacher và manager
        cursor.execute("""
            SELECT 
                c.id,
                c.name,
                c.status,
                c.campus_id,
                t_ua.username as teacher_username,
                t_ua.full_name as teacher_name,
                m_ua.username as manager_username,
                m_ua.full_name as manager_name
            FROM classes c
            LEFT JOIN teachers t ON t.id = c.teacher_id
            LEFT JOIN user_accounts t_ua ON t_ua.id = t.user_account_id
            LEFT JOIN managers m ON m.id = c.manager_id
            LEFT JOIN user_accounts m_ua ON m_ua.id = m.user_account_id
            ORDER BY c.created_at DESC
            LIMIT 20
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("[!] Khong co lop hoc nao trong database")
            return [], []
        
        print(f"[+] Tim thay {len(results)} lop hoc:\n")
        
        teacher_accounts = set()
        manager_accounts = set()
        
        for row in results:
            class_id, class_name, status, campus_id, t_username, t_name, m_username, m_name = row
            
            if t_username:
                teacher_accounts.add((t_username, t_name))
            if m_username:
                manager_accounts.add((m_username, m_name))
            
            status_text = {
                'planned': '[PLANNED] Da len ke hoach',
                'ongoing': '[ONGOING] Dang dien ra',
                'completed': '[COMPLETED] Hoan thanh',
                'cancelled': '[CANCELLED] Da huy'
            }.get(status, status)
            
            print(f"  - {status_text} | {class_name}")
            if t_username:
                print(f"    Giao vien: {t_name or t_username}")
            if m_username:
                print(f"    Quan ly: {m_name or m_username}")
        
        print(f"\n[+] Tai khoan TEACHER co lop hoc:")
        for username, fullname in sorted(teacher_accounts):
            print(f"   - {username} ({fullname})")
        
        print(f"\n[+] Tai khoan MANAGER co lop hoc:")
        for username, fullname in sorted(manager_accounts):
            print(f"   - {username} ({fullname})")
        
        return list(teacher_accounts), list(manager_accounts)

def check_schedule():
    """Kiểm tra tài khoản nào có thời khóa biểu (sessions)"""
    print("\n" + "="*60)
    print("KIEM TRA THOI KHOA BIEU (SCHEDULE/SESSIONS)")
    print("="*60)
    
    with connection.cursor() as cursor:
        # Lấy sessions với thông tin class và teacher
        cursor.execute("""
            SELECT 
                s.id,
                s.study_date,
                s.start_time,
                s.end_time,
                c.name as class_name,
                t_ua.username as teacher_username,
                t_ua.full_name as teacher_name
            FROM sessions s
            LEFT JOIN classes c ON c.id = s.class_id
            LEFT JOIN teachers t ON t.id = s.teacher_id
            LEFT JOIN user_accounts t_ua ON t_ua.id = t.user_account_id
            WHERE s.study_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY s.study_date DESC, s.start_time DESC
            LIMIT 20
        """)
        
        results = cursor.fetchall()
        
        if not results:
            print("[!] Khong co sessions nao trong database")
            return []
        
        print(f"[+] Tim thay {len(results)} sessions (30 ngay gan nhat):\n")
        
        teacher_accounts = set()
        class_names = set()
        
        for row in results:
            session_id, study_date, start_time, end_time, class_name, t_username, t_name = row
            
            if t_username:
                teacher_accounts.add((t_username, t_name))
            if class_name:
                class_names.add(class_name)
            
            print(f"  - {study_date} {start_time}-{end_time} | {class_name or 'N/A'}")
            if t_username:
                print(f"    Giáo viên: {t_name or t_username}")
        
        print(f"\n[+] Tai khoan TEACHER co lich day:")
        for username, fullname in sorted(teacher_accounts):
            print(f"   - {username} ({fullname})")
        
        # Kiểm tra students có enrollment trong các lớp này
        if class_names:
            cursor.execute("""
                SELECT DISTINCT
                    ua.username,
                    ua.full_name
                FROM enrollments e
                JOIN students s ON s.id = e.student_id
                JOIN user_accounts ua ON ua.id = s.user_account_id
                JOIN classes c ON c.id = e.class_id
                WHERE c.name = ANY(%s)
                LIMIT 10
            """, [list(class_names)])
            
            student_results = cursor.fetchall()
            if student_results:
                print(f"\n[+] Tai khoan STUDENT co thoi khoa bieu:")
                for username, fullname in student_results:
                    print(f"   - {username} ({fullname})")
        
        return list(teacher_accounts)

def main():
    print("\n" + "="*60)
    print("KIEM TRA TAI KHOAN CO DU LIEU DE TEST")
    print("="*60)
    
    # Kiểm tra reserve requests
    student_reserve, manager_reserve = check_reserve_requests()
    
    # Kiểm tra classes
    teacher_classes, manager_classes = check_classes()
    
    # Kiểm tra schedule
    teacher_schedule = check_schedule()
    
    # Tóm tắt
    print("\n" + "="*60)
    print("TOM TAT TAI KHOAN DE TEST")
    print("="*60)
    
    print("\n[+] De test BAO LUU:")
    if student_reserve:
        print(f"   - Dang nhap STUDENT: {student_reserve[0][0]} (password123)")
        print(f"     -> Vao trang 'Yeu cau bao luu' de tao yeu cau")
    if manager_reserve:
        print(f"   - Dang nhap MANAGER: {manager_reserve[0][0]} (password123)")
        print(f"     -> Vao trang 'Phe duyet bao luu' de phe duyet")
    
    print("\n[+] De test LOP HOC:")
    if teacher_classes:
        print(f"   - Dang nhap TEACHER: {teacher_classes[0][0]} (password123)")
        print(f"     -> Vao trang 'Lop da dang ky' hoac 'Lich day cua toi'")
    if manager_classes:
        print(f"   - Dang nhap MANAGER: {manager_classes[0][0]} (password123)")
        print(f"     -> Vao trang 'Quan ly lop hoc'")
    
    print("\n[+] De test THOI KHOA BIEU:")
    if teacher_schedule:
        print(f"   - Dang nhap TEACHER: {teacher_schedule[0][0]} (password123)")
        print(f"     -> Vao trang 'Lich day cua toi'")
    
    print("\n" + "="*60)
    print("LUU Y:")
    print("="*60)
    print("   - Tat ca tai khoan co mat khau: password123")
    print("   - Neu khong co du lieu, chay: python manage.py generate_sample_data")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()

