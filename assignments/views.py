from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg

from authentication.permissions import PermissionMixin
from .models import Assignment, AnswerKey, Submission, StudentAnswer
from .serializers import (
    AssignmentSerializer, AssignmentDetailSerializer, AssignmentCreateSerializer,
    AnswerKeySerializer, AnswerKeyCreateUpdateSerializer,
    SubmissionSerializer, SubmissionCreateSerializer,
    SubmissionGradeSerializer, SubmissionListSerializer
)


# ==================== STUDENT ASSIGNMENT VIEWS ====================

class StudentAssignmentListView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/my-homework/ - Lấy danh sách bài tập của học viên
    
    Query params:
    - status: Lọc theo trạng thái (draft, published, closed)
    - session: Lọc theo session
    """
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_assignments',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'session']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        student = self.request.user.student
        return Assignment.objects.filter(
            session__class_session__enrollments__student=student,
            status=Assignment.Status.PUBLISHED
        ).distinct()


class StudentAssignmentDetailView(PermissionMixin, generics.RetrieveAPIView):
    """
    GET /api/my-homework/{id}/ - Xem chi tiết bài tập
    """
    serializer_class = AssignmentDetailSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_assignments',
    }
    lookup_field = 'pk'
    
    def get_queryset(self):
        # ✅ FIX: Thêm check cho Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Assignment.objects.none()
        
        student = self.request.user.student
        return Assignment.objects.filter(
            session__class_session__enrollments__student=student,
            status=Assignment.Status.PUBLISHED
        ).distinct()


class StudentAssignmentStartView(PermissionMixin, APIView):
    """
    GET /api/my-homework/{id}/start/ - Mở bài tập để xem chi tiết và làm
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_assignments',
    }
    
    def get(self, request, pk):
        student = request.user.student
        assignment = get_object_or_404(
            Assignment,
            pk=pk,
            session__class_session__enrollments__student=student,
            status=Assignment.Status.PUBLISHED
        )
        
        # Kiểm tra xem học viên đã nộp bài chưa
        existing_submission = Submission.objects.filter(
            assignment=assignment,
            student=student
        ).first()
        
        if existing_submission:
            return Response({
                'message': 'You have already submitted this assignment',
                'submission_id': existing_submission.id,
                'can_resubmit': existing_submission.needs_resubmit
            }, status=status.HTTP_200_OK)
        
        serializer = AssignmentDetailSerializer(assignment)
        return Response(serializer.data)


class StudentAssignmentSubmitView(PermissionMixin, APIView):
    """
    POST /api/my-homework/{id}/submit/ - Nộp bài tập
    
    Request Body:
    {
        "content": "Nội dung bài làm (optional)",
        "student_answers": [
            {"question_number": 1, "selected_option": 2},
            {"question_number": 2, "selected_option": 1}
        ]
    }
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'POST': 'submit_assignments',
    }
    
    def post(self, request, pk):
        student = request.user.student
        assignment = get_object_or_404(
            Assignment,
            pk=pk,
            session__class_session__enrollments__student=student,
            status=Assignment.Status.PUBLISHED
        )
        
        # Kiểm tra xem đã nộp bài chưa
        existing_submission = Submission.objects.filter(
            assignment=assignment,
            student=student
        ).exclude(status=Submission.Status.RESUBMIT_REQUIRED).first()
        
        if existing_submission:
            return Response({
                'error': 'You have already submitted this assignment'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Tạo submission mới
        serializer = SubmissionCreateSerializer(data=request.data)
        if serializer.is_valid():
            submission = serializer.save(
                assignment=assignment,
                student=student,
                status=Submission.Status.SUBMITTED
            )
            
            # Tự động chấm điểm nếu có answer keys
            self._auto_grade_submission(submission)
            
            return Response(
                SubmissionSerializer(submission).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _auto_grade_submission(self, submission):
        """
        Tự động chấm điểm dựa trên answer keys
        """
        answer_keys = AnswerKey.objects.filter(assignment=submission.assignment)
        if not answer_keys.exists():
            return
        
        student_answers = StudentAnswer.objects.filter(submission=submission)
        correct_count = 0
        total_questions = answer_keys.count()
        
        for student_answer in student_answers:
            answer_key = answer_keys.filter(
                question_number=student_answer.question_number
            ).first()
            
            if answer_key and str(student_answer.selected_option) == answer_key.correct_option:
                student_answer.is_correct = 1
                correct_count += 1
            else:
                student_answer.is_correct = 0
            student_answer.save()
        
        # Cập nhật submission
        submission.correct_count = correct_count
        submission.total_question = total_questions
        submission.result = (correct_count / total_questions * 100) if total_questions > 0 else 0
        submission.status = Submission.Status.GRADED
        submission.save()


class StudentAssignmentResultView(PermissionMixin, APIView):
    """
    GET /api/my-homework/{id}/result/ - Xem kết quả & nhận xét
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_assignments',
    }
    
    def get(self, request, pk):
        student = request.user.student
        assignment = get_object_or_404(Assignment, pk=pk)
        
        submission = get_object_or_404(
            Submission,
            assignment=assignment,
            student=student
        )
        
        serializer = SubmissionSerializer(submission)
        return Response(serializer.data)


