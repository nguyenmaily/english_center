from datetime import date, datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Session
from .serializers import SessionSerializer
from enrollment.models import Enrollment


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.select_related('class_session', 'teacher', 'room', 'skill').all()
    serializer_class = SessionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by class
        class_id = self.request.query_params.get('class_id')
        if class_id:
            queryset = queryset.filter(class_session_id=class_id)
        
        # Filter by teacher
        teacher_id = self.request.query_params.get('teacher_id')
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(study_date__gte=start_date)
        
        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(study_date__lte=end_date)
        
        return queryset.order_by('-study_date', 'start_time')

    @action(detail=False, methods=['get'], url_path='my-schedule')
    def my_schedule(self, request):
        """Lịch học của student"""
        student_id = request.query_params.get('student_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not student_id:
            return Response({'detail': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Lấy danh sách class_id của student
        class_ids = list(Enrollment.objects.filter(student_id=student_id).values_list('class_field_id', flat=True))
        
        # Lấy sessions của các class đó
        qs = Session.objects.filter(class_session_id__in=class_ids)
        
        if start_date:
            qs = qs.filter(study_date__gte=start_date)
        if end_date:
            qs = qs.filter(study_date__lte=end_date)
        
        qs = qs.order_by('study_date', 'start_time')
        return Response(SessionSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='my-upcoming')
    def my_upcoming(self, request):
        """Các buổi học sắp tới của student"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({'detail': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        today = date.today()
        class_ids = list(Enrollment.objects.filter(student_id=student_id).values_list('class_field_id', flat=True))
        qs = Session.objects.filter(class_session_id__in=class_ids, study_date__gte=today).order_by('study_date', 'start_time')
        
        return Response(SessionSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='my-today')
    def my_today(self, request):
        """Các buổi học hôm nay của teacher"""
        teacher_id = request.query_params.get('teacher_id')
        if not teacher_id:
            return Response({'detail': 'teacher_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        today = date.today()
        qs = Session.objects.filter(teacher_id=teacher_id, study_date=today).order_by('start_time')
        return Response(SessionSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='my-stats')
    def my_stats(self, request):
        """Thống kê buổi học của teacher"""
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
        checked_in = qs.filter(check_in__isnull=False).count()
        checked_out = qs.filter(check_out__isnull=False).count()
        
        data = {
            'total_sessions': total,
            'checked_in': checked_in,
            'checked_out': checked_out,
            'check_in_rate': round((checked_in / total * 100), 2) if total > 0 else 0,
            'check_out_rate': round((checked_out / total * 100), 2) if total > 0 else 0,
        }
        return Response(data)
    
    @action(detail=True, methods=['post'], url_path='check-in')
    def check_in(self, request, pk=None):
        """Check-in buổi học"""
        session = self.get_object()
        
        if session.check_in:
            return Response({'detail': 'Đã check-in rồi'}, status=status.HTTP_400_BAD_REQUEST)
        
        session.check_in = datetime.now().time()
        session.save(update_fields=['check_in', 'updated_at'])
        
        return Response({'detail': 'Check-in thành công', 'check_in': session.check_in})
    
    @action(detail=True, methods=['post'], url_path='check-out')
    def check_out(self, request, pk=None):
        """Check-out buổi học"""
        session = self.get_object()
        
        if not session.check_in:
            return Response({'detail': 'Chưa check-in'}, status=status.HTTP_400_BAD_REQUEST)
        
        if session.check_out:
            return Response({'detail': 'Đã check-out rồi'}, status=status.HTTP_400_BAD_REQUEST)
        
        session.check_out = datetime.now().time()
        session.save(update_fields=['check_out', 'updated_at'])
        
        return Response({'detail': 'Check-out thành công', 'check_out': session.check_out})



