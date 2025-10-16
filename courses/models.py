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
    
    def __str__(self):
        return f"{self.name} - {self.course.name}"
    
    @property
    def is_teacher_assigned(self):
        return self.teacher is not None
    
    @property
    def is_full(self):
        if self.limit_slot is None:
            return False
        return self.current_student_count >= self.limit_slot
    
    @property
    def available_slots(self):
        if self.limit_slot is None:
            return None
        return max(0, self.limit_slot - self.current_student_count)
    
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



class Session(BaseModel):
    """
    Model cho buổi học trong lớp
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    session_number = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    session_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    class_session = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='sessions',
        db_column='class_id'
    )
    room = models.ForeignKey(
        'campus.Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        db_column='room_id'
    )
    
    class Meta:
        db_table = 'sessions'
        managed = False
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'
        ordering = ['session_number']
    
    def __str__(self):
        return f"{self.name} - {self.class_session.name}"