# ==================== STUDENT SUBMISSION VIEWS ====================

class StudentSubmissionListView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/submissions/ - Lấy danh sách bài đã nộp của học viên
    """
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_submissions',
    }
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'assignment']
    ordering_fields = ['submitted_at', 'result']
    ordering = ['-submitted_at']
    
    def get_queryset(self):
        student = self.request.user.student
        return Submission.objects.filter(student=student)


class StudentSubmissionDetailView(PermissionMixin, generics.RetrieveAPIView):
    """
    GET /api/submissions/{id}/ - Xem chi tiết bài nộp
    """
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_submissions',
    }
    lookup_field = 'pk'
    
    def get_queryset(self):
        # ✅ FIX: Thêm check cho Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Submission.objects.none()
        
        student = self.request.user.student
        return Submission.objects.filter(student=student)

class StudentSubmissionResubmitView(PermissionMixin, APIView):
    """
    POST /api/submissions/{id}/resubmit/ - Học viên nộp lại bài (nếu bị yêu cầu)
    
    Request Body:
    {
        "content": "Nội dung bài làm lại",
        "student_answers": [
            {"question_number": 1, "selected_option": 3}
        ]
    }
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'POST': 'submit_assignments',
    }
    
    def post(self, request, pk):
        student = request.user.student
        submission = get_object_or_404(Submission, pk=pk, student=student)
        
        if not submission.needs_resubmit:
            return Response({
                'error': 'This submission does not require resubmission'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = SubmissionCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Xóa câu trả lời cũ
            StudentAnswer.objects.filter(submission=submission).delete()
            
            # Cập nhật submission
            submission.content = serializer.validated_data.get('content', submission.content)
            submission.status = Submission.Status.SUBMITTED
            submission.submitted_at = timezone.now()
            submission.save()
            
            # Tạo câu trả lời mới
            student_answers_data = serializer.validated_data.get('student_answers', [])
            for answer_data in student_answers_data:
                StudentAnswer.objects.create(submission=submission, **answer_data)
            
            # Tự động chấm điểm
            self._auto_grade_submission(submission)
            
            return Response(
                SubmissionSerializer(submission).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _auto_grade_submission(self, submission):
        """
        Tự động chấm điểm dựa trên answer keys
        """
        answer_keys = AnswerKey.objects.filter(assignment=submission.assignment)
        if not answer_keys.exists():
            return
        
        student_answers = StudentAnswer.objects.filter(submission=submission)
        correct_count = 0
        total_questions = answer_keys.count()
        
        for student_answer in student_answers:
            answer_key = answer_keys.filter(
                question_number=student_answer.question_number
            ).first()
            
            if answer_key and str(student_answer.selected_option) == answer_key.correct_option:
                student_answer.is_correct = 1
                correct_count += 1
            else:
                student_answer.is_correct = 0
            student_answer.save()
        
        submission.correct_count = correct_count
        submission.total_question = total_questions
        submission.result = (correct_count / total_questions * 100) if total_questions > 0 else 0
        submission.status = Submission.Status.GRADED
        submission.save()


# ==================== TEACHER ASSIGNMENT VIEWS ====================

class TeacherAssignmentListCreateView(PermissionMixin, generics.ListCreateAPIView):
    """
    GET /api/assignments/ - Lấy danh sách bài tập đã giao
    POST /api/assignments/ - Giao bài tập mới (cần quyền: manage_assignments)
    
    Query params:
    - session: Lọc theo session
    - status: Lọc theo trạng thái (draft, published, closed)
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_assignments',
        'POST': 'manage_assignments',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['session', 'status']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        teacher = self.request.user.teacher
        return Assignment.objects.filter(
            session__class_session__teacher=teacher
        ).distinct()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AssignmentCreateSerializer
        return AssignmentSerializer


class TeacherAssignmentDetailView(PermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/assignments/{id}/ - Xem chi tiết bài tập
    PUT /api/assignments/{id}/ - Cập nhật bài tập (cần quyền: manage_assignments)
    PATCH /api/assignments/{id}/ - Cập nhật bài tập (cần quyền: manage_assignments)
    DELETE /api/assignments/{id}/ - Xóa bài tập (cần quyền: manage_assignments)
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_assignments',
        'PUT': 'manage_assignments',
        'PATCH': 'manage_assignments',
        'DELETE': 'manage_assignments',
    }
    lookup_field = 'pk'
    
    def get_queryset(self):
        # ✅ FIX: Thêm check cho Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Assignment.objects.none()
        
        teacher = self.request.user.teacher
        return Assignment.objects.filter(
            session__class_session__teacher=teacher
        ).distinct()
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AssignmentDetailSerializer
        return AssignmentSerializer

class TeacherAssignmentSubmissionsView(PermissionMixin, APIView):
    """
    GET /api/assignments/{id}/submissions/ - Xem thống kê bài nộp
    
    Response:
    {
        "total_students": 30,
        "submitted_count": 25,
        "graded_count": 20,
        "average_score": 78.5,
        "submissions": [...]
    }
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_assignments',
    }
    
    def get(self, request, pk):
        teacher = request.user.teacher
        assignment = get_object_or_404(
            Assignment,
            pk=pk,
            session__class_session__teacher=teacher
        )
        
        submissions = Submission.objects.filter(assignment=assignment)
        serializer = SubmissionListSerializer(submissions, many=True)
        
        # Tính toán thống kê
        total_students = assignment.session.class_session.enrollments.filter(
            status='active'
        ).count() if hasattr(assignment.session, 'class_session') else 0
        
        stats = {
            'total_students': total_students,
            'submitted_count': submissions.count(),
            'graded_count': submissions.filter(status=Submission.Status.GRADED).count(),
            'average_score': submissions.filter(
                result__isnull=False
            ).aggregate(avg_score=Avg('result'))['avg_score'],
            'submissions': serializer.data
        }
        
        return Response(stats)


class TeacherAssignmentAnswerKeysView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/assignments/{assignment_id}/answer-keys/ - Danh sách đáp án của bài tập
    """
    serializer_class = AnswerKeySerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_assignments',
    }
    
    def get_queryset(self):
        assignment_id = self.kwargs['assignment_id']
        teacher = self.request.user.teacher
        
        # Kiểm tra teacher có quyền xem assignment này không
        assignment = get_object_or_404(
            Assignment,
            pk=assignment_id,
            session__class_session__teacher=teacher
        )
        
        return AnswerKey.objects.filter(assignment=assignment)


class TeacherAssignmentAnswerKeysCreateView(PermissionMixin, generics.CreateAPIView):
    """
    POST /api/assignments/{assignment_id}/answer-keys/ - Thêm đáp án mới vào bài tập
    """
    serializer_class = AnswerKeyCreateUpdateSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'POST': 'manage_assignments',
    }
    
    def perform_create(self, serializer):
        assignment_id = self.kwargs['assignment_id']
        teacher = self.request.user.teacher
        
        assignment = get_object_or_404(
            Assignment,
            pk=assignment_id,
            session__class_session__teacher=teacher
        )
        
        serializer.save(assignment=assignment)


# ==================== TEACHER ANSWER KEY VIEWS ====================

class TeacherAnswerKeyDetailView(PermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/answer-keys/{id}/ - Xem chi tiết đáp án
    PUT /api/answer-keys/{id}/ - Cập nhật đáp án (cần quyền: manage_assignments)
    PATCH /api/answer-keys/{id}/ - Cập nhật đáp án (cần quyền: manage_assignments)
    DELETE /api/answer-keys/{id}/ - Xóa đáp án (cần quyền: manage_assignments)
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_assignments',
        'PUT': 'manage_assignments',
        'PATCH': 'manage_assignments',
        'DELETE': 'manage_assignments',
    }
    lookup_field = 'pk'
    
    def get_queryset(self):
        # ✅ FIX: Thêm check cho Swagger
        if getattr(self, 'swagger_fake_view', False):
            return AnswerKey.objects.none()
        
        teacher = self.request.user.teacher
        return AnswerKey.objects.filter(
            assignment__session__class_session__teacher=teacher
        )
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AnswerKeySerializer
        return AnswerKeyCreateUpdateSerializer


# ==================== TEACHER SUBMISSION VIEWS ====================

class TeacherSubmissionListView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/teacher-submissions/ - Lấy danh sách bài nộp
    
    Query params:
    - assignment_id: Lọc theo bài tập (required)
    - status: Lọc theo trạng thái (submitted, graded, resubmit_required)
    """
    serializer_class = SubmissionListSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_submissions',
    }
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['submitted_at', 'result']
    ordering = ['-submitted_at']
    
    def get_queryset(self):
        teacher = self.request.user.teacher
        queryset = Submission.objects.filter(
            assignment__session__class_session__teacher=teacher
        )
        
        # Filter by assignment_id
        assignment_id = self.request.query_params.get('assignment_id')
        if assignment_id:
            queryset = queryset.filter(assignment_id=assignment_id)
        
        return queryset


class TeacherSubmissionDetailView(PermissionMixin, generics.RetrieveAPIView):
    """
    GET /api/teacher-submissions/{id}/ - Xem chi tiết bài nộp
    """
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_submissions',
    }
    lookup_field = 'pk'
    
    def get_queryset(self):
        # ✅ FIX: Thêm check cho Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Submission.objects.none()
        
        teacher = self.request.user.teacher
        return Submission.objects.filter(
            assignment__session__class_session__teacher=teacher
        )


