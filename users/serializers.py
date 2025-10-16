# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from authentication.models import Role  # ← Import Role
from .models import Teacher, Manager, Student
from campus.serializers import CampusSerializer

User = get_user_model()  # Sẽ lấy UserAccount


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer cho User
    """
    role_name = serializers.CharField(source='roleid.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'fullname', 'phone', 
            'sex', 'dob', 'status', 'urlImage',
            'roleid', 'role_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer để tạo User mới
    """
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    role_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'fullname', 
            'phone', 'sex', 'dob', 'role_id'
        ]
    
    def create(self, validated_data):
        role_id = validated_data.pop('role_id', None)
        password = validated_data.pop('password')
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        
        # Gán role
        if role_id:
            try:
                role = Role.objects.get(id=role_id)
                user.roleid = role
            except Role.DoesNotExist:
                pass
        
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer để cập nhật User
    """
    role_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'email', 'fullname', 'phone', 'sex', 'dob', 
            'status', 'urlImage', 'role_id'
        ]
    
    def update(self, instance, validated_data):
        role_id = validated_data.pop('role_id', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Cập nhật role
        if role_id is not None:
            try:
                role = Role.objects.get(id=role_id)
                instance.roleid = role
            except Role.DoesNotExist:
                pass
        
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer để đổi mật khẩu
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Mật khẩu xác nhận không khớp'
            })
        return data


class TeacherSerializer(serializers.ModelSerializer):
    """
    Serializer cho Teacher
    """
    user_info = UserSerializer(source='user_account', read_only=True)
    campus_name = serializers.CharField(source='campus.name', read_only=True)
    
    class Meta:
        model = Teacher
        fields = [
            'id', 'level', 'specialization', 'campus', 'campus_name',
            'user_account', 'user_info', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TeacherDetailSerializer(serializers.ModelSerializer):
    """
    Serializer chi tiết cho Teacher
    """
    user_info = UserSerializer(source='user_account', read_only=True)
    campus_info = CampusSerializer(source='campus', read_only=True)
    
    class Meta:
        model = Teacher
        fields = [
            'id', 'level', 'specialization', 
            'campus', 'campus_info',
            'user_account', 'user_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ManagerSerializer(serializers.ModelSerializer):
    """
    Serializer cho Manager
    """
    user_info = UserSerializer(source='user_account', read_only=True)
    campus_name = serializers.CharField(source='campus.name', read_only=True)
    
    class Meta:
        model = Manager
        fields = [
            'id', 'campus', 'campus_name',
            'user_account', 'user_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer cho Student
    """
    user_info = UserSerializer(source='user_account', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'id', 'commitment_status', 'target_score',
            'user_account', 'user_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
