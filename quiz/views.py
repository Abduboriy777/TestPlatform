import json
import random
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, FloatField, Max, Q, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from .forms import FeedbackForm, QuestionCreateForm, QuizForm, SubjectForm
from .models import (
    Attempt,
    Choice,
    Feedback,
    Notification,
    Question,
    Quiz,
    StudentAnswer,
    Subject,
)


def paginate_queryset(request, queryset, per_page=8):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)


def teacher_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != "teacher":
            messages.error(request, "Bu bo‘lim faqat teacher uchun.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper


def student_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != "student":
            messages.error(request, "Bu bo‘lim faqat student uchun.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper


def create_notification(user, title, message):
    Notification.objects.create(user=user, title=title, message=message)


def finalize_attempt(attempt, answers=None):
    answers = answers or {}
    questions = list(attempt.quiz.questions.prefetch_related("choices").all())
    total = len(questions)
    score = 0

    attempt.student_answers.all().delete()

    for question in questions:
        selected_choice_id = answers.get(str(question.id))
        selected_choice = None
        is_correct = False

        if selected_choice_id:
            selected_choice = question.choices.filter(id=selected_choice_id).first()
            is_correct = bool(selected_choice and selected_choice.is_correct)
            if is_correct:
                score += 1

        StudentAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_choice=selected_choice,
            is_correct=is_correct,
        )

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

    create_notification(
        attempt.student,
        "Quiz finished",
        f'"{attempt.quiz.title}" test natijangiz tayyor: {attempt.percentage}%.',
    )
    return attempt


def home_view(request):
    subjects_count = Subject.objects.count()
    quizzes_count = Quiz.objects.filter(status="published").count()
    students_count = User.objects.filter(role="student").count()

    leaderboard_students = User.objects.filter(role="student").annotate(
        completed_tests=Count(
            "attempts",
            filter=Q(attempts__is_completed=True),
            distinct=True,
        ),
        avg_percentage=Coalesce(
            Avg("attempts__percentage", filter=Q(attempts__is_completed=True)),
            Value(0.0),
            output_field=FloatField(),
        ),
    ).order_by("-avg_percentage", "-completed_tests", "username")

    leaderboard_students = list(leaderboard_students)
    top_students = leaderboard_students[:3]
    other_students = leaderboard_students[3:]

    most_attempted_quizzes = (
        Quiz.objects.annotate(
            total_attempts=Count("attempts", filter=Q(attempts__is_completed=True)),
            unique_students=Count(
                "attempts__student",
                filter=Q(attempts__is_completed=True),
                distinct=True,
            ),
            best_result=Coalesce(
                Max("attempts__percentage", filter=Q(attempts__is_completed=True)),
                Value(0.0),
                output_field=FloatField(),
            ),
        )
        .filter(total_attempts__gt=0)
        .order_by("-total_attempts", "-unique_students", "title")[:6]
    )

    return render(
        request,
        "home.html",
        {
            "subjects_count": subjects_count,
            "quizzes_count": quizzes_count,
            "students_count": students_count,
            "top_students": top_students,
            "other_students": other_students,
            "most_attempted_quizzes": most_attempted_quizzes,
        },
    )


@student_required
def student_subject_list_view(request):
    q = request.GET.get("q", "").strip()

    subjects = Subject.objects.annotate(total_quizzes=Count("quizzes"))
    if q:
        subjects = subjects.filter(name__icontains=q)

    subjects = subjects.order_by("-created_at")
    page_obj = paginate_queryset(request, subjects, 6)

    return render(
        request,
        "quiz/student_subject_list.html",
        {
            "page_obj": page_obj,
            "q": q,
        },
    )


@student_required
def student_quiz_list_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)

    q = request.GET.get("q", "").strip()
    difficulty = request.GET.get("difficulty", "").strip()

    quizzes = subject.quizzes.filter(status="published").order_by("-created_at")

    if q:
        quizzes = quizzes.filter(title__icontains=q)
    if difficulty:
        quizzes = quizzes.filter(difficulty=difficulty)

    page_obj = paginate_queryset(request, quizzes, 6)

    best_attempts = {}
    quiz_ids = [quiz.id for quiz in page_obj]
    attempts = (
        Attempt.objects.filter(
            student=request.user,
            quiz_id__in=quiz_ids,
            is_completed=True,
        )
        .select_related("quiz")
        .order_by("quiz_id", "-score", "-percentage", "used_seconds", "-created_at")
    )

    for attempt in attempts:
        if attempt.quiz_id not in best_attempts:
            best_attempts[attempt.quiz_id] = attempt

    return render(
        request,
        "quiz/student_quiz_list.html",
        {
            "subject": subject,
            "page_obj": page_obj,
            "best_attempts": best_attempts,
            "q": q,
            "difficulty": difficulty,
        },
    )


