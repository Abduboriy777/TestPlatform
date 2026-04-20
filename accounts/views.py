from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from .forms import RegisterForm, LoginForm, ProfileForm


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm

    def get_success_url(self):
        return '/accounts/dashboard/'


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('dashboard')

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'profile_user': request.user})


@login_required
def profile_edit_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('profile')
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')