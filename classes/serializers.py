from rest_framework import serializers
from .models import Class


class ClassSerializer(serializers.ModelSerializer):
    """
    Serializer cơ bản cho Class
    """
    class Meta:
        model = Class
        fields = '__all__'


class ClassDetailSerializer(serializers.ModelSerializer):
    """
    Serializer chi tiết cho Class với thông tin bổ sung
    """
    sessions_count = serializers.SerializerMethodField()
    is_teacher_assigned = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()
    available_slots = serializers.ReadOnlyField()
    enrollment_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = Class
        fields = '__all__'
    
    def get_sessions_count(self, obj):
        """Đếm số sessions của class"""
        return obj.sessions.count() if hasattr(obj, 'sessions') else 0

