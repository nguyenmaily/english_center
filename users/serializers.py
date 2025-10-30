from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from authentication.models import Role
from .models import Teacher, Manager, Student
from campus.models import Campus

User = get_user_model()


# ==================== USER SERIALIZERS ====================

class UserSerializer(serializers.ModelSerializer):
    """Serializer cơ bản cho User"""
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
    Serializer để Admin tạo User mới + Profile
    Chỉ admin có quyền manage_users mới dùng được
    """
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    role_name = serializers.ChoiceField(
        choices=['student', 'teacher', 'manager', 'admin'],
        write_only=True,
        required=True
    )
    
    # ========== Teacher Fields ==========
    teacher_level = serializers.CharField(
        write_only=True, 
        required=False, 
        allow_blank=True,
        allow_null=True,
        help_text="Teacher level (e.g., Junior, Senior)"
    )
    teacher_specialization = serializers.CharField(
        write_only=True, 
        required=False, 
        allow_blank=True,
        allow_null=True,
        help_text="Teacher specialization (e.g., IELTS Speaking)"
    )
    teacher_campus_id = serializers.UUIDField(
        write_only=True, 
        required=False, 
        allow_null=True,
        help_text="Campus ID for teacher"
    )
    
    # ========== Manager Fields ==========
    manager_campus_id = serializers.UUIDField(
        write_only=True, 
        required=False, 
        allow_null=True,
        help_text="Campus ID for manager (required)"
    )
    
    # ========== Student Fields ==========
    student_target_score = serializers.IntegerField(
        write_only=True, 
        required=False, 
        allow_null=True,
        min_value=0,
        max_value=9,
        help_text="Target IELTS score"
    )
    student_commitment_status = serializers.ChoiceField(
        choices=Student.CommitmentStatus.choices,
        write_only=True,
        required=False,
        allow_null=True,
        default=Student.CommitmentStatus.NOT_COMMITTED
    )
    
    class Meta:
        model = User
        fields = [
            # Basic user info
            'username', 'email', 'password', 'fullname', 
            'phone', 'sex', 'dob', 'status', 'urlImage',
            'role_name',
            # Teacher fields
            'teacher_level', 'teacher_specialization', 'teacher_campus_id',
            # Manager fields
            'manager_campus_id',
            # Student fields
            'student_target_score', 'student_commitment_status'
        ]
    
    def validate(self, attrs):
        """Validate dựa trên role"""
        role_name = attrs.get('role_name')
        
        # Validate teacher - Specialization là BẮT BUỘC
        if role_name == 'teacher':
            specialization = attrs.get('teacher_specialization')
            if not specialization or (isinstance(specialization, str) and specialization.strip() == ''):
                raise serializers.ValidationError({
                    'teacher_specialization': 'Specialization is required for teachers'
                })
        
        # Validate manager - Campus là BẮT BUỘC
        if role_name == 'manager':
            campus_id = attrs.get('manager_campus_id')
            if not campus_id:
                raise serializers.ValidationError({
                    'manager_campus_id': 'Campus is required for managers'
                })
            
            # Kiểm tra campus có tồn tại không
            if not Campus.objects.filter(id=campus_id).exists():
                raise serializers.ValidationError({
                    'manager_campus_id': 'Campus not found'
                })
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Tạo User + Profile trong 1 transaction
        """
        # Extract data
        role_name = validated_data.pop('role_name')
        password = validated_data.pop('password')
        
        # Teacher data
        teacher_level = validated_data.pop('teacher_level', None)
        teacher_specialization = validated_data.pop('teacher_specialization', None)
        teacher_campus_id = validated_data.pop('teacher_campus_id', None)
        
        # Manager data
        manager_campus_id = validated_data.pop('manager_campus_id', None)
        
        # Student data
        student_target_score = validated_data.pop('student_target_score', None)
        student_commitment_status = validated_data.pop(
            'student_commitment_status', 
            Student.CommitmentStatus.NOT_COMMITTED
        )
        
        # 1. Get role
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise serializers.ValidationError({
                'role_name': f'Role "{role_name}" does not exist'
            })
        
        # 2. Create user
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.roleid = role
        user.save()
        
        # 3. Create profile based on role
        try:
            if role_name == 'teacher':
                campus = None
                if teacher_campus_id:
                    campus = Campus.objects.get(id=teacher_campus_id)
                
                Teacher.objects.create(
                    user_account=user,
                    level=teacher_level or '',
                    specialization=teacher_specialization or '',
                    campus=campus
                )
            
            elif role_name == 'manager':
                campus = Campus.objects.get(id=manager_campus_id)
                
                Manager.objects.create(
                    user_account=user,
                    campus=campus
                )
            
            elif role_name == 'student':
                Student.objects.create(
                    user_account=user,
                    target_score=student_target_score,
                    commitment_status=student_commitment_status or Student.CommitmentStatus.NOT_COMMITTED
                )
            
            # Admin không cần profile
        
        except Campus.DoesNotExist:
            raise serializers.ValidationError({
                'campus_id': 'Campus not found'
            })
        
        return user