@student_required
def start_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if quiz.status != 'published':
        messages.warning(request, "Bu test hozir active emas.")
        return redirect('result_detail', attempt_id=request.GET.get('attempt_id')) if request.GET.get('attempt_id') else redirect('student_subject_list')

    attempt = Attempt.objects.create(student=request.user, quiz=quiz)
    return redirect('take_quiz', quiz_id=quiz.id, attempt_id=attempt.id)


@student_required
def take_quiz_view(request, quiz_id, attempt_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, status="published")
    attempt = get_object_or_404(
        Attempt,
        id=attempt_id,
        student=request.user,
        quiz=quiz,
    )

    if attempt.is_completed:
        return redirect("result_detail", attempt_id=attempt.id)

    deadline = attempt.started_at + timedelta(minutes=quiz.duration_minutes)
    remaining_seconds = int((deadline - timezone.now()).total_seconds())

    if remaining_seconds <= 0:
        finalize_attempt(attempt, {})
        messages.warning(request, "Vaqt tugadi.")
        return redirect("result_detail", attempt_id=attempt.id)

    questions = list(quiz.questions.prefetch_related("choices").all())
    if quiz.randomize_questions:
        random.shuffle(questions)

    prepared_questions = []
    for question in questions:
        choices = list(question.choices.all())
        if quiz.randomize_choices:
            random.shuffle(choices)
        prepared_questions.append({"obj": question, "choices": choices})

    return render(
        request,
        "quiz/take_quiz.html",
        {
            "quiz": quiz,
            "questions": prepared_questions,
            "attempt": attempt,
            "remaining_seconds": remaining_seconds,
        },
    )


@student_required
def submit_quiz_view(request, quiz_id, attempt_id):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Noto‘g‘ri so‘rov."},
            status=400,
        )

    quiz = get_object_or_404(Quiz, id=quiz_id, status="published")
    attempt = get_object_or_404(
        Attempt,
        id=attempt_id,
        student=request.user,
        quiz=quiz,
    )

    if attempt.is_completed:
        return JsonResponse(
            {
                "success": True,
                "redirect_url": f"/quiz/result/{attempt.id}/",
            }
        )

    deadline = attempt.started_at + timedelta(minutes=quiz.duration_minutes)
    if timezone.now() > deadline:
        finalized = finalize_attempt(attempt, {})
        return JsonResponse(
            {
                "success": True,
                "redirect_url": f"/quiz/result/{finalized.id}/",
            }
        )

    try:
        data = json.loads(request.body)
        answers = data.get("answers", {})
    except Exception:
        answers = {}

    finalized = finalize_attempt(attempt, answers)
    return JsonResponse(
        {
            "success": True,
            "redirect_url": f"/quiz/result/{finalized.id}/",
        }
    )


@student_required
def result_detail_view(request, attempt_id):
    attempt = get_object_or_404(Attempt, id=attempt_id, student=request.user)

    best_attempt = Attempt.objects.filter(
        student=request.user,
        quiz=attempt.quiz,
        is_completed=True
    ).order_by('-score', '-percentage', 'used_seconds', '-created_at').first()

    is_best_attempt = bool(best_attempt and best_attempt.id == attempt.id)
    feedback_form = FeedbackForm()

    return render(request, 'quiz/result_detail.html', {
        'attempt': attempt,
        'best_attempt': best_attempt,
        'is_best_attempt': is_best_attempt,
        'feedback_form': feedback_form,
    })


@student_required
def review_view(request, attempt_id):
    attempt = get_object_or_404(
        Attempt,
        id=attempt_id,
        student=request.user,
        is_completed=True,
    )
    answers = attempt.student_answers.select_related(
        "question",
        "selected_choice",
    ).prefetch_related("question__choices")

    return render(
        request,
        "quiz/review.html",
        {
            "attempt": attempt,
            "answers": answers,
        },
    )


@student_required
def add_feedback_view(request, attempt_id):
    attempt = get_object_or_404(
        Attempt,
        id=attempt_id,
        student=request.user,
        is_completed=True,
    )
    form = FeedbackForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        feedback = form.save(commit=False)
        feedback.attempt = attempt
        feedback.student = request.user
        feedback.save()

        create_notification(
            attempt.quiz.created_by,
            "New feedback",
            f"{request.user.username} left feedback on {attempt.quiz.title}.",
        )
        messages.success(request, "Feedback yuborildi.")

    return redirect("result_detail", attempt_id=attempt.id)


