"""
Django management command để tạo dữ liệu mẫu cho hệ thống
Mỗi bảng sẽ có khoảng 20-30 records
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from datetime import datetime, timedelta
import uuid
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Tạo dữ liệu mẫu cho hệ thống (20-30 records mỗi bảng)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Xóa dữ liệu cũ trước khi tạo mới',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Đang xóa dữ liệu cũ...'))
            self.clear_data()
        
        self.stdout.write(self.style.SUCCESS('Bắt đầu tạo dữ liệu mẫu...'))
        
        # Tạo dữ liệu theo thứ tự phụ thuộc
        roles = self.create_roles()
        campuses = self.create_campuses()
        rooms = self.create_rooms(campuses)
        skills = self.create_skills()
        courses = self.create_courses(skills)
        users = self.create_users(roles)
        admins = [u for u in users if u['role'] == 'admin']
        managers = self.create_managers(users, campuses)
        teachers = self.create_teachers(users, campuses)
        students = self.create_students(users)
        classes = self.create_classes(courses, teachers, campuses, managers)
        enrollments = self.create_enrollments(students, classes, courses)
        sessions = self.create_sessions(classes, teachers, rooms)
        attendances = self.create_attendances(sessions, students)
        assignments = self.create_assignments(sessions)
        submissions = self.create_submissions(assignments, students)
        exam_blueprints = self.create_exam_blueprints()
        exam_instances = self.create_exam_instances(exam_blueprints, classes)
        exam_results = self.create_exam_results(exam_instances, students)
        student_certificates = self.create_student_certificates(students)
        leave_requests = self.create_leave_requests(students, classes)
        reserve_requests = self.create_reserve_requests(students, classes)
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Hoàn thành! Đã tạo dữ liệu mẫu:'))
        self.stdout.write(f'  - Roles: {len(roles)}')
        self.stdout.write(f'  - Campuses: {len(campuses)}')
        self.stdout.write(f'  - Rooms: {len(rooms)}')
        self.stdout.write(f'  - Skills: {len(skills)}')
        self.stdout.write(f'  - Courses: {len(courses)}')
        self.stdout.write(f'  - Users: {len(users)}')
        self.stdout.write(f'  - Managers: {len(managers)}')
        self.stdout.write(f'  - Teachers: {len(teachers)}')
        self.stdout.write(f'  - Students: {len(students)}')
        self.stdout.write(f'  - Classes: {len(classes)}')
        self.stdout.write(f'  - Enrollments: {len(enrollments)}')
        self.stdout.write(f'  - Sessions: {len(sessions)}')
        self.stdout.write(f'  - Attendances: {len(attendances)}')
        self.stdout.write(f'  - Assignments: {len(assignments)}')
        self.stdout.write(f'  - Submissions: {len(submissions)}')
        self.stdout.write(f'  - Exam Blueprints: {len(exam_blueprints)}')
        self.stdout.write(f'  - Exam Instances: {len(exam_instances)}')
        self.stdout.write(f'  - Exam Results: {len(exam_results)}')
        self.stdout.write(f'  - Student Certificates: {len(student_certificates)}')
        self.stdout.write(f'  - Leave Requests: {len(leave_requests)}')
        self.stdout.write(f'  - Reserve Requests: {len(reserve_requests)}')

    def clear_data(self):
        """Xóa dữ liệu cũ (giữ lại superuser)"""
        with connection.cursor() as cursor:
            tables = [
                'reserve_requests', 'leave_requests', 'student_certificates',
                'exam_answers', 'exam_results', 'exam_instance_questions',
                'exam_instances', 'exam_rules', 'exam_blueprints',
                'student_answers', 'submissions', 'answer_keys', 'assignments',
                'attendances', 'sessions', 'enrollments', 'classes',
                'students', 'teachers', 'managers', 'user_accounts',
                'courses', 'skills', 'campuses', 'role_permissions', 'permissions', 'roles'
            ]
            for table in tables:
                try:
                    cursor.execute(f'DELETE FROM {table}')
                    self.stdout.write(f'  Đã xóa {table}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Không thể xóa {table}: {e}'))

    def create_roles(self):
        """Tạo roles và permissions theo setup_auth_data"""
        from authentication.models import Role, Permission, RolePermission
        
        # Create roles
        roles_data = [
            {'name': 'student', 'description': 'Student user'},
            {'name': 'teacher', 'description': 'Teacher user'},
            {'name': 'manager', 'description': 'Manager user'},
            {'name': 'admin', 'description': 'Administrator user'},
        ]
        
        roles = []
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )
            if created:
                self.stdout.write(f'  Created role: {role.name}')
            else:
                self.stdout.write(f'  Role already exists: {role.name}')
            roles.append({'id': role.id, 'name': role.name})
        
        # Create permissions
        permissions_data = [
            # Profile permissions
            {'name': 'view_profile', 'description': 'Can view own profile'},
            {'name': 'edit_profile', 'description': 'Can edit own profile'},
           
            # User management permissions
            {'name': 'view_all_users', 'description': 'Can view all users'},
            {'name': 'edit_all_users', 'description': 'Can edit all users'},
            {'name': 'view_users', 'description': 'Can view users list'},
            {'name': 'manage_users', 'description': 'Can create, update, delete users'},
            {'name': 'view_teachers', 'description': 'Can view teachers list'},
            {'name': 'manage_teachers', 'description': 'Can manage teachers'},
            {'name': 'view_managers', 'description': 'Can view managers list'},
            {'name': 'view_students', 'description': 'Can view students list'},
           
            # Campus permissions
            {'name': 'view_campus', 'description': 'Can view campuses'},
            {'name': 'manage_campus', 'description': 'Can create, update, delete campuses'},
            {'name': 'view_rooms', 'description': 'Can view rooms'},
            {'name': 'manage_rooms', 'description': 'Can manage rooms'},
            {'name': 'view_equipments', 'description': 'Can view equipments'},
            {'name': 'manage_equipments', 'description': 'Can manage equipments'},
           
            # Course & Class permissions
            {'name': 'view_courses', 'description': 'Can view courses'},
            {'name': 'manage_courses', 'description': 'Can manage courses'},
            {'name': 'view_classes', 'description': 'Can view classes'},
            {'name': 'manage_classes', 'description': 'Can manage classes'},
           
            # Assignment permissions
            {'name': 'view_assignments', 'description': 'Can view assignments'},
            {'name': 'manage_assignments', 'description': 'Can manage assignments'},
            {'name': 'view_submissions', 'description': 'Can view submissions'},
            
            # Proficiency profile permissions
            {'name': 'manage_proficiency_profile', 'description': 'Can manage own English proficiency profile'},
            {'name': 'approve_certificates', 'description': 'Can approve/reject student certificates'},
            
            # Enrollment permissions
            {'name': 'view_enrollments', 'description': 'Can view own enrollments'},
            {'name': 'manage_enrollments', 'description': 'Can create enrollments (register for classes)'},
            
            # System permissions
            {'name': 'manage_finance', 'description': 'Can manage finance'},
            {'name': 'generate_reports', 'description': 'Can generate reports'},
            {'name': 'manage_roles', 'description': 'Can manage roles and permissions'},
        ]
        
        permissions = {}
        for perm_data in permissions_data:
            permission, created = Permission.objects.get_or_create(
                name=perm_data['name'],
                defaults={'description': perm_data['description']}
            )
            if created:
                self.stdout.write(f'  Created permission: {permission.name}')
            permissions[permission.name] = permission.id
        
        # Assign permissions to roles
        role_permissions_map = {
            'student': [
                'view_profile', 'edit_profile', 'view_courses', 'view_classes',
                'view_campus', 'view_assignments', 'view_submissions',
                'manage_proficiency_profile', 'view_enrollments', 'manage_enrollments',
            ],
            'teacher': [
                'view_profile', 'edit_profile', 'view_courses', 'view_classes',
                'manage_classes', 'view_assignments', 'manage_assignments', 'view_submissions',
            ],
            'manager': [
                'view_profile', 'edit_profile', 'view_all_users', 'edit_all_users',
                'view_users', 'manage_users', 'view_teachers', 'manage_teachers',
                'view_managers', 'view_students', 'view_campus', 'manage_campus',
                'view_rooms', 'manage_rooms', 'view_equipments', 'manage_equipments',
                'view_courses', 'manage_courses', 'view_classes', 'manage_classes',
                'view_assignments', 'manage_assignments', 'view_submissions', 'generate_reports',
            ],
            'admin': list(permissions.keys()),  # Admin có tất cả permissions
        }
        
        for role_name, perm_names in role_permissions_map.items():
            try:
                role = Role.objects.get(name=role_name)
                # Remove existing permissions for this role
                RolePermission.objects.filter(role=role).delete()
                
                for perm_name in perm_names:
                    if perm_name in permissions:
                        permission = Permission.objects.get(name=perm_name)
                        RolePermission.objects.create(role=role, permission=permission)
                self.stdout.write(f'  Assigned {len(perm_names)} permissions to role {role_name}')
            except Role.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Role "{role_name}" not found'))
        
        return roles

    def create_campuses(self):
        """Tạo 25 campuses"""
        campuses = []
        addresses = [
            '123 Nguyễn Huệ, Q1, TP.HCM', '456 Lê Lợi, Q3, TP.HCM',
            '789 Điện Biên Phủ, Q.Bình Thạnh, TP.HCM', '321 Võ Văn Tần, Q3, TP.HCM',
            '654 Nguyễn Thị Minh Khai, Q1, TP.HCM', '987 Trần Hưng Đạo, Q5, TP.HCM',
            '147 Lý Tự Trọng, Q1, TP.HCM', '258 Pasteur, Q3, TP.HCM',
            '369 Đinh Tiên Hoàng, Q.Bình Thạnh, TP.HCM', '741 Nguyễn Văn Cừ, Q5, TP.HCM',
            '852 Cách Mạng Tháng 8, Q10, TP.HCM', '963 Hoàng Văn Thụ, Q.Tân Bình, TP.HCM',
            '159 Phạm Văn Đồng, Q.Thủ Đức, TP.HCM', '357 Nguyễn Oanh, Q.Gò Vấp, TP.HCM',
            '468 Lê Đức Thọ, Q.12, TP.HCM', '579 Quang Trung, Q.Gò Vấp, TP.HCM',
            '680 Tân Sơn Nhì, Q.Tân Phú, TP.HCM', '791 Hậu Giang, Q6, TP.HCM',
            '802 An Dương Vương, Q5, TP.HCM', '913 Nguyễn Trãi, Q5, TP.HCM',
            '124 Lạc Long Quân, Q11, TP.HCM', '235 Tô Hiến Thành, Q10, TP.HCM',
            '346 Lý Thường Kiệt, Q.Tân Bình, TP.HCM', '457 Hoàng Hoa Thám, Q.Tân Bình, TP.HCM',
            '568 Cộng Hòa, Q.Tân Bình, TP.HCM'
        ]
        with connection.cursor() as cursor:
            for i, address in enumerate(addresses):
                campus_id = uuid.uuid4()
                name = f'Cơ sở {i+1}'
                hotline = f'0{random.randint(200000000, 999999999)}'
                email = f'campus{i+1}@example.com'
                cursor.execute("""
                    INSERT INTO campuses (id, name, address, hotline, email, status, description, facilities, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [campus_id, name, address, hotline, email, 'active', 
                      f'Mô tả cho {name}', '[]', timezone.now(), timezone.now()])
                campuses.append({'id': campus_id, 'name': name})
        return campuses

    def create_rooms(self, campuses):
        """Tạo 30 rooms"""
        rooms = []
        room_names = ['Phòng 101', 'Phòng 102', 'Phòng 201', 'Phòng 202', 'Phòng 301', 
                      'Phòng 302', 'Phòng Lab 1', 'Phòng Lab 2', 'Phòng Hội thảo', 'Phòng Đa năng']
        with connection.cursor() as cursor:
            for i in range(30):
                room_id = uuid.uuid4()
                campus = random.choice(campuses) if campuses else None
                room_name = f"{random.choice(room_names)} - {i+1}"
                cursor.execute("""
                    INSERT INTO rooms (id, name, is_under_repair, campus_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, [room_id, room_name, random.choice([True, False]), 
                      campus['id'] if campus else None, timezone.now(), timezone.now()])
                rooms.append({'id': room_id, 'campus_id': campus['id'] if campus else None})
        return rooms

    def create_skills(self):
        """Tạo skills"""
        skills_data = [
            ('Listening-Reading', 'Kỹ năng Nghe-Đọc'),
            ('Speaking-Writing', 'Kỹ năng Nói-Viết'),
        ]
        skills = []
        with connection.cursor() as cursor:
            for name, desc in skills_data:
                skill_id = uuid.uuid4()
                cursor.execute("""
                    INSERT INTO skills (id, name, description, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, [skill_id, name, desc, timezone.now(), timezone.now()])
                skills.append({'id': skill_id, 'name': name})
        return skills

    def create_courses(self, skills):
        """Tạo 25 courses"""
        courses = []
        course_base_names = [
            'TOEIC Foundation', 'TOEIC Intermediate', 'TOEIC Advanced',
            'IELTS Foundation', 'IELTS Intermediate', 'IELTS Advanced',
            'TOEFL Basic', 'TOEFL Intermediate', 'TOEFL Advanced',
            'Business English Basic', 'Business English Intermediate', 'Business English Advanced',
            'Conversational English Level 1', 'Conversational English Level 2', 'Conversational English Level 3',
            'Grammar Basics', 'Grammar Intermediate', 'Grammar Advanced',
            'Pronunciation Course', 'Writing Skills', 'Reading Comprehension',
            'Listening Skills', 'Speaking Practice', 'Vocabulary Building',
            'English for Kids', 'English for Teens'
        ]
        levels = ['Foundation', 'Intermediate', 'Advanced', 'Basic', 'Level 1', 'Level 2', 'Level 3']
        with connection.cursor() as cursor:
            for i, base_name in enumerate(course_base_names):
                # Tạo tên unique bằng cách thêm timestamp hoặc số
                name = f"{base_name} - {timezone.now().strftime('%Y%m%d%H%M%S')}-{i}"
                course_id = uuid.uuid4()
                level = random.choice(levels)
                skill_id = random.choice(skills)['id']
                fee = Decimal(random.randint(2000000, 10000000))
                total_sessions = random.randint(20, 40)
                min_entry = random.randint(200, 500) if 'TOEIC' in base_name or 'IELTS' in base_name else None
                min_exit = (min_entry + random.randint(50, 150)) if min_entry else None
                cursor.execute("""
                    INSERT INTO courses (id, name, level, description, total_sessions, min_entry_score, min_exit_score, fee, skill_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO NOTHING
                """, [course_id, name, level, f'Mô tả khóa học {name}', total_sessions, 
                      min_entry, min_exit, fee, skill_id, timezone.now(), timezone.now()])
                # Kiểm tra xem có insert thành công không
                cursor.execute("SELECT id FROM courses WHERE name = %s", [name])
                result = cursor.fetchone()
                if result:
                    courses.append({'id': result[0], 'name': name})
        return courses

    def create_users(self, roles):
        """Tạo users với tên thật (admin, manager, teacher, student)"""
        users = []
        role_map = {r['name']: r['id'] for r in roles}
        
        # Danh sách họ Việt Nam phổ biến
        ho_list = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Vũ', 'Đặng', 'Bùi', 'Đỗ', 'Hồ', 
                   'Võ', 'Đinh', 'Lý', 'Phan', 'Ngô', 'Dương', 'Đào', 'Tạ', 'Lương', 'Trịnh']
        
        # Danh sách tên đệm và tên phổ biến
        ten_dem_nam = ['Văn', 'Đức', 'Minh', 'Thanh', 'Quang', 'Hữu', 'Công', 'Tuấn', 'Đình', 'Xuân']
        ten_nam = ['Anh', 'Dũng', 'Hùng', 'Mạnh', 'Tuấn', 'Nam', 'Long', 'Khang', 'Bảo', 'Đức',
                   'Huy', 'Khoa', 'Lâm', 'Phong', 'Quân', 'Sơn', 'Thành', 'Trung', 'Việt', 'Vinh']
        
        ten_dem_nu = ['Thị', 'Ngọc', 'Minh', 'Thanh', 'Thu', 'Hồng', 'Lan', 'Linh', 'Phương', 'Hương']
        ten_nu = ['Anh', 'Linh', 'Lan', 'Hương', 'Phương', 'Hoa', 'Mai', 'Nga', 'Thảo', 'Trang',
                  'Hạnh', 'Hiền', 'Hồng', 'Loan', 'Ly', 'My', 'Nhi', 'Oanh', 'Quỳnh', 'Uyên']
        
        # Tạo password hash một lần và reuse (tối ưu hiệu suất)
        self.stdout.write('  Đang tạo password hash...')
        default_password_hash = make_password('password123')
        admin_password_hash = make_password('admin123')
        
        with connection.cursor() as cursor:
            # 1 admin
            admin_id = uuid.uuid4()
            username = 'admin'
            admin_fullname = 'Nguyễn Văn Quản'
            # Kiểm tra xem đã tồn tại chưa
            cursor.execute("SELECT id FROM user_accounts WHERE username = %s", [username])
            existing = cursor.fetchone()
            if existing:
                users.append({'id': existing[0], 'role': 'admin', 'username': username})
            else:
                cursor.execute("""
                    INSERT INTO user_accounts (id, username, password_hash, email, status, role_id, full_name, phone, sex, dob, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [admin_id, username, admin_password_hash, 'admin@englishcenter.com', 'active', 
                      role_map['admin'], admin_fullname, '0123456789', 'male', '1990-01-01', timezone.now(), timezone.now()])
                users.append({'id': admin_id, 'role': 'admin', 'username': username})
            
            # Tạo 30 managers (đủ để mỗi campus có ít nhất 1 manager, một số campus có nhiều hơn)
            for i in range(30):
                user_id = uuid.uuid4()
                sex = random.choice(['male', 'female'])
                ho = random.choice(ho_list)
                if sex == 'male':
                    ten_dem = random.choice(ten_dem_nam)
                    ten = random.choice(ten_nam)
                else:
                    ten_dem = random.choice(ten_dem_nu)
                    ten = random.choice(ten_nu)
                fullname = f"{ho} {ten_dem} {ten}"
                username = f'ql{str(i+1).zfill(3)}'  # ql001, ql002, ...
                email = f'ql{str(i+1).zfill(3)}@englishcenter.com'
                # Kiểm tra xem đã tồn tại chưa
                cursor.execute("SELECT id FROM user_accounts WHERE username = %s", [username])
                existing = cursor.fetchone()
                if existing:
                    users.append({'id': existing[0], 'role': 'manager', 'username': username})
                else:
                    cursor.execute("""
                        INSERT INTO user_accounts (id, username, password_hash, email, status, role_id, full_name, phone, sex, dob, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [user_id, username, default_password_hash, email, 'active',
                          role_map['manager'], fullname, f'0{random.randint(900000000, 999999999)}',
                          sex, f'198{random.randint(0,9)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                          timezone.now(), timezone.now()])
                    users.append({'id': user_id, 'role': 'manager', 'username': username})
            
            # 10 teachers
            for i in range(10):
                user_id = uuid.uuid4()
                sex = random.choice(['male', 'female'])
                ho = random.choice(ho_list)
                if sex == 'male':
                    ten_dem = random.choice(ten_dem_nam)
                    ten = random.choice(ten_nam)
                else:
                    ten_dem = random.choice(ten_dem_nu)
                    ten = random.choice(ten_nu)
                fullname = f"{ho} {ten_dem} {ten}"
                username = f'gv{str(i+1).zfill(3)}'  # gv001, gv002, ...
                email = f'gv{str(i+1).zfill(3)}@englishcenter.com'
                # Kiểm tra xem đã tồn tại chưa
                cursor.execute("SELECT id FROM user_accounts WHERE username = %s", [username])
                existing = cursor.fetchone()
                if existing:
                    users.append({'id': existing[0], 'role': 'teacher', 'username': username})
                else:
                    cursor.execute("""
                        INSERT INTO user_accounts (id, username, password_hash, email, status, role_id, full_name, phone, sex, dob, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [user_id, username, default_password_hash, email, 'active',
                          role_map['teacher'], fullname, f'0{random.randint(900000000, 999999999)}',
                          sex, f'199{random.randint(0,9)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                          timezone.now(), timezone.now()])
                    users.append({'id': user_id, 'role': 'teacher', 'username': username})
            
            # 14 students
            for i in range(14):
                user_id = uuid.uuid4()
                sex = random.choice(['male', 'female'])
                ho = random.choice(ho_list)
                if sex == 'male':
                    ten_dem = random.choice(ten_dem_nam)
                    ten = random.choice(ten_nam)
                else:
                    ten_dem = random.choice(ten_dem_nu)
                    ten = random.choice(ten_nu)
                fullname = f"{ho} {ten_dem} {ten}"
                username = f'hv{str(i+1).zfill(3)}'  # hv001, hv002, ...
                email = f'hv{str(i+1).zfill(3)}@englishcenter.com'
                # Kiểm tra xem đã tồn tại chưa
                cursor.execute("SELECT id FROM user_accounts WHERE username = %s", [username])
                existing = cursor.fetchone()
                if existing:
                    users.append({'id': existing[0], 'role': 'student', 'username': username})
                else:
                    cursor.execute("""
                        INSERT INTO user_accounts (id, username, password_hash, email, status, role_id, full_name, phone, sex, dob, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [user_id, username, default_password_hash, email, 'active',
                          role_map['student'], fullname, f'0{random.randint(900000000, 999999999)}',
                          sex, f'200{random.randint(0,5)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                          timezone.now(), timezone.now()])
                    users.append({'id': user_id, 'role': 'student', 'username': username})
        
        self.stdout.write(f'  Đã tạo {len(users)} users')
        return users
        
        return users

    def create_managers(self, users, campuses):
        """Tạo managers và gán vào các campuses"""
        managers = []
        manager_users = [u for u in users if u['role'] == 'manager']
        
        if not campuses:
            self.stdout.write(self.style.WARNING('  Không có campuses để gán managers'))
            return managers
        
        with connection.cursor() as cursor:
            # Đảm bảo mỗi campus có ít nhất 1 manager
            campus_index = 0
            for i, user in enumerate(manager_users):
                manager_id = uuid.uuid4()
                
                # Phân bổ managers cho campuses:
                # - Các managers đầu tiên: mỗi campus có ít nhất 1 manager
                # - Các managers còn lại: phân bổ ngẫu nhiên (một số campus có nhiều managers)
                if i < len(campuses):
                    # Mỗi campus có ít nhất 1 manager
                    campus_id = campuses[i]['id']
                else:
                    # Các managers còn lại được phân bổ ngẫu nhiên
                    campus_id = random.choice(campuses)['id']
                
                cursor.execute("""
                    INSERT INTO managers (id, user_account_id, campus_id, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, [manager_id, user['id'], campus_id, timezone.now(), timezone.now()])
                managers.append({'id': manager_id, 'user_id': user['id'], 'campus_id': campus_id})
            
            self.stdout.write(f'  Đã tạo {len(managers)} managers cho {len(campuses)} campuses')
            # Hiển thị thống kê
            cursor.execute("""
                SELECT campus_id, COUNT(*) as manager_count 
                FROM managers 
                WHERE campus_id IS NOT NULL 
                GROUP BY campus_id 
                ORDER BY manager_count DESC
            """)
            stats = cursor.fetchall()
            if stats:
                self.stdout.write(f'  - Campus có nhiều managers nhất: {stats[0][1]} managers')
                self.stdout.write(f'  - Campus có ít managers nhất: {stats[-1][1]} managers')
        
        return managers

    def create_teachers(self, users, campuses):
        """Tạo teachers"""
        teachers = []
        teacher_users = [u for u in users if u['role'] == 'teacher']
        levels = ['Junior', 'Senior', 'Expert']
        specializations = ['TOEIC', 'IELTS', 'TOEFL', 'Business English', 'Conversational English']
        with connection.cursor() as cursor:
            for user in teacher_users:
                teacher_id = uuid.uuid4()
                campus_id = random.choice(campuses)['id'] if campuses else None
                level = random.choice(levels)
                specialization = random.choice(specializations)
                cursor.execute("""
                    INSERT INTO teachers (id, user_account_id, campus_id, level, specialization, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [teacher_id, user['id'], campus_id, level, specialization, timezone.now(), timezone.now()])
                teachers.append({'id': teacher_id, 'user_id': user['id'], 'campus_id': campus_id})
        return teachers

    def create_students(self, users):
        """Tạo students"""
        students = []
        student_users = [u for u in users if u['role'] == 'student']
        commitment_statuses = ['not_committed', 'committed', 'canceled']
        with connection.cursor() as cursor:
            for user in student_users:
                student_id = uuid.uuid4()
                commitment_status = random.choice(commitment_statuses)
                cursor.execute("""
                    INSERT INTO students (id, user_account_id, commitment_status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, [student_id, user['id'], commitment_status, timezone.now(), timezone.now()])
                students.append({'id': student_id, 'user_id': user['id']})
        return students

    def create_classes(self, courses, teachers, campuses, managers):
        """Tạo 25 classes"""
        classes = []
        # Database enum values: planned, ongoing, finished, canceled
        statuses = ['planned', 'ongoing', 'finished', 'canceled']
        weekdays_options = [
            [1, 3, 5], [2, 4, 6], [1, 3], [2, 4], [3, 5], [1, 2, 3, 4, 5], [6, 7]
        ]
        time_slots = ['08:00-10:00', '10:00-12:00', '14:00-16:00', '16:00-18:00', '18:00-20:00', '19:00-21:00']
        with connection.cursor() as cursor:
            for i in range(25):
                class_id = uuid.uuid4()
                course = random.choice(courses)
                teacher = random.choice(teachers) if teachers else None
                campus = random.choice(campuses) if campuses else None
                manager = random.choice(managers) if managers else None
                status = random.choice(statuses)
                start_date = timezone.now().date() - timedelta(days=random.randint(0, 180))
                end_date = start_date + timedelta(days=random.randint(60, 120))
                weekday = random.choice(weekdays_options)
                time_slot = random.choice(time_slots)
                limit_slot = random.randint(15, 30)
                current_count = random.randint(0, limit_slot) if status != 'planned' else 0
                cursor.execute("""
                    INSERT INTO classes (id, name, start_date, end_date, current_student_count, status, course_id, weekday, time_slot, teacher_id, campus_id, manager_id, limit_slot, is_public, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [class_id, f"Lớp {course['name']} - {i+1}", start_date, end_date, current_count, status,
                      course['id'], weekday, time_slot, teacher['id'] if teacher else None,
                      campus['id'] if campus else None, manager['id'] if manager else None,
                      limit_slot, random.choice([True, False]), timezone.now(), timezone.now()])
                classes.append({'id': class_id, 'course_id': course['id']})
        return classes

    def create_enrollments(self, students, classes, courses):
        """Tạo enrollments - đảm bảo không trùng (student_id, class_id)"""
        enrollments = []
        # Database enum values: pending, paid, overdue, canceled
        invoice_statuses = ['pending', 'paid', 'overdue', 'canceled']
        
        # Track các cặp (student_id, class_id) đã tạo để tránh trùng lặp
        used_pairs = set()
        
        with connection.cursor() as cursor:
            max_attempts = 100  # Tối đa 100 lần thử để tìm cặp chưa dùng
            created_count = 0
            target_count = min(30, len(students) * len(classes) if classes else len(students))
            
            for attempt in range(max_attempts):
                if created_count >= target_count:
                    break
                
                enrollment_id = uuid.uuid4()
                student = random.choice(students)
                class_obj = random.choice(classes) if classes else None
                course = random.choice(courses)
                
                # Tạo key để check unique constraint
                pair_key = (str(student['id']), str(class_obj['id']) if class_obj else None)
                
                # Bỏ qua nếu cặp này đã được sử dụng
                if pair_key in used_pairs:
                    continue
                
                invoice_status = random.choice(invoice_statuses)
                amount = Decimal(random.randint(2000000, 10000000))
                due_date = timezone.now().date() + timedelta(days=random.randint(1, 30))
                
                try:
                    cursor.execute("""
                        INSERT INTO enrollments (id, student_id, class_id, course_id, amount, invoice_status, due_date, notes, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [enrollment_id, student['id'], class_obj['id'] if class_obj else None,
                          course['id'], amount, invoice_status, due_date, 
                          f'Ghi chú cho enrollment {created_count + 1}', timezone.now(), timezone.now()])
                    
                    # Đánh dấu cặp này đã được sử dụng
                    used_pairs.add(pair_key)
                    enrollments.append({'id': enrollment_id})
                    created_count += 1
                except Exception as e:
                    # Nếu bị lỗi unique constraint, bỏ qua và thử tiếp
                    if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
                        continue
                    else:
                        raise
        
        self.stdout.write(f'  Đã tạo {len(enrollments)} enrollments (tối đa {target_count})')
        return enrollments

    def create_sessions(self, classes, teachers, rooms):
        """Tạo 30 sessions"""
        sessions = []
        skills = []  # Cần lấy từ DB
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM skills")
            skills = [{'id': row[0]} for row in cursor.fetchall()]
        
        with connection.cursor() as cursor:
            for i in range(30):
                session_id = uuid.uuid4()
                class_obj = random.choice(classes) if classes else None
                teacher = random.choice(teachers) if teachers else None
                skill = random.choice(skills) if skills else None
                room = random.choice(rooms) if rooms else None
                study_date = timezone.now().date() - timedelta(days=random.randint(0, 60))
                start_time = f"{random.randint(8, 19):02d}:00:00"
                end_time = f"{int(start_time.split(':')[0]) + 2:02d}:00:00"
                cursor.execute("""
                    INSERT INTO sessions (id, study_date, start_time, end_time, skill_id, class_id, teacher_id, room_id, check_in, check_out, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [session_id, study_date, start_time, end_time, skill['id'] if skill else None,
                      class_obj['id'] if class_obj else None, teacher['id'] if teacher else None,
                      room['id'] if room else None, start_time, end_time, timezone.now(), timezone.now()])
                sessions.append({'id': session_id, 'class_id': class_obj['id'] if class_obj else None})
        return sessions

    def create_attendances(self, sessions, students):
        """Tạo attendances - đảm bảo không trùng (student_id, session_id)"""
        attendances = []
        statuses = ['present', 'absent', 'late', 'excused']
        
        # Track các cặp (student_id, session_id) đã tạo để tránh trùng lặp
        used_pairs = set()
        
        with connection.cursor() as cursor:
            max_attempts = 100  # Tối đa 100 lần thử để tìm cặp chưa dùng
            created_count = 0
            target_count = min(30, len(students) * len(sessions) if sessions else len(students))
            
            for attempt in range(max_attempts):
                if created_count >= target_count:
                    break
                
                attendance_id = uuid.uuid4()
                session = random.choice(sessions) if sessions else None
                student = random.choice(students)
                
                # Bỏ qua nếu session là None
                if not session:
                    continue
                
                # Tạo key để check unique constraint
                pair_key = (str(student['id']), str(session['id']))
                
                # Bỏ qua nếu cặp này đã được sử dụng
                if pair_key in used_pairs:
                    continue
                
                status = random.choice(statuses)
                
                try:
                    cursor.execute("""
                        INSERT INTO attendances (id, student_id, session_id, status)
                        VALUES (%s, %s, %s, %s)
                    """, [attendance_id, student['id'], session['id'], status])
                    
                    # Đánh dấu cặp này đã được sử dụng
                    used_pairs.add(pair_key)
                    attendances.append({'id': attendance_id})
                    created_count += 1
                except Exception as e:
                    # Nếu bị lỗi unique constraint, bỏ qua và thử tiếp
                    if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
                        continue
                    else:
                        raise
        
        self.stdout.write(f'  Đã tạo {len(attendances)} attendances (tối đa {target_count})')
        return attendances

    def create_assignments(self, sessions):
        """Tạo 25 assignments"""
        assignments = []
        statuses = ['draft', 'published', 'closed']
        with connection.cursor() as cursor:
            for i in range(25):
                assignment_id = uuid.uuid4()
                session = random.choice(sessions) if sessions else None
                status = random.choice(statuses)
                due_date = timezone.now().date() + timedelta(days=random.randint(1, 14))
                cursor.execute("""
                    INSERT INTO assignments (id, title, description, due_date, status, session_id, url_file, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [assignment_id, f'Bài tập {i+1}', f'Mô tả bài tập {i+1}', due_date, status,
                      session['id'] if session else None, f'/files/assignment_{i+1}.pdf',
                      timezone.now(), timezone.now()])
                assignments.append({'id': assignment_id, 'session_id': session['id'] if session else None})
        return assignments

    def create_submissions(self, assignments, students):
        """Tạo submissions - đảm bảo không trùng (assignment_id, student_id)"""
        submissions = []
        # Database enum values có thể chỉ có: submitted, graded
        # resubmit_required có thể không có trong enum, chỉ dùng 2 giá trị an toàn
        statuses = ['submitted', 'graded']
        
        # Track các cặp (assignment_id, student_id) đã tạo để tránh trùng lặp
        used_pairs = set()
        
        with connection.cursor() as cursor:
            max_attempts = 100  # Tối đa 100 lần thử để tìm cặp chưa dùng
            created_count = 0
            target_count = min(30, len(students) * len(assignments) if assignments else len(students))
            
            for attempt in range(max_attempts):
                if created_count >= target_count:
                    break
                
                submission_id = uuid.uuid4()
                assignment = random.choice(assignments) if assignments else None
                student = random.choice(students)
                
                # Bỏ qua nếu assignment là None
                if not assignment:
                    continue
                
                # Tạo key để check unique constraint
                pair_key = (str(assignment['id']), str(student['id']))
                
                # Bỏ qua nếu cặp này đã được sử dụng
                if pair_key in used_pairs:
                    continue
                
                status = random.choice(statuses)
                result = Decimal(random.randint(50, 100)) if status == 'graded' else None
                correct_count = random.randint(5, 20) if status == 'graded' else None
                total_question = 20 if correct_count else None
                
                try:
                    cursor.execute("""
                        INSERT INTO submissions (id, submitted_at, status, content, result, correct_count, total_question, assignment_id, student_id, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [submission_id, timezone.now() - timedelta(days=random.randint(0, 7)), status,
                          f'Nội dung bài nộp {created_count + 1}', result, correct_count, total_question,
                          assignment['id'], student['id'],
                          timezone.now(), timezone.now()])
                    
                    # Đánh dấu cặp này đã được sử dụng
                    used_pairs.add(pair_key)
                    submissions.append({'id': submission_id})
                    created_count += 1
                except Exception as e:
                    # Nếu bị lỗi unique constraint, bỏ qua và thử tiếp
                    if 'unique' in str(e).lower() or 'duplicate' in str(e).lower():
                        continue
                    else:
                        raise
        
        self.stdout.write(f'  Đã tạo {len(submissions)} submissions (tối đa {target_count})')
        return submissions

    def create_exam_blueprints(self):
        """Tạo 5 exam blueprints"""
        blueprints = []
        exam_types = ['placement', 'midterm', 'final']
        with connection.cursor() as cursor:
            for i, exam_type in enumerate(exam_types):
                blueprint_id = uuid.uuid4()
                cursor.execute("""
                    INSERT INTO exam_blueprints (id, exam_type, title, duration, total_questions, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [blueprint_id, exam_type, f'Blueprint {exam_type} {i+1}', 60, 50,
                      timezone.now(), timezone.now()])
                blueprints.append({'id': blueprint_id, 'exam_type': exam_type})
        return blueprints

    def create_exam_instances(self, blueprints, classes):
        """Tạo 25 exam instances"""
        exam_instances = []
        statuses = ['draft', 'published', 'archived']
        exam_types = ['placement', 'midterm', 'final']
        with connection.cursor() as cursor:
            for i in range(25):
                instance_id = uuid.uuid4()
                blueprint = random.choice(blueprints) if blueprints else None
                class_obj = random.choice(classes) if classes and i > 5 else None  # First 5 are placement
                exam_type = 'placement' if not class_obj else random.choice(['midterm', 'final'])
                status = random.choice(statuses)
                cursor.execute("""
                    INSERT INTO exam_instances (id, blueprint_id, title, status, class_id, exam_type, generated_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [instance_id, blueprint['id'] if blueprint else None,
                      f'Bài kiểm tra {exam_type} - {i+1}', status,
                      class_obj['id'] if class_obj else None, exam_type,
                      timezone.now(), None])
                exam_instances.append({'id': instance_id, 'exam_type': exam_type})
        return exam_instances

    def create_exam_results(self, exam_instances, students):
        """Tạo 30 exam results"""
        exam_results = []
        statuses = ['in_progress', 'completed', 'graded']
        with connection.cursor() as cursor:
            for i in range(30):
                result_id = uuid.uuid4()
                exam_instance = random.choice(exam_instances) if exam_instances else None
                student = random.choice(students)
                status = random.choice(statuses)
                score = Decimal(random.randint(50, 100)) if status != 'in_progress' else None
                submitted_at = timezone.now() - timedelta(days=random.randint(0, 30)) if status != 'in_progress' else None
                cursor.execute("""
                    INSERT INTO exam_results (id, exam_instance_id, student_id, score, submitted_at, status, teacher_comment, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [result_id, exam_instance['id'] if exam_instance else None, student['id'],
                      score, submitted_at, status, f'Comment {i+1}' if status == 'graded' else None,
                      timezone.now(), timezone.now()])
                exam_results.append({'id': result_id})
        return exam_results

    def create_student_certificates(self, students):
        """Tạo 25 student certificates"""
        certificates = []
        skill_groups = ['LR', 'SW']
        source_types = ['certificate', 'entry_test', 'midterm_test', 'final_test']
        statuses = ['VERIFIED', 'PENDING', 'REJECTED']
        with connection.cursor() as cursor:
            for i in range(25):
                cert_id = i + 1  # BigAutoField
                student = random.choice(students)
                skill_group = random.choice(skill_groups)
                source_type = random.choice(source_types)
                score_1 = random.randint(50, 100) if skill_group == 'LR' else random.randint(50, 200)
                score_2 = random.randint(50, 100) if skill_group == 'LR' else random.randint(50, 200)
                total_score = score_1 + score_2 if skill_group == 'LR' else (score_1 + score_2) // 2
                test_date = timezone.now().date() - timedelta(days=random.randint(0, 365))
                expired_date = test_date + timedelta(days=730)  # 2 years
                status = random.choice(statuses)
                cursor.execute("""
                    INSERT INTO student_certificates (student_id, skill_group, source_type, score_1, score_2, total_score, test_date, expired_date, proof_image, status, verification_method, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [student['id'], skill_group, source_type, score_1, score_2, total_score,
                      test_date, expired_date, f'/images/cert_{i+1}.jpg', status,
                      'auto_ocr' if status == 'VERIFIED' else 'manual_admin',
                      timezone.now(), timezone.now()])
                certificates.append({'id': cert_id})
        return certificates

    def create_leave_requests(self, students, classes):
        """Tạo 20 leave requests"""
        leave_requests = []
        statuses = ['pending', 'approved', 'rejected']
        with connection.cursor() as cursor:
            for i in range(20):
                request_id = uuid.uuid4()
                student = random.choice(students)
                class_obj = random.choice(classes) if classes else None
                status = random.choice(statuses)
                session_date = timezone.now().date() + timedelta(days=random.randint(1, 30))
                session_time = f"{random.randint(8, 19):02d}:00:00"
                cursor.execute("""
                    INSERT INTO leave_requests (id, student_id, class_id, session_date, session_time, status, reason, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [request_id, student['id'], class_obj['id'] if class_obj else None,
                      session_date, session_time, status, f'Lý do nghỉ {i+1}',
                      timezone.now(), timezone.now()])
                leave_requests.append({'id': request_id})
        return leave_requests

    def create_reserve_requests(self, students, classes):
        """Tạo 20 reserve requests"""
        reserve_requests = []
        statuses = ['pending', 'approved', 'rejected']
        with connection.cursor() as cursor:
            for i in range(20):
                request_id = uuid.uuid4()
                student = random.choice(students)
                class_obj = random.choice(classes) if classes else None
                status = random.choice(statuses)
                start_date = timezone.now().date() + timedelta(days=random.randint(1, 30))
                end_date = start_date + timedelta(days=random.randint(7, 60))
                cursor.execute("""
                    INSERT INTO reserve_requests (id, student_id, class_id, start_date, end_date, status, reason, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [request_id, student['id'], class_obj['id'] if class_obj else None,
                      start_date, end_date, status, f'Lý do bảo lưu {i+1}',
                      timezone.now(), timezone.now()])
                reserve_requests.append({'id': request_id})
        return reserve_requests

