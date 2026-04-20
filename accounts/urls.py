from django.urls import path
from .views import (
    register_view,
    dashboard_view,
    logout_view,
    CustomLoginView,
    profile_view,
    profile_edit_view,
)

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', profile_edit_view, name='profile_edit'),
    path('logout/', logout_view, name='logout'),
]