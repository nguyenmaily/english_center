from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ReserveRequest, LeaveRequest


class ReserveRequestSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ReserveRequest
        fields = '__all__'
    
    def get_student_name(self, obj):
        """Lấy tên học viên từ user_account"""
        try:
            from users.models import Student
            student = Student.objects.select_related('user_account').get(id=obj.student_id)
            return student.user_account.fullname or student.user_account.username
        except Exception:
            return f"Học viên {str(obj.student_id)[:8]}..."
    
    def get_class_name(self, obj):
        """Lấy tên lớp học"""
        try:
            from classes.models import Class
            cls = Class.objects.get(id=obj.class_id)
            return cls.name
        except Exception:
            return f"Lớp {str(obj.class_id)[:8]}..."


class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = '__all__'


class ReserveRequestViewSet(viewsets.ModelViewSet):
    queryset = ReserveRequest.objects.all().order_by('-created_at')
    serializer_class = ReserveRequestSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create method to set default status"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Set status to pending by default
        serializer.save(status='pending')
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        """Override update to only allow updating pending requests"""
        instance = self.get_object()
        if instance.status != 'pending':
            return Response(
                {'detail': 'Chỉ có thể sửa yêu cầu ở trạng thái đang chờ (pending)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Prevent status change when updating
        if 'status' in request.data:
            request.data.pop('status')
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to only allow deleting pending requests"""
        instance = self.get_object()
        if instance.status != 'pending':
            return Response(
                {'detail': 'Chỉ có thể xóa yêu cầu ở trạng thái đang chờ (pending)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], url_path='my')
    def my_reserve_requests(self, request):
        """Student views their reserve requests"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({'detail': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        qs = ReserveRequest.objects.filter(student_id=student_id).order_by('-created_at')
        return Response(ReserveRequestSerializer(qs, many=True).data)
    
    @action(detail=False, methods=['get'], url_path='manager-classes')
    def manager_class_requests(self, request):
        """Get reserve requests for classes in manager's campus"""
        from classes.models import Class
        from users.models import Manager
        
        # Get manager's campus
        manager_campus_id = None
        if hasattr(request.user, 'roleid') and request.user.roleid:
            if request.user.roleid.name == 'manager':
                try:
                    manager = Manager.objects.select_related('campus').get(user_account=request.user)
                    if manager.campus:
                        manager_campus_id = manager.campus.id
                except Manager.DoesNotExist:
                    pass
        
        # If manager has no campus, return empty list
        if manager_campus_id is None:
            # Check if user is admin - admin can see all
            if hasattr(request.user, 'roleid') and request.user.roleid:
                if request.user.roleid.name == 'admin':
                    # Admin can see all
                    qs = ReserveRequest.objects.all().order_by('-created_at')
                else:
                    # Not manager and not admin - return empty
                    return Response([])
            else:
                return Response([])
        else:
            # Get all classes in manager's campus
            campus_classes = Class.objects.filter(campus_id=manager_campus_id).values_list('id', flat=True)
            
            if not campus_classes:
                return Response([])
            
            # Get reserve requests for these classes only
            qs = ReserveRequest.objects.filter(class_id__in=campus_classes).order_by('-created_at')
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        return Response(ReserveRequestSerializer(qs, many=True).data)
    
    @action(detail=True, methods=['patch'], url_path='manager-approval')
    def manager_approval(self, request, pk=None):
        """Manager approves/rejects reserve request"""
        from enrollment.models import Enrollment
        
        reserve_request = self.get_object()
        
        # Check if request is still pending
        if reserve_request.status != 'pending':
            return Response(
                {'detail': 'Yêu cầu này đã được xử lý'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action_type = request.data.get('action')  # 'approve' or 'reject'
        
        if action_type == 'approve':
            import logging
            logger = logging.getLogger(__name__)
            
            reserve_request.status = 'approved'
            
            # Xóa học viên khỏi lớp học khi phê duyệt bảo lưu
            # Thay vì xóa enrollment, set class_id = NULL và giữ course_id
            enrollment_updated = False
            try:
                from classes.models import Class
                from django.db import transaction
                
                logger.info(f'Processing approval for reserve request {reserve_request.id}, student_id: {reserve_request.student_id}, class_id: {reserve_request.class_id}')
                
                enrollment = Enrollment.objects.get(
                    student_id=reserve_request.student_id,
                    class_id=reserve_request.class_id
                )
                
                logger.info(f'Found enrollment {enrollment.id}, current class_id: {enrollment.class_id}, current course_id: {enrollment.course_id}')
                
                # Lấy course_id từ class để lưu vào enrollment
                course_id = enrollment.course_id
                if not course_id:
                    try:
                        cls = Class.objects.get(id=reserve_request.class_id)
                        course_id = cls.course_id
                        logger.info(f'Set course_id from class: {course_id}')
                    except Class.DoesNotExist:
                        logger.warning(f'Class {reserve_request.class_id} not found')
                        course_id = None
                
                # Set class_id = NULL để xóa học viên khỏi lớp nhưng giữ lại course_id
                old_class_id = enrollment.class_id
                
                logger.info(f'Setting class_id from {old_class_id} to NULL, keeping course_id: {course_id}')
                
                # Sử dụng transaction để đảm bảo update thành công
                with transaction.atomic():
                    # Sử dụng raw SQL để đảm bảo update thành công, bỏ qua unique constraint
                    from django.db import connection
                    with connection.cursor() as cursor:
                        # Update với course_id (có thể NULL nếu không tìm được)
                        if course_id:
                            cursor.execute(
                                "UPDATE enrollments SET class_id = NULL, course_id = %s, updated_at = NOW() WHERE id = %s",
                                [course_id, str(enrollment.id)]
                            )
                        else:
                            cursor.execute(
                                "UPDATE enrollments SET class_id = NULL, updated_at = NOW() WHERE id = %s",
                                [str(enrollment.id)]
                            )
                        
                        # Verify update
                        cursor.execute(
                            "SELECT class_id, course_id FROM enrollments WHERE id = %s",
                            [str(enrollment.id)]
                        )
                        result = cursor.fetchone()
                        if result:
                            updated_class_id, updated_course_id = result
                            if updated_class_id is None:
                                enrollment_updated = True
                                logger.info(f'✅ Successfully updated enrollment {enrollment.id}: class_id={updated_class_id}, course_id={updated_course_id}')
                            else:
                                logger.error(f'❌ Enrollment {enrollment.id} class_id is still NOT NULL after update: {updated_class_id}')
                                raise Exception(f'Failed to set class_id to NULL. Current value: {updated_class_id}')
                        else:
                            logger.error(f'❌ Enrollment {enrollment.id} not found after update')
                            raise Exception(f'Enrollment {enrollment.id} not found after update')
                
            except Enrollment.DoesNotExist:
                # Enrollment không tồn tại, có thể đã bị xóa trước đó
                logger.error(f'❌ Enrollment not found for student_id: {reserve_request.student_id}, class_id: {reserve_request.class_id}')
                return Response(
                    {'detail': 'Không tìm thấy enrollment để cập nhật. Vui lòng kiểm tra lại.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                # Log lỗi chi tiết và return error
                import traceback
                logger.error(f'❌ Error updating enrollment when approving reserve request: {str(e)}')
                logger.error(traceback.format_exc())
                return Response(
                    {
                        'detail': f'Không thể cập nhật enrollment: {str(e)}',
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Chỉ approve reserve request nếu enrollment đã được update thành công
            if not enrollment_updated:
                logger.error(f'❌ Enrollment was not updated successfully for reserve request {reserve_request.id}')
                return Response(
                    {'detail': 'Không thể cập nhật enrollment. Vui lòng thử lại.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            reserve_request.save(update_fields=['status', 'updated_at'])
            return Response({
                'detail': 'Reserve request approved by manager. Student has been removed from the class.',
                'enrollment_updated': True
            })
        elif action_type == 'reject':
            reserve_request.status = 'rejected'
            reserve_request.save(update_fields=['status', 'updated_at'])
            return Response({'detail': 'Reserve request rejected by manager'})
        else:
            return Response({'detail': 'Invalid action. Use "approve" or "reject"'}, 
                          status=status.HTTP_400_BAD_REQUEST)


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all().order_by('-created_at')
    serializer_class = LeaveRequestSerializer

    def get_queryset(self):
        """Override to filter by student_id if provided"""
        qs = super().get_queryset()
        student_id = self.request.query_params.get('student_id')
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs

    def create(self, request, *args, **kwargs):
        """Override create method to set default status"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Set status to pending by default
        serializer.save(status='pending')
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        """Override update to only allow updating pending requests"""
        instance = self.get_object()
        if instance.status != 'pending':
            return Response(
                {'detail': 'Chỉ có thể sửa yêu cầu ở trạng thái đang chờ (pending)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Prevent status change when updating
        if 'status' in request.data:
            request.data.pop('status')
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to only allow deleting pending requests"""
        instance = self.get_object()
        if instance.status != 'pending':
            return Response(
                {'detail': 'Chỉ có thể xóa yêu cầu ở trạng thái đang chờ (pending)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='my')
    def my_leave_requests(self, request):
        """Student views their leave requests"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({'detail': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        qs = LeaveRequest.objects.filter(student_id=student_id).order_by('-created_at')
        return Response(LeaveRequestSerializer(qs, many=True).data)
    
    @action(detail=False, methods=['get'], url_path='teacher-classes')
    def teacher_class_requests(self, request):
        """Get leave requests for classes taught by teacher"""
        from classes.models import Class
        
        # Get teacher_id from query params or from user
        teacher_id = request.query_params.get('teacher_id')
        if not teacher_id:
            # Try to get from user's teacher_profile
            if hasattr(request.user, 'teacher_profile'):
                teacher_id = str(request.user.teacher_profile.id)
            else:
                return Response({'detail': 'teacher_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all classes taught by this teacher
        teacher_classes = Class.objects.filter(teacher_id=teacher_id).values_list('id', flat=True)
        
        if not teacher_classes:
            return Response([])
        
        # Get leave requests for these classes
        qs = LeaveRequest.objects.filter(class_id__in=teacher_classes).order_by('-created_at')
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        return Response(LeaveRequestSerializer(qs, many=True).data)

    @action(detail=True, methods=['patch'], url_path='teacher-approval')
    def teacher_approval(self, request, pk=None):
        """Teacher approves/rejects leave request"""
        from classes.models import Class
        
        leave_request = self.get_object()
        
        # Verify teacher has access to this class
        if hasattr(request.user, 'teacher_profile'):
            teacher = request.user.teacher_profile
            try:
                cls = Class.objects.get(id=leave_request.class_id)
                if str(cls.teacher_id) != str(teacher.id):
                    return Response(
                        {'detail': 'Bạn không có quyền phê duyệt yêu cầu này'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Class.DoesNotExist:
                return Response(
                    {'detail': 'Lớp học không tồn tại'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Check if request is still pending
        if leave_request.status != 'pending':
            return Response(
                {'detail': 'Yêu cầu này đã được xử lý'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action_type = request.data.get('action')  # 'approve' or 'reject'
        
        if action_type == 'approve':
            leave_request.status = 'approved'
            leave_request.save(update_fields=['status', 'updated_at'])
            return Response({'detail': 'Leave request approved by teacher'})
        elif action_type == 'reject':
            leave_request.status = 'rejected'
            leave_request.save(update_fields=['status', 'updated_at'])
            return Response({'detail': 'Leave request rejected by teacher'})
        else:
            return Response({'detail': 'Invalid action. Use "approve" or "reject"'}, 
                          status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='manager-approval')
    def manager_approval(self, request, pk=None):
        """Manager approves/rejects leave request"""
        leave_request = self.get_object()
        action_type = request.data.get('action')  # 'approve' or 'reject'
        
        if action_type == 'approve':
            leave_request.status = 'approved'
            leave_request.save(update_fields=['status', 'updated_at'])
            return Response({'detail': 'Leave request approved by manager'})
        elif action_type == 'reject':
            leave_request.status = 'rejected'
            leave_request.save(update_fields=['status', 'updated_at'])
            return Response({'detail': 'Leave request rejected by manager'})
        else:
            return Response({'detail': 'Invalid action. Use "approve" or "reject"'}, 
                          status=status.HTTP_400_BAD_REQUEST)
