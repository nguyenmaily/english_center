from django.contrib import admin
from .models import (
    Question, QuestionGroup, ExamBlueprint, ExamRule,
    ExamInstance, ExamResult, StudentProgress
)


@admin.register(QuestionGroup)
class QuestionGroupAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'context',
        'created_at',
    )
    search_fields = ('context',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'text',
        'difficulty',
        'group_id',
        'created_at',
    )
    search_fields = ('text',)


@admin.register(ExamBlueprint)
class ExamBlueprintAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'duration',
        'total_questions',
        'exam_type',
        'created_at',
    )
    search_fields = ('title',)


@admin.register(ExamRule)
class ExamRuleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'blueprint_id',
        'part',
        'skill',
        'difficulty',
        'num_questions',
    )
    search_fields = ('part', 'skill', 'difficulty')


@admin.register(ExamInstance)
class ExamInstanceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'blueprint_id',
        'status',
        'generated_at',
    )
    search_fields = ('title',)


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student_id',
        'exam_instance_id',
        'score',
        'status',
        'submitted_at',
    )
    search_fields = ('student_id',)


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'student_id',
        'placement_score',
        'midterm_score',
        'final_score',
        'final_status',
        'updated_at',
    )
    search_fields = ('student_id',)

