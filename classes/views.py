from datetime import timedelta
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Class
from class_sessions.models import Session


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = '__all__'


class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all().order_by('id')
    serializer_class = ClassSerializer

    def perform_create(self, serializer):
        cls = serializer.save()
        # Session generation can be handled separately if needed

    def perform_update(self, serializer):
        cls = serializer.save()
        # Optional: regenerate sessions if schedule changed and no teacher conflict handling yet
        # For now, regenerate if days_of_week/start_time/end_time changed would require tracking previous values.
        # Keep simple: do nothing automatically.
        return cls

    def _maybe_generate_sessions(self, cls: Class, time_slot):
        """Generate sessions based on time_slot (e.g., '18:30-20:30')"""
        if not (cls.start_date and cls.end_date and time_slot and cls.weekday):
            return
        
        # Parse time_slot (e.g., '18:30-20:30')
        try:
            start_str, end_str = time_slot.split('-')
            from datetime import time
            start_time = time.fromisoformat(start_str)
            end_time = time.fromisoformat(end_str)
        except:
            return
            
        wanted = set(int(d) for d in cls.weekday)
        current = cls.start_date
        while current <= cls.end_date:
            # In DB: 1=Mon .. 7=Sun; in Python weekday(): 0=Mon .. 6=Sun
            if (current.weekday() + 1) in wanted:
                Session.objects.create(
                    study_date=current,
                    start_time=start_time,
                    end_time=end_time,
                    class_id=cls.id,
                )
            current = current + timedelta(days=1)

    @action(detail=True, methods=['get'], url_path='sessions')
    def list_sessions(self, request, pk=None):
        cls = self.get_object()
        sessions = Session.objects.filter(class_id=cls.id).order_by('study_date', 'start_time')
        from class_sessions.views import SessionSerializer  # local import to avoid circular
        data = SessionSerializer(sessions, many=True).data
        return Response(data)

    @action(detail=False, methods=['get'], url_path='my')
    def my_classes(self, request):
        # Expect request.user to be authenticated and mapped to teacher_id externally
        teacher_id = request.query_params.get('teacher_id')
        if not teacher_id:
            return Response({'detail': 'teacher_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        qs = Class.objects.filter(teacher_id=teacher_id).order_by('-start_date')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='register-teacher')
    def register_teacher(self, request, pk=None):
        cls = self.get_object()
        teacher_id = request.data.get('teacher_id')
        if not teacher_id:
            return Response({'detail': 'teacher_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if cls.teacher_id:
            return Response({'detail': 'Class already has a teacher'}, status=status.HTTP_400_BAD_REQUEST)
        # Check schedule conflict: compare sessions for this class with sessions of teacher's current classes
        class_sessions = list(Session.objects.filter(class_id=cls.id))
        teacher_classes = Class.objects.filter(teacher_id=teacher_id).values_list('id', flat=True)
        conflict = Session.objects.filter(class_id__in=teacher_classes).filter(
            study_date__in=[s.study_date for s in class_sessions]
        )
        # Coarse conflict: same date and overlapping time
        for s in class_sessions:
            if conflict.filter(study_date=s.study_date, start_time__lt=s.end_time, end_time__gt=s.start_time).exists():
                return Response({'detail': 'Bạn đã có lớp vào thời gian này'}, status=status.HTTP_400_BAD_REQUEST)
        cls.teacher_id = teacher_id
        cls.save(update_fields=['teacher_id'])
        return Response({'detail': 'Registered successfully'})

    @action(detail=True, methods=['post'], url_path='assign-teacher')
    def assign_teacher(self, request, pk=None):
        cls = self.get_object()
        teacher_id = request.data.get('teacher_id')
        if not teacher_id:
            return Response({'detail': 'teacher_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        cls.teacher_id = teacher_id
        cls.save(update_fields=['teacher_id'])
        return Response({'detail': 'Teacher assigned'})

    @action(detail=True, methods=['delete'], url_path='teacher')
    def remove_teacher(self, request, pk=None):
        cls = self.get_object()
        cls.teacher_id = None
        cls.save(update_fields=['teacher_id'])
        return Response(status=status.HTTP_204_NO_CONTENT)

# Create your views here.
