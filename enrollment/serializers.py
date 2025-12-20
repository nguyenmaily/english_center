from rest_framework import serializers
from .models import Enrollment, Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class EnrollmentSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    placement_exam_result_id = serializers.UUIDField(source='placement_exam_result.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Enrollment
        fields = '__all__'
        extra_kwargs = {
            'placement_exam_result': {'required': False, 'allow_null': True}
        }


