from django.contrib.auth import get_user_model
from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count
from datetime import datetime, timedelta

from authentication.permissions import PermissionMixin
from core.pagination import CustomPagination
from .models import Teacher, Manager, Student
from classes.models import Class
from courses.models import Course
from proficiency.models import StudentCertificate
from django.utils import timezone
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
        from django.db import transaction, connection
        
        instance = self.get_object()
        
        if instance.id == request.user.id:
            return Response({
                'success': False,
                'error': 'You cannot delete your own account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Sử dụng transaction để đảm bảo atomicity
        try:
            with transaction.atomic():
                # Xóa tất cả dữ liệu liên quan bằng raw SQL để tránh foreign key constraint issues
                # Vì nhiều model có managed = False
                with connection.cursor() as cursor:
                    # Kiểm tra nếu user là student, xóa enrollments và các dữ liệu liên quan trước
                    if hasattr(instance, 'student_profile'):
                        student = instance.student_profile
                        student_id = student.id
                        
                        # 1. Xóa student_answers (tham chiếu đến submissions)
                        cursor.execute(
                            "DELETE FROM student_answers WHERE submission_id IN (SELECT id FROM submissions WHERE student_id = %s)",
                            [str(student_id)]
                        )
                        
                        # 2. Xóa submissions
                        cursor.execute(
                            "DELETE FROM submissions WHERE student_id = %s",
                            [str(student_id)]
                        )
                        
                        # 3. Xóa attendances
                        cursor.execute(
                            "DELETE FROM attendances WHERE student_id = %s",
                            [str(student_id)]
                        )
                        
                        # 4. Xóa enrollments
                        cursor.execute(
                            "DELETE FROM enrollments WHERE student_id = %s",
                            [str(student_id)]
                        )
                        
                        # 5. Xóa student_certificates
                        cursor.execute(
                            "DELETE FROM student_certificates WHERE student_id = %s",
                            [str(student_id)]
                        )
                        
                        # 6. Xóa student_profile bằng raw SQL (vì model có managed = False)
                        cursor.execute(
                            "DELETE FROM students WHERE id = %s",
                            [str(student_id)]
                        )
                    
                    # 7. Xóa user bằng raw SQL (vì UserAccount model có managed = False)
                    # Cần xóa user sau khi đã xóa tất cả dữ liệu liên quan
                    cursor.execute(
                        "DELETE FROM user_accounts WHERE id = %s",
                        [str(instance.id)]
                    )
            
            return Response({
                'success': True,
                'message': 'User deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            # Log lỗi chi tiết để debug
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            error_trace = traceback.format_exc()
            logger.error(f'Error deleting user {instance.id}: {str(e)}\n{error_trace}')
            
            # Trả về thông báo lỗi chi tiết hơn
            error_message = str(e)
            error_detail = None
            
            # Kiểm tra loại lỗi
            if 'foreign key' in error_message.lower() or 'constraint' in error_message.lower():
                error_message = 'Không thể xóa người dùng vì còn dữ liệu liên quan. Vui lòng xóa các đăng ký lớp học và dữ liệu liên quan trước.'
                error_detail = str(e)
            elif 'violates' in error_message.lower():
                error_message = 'Không thể xóa người dùng do ràng buộc dữ liệu. Vui lòng kiểm tra các mối quan hệ dữ liệu.'
                error_detail = str(e)
            elif 'does not exist' in error_message.lower():
                error_message = 'Người dùng không tồn tại hoặc đã bị xóa.'
            else:
                error_detail = str(e)
            
            # Kiểm tra xem user có phải là staff/admin không để hiển thị chi tiết
            is_staff = hasattr(request.user, 'is_staff') and request.user.is_staff
            is_admin = hasattr(request.user, 'roleid') and request.user.roleid and request.user.roleid.name == 'admin'
            
            return Response({
                'success': False,
                'error': error_message,
                'detail': error_detail if (is_staff or is_admin) else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    pagination_class = CustomPagination
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
    pagination_class = CustomPagination
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
# ==================== TEACHER CLASS REGISTRATION ====================

# Level system: beginner < intermediate < advanced < expert < master
LEVEL_ORDER = {
    'beginner': 1,
    'intermediate': 2,
    'advanced': 3,
    'expert': 4,
    'master': 5
}

def compare_levels(level1, level2):
    """
    So sánh 2 level
    Returns: -1 nếu level1 < level2, 0 nếu bằng, 1 nếu level1 > level2
    """
    if not level1 or not level2:
        return None
    
    level1_lower = level1.lower().strip()
    level2_lower = level2.lower().strip()
    
    order1 = LEVEL_ORDER.get(level1_lower)
    order2 = LEVEL_ORDER.get(level2_lower)
    
    if order1 is None or order2 is None:
        return None
    
    if order1 < order2:
        return -1
    elif order1 > order2:
        return 1
    else:
        return 0

def is_level_eligible(course_level, teacher_level):
    """
    Kiểm tra xem teacher có đủ level để dạy course không
    Returns: True nếu course.level <= teacher.level
    """
    if not course_level or not teacher_level:
        return False
    
    comparison = compare_levels(course_level, teacher_level)
    if comparison is None:
        return False
    
    # course.level <= teacher.level
    return comparison <= 0

def has_date_range_overlap(start1, end1, start2, end2):
    """
    Kiểm tra 2 khoảng thời gian có trùng nhau không
    Returns: True nếu có overlap
    Logic: (start1 <= end2) AND (start2 <= end1)
    """
    if not all([start1, end1, start2, end2]):
        return False
    
    return (start1 <= end2) and (start2 <= end1)

def has_weekday_overlap(weekdays1, weekdays2):
    """
    Kiểm tra 2 danh sách weekday có trùng nhau không
    Returns: True nếu có ít nhất 1 weekday trùng
    """
    if not weekdays1 or not weekdays2:
        return False
    
    return bool(set(weekdays1) & set(weekdays2))

def parse_time_slot(time_slot_str):
    """
    Parse time_slot string thành dict với start_time và end_time
    Ví dụ: "18:30" -> {start: "18:30", end: "18:30"}
    Ví dụ: "18:30-20:30" -> {start: "18:30", end: "20:30"}
    Returns: dict hoặc None nếu không parse được
    """
    if not time_slot_str:
        return None
    
    time_slot_str = time_slot_str.strip()
    
    # Nếu có dấu "-", tách thành start và end
    if '-' in time_slot_str:
        parts = time_slot_str.split('-')
        if len(parts) == 2:
            return {
                'start': parts[0].strip(),
                'end': parts[1].strip()
            }
    
    # Nếu không có dấu "-", coi như start = end
    return {
        'start': time_slot_str,
        'end': time_slot_str
    }

def has_time_slot_overlap(time_slot1, time_slot2):
    """
    Kiểm tra 2 time_slot có trùng nhau không
    Returns: True nếu có overlap
    Logic: (start1 < end2) AND (start2 < end1)
    """
    slot1 = parse_time_slot(time_slot1)
    slot2 = parse_time_slot(time_slot2)
    
    if not slot1 or not slot2:
        return False
    
    try:
        # Parse time strings thành minutes từ 00:00
        def time_to_minutes(time_str):
            parts = time_str.split(':')
            if len(parts) != 2:
                return None
            hours = int(parts[0])
            minutes = int(parts[1])
            return hours * 60 + minutes
        
        start1 = time_to_minutes(slot1['start'])
        end1 = time_to_minutes(slot1['end'])
        start2 = time_to_minutes(slot2['start'])
        end2 = time_to_minutes(slot2['end'])
        
        if any(x is None for x in [start1, end1, start2, end2]):
            return False
        
        # Two ranges [a, b] and [c, d] overlap if: a < d AND c < b
        return (start1 < end2) and (start2 < end1)
    except (ValueError, AttributeError):
        return False

def check_schedule_conflict(new_class, existing_class):
    """
    Kiểm tra xem new_class có trùng lịch với existing_class không
    Logic ngắn mạch (short-circuit):
    1. Check date range overlap -> không trùng thì pass
    2. Check weekday overlap -> không trùng thì pass
    3. Check time slot overlap -> không trùng thì pass
    4. Nếu tất cả đều trùng -> return True (có conflict)
    
    Returns: True nếu có conflict, False nếu không có
    """
    # 1. Check date range overlap
    if not has_date_range_overlap(
        new_class.start_date,
        new_class.end_date,
        existing_class.start_date,
        existing_class.end_date
    ):
        return False  # Không trùng date range -> pass
    
    # 2. Check weekday overlap
    if not has_weekday_overlap(new_class.weekday, existing_class.weekday):
        return False  # Không trùng weekday -> pass
    
    # 3. Check time slot overlap
    if not has_time_slot_overlap(new_class.time_slot, existing_class.time_slot):
        return False  # Không trùng time slot -> pass
    
    # Tất cả đều trùng -> có conflict
    return True

class TeacherAvailableClassesView(APIView):
    """
    GET /api/users/teachers/available-classes/
    Lấy danh sách lớp học chưa có giáo viên và level <= level của giáo viên
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Lấy teacher profile của user hiện tại
            user = request.user
            try:
                teacher = Teacher.objects.get(user_account=user)
            except Teacher.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Bạn không phải là giáo viên'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Kiểm tra teacher có level không
            if not teacher.level:
                return Response({
                    'success': False,
                    'error': 'Giáo viên chưa được gán level'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            teacher_level = teacher.level.lower().strip()
            
            # Lấy danh sách lớp chưa có giáo viên, status = 'planned'
            available_classes = Class.objects.filter(
                teacher__isnull=True,
                status='planned'
            ).select_related('course', 'campus')
            
            # Filter theo campus của teacher (nếu có)
            if teacher.campus:
                available_classes = available_classes.filter(campus=teacher.campus)
            
            # Filter theo level: chỉ lấy lớp có course.level <= teacher.level
            eligible_classes = []
            skipped_no_course = 0
            skipped_no_level = 0
            skipped_level_not_eligible = 0
            
            for cls in available_classes:
                # Check course tồn tại
                if not cls.course:
                    skipped_no_course += 1
                    continue
                
                # Check course có level không
                if not cls.course.level:
                    skipped_no_level += 1
                    continue
                
                course_level = cls.course.level.lower().strip()
                
                # Check level eligibility
                if not is_level_eligible(course_level, teacher_level):
                    skipped_level_not_eligible += 1
                    continue
                
                eligible_classes.append(cls)
            
            # Serialize data
            classes_data = []
            for cls in eligible_classes:
                classes_data.append({
                    'id': str(cls.id),
                    'name': cls.name,
                    'course_name': cls.course.name if cls.course else None,
                    'course_level': cls.course.level if cls.course else None,
                    'teacher_level': teacher.level,
                    'is_level_eligible': True,
                    'start_date': cls.start_date.isoformat() if cls.start_date else None,
                    'end_date': cls.end_date.isoformat() if cls.end_date else None,
                    'weekday': cls.weekday if cls.weekday else [],
                    'time_slot': cls.time_slot or '',
                    'campus': {
                        'id': str(cls.campus.id) if cls.campus else None,
                        'name': cls.campus.name if cls.campus else None
                    } if cls.campus else None,
                    'current_student_count': cls.current_student_count,
                    'limit_slot': cls.limit_slot
                })
            
            return Response({
                'success': True,
                'data': classes_data,
                'debug': {
                    'teacher_level': teacher.level,
                    'teacher_campus_id': str(teacher.campus.id) if teacher.campus else None,
                    'total_classes_found': len(available_classes),
                    'skipped_no_course': skipped_no_course,
                    'skipped_no_level': skipped_no_level,
                    'skipped_level_not_eligible': skipped_level_not_eligible,
                    'eligible_count': len(eligible_classes)
                }
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Lỗi khi lấy danh sách lớp: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TeacherRegisterClassView(APIView):
    """
    POST /api/users/teachers/register-class/
    Đăng ký dạy lớp (có check trùng lịch và level)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Lấy teacher profile
            user = request.user
            try:
                teacher = Teacher.objects.get(user_account=user)
            except Teacher.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Bạn không phải là giáo viên'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Kiểm tra teacher có level không
            if not teacher.level:
                return Response({
                    'success': False,
                    'error': 'Giáo viên chưa được gán level'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Lấy class_id từ request
            class_id = request.data.get('class_id')
            if not class_id:
                return Response({
                    'success': False,
                    'error': 'class_id là bắt buộc'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Lấy class
            try:
                new_class = Class.objects.select_related('course', 'campus').get(id=class_id)
            except Class.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Không tìm thấy lớp học'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validation 1: Class chưa có giáo viên
            if new_class.teacher:
                return Response({
                    'success': False,
                    'error': 'Lớp học đã có giáo viên'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validation 2: Class status phải là 'planned'
            if new_class.status != 'planned':
                return Response({
                    'success': False,
                    'error': f'Chỉ có thể đăng ký lớp ở trạng thái planned. Lớp hiện tại: {new_class.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validation 3: Level eligibility
            if not new_class.course or not new_class.course.level:
                return Response({
                    'success': False,
                    'error': 'Khóa học không có level'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            course_level = new_class.course.level.lower().strip()
            teacher_level = teacher.level.lower().strip()
            
            if not is_level_eligible(course_level, teacher_level):
                return Response({
                    'success': False,
                    'error': f'Bạn không đủ trình độ để dạy khóa học này. Yêu cầu level: {new_class.course.level}, level hiện tại của bạn: {teacher.level}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validation 4: Schedule conflict
            # Lấy tất cả lớp giáo viên đang dạy (ongoing và planned)
            existing_classes = Class.objects.filter(
                teacher=teacher,
                status__in=['ongoing', 'planned']
            ).exclude(id=class_id)
            
            for existing_class in existing_classes:
                if check_schedule_conflict(new_class, existing_class):
                    return Response({
                        'success': False,
                        'error': 'Bạn đã có lớp vào thời gian này'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Tất cả validation đều pass -> gán teacher cho class
            new_class.teacher = teacher
            new_class.save()
            
            return Response({
                'success': True,
                'message': 'Đăng ký lớp thành công',
                'data': {
                    'class_id': str(new_class.id),
                    'class_name': new_class.name
                }
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Lỗi khi đăng ký lớp: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TeacherCancelClassRegistrationView(APIView):
    """
    POST /api/users/teachers/cancel-class-registration/
    Hủy đăng ký lớp (chỉ được nếu lớp chưa có học viên)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Lấy teacher profile
            user = request.user
            try:
                teacher = Teacher.objects.get(user_account=user)
            except Teacher.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Bạn không phải là giáo viên'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Lấy class_id từ request
            class_id = request.data.get('class_id')
            if not class_id:
                return Response({
                    'success': False,
                    'error': 'class_id là bắt buộc'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Lấy class
            try:
                cls = Class.objects.get(id=class_id)
            except Class.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Không tìm thấy lớp học'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validation 1: Teacher phải là giáo viên của lớp này
            if cls.teacher != teacher:
                return Response({
                    'success': False,
                    'error': 'Bạn không phải là giáo viên của lớp này'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Validation 2: Class chưa có học viên
            if cls.current_student_count > 0:
                return Response({
                    'success': False,
                    'error': f'Không thể hủy đăng ký vì lớp đã có {cls.current_student_count} học viên đăng ký'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validation 3: Class status phải là 'planned'
            if cls.status != 'planned':
                return Response({
                    'success': False,
                    'error': f'Chỉ có thể hủy đăng ký lớp ở trạng thái planned. Lớp hiện tại: {cls.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Hủy đăng ký: xóa teacher khỏi class
            cls.teacher = None
            cls.save()
            
            return Response({
                'success': True,
                'message': 'Hủy đăng ký lớp thành công'
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'error': f'Lỗi khi hủy đăng ký lớp: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MyLevelView(PermissionMixin, APIView):
    """
    GET /api/users/students/my-level/ - Kiểm tra điểm trình độ của học viên
    
    Trả về điểm LR và SW hiện tại (VERIFIED và còn hạn)
    Nếu không có hoặc đã hết hạn → trả về null
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
        
        # Lấy điểm LR hiện tại (VERIFIED và còn hạn)
        current_lr = StudentCertificate.objects.filter(
            student=student,
            skill_group=StudentCertificate.SkillGroup.LR,
            status=StudentCertificate.Status.VERIFIED,
            expired_date__gte=today
        ).order_by('-test_date').first()
        
        # Lấy điểm SW hiện tại (VERIFIED và còn hạn)
        current_sw = StudentCertificate.objects.filter(
            student=student,
            skill_group=StudentCertificate.SkillGroup.SW,
            status=StudentCertificate.Status.VERIFIED,
            expired_date__gte=today
        ).order_by('-test_date').first()
        
        # Format response
        lr_data = None
        if current_lr:
            lr_data = {
                'score': current_lr.total_score,
                'test_date': current_lr.test_date.isoformat(),
                'expired_date': current_lr.expired_date.isoformat(),
                'source_type': current_lr.source_type
            }
        
        sw_data = None
        if current_sw:
            sw_data = {
                'score': current_sw.total_score,
                'test_date': current_sw.test_date.isoformat(),
                'expired_date': current_sw.expired_date.isoformat(),
                'source_type': current_sw.source_type
            }
        
        # Kiểm tra có cần message không
        message = None
        if not lr_data and not sw_data:
            message = 'Vui lòng cập nhật trình độ của bạn để chọn khóa học phù hợp'
        
        return Response({
            'success': True,
            'data': {
                'lr': lr_data,
                'sw': sw_data
            },
            'message': message
        })

