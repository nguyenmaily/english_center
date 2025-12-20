from datetime import timedelta
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Class
from class_sessions.models import Session
from class_sessions.serializers import SessionSerializer


class ClassSerializer(serializers.ModelSerializer):
    """Serializer for Class with related data"""
    course_name = serializers.CharField(source='course.name', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    campus_name = serializers.CharField(source='campus.name', read_only=True)
    enrollment_rate = serializers.ReadOnlyField()
    available_slots = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    enrollment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = [
            'id', 'name', 'start_date', 'end_date', 'current_student_count',
            'status', 'course', 'weekday', 'time_slot', 'teacher', 'campus',
            'manager', 'limit_slot', 'is_public', 'created_at', 'updated_at',
            # Read-only fields
            'course_name', 'teacher_name', 'campus_name', 'enrollment_rate',
            'available_slots', 'is_full', 'enrollment_count'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'current_student_count',
            'course_name', 'teacher_name', 'campus_name', 'enrollment_rate',
            'available_slots', 'is_full', 'enrollment_count'
        ]
    
    def validate_weekday(self, value):
        """Validate weekday array"""
        if value is not None:
            if not isinstance(value, list):
                raise serializers.ValidationError("weekday must be a list")
            # Ensure all values are integers between 1 and 7
            for day in value:
                if not isinstance(day, int) or day < 1 or day > 7:
                    raise serializers.ValidationError("weekday values must be integers between 1 and 7")
        return value
    
    def validate_teacher(self, value):
        """Validate teacher - allow null/empty"""
        if value == '' or value is None:
            return None
        return value
    
    def validate_campus(self, value):
        """Validate campus - allow null/empty"""
        if value == '' or value is None:
            return None
        return value
    
    def validate_manager(self, value):
        """Validate manager - allow null/empty"""
        if value == '' or value is None:
            return None
        return value
    
    def validate_status(self, value):
        """Validate status - ensure it matches enum values"""
        if value:
            # Convert to string, strip whitespace, and lowercase
            if isinstance(value, str):
                value_clean = value.strip().lower()
            else:
                value_clean = str(value).strip().lower()
            
            # Valid status values from model
            valid_statuses = ['planned', 'ongoing', 'completed', 'cancelled']
            
            if value_clean not in valid_statuses:
                raise serializers.ValidationError(
                    f"Invalid status '{value}'. Must be one of: {', '.join(valid_statuses)}"
                )
            # Return cleaned lowercase value to match database enum
            return value_clean
        return value
    
    def validate(self, attrs):
        """Validate all fields together"""
        # Convert empty strings to None for optional fields
        for field in ['teacher', 'campus', 'manager']:
            if field in attrs and (attrs[field] == '' or attrs[field] is None):
                attrs[field] = None
        
        # Ensure status is lowercase and stripped if provided
        if 'status' in attrs and attrs['status']:
            if isinstance(attrs['status'], str):
                attrs['status'] = attrs['status'].strip().lower()
            else:
                attrs['status'] = str(attrs['status']).strip().lower()
        
        return attrs
    
    def get_teacher_name(self, obj):
        """Get teacher's full name"""
        if obj.teacher and obj.teacher.user_account:
            user = obj.teacher.user_account
            return user.fullname if user.fullname else user.username
        return None
    
    def get_enrollment_count(self, obj):
        """Get total number of enrolled students"""
        try:
            from enrollment.models import Enrollment
            if obj and obj.id:
                return Enrollment.objects.filter(class_id=obj.id).count()
            return 0
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error calculating enrollment_count: {str(e)}")
            return 0
>>>>>>> origin/backend_nhung


class ClassViewSet(viewsets.ModelViewSet):
    serializer_class = ClassSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course', 'teacher', 'campus', 'manager', 'status', 'is_public']
    search_fields = ['name', 'course__name']
    ordering_fields = ['name', 'start_date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Class.objects.select_related(
            'course', 'teacher', 'teacher__user_account', 'campus', 'manager', 'manager__user_account'
        ).all()
        
        # ============================================================================
        # FILTER THEO ROLE - QUAN TRỌNG!
        # ============================================================================
        # Manager chỉ thấy classes của campus mà họ quản lý
        # Admin thấy tất cả classes
        # ============================================================================
        user = self.request.user
        if hasattr(user, 'roleid') and user.roleid:
            role_name = user.roleid.name
            
            if role_name == 'manager':
                # Manager chỉ thấy classes của campus mình quản lý
                from users.models import Manager
                try:
                    manager = Manager.objects.select_related('campus').get(user_account=user)
                    if manager.campus:
                        queryset = queryset.filter(campus=manager.campus)
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Manager {user.username} filtering classes by campus: {manager.campus.name}")
                    else:
                        # Manager chưa có campus → không thấy class nào
                        queryset = queryset.none()
                except Manager.DoesNotExist:
                    # User không phải manager → không filter
                    pass
        
        # Filter by teacher_assigned
        teacher_assigned = self.request.query_params.get('teacher_assigned')
        if teacher_assigned is not None:
            if teacher_assigned.lower() == 'true':
                queryset = queryset.exclude(teacher__isnull=True)
            elif teacher_assigned.lower() == 'false':
                queryset = queryset.filter(teacher__isnull=True)
        
        return queryset

    def perform_create(self, serializer):
        cls = serializer.save()
        # Session generation can be handled separately if needed

    def update(self, request, *args, **kwargs):
        """Override update to handle errors better"""
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        
        try:
            instance = self.get_object()
            logger.info(f"Updating class {instance.id} with data: {request.data}")
            
            # Log the data being sent
            logger.debug(f"Request data: {request.data}")
            logger.debug(f"Partial update: {kwargs.get('partial', False)}")
            
            response = super().update(request, *args, **kwargs)
            logger.info(f"Successfully updated class {instance.id}")
            return response
            
        except serializers.ValidationError as e:
            logger.error(f"Validation error updating class: {str(e)}")
            logger.error(f"Validation errors: {e.detail}")
            # Check if it's a status validation error
            if isinstance(e.detail, dict) and 'status' in e.detail:
                return Response(
                    {
                        'detail': 'Validation error',
                        'errors': e.detail,
                        'status_error': True
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'detail': 'Validation error', 'errors': e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error updating class: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Check for database enum constraint errors (PostgreSQL specific)
            error_str = str(e)
            # Only catch actual database enum constraint errors
            if ('invalid input value for enum' in error_str.lower() and 'class_status_enum' in error_str.lower()) or \
               ('invalid input syntax for type' in error_str.lower() and 'enum' in error_str.lower()):
                # Extract status value from request if available
                status_value = request.data.get('status', 'unknown')
                logger.error(f"Database enum constraint error. Status value received: '{status_value}'")
                logger.error(f"Full error: {error_str}")
                return Response(
                    {
                        'detail': f'Database enum constraint error. Status value "{status_value}" is not valid for enum class_status_enum. Valid values are: planned, ongoing, completed, cancelled',
                        'status_received': status_value,
                        'valid_statuses': ['planned', 'ongoing', 'completed', 'cancelled'],
                        'error_type': 'enum_constraint'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Return more detailed error message
            error_detail = str(e)
            if hasattr(e, 'detail'):
                error_detail = e.detail
            return Response(
                {'detail': f'Error updating class: {error_detail}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_update(self, serializer):
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        
        try:
            # Log validated data before saving
            validated_data = serializer.validated_data
            logger.debug(f"Validated data before save: {validated_data}")
            
            # Ensure status is lowercase if present
            if 'status' in validated_data:
                status_value = validated_data['status']
                logger.info(f"Status value before save: '{status_value}' (type: {type(status_value)})")
                
                # Normalize status value
                if status_value:
                    # Convert to string and strip whitespace
                    status_str = str(status_value).strip().lower()
                    valid_statuses = ['planned', 'ongoing', 'completed', 'cancelled']
                    
                    logger.debug(f"Normalized status: '{status_str}', checking against: {valid_statuses}")
                    
                    if status_str not in valid_statuses:
                        logger.error(f"Invalid status value detected: '{status_value}' (normalized: '{status_str}')")
                        raise serializers.ValidationError(
                            {'status': f"Invalid status '{status_value}'. Must be one of: {', '.join(valid_statuses)}"}
                        )
                    
                    # Map model status values to database enum values
                    # Model uses: planned, ongoing, completed, cancelled
                    # Database uses: planned, ongoing, finished, canceled
                    status_mapping = {
                        'completed': 'finished',
                        'cancelled': 'canceled',
                        'planned': 'planned',
                        'ongoing': 'ongoing'
                    }
                    
                    # Map to database enum value
                    db_status = status_mapping.get(status_str, status_str)
                    validated_data['status'] = db_status
                    logger.debug(f"Status mapped from '{status_str}' to database value '{db_status}'")
            
            # Try to save, if enum error occurs, try to query enum values and match
            try:
                cls = serializer.save()
                logger.info(f"Successfully saved class {cls.id} with status: {cls.status}")
            except Exception as save_error:
                error_str = str(save_error)
                # If it's an enum constraint error, try to query enum values and use correct case
                if 'invalid input value for enum' in error_str.lower() and 'class_status_enum' in error_str.lower():
                    logger.warning(f"Enum constraint error during save: {error_str}")
                    logger.warning("Attempting to query database enum values...")
                    
                    # Query enum values from database
                    from django.db import connection
                    try:
                        with connection.cursor() as cursor:
                            # PostgreSQL query to get enum values
                            cursor.execute("""
                                SELECT enumlabel 
                                FROM pg_enum 
                                WHERE enumtypid = (
                                    SELECT oid 
                                    FROM pg_type 
                                    WHERE typname = 'class_status_enum'
                                )
                                ORDER BY enumsortorder;
                            """)
                            enum_values = [row[0] for row in cursor.fetchall()]
                            logger.info(f"Database enum values: {enum_values}")
                    except Exception as query_error:
                        logger.error(f"Error querying enum values: {query_error}")
                        # Fallback: try common enum value formats
                        enum_values = ['planned', 'ongoing', 'completed', 'cancelled',
                                     'PLANNED', 'ONGOING', 'COMPLETED', 'CANCELLED']
                        logger.warning(f"Using fallback enum values: {enum_values}")
                    
                    # Get the instance
                    cls = serializer.instance
                    status_to_save = validated_data.get('status', cls.status)
                    
                    # Map model values to database enum values
                    # Model uses: planned, ongoing, completed, cancelled
                    # Database uses: planned, ongoing, finished, canceled
                    status_mapping = {
                        'completed': 'finished',
                        'cancelled': 'canceled',
                        'planned': 'planned',
                        'ongoing': 'ongoing'
                    }
                    
                    # Try to match with enum values (case-insensitive)
                    status_matched = None
                    
                    # First, try direct mapping
                    if status_to_save.lower() in status_mapping:
                        mapped_status = status_mapping[status_to_save.lower()]
                        # Check if mapped status exists in enum values
                        for enum_val in enum_values:
                            if enum_val.lower() == mapped_status.lower():
                                status_matched = enum_val
                                break
                    
                    # If not found, try direct match (case-insensitive)
                    if not status_matched:
                        for enum_val in enum_values:
                            if enum_val.lower() == status_to_save.lower():
                                status_matched = enum_val
                                break
                    
                    if status_matched:
                        logger.info(f"Matched status '{status_to_save}' to enum value '{status_matched}'")
                        # Update with matched enum value
                        Class.objects.filter(id=cls.id).update(status=status_matched)
                        cls.refresh_from_db()
                        logger.info(f"Successfully updated status to: '{cls.status}'")
                    else:
                        logger.error(f"Could not match status '{status_to_save}' with enum values: {enum_values}")
                        raise serializers.ValidationError(
                            {'status': f"Status '{status_to_save}' not found in database enum. Available values: {', '.join(enum_values)}"}
                        )
                else:
                    # Re-raise if it's not an enum error
                    raise
            
            # Optional: regenerate sessions if schedule changed and no teacher conflict handling yet
            # For now, regenerate if days_of_week/start_time/end_time changed would require tracking previous values.
            # Keep simple: do nothing automatically.
            return cls
        except Exception as e:
            logger.error(f"Error in perform_update: {str(e)}")
            logger.error(traceback.format_exc())
            raise

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
                    class_session_id=cls.id,
                    teacher_id=cls.teacher_id,
                )
            current = current + timedelta(days=1)

    @action(detail=True, methods=['get'], url_path='sessions')
    def list_sessions(self, request, pk=None):
        cls = self.get_object()
        sessions = Session.objects.filter(class_session_id=cls.id).order_by('study_date', 'start_time')
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
        class_sessions = list(Session.objects.filter(class_session_id=cls.id))
        teacher_classes = Class.objects.filter(teacher_id=teacher_id).values_list('id', flat=True)
        conflict = Session.objects.filter(class_session_id__in=teacher_classes).filter(
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

