from rest_framework import serializers
from .models import Campus, Room, Equipment
from django.contrib.auth import get_user_model

User = get_user_model()


class CampusSerializer(serializers.ModelSerializer):
    """
    Serializer for Campus model
    
    Note: Manager is assigned via ManagerProfile.campus_id (reverse relationship)
    Not via Campus.manager_id (forward relationship)
    """
    manager_name = serializers.SerializerMethodField()
    manager_id = serializers.SerializerMethodField()
    
    code = serializers.ReadOnlyField()
    
    class Meta:
        model = Campus
        fields = [
            'id', 'code', 'name', 'address', 'hotline', 'email',
            'manager_id', 'manager_name', 'status', 'description',
            'facilities', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at', 'manager_name', 'manager_id']
    
    def get_manager_id(self, obj):
        """
        Lấy manager_id từ reverse relationship (Manager → Campus)
        Một campus chỉ có tối đa 1 manager
        """
        try:
            # Import here to avoid circular dependency
            from users.models import Manager
            manager = Manager.objects.select_related('user_account').filter(campus=obj).first()
            if manager:
                return str(manager.user_account.id)
            return None
        except Exception as e:
            print(f"❌ Error getting manager_id: {e}")
            return None
    
    def get_manager_name(self, obj):
        """
        Lấy manager name từ reverse relationship
        """
        try:
            from users.models import Manager
            manager = Manager.objects.select_related('user_account').filter(campus=obj).first()
            if manager:
                user = manager.user_account
                return user.fullname if user.fullname else user.username
            return None
        except Exception as e:
            print(f"❌ Error getting manager_name: {e}")
            return None


class CampusDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Campus with rooms count
    """
    rooms_count = serializers.SerializerMethodField()
    manager_name = serializers.SerializerMethodField()
    manager_id = serializers.SerializerMethodField()
    code = serializers.ReadOnlyField()
    
    class Meta:
        model = Campus
        fields = [
            'id', 'code', 'name', 'address', 'hotline', 'email',
            'manager_id', 'manager_name', 'status', 'description',
            'facilities', 'rooms_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'created_at', 'updated_at', 'manager_name', 'manager_id']
    
    def get_rooms_count(self, obj):
        return obj.rooms.count()
    
    def get_manager_id(self, obj):
        """Lấy manager_id từ reverse relationship"""
        try:
            from users.models import Manager
            manager = Manager.objects.select_related('user_account').filter(campus=obj).first()
            if manager:
                return str(manager.user_account.id)
            return None
        except Exception:
            return None
    
    def get_manager_name(self, obj):
        """Lấy manager name từ reverse relationship"""
        try:
            from users.models import Manager
            manager = Manager.objects.select_related('user_account').filter(campus=obj).first()
            if manager:
                user = manager.user_account
                return user.fullname if user.fullname else user.username
            return None
        except Exception:
            return None


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
        fields = ['id', 'name', 'quantity', 'status', 'room', 'room_name', 'campus_name', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']