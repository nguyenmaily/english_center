import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField

from core.models import BaseModel
from courses.models import Course


class Class(BaseModel):
    """
    Model cho lớp học
    """
    class Status(models.TextChoices):
        PLANNED = 'planned', 'Planned'
        ONGOING = 'ongoing', 'Ongoing'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    current_student_count = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.RESTRICT,
        related_name='classes',
        db_column='course_id'
    )
    weekday = ArrayField(
        models.SmallIntegerField(),
        default=list,
        blank=True,
        help_text='1=Monday, 2=Tuesday, ..., 7=Sunday'
    )
    time_slot = models.TextField(blank=True, null=True)
    teacher = models.ForeignKey(
        'users.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes',
        db_column='teacher_id'
    )
    campus = models.ForeignKey(
        'campus.Campus',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes',
        db_column='campus_id'
    )
    manager = models.ForeignKey(
        'users.Manager',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_classes',
        db_column='manager_id'
    )
    limit_slot = models.IntegerField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'classes'
        managed = False
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['course_id']),
            models.Index(fields=['teacher_id']),
            models.Index(fields=['campus_id']),
            models.Index(fields=['is_public']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.course.name}"
    
    @property
    def is_teacher_assigned(self):
        """Kiểm tra xem lớp đã có giáo viên chưa"""
        return self.teacher is not None
    
    @property
    def is_full(self):
        """Kiểm tra xem lớp đã đầy chưa"""
        if self.limit_slot is None:
            return False
        return self.current_student_count >= self.limit_slot
    
    @property
    def available_slots(self):
        """Số slot còn trống"""
        if self.limit_slot is None:
            return None
        return max(0, self.limit_slot - self.current_student_count)
    
    @property
    def enrollment_rate(self):
        """Tỷ lệ lấp đầy lớp học (%)"""
        if self.limit_slot is None or self.limit_slot == 0:
            return 0
        return round((self.current_student_count / self.limit_slot) * 100, 2)
    
    def get_weekday_display(self):
        """
        Trả về tên các ngày trong tuần
        """
        weekday_names = {
            1: 'Monday',
            2: 'Tuesday',
            3: 'Wednesday',
            4: 'Thursday',
            5: 'Friday',
            6: 'Saturday',
            7: 'Sunday'
        }
        return [weekday_names.get(day, str(day)) for day in self.weekday]