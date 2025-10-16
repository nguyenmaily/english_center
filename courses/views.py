from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q

from authentication.permissions import PermissionMixin
from .models import Course, Skill, Class
from .serializers import (
    CourseSerializer, CourseDetailSerializer,
    SkillSerializer, SkillCreateUpdateSerializer,
    ClassSerializer, ClassDetailSerializer
)


# ==================== COURSE VIEWS ====================

class CourseListCreateView(PermissionMixin, generics.ListCreateAPIView):
    """
    GET /api/courses/ - Lấy danh sách khóa học
    POST /api/courses/ - Tạo khóa học mới (cần quyền: manage_courses)
    
    Query params:
    - max_entry_score: Lọc khóa học phù hợp với điểm test của học viên
    - level: Lọc theo level
    """
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_courses',
        'POST': 'manage_courses',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'level', 'fee', 'total_sessions']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = Course.objects.all()
        
        # Filter theo max_entry_score (cho học viên đăng ký)
        max_entry_score = self.request.query_params.get('max_entry_score')
        if max_entry_score:
            try:
                score = int(max_entry_score)
                # Lọc các khóa có min_entry_score <= điểm test của học viên
                # hoặc không có yêu cầu điểm đầu vào
                queryset = queryset.filter(
                    Q(min_entry_score__lte=score) | Q(min_entry_score__isnull=True)
                )
            except ValueError:
                pass
        
        return queryset


class CourseDetailView(PermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/courses/{id}/ - Xem chi tiết khóa học
    PUT /api/courses/{id}/ - Sửa khóa học (cần quyền: manage_courses)
    PATCH /api/courses/{id}/ - Sửa khóa học (cần quyền: manage_courses)
    DELETE /api/courses/{id}/ - Xóa khóa học (cần quyền: manage_courses)
    """
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_courses',
        'PUT': 'manage_courses',
        'PATCH': 'manage_courses',
        'DELETE': 'manage_courses',
    }
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CourseDetailSerializer
        return CourseSerializer


class CourseSkillsListView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/courses/{course_id}/skills - Danh sách kỹ năng trong khóa học
    """
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_courses',
    }
    
    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return Skill.objects.filter(course_id=course_id)


class CourseSkillsCreateView(PermissionMixin, generics.CreateAPIView):
    """
    POST /api/courses/{course_id}/skills - Thêm skill mới vào khóa học
    """
    serializer_class = SkillCreateUpdateSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'POST': 'manage_courses',
    }
    
    def perform_create(self, serializer):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, pk=course_id)
        serializer.save(course=course)


class CourseClassesListView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/courses/{course_id}/classes - Danh sách lớp học của khóa học
    
    Query params:
    - status: Lọc theo trạng thái (planned, ongoing, completed, cancelled)
    - teacher_assigned: true/false - Lọc lớp đã/chưa có giáo viên
    - is_public: true/false - Lọc lớp public
    """
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_courses',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'is_public']
    search_fields = ['name']
    
    def get_queryset(self):
        course_id = self.kwargs['course_id']
        queryset = Class.objects.filter(course_id=course_id).select_related(
            'course', 'teacher', 'teacher__user_account', 'campus', 'manager', 'manager__user_account'
        )
        
        # Filter theo teacher_assigned
        teacher_assigned = self.request.query_params.get('teacher_assigned')
        if teacher_assigned is not None:
            if teacher_assigned.lower() == 'true':
                queryset = queryset.exclude(teacher__isnull=True)
            elif teacher_assigned.lower() == 'false':
                queryset = queryset.filter(teacher__isnull=True)
        
        return queryset


# ==================== SKILL VIEWS ====================

class SkillDetailView(PermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/skills/{id}/ - Xem chi tiết skill
    PUT /api/skills/{id}/ - Cập nhật skill (cần quyền: manage_courses)
    PATCH /api/skills/{id}/ - Cập nhật skill (cần quyền: manage_courses)
    DELETE /api/skills/{id}/ - Xóa skill (cần quyền: manage_courses)
    """
    queryset = Skill.objects.all()
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_courses',
        'PUT': 'manage_courses',
        'PATCH': 'manage_courses',
        'DELETE': 'manage_courses',
    }
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SkillSerializer
        return SkillCreateUpdateSerializer


# ==================== CLASS VIEWS ====================

class ClassListCreateView(PermissionMixin, generics.ListCreateAPIView):
    """
    GET /api/classes/ - Lấy danh sách lớp học
    POST /api/classes/ - Tạo lớp học mới (cần quyền: manage_classes)
    """
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_classes',
        'POST': 'manage_classes',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course', 'teacher', 'campus', 'manager', 'status', 'is_public']
    search_fields = ['name', 'course__name']
    ordering_fields = ['name', 'start_date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Class.objects.select_related(
            'course', 'teacher', 'teacher__user_account', 'campus', 'manager', 'manager__user_account'
        ).all()
        
        # Filter theo teacher_assigned
        teacher_assigned = self.request.query_params.get('teacher_assigned')
        if teacher_assigned is not None:
            if teacher_assigned.lower() == 'true':
                queryset = queryset.exclude(teacher__isnull=True)
            elif teacher_assigned.lower() == 'false':
                queryset = queryset.filter(teacher__isnull=True)
        
        return queryset


class ClassDetailView(PermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/classes/{id}/ - Xem chi tiết lớp học
    PUT /api/classes/{id}/ - Cập nhật lớp học (cần quyền: manage_classes)
    PATCH /api/classes/{id}/ - Cập nhật lớp học (cần quyền: manage_classes)
    DELETE /api/classes/{id}/ - Xóa lớp học (cần quyền: manage_classes)
    """
    queryset = Class.objects.select_related(
        'course', 'teacher', 'teacher__user_account', 'campus', 'manager', 'manager__user_account'
    ).all()
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_classes',
        'PUT': 'manage_classes',
        'PATCH': 'manage_classes',
        'DELETE': 'manage_classes',
    }
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ClassDetailSerializer
        return ClassSerializer


class ClassAssignTeacherView(PermissionMixin, APIView):
    """
    PATCH /api/classes/{id}/assign-teacher/ - Gán giáo viên cho lớp
    Body: {"teacher_id": "uuid"}
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'PATCH': 'manage_classes',
    }
    
    def patch(self, request, pk):
        from users.models import Teacher
        
        class_obj = get_object_or_404(Class, pk=pk)
        teacher_id = request.data.get('teacher_id')
        
        if not teacher_id:
            return Response(
                {'error': 'teacher_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            teacher = Teacher.objects.get(pk=teacher_id)
            class_obj.teacher = teacher
            class_obj.save()
            
            serializer = ClassDetailSerializer(class_obj)
            return Response(serializer.data)
        except Teacher.DoesNotExist:
            return Response(
                {'error': 'Teacher not found'},
                status=status.HTTP_404_NOT_FOUND
            )
