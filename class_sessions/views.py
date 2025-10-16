from datetime import date
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Session, Attendance, Assignment, Submission
from enrollment.models import Enrollment


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = '__all__'


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all().order_by('-study_date')
    serializer_class = SessionSerializer

    @action(detail=False, methods=['get'], url_path='my-schedule')
    def my_schedule(self, request):
        student_id = request.query_params.get('student_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if not student_id:
            return Response({'detail': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        class_ids = list(Enrollment.objects.filter(student_id=student_id).values_list('class_id', flat=True))
        qs = Session.objects.filter(class_id__in=class_ids)
        if start_date:
            qs = qs.filter(study_date__gte=start_date)
        if end_date:
            qs = qs.filter(study_date__lte=end_date)
        qs = qs.order_by('study_date', 'start_time')
        return Response(SessionSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='my-upcoming')
    def my_upcoming(self, request):
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({'detail': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        today = date.today()
        class_ids = list(Enrollment.objects.filter(student_id=student_id).values_list('class_id', flat=True))
        qs = Session.objects.filter(class_id__in=class_ids, study_date__gte=today).order_by('study_date', 'start_time')
        return Response(SessionSerializer(qs, many=True).data)

    @action(detail=True, methods=['get'], url_path='assignments')
    def assignments(self, request, pk=None):
        session_id = pk
        items = Assignment.objects.filter(session_id=session_id).order_by('due_date')
        data = [{'id': a.id, 'title': a.title, 'description': a.description, 'due_date': a.due_date} for a in items]
        return Response(data)

    @action(detail=False, methods=['get'], url_path='my-today')
    def my_today(self, request):
        teacher_id = request.query_params.get('teacher_id')
        if not teacher_id:
            return Response({'detail': 'teacher_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        today = date.today()
        qs = Session.objects.filter(teacher_id=teacher_id, study_date=today).order_by('start_time')
        return Response(SessionSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='my-stats')
    def my_stats(self, request):
        teacher_id = request.query_params.get('teacher_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if not teacher_id:
            return Response({'detail': 'teacher_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        qs = Session.objects.filter(teacher_id=teacher_id)
        if start_date:
            qs = qs.filter(study_date__gte=start_date)
        if end_date:
            qs = qs.filter(study_date__lte=end_date)
        total = qs.count()
        att = Attendance.objects.filter(session_id__in=qs.values_list('id', flat=True))
        present = att.filter(status='present').count()
        absent = att.filter(status='absent').count()
        late = att.filter(status='late').count()
        excused = att.filter(status='excused').count()
        data = {
            'total_sessions': total,
            'attendance_counts': {
                'present': present,
                'absent': absent,
                'late': late,
                'excused': excused,
            },
        }
        return Response(data)


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all().order_by('id')
    serializer_class = AttendanceSerializer

    @action(detail=False, methods=['get'], url_path='my')
    def my(self, request):
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({'detail': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        qs = Attendance.objects.filter(student_id=student_id).order_by('-session_id')
        return Response(AttendanceSerializer(qs, many=True).data)



