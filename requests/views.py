from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ReserveRequest, LeaveRequest


class ReserveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReserveRequest
        fields = '__all__'


class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = '__all__'


class ReserveRequestViewSet(viewsets.ModelViewSet):
    queryset = ReserveRequest.objects.all().order_by('-created_at')
    serializer_class = ReserveRequestSerializer


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all().order_by('-created_at')
    serializer_class = LeaveRequestSerializer

    def create(self, request, *args, **kwargs):
        """Override create method to set default status"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Set status to pending by default
        serializer.save(status='pending')
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'], url_path='my')
    def my_leave_requests(self, request):
        """Student views their leave requests"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({'detail': 'student_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        qs = LeaveRequest.objects.filter(student_id=student_id).order_by('-created_at')
        return Response(LeaveRequestSerializer(qs, many=True).data)

    @action(detail=True, methods=['patch'], url_path='teacher-approval')
    def teacher_approval(self, request, pk=None):
        """Teacher approves/rejects leave request"""
        leave_request = self.get_object()
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
