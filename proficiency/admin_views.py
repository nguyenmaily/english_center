"""
Admin views cho quản lý và phê duyệt chứng chỉ
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from authentication.permissions import PermissionMixin
from .models import StudentCertificate
from .serializers import StudentCertificateSerializer


class PendingCertificatesListView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/proficiency/admin/pending/ - Lấy danh sách chứng chỉ
    
    Query params:
    - status: Lọc theo status (PENDING, VERIFIED, REJECTED). Mặc định: PENDING
    - skill_group: Lọc theo LR hoặc SW
    - search: Tìm kiếm theo tên học viên
    """
    serializer_class = StudentCertificateSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'approve_certificates',
    }
    
    def get_queryset(self):
        # Filter theo status (mặc định là PENDING)
        status_filter = self.request.query_params.get('status', 'PENDING')
        if status_filter in ['PENDING', 'VERIFIED', 'REJECTED']:
            queryset = StudentCertificate.objects.filter(
                status=status_filter
            ).select_related('student__user_account', 'admin').order_by('-created_at')
        else:
            # Nếu status không hợp lệ, mặc định là PENDING
            queryset = StudentCertificate.objects.filter(
                status=StudentCertificate.Status.PENDING
            ).select_related('student__user_account', 'admin').order_by('-created_at')
        
        # Filter theo skill_group
        skill_group = self.request.query_params.get('skill_group')
        if skill_group in ['LR', 'SW']:
            queryset = queryset.filter(skill_group=skill_group)
        
        # Search theo tên học viên
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(student__user_account__fullname__icontains=search) |
                Q(student__user_account__username__icontains=search)
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        
        # Debug: Log queryset count
        queryset = self.get_queryset()
        queryset_count = queryset.count()
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 [PendingCertificatesListView] Queryset count: {queryset_count}")
        logger.info(f"🔍 [PendingCertificatesListView] Response data type: {type(response.data)}")
        
        # Handle DRF pagination response format
        # CustomPagination returns: {'success': True, 'data': [...], 'meta': {...}}
        # Standard DRF pagination returns: {'count': X, 'next': ..., 'previous': ..., 'results': [...]}
        data = response.data
        
        # Debug: Log the actual structure
        logger.info(f"🔍 [PendingCertificatesListView] Response.data type: {type(data)}")
        if isinstance(data, dict):
            logger.info(f"🔍 [PendingCertificatesListView] Response.data keys: {list(data.keys())}")
            # Print first few keys and their types for debugging
            for key, value in list(data.items())[:5]:
                value_type = type(value).__name__
                is_list = isinstance(value, list)
                if isinstance(value, dict):
                    value_info = f"dict with keys: {list(value.keys())[:3]}"
                else:
                    value_info = str(value)[:50] if not is_list else f"list[{len(value)}]"
                logger.info(f"🔍 [PendingCertificatesListView] Key '{key}': type={value_type}, is_list={is_list}, value={value_info}")
        
        # Extract list from nested structure
        # CustomPagination returns: {'success': True, 'data': [...], 'meta': {...}}
        # CustomJSONRenderer might wrap: {'success': True, 'data': {'success': True, 'data': [...], 'meta': {...}}, 'error': None}
        if isinstance(data, dict):
            # Check for CustomPagination format (has 'data' key)
            if 'data' in data:
                inner_data = data['data']
                if isinstance(inner_data, list):
                    # Direct: {'data': [...]}
                    data = inner_data
                    logger.info(f"✅ [PendingCertificatesListView] Extracted {len(data)} items from data['data']")
                elif isinstance(inner_data, dict):
                    # Nested: {'data': {'data': [...]}} or {'data': {'results': [...]}}
                    if 'data' in inner_data and isinstance(inner_data['data'], list):
                        data = inner_data['data']
                        logger.info(f"✅ [PendingCertificatesListView] Extracted {len(data)} items from data['data']['data']")
                    elif 'results' in inner_data and isinstance(inner_data['results'], list):
                        data = inner_data['results']
                        logger.info(f"✅ [PendingCertificatesListView] Extracted {len(data)} items from data['data']['results']")
                    else:
                        logger.warning(f"⚠️ [PendingCertificatesListView] data['data'] is dict but no list found. Keys: {list(inner_data.keys())}")
                        data = []
                else:
                    logger.warning(f"⚠️ [PendingCertificatesListView] data['data'] is not list or dict: {type(inner_data)}")
                    data = []
            # Check for standard DRF pagination format (has 'results' key)
            elif 'results' in data and isinstance(data['results'], list):
                data = data['results']
                logger.info(f"✅ [PendingCertificatesListView] Extracted {len(data)} results from standard pagination")
            else:
                # Try to find any list value in the dict
                logger.warning(f"⚠️ [PendingCertificatesListView] Dict without 'data' or 'results' key. Keys: {list(data.keys())}")
                for key, value in data.items():
                    if isinstance(value, list):
                        logger.info(f"✅ [PendingCertificatesListView] Found list in key '{key}' with {len(value)} items")
                        data = value
                        break
                else:
                    # No list found, return empty
                    logger.warning(f"⚠️ [PendingCertificatesListView] No list found in response, returning empty")
                    data = []
        elif isinstance(data, list):
            logger.info(f"✅ [PendingCertificatesListView] Direct list response with {len(data)} items")
        else:
            logger.warning(f"⚠️ [PendingCertificatesListView] Unexpected response format: {type(data)}")
            data = []
        
        # Thêm thống kê (luôn tính cho PENDING)
        total_pending = StudentCertificate.objects.filter(
            status=StudentCertificate.Status.PENDING
        ).count()
        
        pending_lr = StudentCertificate.objects.filter(
            status=StudentCertificate.Status.PENDING,
            skill_group=StudentCertificate.SkillGroup.LR
        ).count()
        
        pending_sw = StudentCertificate.objects.filter(
            status=StudentCertificate.Status.PENDING,
            skill_group=StudentCertificate.SkillGroup.SW
        ).count()
        
        # Thống kê cho VERIFIED và REJECTED
        total_verified = StudentCertificate.objects.filter(
            status=StudentCertificate.Status.VERIFIED
        ).count()
        
        total_rejected = StudentCertificate.objects.filter(
            status=StudentCertificate.Status.REJECTED
        ).count()
        
        logger.info(f"📊 [PendingCertificatesListView] Stats - Pending: {total_pending}, Verified: {total_verified}, Rejected: {total_rejected}")
        
        return Response({
            'success': True,
            'data': data,  # Now guaranteed to be a list
            'stats': {
                'total_pending': total_pending,
                'pending_lr': pending_lr,
                'pending_sw': pending_sw,
                'total_verified': total_verified,
                'total_rejected': total_rejected
            }
        })


