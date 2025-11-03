import uuid
from django.db import models


class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    due_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    invoice_status = models.CharField(max_length=32, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.CASCADE,
        related_name='enrollments',
        db_column='student_id'
    )
    class_field = models.ForeignKey(
        'classes.Class',
        on_delete=models.CASCADE,
        related_name='enrollments',
        db_column='class_id'
    )

    class Meta:
        db_table = 'enrollments'
        managed = False
        unique_together = ('student', 'class_field')

