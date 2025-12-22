from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count
from django.db import connection
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import unicodedata
from authentication.permissions import PermissionMixin
from .models import Enrollment
from classes.models import Class
from class_sessions.models import Session

logger = logging.getLogger(__name__)


class EnrollmentSerializer(serializers.ModelSerializer):
    student_info = serializers.SerializerMethodField()
    payment_status = serializers.CharField(source='invoice_status', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = '__all__'
    
    def get_student_info(self, obj):
        """Get student information including user account"""
        try:
            from users.models import Student
            student = Student.objects.select_related('user_account').get(id=obj.student_id)
            user = student.user_account
            return {
                'id': str(student.id),
                'user_account': {
                    'id': str(user.id),
                    'username': user.username,
                    'fullname': user.fullname,
                    'email': user.email,
                }
            }
        except Exception as e:
            logger.warning(f"Could not fetch student info for enrollment {obj.id}: {str(e)}")
            return None
    
    def to_representation(self, instance):
        """Override to handle encoding issues"""
        try:
            data = super().to_representation(instance)
            # Handle potential encoding issues in notes field
            if data.get('notes'):
                try:
                    # Handle encoding issues by normalizing unicode
                    notes = data['notes']
                    # Normalize unicode characters
                    notes = unicodedata.normalize('NFKD', notes)
                    # Replace common encoding issues
                    replacements = {
                        'ÃÃ£': 'Đã', 'Ã¡': 'á', 'Ã³': 'ó', 'Ã­': 'í',
                        'Ã©': 'é', 'Ã¹': 'ù', 'Ã¨': 'è', 'Ã¢': 'â',
                        'Ã´': 'ô', 'Ãª': 'ê', 'Ã®': 'î', 'Ã»': 'û',
                        'Ã§': 'ç', 'Ã ': 'à', 'Ã¹': 'ù', 'Ã¨': 'è',
                        'Ã¢': 'â', 'Ã´': 'ô', 'Ãª': 'ê', 'Ã®': 'î',
                        'Ã»': 'û', 'Ã§': 'ç', 'Ã': 'à', 'Ã': 'á',
                        'Ã': 'â', 'Ã': 'ã', 'Ã': 'ä', 'Ã': 'å',
                        'Ã': 'æ', 'Ã': 'ç', 'Ã': 'è', 'Ã': 'é',
                        'Ã': 'ê', 'Ã': 'ë', 'Ã': 'ì', 'Ã': 'í',
                        'Ã': 'î', 'Ã': 'ï', 'Ã': 'ð', 'Ã': 'ñ',
                        'Ã': 'ò', 'Ã': 'ó', 'Ã': 'ô', 'Ã': 'õ',
                        'Ã': 'ö', 'Ã': '÷', 'Ã': 'ø', 'Ã': 'ù',
                        'Ã': 'ú', 'Ã': 'û', 'Ã': 'ü', 'Ã': 'ý',
                        'Ã': 'þ', 'Ã': 'ÿ', '?': 'n', '?': 'o'
                    }
                    for old, new in replacements.items():
                        notes = notes.replace(old, new)
                    data['notes'] = notes
                except Exception as e:
                    logger.warning(f"Encoding issue in notes for enrollment {instance.id}: {str(e)}")
                    data['notes'] = str(data['notes']).encode('utf-8', errors='ignore').decode('utf-8')
            return data
        except Exception as e:
            logger.error(f"Serialization error for enrollment {instance.id}: {str(e)}")
            # Return basic data if serialization fails
            return {
                'id': str(instance.id),
                'student_id': str(instance.student_id),
                'class_id': str(instance.class_id),
                'amount': float(instance.amount),
                'invoice_status': instance.invoice_status,
                'due_date': instance.due_date,
                'created_at': instance.created_at,
                'updated_at': instance.updated_at,
                'notes': str(instance.notes).encode('utf-8', errors='ignore').decode('utf-8') if instance.notes else None,
            }


class EnrollmentViewSet(PermissionMixin, viewsets.ModelViewSet):
    queryset = Enrollment.objects.all().order_by('-created_at')
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_enrollments',
        'POST': 'manage_enrollments',
        'PUT': 'manage_enrollments',
        'PATCH': 'manage_enrollments',
        'DELETE': 'manage_enrollments',
    }

    def check_permissions(self, request):
        """
        Override check_permissions để cho phép giáo viên xem enrollments của lớp học mà họ đang dạy
        """
        method = request.method
        
        # Cho phép giáo viên xem enrollments của lớp học mà họ đang dạy
        if method == 'GET':
            from authentication.permissions import is_teacher
            if is_teacher(request.user):
                # Kiểm tra xem có class_id trong query params không
                class_id = request.query_params.get('class_id')
                if class_id:
                    # Kiểm tra giáo viên có đang dạy lớp này không
                    try:
                        cls = Class.objects.get(id=class_id)
                        if cls.teacher and cls.teacher.user_account == request.user:
                            # Giáo viên đang dạy lớp này → cho phép xem enrollments
                            return  # Bỏ qua permission check
                    except Class.DoesNotExist:
                        pass
        
        # Gọi check permissions mặc định
        super().check_permissions(request)

    def get_queryset(self):
        """Filter enrollments by class_id or student_id if provided"""
        queryset = super().get_queryset()
        
        # Filter by class_id
        class_id = self.request.query_params.get('class_id')
        if class_id:
            queryset = queryset.filter(class_id=class_id)
        
        # Filter by student_id
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset

    def list(self, request, *args, **kwargs):
        """Override list method to add error handling"""
        try:
            logger.info("Fetching enrollments list")
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            logger.info(f"Successfully fetched {len(serializer.data)} enrollments")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching enrollments: {str(e)}")
            return Response(
                {'detail': f'Error fetching enrollments: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        """
        POST /api/enrollment/enrollments/
        
        Request Body:
        {
            "class_id": "uuid",
            "payment_method": "cash"  // hoặc "vnpay"
        }
        
        Logic:
        1. Validate class (status, capacity, teacher)
        2. Check time conflict với các enrollment khác
        3. Lấy amount từ course.fee
        4. Xử lý payment_method (cash hoặc vnpay)
        5. Tạo enrollment
        6. Trả về confirmation message và PDF URL
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.shortcuts import get_object_or_404
        
        try:
            # Lấy student từ request.user
            if not hasattr(request.user, 'student_profile'):
                return Response({
                    'success': False,
                    'error': 'Chỉ học viên mới có thể đăng ký lớp học'
                }, status=status.HTTP_403_FORBIDDEN)
            
            student = request.user.student_profile
            student_id = student.id
            
            # Lấy class_id và payment_method từ request
            class_id = request.data.get('class_id')
            payment_method = request.data.get('payment_method', 'cash')
            
            if not class_id:
                return Response({
                    'success': False,
                    'error': 'class_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if payment_method not in ['cash', 'vnpay']:
                return Response({
                    'success': False,
                    'error': 'payment_method must be "cash" or "vnpay"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Lấy class object
            try:
                cls = Class.objects.select_related('course', 'teacher', 'campus').get(id=class_id)
            except Class.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Class not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # VALIDATION 1: Class status phải là 'planned'
            if cls.status != Class.Status.PLANNED:
                return Response({
                    'success': False,
                    'error': f'Không thể đăng ký lớp có trạng thái: {cls.status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # VALIDATION 2: Class phải có giáo viên
            if not cls.teacher_id:
                return Response({
                    'success': False,
                    'error': 'Lớp học chưa có giáo viên'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # VALIDATION 3: Class phải còn slot
            if cls.limit_slot is not None and cls.current_student_count >= cls.limit_slot:
                return Response({
                    'success': False,
                    'error': 'Lớp đã đầy'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # VALIDATION 4: Kiểm tra duplicate enrollment
            existing_enrollment = Enrollment.objects.filter(
                student_id=student_id,
                class_id=class_id
            ).first()
            
            if existing_enrollment:
                return Response({
                    'success': False,
                    'error': 'Bạn đã đăng ký lớp này rồi'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # VALIDATION 5: Kiểm tra trùng lịch học
            existing_enrollments = Enrollment.objects.filter(
                student_id=student_id
            ).exclude(
                invoice_status='canceled'
            )
            
            # Lấy các lớp học từ enrollments
            existing_class_ids = [e.class_id for e in existing_enrollments]
            existing_classes = Class.objects.filter(id__in=existing_class_ids)
            
            # Kiểm tra trùng thời gian
            if cls.start_date and cls.end_date:
                for existing_class in existing_classes:
                    if existing_class.start_date and existing_class.end_date:
                        # Trùng nếu: (new_start <= existing_end) AND (new_end >= existing_start)
                        if (cls.start_date <= existing_class.end_date and 
                            cls.end_date >= existing_class.start_date):
                            return Response({
                                'success': False,
                                'error': (
                                    f'Bạn đã đăng ký lớp "{existing_class.name}" '
                                    f'({existing_class.start_date} - {existing_class.end_date}). '
                                    f'Không thể đăng ký lớp "{cls.name}" '
                                    f'({cls.start_date} - {cls.end_date}) vì trùng lịch học.'
                                )
                            }, status=status.HTTP_400_BAD_REQUEST)
            
            # Lấy amount từ course.fee
            amount = cls.course.fee if cls.course else 0
            
            # Tính due_date (2 ngày từ hôm nay)
            today = timezone.now().date()
            due_date = today + timedelta(days=2)
            
            # Tạo enrollment trước
            enrollment = Enrollment.objects.create(
                student_id=student_id,
                class_id=class_id,
                amount=amount,
                invoice_status='pending',
                due_date=due_date
            )
            
            # Xử lý payment_method sau khi đã có enrollment.id
            payment_url = None
            if payment_method == 'vnpay':
                # Tạo payment URL từ VNPay
                try:
                    from .payment_gateway import create_vnpay_payment_url
                    payment_url = create_vnpay_payment_url(enrollment.id, amount, request)
                    logger.info(f"Created VNPay payment URL for enrollment {enrollment.id}")
                except Exception as e:
                    logger.error(f"Error creating VNPay payment URL: {str(e)}", exc_info=True)
                    return Response({
                        'success': False,
                        'error': f'Lỗi khi tạo payment URL: {str(e)}'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Increment class counter
            cls.current_student_count = (cls.current_student_count or 0) + 1
            cls.save(update_fields=['current_student_count'])
            
            # Format confirmation message
            enrollment_date = timezone.now()
            student_name = student.user_account.fullname if hasattr(student, 'user_account') else 'Học viên'
            class_name = cls.name
            formatted_date = enrollment_date.strftime('%d/%m/%Y %H:%M:%S')
            
            confirmation_message = (
                f'Học viên {student_name} đã đăng ký thành công lớp {class_name} '
                f'vào thời điểm {formatted_date}'
            )
            
            # Tạo response
            response_data = {
                'success': True,
                'data': {
                    'id': str(enrollment.id),
                    'invoice_status': enrollment.invoice_status,
                    'amount': float(amount),
                    'due_date': due_date.isoformat() if due_date else None,
                    'payment_url': payment_url,
                    'confirmation': {
                        'message': confirmation_message,
                        'student_name': student_name,
                        'class_name': class_name,
                        'enrollment_date': enrollment_date.isoformat(),
                        'pdf_download_url': f'/api/enrollment/enrollments/{enrollment.id}/confirmation-pdf/'
                    }
                }
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error creating enrollment: {str(e)}")
            logger.error(f"Traceback: {error_traceback}")
            return Response({
                'success': False,
                'error': f'Đăng ký thất bại: {str(e)}',
                'detail': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='payment-info')
    def payment_info(self, request, pk=None):
        enrollment = self.get_object()
        return Response({
            'enrollment_id': enrollment.id,
            'amount': enrollment.amount,
            'invoice_status': enrollment.invoice_status,
            'due_date': enrollment.due_date,
            'notes': enrollment.notes
        })

    @action(detail=True, methods=['patch'], url_path='update-payment')
    def update_payment(self, request, pk=None):
        """Update payment status"""
        enrollment = self.get_object()
        new_status = request.data.get('invoice_status')
        if new_status in ['pending', 'paid', 'overdue', 'canceled']:
            enrollment.invoice_status = new_status
            enrollment.save(update_fields=['invoice_status', 'updated_at'])
            return Response({'detail': 'Payment status updated'})
        return Response({'detail': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='my-classes')
    def my_classes(self, request):
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({'detail': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        enrollments = Enrollment.objects.filter(student_id=student_id).order_by('-created_at')
        class_ids = [e.class_id for e in enrollments]
        classes = Class.objects.filter(id__in=class_ids)
        # merge with sessions for timetable
        sessions = Session.objects.filter(class_id__in=class_ids).order_by('study_date', 'start_time')
        # Assemble a minimal timetable response
        classes_map = {str(c.id): {'id': c.id, 'name': c.name, 'start_date': c.start_date, 'end_date': c.end_date} for c in classes}
        timetable = {}
        for s in sessions:
            key = str(s.class_id)
            timetable.setdefault(key, []).append({
                'study_date': s.study_date,
                'start_time': s.start_time,
                'end_time': s.end_time,
                'session_id': s.id,
            })
        result = []
        for class_id in classes_map:
            result.append({
                **classes_map[class_id],
                'sessions': timetable.get(class_id, []),
            })
        return Response(result)

    @action(detail=False, methods=['get'], url_path='payment-stats')
    def payment_stats(self, request):
        """Get payment statistics"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        qs = Enrollment.objects.all()
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)
        
        total_amount = qs.aggregate(total=Sum('amount'))['total'] or 0
        total_count = qs.count()
        
        # Status breakdown
        status_breakdown = qs.values('invoice_status').annotate(
            amount=Sum('amount'),
            count=Count('id')
        )
        
        return Response({
            'total_amount': total_amount,
            'total_count': total_count,
            'status_breakdown': list(status_breakdown)
        })

    @action(detail=True, methods=['get'], url_path='schedule')
    def schedule(self, request, pk=None):
        """
        GET /api/enrollment/enrollments/{id}/schedule/
        
        Lấy lịch học của enrollment, tính toán từ sessions hoặc từ class info
        """
        from django.utils import timezone
        from datetime import timedelta
        from collections import defaultdict
        
        enrollment = self.get_object()
        
        # Verify student có quyền xem (chỉ student đã đăng ký mới xem được)
        if hasattr(request.user, 'student_profile'):
            if enrollment.student_id != request.user.student_profile.id:
                return Response({
                    'success': False,
                    'error': 'Bạn không có quyền xem lịch học này'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Lấy class object
        try:
            cls = Class.objects.select_related('course', 'teacher', 'campus').get(id=enrollment.class_id)
        except Class.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Class not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Kiểm tra sessions trong DB
        sessions = Session.objects.filter(class_id=enrollment.class_id).order_by('study_date', 'start_time')
        
        # Nếu không có sessions trong DB → tính toán từ class info
        if not sessions.exists():
            sessions_list = []
            if cls.start_date and cls.end_date and cls.weekday and cls.time_slot:
                current_date = cls.start_date
                
                # Parse time_slot (ví dụ: "18:00-20:00")
                time_parts = cls.time_slot.split('-')
                start_time_str = time_parts[0].strip() if len(time_parts) > 0 else None
                end_time_str = time_parts[1].strip() if len(time_parts) > 1 else None
                
                while current_date <= cls.end_date:
                    # weekday: 1=Mon, 2=Tue, ..., 7=Sun
                    # Python weekday(): 0=Mon, 1=Tue, ..., 6=Sun
                    python_weekday = current_date.weekday() + 1
                    
                    if python_weekday in cls.weekday:
                        sessions_list.append({
                            'id': None,  # Không có trong DB
                            'study_date': current_date,
                            'start_time': start_time_str,
                            'end_time': end_time_str,
                            'skill': None,
                            'room': None,
                            'teacher': {
                                'id': str(cls.teacher.id) if cls.teacher else None,
                                'name': cls.teacher.user_account.fullname if cls.teacher and cls.teacher.user_account else None
                            } if cls.teacher else None
                        })
                    
                    current_date += timedelta(days=1)
        else:
            # Có sessions trong DB → format từ DB
            sessions_list = []
            for session in sessions:
                sessions_list.append({
                    'id': str(session.id),
                    'study_date': session.study_date,
                    'start_time': session.start_time.strftime('%H:%M') if session.start_time else None,
                    'end_time': session.end_time.strftime('%H:%M') if session.end_time else None,
                    'skill': session.skill if hasattr(session, 'skill') else None,
                    'room': session.room if hasattr(session, 'room') else None,
                    'teacher': {
                        'id': str(cls.teacher.id) if cls.teacher else None,
                        'name': cls.teacher.user_account.fullname if cls.teacher and cls.teacher.user_account else None
                    } if cls.teacher else None
                })
        
        # Group sessions by week
        today = timezone.now().date()
        by_week = []
        week_sessions = defaultdict(list)
        
        for session in sessions_list:
            study_date = session['study_date']
            if isinstance(study_date, str):
                from datetime import datetime
                study_date = datetime.strptime(study_date, '%Y-%m-%d').date()
            
            # Tính tuần (week number từ start_date)
            if cls.start_date:
                week_num = ((study_date - cls.start_date).days // 7) + 1
                week_sessions[week_num].append(session)
        
        # Format by_week
        for week_num in sorted(week_sessions.keys()):
            week_sessions_list = sorted(week_sessions[week_num], key=lambda x: x['study_date'])
            if week_sessions_list:
                first_date = week_sessions_list[0]['study_date']
                last_date = week_sessions_list[-1]['study_date']
                if isinstance(first_date, str):
                    from datetime import datetime
                    first_date = datetime.strptime(first_date, '%Y-%m-%d').date()
                    last_date = datetime.strptime(last_date, '%Y-%m-%d').date()
                
                by_week.append({
                    'week': week_num,
                    'start_date': first_date.isoformat(),
                    'end_date': last_date.isoformat(),
                    'sessions': week_sessions_list
                })
        
        # Tính summary
        total_sessions = len(sessions_list)
        completed_sessions = sum(1 for s in sessions_list if (
            isinstance(s['study_date'], str) and 
            datetime.strptime(s['study_date'], '%Y-%m-%d').date() < today
        ) or (isinstance(s['study_date'], type(today)) and s['study_date'] < today))
        upcoming_sessions = total_sessions - completed_sessions
        
        # Tìm next session
        next_session = None
        for session in sorted(sessions_list, key=lambda x: x['study_date']):
            study_date = session['study_date']
            if isinstance(study_date, str):
                from datetime import datetime
                study_date = datetime.strptime(study_date, '%Y-%m-%d').date()
            
            if study_date >= today:
                next_session = session
                break
        
        return Response({
            'success': True,
            'data': {
                'enrollment_id': str(enrollment.id),
                'class': {
                    'id': str(cls.id),
                    'name': cls.name,
                    'course': {
                        'id': str(cls.course.id) if cls.course else None,
                        'name': cls.course.name if cls.course else None,
                        'level': cls.course.level if cls.course else None
                    } if cls.course else None,
                    'teacher': {
                        'id': str(cls.teacher.id) if cls.teacher else None,
                        'name': cls.teacher.user_account.fullname if cls.teacher and cls.teacher.user_account else None
                    } if cls.teacher else None,
                    'campus': {
                        'id': str(cls.campus.id) if cls.campus else None,
                        'name': cls.campus.name if cls.campus else None
                    } if cls.campus else None,
                    'start_date': cls.start_date.isoformat() if cls.start_date else None,
                    'end_date': cls.end_date.isoformat() if cls.end_date else None,
                    'weekday': cls.weekday or [],
                    'time_slot': cls.time_slot
                },
                'schedule': {
                    'by_week': by_week
                },
                'summary': {
                    'total_sessions': total_sessions,
                    'completed_sessions': completed_sessions,
                    'upcoming_sessions': upcoming_sessions,
                    'next_session': next_session
                }
            }
        })
    
    @action(detail=True, methods=['get'], url_path='confirmation-pdf')
    def confirmation_pdf(self, request, pk=None):
        """
        GET /api/enrollment/enrollments/{id}/confirmation-pdf/
        
        Download PDF xác nhận đăng ký lớp học
        """
        from django.http import HttpResponse
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from io import BytesIO
        
        enrollment = self.get_object()
        
        # Verify student có quyền xem
        if hasattr(request.user, 'student_profile'):
            if enrollment.student_id != request.user.student_profile.id:
                return Response({
                    'success': False,
                    'error': 'Bạn không có quyền xem PDF này'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Lấy thông tin enrollment
        try:
            from users.models import Student
            student = Student.objects.select_related('user_account').get(id=enrollment.student_id)
            cls = Class.objects.select_related('course', 'teacher', 'campus').get(id=enrollment.class_id)
        except (Student.DoesNotExist, Class.DoesNotExist) as e:
            return Response({
                'success': False,
                'error': 'Không tìm thấy thông tin đăng ký'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Tạo PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Tiêu đề
        story.append(Paragraph('XÁC NHẬN ĐĂNG KÝ LỚP HỌC', title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Thông tin học viên
        student_name = student.user_account.fullname if student.user_account else 'N/A'
        student_email = student.user_account.email if student.user_account else 'N/A'
        student_phone = getattr(student.user_account, 'phone', 'N/A') if student.user_account else 'N/A'
        
        student_data = [
            ['Học viên:', student_name],
            ['Email:', student_email],
            ['Số điện thoại:', student_phone]
        ]
        
        student_table = Table(student_data, colWidths=[2*inch, 4*inch])
        student_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(student_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Thông tin lớp học
        class_name = cls.name
        course_name = cls.course.name if cls.course else 'N/A'
        teacher_name = cls.teacher.user_account.fullname if cls.teacher and cls.teacher.user_account else 'N/A'
        campus_name = cls.campus.name if cls.campus else 'N/A'
        
        class_data = [
            ['Tên lớp:', class_name],
            ['Khóa học:', course_name],
            ['Giáo viên:', teacher_name],
            ['Cơ sở:', campus_name]
        ]
        
        class_table = Table(class_data, colWidths=[2*inch, 4*inch])
        class_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(class_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Thông tin đăng ký
        enrollment_date = enrollment.created_at.strftime('%d/%m/%Y %H:%M:%S') if enrollment.created_at else 'N/A'
        amount = f"{float(enrollment.amount):,.0f} VNĐ" if enrollment.amount else 'N/A'
        payment_method = 'Tiền mặt' if not hasattr(enrollment, 'payment_method') or enrollment.payment_method == 'cash' else 'VNPay'
        invoice_status_map = {
            'pending': 'Chờ thanh toán',
            'paid': 'Đã thanh toán',
            'overdue': 'Quá hạn',
            'canceled': 'Đã hủy'
        }
        status_display = invoice_status_map.get(enrollment.invoice_status, enrollment.invoice_status)
        due_date = enrollment.due_date.strftime('%d/%m/%Y') if enrollment.due_date else 'N/A'
        
        enrollment_data = [
            ['Ngày đăng ký:', enrollment_date],
            ['Số tiền:', amount],
            ['Phương thức thanh toán:', payment_method],
            ['Trạng thái:', status_display],
            ['Hạn thanh toán:', due_date]
        ]
        
        enrollment_table = Table(enrollment_data, colWidths=[2*inch, 4*inch])
        enrollment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(enrollment_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Thông tin lớp học (thời gian)
        start_date = cls.start_date.strftime('%d/%m/%Y') if cls.start_date else 'N/A'
        end_date = cls.end_date.strftime('%d/%m/%Y') if cls.end_date else 'N/A'
        weekday_display = ', '.join([f'Thứ {d}' for d in cls.weekday]) if cls.weekday else 'N/A'
        time_slot = cls.time_slot or 'N/A'
        
        schedule_data = [
            ['Ngày bắt đầu:', start_date],
            ['Ngày kết thúc:', end_date],
            ['Lịch học:', f'{weekday_display} ({time_slot})']
        ]
        
        schedule_table = Table(schedule_data, colWidths=[2*inch, 4*inch])
        schedule_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(schedule_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        footer_text = f"Ngày in: {timezone.now().strftime('%d/%m/%Y')} | Mã đăng ký: {enrollment.id}"
        story.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        buffer.seek(0)
        pdf_content = buffer.read()
        buffer.close()
        
        # Create HTTP response
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="xac-nhan-dang-ky-{enrollment.id}.pdf"'
        
        return response
    
    @action(detail=False, methods=['get'], url_path='debug')
    def debug_info(self, request):
        """Debug endpoint to check database connection and data"""
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM enrollments")
                db_count = cursor.fetchone()[0]
            
            # Test Django ORM
            orm_count = Enrollment.objects.count()
            first_enrollment = Enrollment.objects.first()
            
            return Response({
                'database_count': db_count,
                'orm_count': orm_count,
                'first_enrollment': {
                    'id': str(first_enrollment.id) if first_enrollment else None,
                    'student_id': str(first_enrollment.student_id) if first_enrollment else None,
                    'class_id': str(first_enrollment.class_id) if first_enrollment else None,
                    'amount': float(first_enrollment.amount) if first_enrollment else None,
                } if first_enrollment else None,
                'connection_info': {
                    'database': connection.settings_dict['NAME'],
                    'host': connection.settings_dict['HOST'],
                }
            })
        except Exception as e:
            logger.error(f"Debug error: {str(e)}")
            return Response(
                {'error': str(e), 'type': type(e).__name__}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
