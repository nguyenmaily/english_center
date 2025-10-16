import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField


class Class(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    current_student_count = models.IntegerField(default=0)
    status = models.CharField(max_length=32, default='planned')
    course_id = models.UUIDField()
    weekday = ArrayField(models.SmallIntegerField(), default=list)  # 1=Mon .. 7=Sun
    time_slot = models.TextField(null=True, blank=True)
    teacher_id = models.UUIDField(null=True, blank=True)
    campus_id = models.UUIDField(null=True, blank=True)
    manager_id = models.UUIDField(null=True, blank=True)
    limit_slot = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)

    # Note: start_time and end_time are not in the database schema
    # They are handled in the time_slot field as text

    class Meta:
        db_table = 'classes'
        managed = False

    def __str__(self):
        return f"{self.name}"
