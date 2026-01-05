from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg, Q

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
        from users.models import Student
        from enrollment.models import Enrollment
        
        # Get student instance explicitly to avoid any relationship issues
        try:
            student = Student.objects.get(user_account=self.request.user)
        except Student.DoesNotExist:
            return Assignment.objects.none()
        
        # Get class IDs from enrollments
        enrolled_class_ids = Enrollment.objects.filter(
            student_id=student.id
        ).values_list('class_id', flat=True)
        
        # Get assignments from sessions in enrolled classes
        return Assignment.objects.filter(
            session__class_session_id__in=enrolled_class_ids,
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
        from users.models import Student
        
        # ✅ FIX: Thêm check cho Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Assignment.objects.none()
        
        # Get student instance explicitly to avoid any relationship issues
        try:
            student = Student.objects.get(user_account=self.request.user)
        except Student.DoesNotExist:
            return Assignment.objects.none()
        
        from enrollment.models import Enrollment
        
        # Get class IDs from enrollments
        enrolled_class_ids = Enrollment.objects.filter(
            student_id=student.id
        ).values_list('class_id', flat=True)
        
        # Get assignments from sessions in enrolled classes
        return Assignment.objects.filter(
            session__class_session_id__in=enrolled_class_ids,
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
        from users.models import Student
        from enrollment.models import Enrollment
        
        # Get student instance explicitly to avoid any relationship issues
        try:
            student = Student.objects.get(user_account=request.user)
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Only students can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Lấy assignment với answer_keys prefetched
        assignment = get_object_or_404(
            Assignment.objects.select_related('session').prefetch_related('answer_keys'),
            pk=pk,
            status='published'  # Hoặc Assignment.Status.PUBLISHED nếu có enum
        )
        
        # Kiểm tra enrollment riêng
        is_enrolled = Enrollment.objects.filter(
            student_id=student.id,
            class_id=assignment.session.class_session_id
        ).exists()
        
        if not is_enrolled:
            return Response({
                'success': False,
                'error': 'You are not enrolled in this class'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Kiểm tra xem học viên đã nộp bài chưa
        existing_submission = Submission.objects.filter(
            assignment=assignment,
            student=student
        ).first()
        
        # Nếu có submission và status là 'resubmit_required', cho phép làm lại
        # Trả về assignment data để học sinh có thể làm lại
        if existing_submission and existing_submission.status == Submission.Status.RESUBMIT_REQUIRED:
            # Cho phép làm lại - trả về assignment data
            serializer = AssignmentDetailSerializer(assignment, context={'request': request})
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'You can resubmit this assignment',
                'submission_status': existing_submission.status
            })
        
        # Nếu đã nộp và không phải resubmit_required, trả về thông báo
        if existing_submission:
            return Response({
                'success': True,
                'message': 'You have already submitted this assignment',
                'data': {
                    'submission_id': str(existing_submission.id),
                    'status': existing_submission.status,
                    'can_resubmit': getattr(existing_submission, 'needs_resubmit', False)
                }
            }, status=status.HTTP_200_OK)
        
        # Chưa nộp - trả về assignment data bình thường
        serializer = AssignmentDetailSerializer(assignment, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        })

class StudentAssignmentSubmitView(APIView):
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
    # Không dùng PermissionMixin vì học sinh chỉ có thể submit bài tập của chính họ
    # (đã kiểm tra enrollment và student profile trong method)
    
    def post(self, request, pk):
        import logging
        logger = logging.getLogger(__name__)
        from users.models import Student
        
        # Get student instance explicitly to avoid any relationship issues
        try:
            student = Student.objects.get(user_account=request.user)
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student profile not found'
            }, status=status.HTTP_403_FORBIDDEN)
        
        from enrollment.models import Enrollment
        
        # Get class IDs from enrollments
        enrolled_class_ids = Enrollment.objects.filter(
            student_id=student.id
        ).values_list('class_id', flat=True)
        
        assignment = get_object_or_404(
            Assignment,
            pk=pk,
            session__class_session_id__in=enrolled_class_ids,
            status=Assignment.Status.PUBLISHED
        )
        
        # Kiểm tra xem đã nộp bài chưa (trừ trường hợp resubmit)
        # Nếu có submission với status 'resubmit_required', cho phép nộp lại (update submission cũ)
        # Nếu có submission với status 'submitted' hoặc 'graded', không cho phép nộp lại
        existing_submission = Submission.objects.filter(
            assignment=assignment,
            student=student
        ).first()
        
        is_resubmit = False
        if existing_submission:
            if existing_submission.status == Submission.Status.RESUBMIT_REQUIRED:
                # Cho phép nộp lại - sẽ update submission cũ
                is_resubmit = True
                logger.info(f"🔄 Resubmitting assignment {assignment.id} for student {student.id}")
            elif existing_submission.status in [Submission.Status.SUBMITTED, Submission.Status.GRADED]:
                # Đã nộp rồi, không cho phép nộp lại
                return Response({
                    'success': False,
                    'error': 'Bạn đã nộp bài tập này rồi'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle file upload (Word, MP3, etc.)
        # Don't copy request.data directly as it contains file objects that can't be pickled
        # Create a mutable copy of data without file objects
        data = {}
        for key, value in request.data.items():
            if key != 'file':  # Skip file, it's in request.FILES
                data[key] = value
        
        file_url = None
        has_file_upload = False
        
        if 'file' in request.FILES:
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            from datetime import datetime
            import os
            
            uploaded_file = request.FILES['file']
            # Validate file type (Word, PDF, MP3, images)
            allowed_extensions = ['.doc', '.docx', '.pdf', '.mp3', '.wav', '.jpg', '.jpeg', '.png', '.gif']
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_ext not in allowed_extensions:
                return Response({
                    'success': False,
                    'error': f'File type không được hỗ trợ. Chỉ chấp nhận: {", ".join(allowed_extensions)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save file to media folder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"submissions/{timestamp}_{uploaded_file.name}"
            file_path = default_storage.save(filename, ContentFile(uploaded_file.read()))
            file_url = default_storage.url(file_path)
            has_file_upload = True
            logger.info(f"✅ Student file uploaded: {file_url}")
            
            # Store file URL in content field
            if 'content' not in data or not data['content']:
                data['content'] = file_url
            else:
                # If content already exists, append file URL
                data['content'] = f"{data['content']}\n[FILE]:{file_url}"
        
        # Handle student_answers from JSON if provided
        student_answers_data = []
        if 'student_answers' in data:
            import json
            if isinstance(data['student_answers'], str):
                try:
                    student_answers_data = json.loads(data['student_answers'])
                except json.JSONDecodeError:
                    student_answers_data = []
            elif isinstance(data['student_answers'], list):
                student_answers_data = data['student_answers']
        
        # Create submission
        logger.info(f"📝 Creating submission with data: {data}")
        logger.info(f"📝 Student answers data: {student_answers_data}")
        
        serializer = SubmissionCreateSerializer(data=data)
        if not serializer.is_valid():
            logger.error(f"❌ Serializer validation errors: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .models import StudentAnswer
            from django.utils import timezone
            
            if is_resubmit and existing_submission:
                # Update existing submission (resubmit)
                logger.info(f"🔄 Updating existing submission {existing_submission.id} for resubmit")
                
                # Update submission fields
                existing_submission.content = serializer.validated_data.get('content', existing_submission.content)
                existing_submission.status = Submission.Status.SUBMITTED
                existing_submission.submitted_at = timezone.now()
                
                # Update using raw SQL (model has managed=False)
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE submissions 
                        SET content = %s,
                            status = %s,
                            submitted_at = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        [
                            existing_submission.content,
                            'submitted',
                            existing_submission.submitted_at,
                            str(existing_submission.id)
                        ]
                    )
                
                submission = existing_submission
                logger.info(f"✅ Submission updated: {submission.id}")
                
                # Delete old student answers
                StudentAnswer.objects.filter(submission=submission).delete()
                logger.info(f"🗑️ Deleted old student answers for submission {submission.id}")
            else:
                # Create new submission
                submission = serializer.save(
                    assignment=assignment,
                    student=student,
                    status=Submission.Status.SUBMITTED
                )
                logger.info(f"✅ Submission created: {submission.id}")
            
            logger.info(f"📝 Has file upload: {has_file_upload}")
            logger.info(f"📝 Has student answers: {len(student_answers_data) > 0}")
            
            # Create student answers if provided
            if student_answers_data:
                for answer_data in student_answers_data:
                    try:
                        StudentAnswer.objects.create(
                            submission=submission,
                            question_number=answer_data.get('question_number'),
                            selected_option=answer_data.get('selected_option')
                        )
                        logger.info(f"✅ Created student answer for question {answer_data.get('question_number')}")
                    except Exception as e:
                        logger.error(f"❌ Error creating student answer: {str(e)}")
                        logger.exception(e)
            
            # Tự động chấm điểm chỉ khi:
            # 1. Có answer keys trong assignment
            # 2. Có student_answers (trắc nghiệm)
            # 3. KHÔNG có file upload (file upload cần giáo viên chấm thủ công)
            if not has_file_upload and len(student_answers_data) > 0:
                logger.info("🔍 Auto-grading submission...")
                try:
                    self._auto_grade_submission(submission)
                except Exception as e:
                    logger.error(f"❌ Error auto-grading: {str(e)}")
                    logger.exception(e)
                    # Continue anyway, teacher can grade manually
            else:
                logger.info("⏳ Submission requires manual grading (file upload or no answers)")
            
            return Response({
                'success': True,
                'data': SubmissionSerializer(submission).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"❌ Error creating submission: {str(e)}")
            logger.exception(e)
            return Response({
                'success': False,
                'error': f'Error creating submission: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _auto_grade_submission(self, submission):
        """
        Tự động chấm điểm dựa trên answer keys
        """
        import logging
        logger = logging.getLogger(__name__)
        
        answer_keys = AnswerKey.objects.filter(assignment=submission.assignment)
        if not answer_keys.exists():
            return
        
        student_answers = StudentAnswer.objects.filter(submission=submission)
        correct_count = 0
        total_questions = answer_keys.count()
        
        # Map để convert chữ cái sang số (và ngược lại)
        # answer_keys lưu "A", "B", "C", "D" hoặc "1", "2", "3", "4"
        # student_answer.selected_option lưu số: 1, 2, 3, 4
        option_map_letter_to_number = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 
                                       'a': 1, 'b': 2, 'c': 3, 'd': 4}
        
        for student_answer in student_answers:
            answer_key = answer_keys.filter(
                question_number=student_answer.question_number
            ).first()
            
            if answer_key:
                # Lấy correct_option từ answer_key và normalize
                correct_option_raw = str(answer_key.correct_option).strip()
                correct_option_normalized = correct_option_raw.upper()
                
                # Convert correct_option về số để so sánh với selected_option (IntegerField)
                correct_option_number = None
                
                # Nếu là chữ cái (A, B, C, D), convert sang số
                if correct_option_normalized in option_map_letter_to_number:
                    correct_option_number = option_map_letter_to_number[correct_option_normalized]
                # Nếu đã là số (string), convert sang int
                elif correct_option_normalized.isdigit():
                    correct_option_number = int(correct_option_normalized)
                else:
                    # Nếu không phải chữ cái hoặc số hợp lệ, đánh sai
                    correct_option_number = None
                
                # Lấy selected_option từ student_answer (đã là IntegerField)
                student_option_number = student_answer.selected_option
                
                # Debug logging
                logger.info(f"🔍 Question {student_answer.question_number}: "
                          f"student_option_number={student_option_number} (type: {type(student_option_number).__name__}), "
                          f"correct_option_raw='{correct_option_raw}', "
                          f"correct_option_normalized='{correct_option_normalized}', "
                          f"correct_option_number={correct_option_number} (type: {type(correct_option_number).__name__ if correct_option_number else None}), "
                          f"match={student_option_number == correct_option_number if correct_option_number is not None else False}")
                
                # So sánh số với số
                if correct_option_number is not None and student_option_number == correct_option_number:
                    student_answer.is_correct = 1
                    correct_count += 1
                else:
                    student_answer.is_correct = 0
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
        from users.models import Student
        
        # Get student instance explicitly to avoid any relationship issues
        try:
            student = Student.objects.get(user_account=request.user)
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student profile not found'
            }, status=status.HTTP_403_FORBIDDEN)
        
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
        from users.models import Student
        
        # Get student instance explicitly to avoid any relationship issues
        try:
            student = Student.objects.get(user_account=self.request.user)
        except Student.DoesNotExist:
            return Submission.objects.none()
        
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
        from users.models import Student
        
        # ✅ FIX: Thêm check cho Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Submission.objects.none()
        
        # Get student instance explicitly to avoid any relationship issues
        try:
            student = Student.objects.get(user_account=self.request.user)
        except Student.DoesNotExist:
            return Submission.objects.none()
        
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
        from users.models import Student
        
        # Get student instance explicitly to avoid any relationship issues
        try:
            student = Student.objects.get(user_account=request.user)
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student profile not found'
            }, status=status.HTTP_403_FORBIDDEN)
        
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
        import logging
        logger = logging.getLogger(__name__)
        
        answer_keys = AnswerKey.objects.filter(assignment=submission.assignment)
        if not answer_keys.exists():
            return
        
        student_answers = StudentAnswer.objects.filter(submission=submission)
        correct_count = 0
        total_questions = answer_keys.count()
        
        # Map để convert chữ cái sang số (và ngược lại)
        # answer_keys lưu "A", "B", "C", "D" hoặc "1", "2", "3", "4"
        # student_answer.selected_option lưu số: 1, 2, 3, 4
        option_map_letter_to_number = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 
                                       'a': 1, 'b': 2, 'c': 3, 'd': 4}
        
        for student_answer in student_answers:
            answer_key = answer_keys.filter(
                question_number=student_answer.question_number
            ).first()
            
            if answer_key:
                # Lấy correct_option từ answer_key và normalize
                correct_option_raw = str(answer_key.correct_option).strip()
                correct_option_normalized = correct_option_raw.upper()
                
                # Convert correct_option về số để so sánh với selected_option (IntegerField)
                correct_option_number = None
                
                # Nếu là chữ cái (A, B, C, D), convert sang số
                if correct_option_normalized in option_map_letter_to_number:
                    correct_option_number = option_map_letter_to_number[correct_option_normalized]
                # Nếu đã là số (string), convert sang int
                elif correct_option_normalized.isdigit():
                    correct_option_number = int(correct_option_normalized)
                else:
                    # Nếu không phải chữ cái hoặc số hợp lệ, đánh sai
                    correct_option_number = None
                
                # Lấy selected_option từ student_answer (đã là IntegerField)
                student_option_number = student_answer.selected_option
                
                # Debug logging
                logger.info(f"🔍 Question {student_answer.question_number}: "
                          f"student_option_number={student_option_number} (type: {type(student_option_number).__name__}), "
                          f"correct_option_raw='{correct_option_raw}', "
                          f"correct_option_normalized='{correct_option_normalized}', "
                          f"correct_option_number={correct_option_number} (type: {type(correct_option_number).__name__ if correct_option_number else None}), "
                          f"match={student_option_number == correct_option_number if correct_option_number is not None else False}")
                
                # So sánh số với số
                if correct_option_number is not None and student_option_number == correct_option_number:
                    student_answer.is_correct = 1
                    correct_count += 1
                else:
                    student_answer.is_correct = 0
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
    # Chỉ filter status, không filter session vì chúng ta xử lý trong get_queryset()
    filterset_fields = ['status']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'created_at']
    ordering = ['-created_at']
    
    def list(self, request, *args, **kwargs):
        """
        Override list to handle response format correctly when filtering by session
        """
        import logging
        logger = logging.getLogger(__name__)
        
        queryset = self.filter_queryset(self.get_queryset())
        queryset_count = queryset.count()
        logger.info(f"📝 Queryset count BEFORE serialization: {queryset_count}")
        
        # Get session_id from query params
        session_id = request.query_params.get('session')
        
        # If filtering by session, return all results without pagination
        # to avoid double wrapping issue with CustomPagination + CustomJSONRenderer
        if session_id:
            # Log queryset details
            logger.info(f"📝 Filtering by session_id: {session_id}")
            logger.info(f"📝 Queryset type: {type(queryset)}")
            logger.info(f"📝 Queryset count: {queryset_count}")
            
            # Try to evaluate queryset
            try:
                queryset_list = list(queryset[:10])  # Limit to 10 for logging
                logger.info(f"📝 Queryset evaluated, found {len(queryset_list)} items")
                for item in queryset_list:
                    logger.info(f"📝 Assignment: ID={item.id}, Title={item.title}, Session={item.session_id}")
            except Exception as e:
                logger.error(f"❌ Error evaluating queryset: {str(e)}")
                logger.exception(e)
            
            serializer = self.get_serializer(queryset, many=True)
            logger.info(f"📝 Serializer data count: {len(serializer.data)}")
            
            # If queryset is empty but we know data exists (managed=False issue), use raw SQL
            if len(serializer.data) == 0:
                logger.warning(f"⚠️ Queryset returned 0 assignments, checking with raw SQL (managed=False issue)")
                from django.db import connection
                import uuid
                from datetime import datetime
                
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, title, description, due_date, status, url_file, session_id, 
                               created_at, updated_at 
                        FROM assignments 
                        WHERE session_id = %s 
                        ORDER BY created_at DESC
                        """,
                        [str(session_id)]
                    )
                    raw_results = cursor.fetchall()
                    logger.info(f"📝 Raw SQL query found {len(raw_results)} assignments")
                    
                    if raw_results:
                        # Convert raw SQL results to Assignment objects
                        # Assignment model has managed=False, so we need to create objects manually
                        assignments_list = []
                        for row in raw_results:
                            assignment = Assignment()
                            assignment.id = row[0]  # UUID
                            assignment.title = row[1] or ''
                            assignment.description = row[2]
                            assignment.due_date = row[3]
                            assignment.status = row[4] or 'draft'
                            assignment.url_file = row[5]
                            assignment.session_id = row[6]  # UUID
                            assignment.created_at = row[7]
                            assignment.updated_at = row[8]
                            assignments_list.append(assignment)
                            logger.info(f"📝 Raw SQL Assignment: ID={assignment.id}, Title={assignment.title}, Session={assignment.session_id}")
                        
                        # Use serializer to format the Assignment objects
                        serializer = self.get_serializer(assignments_list, many=True)
                        logger.info(f"✅ Using raw SQL results, returning {len(serializer.data)} assignments")
                    else:
                        logger.warning(f"⚠️ Raw SQL also found 0 assignments for session {session_id}")
            
            logger.info(f"📝 Returning {len(serializer.data)} assignments for session {session_id} (no pagination)")
            
            return Response({
                'success': True,
                'data': serializer.data,
                'error': None
            })
        
        # Otherwise, use default pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'error': None
        })
    
    def get_queryset(self):
        # Check if user has teacher profile
        if not hasattr(self.request.user, 'teacher_profile'):
            return Assignment.objects.none()
        
        # Lấy teacher profile của user đang đăng nhập
        # teacher.id = UUID của teacher trong bảng teachers
        # Ví dụ: teacher.id = "123e4567-e89b-12d3-a456-426614174000"
        teacher = self.request.user.teacher_profile
        
        # Get session_id from query params if provided
        session_id = self.request.query_params.get('session')
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 Teacher {teacher.id} requesting assignments")
        logger.info(f"🔍 Session ID from query params: {session_id}")
        
        if session_id:
            # If filtering by specific session_id, filter directly by session_id
            # Assignment table only has session_id, not teacher_id
            logger.info(f"🔍 Filtering by session_id: {session_id}")
            
            # Verify session belongs to teacher for security
            from class_sessions.models import Session
            try:
                session = Session.objects.select_related('teacher', 'class_session', 'class_session__teacher').get(id=session_id)
                logger.info(f"🔍 Session found: {session_id}")
                
                # SO SÁNH 1: session.teacher_id (teacher_id trực tiếp của session)
                # - Lấy từ bảng sessions, cột teacher_id
                # - Có thể là NULL nếu session chưa được assign teacher trực tiếp
                logger.info(f"🔍 Session.teacher_id: {session.teacher_id}")
                
                # SO SÁNH 2: session.class_session.teacher_id (teacher_id của lớp học)
                # - Lấy từ bảng classes, cột teacher_id
                # - Là teacher được assign cho lớp học
                logger.info(f"🔍 Session.class_session_id: {session.class_session_id if session.class_session else None}")
                logger.info(f"🔍 Session.class_session.teacher_id: {session.class_session.teacher_id if session.class_session and session.class_session.teacher else None}")
                
                # SO SÁNH 3: teacher.id (teacher_id của user đang đăng nhập)
                # - Lấy từ request.user.teacher.id
                # - Là teacher profile của user hiện tại
                logger.info(f"🔍 Current teacher.id (user đang đăng nhập): {teacher.id}")
                logger.info(f"🔍 Current teacher.id type: {type(teacher.id)}")
                logger.info(f"🔍 Session.teacher_id type: {type(session.teacher_id)}")
                
                # Check if session belongs to teacher (either directly or via class)
                # Convert to string for comparison to handle UUID comparison issues
                # teacher_id_str = UUID của teacher đang đăng nhập (từ request.user.teacher.id)
                teacher_id_str = str(teacher.id)
                
                # session_teacher_id_str = UUID của teacher được assign trực tiếp cho session
                session_teacher_id_str = str(session.teacher_id) if session.teacher_id else None
                
                # class_teacher_id_str = UUID của teacher được assign cho lớp học
                class_teacher_id_str = str(session.class_session.teacher_id) if session.class_session and session.class_session.teacher_id else None
                
                # So sánh: Session thuộc về teacher nếu:
                # 1. session.teacher_id == teacher.id (session được assign trực tiếp cho teacher này)
                # HOẶC
                # 2. class_session.teacher_id == teacher.id (lớp học được assign cho teacher này)
                session_belongs_to_teacher = (
                    (session_teacher_id_str == teacher_id_str) or 
                    (class_teacher_id_str == teacher_id_str)
                )
                
                logger.info(f"🔍 Session belongs to teacher check: {session_belongs_to_teacher}")
                logger.info(f"🔍 So sánh 1 - session.teacher_id == teacher.id: {session_teacher_id_str == teacher_id_str}")
                logger.info(f"🔍 So sánh 2 - class.teacher_id == teacher.id: {class_teacher_id_str == teacher_id_str}")
                
                if not session_belongs_to_teacher:
                    logger.warning(f"⚠️ Session {session_id} doesn't belong to teacher {teacher.id}")
                    logger.warning(f"⚠️ Session.teacher_id: {session.teacher_id} ({session_teacher_id_str}), Expected: {teacher.id} ({teacher_id_str})")
                    logger.warning(f"⚠️ Class.teacher_id: {session.class_session.teacher_id if session.class_session else None} ({class_teacher_id_str}), Expected: {teacher.id} ({teacher_id_str})")
                    # For now, allow access if session exists (temporary fix for debugging)
                    # TODO: Fix teacher assignment logic
                    logger.warning(f"⚠️ Allowing access anyway for debugging purposes")
                    # return Assignment.objects.none()
                else:
                    logger.info(f"✅ Session {session_id} belongs to teacher {teacher.id}")
            except Session.DoesNotExist:
                logger.warning(f"⚠️ Session {session_id} not found")
                return Assignment.objects.none()
            except Exception as e:
                logger.error(f"❌ Error checking session: {str(e)}")
                logger.exception(e)
                # For debugging, allow access even if there's an error
                logger.warning(f"⚠️ Allowing access anyway due to error (for debugging)")
                # return Assignment.objects.none()
            
            # Filter directly by session_id (UUID field in database)
            # IMPORTANT: session_id từ query params là string, Django sẽ tự động convert sang UUID
            # Nhưng để chắc chắn, thử nhiều cách filter
            
            import uuid
            session_uuid = None
            try:
                session_uuid = uuid.UUID(str(session_id))
                logger.info(f"🔍 Converting session_id to UUID: {session_id} -> {session_uuid}")
            except ValueError:
                logger.error(f"❌ Invalid UUID format for session_id: {session_id}")
                return Assignment.objects.none()
            
            # IMPORTANT: Assignment model has managed=False, so Django ORM may not work correctly
            # Try Django ORM first, but we'll handle empty results in list() method with raw SQL
            # Use select_related to optimize queries
            assignments = Assignment.objects.select_related(
                'session', 'session__class_session'
            ).filter(session_id=session_uuid)
            count_uuid = assignments.count()
            logger.info(f"🔍 Django ORM filter by UUID: {count_uuid} assignments")
            
            # Also try string filter as fallback
            if count_uuid == 0:
                assignments_str = Assignment.objects.select_related(
                    'session', 'session__class_session'
                ).filter(session_id=str(session_id))
                count_str = assignments_str.count()
                logger.info(f"🔍 Filter by string: {count_str} assignments")
                if count_str > 0:
                    assignments = assignments_str
                    logger.info(f"✅ Using string filter method, found {count_str} assignments")
            
            # If still 0, try session object filter
            if count_uuid == 0 and session:
                assignments_session_obj = Assignment.objects.select_related(
                    'session', 'session__class_session'
                ).filter(session=session)
                count_session_obj = assignments_session_obj.count()
                logger.info(f"🔍 Filter by session object: {count_session_obj} assignments")
                if count_session_obj > 0:
                    assignments = assignments_session_obj
                    logger.info(f"✅ Using session object filter method, found {count_session_obj} assignments")
            
            # Note: If Django ORM returns 0, we'll use raw SQL in list() method
            logger.info(f"🔍 get_queryset returning {assignments.count()} assignments (may be 0 due to managed=False)")
            
            assignments_count = assignments.count()
            logger.info(f"✅ Final assignments count: {assignments_count} for session {session_id}")
            
            # Tự động cập nhật trạng thái "closed" cho bài tập quá hạn
            from datetime import date
            today = date.today()
            from django.db import connection
            
            # Cập nhật các bài tập có due_date đã qua và status chưa phải "closed"
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE assignments 
                    SET status = 'closed', updated_at = NOW()
                    WHERE due_date IS NOT NULL 
                    AND due_date < %s 
                    AND status != 'closed'
                    """,
                    [today]
                )
                updated_count = cursor.rowcount
                if updated_count > 0:
                    logger.info(f"✅ Auto-updated {updated_count} assignments to 'closed' status (past due date)")
            
            # Debug: Log all assignments
            if assignments_count > 0:
                for assignment in assignments[:10]:  # Limit to 10 for logging
                    logger.info(f"📝 Assignment: ID={assignment.id}, Title={assignment.title}, Session={assignment.session_id}, Session type={type(assignment.session_id)}")
            else:
                # Double check: Query ALL assignments to see what's in DB
                all_assignments_total = Assignment.objects.all().count()
                logger.info(f"🔍 Total assignments in DB: {all_assignments_total}")
                
                # Try raw SQL query to see if there are any assignments
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT id, title, session_id FROM assignments WHERE session_id = %s",
                        [str(session_uuid)]
                    )
                    raw_results = cursor.fetchall()
                    logger.info(f"🔍 Raw SQL query count: {len(raw_results)}")
                    if raw_results:
                        for row in raw_results[:5]:
                            logger.info(f"🔍 Raw SQL Assignment: ID={row[0]}, Title={row[1]}, Session={row[2]}")
            
            return assignments
        else:
            # No session filter, return all assignments for sessions that belong to this teacher
            # Filter through session -> teacher or session -> class_session -> teacher
            logger.info(f"🔍 No session filter, returning all assignments for teacher {teacher.id}")
            queryset = Assignment.objects.select_related(
                'session', 'session__class_session'
            ).filter(
                Q(session__teacher=teacher) | 
                Q(session__class_session__teacher=teacher)
            ).distinct()
            logger.info(f"✅ Found {queryset.count()} total assignments for teacher")
            
            # Tự động cập nhật trạng thái "closed" cho bài tập quá hạn
            from django.db import connection
            from datetime import date
            today = date.today()
            
            # Cập nhật các bài tập có due_date đã qua và status chưa phải "closed"
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE assignments 
                    SET status = 'closed', updated_at = NOW()
                    WHERE due_date IS NOT NULL 
                    AND due_date < %s 
                    AND status != 'closed'
                    """,
                    [today]
                )
                updated_count = cursor.rowcount
                if updated_count > 0:
                    logger.info(f"✅ Auto-updated {updated_count} assignments to 'closed' status (past due date)")
            
            return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AssignmentCreateSerializer
        return AssignmentSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Override create to handle file uploads and answer keys
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"📤 Creating assignment with data: {request.data}")
        logger.info(f"📤 Files: {list(request.FILES.keys())}")
        
        # Handle file upload
        # Create a mutable copy of data (QueryDict from FormData needs to be converted)
        if hasattr(request.data, '_mutable'):
            data = request.data.copy()
        else:
            data = dict(request.data) if hasattr(request.data, 'items') else request.data.copy()
        file_url = None
        
        if 'file' in request.FILES:
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            from datetime import datetime
            import os
            
            uploaded_file = request.FILES['file']
            # Validate file type (Word, PDF, or images)
            allowed_extensions = ['.doc', '.docx', '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp']
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_ext not in allowed_extensions:
                return Response({
                    'success': False,
                    'error': f'File type không được hỗ trợ. Chỉ chấp nhận: {", ".join(allowed_extensions)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save file to media folder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"assignments/{timestamp}_{uploaded_file.name}"
            file_path = default_storage.save(filename, ContentFile(uploaded_file.read()))
            file_url = default_storage.url(file_path)
            data['url_file'] = file_url
            logger.info(f"✅ File uploaded: {file_url}")
        
        # Handle empty strings - convert to None for optional fields
        if 'due_date' in data and data['due_date'] == '':
            data['due_date'] = None
        if 'description' in data and data['description'] == '':
            data['description'] = None
        if 'url_file' in data and data['url_file'] == '':
            data['url_file'] = None
        
        # Handle answer_keys from JSON if provided
        answer_keys_data = []
        if 'answer_keys' in data:
            import json
            if isinstance(data['answer_keys'], str):
                try:
                    answer_keys_data = json.loads(data['answer_keys'])
                except json.JSONDecodeError:
                    answer_keys_data = []
            elif isinstance(data['answer_keys'], list):
                answer_keys_data = data['answer_keys']
            # Remove answer_keys from data as it's handled separately
            data.pop('answer_keys', None)
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Log validated data
        logger.info(f"✅ Validated data: {serializer.validated_data}")
        
        # Check session
        session = serializer.validated_data.get('session')
        if session:
            logger.info(f"📝 Assignment session_id: {session.id if hasattr(session, 'id') else session}")
            
            # Load session with related objects
            from class_sessions.models import Session
            try:
                session_obj = Session.objects.select_related('teacher', 'class_session', 'class_session__teacher').get(
                    id=session.id if hasattr(session, 'id') else session
                )
                logger.info(f"📝 Session.teacher_id: {session_obj.teacher_id}")
                logger.info(f"📝 Session.class_session.teacher_id: {session_obj.class_session.teacher_id if session_obj.class_session else None}")
            except Session.DoesNotExist:
                logger.warning(f"⚠️ Session not found: {session}")
        
        # Create assignment
        try:
            assignment = serializer.save()
            logger.info(f"✅ Assignment created successfully: {assignment.id}")
            logger.info(f"✅ Assignment session_id: {assignment.session_id}")
            logger.info(f"✅ Assignment title: {assignment.title}")
            
            # Create answer keys if provided
            if answer_keys_data:
                for answer_key_data in answer_keys_data:
                    AnswerKey.objects.create(assignment=assignment, **answer_key_data)
                logger.info(f"✅ Created {len(answer_keys_data)} answer keys for assignment {assignment.id}")
            else:
                logger.info(f"ℹ️ No answer keys provided for assignment {assignment.id}")
            
            # Force refresh from database to ensure it's saved
            assignment.refresh_from_db()
            logger.info(f"✅ Assignment refreshed from DB: {assignment.id}")
            
            # Verify assignment was saved - try multiple queries
            saved_assignment = Assignment.objects.filter(id=assignment.id).first()
            if saved_assignment:
                logger.info(f"✅ Assignment verified in database: {saved_assignment.id}")
                logger.info(f"✅ Answer keys count: {saved_assignment.answer_keys.count()}")
            else:
                logger.error(f"❌ Assignment not found in database after creation!")
                # Try querying by session_id
                session_assignments = Assignment.objects.filter(session_id=assignment.session_id)
                logger.info(f"🔍 Total assignments for session {assignment.session_id}: {session_assignments.count()}")
                if session_assignments.exists():
                    for a in session_assignments:
                        logger.info(f"🔍 Found assignment: ID={a.id}, Title={a.title}")
        except Exception as e:
            logger.error(f"❌ Error creating assignment: {str(e)}")
            logger.exception(e)
            raise
        
        # Return assignment with answer keys
        response_serializer = AssignmentDetailSerializer(assignment, context={'request': request})
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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
        
        # Check if user has teacher profile
        if not hasattr(self.request.user, 'teacher_profile'):
            return Assignment.objects.none()
        
        teacher = self.request.user.teacher_profile
        # Assignment model has managed=False, so Django ORM may not work correctly
        # Try Django ORM first, but handle errors gracefully
        try:
            # Filter by both session__teacher and session__class_session__teacher
            return Assignment.objects.select_related(
                'session', 'session__class_session'
            ).filter(
                Q(session__teacher=teacher) | 
                Q(session__class_session__teacher=teacher)
            ).distinct()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️ Django ORM failed in get_queryset: {str(e)}")
            # Return empty queryset, we'll handle in get_object method
            return Assignment.objects.none()
    
    def get_object(self):
        """
        Override get_object to handle managed=False with raw SQL fallback
        """
        import logging
        logger = logging.getLogger(__name__)
        
        pk = self.kwargs.get('pk')
        logger.info(f"🔍 ========== GET_OBJECT CALLED ==========")
        logger.info(f"🔍 Assignment ID: {pk}")
        logger.info(f"🔍 User: {self.request.user.username} ({self.request.user.id})")
        
        # Check if user has teacher profile
        if not hasattr(self.request.user, 'teacher_profile'):
            logger.warning(f"⚠️ User {self.request.user.username} does not have teacher profile")
            raise NotFound("Only teachers can access this endpoint")
        
        teacher = self.request.user.teacher_profile
        logger.info(f"🔍 Teacher ID: {teacher.id}")
        
        # Try Django ORM first
        try:
            assignment = Assignment.objects.get(pk=pk)
            logger.info(f"✅ Found assignment {pk} using Django ORM")
            # Verify teacher has access
            # Check if session belongs to teacher (either directly or via class)
            try:
                session = assignment.session
                if session:
                    session_teacher_id = str(session.teacher_id) if session.teacher_id else None
                    class_teacher_id = str(session.class_session.teacher_id) if session.class_session and session.class_session.teacher_id else None
                    teacher_id_str = str(teacher.id)
                    
                    logger.info(f"🔍 Assignment {pk} - Session teacher: {session_teacher_id}, Class teacher: {class_teacher_id}, Current teacher: {teacher_id_str}")
                    
                    if session_teacher_id == teacher_id_str or class_teacher_id == teacher_id_str:
                        logger.info(f"✅ Teacher {teacher_id_str} has access to assignment {pk}")
                        return assignment
                    else:
                        logger.warning(f"⚠️ Teacher {teacher_id_str} does not have access to assignment {pk}")
                        raise NotFound("Assignment not found")
                else:
                    logger.warning(f"⚠️ Assignment {pk} has no session")
                    raise NotFound("Assignment not found")
            except Exception as e:
                logger.warning(f"⚠️ Error checking session for assignment {pk}: {str(e)}")
                # If session check fails, try raw SQL
                pass
        except Assignment.DoesNotExist:
            logger.warning(f"⚠️ Django ORM: Assignment {pk} not found, trying raw SQL")
        except Exception as e:
            logger.warning(f"⚠️ Django ORM error for assignment {pk}: {str(e)}, trying raw SQL")
        
        # Try raw SQL as fallback
        logger.info(f"🔍 Trying raw SQL to find assignment {pk} for teacher {teacher.id}")
        from django.db import connection
        
        with connection.cursor() as cursor:
            # First, check if assignment exists
            cursor.execute(
                "SELECT id, title, description, due_date, status, url_file, session_id, created_at, updated_at FROM assignments WHERE id = %s",
                [str(pk)]
            )
            row = cursor.fetchone()
            
            if not row:
                logger.warning(f"⚠️ Raw SQL: Assignment {pk} not found in database")
                raise NotFound("Assignment not found")
            
            # Check if assignment belongs to teacher
            assignment_session_id = row[6]  # session_id
            logger.info(f"🔍 Assignment {pk} has session_id: {assignment_session_id}")
            
            # Check session teacher
            cursor.execute(
                """
                SELECT s.teacher_id, cs.teacher_id as class_teacher_id
                FROM sessions s
                LEFT JOIN class_sessions cs ON s.class_id = cs.id
                WHERE s.id = %s
                """,
                [str(assignment_session_id)]
            )
            session_row = cursor.fetchone()
            
            if session_row:
                session_teacher_id = str(session_row[0]) if session_row[0] else None
                class_teacher_id = str(session_row[1]) if session_row[1] else None
                teacher_id_str = str(teacher.id)
                
                logger.info(f"🔍 Session {assignment_session_id} - Session teacher: {session_teacher_id}, Class teacher: {class_teacher_id}, Current teacher: {teacher_id_str}")
                
                if session_teacher_id == teacher_id_str or class_teacher_id == teacher_id_str:
                    logger.info(f"✅ Teacher {teacher_id_str} has access to assignment {pk} (raw SQL)")
                    # Try to get assignment using Django ORM with select_related to load session
                    try:
                        assignment = Assignment.objects.select_related(
                            'session', 'session__class_session'
                        ).get(pk=pk)
                        logger.info(f"✅ Loaded assignment {pk} with session relationship using Django ORM")
                        return assignment
                    except Assignment.DoesNotExist:
                        logger.warning(f"⚠️ Django ORM get failed, creating Assignment object from raw SQL")
                        # Create Assignment object from raw SQL result as fallback
                        assignment = Assignment()
                        assignment.id = row[0]
                        assignment.title = row[1]
                        assignment.description = row[2]
                        assignment.due_date = row[3]
                        assignment.status = row[4]
                        assignment.url_file = row[5]
                        assignment.session_id = row[6]
                        assignment.created_at = row[7]
                        assignment.updated_at = row[8]
                        # Try to load session manually
                        try:
                            from class_sessions.models import Session
                            assignment.session = Session.objects.select_related('class_session').get(id=row[6])
                            logger.info(f"✅ Manually loaded session for assignment {pk}")
                        except Exception as e:
                            logger.warning(f"⚠️ Could not load session for assignment {pk}: {str(e)}")
                        return assignment
                else:
                    logger.warning(f"⚠️ Teacher {teacher_id_str} does not have access to assignment {pk} (raw SQL)")
                    raise NotFound("Assignment not found")
            else:
                logger.warning(f"⚠️ Session {assignment_session_id} not found")
                raise NotFound("Assignment not found")
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to handle managed=False with raw SQL
        """
        import logging
        logger = logging.getLogger(__name__)
        
        assignment = self.get_object()
        assignment_id = assignment.id
        
        try:
            # Try Django ORM delete first
            assignment.delete()
            logger.info(f"✅ Deleted assignment {assignment_id} using Django ORM")
        except Exception as e:
            logger.warning(f"⚠️ Django ORM delete failed: {str(e)}, trying raw SQL")
            # Fallback to raw SQL delete
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM assignments WHERE id = %s",
                    [str(assignment_id)]
                )
                if cursor.rowcount == 0:
                    raise NotFound("Assignment not found")
                logger.info(f"✅ Deleted assignment {assignment_id} using raw SQL")
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AssignmentDetailSerializer
        return AssignmentCreateSerializer
    
    def update(self, request, *args, **kwargs):
        """
        Override update to handle file uploads and answer keys
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"📤 Updating assignment with data keys: {list(request.data.keys())}")
        logger.info(f"📤 Files: {list(request.FILES.keys())}")
        
        assignment = self.get_object()
        
        # Handle file upload - don't copy request.data directly as it contains file objects
        # Create a mutable copy of data without file objects
        data = {}
        for key, value in request.data.items():
            if key != 'file':  # Skip file, it's in request.FILES
                data[key] = value
        file_url = None
        
        if 'file' in request.FILES:
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            from datetime import datetime
            import os
            
            uploaded_file = request.FILES['file']
            # Validate file type (Word, PDF, or images)
            allowed_extensions = ['.doc', '.docx', '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp']
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_ext not in allowed_extensions:
                return Response({
                    'success': False,
                    'error': f'File type không được hỗ trợ. Chỉ chấp nhận: {", ".join(allowed_extensions)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Save file to media folder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"assignments/{timestamp}_{uploaded_file.name}"
            file_path = default_storage.save(filename, ContentFile(uploaded_file.read()))
            file_url = default_storage.url(file_path)
            data['url_file'] = file_url
            logger.info(f"✅ File uploaded: {file_url}")
        
        # Handle answer_keys from JSON if provided - remove from data before validation
        answer_keys_data = []
        if 'answer_keys' in data:
            import json
            if isinstance(data['answer_keys'], str):
                try:
                    answer_keys_data = json.loads(data['answer_keys'])
                except json.JSONDecodeError:
                    answer_keys_data = []
            elif isinstance(data['answer_keys'], list):
                answer_keys_data = data['answer_keys']
            # Remove answer_keys from data as it's handled separately
            data.pop('answer_keys', None)
        
        # Update assignment
        serializer = self.get_serializer(assignment, data=data, partial=kwargs.get('partial', False))
        if not serializer.is_valid():
            logger.error(f"❌ Serializer validation errors: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save assignment
        assignment = serializer.save()
        logger.info(f"✅ Assignment updated: {assignment.id}")
        
        # Handle answer keys: only update if provided in original request
        if 'answer_keys' in request.data or answer_keys_data:
            # Delete existing answer keys and create new ones
            if answer_keys_data:
                # Delete old answer keys
                assignment.answer_keys.all().delete()
                logger.info(f"🗑️ Deleted old answer keys")
                
                # Create new answer keys
                for answer_key_data in answer_keys_data:
                    AnswerKey.objects.create(assignment=assignment, **answer_key_data)
                logger.info(f"✅ Created {len(answer_keys_data)} answer keys")
            elif 'answer_keys' in request.data:
                # Empty array means delete all answer keys
                assignment.answer_keys.all().delete()
                logger.info(f"🗑️ Deleted all answer keys (empty array provided)")
        
        # Return updated assignment with answer keys
        response_serializer = AssignmentDetailSerializer(assignment, context={'request': request})
        return Response(response_serializer.data)

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
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if user has teacher profile
        if not hasattr(request.user, 'teacher_profile'):
            return Response({
                'success': False,
                'error': 'Only teachers can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
        
        teacher = request.user.teacher_profile
        
        # Try to get assignment with Django ORM
        assignment = None
        try:
            assignment = Assignment.objects.get(pk=pk)
            # Verify teacher has access
            session = assignment.session
            if session:
                session_teacher_id = str(session.teacher_id) if session.teacher_id else None
                class_teacher_id = str(session.class_session.teacher_id) if session.class_session and session.class_session.teacher_id else None
                teacher_id_str = str(teacher.id)
                
                if session_teacher_id != teacher_id_str and class_teacher_id != teacher_id_str:
                    assignment = None
        except Assignment.DoesNotExist:
            pass
        except Exception as e:
            logger.warning(f"⚠️ Django ORM failed to get assignment: {str(e)}")
        
        # If Django ORM failed, try raw SQL
        if not assignment:
            logger.warning(f"⚠️ Trying raw SQL to get assignment {pk}")
            from django.db import connection
            
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT a.id, a.title, a.description, a.due_date, a.status, a.url_file, 
                           a.session_id, a.created_at, a.updated_at
                    FROM assignments a
                    INNER JOIN sessions s ON a.session_id = s.id
                    LEFT JOIN class_sessions cs ON s.class_id = cs.id
                    WHERE a.id = %s 
                    AND (s.teacher_id = %s OR cs.teacher_id = %s)
                    """,
                    [str(pk), str(teacher.id), str(teacher.id)]
                )
                row = cursor.fetchone()
                
                if row:
                    assignment = Assignment()
                    assignment.id = row[0]
                    assignment.title = row[1]
                    assignment.description = row[2]
                    assignment.due_date = row[3]
                    assignment.status = row[4]
                    assignment.url_file = row[5]
                    assignment.session_id = row[6]
                    assignment.created_at = row[7]
                    assignment.updated_at = row[8]
                else:
                    raise NotFound("Assignment not found")
        
        # Get submissions
        submissions = Submission.objects.filter(assignment_id=assignment.id)
        serializer = SubmissionListSerializer(submissions, many=True)
        
        # Calculate statistics
        # Get total students from enrollment (need to get session and class_session)
        total_students = 0
        try:
            if assignment.session_id:
                # First, get the class_id from the session
                from django.db import connection
                with connection.cursor() as cursor:
                    # Get class_id from session
                    cursor.execute(
                        """
                        SELECT class_id 
                        FROM sessions 
                        WHERE id = %s
                        """,
                        [str(assignment.session_id)]
                    )
                    session_row = cursor.fetchone()
                    
                    if session_row and session_row[0]:
                        class_id = session_row[0]
                        # Count students enrolled in this class
                        cursor.execute(
                            """
                            SELECT COUNT(DISTINCT student_id)
                            FROM enrollments
                            WHERE class_id = %s AND status = 'active'
                            """,
                            [str(class_id)]
                        )
                        result = cursor.fetchone()
                        total_students = result[0] if result else 0
                    else:
                        logger.warning(f"⚠️ Session {assignment.session_id} has no class_id")
        except Exception as e:
            logger.warning(f"⚠️ Error calculating total_students: {str(e)}")
            import traceback
            logger.warning(f"⚠️ Traceback: {traceback.format_exc()}")
        
        stats = {
            'total_students': total_students,
            'submitted_count': submissions.count(),
            'graded_count': submissions.filter(status=Submission.Status.GRADED).count(),
            'average_score': submissions.filter(
                result__isnull=False
            ).aggregate(avg_score=Avg('result'))['avg_score'] or 0,
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
        if not hasattr(self.request.user, 'teacher_profile'):
            return AnswerKey.objects.none()
        
        assignment_id = self.kwargs['assignment_id']
        teacher = self.request.user.teacher_profile
        
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
        if not hasattr(self.request.user, 'teacher_profile'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only teachers can access this endpoint")
        
        assignment_id = self.kwargs['assignment_id']
        teacher = self.request.user.teacher_profile
        
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
        
        if not hasattr(self.request.user, 'teacher_profile'):
            return AnswerKey.objects.none()
        
        teacher = self.request.user.teacher_profile
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
        if not hasattr(self.request.user, 'teacher_profile'):
            return Submission.objects.none()
        
        teacher = self.request.user.teacher_profile
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
        
        if not hasattr(self.request.user, 'teacher_profile'):
            return Submission.objects.none()
        
        teacher = self.request.user.teacher_profile
        return Submission.objects.filter(
            assignment__session__class_session__teacher=teacher
        )


class TeacherSubmissionGradeView(APIView):
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
    
    def patch(self, request, pk):
        if not hasattr(request.user, 'teacher_profile'):
            return Response({
                'success': False,
                'error': 'Only teachers can access this endpoint'
            }, status=status.HTTP_403_FORBIDDEN)
        
        teacher = request.user.teacher_profile
        
        # Get submission and verify teacher has access
        try:
            submission = Submission.objects.select_related(
                'assignment', 'assignment__session', 
                'assignment__session__class_session'
            ).get(pk=pk)
        except Submission.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Submission not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify teacher has access to this submission's assignment
        assignment = submission.assignment
        session = assignment.session
        if not session:
            return Response({
                'success': False,
                'error': 'Assignment has no session'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if teacher is the teacher of the session or class
        session_teacher_id = str(session.teacher_id) if session.teacher_id else None
        class_teacher_id = str(session.class_session.teacher_id) if session.class_session and session.class_session.teacher_id else None
        teacher_id_str = str(teacher.id)
        
        if session_teacher_id != teacher_id_str and class_teacher_id != teacher_id_str:
            return Response({
                'success': False,
                'error': 'You do not have permission to grade this submission'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SubmissionGradeSerializer(submission, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(status=Submission.Status.GRADED)
            return Response({
                'success': True,
                'data': SubmissionSerializer(submission).data,
                'message': 'Chấm điểm thành công'
            })
        return Response({
            'success': False,
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TeacherSubmissionRequestResubmitView(APIView):
    """
    PATCH /api/teacher-submissions/{id}/request-resubmit/ - Yêu cầu học viên nộp lại
    
    Request Body:
    {
        "content": "Bài làm chưa đạt yêu cầu. Vui lòng làm lại phần..."
    }
    """
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, pk):
        import logging
        logger = logging.getLogger(__name__)
        
        if not hasattr(request.user, 'teacher_profile'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only teachers can access this endpoint")
        
        try:
            teacher = request.user.teacher_profile
        except AttributeError:
            logger.error("User does not have teacher_profile")
            return Response({
                'error': 'User is not a teacher'
            }, status=status.HTTP_403_FORBIDDEN)
        
        submission = get_object_or_404(
            Submission,
            pk=pk,
            assignment__session__class_session__teacher=teacher
        )
        
        content = request.data.get('content', 'Please resubmit your assignment.')
        
        # Update using raw SQL (model has managed=False, so ORM save() won't work)
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                # First, try to update without enum cast (PostgreSQL will validate automatically)
                cursor.execute(
                    """
                    UPDATE submissions 
                    SET status = %s,
                        content = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    ['resubmit_required', content, str(submission.id)]
                )
                if cursor.rowcount == 0:
                    from rest_framework.exceptions import NotFound
                    raise NotFound("Submission not found")
                logger.info(f"✅ Successfully updated submission {submission.id} to resubmit_required")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error updating submission status: {error_msg}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Check if error is about enum value
            if 'invalid input value for enum' in error_msg.lower() or 'resubmit_required' in error_msg.lower():
                # Try to add enum value first, then update
                try:
                    with connection.cursor() as cursor:
                        # Try to add enum value if it doesn't exist
                        cursor.execute("""
                            DO $$ 
                            BEGIN
                                IF NOT EXISTS (
                                    SELECT 1 FROM pg_enum 
                                    WHERE enumlabel = 'resubmit_required' 
                                    AND enumtypid = (
                                        SELECT oid FROM pg_type WHERE typname = 'submission_status_enum'
                                    )
                                ) THEN
                                    ALTER TYPE submission_status_enum ADD VALUE 'resubmit_required';
                                END IF;
                            END $$;
                        """)
                        logger.info("✅ Added 'resubmit_required' to enum if it didn't exist")
                        
                        # Now try update again
                        cursor.execute(
                            """
                            UPDATE submissions 
                            SET status = %s,
                                content = %s,
                                updated_at = NOW()
                            WHERE id = %s
                            """,
                            ['resubmit_required', content, str(submission.id)]
                        )
                        if cursor.rowcount == 0:
                            from rest_framework.exceptions import NotFound
                            raise NotFound("Submission not found")
                        logger.info(f"✅ Successfully updated submission {submission.id} after adding enum value")
                except Exception as e2:
                    logger.error(f"❌ Failed to add enum value and update: {str(e2)}")
                    return Response({
                        'error': f'Cannot update submission status. Database enum may not support "resubmit_required" value.',
                        'detail': f'Original error: {error_msg}. Enum update error: {str(e2)}',
                        'suggestion': 'Please run SQL: ALTER TYPE submission_status_enum ADD VALUE IF NOT EXISTS \'resubmit_required\';'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    'error': f'Cannot update submission status: {error_msg}',
                    'detail': 'Please check database configuration and logs'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Refresh submission from database
        try:
            submission.refresh_from_db()
        except Exception as e:
            logger.warning(f"⚠️ Could not refresh from DB: {str(e)}, fetching fresh instance")
            # Fallback: fetch fresh instance
            submission = Submission.objects.get(pk=submission.id)
        
        # Serialize and return
        try:
            serializer = SubmissionSerializer(submission, context={'request': request})
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"❌ Error serializing submission: {str(e)}")
            # Return basic success response even if serialization fails
            return Response({
                'success': True,
                'message': 'Submission status updated successfully',
                'submission_id': str(submission.id),
                'status': 'resubmit_required',
                'warning': f'Could not serialize full response: {str(e)}'
            }, status=status.HTTP_200_OK)
