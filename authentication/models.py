# authentication/models.py
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
from core.models import BaseModel
import uuid


class Role(BaseModel):
    """
    Role model for managing user roles
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'roles'
        ordering = ['name']
        managed = False
    
    def __str__(self):
        return self.name


class Permission(BaseModel):
    """
    Permission model for managing permissions
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'permissions'
        ordering = ['name']
        managed = False
    
    def __str__(self):
        return self.name


class RolePermission(models.Model):
    """
    Role Permission junction table
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_column='role_id', primary_key=True)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, db_column='permission_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'role_permissions'
        unique_together = ['role', 'permission']
        managed = False
    
    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"


class CustomUserManager(UserManager):
    """
    Custom User Manager để bỏ qua các trường không cần thiết
    """
    def _create_user(self, username, email, password, **extra_fields):
        extra_fields.pop('is_staff', None)
        extra_fields.pop('is_superuser', None)
        extra_fields.pop('is_active', None)
        extra_fields.pop('date_joined', None)
        extra_fields.pop('last_login', None)
        
        if not username:
            raise ValueError('The username must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        return self._create_user(username, email, password, **extra_fields)





class UserAccount(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    
    SEX_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.TextField(unique=True)
    password = models.TextField(db_column='password_hash')  # Map to password_hash in DB
    email = models.EmailField(unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_column='status')
    urlImage = models.TextField(blank=True, null=True, db_column='avatar_url')
    roleid = models.ForeignKey(
        Role, 
        on_delete=models.SET_NULL, 
        null=True,
        db_column='role_id'
    )
    fullname = models.TextField(db_column='full_name', blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    sex = models.CharField(max_length=10, choices=SEX_CHOICES, default='other')
    dob = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Các trường này từ AbstractUser cần override
    first_name = None
    last_name = None
    last_login = None  
    is_superuser = None  
    is_staff = None  
    #is_active = None  
    date_joined = None  
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        db_table = 'user_accounts'
        ordering = ['-created_at']
        managed = False
    
    def __str__(self):
        return f"{self.fullname or self.username} ({self.username})"
    
    @property
    def is_active(self):
        """
        Property để tương thích với Django authentication backend
        Trả về True nếu status = 'active'
        """
        return self.status == 'active'

    @property
    def role(self):
        """Get role name"""
        return self.roleid.name if self.roleid else None
    
    def has_permission(self, permission_name):
        """Check if user has specific permission"""
        if not self.roleid:
            return False
        
        return RolePermission.objects.filter(
            role=self.roleid,
            permission__name=permission_name
        ).exists()
    
    def get_all_permissions(self):
        """Get all permissions for this user"""
        if not self.roleid:
            return []
        
        return Permission.objects.filter(
            rolepermission__role=self.roleid
        ).values_list('name', flat=True)


class PasswordResetToken(models.Model):
    """
    Model for storing password reset tokens
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, db_column='user_id')
    token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']
        managed=False
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"Reset token for {self.user.username}"
