from rest_framework import serializers
from .models import StudentCertificate
from users.models import Student


class StudentCertificateSerializer(serializers.ModelSerializer):
    """Serializer cho StudentCertificate - hiển thị đầy đủ thông tin"""
    
    skill_group_display = serializers.CharField(source='get_skill_group_display', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    verification_method_display = serializers.CharField(source='get_verification_method_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_current = serializers.BooleanField(read_only=True)
    student_name = serializers.CharField(source='student.display_name', read_only=True)
    admin_name = serializers.CharField(source='admin.fullname', read_only=True, allow_null=True)
    
    class Meta:
        model = StudentCertificate
        fields = [
            'id',
            'student',
            'student_name',
            'skill_group',
            'skill_group_display',
            'source_type',
            'source_type_display',
            'score_1',
            'score_2',
            'total_score',
            'test_date',
            'expired_date',
            'proof_image',
            'status',
            'status_display',
            'admin',
            'admin_name',
            'verification_method',
            'verification_method_display',
            'is_expired',
            'is_current',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status', 'admin', 'verification_method']


class StudentCertificateCreateSerializer(serializers.ModelSerializer):
    """Serializer cho tạo mới chứng chỉ (upload certificate)"""
    
    class Meta:
        model = StudentCertificate
        fields = [
            'skill_group',
            'score_1',
            'score_2',
            'total_score',
            'test_date',
            'proof_image',
        ]
    
    def validate(self, attrs):
        """Validation logic"""
        skill_group = attrs.get('skill_group')
        total_score = attrs.get('total_score')
        
        # Validate điểm số theo skill_group
        if skill_group == StudentCertificate.SkillGroup.LR:
            if total_score < 0 or total_score > 990:
                raise serializers.ValidationError({
                    'total_score': 'Điểm LR phải trong khoảng 0-990'
                })
        elif skill_group == StudentCertificate.SkillGroup.SW:
            if total_score < 0 or total_score > 400:
                raise serializers.ValidationError({
                    'total_score': 'Điểm SW phải trong khoảng 0-400'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Tạo mới certificate với source_type = CERTIFICATE"""
        validated_data['source_type'] = StudentCertificate.SourceType.CERTIFICATE
        validated_data['status'] = StudentCertificate.Status.PENDING
        validated_data['verification_method'] = StudentCertificate.VerificationMethod.AUTO_OCR
        
        # Lấy student từ request user
        user = self.context['request'].user
        try:
            student = Student.objects.get(user_account=user)
            validated_data['student'] = student
        except Student.DoesNotExist:
            raise serializers.ValidationError({
                'student': 'Bạn chưa có profile học viên'
            })
        
        # Tính expired_date
        test_date = validated_data['test_date']
        validated_data['expired_date'] = StudentCertificate.calculate_expired_date_for_certificate(test_date)
        
        return super().create(validated_data)


class PlacementTestResultSerializer(serializers.ModelSerializer):
    """Serializer cho kết quả Placement Test"""
    
    class Meta:
        model = StudentCertificate
        fields = [
            'skill_group',
            'score_1',
            'score_2',
            'total_score',
        ]
    
    def validate(self, attrs):
        """Validation logic"""
        skill_group = attrs.get('skill_group')
        total_score = attrs.get('total_score')
        
        # Validate điểm số theo skill_group
        if skill_group == StudentCertificate.SkillGroup.LR:
            if total_score < 0 or total_score > 990:
                raise serializers.ValidationError({
                    'total_score': 'Điểm LR phải trong khoảng 0-990'
                })
        elif skill_group == StudentCertificate.SkillGroup.SW:
            if total_score < 0 or total_score > 400:
                raise serializers.ValidationError({
                    'total_score': 'Điểm SW phải trong khoảng 0-400'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Tạo mới certificate với source_type = ENTRY_TEST"""
        validated_data['source_type'] = StudentCertificate.SourceType.ENTRY_TEST
        validated_data['status'] = StudentCertificate.Status.VERIFIED
        validated_data['verification_method'] = StudentCertificate.VerificationMethod.AUTO_OCR
        
        # Lấy student từ request user
        user = self.context['request'].user
        try:
            student = Student.objects.get(user_account=user)
            validated_data['student'] = student
        except Student.DoesNotExist:
            raise serializers.ValidationError({
                'student': 'Bạn chưa có profile học viên'
            })
        
        # Set test_date = today và tính expired_date
        from django.utils import timezone
        validated_data['test_date'] = timezone.now().date()
        validated_data['expired_date'] = StudentCertificate.calculate_expired_date_for_test()
        
        return super().create(validated_data)


class ProficiencyProfileSerializer(serializers.Serializer):
    """Serializer cho profile tổng hợp - highlight cards + history"""
    
    current_lr = StudentCertificateSerializer(allow_null=True)
    current_sw = StudentCertificateSerializer(allow_null=True)
    history = StudentCertificateSerializer(many=True)
    can_take_placement_test_lr = serializers.BooleanField()
    can_take_placement_test_sw = serializers.BooleanField()






