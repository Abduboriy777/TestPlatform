import random
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class Subject(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_subjects'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Quiz(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=10)
    pass_percentage = models.PositiveIntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    randomize_questions = models.BooleanField(default=False)
    randomize_choices = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_quizzes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def is_active(self):
        return self.status == 'published'


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500)
    image = models.ImageField(upload_to='question_images/', blank=True, null=True)
    explanation = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class Attempt(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    used_seconds = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(blank=True, null=True)
    certificate_code = models.CharField(max_length=32, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}"

    @property
    def passed(self):
        return float(self.percentage) >= self.quiz.pass_percentage

    @property
    def used_minutes_text(self):
        minutes = self.used_seconds // 60
        seconds = self.used_seconds % 60
        return f"{minutes} min {seconds} sec"

    def save(self, *args, **kwargs):
        if not self.certificate_code:
            self.certificate_code = uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)

class StudentAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='student_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, blank=True, null=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('attempt', 'question')


class Feedback(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='feedbacks')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
    

