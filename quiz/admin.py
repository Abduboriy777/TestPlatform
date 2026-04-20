from django.contrib import admin
from .models import Subject, Quiz, Question, Choice, Attempt

# Savol ichida variantlarni (Choice) ko'rsatish uchun
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4  # Default holatda 4 ta bo'sh katak ko'rsatadi
    min_num = 2 # Kamida 2 ta variant bo'lishi shart

# Quiz ichida savollarni (Question) ko'rsatish uchun
class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True # Savolning o'ziga o'tish tugmasi

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'duration_minutes', 'pass_percentage', 'is_active', 'question_count')
    list_filter = ('subject', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]
    list_editable = ('is_active',) # Ro'yxatning o'zidan turib aktivlikni o'zgartirish

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'order')
    list_filter = ('quiz',)
    search_fields = ('text',)
    inlines = [ChoiceInline]

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'total', 'percentage', 'passed', 'submitted_at')
    list_filter = ('quiz', 'is_completed', 'submitted_at')
    search_fields = ('student__username', 'certificate_code')
    readonly_fields = ('started_at', 'submitted_at', 'certificate_code', 'percentage', 'score', 'total')
    
    # "passed" property-sini admin panelda chiroyli ko'rsatish
    def passed(self, obj):
        return obj.passed
    passed.boolean = True # To'g'ri/noto'g'ri belgisi bilan ko'rsatadi



@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    # Ro'yxatda ko'rinadigan ustunlar
    list_display = ('text', 'question', 'is_correct')
    
    # Savol nomi va variant matni bo'yicha qidiruv
    search_fields = ('text', 'question__text')
    
    # To'g'ri yoki noto'g'ri variantlar bo'yicha filter
    list_filter = ('is_correct', 'question__quiz')
    
    # Ro'yxatning o'zida to'g'riligini o'zgartirish imkoniyati
    list_editable = ('is_correct',)