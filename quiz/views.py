import json
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, FloatField, Q, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from accounts.models import User
from .forms import SubjectForm, QuizForm, QuestionCreateForm
from .models import Subject, Quiz, Question, Choice, Attempt


def home_view(request):
    subjects_count = Subject.objects.count()
    quizzes_count = Quiz.objects.filter(is_active=True).count()
    students_count = User.objects.filter(role='student').count()

    leaderboard_students = User.objects.filter(role='student').annotate(
        completed_tests=Count(
            'attempts',
            filter=Q(attempts__is_completed=True),
            distinct=True
        ),
        avg_percentage=Coalesce(
            Avg('attempts__percentage', filter=Q(attempts__is_completed=True)),
            Value(0.0),
            output_field=FloatField()
        )
    ).order_by('-avg_percentage', '-completed_tests', 'username')

    leaderboard_students = list(leaderboard_students)
    top_students = leaderboard_students[:3]
    other_students = leaderboard_students[3:]

    return render(request, 'home.html', {
        'subjects_count': subjects_count,
        'quizzes_count': quizzes_count,
        'students_count': students_count,
        'top_students': top_students,
        'other_students': other_students,
    })


def teacher_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'teacher':
            messages.error(request, 'Bu bo‘lim faqat teacher uchun.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'student':
            messages.error(request, 'Bu bo‘lim faqat student uchun.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def paginate_queryset(request, queryset, per_page=8):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def finalize_attempt(attempt, answers=None):
    answers = answers or {}
    questions = attempt.quiz.questions.prefetch_related('choices').all()
    total = questions.count()
    score = 0

    for question in questions:
        selected_choice_id = answers.get(str(question.id))
        if selected_choice_id and question.choices.filter(id=selected_choice_id, is_correct=True).exists():
            score += 1

    submitted_at = timezone.now()
    used_seconds = max(0, int((submitted_at - attempt.started_at).total_seconds()))
    percentage = round((score / total) * 100, 2) if total else 0

    attempt.score = score
    attempt.total = total
    attempt.percentage = percentage
    attempt.used_seconds = used_seconds
    attempt.is_completed = True
    attempt.submitted_at = submitted_at
    attempt.save()
    return attempt


# =========================
# STUDENT
# =========================

@student_required
def student_subject_list_view(request):
    subjects = Subject.objects.annotate(total_quizzes=Count('quizzes')).order_by('-created_at')
    page_obj = paginate_queryset(request, subjects, 6)
    return render(request, 'quiz/student_subject_list.html', {'page_obj': page_obj})


@student_required
def student_quiz_list_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    quizzes = subject.quizzes.filter(is_active=True).order_by('-created_at')
    page_obj = paginate_queryset(request, quizzes, 6)
    return render(request, 'quiz/student_quiz_list.html', {
        'subject': subject,
        'page_obj': page_obj,
    })


@student_required
def start_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    attempt, created = Attempt.objects.get_or_create(student=request.user, quiz=quiz)

    if attempt.is_completed:
        messages.info(request, 'Siz bu testni oldin ishlab bo‘lgansiz.')
        return redirect('result_detail', attempt_id=attempt.id)

    return redirect('take_quiz', quiz_id=quiz.id)


@student_required
def take_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    attempt = get_object_or_404(Attempt, student=request.user, quiz=quiz)

    if attempt.is_completed:
        return redirect('result_detail', attempt_id=attempt.id)

    deadline = attempt.started_at + timedelta(minutes=quiz.duration_minutes)
    remaining_seconds = int((deadline - timezone.now()).total_seconds())

    if remaining_seconds <= 0:
        finalize_attempt(attempt, {})
        messages.warning(request, 'Vaqt tugadi.')
        return redirect('result_detail', attempt_id=attempt.id)

    questions = quiz.questions.prefetch_related('choices').all()
    return render(request, 'quiz/take_quiz.html', {
        'quiz': quiz,
        'questions': questions,
        'attempt': attempt,
        'remaining_seconds': remaining_seconds,
    })


@student_required
def submit_quiz_view(request, quiz_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Noto‘g‘ri so‘rov.'}, status=400)

    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)
    attempt = get_object_or_404(Attempt, student=request.user, quiz=quiz)

    if attempt.is_completed:
        return JsonResponse({
            'success': True,
            'redirect_url': f'/quiz/result/{attempt.id}/'
        })

    deadline = attempt.started_at + timedelta(minutes=quiz.duration_minutes)
    if timezone.now() > deadline:
        finalized = finalize_attempt(attempt, {})
        return JsonResponse({
            'success': True,
            'redirect_url': f'/quiz/result/{finalized.id}/'
        })

    try:
        data = json.loads(request.body)
        answers = data.get('answers', {})
    except Exception:
        answers = {}

    finalized = finalize_attempt(attempt, answers)
    return JsonResponse({
        'success': True,
        'redirect_url': f'/quiz/result/{finalized.id}/'
    })


@student_required
def result_detail_view(request, attempt_id):
    attempt = get_object_or_404(Attempt, id=attempt_id, student=request.user)
    return render(request, 'quiz/result_detail.html', {'attempt': attempt})


@student_required
def history_view(request):
    attempts = Attempt.objects.filter(student=request.user, is_completed=True).select_related('quiz', 'quiz__subject')
    page_obj = paginate_queryset(request, attempts, 8)
    return render(request, 'quiz/history.html', {'page_obj': page_obj})


@student_required
def certificate_view(request, attempt_id):
    attempt = get_object_or_404(Attempt, id=attempt_id, student=request.user, is_completed=True)
    if not attempt.passed:
        messages.error(request, 'Certificate olish uchun passing score yetmagan.')
        return redirect('result_detail', attempt_id=attempt.id)
    return render(request, 'quiz/certificate.html', {'attempt': attempt})



# =========================
# TEACHER
# =========================

@teacher_required
def teacher_subject_list_view(request):
    subjects = Subject.objects.filter(created_by=request.user)
    page_obj = paginate_queryset(request, subjects, 8)
    return render(request, 'quiz/teacher_subject_list.html', {'page_obj': page_obj})


@teacher_required
def teacher_subject_create_view(request):
    form = SubjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        subject = form.save(commit=False)
        subject.created_by = request.user
        subject.save()
        messages.success(request, 'Subject yaratildi.')
        return redirect('teacher_subject_list')
    return render(request, 'quiz/teacher_subject_form.html', {'form': form, 'title': 'Subject yaratish'})


@teacher_required
def teacher_subject_edit_view(request, pk):
    subject = get_object_or_404(Subject, pk=pk, created_by=request.user)
    form = SubjectForm(request.POST or None, instance=subject)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Subject yangilandi.')
        return redirect('teacher_subject_list')
    return render(request, 'quiz/teacher_subject_form.html', {'form': form, 'title': 'Subject tahrirlash'})


@teacher_required
def teacher_subject_delete_view(request, pk):
    subject = get_object_or_404(Subject, pk=pk, created_by=request.user)
    subject.delete()
    messages.success(request, 'Subject o‘chirildi.')
    return redirect('teacher_subject_list')


@teacher_required
def teacher_quiz_list_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id, created_by=request.user)
    quizzes = subject.quizzes.filter(created_by=request.user)
    page_obj = paginate_queryset(request, quizzes, 8)
    return render(request, 'quiz/teacher_quiz_list.html', {
        'subject': subject,
        'page_obj': page_obj,
    })


@teacher_required
def teacher_quiz_create_view(request):
    form = QuizForm(request.POST or None)
    form.fields['subject'].queryset = Subject.objects.filter(created_by=request.user)
    if request.method == 'POST' and form.is_valid():
        quiz = form.save(commit=False)
        quiz.created_by = request.user
        quiz.save()
        messages.success(request, 'Quiz yaratildi.')
        return redirect('teacher_quiz_list', subject_id=quiz.subject.id)
    return render(request, 'quiz/teacher_quiz_form.html', {'form': form, 'title': 'Quiz yaratish'})


@teacher_required
def teacher_quiz_edit_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    form = QuizForm(request.POST or None, instance=quiz)
    form.fields['subject'].queryset = Subject.objects.filter(created_by=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Quiz yangilandi.')
        return redirect('teacher_quiz_list', subject_id=quiz.subject.id)
    return render(request, 'quiz/teacher_quiz_form.html', {'form': form, 'title': 'Quiz tahrirlash'})


@teacher_required
def teacher_quiz_delete_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    subject_id = quiz.subject.id
    quiz.delete()
    messages.success(request, 'Quiz o‘chirildi.')
    return redirect('teacher_quiz_list', subject_id=subject_id)


@teacher_required
def teacher_quiz_analytics_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
    attempts = Attempt.objects.filter(quiz=quiz, is_completed=True).select_related('student')
    page_obj = paginate_queryset(request, attempts, 10)

    total_attempts = attempts.count()
    avg_score = attempts.aggregate(avg=Coalesce(Avg('percentage'), Value(0.0), output_field=FloatField()))['avg']
    passed_count = sum(1 for i in attempts if i.passed)

    return render(request, 'quiz/teacher_quiz_analytics.html', {
        'quiz': quiz,
        'page_obj': page_obj,
        'total_attempts': total_attempts,
        'avg_score': avg_score,
        'passed_count': passed_count,
    })


@teacher_required
def teacher_question_list_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
    questions = quiz.questions.prefetch_related('choices').all()
    page_obj = paginate_queryset(request, questions, 8)
    return render(request, 'quiz/teacher_question_list.html', {
        'quiz': quiz,
        'page_obj': page_obj,
    })


@teacher_required
def teacher_question_create_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
    form = QuestionCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        question = Question.objects.create(
            quiz=quiz,
            text=form.cleaned_data['text'],
            order=form.cleaned_data['order'],
        )

        correct_choice = form.cleaned_data['correct_choice']
        for index in range(1, 5):
            Choice.objects.create(
                question=question,
                text=form.cleaned_data[f'choice_{index}'],
                is_correct=(str(index) == str(correct_choice))
            )

        messages.success(request, 'Savol va variantlar yaratildi.')
        return redirect('teacher_question_list', quiz_id=quiz.id)

    return render(request, 'quiz/teacher_question_form.html', {
        'form': form,
        'quiz': quiz,
        'title': 'Savol yaratish',
    })


@teacher_required
def teacher_question_edit_view(request, pk):
    question = get_object_or_404(Question, pk=pk, quiz__created_by=request.user)
    choices = list(question.choices.all())

    initial = {
        'text': question.text,
        'order': question.order,
    }
    for idx, choice in enumerate(choices, start=1):
        initial[f'choice_{idx}'] = choice.text
        if choice.is_correct:
            initial['correct_choice'] = str(idx)

    form = QuestionCreateForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        question.text = form.cleaned_data['text']
        question.order = form.cleaned_data['order']
        question.save()

        question.choices.all().delete()
        correct_choice = form.cleaned_data['correct_choice']
        for index in range(1, 5):
            Choice.objects.create(
                question=question,
                text=form.cleaned_data[f'choice_{index}'],
                is_correct=(str(index) == str(correct_choice))
            )

        messages.success(request, 'Savol yangilandi.')
        return redirect('teacher_question_list', quiz_id=question.quiz.id)

    return render(request, 'quiz/teacher_question_form.html', {
        'form': form,
        'quiz': question.quiz,
        'title': 'Savol tahrirlash',
    })


@teacher_required
def teacher_question_delete_view(request, pk):
    question = get_object_or_404(Question, pk=pk, quiz__created_by=request.user)
    quiz_id = question.quiz.id
    question.delete()
    messages.success(request, 'Savol o‘chirildi.')
    return redirect('teacher_question_list', quiz_id=quiz_id)