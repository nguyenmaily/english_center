from django.contrib import admin
from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student',
        'class_field',
        'amount',
        'invoice_status',
        'due_date',
        'created_at',
    )
    search_fields = ('student__id', 'class_field__id')
