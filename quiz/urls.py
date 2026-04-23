from django.urls import path
from .views import (
    home_view,
    student_subject_list_view,
    student_quiz_list_view,
    start_quiz_view,
    take_quiz_view,
    submit_quiz_view,
    result_detail_view,
    review_view,
    history_view,
    certificate_view,
    notifications_view,
    add_feedback_view,
    teacher_subject_list_view,
    teacher_subject_create_view,
    teacher_subject_edit_view,
    teacher_subject_delete_view,
    teacher_quiz_list_view,
    teacher_quiz_create_view,
    teacher_quiz_edit_view,
    teacher_quiz_delete_view,
    teacher_question_list_view,
    teacher_question_create_view,
    teacher_question_edit_view,
    teacher_question_delete_view,
    teacher_quiz_analytics_view,
)

urlpatterns = [
    path('', home_view, name='home'),

    path('subjects/', student_subject_list_view, name='student_subject_list'),
    path('subjects/<int:subject_id>/quizzes/', student_quiz_list_view, name='student_quiz_list'),

    path('<int:quiz_id>/start/', start_quiz_view, name='start_quiz'),
    path('<int:quiz_id>/take/<int:attempt_id>/', take_quiz_view, name='take_quiz'),
    path('<int:quiz_id>/submit/<int:attempt_id>/', submit_quiz_view, name='submit_quiz'),

    path('result/<int:attempt_id>/', result_detail_view, name='result_detail'),
    path('review/<int:attempt_id>/', review_view, name='review'),
    path('history/', history_view, name='history'),
    path('certificate/<int:attempt_id>/', certificate_view, name='certificate'),
    path('notifications/', notifications_view, name='notifications'),
    path('feedback/<int:attempt_id>/', add_feedback_view, name='add_feedback'),

    path('teacher/subjects/', teacher_subject_list_view, name='teacher_subject_list'),
    path('teacher/subjects/create/', teacher_subject_create_view, name='teacher_subject_create'),
    path('teacher/subjects/<int:pk>/edit/', teacher_subject_edit_view, name='teacher_subject_edit'),
    path('teacher/subjects/<int:pk>/delete/', teacher_subject_delete_view, name='teacher_subject_delete'),

    path('teacher/subjects/<int:subject_id>/quizzes/', teacher_quiz_list_view, name='teacher_quiz_list'),
    path('teacher/quizzes/create/', teacher_quiz_create_view, name='teacher_quiz_create'),
    path('teacher/quizzes/<int:pk>/edit/', teacher_quiz_edit_view, name='teacher_quiz_edit'),
    path('teacher/quizzes/<int:pk>/delete/', teacher_quiz_delete_view, name='teacher_quiz_delete'),
    path('teacher/quizzes/<int:quiz_id>/analytics/', teacher_quiz_analytics_view, name='teacher_quiz_analytics'),

    path('teacher/quizzes/<int:quiz_id>/questions/', teacher_question_list_view, name='teacher_question_list'),
    path('teacher/quizzes/<int:quiz_id>/questions/create/', teacher_question_create_view, name='teacher_question_create'),
    path('teacher/questions/<int:pk>/edit/', teacher_question_edit_view, name='teacher_question_edit'),
    path('teacher/questions/<int:pk>/delete/', teacher_question_delete_view, name='teacher_question_delete'),
]