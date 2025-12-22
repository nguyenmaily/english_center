from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
import uuid
from core.models import BaseModel


class Course(BaseModel):
    """
    Model cho khóa học
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(unique=True)
    level = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    total_sessions = models.IntegerField(default=0)
    min_entry_score = models.IntegerField(null=True, blank=True)
    min_exit_score = models.IntegerField(null=True, blank=True)
    fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    skill = models.ForeignKey(
        'courses.Skill',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        db_column='skill_id',
        help_text='Kỹ năng của khóa học (LR hoặc SW)'
    )
    
    class Meta:
        db_table = 'courses'
        managed = False
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
    
    def __str__(self):
        return f"{self.name} ({self.level or 'N/A'})"


class Skill(BaseModel):
    """
    Model cho kỹ năng (LR hoặc SW)
    1 Skill có thể thuộc nhiều Courses
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    # ❌ Đã xóa: course = models.ForeignKey(...)
    # ✅ Quan hệ ngược: course.skill với related_name='courses'
    
    class Meta:
        db_table = 'skills'
        managed = False
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'
    
    def __str__(self):
        return f"{self.name}"
    
    @property
    def skill_group(self):
        """
        Xác định skill_group (LR/SW) từ skill.name
        Dùng để map với StudentCertificate.skill_group
        """
        name_upper = self.name.upper()
        if 'LISTENING' in name_upper and 'READING' in name_upper:
            return 'LR'
        elif 'SPEAKING' in name_upper and 'WRITING' in name_upper:
            return 'SW'
        # Fallback: kiểm tra từ khóa đơn
        if 'LISTENING' in name_upper or 'READING' in name_upper:
            return 'LR'
        elif 'SPEAKING' in name_upper or 'WRITING' in name_upper:
            return 'SW'
        return None





