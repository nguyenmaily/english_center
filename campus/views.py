from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from authentication.permissions import PermissionMixin
from .models import Campus, Room, Equipment
from .serializers import (
    CampusSerializer, CampusDetailSerializer,
    RoomSerializer, RoomDetailSerializer,
    EquipmentSerializer
)


# ==================== CAMPUS VIEWS ====================

class CampusListCreateView(PermissionMixin, generics.ListCreateAPIView):
    """
    GET /api/campus/campuses/ - Lấy danh sách tất cả campus
    POST /api/campus/campuses/ - Tạo campus mới (cần quyền: manage_campus)
    
    Note: Manager relationship is via ManagerProfile.campus_id (reverse)
    
    ============================================================================
    PERMISSIONS - QUAN TRỌNG!
    ============================================================================
    permission_map định nghĩa permission cần thiết cho mỗi HTTP method:
    - 'GET': 'view_campus'   → Cần permission 'view_campus' để xem danh sách
    - 'POST': 'manage_campus' → Cần permission 'manage_campus' để tạo mới
    
    Để biết permission này thuộc role nào:
    1. Tìm file: english_center/authentication/management/commands/setup_auth_data.py
    2. Xem dictionary 'role_permissions' (dòng ~61)
    3. Tìm permission name trong danh sách của role
    
    Ví dụ: 'manage_campus' có thể thuộc 'admin' hoặc 'manager'
    ============================================================================
    """
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_campus',      # Permission để GET (xem)
        'POST': 'manage_campus',  # Permission để POST (tạo mới)
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status'] 
    search_fields = ['name', 'address', 'hotline', 'email']  
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter queryset based on user role:
        - Admin: See all campuses
        - Manager: Only see their own campus
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # Check if user is manager
        if hasattr(user, 'roleid') and user.roleid:
            role_name = user.roleid.name
            
            if role_name == 'manager':
                # Manager chỉ thấy campus của họ
                from users.models import Manager
                try:
                    manager = Manager.objects.select_related('campus').get(user_account=user)
                    if manager.campus:
                        queryset = queryset.filter(id=manager.campus.id)
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Manager {user.username} filtering campuses to: {manager.campus.name}")
                    else:
                        # Manager chưa có campus → không thấy campus nào
                        queryset = queryset.none()
                except Manager.DoesNotExist:
                    # User không phải manager → không filter (admin sẽ thấy tất cả)
                    pass
        
        return queryset


class CampusDetailView(PermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/campus/campuses/{id}/ - Lấy chi tiết một campus
    PUT /api/campus/campuses/{id}/ - Cập nhật toàn bộ campus (cần quyền: manage_campus)
    PATCH /api/campus/campuses/{id}/ - Cập nhật một phần campus (cần quyền: manage_campus)
    DELETE /api/campus/campuses/{id}/ - Xóa campus (cần quyền: manage_campus)
    """
    queryset = Campus.objects.all()
    serializer_class = CampusDetailSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_campus',
        'PUT': 'manage_campus',
        'PATCH': 'manage_campus',
        'DELETE': 'manage_campus',
    }
    lookup_field = 'pk'


class CampusRoomsView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/campus/campuses/{id}/rooms/ - Lấy danh sách phòng của campus
    
    Permission: 
    - view_campus (admin, manager, student)
    - view_classes (teacher - cần để xem phòng học khi thêm buổi học)
    """
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_campus',  # Default permission
    }
    
    def check_permissions(self, request):
        """
        Override để cho phép teacher với view_classes permission cũng có thể truy cập
        """
        from authentication.permissions import check_user_permission
        
        # Check default permission (view_campus)
        if check_user_permission(request.user, 'view_campus'):
            return
        
        # Nếu không có view_campus, check xem có view_classes không (cho teacher)
        if check_user_permission(request.user, 'view_classes'):
            return
        
        # Nếu không có cả 2, raise PermissionDenied
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied(
            detail={
                'error': 'Permission denied',
                'message': 'Bạn không có quyền xem danh sách phòng học',
                'detail': 'Cần quyền: view_campus hoặc view_classes',
                'required_permission': 'view_campus hoặc view_classes'
            }
        )
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Room.objects.none()
        
        campus_id = self.kwargs['pk']
        
        # Validate campus exists
        campus = get_object_or_404(Campus, id=campus_id)
        
        # Filter rooms by campus_id - chỉ trả về phòng học của campus này
        queryset = Room.objects.filter(campus_id=campus_id).select_related('campus')
        
        # Log để debug
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"📋 Loading rooms for campus: {campus.name} (ID: {campus_id})")
        logger.info(f"📋 Found {queryset.count()} rooms for this campus")
        
        return queryset


