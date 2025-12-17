from django.contrib.auth import get_user_model
from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count

from authentication.permissions import PermissionMixin
from .models import Teacher, Manager, Student
from .serializers import (
    UserCreateSerializer,
    UserWithProfileSerializer,
    UserUpdateWithProfileSerializer,
    ChangePasswordSerializer,
    TeacherSerializer,
    TeacherDetailSerializer,
    ManagerSerializer,
    StudentSerializer,
    RoleFieldsSchemaSerializer
)

User = get_user_model()


# ==================== HELPER - ROLE SCHEMA ====================

class RoleFieldsSchemaView(generics.GenericAPIView):
    """
    GET /api/users/role-fields/?role=teacher
    
    Trả về danh sách fields cần điền cho từng role
    Frontend dùng để render form động
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RoleFieldsSchemaSerializer
    
    def get(self, request, *args, **kwargs):
        role = request.query_params.get('role', '').lower()
        
        if not role:
            return Response({
                'success': False,
                'error': 'Role parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        schemas = {
            'student': {
                'role': 'student',
                'label': 'Student (Học viên)',
                'description': 'Tài khoản học viên',
                'fields': [
                    {
                        'name': 'student_target_score',
                        'backend_field': 'student_target_score',
                        'type': 'number',
                        'required': False,
                        'label': 'Điểm mục tiêu',
                        'placeholder': '7.5',
                        'min': 0,
                        'max': 9,
                        'step': 0.5,
                        'help_text': 'Điểm IELTS/TOEIC mục tiêu (không bắt buộc)'
                    },
                    {
                        'name': 'student_commitment_status',
                        'backend_field': 'student_commitment_status',
                        'type': 'select',
                        'required': False,
                        'label': 'Trạng thái cam kết',
                        'default': 'not_committed',
                        'choices': [
                            {'value': choice[0], 'label': choice[1]}
                            for choice in Student.CommitmentStatus.choices
                        ],
                        'help_text': 'Trạng thái cam kết học tập'
                    }
                ],
                'note': '💡 Các thông tin này có thể để trống, sẽ cập nhật sau'
            },
            
            'teacher': {
                'role': 'teacher',
                'label': 'Teacher (Giảng viên)',
                'description': 'Tài khoản giảng viên',
                'fields': [
                    {
                        'name': 'teacher_specialization',
                        'backend_field': 'teacher_specialization',
                        'type': 'text',
                        'required': True,
                        'label': 'Chuyên môn',
                        'placeholder': 'Ví dụ: IELTS Speaking, TOEIC Listening',
                        'max_length': 200,
                        'help_text': 'Chuyên môn giảng dạy (bắt buộc)'
                    },
                    {
                        'name': 'teacher_level',
                        'backend_field': 'teacher_level',
                        'type': 'select',
                        'required': False,
                        'label': 'Cấp độ',
                        'choices': [
                            {'value': 'junior', 'label': 'Junior'},
                            {'value': 'senior', 'label': 'Senior'},
                            {'value': 'expert', 'label': 'Expert'},
                            {'value': 'master', 'label': 'Master'}
                        ],
                        'help_text': 'Cấp độ giảng viên'
                    },
                    {
                        'name': 'teacher_campus_id',
                        'backend_field': 'teacher_campus_id',
                        'type': 'select-api',
                        'required': False,
                        'label': 'Cơ sở giảng dạy',
                        'api_endpoint': '/api/campus/',
                        'display_field': 'name',
                        'value_field': 'id',
                        'help_text': 'Cơ sở giảng viên sẽ giảng dạy'
                    }
                ],
                'note': '⚠️ Chuyên môn là bắt buộc'
            },
            
            'manager': {
                'role': 'manager',
                'label': 'Manager (Quản lý)',
                'description': 'Tài khoản quản lý',
                'fields': [
                    {
                        'name': 'manager_campus_id',
                        'backend_field': 'manager_campus_id',
                        'type': 'select-api',
                        'required': True,
                        'label': 'Cơ sở quản lý',
                        'api_endpoint': '/api/campus/',
                        'display_field': 'name',
                        'value_field': 'id',
                        'help_text': 'Cơ sở mà manager sẽ quản lý (bắt buộc)'
                    }
                ],
                'note': '⚠️ Cơ sở quản lý là bắt buộc'
            },
            
            'admin': {
                'role': 'admin',
                'label': 'Admin (Quản trị viên)',
                'description': 'Tài khoản quản trị viên',
                'fields': [],
                'note': '💡 Admin không cần thông tin bổ sung'
            }
        }
        
        if role not in schemas:
            return Response({
                'success': False,
                'error': f'Invalid role. Valid roles: student, teacher, manager, admin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': schemas[role]
        })



# ==================== QUẢN LÝ PROFILE CÁ NHÂN ====================

class MyProfileView(generics.GenericAPIView):
    """
    GET /api/users/me/ - Xem thông tin cá nhân
    PUT /api/users/me/ - Cập nhật thông tin cá nhân
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserWithProfileSerializer
    
    def get(self, request, *args, **kwargs):
        """Xem profile của mình"""
        serializer = self.get_serializer(request.user)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request, *args, **kwargs):
        """Cập nhật profile của mình"""
        user = request.user
        
        allowed_fields = ['email', 'fullname', 'phone', 'sex', 'dob', 'urlImage']
        
        for field, value in request.data.items():
            if field in allowed_fields:
                setattr(user, field, value)
        
        user.save()
        
        serializer = self.get_serializer(user)
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'data': serializer.data
        })


