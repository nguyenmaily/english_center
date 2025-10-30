from django.contrib.auth import get_user_model
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q

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
    filterset_fields = ['roleid__name']
    search_fields = ['username', 'email', 'fullname', 'phone']
    ordering_fields = ['username', 'date_joined']
    ordering = ['-date_joined']
    
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
        
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(roleid__name=role)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserWithProfileSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        response_serializer = UserWithProfileSerializer(user)
        
        return Response({
            'success': True,
            'message': f'{user.roleid.name.title()} created successfully',
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
            
            return queryset.filter(
                Q(id__in=teacher_user_ids) | 
                Q(id__in=manager_user_ids) |
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
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        response_serializer = UserWithProfileSerializer(instance)
        
        return Response({
            'success': True,
            'message': 'User updated successfully',
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
    """GET /api/students/ - Danh sách students"""
    permission_classes = [IsAuthenticated]
    permission_map = {'GET': 'view_students'}
    serializer_class = StudentSerializer
    queryset = Student.objects.select_related('user_account').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['commitment_status']
    search_fields = ['user_account__fullname', 'user_account__username']
    ordering = ['user_account__fullname']
