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
    
    class Meta:
        db_table = 'courses'
        managed = False
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
    
    def __str__(self):
        return f"{self.name} ({self.level or 'N/A'})"


class Skill(BaseModel):
    """
    Model cho kỹ năng trong khóa học
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='skills',
        db_column='course_id'
    )
    
    class Meta:
        db_table = 'skills'
        managed = False
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'
    
    def __str__(self):
        return f"{self.name} - {self.course.name}"