class ChangePasswordView(generics.GenericAPIView):
    """
    POST /api/users/change-password/ - Đổi mật khẩu
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'success': False,
                'error': 'Old password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'success': True,
            'message': 'Password changed successfully'
        })


# ==================== QUẢN LÝ NGƯỜI DÙNG ====================

class UserListCreateView(PermissionMixin, generics.ListCreateAPIView):
    """
    GET /api/users/ - Lấy danh sách người dùng
    POST /api/users/ - Tạo người dùng mới
    
    Phân quyền:
    - Admin: Xem tất cả users trong hệ thống
    - Manager: Chỉ xem users trong campus của mình
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_users',
        'POST': 'manage_users',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = []  # Removed roleid__name, using custom filter
    search_fields = ['username', 'email', 'fullname', 'phone']
    ordering_fields = ['username', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.select_related('roleid').all()
        
        if hasattr(user, 'roleid') and user.roleid.name == 'admin':
            pass
        
        elif hasattr(user, 'manager_profile') and user.manager_profile.campus:
            campus = user.manager_profile.campus
            
            teacher_user_ids = Teacher.objects.filter(
                campus=campus
            ).values_list('user_account_id', flat=True)
            
            manager_user_ids = Manager.objects.filter(
                campus=campus
            ).values_list('user_account_id', flat=True)
            
            student_user_ids = Student.objects.all().values_list('user_account_id', flat=True)
            
            queryset = queryset.filter(
                Q(id__in=teacher_user_ids) | 
                Q(id__in=manager_user_ids) | 
                Q(id__in=student_user_ids) |
                Q(id=user.id)
            )
        
        # Support both 'role' and 'roleid__name' parameters for filtering
        role = self.request.query_params.get('role') or self.request.query_params.get('roleid__name')
        if role:
            queryset = queryset.filter(roleid__name=role)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserWithProfileSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        # Validate and return detailed errors
        if not serializer.is_valid():
            errors = serializer.errors
            error_messages = []
            
            # Format error messages in Vietnamese
            field_names = {
                'username': 'Tên đăng nhập',
                'email': 'Email',
                'fullname': 'Họ và tên',
                'password': 'Mật khẩu',
                'phone': 'Số điện thoại',
                'role_name': 'Vai trò',
                'teacher_specialization': 'Chuyên môn giảng viên',
                'teacher_campus_id': 'Cơ sở giảng dạy',
                'manager_campus_id': 'Cơ sở quản lý',
            }
            
            for field, messages in errors.items():
                field_label = field_names.get(field, field)
                if isinstance(messages, list):
                    for msg in messages:
                        # Translate common error messages
                        if 'already exists' in str(msg).lower() or 'unique' in str(msg).lower():
                            error_messages.append(f'{field_label} đã tồn tại trong hệ thống')
                        elif 'required' in str(msg).lower():
                            error_messages.append(f'{field_label} là bắt buộc')
                        elif 'invalid' in str(msg).lower():
                            error_messages.append(f'{field_label} không hợp lệ')
                        else:
                            error_messages.append(f'{field_label}: {msg}')
                else:
                    error_messages.append(f'{field_label}: {messages}')
            
            return Response({
                'success': False,
                'message': error_messages[0] if error_messages else 'Dữ liệu không hợp lệ',
                'errors': error_messages,
                'data': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save user
        try:
            user = serializer.save()
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Lỗi khi tạo người dùng: {str(e)}',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        response_serializer = UserWithProfileSerializer(user)
        
        return Response({
            'success': True,
            'message': f'Tạo {user.roleid.name} thành công',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class UserDetailView(PermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/users/{id}/ - Xem chi tiết user
    PUT /api/users/{id}/ - Cập nhật user
    DELETE /api/users/{id}/ - Xóa user
    
    Phân quyền:
    - Admin: Xem/sửa/xóa tất cả users
    - Manager: Chỉ xem/sửa/xóa users trong campus của mình
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_users',
        'PUT': 'manage_users',
        'PATCH': 'manage_users',
        'DELETE': 'manage_users',
    }
    queryset = User.objects.select_related('roleid').all()
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if hasattr(user, 'roleid') and user.roleid.name == 'admin':
            return queryset
        
        if hasattr(user, 'manager_profile') and user.manager_profile.campus:
            campus = user.manager_profile.campus
            
            teacher_user_ids = Teacher.objects.filter(campus=campus).values_list('user_account_id', flat=True)
            manager_user_ids = Manager.objects.filter(campus=campus).values_list('user_account_id', flat=True)
            
            # Lấy student user_ids từ enrollments trong campus
            from classes.models import Class
            from enrollment.models import Enrollment
            
            campus_classes = Class.objects.filter(campus=campus).values_list('id', flat=True)
            enrollments = Enrollment.objects.filter(class_id__in=campus_classes)
            student_ids = enrollments.values_list('student_id', flat=True).distinct()
            student_user_ids = Student.objects.filter(id__in=student_ids).values_list('user_account_id', flat=True)
            
            return queryset.filter(
                Q(id__in=teacher_user_ids) | 
                Q(id__in=manager_user_ids) |
                Q(id__in=student_user_ids) |
                Q(id=user.id)
            )
        
        return queryset.filter(id=user.id)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateWithProfileSerializer
        return UserWithProfileSerializer
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        # Validate and return detailed errors
        if not serializer.is_valid():
            errors = serializer.errors
            error_messages = []
            
            # Format error messages in Vietnamese
            field_names = {
                'username': 'Tên đăng nhập',
                'email': 'Email',
                'fullname': 'Họ và tên',
                'password': 'Mật khẩu',
                'phone': 'Số điện thoại',
                'role_name': 'Vai trò',
                'teacher_specialization': 'Chuyên môn giảng viên',
                'teacher_campus_id': 'Cơ sở giảng dạy',
                'manager_campus_id': 'Cơ sở quản lý',
            }
            
            for field, messages in errors.items():
                field_label = field_names.get(field, field)
                if isinstance(messages, list):
                    for msg in messages:
                        # Translate common error messages
                        if 'already exists' in str(msg).lower() or 'unique' in str(msg).lower():
                            error_messages.append(f'{field_label} đã tồn tại trong hệ thống')
                        elif 'required' in str(msg).lower():
                            error_messages.append(f'{field_label} là bắt buộc')
                        elif 'invalid' in str(msg).lower():
                            error_messages.append(f'{field_label} không hợp lệ')
                        else:
                            error_messages.append(f'{field_label}: {msg}')
                else:
                    error_messages.append(f'{field_label}: {messages}')
            
            return Response({
                'success': False,
                'message': error_messages[0] if error_messages else 'Dữ liệu không hợp lệ',
                'errors': error_messages,
                'data': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.perform_update(serializer)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Lỗi khi cập nhật người dùng: {str(e)}',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        response_serializer = UserWithProfileSerializer(instance)
        
        return Response({
            'success': True,
            'message': 'Cập nhật người dùng thành công',
            'data': response_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance.id == request.user.id:
            return Response({
                'success': False,
                'error': 'You cannot delete your own account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': 'User deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


# ==================== QUẢN LÝ GIẢNG VIÊN ====================

class TeacherListView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/teachers/ - Danh sách giảng viên
    
    Phân quyền:
    - Admin: Xem tất cả teachers
    - Manager: Chỉ xem teachers trong campus của mình
    """
    permission_classes = [IsAuthenticated]
    permission_map = {'GET': 'view_teachers'}
    serializer_class = TeacherSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['campus', 'level']
    search_fields = ['user_account__fullname', 'user_account__username', 'specialization']
    ordering_fields = ['user_account__fullname']
    ordering = ['user_account__fullname']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Teacher.objects.select_related('user_account', 'campus').all()
        
        if hasattr(user, 'roleid') and user.roleid.name == 'admin':
            return queryset
        
        if hasattr(user, 'manager_profile') and user.manager_profile.campus:
            return queryset.filter(campus=user.manager_profile.campus)
        
        return queryset.none()


class TeacherDetailView(PermissionMixin, generics.RetrieveUpdateAPIView):
    """
    GET /api/teachers/{teacher_id}/ - Xem chi tiết giảng viên
    PUT /api/teachers/{teacher_id}/ - Cập nhật thông tin giảng viên
    
    Phân quyền:
    - Admin: Xem/sửa tất cả teachers
    - Manager: Chỉ xem/sửa teachers trong campus của mình
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_teachers',
        'PUT': 'manage_teachers',
        'PATCH': 'manage_teachers',
    }
    serializer_class = TeacherDetailSerializer
    queryset = Teacher.objects.select_related('user_account', 'campus').all()
    lookup_field = 'id'
    lookup_url_kwarg = 'teacher_id'
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if hasattr(user, 'roleid') and user.roleid.name == 'admin':
            return queryset
        
        if hasattr(user, 'manager_profile') and user.manager_profile.campus:
            return queryset.filter(campus=user.manager_profile.campus)
        
        return queryset.none()


# ==================== MANAGER & STUDENT LISTS ====================

class ManagerListView(PermissionMixin, generics.ListAPIView):
    """GET /api/managers/ - Danh sách managers"""
    permission_classes = [IsAuthenticated]
    permission_map = {'GET': 'view_managers'}
    serializer_class = ManagerSerializer
    queryset = Manager.objects.select_related('user_account', 'campus').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['campus']
    search_fields = ['user_account__fullname', 'user_account__username']
    ordering = ['user_account__fullname']


class StudentListView(PermissionMixin, generics.ListAPIView):
    """GET /api/users/students/ - Danh sách students"""
    permission_classes = [IsAuthenticated]
    permission_map = {'GET': 'view_students'}
    serializer_class = StudentSerializer
    queryset = Student.objects.select_related('user_account').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['commitment_status']
    search_fields = ['user_account__fullname', 'user_account__username']
    ordering = ['user_account__fullname']
    
    def get_queryset(self):
        """
        Filter students based on user role:
        - Admin: See all students
        - Manager: Only see students enrolled in classes at their campus
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # Check if user is manager
        if hasattr(user, 'roleid') and user.roleid:
            role_name = user.roleid.name
            
            if role_name == 'manager':
                # Manager chỉ thấy học viên đang học tại campus của họ
                try:
                    manager = Manager.objects.select_related('campus').get(user_account=user)
                    if manager.campus:
                        # Lấy tất cả classes thuộc campus này
                        from classes.models import Class
                        from enrollment.models import Enrollment
                        
                        campus_classes = Class.objects.filter(campus=manager.campus).values_list('id', flat=True)
                        
                        # Lấy tất cả enrollments của các classes này
                        enrollments = Enrollment.objects.filter(class_id__in=campus_classes)
                        
                        # Lấy danh sách student_ids từ enrollments
                        student_ids = enrollments.values_list('student_id', flat=True).distinct()
                        
                        # Filter students theo student_ids
                        queryset = queryset.filter(id__in=student_ids)
                        
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Manager {user.username} filtering students for campus: {manager.campus.name}, found {queryset.count()} students")
                    else:
                        # Manager chưa có campus → không thấy student nào
                        queryset = queryset.none()
                except Manager.DoesNotExist:
                    # User không phải manager → không filter (admin sẽ thấy tất cả)
                    pass
        
        return queryset


class ManagerDashboardStatsView(APIView):
    """
    GET /api/users/manager/dashboard-stats/
    Thống kê dashboard cho manager dựa trên campus của họ
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get manager profile for current user
            manager = Manager.objects.select_related('user_account', 'campus').filter(
                user_account=request.user
            ).first()
            
            if not manager:
                return Response(
                    {'detail': 'User is not a manager'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if not manager.campus:
                return Response({
                    'campus': None,
                    'message': 'Manager chưa được gán campus'
            })
            
            campus = manager.campus
            
            # Import here to avoid circular dependency
            from classes.models import Class
            from enrollment.models import Enrollment
            from class_sessions.models import Session
            from datetime import date, timedelta, datetime
            from django.utils import timezone as tz
            
            # Get classes in this campus
            classes = Class.objects.filter(campus=campus)
            total_classes = classes.count()
            ongoing_classes = classes.filter(status='ongoing').count()
            planned_classes = classes.filter(status='planned').count()
            
            # Get students enrolled in classes of this campus
            class_ids = list(classes.values_list('id', flat=True))
            total_students = Enrollment.objects.filter(class_id__in=class_ids).values('student_id').distinct().count()
            
            # Get all teachers in this campus (not just those teaching classes)
            from users.models import Teacher
            teachers_in_campus = Teacher.objects.filter(campus=campus).count()
            
            # Get revenue (from enrollments - only paid)
            enrollments = Enrollment.objects.filter(
                class_id__in=class_ids,
                invoice_status='paid'  # Chỉ tính enrollments đã thanh toán
            )
            total_revenue = enrollments.aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            # Get upcoming sessions (next 7 days)
            today = date.today()
            next_week = today + timedelta(days=7)
            upcoming_sessions = Session.objects.filter(
                class_session__in=classes,
                study_date__gte=today,
                study_date__lte=next_week
            ).count()
            
            # Get today's sessions
            today_sessions = Session.objects.filter(
                class_session__in=classes,
                study_date=today
            ).count()
            
            # ========== CHART DATA ==========
            from collections import defaultdict
            from calendar import monthrange
            from django.db.models import Count, Q
            from django.utils import timezone as tz
            from datetime import datetime
            
            # 1. Revenue by month (last 6 months)
            revenue_by_month = []
            months_labels = []
            for i in range(5, -1, -1):  # Last 6 months
                # Calculate month start and end correctly
                target_month = today.month - i
                target_year = today.year
                if target_month <= 0:
                    target_month += 12
                    target_year -= 1
                
                month_start = date(target_year, target_month, 1)
                last_day = monthrange(target_year, target_month)[1]
                month_end = date(target_year, target_month, last_day)
                
                # Convert to timezone-aware datetime
                month_start_dt = tz.make_aware(datetime.combine(month_start, datetime.min.time()))
                month_end_dt = tz.make_aware(datetime.combine(month_end, datetime.max.time()))
                
                month_revenue = Enrollment.objects.filter(
                    class_id__in=class_ids,
                    invoice_status='paid',
                    created_at__gte=month_start_dt,
                    created_at__lte=month_end_dt
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                revenue_by_month.append(float(month_revenue))
                months_labels.append(month_start.strftime('%m/%Y'))
            
            # 2. Class distribution by status
            # Note: Database enum uses 'finished' not 'completed', 'canceled' not 'cancelled'
            # Use raw SQL to query enum values directly
            from django.db import connection
            completed_classes = 0
            cancelled_classes = 0
            
            try:
                with connection.cursor() as cursor:
                    # Query for 'finished' status (database enum)
                    cursor.execute("""
                        SELECT COUNT(*) FROM classes 
                        WHERE campus_id = %s AND status = 'finished'
                    """, [campus.id])
                    completed_classes = cursor.fetchone()[0] or 0
                    
                    # Query for 'canceled' status (database enum)
                    cursor.execute("""
                        SELECT COUNT(*) FROM classes 
                        WHERE campus_id = %s AND status = 'canceled'
                    """, [campus.id])
                    cancelled_classes = cursor.fetchone()[0] or 0
            except Exception as e:
                # Fallback: try model enum values
                try:
                    completed_classes = classes.filter(status='completed').count()
                except:
                    completed_classes = 0
                try:
                    cancelled_classes = classes.filter(status='cancelled').count()
                except:
                    cancelled_classes = 0
            
            class_distribution = {
                'ongoing': ongoing_classes,
                'planned': planned_classes,
                'completed': completed_classes,
                'cancelled': cancelled_classes
            }
            
            # 3. Student growth (new enrollments by month - last 6 months)
            student_growth = []
            for i in range(5, -1, -1):
                target_month = today.month - i
                target_year = today.year
                if target_month <= 0:
                    target_month += 12
                    target_year -= 1
                
                month_start = date(target_year, target_month, 1)
                last_day = monthrange(target_year, target_month)[1]
                month_end = date(target_year, target_month, last_day)
                
                # Convert to timezone-aware datetime
                month_start_dt = tz.make_aware(datetime.combine(month_start, datetime.min.time()))
                month_end_dt = tz.make_aware(datetime.combine(month_end, datetime.max.time()))
                
                new_students = Enrollment.objects.filter(
                    class_id__in=class_ids,
                    created_at__gte=month_start_dt,
                    created_at__lte=month_end_dt
                ).values('student_id').distinct().count()
                
                student_growth.append(new_students)
            
            # 4. Sessions by month (last 6 months)
            sessions_by_month = []
            for i in range(5, -1, -1):
                target_month = today.month - i
                target_year = today.year
                if target_month <= 0:
                    target_month += 12
                    target_year -= 1
                
                month_start = date(target_year, target_month, 1)
                last_day = monthrange(target_year, target_month)[1]
                month_end = date(target_year, target_month, last_day)
                
                month_sessions = Session.objects.filter(
                    class_session__in=classes,
                    study_date__gte=month_start,
                    study_date__lte=month_end
                ).count()
                
                sessions_by_month.append(month_sessions)
            
            # 5. Attendance rate by month (last 6 months)
            attendance_data = []
            attendance_labels = []
            for i in range(5, -1, -1):
                target_month = today.month - i
                target_year = today.year
                if target_month <= 0:
                    target_month += 12
                    target_year -= 1
                
                month_start = date(target_year, target_month, 1)
                last_day = monthrange(target_year, target_month)[1]
                month_end = date(target_year, target_month, last_day)
                
                month_sessions = Session.objects.filter(
                    class_session__in=classes,
                    study_date__gte=month_start,
                    study_date__lte=month_end
                )
                session_ids = list(month_sessions.values_list('id', flat=True))
                
                from class_sessions.models import Attendance
                total_attendance = Attendance.objects.filter(session_id__in=session_ids).count()
                present_count = Attendance.objects.filter(
                    session_id__in=session_ids,
                    status='present'
                ).count()
                absent_count = Attendance.objects.filter(
                    session_id__in=session_ids,
                    status='absent'
                ).count()
                
                attendance_data.append({
                    'present': present_count,
                    'absent': absent_count,
                    'total': total_attendance
                })
                attendance_labels.append(month_start.strftime('%m/%Y'))
            
            # 6. Top classes by student count
            top_classes_data = []
            for cls in classes:
                student_count = Enrollment.objects.filter(class_id=cls.id).values('student_id').distinct().count()
                top_classes_data.append({
                    'name': cls.name,
                    'student_count': student_count
                })
            top_classes_data = sorted(top_classes_data, key=lambda x: x['student_count'], reverse=True)[:10]
            
            return Response({
                'campus': {
                    'id': str(campus.id),
                    'name': campus.name,
                    'address': campus.address,
                    'hotline': campus.hotline,
                    'email': campus.email,
                    'status': campus.status
                },
                'statistics': {
                    'total_classes': total_classes,
                    'ongoing_classes': ongoing_classes,
                    'planned_classes': planned_classes,
                    'total_students': total_students,
                    'teachers_count': teachers_in_campus,
                    'total_revenue': float(total_revenue),
                    'upcoming_sessions': upcoming_sessions,
                    'today_sessions': today_sessions
                },
                'charts': {
                    'revenue_by_month': {
                        'labels': months_labels,
                        'data': revenue_by_month
                    },
                    'class_distribution': class_distribution,
                    'student_growth': {
                        'labels': months_labels,
                        'data': student_growth
                    },
                    'sessions_by_month': {
                        'labels': months_labels,
                        'data': sessions_by_month
                    },
                    'attendance_by_month': {
                        'labels': attendance_labels,
                        'data': attendance_data
                    },
                    'top_classes': top_classes_data
                }
            })
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting manager dashboard stats: {str(e)}")
            return Response(
                {'detail': f'Error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminDashboardStatsView(APIView):
    """
    GET /api/users/admin/dashboard-stats/
    Thống kê dashboard cho admin - tính cho toàn bộ hệ thống
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Check if user is admin
            if not hasattr(request.user, 'roleid') or request.user.roleid.name != 'admin':
                return Response(
                    {'detail': 'User is not an admin'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Import here to avoid circular dependency
            from classes.models import Class
            from enrollment.models import Enrollment
            from class_sessions.models import Session
            from campus.models import Campus
            from datetime import date, timedelta
            
            # Get all classes
            classes = Class.objects.all()
            total_classes = classes.count()
            ongoing_classes = classes.filter(status='ongoing').count()
            planned_classes = classes.filter(status='planned').count()
            
            # Get all students (from enrollments)
            class_ids = list(classes.values_list('id', flat=True))
            total_students = Enrollment.objects.filter(class_id__in=class_ids).values('student_id').distinct().count()
            
            # Get all teachers
            from users.models import Teacher
            total_teachers = Teacher.objects.count()
            
            # Get all campuses
            total_campuses = Campus.objects.count()
            active_campuses = Campus.objects.filter(status='active').count()
            
            # Get revenue (from all enrollments - only paid)
            total_revenue = Enrollment.objects.filter(
                invoice_status='paid'  # Chỉ tính enrollments đã thanh toán
            ).aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            # Get upcoming sessions (next 7 days)
            today = date.today()
            next_week = today + timedelta(days=7)
            upcoming_sessions = Session.objects.filter(
                study_date__gte=today,
                study_date__lte=next_week
            ).count()
            
            # Get today's sessions
            today_sessions = Session.objects.filter(
                study_date=today
            ).count()
            
            # ========== CHART DATA ==========
            from collections import defaultdict
            from calendar import monthrange
            from datetime import datetime
            from django.utils import timezone as tz
            
            # 1. Revenue by month (last 6 months)
            revenue_by_month = []
            months_labels = []
            for i in range(5, -1, -1):  # Last 6 months
                # Calculate month start and end correctly
                target_month = today.month - i
                target_year = today.year
                if target_month <= 0:
                    target_month += 12
                    target_year -= 1
                
                month_start = date(target_year, target_month, 1)
                last_day = monthrange(target_year, target_month)[1]
                month_end = date(target_year, target_month, last_day)
                
                # Convert to timezone-aware datetime
                month_start_dt = tz.make_aware(datetime.combine(month_start, datetime.min.time()))
                month_end_dt = tz.make_aware(datetime.combine(month_end, datetime.max.time()))
                
                month_revenue = Enrollment.objects.filter(
                    invoice_status='paid',
                    created_at__gte=month_start_dt,
                    created_at__lte=month_end_dt
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                revenue_by_month.append(float(month_revenue))
                months_labels.append(month_start.strftime('%m/%Y'))
            
            # 2. Student growth by month (last 6 months)
            student_growth = []
            student_growth_labels = []
            for i in range(5, -1, -1):  # Last 6 months
                target_month = today.month - i
                target_year = today.year
                if target_month <= 0:
                    target_month += 12
                    target_year -= 1
                
                month_start = date(target_year, target_month, 1)
                last_day = monthrange(target_year, target_month)[1]
                month_end = date(target_year, target_month, last_day)
                
                month_start_dt = tz.make_aware(datetime.combine(month_start, datetime.min.time()))
                month_end_dt = tz.make_aware(datetime.combine(month_end, datetime.max.time()))
                
                # Count distinct students who enrolled in this month
                new_students = Enrollment.objects.filter(
                    created_at__gte=month_start_dt,
                    created_at__lte=month_end_dt
                ).values('student_id').distinct().count()
                
                student_growth.append(new_students)
                student_growth_labels.append(month_start.strftime('%m/%Y'))
            
            # 3. Student distribution by campus
            student_by_campus = []
            campus_names = []
            all_campuses = Campus.objects.all()
            for campus in all_campuses:
                campus_classes = Class.objects.filter(campus=campus).values_list('id', flat=True)
                campus_students = Enrollment.objects.filter(
                    class_id__in=campus_classes
                ).values('student_id').distinct().count()
                
                student_by_campus.append(campus_students)
                campus_names.append(campus.name or f'Cơ sở {campus.id}')
            
            # 4. Teachers by campus
            teachers_by_campus = []
            teachers_campus_names = []
            from users.models import Teacher
            for campus in all_campuses:
                campus_teachers = Teacher.objects.filter(campus=campus).count()
                teachers_by_campus.append(campus_teachers)
                teachers_campus_names.append(campus.name or f'Cơ sở {campus.id}')
            
            # 5. Class distribution by status
            # Use raw SQL to query enum values directly
            from django.db import connection
            completed_classes = 0
            cancelled_classes = 0
            
            try:
                with connection.cursor() as cursor:
                    # Query for 'finished' status (database enum)
                    cursor.execute("""
                        SELECT COUNT(*) FROM classes 
                        WHERE status = 'finished'
                    """)
                    completed_classes = cursor.fetchone()[0]
                    
                    # Query for 'canceled' status (database enum)
                    cursor.execute("""
                        SELECT COUNT(*) FROM classes 
                        WHERE status = 'canceled'
                    """)
                    cancelled_classes = cursor.fetchone()[0]
            except Exception as e:
                # Fallback to model enum values
                try:
                    completed_classes = classes.filter(status='completed').count()
                except:
                    completed_classes = 0
                try:
                    cancelled_classes = classes.filter(status='cancelled').count()
                except:
                    cancelled_classes = 0
            
            class_distribution = {
                'ongoing': ongoing_classes,
                'planned': planned_classes,
                'completed': completed_classes,
                'cancelled': cancelled_classes
            }
            
            return Response({
                'statistics': {
                    'total_classes': total_classes,
                    'ongoing_classes': ongoing_classes,
                    'planned_classes': planned_classes,
                    'total_students': total_students,
                    'total_teachers': total_teachers,
                    'total_campuses': total_campuses,
                    'active_campuses': active_campuses,
                    'total_revenue': float(total_revenue),
                    'upcoming_sessions': upcoming_sessions,
                    'today_sessions': today_sessions
                },
                'charts': {
                    'revenue_by_month': {
                        'labels': months_labels,
                        'data': revenue_by_month
                    },
                    'student_growth': {
                        'labels': student_growth_labels,
                        'data': student_growth
                    },
                    'students_by_campus': {
                        'labels': campus_names,
                        'data': student_by_campus
                    },
                    'teachers_by_campus': {
                        'labels': teachers_campus_names,
                        'data': teachers_by_campus
                    },
                    'class_distribution': class_distribution
                }
            })
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting admin dashboard stats: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'detail': f'Error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
