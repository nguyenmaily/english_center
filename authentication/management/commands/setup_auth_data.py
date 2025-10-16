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
        
        # Create permissions
        permissions_data = [
            {'name': 'view_profile', 'description': 'Can view own profile'},
            {'name': 'edit_profile', 'description': 'Can edit own profile'},
            {'name': 'view_all_users', 'description': 'Can view all users'},
            {'name': 'edit_all_users', 'description': 'Can edit all users'},
            {'name': 'manage_classes', 'description': 'Can manage classes'},
            {'name': 'manage_courses', 'description': 'Can manage courses'},
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
        
        # Assign permissions to roles
        role_permissions = {
            'student': ['view_profile', 'edit_profile'],
            'teacher': ['view_profile', 'edit_profile', 'manage_classes', 'manage_courses'],
            'manager': ['view_profile', 'edit_profile', 'view_all_users', 'manage_classes', 'manage_courses', 'generate_reports'],
            'admin': list(Permission.objects.all().values_list('name', flat=True))
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
