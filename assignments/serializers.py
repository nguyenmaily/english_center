from rest_framework import serializers
from .models import Assignment, AnswerKey, Submission, StudentAnswer


class AnswerKeySerializer(serializers.ModelSerializer):
    """
    Serializer cho AnswerKey
    """
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    
    class Meta:
        model = AnswerKey
        fields = ['id', 'question_number', 'correct_option', 'description', 'assignment', 'assignment_title']
        read_only_fields = ['id']


class AnswerKeyCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer để tạo/cập nhật AnswerKey
    """
    class Meta:
        model = AnswerKey
        fields = ['question_number', 'correct_option', 'description']


class StudentAnswerSerializer(serializers.ModelSerializer):
    """
    Serializer cho StudentAnswer
    """
    class Meta:
        model = StudentAnswer
        fields = ['id', 'question_number', 'selected_option', 'is_correct']
        read_only_fields = ['id', 'is_correct']


class StudentAnswerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer để tạo StudentAnswer
    """
    class Meta:
        model = StudentAnswer
        fields = ['question_number', 'selected_option']


class AssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer cho Assignment
    """
    session_name = serializers.CharField(source='session.name', read_only=True)
    class_name = serializers.SerializerMethodField()
    class_id = serializers.SerializerMethodField()
    answer_keys_count = serializers.SerializerMethodField()
    submissions_count = serializers.SerializerMethodField()
    url_file = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'due_date', 'status',
            'url_file', 'session', 'session_name', 'class_name', 'class_id',
            'answer_keys_count', 'submissions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_class_name(self, obj):
        """Get class name from session -> class_session"""
        if obj.session and hasattr(obj.session, 'class_session') and obj.session.class_session:
            return obj.session.class_session.name
        return None
    
    def get_class_id(self, obj):
        """Get class ID from session -> class_session"""
        if obj.session and hasattr(obj.session, 'class_session') and obj.session.class_session:
            return str(obj.session.class_session.id) if hasattr(obj.session.class_session, 'id') else None
        return None
    
    def get_url_file(self, obj):
        """Convert relative URL to absolute URL"""
        if obj.url_file:
            request = self.context.get('request')
            if request and obj.url_file.startswith('/'):
                return request.build_absolute_uri(obj.url_file)
            elif request and not obj.url_file.startswith('http'):
                return request.build_absolute_uri('/' + obj.url_file.lstrip('/'))
            return obj.url_file
        return None
    
    def get_answer_keys_count(self, obj):
        return obj.answer_keys.count()
    
    def get_submissions_count(self, obj):
        return obj.submissions.count()


class AssignmentDetailSerializer(serializers.ModelSerializer):
    """
    Serializer chi tiết cho Assignment với answer keys
    """
    answer_keys = AnswerKeySerializer(many=True, read_only=True)
    session_name = serializers.CharField(source='session.name', read_only=True)
    class_name = serializers.SerializerMethodField()
    class_id = serializers.SerializerMethodField()
    answer_keys_count = serializers.SerializerMethodField()
    submissions_count = serializers.SerializerMethodField()
    graded_submissions_count = serializers.SerializerMethodField()
    url_file = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'due_date', 'status',
            'url_file', 'session', 'session_name', 'class_name', 'class_id',
            'answer_keys', 'answer_keys_count',
            'submissions_count', 'graded_submissions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_class_name(self, obj):
        """Get class name from session -> class_session"""
        if obj.session and hasattr(obj.session, 'class_session') and obj.session.class_session:
            return obj.session.class_session.name
        return None
    
    def get_class_id(self, obj):
        """Get class ID from session -> class_session"""
        if obj.session and hasattr(obj.session, 'class_session') and obj.session.class_session:
            return str(obj.session.class_session.id) if hasattr(obj.session.class_session, 'id') else None
        return None
    
    def get_url_file(self, obj):
        """Convert relative URL to absolute URL"""
        if obj.url_file:
            request = self.context.get('request')
            if request and obj.url_file.startswith('/'):
                return request.build_absolute_uri(obj.url_file)
            elif request and not obj.url_file.startswith('http'):
                return request.build_absolute_uri('/' + obj.url_file.lstrip('/'))
            return obj.url_file
        return None
    
    def get_answer_keys_count(self, obj):
        return obj.answer_keys.count()
    
    def get_submissions_count(self, obj):
        return obj.submissions.count()
    
    def get_graded_submissions_count(self, obj):
        return obj.submissions.filter(status=Submission.Status.GRADED).count()


class AssignmentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer để tạo và cập nhật Assignment với answer keys
    """
    answer_keys = AnswerKeyCreateUpdateSerializer(many=True, required=False)
    
    class Meta:
        model = Assignment
        fields = [
            'title', 'description', 'due_date', 'status',
            'url_file', 'session', 'answer_keys'
        ]
    
    def create(self, validated_data):
        answer_keys_data = validated_data.pop('answer_keys', [])
        assignment = Assignment.objects.create(**validated_data)
        
        for answer_key_data in answer_keys_data:
            AnswerKey.objects.create(assignment=assignment, **answer_key_data)
        
        return assignment
    
    def update(self, instance, validated_data):
        """
        Update assignment - answer_keys are handled in view, not here
        """
        # Remove answer_keys from validated_data as they're handled separately in view
        validated_data.pop('answer_keys', None)
        
        # Update assignment fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class SubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer cho Submission
    """
    student_answers = StudentAnswerSerializer(many=True, read_only=True)
    answer_keys = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    student_code = serializers.SerializerMethodField()
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    is_graded = serializers.BooleanField(read_only=True)
    needs_resubmit = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Submission
        fields = [
            'id', 'submitted_at', 'status', 'content', 'result',
            'correct_count', 'total_question',
            'assignment', 'assignment_title',
            'student', 'student_name', 'student_code',
            'student_answers', 'answer_keys', 'is_graded', 'needs_resubmit',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'submitted_at', 'created_at', 'updated_at']
    
    def get_answer_keys(self, obj):
        """Lấy answer keys của assignment để so sánh với đáp án học sinh"""
        from .models import AnswerKey
        answer_keys = AnswerKey.objects.filter(assignment=obj.assignment).order_by('question_number')
        return AnswerKeySerializer(answer_keys, many=True).data
    
    def get_student_name(self, obj):
        if obj.student and obj.student.user_account:
            return obj.student.user_account.fullname or obj.student.user_account.username
        return None
    
    def get_student_code(self, obj):
        if obj.student and obj.student.user_account:
            return obj.student.user_account.username
        return None


class SubmissionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer để tạo Submission với student answers
    """
    student_answers = StudentAnswerCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Submission
        fields = ['content', 'student_answers']
    
    def save(self, **kwargs):
        """Override save to capture assignment and student"""
        self._assignment = kwargs.pop('assignment', None)
        self._student = kwargs.pop('student', None)
        self._status = kwargs.pop('status', 'submitted')
        return super().save(**kwargs)
    
    def create(self, validated_data):
        import uuid
        from django.utils import timezone
        from django.db import connection
        
        student_answers_data = validated_data.pop('student_answers', [])
        content = validated_data.get('content', None)
        
        # Get assignment, student, and status from save() kwargs
        assignment = getattr(self, '_assignment', None)
        student = getattr(self, '_student', None)
        status = getattr(self, '_status', 'submitted')
        
        if not assignment or not student:
            raise ValueError("Assignment and student must be provided in serializer.save()")
        
        # Create submission using raw SQL to avoid enum issues
        submission_id = uuid.uuid4()
        submitted_at = timezone.now()
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO submissions (id, submitted_at, status, content, assignment_id, student_id, created_at, updated_at)
                    VALUES (%s, %s, %s::submission_status_enum, %s, %s, %s, %s, %s)
                    """,
                    [
                        str(submission_id),
                        submitted_at,
                        status,
                        content,
                        str(assignment.id),
                        str(student.id),
                        submitted_at,
                        submitted_at
                    ]
                )
        except Exception as e:
            # Fallback: try without enum cast
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to insert with enum cast: {str(e)}, trying without cast")
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO submissions (id, submitted_at, status, content, assignment_id, student_id, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            str(submission_id),
                            submitted_at,
                            status,
                            content,
                            str(assignment.id),
                            str(student.id),
                            submitted_at,
                            submitted_at
                        ]
                    )
            except Exception as e2:
                logger.error(f"Failed to insert submission: {str(e2)}")
                raise
        
        # Get created submission
        submission = Submission.objects.get(id=submission_id)
        
        # Create student answers
        for answer_data in student_answers_data:
            StudentAnswer.objects.create(submission=submission, **answer_data)
        
        return submission


class SubmissionGradeSerializer(serializers.ModelSerializer):
    """
    Serializer để chấm điểm Submission
    """
    class Meta:
        model = Submission
        fields = ['result', 'status', 'content']
    
    def validate_result(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Result must be between 0 and 100")
        return value


class SubmissionListSerializer(serializers.ModelSerializer):
    """
    Serializer cho danh sách Submission (dùng cho teacher xem thống kê)
    """
    student_name = serializers.SerializerMethodField()
    student_code = serializers.SerializerMethodField()
    
    class Meta:
        model = Submission
        fields = [
            'id', 'student', 'student_name', 'student_code',
            'submitted_at', 'status', 'result',
            'correct_count', 'total_question'
        ]
    
    def get_student_name(self, obj):
        if obj.student and obj.student.user_account:
            return obj.student.user_account.fullname or obj.student.user_account.username
        return None
    
    def get_student_code(self, obj):
        if obj.student and obj.student.user_account:
            return obj.student.user_account.username
        return None
