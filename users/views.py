# users/views.py
from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth import get_user_model

from authentication.permissions import PermissionMixin
from .models import Teacher, Manager, Student
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, TeacherSerializer, TeacherDetailSerializer,
    ManagerSerializer, StudentSerializer
)

User = get_user_model()


# ==================== PROFILE VIEWS ====================

class MyProfileView(APIView):
    """
    GET /api/users/me/ - Xem thông tin cá nhân
    PUT /api/users/me/ - Cập nhật thông tin cá nhân
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Lấy thông tin profile của user đang đăng nhập
        Không cần permission đặc biệt vì đây là thông tin của chính mình
        """
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """
        Cập nhật thông tin profile của user đang đăng nhập
        Không cần permission đặc biệt vì đây là thông tin của chính mình
        """
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    """
    POST /api/users/change-password/ - Đổi mật khẩu
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Đổi mật khẩu của user đang đăng nhập
        Không cần permission đặc biệt vì đây là mật khẩu của chính mình
        """
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Kiểm tra mật khẩu cũ
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Old password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Đổi mật khẩu
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully'})


# ==================== USER MANAGEMENT VIEWS ====================

class UserListCreateView(PermissionMixin, generics.ListCreateAPIView):
    """
    GET /api/users/ - Lấy danh sách người dùng (cần quyền: view_users)
    POST /api/users/ - Tạo người dùng mới (cần quyền: manage_users)
    
    Query params:
    - role: Lọc theo role (student, teacher, manager, admin)
    - search: Tìm kiếm theo username, email, fullname, phone
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_users',
        'POST': 'manage_users',
    }
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'fullname', 'phone']
    ordering_fields = ['username', 'email', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.all()
        
        # Filter theo role nếu có
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(roleid__name=role)
        
        # Nếu user là manager, chỉ xem users trong campus của mình
        if hasattr(user, 'manager_profile') and user.manager_profile.campus:
            campus = user.manager_profile.campus
            
            teacher_user_ids = Teacher.objects.filter(campus=campus).values_list('user_account_id', flat=True)
            manager_user_ids = Manager.objects.filter(campus=campus).values_list('user_account_id', flat=True)
            student_user_ids = Student.objects.filter(
                enrollments__class_enrolled__campus=campus
            ).distinct().values_list('user_account_id', flat=True)
            
            queryset = queryset.filter(
                Q(id__in=teacher_user_ids) | 
                Q(id__in=manager_user_ids) | 
                Q(id__in=student_user_ids)
            )
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer


class UserDetailView(PermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/users/{id}/ - Xem thông tin chi tiết user (cần quyền: view_users)
    PUT /api/users/{id}/ - Cập nhật toàn bộ user (cần quyền: manage_users)
    PATCH /api/users/{id}/ - Cập nhật một phần user (cần quyền: manage_users)
    DELETE /api/users/{id}/ - Xóa user (cần quyền: manage_users)
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_users',
        'PUT': 'manage_users',
        'PATCH': 'manage_users',
        'DELETE': 'manage_users',
    }
    queryset = User.objects.all()
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer


# ==================== TEACHER MANAGEMENT VIEWS ====================

class TeacherListView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/teachers/ - Danh sách giảng viên (cần quyền: view_teachers)
    
    Query params:
    - campus: Lọc theo campus
    - level: Lọc theo level
    - search: Tìm kiếm theo tên, username, specialization
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_teachers',
    }
    serializer_class = TeacherSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['campus', 'level']
    search_fields = ['user_account__fullname', 'user_account__username', 'specialization']
    ordering_fields = ['created_at', 'level']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Teacher.objects.select_related('user_account', 'campus').all()
        
        # Nếu user là manager, chỉ xem teachers trong campus của mình
        if hasattr(user, 'manager_profile') and user.manager_profile.campus:
            queryset = queryset.filter(campus=user.manager_profile.campus)
        
        return queryset


class TeacherDetailView(PermissionMixin, generics.RetrieveUpdateAPIView):
    """
    GET /api/teachers/{id}/ - Xem chi tiết giảng viên (cần quyền: view_teachers)
    PUT /api/teachers/{id}/ - Cập nhật toàn bộ thông tin giảng viên (cần quyền: manage_teachers)
    PATCH /api/teachers/{id}/ - Cập nhật một phần thông tin giảng viên (cần quyền: manage_teachers)
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_teachers',
        'PUT': 'manage_teachers',
        'PATCH': 'manage_teachers',
    }
    serializer_class = TeacherDetailSerializer
    queryset = Teacher.objects.select_related('user_account', 'campus').all()
    lookup_field = 'pk'
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # Nếu user là manager, chỉ xem teachers trong campus của mình
        if hasattr(user, 'manager_profile') and user.manager_profile.campus:
            queryset = queryset.filter(campus=user.manager_profile.campus)
        
        return queryset


