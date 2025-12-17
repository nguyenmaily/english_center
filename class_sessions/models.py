import uuid
from django.db import models

from classes.models import Class
from core.models import BaseModel


class Session(BaseModel):
    """
    Model cho buổi học trong lớp
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    study_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    skill = models.ForeignKey(
        'courses.Skill',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        db_column='skill_id'
    )
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
    teacher = models.ForeignKey(
        'users.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions',
        db_column='teacher_id'
    )
    check_in = models.TimeField(blank=True, null=True)
    check_out = models.TimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'sessions'
        managed = False
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'
        ordering = ['study_date', 'start_time']
    
    def __str__(self):
        return f"Session {self.study_date} - {self.class_session.name if self.class_session else 'No Class'}"
    
    @property
    def duration(self):
        """Tính thời lượng buổi học (phút)"""
        if self.start_time and self.end_time:
            from datetime import datetime, timedelta
            start = datetime.combine(datetime.today(), self.start_time)
            end = datetime.combine(datetime.today(), self.end_time)
            duration = end - start
            return int(duration.total_seconds() / 60)
        return None
    
    @property
    def is_checked_in(self):
        """Kiểm tra đã check-in chưa"""
        return self.check_in is not None
    
    @property
    def is_checked_out(self):
        """Kiểm tra đã check-out chưa"""
        return self.check_out is not None


class Attendance(models.Model):
    """
    Model cho điểm danh học sinh trong buổi học
    """
    # Các trạng thái điểm danh
    STATUS_PRESENT = 'present'  # Có mặt
    STATUS_ABSENT = 'absent'    # Vắng mặt
    STATUS_LATE = 'late'        # Đi muộn
    STATUS_EXCUSED = 'excused'  # Vắng có phép
    
    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_LATE, 'Late'),
        (STATUS_EXCUSED, 'Excused'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=16)
    student_id = models.UUIDField()
    session_id = models.UUIDField()

    class Meta:
        db_table = 'attendances'
        managed = False
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'
    
    def __str__(self):
        return f"Attendance {self.id} - {self.status}"