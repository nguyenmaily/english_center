from rest_framework import serializers
from .models import Course, Skill
from classes.models import Class


class SkillSerializer(serializers.ModelSerializer):
    """
    Serializer cho Skill
    """
    courses_count = serializers.SerializerMethodField()
    skill_group = serializers.SerializerMethodField()
    
    class Meta:
        model = Skill
        fields = ['id', 'name', 'description', 'courses_count', 'skill_group']
        read_only_fields = ['id']
    
    def get_courses_count(self, obj):
        """Số lượng courses sử dụng skill này"""
        return obj.courses.count()
    
    def get_skill_group(self, obj):
        """Xác định skill_group (LR/SW) từ skill.name"""
        return obj.skill_group


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
    skill = SkillSerializer(read_only=True)
    skill_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    classes_count = serializers.SerializerMethodField()
    is_eligible = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'level', 'description',
            'total_sessions', 'min_entry_score', 'min_exit_score', 'fee',
            'skill', 'skill_id', 'classes_count', 'is_eligible'
        ]
        read_only_fields = ['id']
    
    def get_classes_count(self, obj):
        return obj.classes.count()
    
    def get_is_eligible(self, obj):
        """
        Tính is_eligible dựa trên điểm của học viên
        Logic:
        1. Lấy skill từ course.skill
        2. Xác định skill_group từ skill.skill_group (hoặc từ course name nếu không có skill)
        3. Lấy điểm học viên từ StudentCertificate
        4. So sánh với min_entry_score
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        # Kiểm tra user có student profile không
        if not hasattr(request.user, 'student_profile'):
            return None
        
        student = request.user.student_profile
        
        # Nếu course không có min_entry_score → eligible = true (không yêu cầu điểm đầu vào)
        if obj.min_entry_score is None:
            return True
        
        # Xác định skill_group
        skill_group = None
        
        # Ưu tiên: lấy từ skill nếu có
        if obj.skill:
            skill_group = obj.skill.skill_group
        else:
            # Fallback: xác định từ course name
            # Hầu hết các khóa học TOEIC là LR, IELTS có thể là LR hoặc SW
            course_name_upper = obj.name.upper()
            if 'SPEAKING' in course_name_upper or 'WRITING' in course_name_upper or 'S&W' in course_name_upper or 'SW' in course_name_upper:
                skill_group = 'SW'
            else:
                # Mặc định là LR cho các khóa học TOEIC/IELTS
                skill_group = 'LR'
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 [is_eligible] Course: {obj.name}, Skill: {obj.skill.name if obj.skill else None}, Skill Group: {skill_group}, Min Entry Score: {obj.min_entry_score}")
        
        if not skill_group:
            logger.warning(f"⚠️ [is_eligible] Cannot determine skill_group for course {obj.name}")
            # Nếu không thể xác định skill_group → không thể kiểm tra → return None
            return None
        
        # Lấy điểm học viên từ StudentCertificate
        # Ưu tiên VERIFIED còn hạn, nếu không có thì xem PENDING
        from proficiency.models import StudentCertificate
        from django.utils import timezone
        import logging
        
        logger = logging.getLogger(__name__)
        today = timezone.now().date()
        
        logger.info(f"🔍 [is_eligible] Course: {obj.name}, Skill Group: {skill_group}, Min Entry Score: {obj.min_entry_score}")
        logger.info(f"🔍 [is_eligible] Student: {student.id}, Today: {today}")
        
        # Tìm chứng chỉ VERIFIED còn hạn trước
        student_cert = StudentCertificate.objects.filter(
            student=student,
            skill_group=skill_group,
            status=StudentCertificate.Status.VERIFIED,
            expired_date__gte=today
        ).order_by('-test_date').first()
        
        if student_cert:
            logger.info(f"✅ [is_eligible] Found VERIFIED cert: ID={student_cert.id}, Score={student_cert.total_score}, Expired={student_cert.expired_date}")
        else:
            logger.info(f"⚠️ [is_eligible] No VERIFIED cert found, checking PENDING...")
        
        # Nếu không có VERIFIED, xem có PENDING không (đang chờ duyệt)
        if not student_cert:
            student_cert = StudentCertificate.objects.filter(
                student=student,
                skill_group=skill_group,
                status=StudentCertificate.Status.PENDING
            ).order_by('-created_at').first()
            
            if student_cert:
                logger.info(f"⏳ [is_eligible] Found PENDING cert: ID={student_cert.id}, Score={student_cert.total_score}")
        
        # Nếu không có điểm → không eligible
        if not student_cert:
            logger.warning(f"❌ [is_eligible] No certificate found for skill_group={skill_group}")
            return False
        
        # So sánh điểm
        is_eligible = student_cert.total_score >= obj.min_entry_score
        logger.info(f"📊 [is_eligible] Student score: {student_cert.total_score}, Min required: {obj.min_entry_score}, Eligible: {is_eligible}")
        
        return is_eligible


class CourseDetailSerializer(serializers.ModelSerializer):
    """
    Serializer chi tiết cho Course với skill
    """
    skill = SkillSerializer(read_only=True)
    skill_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    classes_count = serializers.SerializerMethodField()
    active_classes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'level', 'description',
            'total_sessions', 'min_entry_score', 'min_exit_score', 'fee',
            'skill', 'skill_id', 'classes_count', 'active_classes_count'
        ]
        read_only_fields = ['id']
    
    def get_classes_count(self, obj):
        return obj.classes.count()
    
    def get_active_classes_count(self, obj):
        return obj.classes.filter(status__in=['planned', 'ongoing']).count()


class CourseClassSerializer(serializers.ModelSerializer):
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
                'phone': getattr(obj.campus, 'phone', None) or getattr(obj.campus, 'hotline', None)
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
