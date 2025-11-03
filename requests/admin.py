from django.contrib import admin
from .models import ReserveRequest, LeaveRequest


@admin.register(ReserveRequest)
class ReserveRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student_id',
        'class_id',
        'start_date',
        'end_date',
        'status',
        'created_at',
    )
    search_fields = ('student_id', 'class_id')


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student_id',
        'class_id',
        'session_date',
        'session_time',
        'status',
        'created_at',
    )
    search_fields = ('student_id', 'class_id')
