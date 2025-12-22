# authentication/management/commands/setup_auth.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import Role, Permission, RolePermission


User = get_user_model()




class Command(BaseCommand):
    help = 'Setup initial authentication data (roles, permissions)'


    def handle(self, *args, **options):
        self.stdout.write('Setting up authentication data...')
       
        # Create roles
        roles_data = [
            {'name': 'student', 'description': 'Student user'},
            {'name': 'teacher', 'description': 'Teacher user'},
            {'name': 'manager', 'description': 'Manager user'},
            {'name': 'admin', 'description': 'Administrator user'},
        ]
       
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description']
                }
            )
            if created:
                self.stdout.write(f'Created role: {role.name}')
            else:
                self.stdout.write(f'Role already exists: {role.name}')
       
        # Create permissions - Tất cả permissions được sử dụng trong backend
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
       
        for perm_data in permissions_data:
            permission, created = Permission.objects.get_or_create(
                name=perm_data['name'],
                defaults={
                    'description': perm_data['description']
                }
            )
            if created:
                self.stdout.write(f'Created permission: {permission.name}')
            else:
                self.stdout.write(f'Permission already exists: {permission.name}')
       
        # ============================================================================
        # ASSIGN PERMISSIONS TO ROLES - QUAN TRỌNG!
        # ============================================================================
        # Đây là nơi map permissions với roles
        # Để biết permission nào thuộc role nào, xem dictionary bên dưới
        #
        # CÁCH ĐỌC:
        # - Key: Tên role (student, teacher, manager, admin)
        # - Value: Danh sách permission names mà role đó có
        #
        # VÍ DỤ:
        # 'manager': ['view_profile', 'edit_profile', ...]
        # → Manager có các permissions: view_profile, edit_profile, ...
        #
        # 'admin': list(Permission.objects.all()...)
        # → Admin có TẤT CẢ permissions trong database
        # ============================================================================
        role_permissions = {
            'student': [
                'view_profile',        # Xem profile của mình
                'edit_profile',        # Sửa profile của mình
                'view_courses',        # Xem khóa học (cần để đăng ký lớp)
                'view_classes',        # Xem lớp học (cần để đăng ký lớp)
                'view_campus',         # Xem campus (cần để filter lớp học)
                'view_assignments',    # Xem bài tập của mình
                'view_submissions',     # Xem bài nộp của mình
                'manage_proficiency_profile',  # Quản lý hồ sơ năng lực tiếng Anh
                'view_enrollments',    # Xem đăng ký lớp học của mình
                'manage_enrollments',  # Đăng ký lớp học
            ],
            'teacher': [
                'view_profile',        # Xem profile của mình
                'edit_profile',        # Sửa profile của mình
                'view_courses',        # Xem khóa học
                'view_classes',        # Xem lớp học
                'manage_classes',      # Quản lý lớp học (lớp được gán)
                'view_assignments',    # Xem bài tập
                'manage_assignments',  # Quản lý bài tập (lớp được gán)
                'view_submissions',    # Xem bài nộp của học viên
            ],
            'manager': [
                'view_profile',        # Xem profile của mình
                'edit_profile',        # Sửa profile của mình
                'view_all_users',      # Xem tất cả users
                'edit_all_users',      # Sửa tất cả users (quản lý học viên, giáo viên)
                'view_users',          # Xem danh sách users
                'manage_users',        # Quản lý users (tạo, sửa, xóa)
                'view_teachers',       # Xem danh sách giáo viên
                'manage_teachers',     # Quản lý giáo viên
                'view_managers',       # Xem danh sách quản lý
                'view_students',       # Xem danh sách học viên
                'view_campus',         # Xem cơ sở (campus của mình)
                'manage_campus',       # Quản lý cơ sở (campus của mình)
                'view_rooms',         # Xem phòng học
                'manage_rooms',        # Quản lý phòng học
                'view_equipments',    # Xem thiết bị
                'manage_equipments',   # Quản lý thiết bị
                'view_courses',        # Xem khóa học
                'manage_courses',      # Quản lý khóa học
                'view_classes',        # Xem lớp học
                'manage_classes',      # Quản lý lớp học
                'view_assignments',    # Xem bài tập
                'manage_assignments',  # Quản lý bài tập
                'view_submissions',    # Xem bài nộp
                'generate_reports',    # Tạo báo cáo
            ],
            'admin': list(Permission.objects.all().values_list('name', flat=True))
            # Admin có TẤT CẢ permissions - không cần liệt kê
        }
       
        for role_name, perm_names in role_permissions.items():
            try:
                role = Role.objects.get(name=role_name)
                # Remove existing permissions for this role
                RolePermission.objects.filter(role=role).delete()
               
                for perm_name in perm_names:
                    try:
                        permission = Permission.objects.get(name=perm_name)
                        RolePermission.objects.create(role=role, permission=permission)
                        self.stdout.write(f'Assigned permission "{permission.name}" to role "{role.name}"')
                    except Permission.DoesNotExist:
                        self.stdout.write(f'Permission "{perm_name}" not found')
            except Role.DoesNotExist:
                self.stdout.write(f'Role "{role_name}" not found')
       
        # Create default admin user
        try:
            admin_role = Role.objects.get(name='admin')
            if not User.objects.filter(username='admin').exists():
                admin_user = User.objects.create_user(
                    username='admin',
                    email='admin@englishcenter.com',
                    password='admin123',
                    fullname='Administrator',
                    roleid=admin_role
                )
                self.stdout.write('Created default admin user: admin/admin123')
            else:
                self.stdout.write('Default admin user already exists')
        except Role.DoesNotExist:
            self.stdout.write('Error: Admin role not found')
       
        self.stdout.write(
            self.style.SUCCESS('Authentication data setup completed successfully!')
        )




