from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
import secrets
import string

from .models import Permission, RolePermission, UserAccount, Role, PasswordResetToken

class PermissionSerializer(serializers.ModelSerializer):
    """Serializer cho Permission model"""
    
    class Meta:
        model = Permission
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_codename(self, value):
        """Validate codename format"""
        if not value.replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Codename must contain only letters, numbers, and underscores."
            )
        return value.lower()


class RoleSerializer(serializers.ModelSerializer):
    """Serializer cho Role model"""
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of permission IDs to assign to this role"
    )
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'permission_ids', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create role and assign permissions"""
        permission_ids = validated_data.pop('permission_ids', [])
        role = Role.objects.create(**validated_data)
        
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            for permission in permissions:
                RolePermission.objects.create(role=role, permission=permission)
        
        return role
    
    def update(self, instance, validated_data):
        """Update role and reassign permissions"""
        permission_ids = validated_data.pop('permission_ids', None)
        
        # Update basic fields
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        
        # Update permissions if provided
        if permission_ids is not None:
            # Remove existing permissions
            RolePermission.objects.filter(role=instance).delete()
            
            # Add new permissions
            permissions = Permission.objects.filter(id__in=permission_ids)
            for permission in permissions:
                RolePermission.objects.create(role=instance, permission=permission)
        
        return instance


class RolePermissionSerializer(serializers.Serializer):
    """Serializer for adding permissions to role"""
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of permission IDs to add to the role"
    )
    
    def validate_permission_ids(self, value):
        """Validate that all permission IDs exist"""
        if not value:
            raise serializers.ValidationError("Permission IDs list cannot be empty.")
        
        existing_ids = set(Permission.objects.filter(id__in=value).values_list('id', flat=True))
        invalid_ids = set(value) - existing_ids
        
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid permission IDs: {', '.join(map(str, invalid_ids))}"
            )
        
        return value
        


class UserAccountSerializer(serializers.ModelSerializer):
    """Serializer for User Account display"""
    role = serializers.CharField(source='roleid.name', read_only=True)
    role_id = serializers.CharField(source='roleid.id', read_only=True)
    
    class Meta:
        model = UserAccount
        fields = [
            'id', 'username', 'email', 'status', 'role', 'role_id',
            'fullname', 'phone', 'sex', 'dob', 'urlImage', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.CharField(write_only=True)  # ← ĐÃ ĐÚNG (CharField)
    
    class Meta:
        model = UserAccount
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'fullname', 'phone', 'sex', 'dob', 'role'
        ]
    
    def validate_username(self, value):
        if UserAccount.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value
    
    def validate_email(self, value):
        if UserAccount.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value
 
    def validate(self, attrs):
        # Kiểm tra password khớp
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords don't match."})
        
        # Validate role - Kiểm tra trong database bằng name
        role_name = attrs['role']
        try:
            Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise serializers.ValidationError({
                "role": "Invalid role. Must be one of: student, teacher, manager, admin"
            })
        
        return attrs
    
    
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        role_name = validated_data.pop('role')  # ← SỬA: role_str → role_name
        
        # Get role by name
        role = Role.objects.get(name=role_name)  # ← SỬA: id → name, bỏ try-except
        
        # Create user
        user = UserAccount.objects.create_user(
            roleid=role,
            **validated_data
        )
        return user



class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            # Try to authenticate using username
            user = authenticate(username=username, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            
            if user.status != 'active':
                raise serializers.ValidationError('Account is not active.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password.')


class ForgotPasswordSerializer(serializers.Serializer):
    """Request OTP to reset password"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = UserAccount.objects.get(email=value)
            if user.status != 'active':
                raise serializers.ValidationError('Account is not active.')
        except UserAccount.DoesNotExist:
            raise serializers.ValidationError('Email not found.')
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Reset password with OTP"""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)  # ← OTP 6 số
    new_password = serializers.CharField(validators=[validate_password])
    confirm_password = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords don't match."})
        return attrs

class LogoutSerializer(serializers.Serializer):
    """Serializer for logout request"""
    refresh_token = serializers.CharField(required=True, help_text="Refresh token to blacklist")



class RefreshTokenSerializer(serializers.Serializer):
    """Serializer for JWT refresh token"""
    refresh = serializers.CharField()