class UserWithProfileSerializer(serializers.ModelSerializer):
    """
    Serializer để hiển thị User + Profile
    """
    role_name = serializers.CharField(source='roleid.name', read_only=True)
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'fullname', 'phone', 
            'sex', 'dob', 'status', 'urlImage',
            'roleid', 'role_name', 'profile',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_profile(self, obj):
        """Lấy profile tương ứng với role"""
        role_name = obj.roleid.name if obj.roleid else None
        
        if role_name == 'teacher':
            try:
                teacher = Teacher.objects.get(user_account=obj)
                return {
                    'id': str(teacher.id),
                    'level': teacher.level,
                    'specialization': teacher.specialization,
                    'campus_id': str(teacher.campus.id) if teacher.campus else None,
                    'campus_name': teacher.campus.name if teacher.campus else None
                }
            except Teacher.DoesNotExist:
                return None
        
        elif role_name == 'manager':
            try:
                manager = Manager.objects.get(user_account=obj)
                return {
                    'id': str(manager.id),
                    'campus_id': str(manager.campus.id) if manager.campus else None,
                    'campus_name': manager.campus.name if manager.campus else None
                }
            except Manager.DoesNotExist:
                return None
        
        elif role_name == 'student':
            try:
                student = Student.objects.get(user_account=obj)
                return {
                    'id': str(student.id),
                    'commitment_status': student.commitment_status,
                    'commitment_status_display': student.get_commitment_status_display(),
                    'target_score': student.target_score
                }
            except Student.DoesNotExist:
                return None
        
        return None


class UserUpdateWithProfileSerializer(serializers.ModelSerializer):
    """
    Serializer để Admin cập nhật User + Profile
    """
    # Teacher fields
    teacher_level = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    teacher_specialization = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    teacher_campus_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    # Manager fields
    manager_campus_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    # Student fields
    student_target_score = serializers.IntegerField(write_only=True, required=False, allow_null=True, min_value=0, max_value=9)
    student_commitment_status = serializers.ChoiceField(
        choices=Student.CommitmentStatus.choices,
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'fullname', 'phone', 'sex', 'dob', 
            'status', 'urlImage',
            # Teacher fields
            'teacher_level', 'teacher_specialization', 'teacher_campus_id',
            # Manager fields
            'manager_campus_id',
            # Student fields
            'student_target_score', 'student_commitment_status'
        ]
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Cập nhật User + Profile
        """
        # Extract profile data
        teacher_level = validated_data.pop('teacher_level', None)
        teacher_specialization = validated_data.pop('teacher_specialization', None)
        teacher_campus_id = validated_data.pop('teacher_campus_id', None)
        
        manager_campus_id = validated_data.pop('manager_campus_id', None)
        
        student_target_score = validated_data.pop('student_target_score', None)
        student_commitment_status = validated_data.pop('student_commitment_status', None)
        
        # Update user basic info
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile based on role
        role_name = instance.roleid.name if instance.roleid else None
        
        if role_name == 'teacher':
            try:
                teacher = Teacher.objects.get(user_account=instance)
                
                if teacher_level is not None:
                    teacher.level = teacher_level
                if teacher_specialization is not None:
                    teacher.specialization = teacher_specialization
                if teacher_campus_id is not None:
                    if teacher_campus_id:
                        teacher.campus = Campus.objects.get(id=teacher_campus_id)
                    else:
                        teacher.campus = None
                
                teacher.save()
            except Teacher.DoesNotExist:
                pass
            except Campus.DoesNotExist:
                raise serializers.ValidationError({
                    'teacher_campus_id': 'Campus not found'
                })
        
        elif role_name == 'manager':
            try:
                manager = Manager.objects.get(user_account=instance)
                
                if manager_campus_id is not None:
                    if manager_campus_id:
                        manager.campus = Campus.objects.get(id=manager_campus_id)
                    else:
                        manager.campus = None
                
                manager.save()
            except Manager.DoesNotExist:
                pass
            except Campus.DoesNotExist:
                raise serializers.ValidationError({
                    'manager_campus_id': 'Campus not found'
                })
        
        elif role_name == 'student':
            try:
                student = Student.objects.get(user_account=instance)
                
                if student_target_score is not None:
                    student.target_score = student_target_score
                if student_commitment_status is not None:
                    student.commitment_status = student_commitment_status
                
                student.save()
            except Student.DoesNotExist:
                pass
        
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer để đổi mật khẩu"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match'
            })
        return data


# ==================== PROFILE SERIALIZERS ====================

class TeacherSerializer(serializers.ModelSerializer):
    """Serializer cho Teacher"""
    user_info = UserSerializer(source='user_account', read_only=True)
    campus_name = serializers.CharField(source='campus.name', read_only=True)
    
    class Meta:
        model = Teacher
        fields = [
            'id', 'level', 'specialization', 
            'campus', 'campus_name',
            'user_account', 'user_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TeacherDetailSerializer(serializers.ModelSerializer):
    """Serializer chi tiết cho Teacher"""
    user_info = UserWithProfileSerializer(source='user_account', read_only=True)
    campus_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = [
            'id', 'level', 'specialization',
            'campus', 'campus_info',
            'user_account', 'user_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_campus_info(self, obj):
        if obj.campus:
            return {
                'id': str(obj.campus.id),
                'name': obj.campus.name,
                'address': obj.campus.address,
                'phone': obj.campus.phone
            }
        return None


class ManagerSerializer(serializers.ModelSerializer):
    """Serializer cho Manager"""
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
    """Serializer cho Student"""
    user_info = UserSerializer(source='user_account', read_only=True)
    commitment_status_display = serializers.CharField(
        source='get_commitment_status_display', 
        read_only=True
    )
    
    class Meta:
        model = Student
        fields = [
            'id', 'commitment_status', 'commitment_status_display',
            'target_score', 'user_account', 'user_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoleFieldsSchemaSerializer(serializers.Serializer):
    """Serializer cho response của role fields schema"""
    success = serializers.BooleanField()
    data = serializers.DictField()

