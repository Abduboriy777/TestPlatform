from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs['class'] = 'form-select'
            elif isinstance(widget, forms.Textarea):
                widget.attrs['class'] = 'form-control'
                widget.attrs['rows'] = 4
            elif isinstance(widget, forms.DateInput):
                widget.attrs['class'] = 'form-control'
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs['class'] = 'form-control'
            else:
                widget.attrs['class'] = 'form-control'


class RegisterForm(BootstrapMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'role', 'password1', 'password2']


class LoginForm(BootstrapMixin, AuthenticationForm):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class ProfileForm(BootstrapMixin, forms.ModelForm):
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'birth_date',
            'telegram',
            'instagram',
            'bio',
            'avatar',
        ]