from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from authentication.permissions import PermissionMixin
from users.models import Student
from .models import StudentCertificate
from .serializers import (
    StudentCertificateSerializer,
    StudentCertificateCreateSerializer,
    PlacementTestResultSerializer,
    ProficiencyProfileSerializer
)
from .ocr_utils import verify_certificate_with_ocr


class ProficiencyProfileView(PermissionMixin, APIView):
    """
    GET /api/proficiency/profile/ - Lấy hồ sơ năng lực tiếng Anh của học viên
    
    Trả về:
    - current_lr: Chứng chỉ LR hiện tại (VERIFIED và còn hạn)
    - current_sw: Chứng chỉ SW hiện tại (VERIFIED và còn hạn)
    - history: Lịch sử các chứng chỉ đã VERIFIED
    - can_take_placement_test_lr: Có thể làm placement test LR không
    - can_take_placement_test_sw: Có thể làm placement test SW không
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'manage_proficiency_profile',
    }
    
    def get(self, request):
        # Kiểm tra user có student profile không
        if not hasattr(request.user, 'student_profile'):
            return Response({
                'success': False,
                'error': 'Chỉ học viên mới có thể truy cập chức năng này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        student = request.user.student_profile
        today = timezone.now().date()
        
        # Lấy năng lực hiện tại (VERIFIED và còn hạn)
        current_lr = StudentCertificate.objects.filter(
            student=student,
            skill_group=StudentCertificate.SkillGroup.LR,
            status=StudentCertificate.Status.VERIFIED,
            expired_date__gte=today
        ).order_by('-test_date').first()
        
        current_sw = StudentCertificate.objects.filter(
            student=student,
            skill_group=StudentCertificate.SkillGroup.SW,
            status=StudentCertificate.Status.VERIFIED,
            expired_date__gte=today
        ).order_by('-test_date').first()
        
        # Lấy chứng chỉ PENDING (đang chờ duyệt) để hiển thị
        pending_lr = StudentCertificate.objects.filter(
            student=student,
            skill_group=StudentCertificate.SkillGroup.LR,
            status=StudentCertificate.Status.PENDING
        ).order_by('-created_at').first()
        
        pending_sw = StudentCertificate.objects.filter(
            student=student,
            skill_group=StudentCertificate.SkillGroup.SW,
            status=StudentCertificate.Status.PENDING
        ).order_by('-created_at').first()
        
        # Nếu không có VERIFIED, hiển thị PENDING (nếu có)
        if not current_lr and pending_lr:
            current_lr = pending_lr
        if not current_sw and pending_sw:
            current_sw = pending_sw
        
        # Lấy lịch sử (tất cả status, ưu tiên VERIFIED)
        history = StudentCertificate.objects.filter(
            student=student
        ).order_by('-test_date', '-created_at')
        
        # Kiểm tra có thể làm placement test không
        # Có thể làm nếu: chưa có VERIFIED còn hạn
        can_take_placement_test_lr = (
            current_lr is None or 
            (current_lr.status != StudentCertificate.Status.VERIFIED) or
            (current_lr.expired_date < today if current_lr.expired_date else True)
        )
        
        can_take_placement_test_sw = (
            current_sw is None or 
            (current_sw.status != StudentCertificate.Status.VERIFIED) or
            (current_sw.expired_date < today if current_sw.expired_date else True)
        )
        
        # Log để debug
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"📊 [ProficiencyProfileView] Student: {student.id}")
        logger.info(f"📊 [ProficiencyProfileView] Current LR: {current_lr.id if current_lr else None}, Status: {current_lr.status if current_lr else None}")
        logger.info(f"📊 [ProficiencyProfileView] Current SW: {current_sw.id if current_sw else None}, Status: {current_sw.status if current_sw else None}")
        logger.info(f"📊 [ProficiencyProfileView] History count: {history.count()}")
        
        # Serialize data
        serializer = ProficiencyProfileSerializer({
            'current_lr': current_lr,
            'current_sw': current_sw,
            'history': history,
            'can_take_placement_test_lr': can_take_placement_test_lr,
            'can_take_placement_test_sw': can_take_placement_test_sw,
        })
        
        return Response({
            'success': True,
            'data': serializer.data
        })


class UploadCertificateView(PermissionMixin, APIView):
    """
    POST /api/proficiency/upload-certificate/ - Upload chứng chỉ TOEIC
    
    Body:
    {
        "skill_group": "LR" hoặc "SW",
        "score_1": 450,
        "score_2": 400,
        "total_score": 850,
        "test_date": "2024-01-15",
        "proof_image": "https://..."
    }
    
    Hệ thống sẽ:
    1. Tạo bản ghi với status = PENDING
    2. Gọi OCR để so khớp
    3. Nếu khớp > 90% -> status = VERIFIED
    4. Nếu không khớp -> status = PENDING (chờ admin duyệt)
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'POST': 'manage_proficiency_profile',
    }
    
    def post(self, request):
        # Kiểm tra user có student profile không
        if not hasattr(request.user, 'student_profile'):
            return Response({
                'success': False,
                'error': 'Chỉ học viên mới có thể upload chứng chỉ'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = StudentCertificateCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Tạo certificate với status PENDING
            certificate = serializer.save()
            
            # Gọi OCR và so khớp
            proof_image = certificate.proof_image
            if proof_image:
                user_data = {
                    'total_score': certificate.total_score,
                    'skill_group': certificate.skill_group,
                    'test_date': certificate.test_date,
                }
                user_name = request.user.fullname or request.user.username
                
                try:
                    is_verified, message, ocr_data = verify_certificate_with_ocr(
                        proof_image,
                        user_data,
                        user_name
                    )
                    
                    if is_verified:
                        certificate.status = StudentCertificate.Status.VERIFIED
                        certificate.verification_method = StudentCertificate.VerificationMethod.AUTO_OCR
                        certificate.save()
                        
                        return Response({
                            'success': True,
                            'message': message,
                            'data': StudentCertificateSerializer(certificate).data,
                            'ocr_data': ocr_data
                        }, status=status.HTTP_201_CREATED)
                    else:
                        # Giữ nguyên PENDING
                        return Response({
                            'success': True,
                            'message': message,
                            'data': StudentCertificateSerializer(certificate).data,
                            'ocr_data': ocr_data
                        }, status=status.HTTP_201_CREATED)
                
                except Exception as e:
                    # Nếu OCR lỗi, vẫn lưu nhưng để PENDING
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"OCR error: {e}")
                    
                    return Response({
                        'success': True,
                        'message': 'Chứng chỉ đã được upload. Hệ thống không thể xác thực tự động, đang chờ admin duyệt.',
                        'data': StudentCertificateSerializer(certificate).data
                    }, status=status.HTTP_201_CREATED)
            else:
                # Không có ảnh, để PENDING
                return Response({
                    'success': True,
                    'message': 'Chứng chỉ đã được upload. Đang chờ admin duyệt.',
                    'data': StudentCertificateSerializer(certificate).data
                }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PlacementTestResultView(PermissionMixin, APIView):
    """
    POST /api/proficiency/placement-test-result/ - Lưu kết quả Placement Test
    
    Body:
    {
        "skill_group": "LR" hoặc "SW",
        "score_1": 450,
        "score_2": 400,
        "total_score": 850
    }
    
    Hệ thống sẽ:
    1. Kiểm tra xem học viên có thể làm test cho skill_group này không
    2. Tạo bản ghi với status = VERIFIED (tự động duyệt)
    3. expired_date = today + 6 tháng
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'POST': 'manage_proficiency_profile',
    }
    
    def post(self, request):
        # Kiểm tra user có student profile không
        if not hasattr(request.user, 'student_profile'):
            return Response({
                'success': False,
                'error': 'Chỉ học viên mới có thể lưu kết quả test'
            }, status=status.HTTP_403_FORBIDDEN)
        
        student = request.user.student_profile
        skill_group = request.data.get('skill_group')
        today = timezone.now().date()
        
        # Kiểm tra xem có thể làm test cho skill_group này không
        if skill_group:
            current_cert = StudentCertificate.objects.filter(
                student=student,
                skill_group=skill_group,
                status=StudentCertificate.Status.VERIFIED,
                expired_date__gte=today
            ).order_by('-test_date').first()
            
            if current_cert:
                return Response({
                    'success': False,
                    'error': f'Bạn vẫn còn chứng chỉ {skill_group} còn hạn. Không thể làm placement test.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PlacementTestResultSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            certificate = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Kết quả placement test đã được lưu thành công',
                'data': StudentCertificateSerializer(certificate).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CertificateHistoryView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/proficiency/history/ - Lấy lịch sử chứng chỉ
    
    Query params:
    - skill_group: Lọc theo LR hoặc SW
    - status: Lọc theo VERIFIED, PENDING, REJECTED
    """
    serializer_class = StudentCertificateSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'manage_proficiency_profile',
    }
    
    def get_queryset(self):
        # Kiểm tra user có student profile không
        if not hasattr(self.request.user, 'student_profile'):
            return StudentCertificate.objects.none()
        
        student = self.request.user.student_profile
        queryset = StudentCertificate.objects.filter(student=student)
        
        # Filter theo skill_group
        skill_group = self.request.query_params.get('skill_group')
        if skill_group in ['LR', 'SW']:
            queryset = queryset.filter(skill_group=skill_group)
        
        # Filter theo status (chỉ hiển thị VERIFIED theo yêu cầu)
        # Nhưng để linh hoạt, có thể filter theo query param
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        else:
            # Mặc định chỉ hiển thị VERIFIED
            queryset = queryset.filter(status=StudentCertificate.Status.VERIFIED)
        
        return queryset.order_by('-test_date')