@student_required
def history_view(request):
    attempts = (
        Attempt.objects.filter(
            student=request.user,
            is_completed=True,
        )
        .select_related("quiz", "quiz__subject")
        .order_by("-created_at")
    )

    best_attempt_ids = set()
    grouped = Attempt.objects.filter(
        student=request.user,
        is_completed=True,
    ).order_by("quiz_id", "-score", "-percentage", "used_seconds", "-created_at")

    seen = set()
    for item in grouped:
        if item.quiz_id not in seen:
            seen.add(item.quiz_id)
            best_attempt_ids.add(item.id)

    page_obj = paginate_queryset(request, attempts, 8)

    return render(
        request,
        "quiz/history.html",
        {
            "page_obj": page_obj,
            "best_attempt_ids": best_attempt_ids,
        },
    )


@student_required
def certificate_view(request, attempt_id):
    attempt = get_object_or_404(
        Attempt,
        id=attempt_id,
        student=request.user,
        is_completed=True,
    )
    if not attempt.passed:
        messages.error(request, "Certificate olish uchun passing score yetmagan.")
        return redirect("result_detail", attempt_id=attempt.id)

    return render(
        request,
        "quiz/certificate.html",
        {
            "attempt": attempt,
        },
    )


@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    request.user.notifications.filter(is_read=False).update(is_read=True)
    page_obj = paginate_queryset(request, notifications, 12)

    return render(
        request,
        "quiz/notifications.html",
        {
            "page_obj": page_obj,
        },
    )


@teacher_required
def teacher_subject_list_view(request):
    subjects = Subject.objects.filter(created_by=request.user).order_by("-created_at")
    page_obj = paginate_queryset(request, subjects, 8)

    return render(
        request,
        "quiz/teacher_subject_list.html",
        {
            "page_obj": page_obj,
        },
    )


@teacher_required
def teacher_subject_create_view(request):
    form = SubjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        subject = form.save(commit=False)
        subject.created_by = request.user
        subject.save()
        messages.success(request, "Subject yaratildi.")
        return redirect("teacher_subject_list")

    return render(
        request,
        "quiz/teacher_subject_form.html",
        {
            "form": form,
            "title": "Subject yaratish",
        },
    )


@teacher_required
def teacher_subject_edit_view(request, pk):
    subject = get_object_or_404(Subject, pk=pk, created_by=request.user)
    form = SubjectForm(request.POST or None, instance=subject)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Subject yangilandi.")
        return redirect("teacher_subject_list")

    return render(
        request,
        "quiz/teacher_subject_form.html",
        {
            "form": form,
            "title": "Subject tahrirlash",
        },
    )


@teacher_required
def teacher_subject_delete_view(request, pk):
    subject = get_object_or_404(Subject, pk=pk, created_by=request.user)
    subject.delete()
    messages.success(request, "Subject o‘chirildi.")
    return redirect("teacher_subject_list")


@teacher_required
def teacher_quiz_list_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id, created_by=request.user)

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    quizzes = subject.quizzes.filter(created_by=request.user)
    if q:
        quizzes = quizzes.filter(title__icontains=q)
    if status:
        quizzes = quizzes.filter(status=status)

    quizzes = quizzes.order_by("-created_at")
    page_obj = paginate_queryset(request, quizzes, 8)

    return render(
        request,
        "quiz/teacher_quiz_list.html",
        {
            "subject": subject,
            "page_obj": page_obj,
            "q": q,
            "status": status,
        },
    )


@teacher_required
def teacher_quiz_create_view(request):
    form = QuizForm(request.POST or None)
    form.fields["subject"].queryset = Subject.objects.filter(created_by=request.user)

    if request.method == "POST" and form.is_valid():
        quiz = form.save(commit=False)
        quiz.created_by = request.user
        quiz.save()
        messages.success(request, "Quiz yaratildi.")
        return redirect("teacher_quiz_list", subject_id=quiz.subject.id)

    return render(
        request,
        "quiz/teacher_quiz_form.html",
        {
            "form": form,
            "title": "Quiz yaratish",
        },
    )


@teacher_required
def teacher_quiz_edit_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    form = QuizForm(request.POST or None, instance=quiz)
    form.fields["subject"].queryset = Subject.objects.filter(created_by=request.user)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Quiz yangilandi.")
        return redirect("teacher_quiz_list", subject_id=quiz.subject.id)

    return render(
        request,
        "quiz/teacher_quiz_form.html",
        {
            "form": form,
            "title": "Quiz tahrirlash",
        },
    )


