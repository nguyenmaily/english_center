import uuid
from django.db import models


class QuestionGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    part = models.TextField()  # Part 1, 2, 3, etc.
    skill = models.TextField()  # Listening, Reading, etc.
    context = models.TextField(blank=True, null=True)
    audio_file = models.TextField(blank=True, null=True)
    image_file = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'question_groups'
        managed = False

    def __str__(self):
        return f"Question Group {self.id}"


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group_id = models.UUIDField(null=True, blank=True)
    text = models.TextField()
    option_a = models.TextField(null=True, blank=True)
    option_b = models.TextField(null=True, blank=True)
    option_c = models.TextField(null=True, blank=True)
    option_d = models.TextField(null=True, blank=True)
    correct_answer = models.TextField()
    difficulty = models.CharField(max_length=20, default='medium')  # easy, medium, hard
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'questions'
        managed = False

    def __str__(self):
        return f"Question {self.id}"


class ExamBlueprint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam_type = models.CharField(max_length=50)  # placement, midterm, final
    title = models.TextField()
    duration = models.IntegerField()  # in minutes
    total_questions = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'exam_blueprints'
        managed = False

    def __str__(self):
        return f"Blueprint {self.title}"


class ExamRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blueprint_id = models.UUIDField()
    part = models.TextField()
    skill = models.TextField()
    difficulty = models.CharField(max_length=20)  # easy, medium, hard
    num_questions = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'exam_rules'
        managed = False

    def __str__(self):
        return f"Rule {self.part} - {self.skill}"


class ExamInstance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blueprint_id = models.UUIDField(null=True, blank=True)
    title = models.TextField()
    status = models.CharField(max_length=20, default='draft')  # draft, published, archived
    generated_at = models.DateTimeField(auto_now_add=True)
    created_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'exam_instances'
        managed = False

    def __str__(self):
        return f"Exam {self.title}"


class ExamInstanceQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam_instance_id = models.UUIDField()
    question_id = models.UUIDField()
    order_number = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'exam_instance_questions'
        managed = False
        unique_together = ('exam_instance_id', 'question_id')

    def __str__(self):
        return f"Exam Question {self.id}"


class ExamResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam_instance_id = models.UUIDField()
    student_id = models.UUIDField()
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='in_progress')  # in_progress, completed, graded
    teacher_comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'exam_results'
        managed = False
        unique_together = ('exam_instance_id', 'student_id')

    def __str__(self):
        return f"Result {self.id} - Score: {self.score}"


class ExamAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    result_id = models.UUIDField()
    question_id = models.UUIDField()
    selected_answer = models.TextField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'exam_answers'
        managed = False

    def __str__(self):
        return f"Answer {self.id}"


class StudentProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_id = models.UUIDField()
    placement_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    midterm_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    final_status = models.CharField(max_length=20, null=True, blank=True)  # pass, fail, retake_required, certified
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_progress'
        managed = False
        unique_together = ('student_id',)

    def __str__(self):
        return f"Progress {self.student_id} - {self.final_status}"

