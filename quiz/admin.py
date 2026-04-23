from django.contrib import admin
from .models import Subject, Quiz, Question, Choice, Attempt, StudentAnswer, Notification, Feedback


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_by', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title',
        'subject',
        'difficulty',
        'status',
        'duration_minutes',
        'pass_percentage',
        'created_by',
        'created_at',
    ]
    search_fields = ['title', 'subject__name']
    list_filter = ['subject', 'difficulty', 'status', 'created_at']
    list_editable = ['status', 'difficulty']
    ordering = ['-created_at']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'quiz', 'order', 'text']
    search_fields = ['text', 'quiz__title']
    list_filter = ['quiz']


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'question', 'text', 'is_correct']
    search_fields = ['text', 'question__text']
    list_filter = ['is_correct']


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'student',
        'quiz',
        'score',
        'total',
        'percentage',
        'used_seconds',
        'is_completed',
        'created_at',
    ]
    search_fields = ['student__username', 'quiz__title']
    list_filter = ['is_completed', 'quiz', 'created_at']


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['id', 'attempt', 'question', 'selected_choice', 'is_correct']
    list_filter = ['is_correct']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['title', 'user__username']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'attempt', 'created_at']
    search_fields = ['student__username', 'attempt__quiz__title']
    list_filter = ['created_at']