@teacher_required
def teacher_quiz_delete_view(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    subject_id = quiz.subject.id
    quiz.delete()
    messages.success(request, "Quiz o‘chirildi.")
    return redirect("teacher_quiz_list", subject_id=subject_id)


@teacher_required
def teacher_question_list_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
    questions = quiz.questions.prefetch_related("choices").all()
    page_obj = paginate_queryset(request, questions, 8)

    return render(
        request,
        "quiz/teacher_question_list.html",
        {
            "quiz": quiz,
            "page_obj": page_obj,
        },
    )


@teacher_required
def teacher_question_create_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
    form = QuestionCreateForm(request.POST or None, request.FILES or None)

    if request.method == "POST" and form.is_valid():
        question = Question.objects.create(
            quiz=quiz,
            text=form.cleaned_data["text"],
            image=form.cleaned_data.get("image"),
            explanation=form.cleaned_data.get("explanation"),
            order=form.cleaned_data["order"],
        )

        correct_choice = form.cleaned_data["correct_choice"]
        for index in range(1, 5):
            Choice.objects.create(
                question=question,
                text=form.cleaned_data[f"choice_{index}"],
                is_correct=(str(index) == str(correct_choice)),
            )

        create_notification(
            request.user,
            "Question created",
            f"New question added to {quiz.title}.",
        )
        messages.success(request, "Savol va variantlar yaratildi.")
        return redirect("teacher_question_list", quiz_id=quiz.id)

    return render(
        request,
        "quiz/teacher_question_form.html",
        {
            "form": form,
            "quiz": quiz,
            "title": "Savol yaratish",
        },
    )


@teacher_required
def teacher_question_edit_view(request, pk):
    question = get_object_or_404(Question, pk=pk, quiz__created_by=request.user)
    choices = list(question.choices.all())

    initial = {
        "text": question.text,
        "explanation": question.explanation,
        "order": question.order,
    }

    for idx, choice in enumerate(choices, start=1):
        initial[f"choice_{idx}"] = choice.text
        if choice.is_correct:
            initial["correct_choice"] = str(idx)

    form = QuestionCreateForm(
        request.POST or None,
        request.FILES or None,
        initial=initial,
    )

    if request.method == "POST" and form.is_valid():
        question.text = form.cleaned_data["text"]
        question.explanation = form.cleaned_data.get("explanation")
        if form.cleaned_data.get("image"):
            question.image = form.cleaned_data.get("image")
        question.order = form.cleaned_data["order"]
        question.save()

        question.choices.all().delete()
        correct_choice = form.cleaned_data["correct_choice"]

        for index in range(1, 5):
            Choice.objects.create(
                question=question,
                text=form.cleaned_data[f"choice_{index}"],
                is_correct=(str(index) == str(correct_choice)),
            )

        messages.success(request, "Savol yangilandi.")
        return redirect("teacher_question_list", quiz_id=question.quiz.id)

    return render(
        request,
        "quiz/teacher_question_form.html",
        {
            "form": form,
            "quiz": question.quiz,
            "title": "Savol tahrirlash",
        },
    )


@teacher_required
def teacher_question_delete_view(request, pk):
    question = get_object_or_404(Question, pk=pk, quiz__created_by=request.user)
    quiz_id = question.quiz.id
    question.delete()
    messages.success(request, "Savol o‘chirildi.")
    return redirect("teacher_question_list", quiz_id=quiz_id)


@teacher_required
def teacher_quiz_analytics_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
    attempts = (
        Attempt.objects.filter(quiz=quiz, is_completed=True)
        .select_related("student")
        .order_by("-created_at")
    )
    page_obj = paginate_queryset(request, attempts, 10)

    total_attempts = attempts.count()
    unique_students = attempts.values("student").distinct().count()
    avg_score = attempts.aggregate(
        avg=Coalesce(Avg("percentage"), Value(0.0), output_field=FloatField())
    )["avg"]
    passed_count = sum(1 for i in attempts if i.passed)

    student_attempt_stats = attempts.values(
        "student__id",
        "student__username",
        "student__first_name",
        "student__last_name",
    ).annotate(
        attempt_count=Count("id"),
        best_percentage=Max("percentage"),
        best_score=Max("score"),
    ).order_by("-attempt_count", "-best_percentage", "student__username")

    question_stats = []
    for question in quiz.questions.all():
        total_answers = StudentAnswer.objects.filter(
            attempt__quiz=quiz,
            question=question,
        ).count()
        wrong_answers = StudentAnswer.objects.filter(
            attempt__quiz=quiz,
            question=question,
            is_correct=False,
        ).count()
        wrong_percent = round((wrong_answers / total_answers) * 100, 1) if total_answers else 0

        question_stats.append(
            {
                "question": question,
                "wrong_percent": wrong_percent,
                "wrong_answers": wrong_answers,
                "total_answers": total_answers,
            }
        )

    question_stats = sorted(question_stats, key=lambda x: x["wrong_percent"], reverse=True)

    return render(
        request,
        "quiz/teacher_quiz_analytics.html",
        {
            "quiz": quiz,
            "page_obj": page_obj,
            "total_attempts": total_attempts,
            "unique_students": unique_students,
            "avg_score": avg_score,
            "passed_count": passed_count,
            "student_attempt_stats": student_attempt_stats,
            "question_stats": question_stats,
        },
    )