class ApproveCertificateView(PermissionMixin, APIView):
    """
    POST /api/proficiency/admin/{id}/approve/ - Phê duyệt chứng chỉ
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'POST': 'approve_certificates',
    }
    
    def post(self, request, pk):
        try:
            certificate = StudentCertificate.objects.get(pk=pk)
        except StudentCertificate.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Chứng chỉ không tồn tại'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if certificate.status != StudentCertificate.Status.PENDING:
            return Response({
                'success': False,
                'error': f'Chứng chỉ này đã được xử lý (status: {certificate.get_status_display()})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cập nhật status
        certificate.status = StudentCertificate.Status.VERIFIED
        certificate.admin = request.user
        certificate.verification_method = StudentCertificate.VerificationMethod.MANUAL_ADMIN
        certificate.save()
        
        return Response({
            'success': True,
            'message': 'Chứng chỉ đã được phê duyệt thành công',
            'data': StudentCertificateSerializer(certificate).data
        })


class RejectCertificateView(PermissionMixin, APIView):
    """
    POST /api/proficiency/admin/{id}/reject/ - Từ chối chứng chỉ
    
    Body (optional):
    {
        "reason": "Lý do từ chối"
    }
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'POST': 'approve_certificates',
    }
    
    def post(self, request, pk):
        try:
            certificate = StudentCertificate.objects.get(pk=pk)
        except StudentCertificate.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Chứng chỉ không tồn tại'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if certificate.status != StudentCertificate.Status.PENDING:
            return Response({
                'success': False,
                'error': f'Chứng chỉ này đã được xử lý (status: {certificate.get_status_display()})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cập nhật status
        certificate.status = StudentCertificate.Status.REJECTED
        certificate.admin = request.user
        certificate.verification_method = StudentCertificate.VerificationMethod.MANUAL_ADMIN
        certificate.save()
        
        reason = request.data.get('reason', '')
        
        return Response({
            'success': True,
            'message': 'Chứng chỉ đã bị từ chối',
            'data': StudentCertificateSerializer(certificate).data,
            'reason': reason
        })


class CertificateDetailView(PermissionMixin, generics.RetrieveAPIView):
    """
    GET /api/proficiency/admin/{id}/ - Xem chi tiết chứng chỉ
    """
    serializer_class = StudentCertificateSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'approve_certificates',
    }
    queryset = StudentCertificate.objects.all()


class DebugCertificatesView(PermissionMixin, APIView):
    """
    GET /api/proficiency/admin/debug/ - Debug endpoint để xem tất cả certificates và status
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'approve_certificates',
    }
    
    def get(self, request):
        """Debug: Xem tất cả certificates với status"""
        all_certs = StudentCertificate.objects.all().select_related('student__user_account')
        
        # Group by status
        by_status = {}
        for cert in all_certs:
            status = cert.status
            if status not in by_status:
                by_status[status] = []
            by_status[status].append({
                'id': cert.id,
                'student_id': str(cert.student.id) if cert.student else None,
                'student_name': cert.student.user_account.fullname if cert.student and cert.student.user_account else 'N/A',
                'skill_group': cert.skill_group,
                'status': cert.status,
                'created_at': cert.created_at.isoformat() if cert.created_at else None
            })
        
        # Count by status
        status_counts = {
            status: StudentCertificate.objects.filter(status=status).count()
            for status in ['VERIFIED', 'PENDING', 'REJECTED']
        }
        
        return Response({
            'success': True,
            'total_certificates': all_certs.count(),
            'status_counts': status_counts,
            'by_status': by_status,
            'pending_certificates': [
                {
                    'id': cert.id,
                    'student_id': str(cert.student.id) if cert.student else None,
                    'student_name': cert.student.user_account.fullname if cert.student and cert.student.user_account else 'N/A',
                    'skill_group': cert.skill_group,
                    'created_at': cert.created_at.isoformat() if cert.created_at else None
                }
                for cert in StudentCertificate.objects.filter(status=StudentCertificate.Status.PENDING).select_related('student__user_account')
            ]
        })

