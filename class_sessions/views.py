from datetime import date, datetime
from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from .models import Session, Attendance
from enrollment.models import Enrollment


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['id', 'status', 'student_id', 'session_id']


class SessionSerializer(serializers.ModelSerializer):
    duration = serializers.ReadOnlyField()
    is_checked_in = serializers.ReadOnlyField()
    is_checked_out = serializers.ReadOnlyField()
    attendance_summary = serializers.SerializerMethodField()
    room_name = serializers.CharField(source='room.name', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    class_session_name = serializers.CharField(source='class_session.name', read_only=True)
    
    class Meta:
        model = Session
        fields = '__all__'
    
    def get_teacher_name(self, obj):
        """Get teacher's full name"""
        if obj.teacher and obj.teacher.user_account:
            user = obj.teacher.user_account
            return user.fullname if user.fullname else user.username
        return None
    
    def get_attendance_summary(self, obj):
        """Thống kê điểm danh của buổi học"""
        attendances = Attendance.objects.filter(session_id=obj.id)
        total = attendances.count()
        
        if total == 0:
            return None
        
        return {
            'total': total,
            'present': attendances.filter(status=Attendance.STATUS_PRESENT).count(),
            'absent': attendances.filter(status=Attendance.STATUS_ABSENT).count(),
            'late': attendances.filter(status=Attendance.STATUS_LATE).count(),
            'excused': attendances.filter(status=Attendance.STATUS_EXCUSED).count(),
        }


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
    
    def perform_create(self, serializer):
        """
        Tự động set teacher khi tạo session
        Ưu tiên:
        1. Nếu user là teacher, tự động set teacher_id từ request.user.teacher
        2. Nếu không, lấy teacher từ class_session nếu có
        """
        # Kiểm tra nếu user là teacher
        if hasattr(self.request.user, 'teacher'):
            teacher = self.request.user.teacher
            serializer.save(teacher=teacher)
        else:
            # Nếu không phải teacher, kiểm tra class có teacher không
            class_session = serializer.validated_data.get('class_session')
            if class_session:
                # class_session có thể là Class object hoặc ID
                if hasattr(class_session, 'teacher') and class_session.teacher:
                    serializer.save(teacher=class_session.teacher)
                elif hasattr(class_session, 'id'):
                    # Nếu là object nhưng chưa load teacher, load lại
                    from classes.models import Class
                    try:
                        class_obj = Class.objects.select_related('teacher').get(id=class_session.id)
                        if class_obj.teacher:
                            serializer.save(teacher=class_obj.teacher)
                        else:
                            serializer.save()
                    except Class.DoesNotExist:
                        serializer.save()
                else:
                    serializer.save()
            else:
                serializer.save()

    @action(detail=False, methods=['get'], url_path='my-schedule')
    def my_schedule(self, request):
        """
        Lịch học đầy đủ của student (tương tự như giáo viên)
        
        Query params:
        - student_id: UUID của học sinh (required)
        - start_date: YYYY-MM-DD (optional)
        - end_date: YYYY-MM-DD (optional)
        
        Returns:
        - sessions_by_date: Group sessions theo ngày
        - summary: Thống kê tổng quan
        - upcoming_sessions: Các buổi học sắp tới
        """
        from collections import defaultdict
        
        student_id = request.query_params.get('student_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not student_id:
            return Response({
                'success': False,
                'error': 'student_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Lấy danh sách class_id của student
        enrollments = Enrollment.objects.filter(student_id=student_id).select_related('class_id')
        class_ids = list(enrollments.values_list('class_id', flat=True))
        
        if not class_ids:
            return Response({
                'success': True,
                'data': {
                    'sessions_by_date': {},
                    'summary': {
                        'total_sessions': 0,
                        'completed_sessions': 0,
                        'upcoming_sessions': 0,
                        'today_sessions': 0
                    },
                    'upcoming_sessions': [],
                    'today_sessions': []
                }
            })
        
        # Lấy sessions của các class đó
        qs = Session.objects.filter(class_session_id__in=class_ids).select_related(
            'class_session', 'teacher', 'room', 'skill'
        )
        
        if start_date:
            qs = qs.filter(study_date__gte=start_date)
        if end_date:
            qs = qs.filter(study_date__lte=end_date)
        
        qs = qs.order_by('study_date', 'start_time')
        sessions = list(qs)
        
        # Nếu không có sessions trong DB → tính toán từ class info
        if not sessions:
            from classes.models import Class
            from datetime import timedelta
            
            # Lấy thông tin các lớp
            classes = Class.objects.filter(id__in=class_ids).select_related('course', 'teacher', 'campus')
            
            for cls in classes:
                if not (cls.start_date and cls.end_date and cls.weekday and cls.time_slot):
                    continue
                
                # Parse time_slot (ví dụ: "18:00-20:00")
                time_parts = cls.time_slot.split('-')
                start_time_str = time_parts[0].strip() if len(time_parts) > 0 else None
                end_time_str = time_parts[1].strip() if len(time_parts) > 1 else None
                
                if not start_time_str:
                    continue
                
                # Parse start_time và end_time
                from datetime import time as dt_time
                try:
                    start_time = dt_time.fromisoformat(start_time_str)
                    end_time = dt_time.fromisoformat(end_time_str) if end_time_str else None
                except:
                    continue
                
                current_date = cls.start_date
                
                while current_date <= cls.end_date:
                    # weekday: 1=Mon, 2=Tue, ..., 7=Sun
                    # Python weekday(): 0=Mon, 1=Tue, ..., 6=Sun
                    python_weekday = current_date.weekday() + 1
                    
                    # Filter by date range if provided
                    if start_date and current_date < start_date:
                        current_date += timedelta(days=1)
                        continue
                    if end_date and current_date > end_date:
                        break
                    
                    if python_weekday in cls.weekday:
                        # Tạo session object giả (không có trong DB)
                        from types import SimpleNamespace
                        fake_session = SimpleNamespace(
                            id=None,
                            study_date=current_date,
                            start_time=start_time,
                            end_time=end_time,
                            class_session=cls,
                            teacher=cls.teacher,
                            room=None,
                            skill=None,
                            check_in=None,
                            check_out=None
                        )
                        sessions.append(fake_session)
                    
                    current_date += timedelta(days=1)
        
        # Group sessions by date
        sessions_by_date = defaultdict(list)
        today = date.today()
        completed_count = 0
        upcoming_count = 0
        today_count = 0
        
        for session in sessions:
            # Serialize session (handle both real and fake sessions)
            if hasattr(session, 'id') and session.id is not None:
                # Real session from DB
                session_data = SessionSerializer(session).data
            else:
                # Fake session calculated from class info
                session_data = {
                    'id': None,
                    'study_date': str(session.study_date),
                    'start_time': session.start_time.strftime('%H:%M') if session.start_time else None,
                    'end_time': session.end_time.strftime('%H:%M') if session.end_time else None,
                    'class_session_id': str(session.class_session.id) if session.class_session else None,
                    'class_session_name': session.class_session.name if session.class_session else None,
                    'teacher_id': str(session.teacher.id) if session.teacher else None,
                    'teacher_name': session.teacher.user_account.fullname if session.teacher and session.teacher.user_account else None,
                    'room_id': None,
                    'room_name': None,
                    'skill_id': None,
                    'check_in': None,
                    'check_out': None,
                    'class_session': {
                        'id': str(session.class_session.id) if session.class_session else None,
                        'name': session.class_session.name if session.class_session else None,
                        'course': {
                            'id': str(session.class_session.course.id) if session.class_session and session.class_session.course else None,
                            'name': session.class_session.course.name if session.class_session and session.class_session.course else None,
                        } if session.class_session and session.class_session.course else None
                    } if session.class_session else None
                }
            
            sessions_by_date[str(session.study_date)].append(session_data)
            
            # Tính toán thống kê
            if session.study_date < today:
                completed_count += 1
            elif session.study_date > today:
                upcoming_count += 1
            else:
                today_count += 1
        
        # Lấy các buổi học sắp tới (tối đa 5 buổi) - từ sessions đã tính toán
        from datetime import time as dt_time
        upcoming_sessions_list = [s for s in sessions if s.study_date >= today]
        upcoming_sessions_list.sort(key=lambda x: (x.study_date, x.start_time or dt_time.min))
        upcoming_sessions_list = upcoming_sessions_list[:5]
        
        # Serialize upcoming sessions
        upcoming_sessions_serialized = []
        for session in upcoming_sessions_list:
            if hasattr(session, 'id') and session.id is not None:
                upcoming_sessions_serialized.append(SessionSerializer(session).data)
            else:
                # Fake session
                upcoming_sessions_serialized.append({
                    'id': None,
                    'study_date': str(session.study_date),
                    'start_time': session.start_time.strftime('%H:%M') if session.start_time else None,
                    'end_time': session.end_time.strftime('%H:%M') if session.end_time else None,
                    'class_session_name': session.class_session.name if session.class_session else None,
                    'teacher_name': session.teacher.user_account.fullname if session.teacher and session.teacher.user_account else None,
                    'room_name': None,
                    'class_session': {
                        'id': str(session.class_session.id) if session.class_session else None,
                        'name': session.class_session.name if session.class_session else None,
                        'course': {
                            'id': str(session.class_session.course.id) if session.class_session and session.class_session.course else None,
                            'name': session.class_session.course.name if session.class_session and session.class_session.course else None,
                        } if session.class_session and session.class_session.course else None
                    } if session.class_session else None
                })
        
        # Lấy các buổi học hôm nay - từ sessions đã tính toán
        today_sessions_list = [s for s in sessions if s.study_date == today]
        today_sessions_list.sort(key=lambda x: x.start_time or dt_time.min)
        
        # Serialize today sessions
        today_sessions_serialized = []
        for session in today_sessions_list:
            if hasattr(session, 'id') and session.id is not None:
                today_sessions_serialized.append(SessionSerializer(session).data)
            else:
                # Fake session
                today_sessions_serialized.append({
                    'id': None,
                    'study_date': str(session.study_date),
                    'start_time': session.start_time.strftime('%H:%M') if session.start_time else None,
                    'end_time': session.end_time.strftime('%H:%M') if session.end_time else None,
                    'class_session_name': session.class_session.name if session.class_session else None,
                    'teacher_name': session.teacher.user_account.fullname if session.teacher and session.teacher.user_account else None,
                    'room_name': None,
                    'class_session': {
                        'id': str(session.class_session.id) if session.class_session else None,
                        'name': session.class_session.name if session.class_session else None,
                        'course': {
                            'id': str(session.class_session.course.id) if session.class_session and session.class_session.course else None,
                            'name': session.class_session.course.name if session.class_session and session.class_session.course else None,
                        } if session.class_session and session.class_session.course else None
                    } if session.class_session else None
                })
        
        return Response({
            'success': True,
            'data': {
                'sessions_by_date': dict(sessions_by_date),
                'summary': {
                    'total_sessions': len(sessions),
                    'completed_sessions': completed_count,
                    'upcoming_sessions': upcoming_count,
                    'today_sessions': today_count
                },
                'upcoming_sessions': upcoming_sessions_serialized,
                'today_sessions': today_sessions_serialized
            }
        })

    @action(detail=False, methods=['get'], url_path='my-upcoming')
    def my_upcoming(self, request):
        """Các buổi học sắp tới của student"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({'detail': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        today = date.today()
        class_ids = list(Enrollment.objects.filter(student_id=student_id).values_list('class_id', flat=True))
        qs = Session.objects.filter(class_session_id__in=class_ids, study_date__gte=today).order_by('study_date', 'start_time')
        
        return Response(SessionSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='my-today')
    def my_today(self, request):
        """
        Các buổi học hôm nay
        
        Query params:
        - teacher_id: UUID của giáo viên (cho giáo viên)
        - student_id: UUID của học sinh (cho học sinh)
        """
        teacher_id = request.query_params.get('teacher_id')
        student_id = request.query_params.get('student_id')
        
        if not teacher_id and not student_id:
            return Response({
                'success': False,
                'error': 'teacher_id hoặc student_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        today = date.today()
        
        if teacher_id:
            # Giáo viên
            qs = Session.objects.filter(teacher_id=teacher_id, study_date=today).select_related(
                'class_session', 'teacher', 'room', 'skill'
            ).order_by('start_time')
        else:
            # Học sinh
            class_ids = list(Enrollment.objects.filter(student_id=student_id).values_list('class_id', flat=True))
            qs = Session.objects.filter(
                class_session_id__in=class_ids,
                study_date=today
            ).select_related('class_session', 'teacher', 'room', 'skill').order_by('start_time')
        
        return Response({
            'success': True,
            'data': SessionSerializer(qs, many=True).data
        })

    @action(detail=False, methods=['get'], url_path='my-stats')
    def my_stats(self, request):
        """
        Thống kê buổi học
        
        Query params:
        - teacher_id: UUID của giáo viên (cho giáo viên)
        - student_id: UUID của học sinh (cho học sinh)
        - start_date: YYYY-MM-DD (optional)
        - end_date: YYYY-MM-DD (optional)
        """
        teacher_id = request.query_params.get('teacher_id')
        student_id = request.query_params.get('student_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not teacher_id and not student_id:
            return Response({
                'success': False,
                'error': 'teacher_id hoặc student_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if teacher_id:
            # Giáo viên
            qs = Session.objects.filter(teacher_id=teacher_id)
        else:
            # Học sinh
            class_ids = list(Enrollment.objects.filter(student_id=student_id).values_list('class_id', flat=True))
            qs = Session.objects.filter(class_session_id__in=class_ids)
        
        if start_date:
            qs = qs.filter(study_date__gte=start_date)
        if end_date:
            qs = qs.filter(study_date__lte=end_date)
        
        total = qs.count()
        
        if teacher_id:
            # Thống kê cho giáo viên (check-in/check-out)
            checked_in = qs.filter(check_in__isnull=False).count()
            checked_out = qs.filter(check_out__isnull=False).count()
            
            data = {
                'success': True,
                'data': {
                    'total_sessions': total,
                    'checked_in': checked_in,
                    'checked_out': checked_out,
                    'check_in_rate': round((checked_in / total * 100), 2) if total > 0 else 0,
                    'check_out_rate': round((checked_out / total * 100), 2) if total > 0 else 0,
                }
            }
        else:
            # Thống kê cho học sinh (attendance)
            from .models import Attendance
            session_ids = list(qs.values_list('id', flat=True))
            attendances = Attendance.objects.filter(session_id__in=session_ids, student_id=student_id)
            
            attendance_total = attendances.count()
            present = attendances.filter(status=Attendance.STATUS_PRESENT).count()
            absent = attendances.filter(status=Attendance.STATUS_ABSENT).count()
            late = attendances.filter(status=Attendance.STATUS_LATE).count()
            excused = attendances.filter(status=Attendance.STATUS_EXCUSED).count()
            
            data = {
                'success': True,
                'data': {
                    'total_sessions': total,
                    'attended_sessions': attendance_total,
                    'present': present,
                    'absent': absent,
                    'late': late,
                    'excused': excused,
                    'attendance_rate': round(((present + late) / attendance_total * 100), 2) if attendance_total > 0 else 0,
                }
            }
        
        return Response(data)
    
    @action(detail=False, methods=['get'], url_path='my-teaching-schedule')
    def my_teaching_schedule(self, request):
        """
        Lịch dạy đầy đủ của giáo viên (tương tự như my-schedule của học sinh)
        
        Query params:
        - teacher_id: UUID của giáo viên (required)
        - start_date: YYYY-MM-DD (optional)
        - end_date: YYYY-MM-DD (optional)
        
        Returns:
        - sessions_by_date: Group sessions theo ngày
        - summary: Thống kê tổng quan
        - upcoming_sessions: Các buổi học sắp tới
        """
        from collections import defaultdict
        
        teacher_id = request.query_params.get('teacher_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not teacher_id:
            return Response({
                'success': False,
                'error': 'teacher_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Lấy sessions của giáo viên
        qs = Session.objects.filter(teacher_id=teacher_id).select_related(
            'class_session', 'teacher', 'room', 'skill'
        )
        
        if start_date:
            qs = qs.filter(study_date__gte=start_date)
        if end_date:
            qs = qs.filter(study_date__lte=end_date)
        
        qs = qs.order_by('study_date', 'start_time')
        sessions = qs
        
        # Group sessions by date
        sessions_by_date = defaultdict(list)
        today = date.today()
        completed_count = 0
        upcoming_count = 0
        today_count = 0
        
        for session in sessions:
            session_data = SessionSerializer(session).data
            sessions_by_date[str(session.study_date)].append(session_data)
            
            # Tính toán thống kê
            if session.study_date < today:
                completed_count += 1
            elif session.study_date > today:
                upcoming_count += 1
            else:
                today_count += 1
        
        # Lấy các buổi học sắp tới (tối đa 5 buổi)
        upcoming_sessions = Session.objects.filter(
            teacher_id=teacher_id,
            study_date__gte=today
        ).select_related('class_session', 'teacher', 'room').order_by('study_date', 'start_time')[:5]
        
        # Lấy các buổi học hôm nay
        today_sessions = Session.objects.filter(
            teacher_id=teacher_id,
            study_date=today
        ).select_related('class_session', 'teacher', 'room').order_by('start_time')
        
        return Response({
            'success': True,
            'data': {
                'sessions_by_date': dict(sessions_by_date),
                'summary': {
                    'total_sessions': len(sessions),
                    'completed_sessions': completed_count,
                    'upcoming_sessions': upcoming_count,
                    'today_sessions': today_count
                },
                'upcoming_sessions': SessionSerializer(upcoming_sessions, many=True).data,
                'today_sessions': SessionSerializer(today_sessions, many=True).data
            }
        })
    
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

    # === CÁC ENDPOINT MỚI CHO ATTENDANCE ===
    
    @action(detail=True, methods=['get'], url_path='attendances')
    def get_attendances(self, request, pk=None):
        """Lấy danh sách điểm danh của buổi học"""
        session = self.get_object()
        attendances = Attendance.objects.filter(session_id=session.id)
        serializer = AttendanceSerializer(attendances, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='mark-attendance')
    def mark_attendance(self, request, pk=None):
        """
        Điểm danh cho học sinh trong buổi học
        Body: {
            "student_id": "uuid",
            "status": "present|absent|late|excused"
        }
        """
        session = self.get_object()
        student_id = request.data.get('student_id')
        attendance_status = request.data.get('status', 'absent')
        
        if not student_id:
            return Response(
                {'detail': 'student_id là bắt buộc'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Kiểm tra status hợp lệ
        valid_statuses = [choice[0] for choice in Attendance.STATUS_CHOICES]
        if attendance_status not in valid_statuses:
            return Response(
                {'detail': f'Status không hợp lệ. Chọn một trong: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Kiểm tra học sinh có trong lớp không
        if not Enrollment.objects.filter(
            student_id=student_id,
            class_id=session.class_session_id
        ).exists():
            return Response(
                {'detail': 'Học sinh không thuộc lớp này'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Kiểm tra đã điểm danh chưa
        existing = Attendance.objects.filter(
            student_id=student_id,
            session_id=session.id
        ).first()
        
        if existing:
            # Cập nhật
            existing.status = attendance_status
            existing.save()
            serializer = AttendanceSerializer(existing)
            return Response({
                'detail': 'Cập nhật điểm danh thành công',
                'attendance': serializer.data
            })
        else:
            # Tạo mới
            attendance = Attendance.objects.create(
                student_id=student_id,
                session_id=session.id,
                status=attendance_status
            )
            serializer = AttendanceSerializer(attendance)
            return Response({
                'detail': 'Điểm danh thành công',
                'attendance': serializer.data
            }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='mark-all-attendance')
    def mark_all_attendance(self, request, pk=None):
        """
        Điểm danh hàng loạt cho buổi học
        Body: {
            "attendances": [
                {"student_id": "uuid", "status": "present"},
                {"student_id": "uuid", "status": "absent"}
            ]
        }
        """
        session = self.get_object()
        attendances_data = request.data.get('attendances', [])
        
        if not attendances_data:
            return Response(
                {'detail': 'Danh sách điểm danh trống'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Lấy danh sách student_id trong lớp
        enrolled_students = set(
            str(sid) for sid in Enrollment.objects.filter(
                class_id=session.class_session_id
            ).values_list('student_id', flat=True)
        )
        
        created_count = 0
        updated_count = 0
        errors = []
        
        for item in attendances_data:
            student_id = item.get('student_id')
            attendance_status = item.get('status', 'absent')
            
            # Validate
            if not student_id:
                errors.append("Thiếu student_id")
                continue
            
            if str(student_id) not in enrolled_students:
                errors.append(f"Student {student_id}: Không thuộc lớp")
                continue
            
            valid_statuses = [choice[0] for choice in Attendance.STATUS_CHOICES]
            if attendance_status not in valid_statuses:
                errors.append(f"Student {student_id}: Status không hợp lệ")
                continue
            
            # Tạo hoặc cập nhật
            existing = Attendance.objects.filter(
                student_id=student_id,
                session_id=session.id
            ).first()
            
            if existing:
                existing.status = attendance_status
                existing.save()
                updated_count += 1
            else:
                Attendance.objects.create(
                    student_id=student_id,
                    session_id=session.id,
                    status=attendance_status
                )
                created_count += 1
        
        return Response({
            'detail': 'Điểm danh hàng loạt hoàn tất',
            'created': created_count,
            'updated': updated_count,
            'errors': errors
        })
    
    @action(detail=False, methods=['get'], url_path='student-attendance-history')
    def student_attendance_history(self, request):
        """
        Lịch sử điểm danh của học sinh
        Query params: student_id, start_date, end_date
        """
        student_id = request.query_params.get('student_id')
        
        if not student_id:
            return Response(
                {'detail': 'student_id là bắt buộc'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Lọc attendance
        attendances = Attendance.objects.filter(student_id=student_id)
        
        # Lấy thông tin session để filter theo date
        session_ids = list(attendances.values_list('session_id', flat=True))
        sessions_qs = Session.objects.filter(id__in=session_ids)
        
        start_date = request.query_params.get('start_date')
        if start_date:
            sessions_qs = sessions_qs.filter(study_date__gte=start_date)
        
        end_date = request.query_params.get('end_date')
        if end_date:
            sessions_qs = sessions_qs.filter(study_date__lte=end_date)
        
        filtered_session_ids = list(sessions_qs.values_list('id', flat=True))
        attendances = attendances.filter(session_id__in=filtered_session_ids)
        
        # Thống kê
        total = attendances.count()
        stats = {
            'total': total,
            'present': attendances.filter(status=Attendance.STATUS_PRESENT).count(),
            'absent': attendances.filter(status=Attendance.STATUS_ABSENT).count(),
            'late': attendances.filter(status=Attendance.STATUS_LATE).count(),
            'excused': attendances.filter(status=Attendance.STATUS_EXCUSED).count(),
        }
        
        if total > 0:
            stats['attendance_rate'] = round((stats['present'] + stats['late']) / total * 100, 2)
        else:
            stats['attendance_rate'] = 0
        
        serializer = AttendanceSerializer(attendances, many=True)
        
        return Response({
            'statistics': stats,
            'attendances': serializer.data
        })
    
    @action(detail=True, methods=['get'], url_path='attendance-summary')
    def attendance_summary(self, request, pk=None):
        """Tóm tắt điểm danh của buổi học"""
        session = self.get_object()
        
        # Lấy tất cả học sinh trong lớp
        enrolled_students = Enrollment.objects.filter(
            class_id=session.class_session_id
        ).count()
        
        # Thống kê attendance
        attendances = Attendance.objects.filter(session_id=session.id)
        marked_count = attendances.count()
        
        summary = {
            'session_id': str(session.id),
            'study_date': session.study_date,
            'total_students': enrolled_students,
            'marked': marked_count,
            'unmarked': enrolled_students - marked_count,
            'present': attendances.filter(status=Attendance.STATUS_PRESENT).count(),
            'absent': attendances.filter(status=Attendance.STATUS_ABSENT).count(),
            'late': attendances.filter(status=Attendance.STATUS_LATE).count(),
            'excused': attendances.filter(status=Attendance.STATUS_EXCUSED).count(),
        }
        
        if marked_count > 0:
            summary['attendance_rate'] = round(
                (summary['present'] + summary['late']) / marked_count * 100, 2
            )
        else:
            summary['attendance_rate'] = 0
        
        return Response(summary)


class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet riêng cho Attendance"""
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by session
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        # Filter by student
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        # Filter by status
        attendance_status = self.request.query_params.get('status')
        if attendance_status:
            queryset = queryset.filter(status=attendance_status)
        
        return queryset
