from django.db import models
from django.conf import settings
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import uuid


class StudentCertificate(models.Model):
    """
    Model cho hồ sơ năng lực tiếng Anh của học viên
    Mapping với bảng student_certificates trong PostgreSQL
    """
    
    class SkillGroup(models.TextChoices):
        """Enum cho skill_group"""
        LR = 'LR', 'Listening-Reading'
        SW = 'SW', 'Speaking-Writing'
    
    class SourceType(models.TextChoices):
        """Enum cho source_type"""
        CERTIFICATE = 'certificate', 'Chứng chỉ'
        ENTRY_TEST = 'entry_test', 'Test đầu vào'
        FINAL_TEST = 'final_test', 'Test cuối khóa'
    
    class Status(models.TextChoices):
        """Enum cho status"""
        VERIFIED = 'VERIFIED', 'Đã xác thực'
        PENDING = 'PENDING', 'Chờ duyệt'
        REJECTED = 'REJECTED', 'Từ chối'
    
    class VerificationMethod(models.TextChoices):
        """Enum cho verification_method"""
        AUTO_OCR = 'auto_ocr', 'Tự động OCR'
        MANUAL_ADMIN = 'manual_admin', 'Admin duyệt thủ công'
    
    id = models.BigAutoField(primary_key=True, db_column='id')
    
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.CASCADE,
        related_name='certificates',
        db_column='student_id'
    )
    
    skill_group = models.CharField(
        max_length=2,
        choices=SkillGroup.choices,
        db_column='skill_group',
        help_text='LR: Listening-Reading; SW: Speaking-Writing'
    )
    
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        db_column='source_type',
        help_text='certificate: Chứng chỉ; entry_test: Test đầu vào; final_test: Test cuối khóa'
    )
    
    score_1 = models.IntegerField(
        null=True,
        blank=True,
        db_column='score_1',
        help_text='Listening (nếu LR) hoặc Speaking (nếu SW)'
    )
    
    score_2 = models.IntegerField(
        null=True,
        blank=True,
        db_column='score_2',
        help_text='Reading (nếu LR) hoặc Writing (nếu SW)'
    )
    
    total_score = models.IntegerField(
        db_column='total_score',
        help_text='Điểm tổng. LR: 0-990, SW: 0-400'
    )
    
    test_date = models.DateField(
        db_column='test_date',
        help_text='Ngày thi hoặc ngày làm bài'
    )
    
    expired_date = models.DateField(
        db_column='expired_date',
        help_text='Ngày hết hạn của kết quả'
    )
    
    proof_image = models.TextField(
        null=True,
        blank=True,
        db_column='proof_image',
        help_text='Link ảnh chứng chỉ'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_column='status',
        help_text='VERIFIED: Đã xác thực; PENDING: Chờ duyệt; REJECTED: Từ chối'
    )
    
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_certificates',
        db_column='admin_id',
        help_text='Admin thực hiện duyệt (null nếu hệ thống tự duyệt)'
    )
    
    verification_method = models.CharField(
        max_length=20,
        choices=VerificationMethod.choices,
        default=VerificationMethod.AUTO_OCR,
        db_column='verification_method',
        help_text='auto_ocr: Tự động xác thực bằng OCR; manual_admin: Admin duyệt thủ công'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    updated_at = models.DateTimeField(auto_now=True, db_column='updated_at')
    
    class Meta:
        db_table = 'student_certificates'
        managed = False  # Bảng đã được tạo từ SQL script, Django không quản lý
        verbose_name = 'Student Certificate'
        verbose_name_plural = 'Student Certificates'
        ordering = ['-test_date']
        indexes = [
            models.Index(fields=['student', 'skill_group']),
            models.Index(fields=['status']),
            models.Index(fields=['-test_date']),
            models.Index(fields=['expired_date']),
            models.Index(fields=['student', 'skill_group', 'status', 'expired_date']),
        ]
    
    def __str__(self):
        return f"{self.student.display_name} - {self.get_skill_group_display()} - {self.total_score} ({self.get_status_display()})"
    
    @property
    def is_expired(self):
        """Kiểm tra chứng chỉ đã hết hạn chưa"""
        return self.expired_date < timezone.now().date()
    
    @property
    def is_current(self):
        """Kiểm tra đây có phải là năng lực hiện tại không (VERIFIED và còn hạn)"""
        return (
            self.status == self.Status.VERIFIED and
            not self.is_expired
        )
    
    @staticmethod
    def calculate_expired_date_for_certificate(test_date):
        """
        Tính expired_date cho chứng chỉ: test_date + 2 năm
        """
        return test_date + relativedelta(years=2)
    
    @staticmethod
    def calculate_expired_date_for_test():
        """
        Tính expired_date cho test: today + 6 tháng
        """
        return timezone.now().date() + relativedelta(months=6)
    
    def clean(self):
        """Validation logic"""
        from django.core.exceptions import ValidationError
        
        # Validate điểm số theo skill_group
        if self.skill_group == self.SkillGroup.LR:
            if self.total_score < 0 or self.total_score > 990:
                raise ValidationError({'total_score': 'Điểm LR phải trong khoảng 0-990'})
        elif self.skill_group == self.SkillGroup.SW:
            if self.total_score < 0 or self.total_score > 400:
                raise ValidationError({'total_score': 'Điểm SW phải trong khoảng 0-400'})
        
        # Validate expired_date >= test_date
        if self.expired_date < self.test_date:
            raise ValidationError({'expired_date': 'Ngày hết hạn phải sau hoặc bằng ngày thi'})
    
    def save(self, *args, **kwargs):
        """Override save để tự động tính expired_date nếu chưa có"""
        if not self.expired_date:
            if self.source_type == self.SourceType.CERTIFICATE:
                self.expired_date = self.calculate_expired_date_for_certificate(self.test_date)
            else:
                self.expired_date = self.calculate_expired_date_for_test()
        
        self.full_clean()
        super().save(*args, **kwargs)