class TeacherSubmissionGradeView(PermissionMixin, APIView):
    """
    PATCH /api/teacher-submissions/{id}/grade/ - Chấm điểm và đánh giá
    
    Request Body:
    {
        "result": 85.50,
        "content": "Bài làm tốt, cần cải thiện phần...",
        "status": "graded"
    }
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'PATCH': 'grade_submissions',
    }
    
    def patch(self, request, pk):
        teacher = request.user.teacher
        submission = get_object_or_404(
            Submission,
            pk=pk,
            assignment__session__class_session__teacher=teacher
        )
        
        serializer = SubmissionGradeSerializer(submission, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(status=Submission.Status.GRADED)
            return Response(SubmissionSerializer(submission).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherSubmissionRequestResubmitView(PermissionMixin, APIView):
    """
    PATCH /api/teacher-submissions/{id}/request-resubmit/ - Yêu cầu học viên nộp lại
    
    Request Body:
    {
        "content": "Bài làm chưa đạt yêu cầu. Vui lòng làm lại phần..."
    }
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'PATCH': 'grade_submissions',
    }
    
    def patch(self, request, pk):
        teacher = request.user.teacher
        submission = get_object_or_404(
            Submission,
            pk=pk,
            assignment__session__class_session__teacher=teacher
        )
        
        content = request.data.get('content', 'Please resubmit your assignment.')
        
        submission.status = Submission.Status.RESUBMIT_REQUIRED
        submission.content = content
        submission.save()
        
        return Response(SubmissionSerializer(submission).data)
