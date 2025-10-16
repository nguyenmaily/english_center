# users/models.py
from django.db import models
from django.conf import settings  # ← Import settings
from core.models import BaseModel
from campus.models import Campus
import uuid


class Teacher(BaseModel):
    """
    Model cho giảng viên
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    level = models.TextField(blank=True, null=True)
    specialization = models.TextField(blank=True, null=True)
    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teachers'
    )
    user_account = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # ← Dùng settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )
    
    class Meta:
        db_table = 'teachers'
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_account.fullname or self.user_account.username} - {self.specialization or 'Teacher'}"


class Manager(BaseModel):
    """
    Model cho quản lý
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_account = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # ← Dùng settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='manager_profile'
    )
    campus = models.ForeignKey(
        Campus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managers'
    )
    
    class Meta:
        db_table = 'managers'
        verbose_name = 'Manager'
        verbose_name_plural = 'Managers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_account.fullname or self.user_account.username} - Manager of {self.campus.name if self.campus else 'No Campus'}"


class Student(BaseModel):
    """
    Model cho học viên
    """
    class CommitmentStatus(models.TextChoices):
        NOT_COMMITTED = 'not_committed', 'Not Committed'
        COMMITTED = 'committed', 'Committed'
        COMPLETED = 'completed', 'Completed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commitment_status = models.CharField(
        max_length=20,
        choices=CommitmentStatus.choices,
        default=CommitmentStatus.NOT_COMMITTED
    )
    user_account = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # ← Dùng settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    target_score = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_account.fullname or self.user_account.username} - Student (Target: {self.target_score or 'N/A'})"
