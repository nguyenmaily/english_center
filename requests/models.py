import uuid
from django.db import models


class LeaveRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_date = models.DateField(null=True, blank=True)
    session_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=32, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    student_id = models.UUIDField()
    class_id = models.UUIDField()

    class Meta:
        db_table = 'leave_requests'
        managed = False


class ReserveRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    student_id = models.UUIDField()
    class_id = models.UUIDField()

    class Meta:
        db_table = 'reserve_requests'
        managed = False
