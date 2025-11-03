from django.contrib import admin
from .models import Session


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """
    Admin cho Session (Buổi học)
    """
    list_display = (
        'id',
        'study_date',
        'start_time',
        'end_time',
        'class_session',
        'teacher',
        'room',
        'skill',
        'is_checked_in',
        'is_checked_out',
    )
    list_filter = ('study_date', 'teacher', 'room')
    search_fields = ('class_session__name', 'teacher__user_account__fullname')
    ordering = ('-study_date', 'start_time')
    date_hierarchy = 'study_date'
    
    readonly_fields = ('id', 'created_at', 'updated_at', 'duration', 'is_checked_in', 'is_checked_out')
    
    fieldsets = (
        ('Thông tin buổi học', {
            'fields': ('id', 'study_date', 'start_time', 'end_time', 'duration')
        }),
        ('Liên kết', {
            'fields': ('class_session', 'teacher', 'room', 'skill')
        }),
        ('Check-in/Check-out', {
            'fields': ('check_in', 'check_out', 'is_checked_in', 'is_checked_out')
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_checked_in(self, obj):
        """Hiển thị trạng thái check-in"""
        return '✓' if obj.is_checked_in else '✗'
    is_checked_in.short_description = 'Đã check-in'
    is_checked_in.boolean = True
    
    def is_checked_out(self, obj):
        """Hiển thị trạng thái check-out"""
        return '✓' if obj.is_checked_out else '✗'
    is_checked_out.short_description = 'Đã check-out'
    is_checked_out.boolean = True
