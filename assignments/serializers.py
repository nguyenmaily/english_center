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
    answer_keys_count = serializers.SerializerMethodField()
    submissions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'due_date', 'status',
            'url_file', 'session', 'session_name',
            'answer_keys_count', 'submissions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
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
    answer_keys_count = serializers.SerializerMethodField()
    submissions_count = serializers.SerializerMethodField()
    graded_submissions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Assignment
        fields = [
            'id', 'title', 'description', 'due_date', 'status',
            'url_file', 'session', 'session_name',
            'answer_keys', 'answer_keys_count',
            'submissions_count', 'graded_submissions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_answer_keys_count(self, obj):
        return obj.answer_keys.count()
    
    def get_submissions_count(self, obj):
        return obj.submissions.count()
    
    def get_graded_submissions_count(self, obj):
        return obj.submissions.filter(status=Submission.Status.GRADED).count()


class AssignmentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer để tạo Assignment với answer keys
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


class SubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer cho Submission
    """
    student_answers = StudentAnswerSerializer(many=True, read_only=True)
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
            'student_answers', 'is_graded', 'needs_resubmit',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'submitted_at', 'created_at', 'updated_at']
    
    def get_student_name(self, obj):
        if obj.student and obj.student.user_account:
            return obj.student.user_account.fullname or obj.student.user_account.username
        return None
    
    def get_student_code(self, obj):
        return obj.student.student_code if obj.student else None


class SubmissionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer để tạo Submission với student answers
    """
    student_answers = StudentAnswerCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Submission
        fields = ['content', 'student_answers']
    
    def create(self, validated_data):
        student_answers_data = validated_data.pop('student_answers', [])
        submission = Submission.objects.create(**validated_data)
        
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
        return obj.student.student_code if obj.student else None
