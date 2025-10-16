
from django.db import models
import uuid
from core.models import BaseModel


class Assignment(BaseModel):
    """
    Model cho bài tập
    """
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        CLOSED = 'closed', 'Closed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField()
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    url_file = models.CharField(max_length=500, blank=True, null=True)
    session = models.ForeignKey(
        'courses.Session',  # Đảm bảo đúng tên app và model
        on_delete=models.CASCADE,
        related_name='assignments',
        db_column='session_id'
    )
    
    class Meta:
        db_table = 'assignments'
        managed = False
        verbose_name = 'Assignment'
        verbose_name_plural = 'Assignments'
    
    def __str__(self):
        return f"{self.title} - {self.session}"


class AnswerKey(BaseModel):
    """
    Model cho đáp án đúng của bài tập
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_number = models.IntegerField()
    correct_option = models.CharField(max_length=10)
    description = models.TextField(blank=True, null=True)
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='answer_keys',
        db_column='assignment_id'
    )
    
    class Meta:
        db_table = 'answer_keys'
        managed = False
        verbose_name = 'Answer Key'
        verbose_name_plural = 'Answer Keys'
        ordering = ['question_number']
    
    def __str__(self):
        return f"Question {self.question_number} - {self.assignment.title}"


class Submission(BaseModel):
    """
    Model cho bài nộp của học viên
    """
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        GRADED = 'graded', 'Graded'
        RESUBMIT_REQUIRED = 'resubmit_required', 'Resubmit Required'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED
    )
    content = models.TextField(blank=True, null=True)
    result = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    correct_count = models.IntegerField(blank=True, null=True)
    total_question = models.IntegerField(blank=True, null=True)
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions',
        db_column='assignment_id'
    )
    student = models.ForeignKey(
        'users.Student',
        on_delete=models.CASCADE,
        related_name='submissions',
        db_column='student_id'
    )
    
    class Meta:
        db_table = 'submissions'
        managed = False
        verbose_name = 'Submission'
        verbose_name_plural = 'Submissions'
        unique_together = [['assignment', 'student']]
    
    def __str__(self):
        return f"{self.student} - {self.assignment.title}"
    
    @property
    def is_graded(self):
        return self.status == self.Status.GRADED
    
    @property
    def needs_resubmit(self):
        return self.status == self.Status.RESUBMIT_REQUIRED


class StudentAnswer(models.Model):
    """
    Model cho câu trả lời của học viên
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_number = models.IntegerField()
    selected_option = models.IntegerField(blank=True, null=True)
    is_correct = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='student_answers',
        db_column='submission_id'
    )
    
    class Meta:
        db_table = 'student_answers'
        managed = False
        verbose_name = 'Student Answer'
        verbose_name_plural = 'Student Answers'
        ordering = ['question_number']
    
    def __str__(self):
        return f"Q{self.question_number} - {self.submission}"