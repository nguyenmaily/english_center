from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.db import connection
import logging
import unicodedata
from .models import Enrollment
from classes.models import Class
from class_sessions.models import Session

logger = logging.getLogger(__name__)


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = '__all__'
    
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


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all().order_by('-created_at')
    serializer_class = EnrollmentSerializer

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
        # Inputs: student_id, class_id, amount (optional), due_date (optional)
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Handle encoding issues in notes field before saving
            validated_data = serializer.validated_data.copy()
            if 'notes' in validated_data and validated_data['notes']:
                notes = validated_data['notes']
                # Replace Vietnamese characters that cause encoding issues
                replacements = {
                    'đ': 'd', 'Đ': 'D', 'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
                    'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
                    'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
                    'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
                    'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
                    'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
                    'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
                    'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
                    'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
                    'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
                    'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
                    'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y'
                }
                for old, new in replacements.items():
                    notes = notes.replace(old, new)
                validated_data['notes'] = notes
            
            student_id = validated_data.get('student_id')
            class_id = validated_data.get('class_id')
            
            # Check class capacity
            try:
                cls = Class.objects.get(id=class_id)
            except Class.DoesNotExist:
                return Response({'detail': 'Class not found'}, status=status.HTTP_400_BAD_REQUEST)
            
            if cls.limit_slot is not None and cls.current_student_count >= cls.limit_slot:
                return Response({'detail': 'Lop da day'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create enrollment with cleaned data
            enrollment = Enrollment.objects.create(**validated_data)
            
            # Increment class counter
            cls.current_student_count = (cls.current_student_count or 0) + 1
            cls.save(update_fields=['current_student_count'])
            
            # Return created enrollment data
            response_serializer = self.get_serializer(enrollment)
            headers = self.get_success_headers(response_serializer.data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            logger.error(f"Error creating enrollment: {str(e)}")
            return Response(
                {'detail': f'Error creating enrollment: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