# ==================== ROOM VIEWS ====================

class RoomListCreateView(PermissionMixin, generics.ListCreateAPIView):
    """
    GET /api/campus/rooms/ - Lấy danh sách tất cả phòng
    POST /api/campus/rooms/ - Tạo phòng mới (cần quyền: manage_rooms)
    """
    queryset = Room.objects.select_related('campus').all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_rooms',
        'POST': 'manage_rooms',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['campus', 'is_under_repair']
    search_fields = ['name', 'campus__name']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']


class RoomDetailView(PermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/campus/rooms/{id}/ - Lấy chi tiết một phòng
    PUT /api/campus/rooms/{id}/ - Cập nhật toàn bộ phòng (cần quyền: manage_rooms)
    PATCH /api/campus/rooms/{id}/ - Cập nhật một phần phòng (cần quyền: manage_rooms)
    DELETE /api/campus/rooms/{id}/ - Xóa phòng (cần quyền: manage_rooms)
    """
    queryset = Room.objects.select_related('campus').all()
    serializer_class = RoomDetailSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_rooms',
        'PUT': 'manage_rooms',
        'PATCH': 'manage_rooms',
        'DELETE': 'manage_rooms',
    }
    lookup_field = 'pk'


class RoomEquipmentsView(PermissionMixin, generics.ListAPIView):
    """
    GET /api/campus/rooms/{id}/equipments/ - Lấy danh sách thiết bị của phòng
    """
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_equipments',
    }
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Equipment.objects.none()
        
        room_id = self.kwargs['pk']
        return Equipment.objects.filter(room_id=room_id).select_related('room', 'room__campus')


class RoomToggleRepairView(PermissionMixin, APIView):
    """
    PATCH /api/campus/rooms/{id}/toggle-repair/ - Chuyển đổi trạng thái sửa chữa (cần quyền: manage_rooms)
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'PATCH': 'manage_rooms',
    }
    
    def patch(self, request, pk):
        room = get_object_or_404(Room.objects.select_related('campus'), pk=pk)
        room.is_under_repair = not room.is_under_repair
        room.save()
        serializer = RoomDetailSerializer(room)
        return Response(serializer.data)


# ==================== EQUIPMENT VIEWS ====================

class EquipmentListCreateView(PermissionMixin, generics.ListCreateAPIView):
    """
    GET /api/campus/equipments/ - Lấy danh sách tất cả thiết bị
    POST /api/campus/equipments/ - Tạo thiết bị mới (cần quyền: manage_equipments)
    """
    queryset = Equipment.objects.select_related('room', 'room__campus').all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_equipments',
        'POST': 'manage_equipments',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['room', 'status', 'room__campus']
    search_fields = ['name', 'room__name', 'room__campus__name']
    ordering_fields = ['name', 'status', 'created_at', 'updated_at']
    ordering = ['-created_at']


class EquipmentDetailView(PermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/campus/equipments/{id}/ - Lấy chi tiết một thiết bị
    PUT /api/campus/equipments/{id}/ - Cập nhật toàn bộ thiết bị (cần quyền: manage_equipments)
    PATCH /api/campus/equipments/{id}/ - Cập nhật một phần thiết bị (cần quyền: manage_equipments)
    DELETE /api/campus/equipments/{id}/ - Xóa thiết bị (cần quyền: manage_equipments)
    """
    queryset = Equipment.objects.select_related('room', 'room__campus').all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_equipments',
        'PUT': 'manage_equipments',
        'PATCH': 'manage_equipments',
        'DELETE': 'manage_equipments',
    }
    lookup_field = 'pk'


class EquipmentChangeStatusView(PermissionMixin, APIView):
    """
    PATCH /api/campus/equipments/{id}/change-status/ - Thay đổi trạng thái thiết bị (cần quyền: manage_equipments)
    Body: {"status": "working" | "broken" | "maintenance"}
    """
    permission_classes = [IsAuthenticated]
    permission_map = {
        'PATCH': 'manage_equipments',
    }
    
    def patch(self, request, pk):
        equipment = get_object_or_404(
            Equipment.objects.select_related('room', 'room__campus'), 
            pk=pk
        )
        new_status = request.data.get('status')
        
        if new_status not in dict(Equipment.EquipmentStatus.choices):
            return Response(
                {'error': 'Invalid status value. Must be one of: working, broken, maintenance'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        equipment.status = new_status
        equipment.save()
        serializer = EquipmentSerializer(equipment)
        return Response(serializer.data)
