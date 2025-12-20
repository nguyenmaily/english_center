# authentication/management/commands/fix_passwords.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix passwords in database - hash passwords that are in format hash$role'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually changing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        self.stdout.write('Checking passwords in database...')
        
        # Get all users with raw SQL to check password format
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, password_hash, role_id FROM user_accounts")
            users = cursor.fetchall()
        
        fixed_count = 0
        skipped_count = 0
        
        for user_id, username, password_hash, role_id in users:
            # Check if password is in format hash$role
            if password_hash and password_hash.startswith('hash$'):
                # Extract role from password
                role_name = password_hash.replace('hash$', '')
                
                # Map role name to password
                # Based on database: hash$manager -> password is 'manager'
                # hash$admin -> password is 'admin', etc.
                new_password = role_name
                
                if dry_run:
                    self.stdout.write(
                        f'Would fix: {username} - password: {password_hash} -> {new_password} (hashed)'
                    )
                else:
                    try:
                        user = User.objects.get(id=user_id)
                        user.set_password(new_password)
                        user.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'[OK] Fixed password for: {username}')
                        )
                        fixed_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'[ERROR] Error fixing {username}: {str(e)}')
                        )
            else:
                skipped_count += 1
                if not dry_run:
                    self.stdout.write(f'Skipped: {username} (password already in correct format)')
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\nWould fix {len([u for u in users if u[2] and u[2].startswith("hash$")])} passwords'))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[OK] Fixed {fixed_count} passwords\n'
                    f'  Skipped {skipped_count} passwords (already correct)'
                )
            )
            
            # Show test credentials
            self.stdout.write('\n' + '='*50)
            self.stdout.write('Test credentials (based on role):')
            self.stdout.write('='*50)
            self.stdout.write('Manager: username = ql.hoangc, password = manager')
            self.stdout.write('Admin: username = admin.ly, password = admin')
            self.stdout.write('Teacher: username = gv.tranb, password = teacher')
            self.stdout.write('Student: username = hv.minhd, password = student')
            self.stdout.write('='*50)


