from django.db import models
from django.conf import settings
import uuid


class Teacher(models.Model):
    """
    Model cho giảng viên
    Mapping với bảng teachers trong PostgreSQL
    """
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        db_column='id'
    )
    
    level = models.TextField(
        blank=True, 
        null=True,
        db_column='level',
        help_text='Teacher level (e.g., Junior, Senior, Expert)'
    )
    
    specialization = models.TextField(
        blank=True, 
        null=True,
        db_column='specialization',
        help_text='Teacher specialization (e.g., IELTS Speaking, TOEIC)'
    )
    
    campus = models.ForeignKey(
        'campus.Campus',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teachers',
        db_column='campus_id'
    )
    
    user_account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        db_column='user_account_id'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        db_table = 'teachers'
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['campus']),
            models.Index(fields=['user_account']),
        ]
    
    def __str__(self):
        return f"{self.user_account.fullname or self.user_account.username} - {self.specialization or 'Teacher'}"
    
    @property
    def display_name(self):
        """Tên hiển thị đầy đủ"""
        return self.user_account.fullname or self.user_account.username
    
    @property
    def email(self):
        """Email của teacher"""
        return self.user_account.email


class Manager(models.Model):
    """
    Model cho quản lý
    Mapping với bảng managers trong PostgreSQL
    """
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        db_column='id'
    )
    
    user_account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='manager_profile',
        db_column='user_account_id'
    )
    
    campus = models.ForeignKey(
        'campus.Campus',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managers',
        db_column='campus_id'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        db_table = 'managers'
        verbose_name = 'Manager'
        verbose_name_plural = 'Managers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['campus']),
            models.Index(fields=['user_account']),
        ]
    
    def __str__(self):
        campus_name = self.campus.name if self.campus else 'No Campus'
        return f"{self.user_account.fullname or self.user_account.username} - Manager of {campus_name}"
    
    @property
    def display_name(self):
        """Tên hiển thị đầy đủ"""
        return self.user_account.fullname or self.user_account.username
    
    @property
    def email(self):
        """Email của manager"""
        return self.user_account.email


class Student(models.Model):
    """
    Model cho học viên
    Mapping với bảng students trong PostgreSQL
    """
    
    class CommitmentStatus(models.TextChoices):
        """
        Enum cho commitment_status_enum trong PostgreSQL
        """
        NOT_COMMITTED = 'not_committed', 'Not Committed'
        COMMITTED = 'committed', 'Committed'
        CANCELED = 'canceled', 'Canceled'  # ← Sửa từ COMPLETED
    
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        db_column='id'
    )
    
    commitment_status = models.CharField(
        max_length=20,
        choices=CommitmentStatus.choices,
        default=CommitmentStatus.NOT_COMMITTED,
        db_column='commitment_status',
        help_text='Student commitment status'
    )
    
    user_account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        db_column='user_account_id'
    )
    
    target_score = models.IntegerField(
        null=True, 
        blank=True,
        db_column='target_score',
        help_text='Target IELTS/TOEIC score'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['commitment_status']),
            models.Index(fields=['user_account']),
        ]
    
    def __str__(self):
        return f"{self.user_account.fullname or self.user_account.username} - Student (Target: {self.target_score or 'N/A'})"
    
    @property
    def display_name(self):
        """Tên hiển thị đầy đủ"""
        return self.user_account.fullname or self.user_account.username
    
    @property
    def email(self):
        """Email của student"""
        return self.user_account.email
    
    @property
    def is_committed(self):
        """Kiểm tra student đã cam kết chưa"""
        return self.commitment_status == self.CommitmentStatus.COMMITTED
