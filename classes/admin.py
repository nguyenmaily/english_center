from django.contrib import admin
from .models import Class


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'status',
        'teacher_id',
        'start_date',
        'end_date',
    )
    search_fields = ('name',)
