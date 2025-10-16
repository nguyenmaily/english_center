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
    """
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_campus',
        'POST': 'manage_campus',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address', 'phone']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']


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
    """
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    permission_map = {
        'GET': 'view_campus',
    }
    
    def get_queryset(self):
        # ✅ FIX: Thêm check cho Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Room.objects.none()
        
        campus_id = self.kwargs['pk']
        return Room.objects.filter(campus_id=campus_id).select_related('campus')

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
        # ✅ FIX: Thêm check cho Swagger
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
