from django.contrib import admin
from .models import Session, Attendance, Assignment, Submission


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'study_date',
        'start_time',
        'end_time',
        'class_id',
        'teacher_id',
    )
    search_fields = ('class_id', 'teacher_id')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student_id',
        'session_id',
        'status',
    )
    search_fields = ('student_id',)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'session_id',
        'due_date',
    )
    search_fields = ('title',)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student_id',
        'assignment_id',
        'status',
        'result',
        'submitted_at',
    )
    search_fields = ('student_id',)
