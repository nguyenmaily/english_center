from rest_framework import serializers
from .models import Course, Skill, Class


class SkillSerializer(serializers.ModelSerializer):
    """
    Serializer cho Skill
    """
    course_name = serializers.CharField(source='course.name', read_only=True)
    
    class Meta:
        model = Skill
        fields = ['id', 'name', 'description', 'course', 'course_name']
        read_only_fields = ['id']


class SkillCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer để tạo/cập nhật Skill
    """
    class Meta:
        model = Skill
        fields = ['name', 'description']


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer cho Course
    """
    skills_count = serializers.SerializerMethodField()
    classes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'level', 'description',
            'total_sessions', 'min_entry_score', 'min_exit_score', 'fee',
            'skills_count', 'classes_count'
        ]
        read_only_fields = ['id']
    
    def get_skills_count(self, obj):
        return obj.skills.count()
    
    def get_classes_count(self, obj):
        return obj.classes.count()


class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Serializer chi tiết cho Course với skills
    """
    skills = SkillSerializer(many=True, read_only=True)
    skills_count = serializers.SerializerMethodField()
    classes_count = serializers.SerializerMethodField()
    active_classes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'level', 'description',
            'total_sessions', 'min_entry_score', 'min_exit_score', 'fee',
            'skills', 'skills_count', 'classes_count', 'active_classes_count'
        ]
        read_only_fields = ['id']
    
    def get_skills_count(self, obj):
        return obj.skills.count()
    
    def get_classes_count(self, obj):
        return obj.classes.count()
    
    def get_active_classes_count(self, obj):
        return obj.classes.filter(status__in=['planned', 'ongoing']).count()


class ClassSerializer(serializers.ModelSerializer):
    """
    Serializer cho Class
    """
    course_name = serializers.CharField(source='course.name', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    campus_name = serializers.CharField(source='campus.name', read_only=True)
    manager_name = serializers.SerializerMethodField()
    is_teacher_assigned = serializers.BooleanField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    available_slots = serializers.IntegerField(read_only=True)
    weekday_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = [
            'id', 'name', 'course', 'course_name',
            'teacher', 'teacher_name', 'campus', 'campus_name',
            'manager', 'manager_name',
            'status', 'start_date', 'end_date',
            'weekday', 'weekday_display', 'time_slot',
            'current_student_count', 'limit_slot', 'available_slots',
            'is_full', 'is_teacher_assigned', 'is_public',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'current_student_count']
    
    def get_teacher_name(self, obj):
        if obj.teacher and obj.teacher.user_account:
            return obj.teacher.user_account.fullname or obj.teacher.user_account.username
        return None
    
    def get_manager_name(self, obj):
        if obj.manager and obj.manager.user_account:
            return obj.manager.user_account.fullname or obj.manager.user_account.username
        return None
    
    def get_weekday_display(self, obj):
        return obj.get_weekday_display()
    
    def validate_weekday(self, value):
        """
        Validate weekday array contains only 1-7
        """
        if value:
            for day in value:
                if day < 1 or day > 7:
                    raise serializers.ValidationError(
                        f"Weekday must be between 1 (Monday) and 7 (Sunday). Got: {day}"
                    )
        return value
    
    def validate(self, data):
        """
        Validate start_date and end_date
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be greater than or equal to start date'
            })
        
        return data


class ClassDetailSerializer(serializers.ModelSerializer):
    """
    Serializer chi tiết cho Class
    """
    course_info = CourseSerializer(source='course', read_only=True)
    teacher_info = serializers.SerializerMethodField()
    campus_info = serializers.SerializerMethodField()
    manager_info = serializers.SerializerMethodField()
    is_teacher_assigned = serializers.BooleanField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    available_slots = serializers.IntegerField(read_only=True)
    weekday_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = [
            'id', 'name', 'course', 'course_info',
            'teacher', 'teacher_info', 'campus', 'campus_info',
            'manager', 'manager_info',
            'status', 'start_date', 'end_date',
            'weekday', 'weekday_display', 'time_slot',
            'current_student_count', 'limit_slot', 'available_slots',
            'is_full', 'is_teacher_assigned', 'is_public',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'current_student_count']
    
    def get_teacher_info(self, obj):
        if obj.teacher and obj.teacher.user_account:
            return {
                'id': str(obj.teacher.id),
                'name': obj.teacher.user_account.fullname or obj.teacher.user_account.username,
                'email': obj.teacher.user_account.email,
                'specialization': obj.teacher.specialization
            }
        return None
    
    def get_campus_info(self, obj):
        if obj.campus:
            return {
                'id': str(obj.campus.id),
                'name': obj.campus.name,
                'address': obj.campus.address,
                'phone': obj.campus.phone
            }
        return None
    
    def get_manager_info(self, obj):
        if obj.manager and obj.manager.user_account:
            return {
                'id': str(obj.manager.id),
                'name': obj.manager.user_account.fullname or obj.manager.user_account.username,
                'email': obj.manager.user_account.email
            }
        return None
    
    def get_weekday_display(self, obj):
        return obj.get_weekday_display()
