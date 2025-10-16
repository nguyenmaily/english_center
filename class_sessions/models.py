import uuid
from django.db import models


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    study_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    skill_id = models.UUIDField(null=True, blank=True)
    class_id = models.UUIDField()
    room_id = models.UUIDField(null=True, blank=True)
    teacher_id = models.UUIDField(null=True, blank=True)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = 'sessions'
        managed = False


class Attendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=16)
    student_id = models.UUIDField()
    session_id = models.UUIDField()

    class Meta:
        db_table = 'attendances'
        managed = False


class Assignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField()
    description = models.TextField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    session_id = models.UUIDField()
    status = models.CharField(max_length=32, default='draft')  # draft, published, closed
    url_file = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = 'assignments'
        managed = False


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=32, default='submitted')  # submitted, graded, resubmitted, late, missing
    content = models.TextField(null=True, blank=True)
    result = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    assignment_id = models.UUIDField()
    student_id = models.UUIDField()
    correct_count = models.IntegerField(null=True, blank=True)
    total_question = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'submissions'
        managed = False
        unique_together = ('assignment_id', 'student_id')



