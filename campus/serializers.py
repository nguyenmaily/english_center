from rest_framework import serializers
from .models import Campus, Room, Equipment


class CampusSerializer(serializers.ModelSerializer):
    """
    Serializer for Campus model
    """
    class Meta:
        model = Campus
        fields = ['id', 'name', 'address', 'phone', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CampusDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Campus with rooms count
    """
    rooms_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Campus
        fields = ['id', 'name', 'address', 'phone', 'rooms_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_rooms_count(self, obj):
        return obj.rooms.count()


class RoomSerializer(serializers.ModelSerializer):
    """
    Serializer for Room model
    """
    campus_name = serializers.CharField(source='campus.name', read_only=True)
    
    class Meta:
        model = Room
        fields = ['id', 'name', 'is_under_repair', 'campus', 'campus_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoomDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Room with equipment count
    """
    campus_name = serializers.CharField(source='campus.name', read_only=True)
    equipments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Room
        fields = ['id', 'name', 'is_under_repair', 'campus', 'campus_name', 
                  'equipments_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_equipments_count(self, obj):
        return obj.equipments.count()


class EquipmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Equipment model
    """
    room_name = serializers.CharField(source='room.name', read_only=True)
    campus_name = serializers.CharField(source='room.campus.name', read_only=True)
    
    class Meta:
        model = Equipment
        fields = ['id', 'name', 'status', 'room', 'room_name', 'campus_name', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
