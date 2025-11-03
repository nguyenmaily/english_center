from rest_framework import serializers
from .models import Session


class SessionSerializer(serializers.ModelSerializer):
    """
    Serializer cơ bản cho Session
    """
    duration = serializers.ReadOnlyField()
    is_checked_in = serializers.ReadOnlyField()
    is_checked_out = serializers.ReadOnlyField()
    
    class Meta:
        model = Session
        fields = '__all__'


class SessionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer chi tiết cho Session với thông tin class và teacher
    """
    duration = serializers.ReadOnlyField()
    is_checked_in = serializers.ReadOnlyField()
    is_checked_out = serializers.ReadOnlyField()
    class_name = serializers.CharField(source='class_session.name', read_only=True)
    course_name = serializers.CharField(source='class_session.course.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user_account.fullname', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    
    class Meta:
        model = Session
        fields = '__all__'

