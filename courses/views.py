
from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q

from authentication.permissions import PermissionMixin
from classes.models import Class
from courses.models import Course, Skill

from .serializers import (
    CourseSerializer, CourseDetailSerializer,
    SkillSerializer, SkillCreateUpdateSerializer,
    CourseClassSerializer, ClassDetailSerializer
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
        queryset = Course.objects.select_related('skill').all()
        
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
    
    def get_serializer_context(self):
        """Thêm request vào context để serializer có thể tính is_eligible"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


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


class CourseSkillView(PermissionMixin, generics.RetrieveAPIView):
    """
    GET /api/courses/{course_id}/skill/ - Lấy skill của course
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_courses',
    }
    serializer_class = SkillSerializer
    
    def get_object(self):
        course_id = self.kwargs['course_id']
        course = get_object_or_404(Course, pk=course_id)
        if not course.skill:
            from rest_framework.exceptions import NotFound
            raise NotFound('Course has no skill assigned')
        return course.skill
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })


class CourseAssignSkillView(PermissionMixin, APIView):
    """
    PATCH /api/courses/{course_id}/assign-skill/ - Gán skill cho course
    Body: {"skill_id": "uuid"}
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'PATCH': 'manage_courses',
    }
    
    def patch(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        skill_id = request.data.get('skill_id')
        
        if skill_id is None:
            # Cho phép xóa skill (set null)
            course.skill = None
            course.save()
            return Response({
                'success': True,
                'message': 'Skill removed from course'
            })
        
        try:
            skill = Skill.objects.get(pk=skill_id)
            course.skill = skill
            course.save()
            
            serializer = CourseDetailSerializer(course)
            return Response({
                'success': True,
                'message': 'Skill assigned successfully',
                'data': serializer.data
            })
        except Skill.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Skill not found'
            }, status=status.HTTP_404_NOT_FOUND)


class CourseEligibleClassesView(PermissionMixin, APIView):
    """
    GET /api/courses/courses/{course_id}/eligible-classes/
    
    Lấy danh sách lớp học eligible cho khóa học
    Filter:
    - course_id = course_id
    - status = 'planned' (chỉ lớp chưa bắt đầu)
    - teacher_id IS NOT NULL (phải có giáo viên)
    - current_student_count < limit_slot (còn slot)
    - Query param: campus_id (optional)
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_classes',
    }
    
    def get(self, request, course_id):
        from classes.models import Class
        
        course = get_object_or_404(Course, pk=course_id)
        
        # Filter classes
        queryset = Class.objects.filter(
            course=course,
            status=Class.Status.PLANNED,
            teacher__isnull=False
        ).select_related('teacher', 'campus', 'course')
        
        # Filter theo campus (optional)
        campus_id = request.query_params.get('campus_id')
        if campus_id:
            queryset = queryset.filter(campus_id=campus_id)
        
        # Tính is_available và available_slots
        result = []
        for cls in queryset:
            # Kiểm tra còn slot không
            is_available = (
                cls.status == Class.Status.PLANNED and
                cls.teacher_id is not None and
                (cls.limit_slot is None or cls.current_student_count < cls.limit_slot)
            )
            
            # Tính available_slots
            if cls.limit_slot is None:
                available_slots = None  # Không giới hạn
            else:
                available_slots = max(0, cls.limit_slot - cls.current_student_count)
            
            # Format weekday
            weekday_names = {
                1: 'Thứ 2',
                2: 'Thứ 3',
                3: 'Thứ 4',
                4: 'Thứ 5',
                5: 'Thứ 6',
                6: 'Thứ 7',
                7: 'Chủ nhật'
            }
            weekday_display = [weekday_names.get(d, str(d)) for d in (cls.weekday or [])]
            
            class_data = {
                'id': str(cls.id),
                'name': cls.name,
                'teacher_name': cls.teacher.user_account.fullname if cls.teacher else None,
                'teacher_id': str(cls.teacher.id) if cls.teacher else None,
                'start_date': cls.start_date.isoformat() if cls.start_date else None,
                'end_date': cls.end_date.isoformat() if cls.end_date else None,
                'current_student_count': cls.current_student_count,
                'limit_slot': cls.limit_slot,
                'available_slots': available_slots,
                'status': cls.status,
                'is_available': is_available,
                'fee': course.fee,
                'campus': {
                    'id': str(cls.campus.id) if cls.campus else None,
                    'name': cls.campus.name if cls.campus else None
                } if cls.campus else None,
                'weekday': cls.weekday or [],
                'weekday_display': weekday_display,
                'time_slot': cls.time_slot
            }
            
            result.append(class_data)
        
        return Response({
            'success': True,
            'data': result
        })


class CourseClassesListView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/courses/{course_id}/classes - Danh sách lớp học của khóa học
    
    Query params:
    - status: Lọc theo trạng thái (planned, ongoing, completed, cancelled)
    - teacher_assigned: true/false - Lọc lớp đã/chưa có giáo viên
    - is_public: true/false - Lọc lớp public
    """
    serializer_class = CourseClassSerializer
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
    serializer_class = CourseClassSerializer
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
        return CourseClassSerializer


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