# ==================== MANAGER MANAGEMENT VIEWS ====================

class ManagerListView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/managers/ - Danh sách quản lý (cần quyền: view_managers)
    
    Query params:
    - campus: Lọc theo campus
    - search: Tìm kiếm theo tên, username
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_managers',
    }
    serializer_class = ManagerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['campus']
    search_fields = ['user_account__fullname', 'user_account__username']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Manager.objects.select_related('user_account', 'campus').all()
        
        # Nếu user là manager, chỉ xem managers trong campus của mình
        if hasattr(user, 'manager_profile') and user.manager_profile.campus:
            queryset = queryset.filter(campus=user.manager_profile.campus)
        
        return queryset


class ManagerDetailView(PermissionMixin, generics.RetrieveUpdateAPIView):
    """
    GET /api/managers/{id}/ - Xem chi tiết quản lý (cần quyền: view_managers)
    PUT /api/managers/{id}/ - Cập nhật toàn bộ thông tin quản lý (cần quyền: manage_managers)
    PATCH /api/managers/{id}/ - Cập nhật một phần thông tin quản lý (cần quyền: manage_managers)
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_managers',
        'PUT': 'manage_managers',
        'PATCH': 'manage_managers',
    }
    serializer_class = ManagerSerializer
    queryset = Manager.objects.select_related('user_account', 'campus').all()
    lookup_field = 'pk'
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # Nếu user là manager, chỉ xem managers trong campus của mình
        if hasattr(user, 'manager_profile') and user.manager_profile.campus:
            queryset = queryset.filter(campus=user.manager_profile.campus)
        
        return queryset


# ==================== STUDENT MANAGEMENT VIEWS ====================

class StudentListView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/students/ - Danh sách học viên (cần quyền: view_students)
    
    Query params:
    - class_id: Lọc theo lớp học
    - search: Tìm kiếm theo tên, username, student_code
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_students',
    }
    serializer_class = StudentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user_account__fullname', 'user_account__username', 'student_code']
    ordering_fields = ['created_at', 'student_code']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Student.objects.select_related('user_account').all()
        
        # Filter theo class nếu có
        class_id = self.request.query_params.get('class_id')
        if class_id:
            queryset = queryset.filter(enrollments__class_enrolled_id=class_id).distinct()
        
        # Nếu user là teacher, chỉ xem students trong các lớp mình dạy
        if hasattr(user, 'teacher_profile'):
            queryset = queryset.filter(
                enrollments__class_enrolled__teacher=user.teacher_profile
            ).distinct()
        
        # Nếu user là manager, chỉ xem students trong campus của mình
        if hasattr(user, 'manager_profile') and user.manager_profile.campus:
            queryset = queryset.filter(
                enrollments__class_enrolled__campus=user.manager_profile.campus
            ).distinct()
        
        return queryset




# ==================== USER ACTIVATION VIEWS ====================

class UserActivateView(PermissionMixin, APIView):
    """
    PATCH /api/users/{id}/activate/ - Kích hoạt tài khoản user (cần quyền: manage_users)
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'PATCH': 'manage_users',
    }
    
    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = True
        user.save()
        return Response({
            'message': 'User activated successfully',
            'user': UserSerializer(user).data
        })


class UserDeactivateView(PermissionMixin, APIView):
    """
    PATCH /api/users/{id}/deactivate/ - Vô hiệu hóa tài khoản user (cần quyền: manage_users)
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'PATCH': 'manage_users',
    }
    
    def patch(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        
        # Không cho phép tự vô hiệu hóa chính mình
        if user.id == request.user.id:
            return Response(
                {'error': 'You cannot deactivate your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_active = False
        user.save()
        return Response({
            'message': 'User deactivated successfully',
            'user': UserSerializer(user).data
        })
