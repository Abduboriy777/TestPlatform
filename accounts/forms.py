from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
import re


# ========================
# BOOTSTRAP MIXIN
# ========================
class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            widget = field.widget

            if isinstance(widget, forms.Select):
                widget.attrs['class'] = 'form-select'

            elif isinstance(widget, forms.Textarea):
                widget.attrs['class'] = 'form-control'
                widget.attrs['rows'] = 4

            elif isinstance(widget, forms.DateInput):
                widget.attrs['class'] = 'form-control'
                widget.attrs['type'] = 'date'

            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs['class'] = 'form-control'

            else:
                widget.attrs['class'] = 'form-control'


# ========================
# REGISTER FORM
# ========================
class RegisterForm(BootstrapMixin, UserCreationForm):

    telegram_username = forms.CharField(
        required=False,
        help_text="@username formatda yozing"
    )

    telegram_id = forms.CharField(
        required=True,
        help_text="Telegram bot orqali olinadi (majburiy)"
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'role',
            'telegram_username',
            'telegram_id',
            'password1',
            'password2'
        ]

    def clean_telegram_username(self):
        tg = self.cleaned_data.get('telegram_username')

        if tg:
            if not re.match(r'^@[\w\d_]{4,}$', tg):
                raise forms.ValidationError("Telegram username noto‘g‘ri (@username)")

        return tg

    def clean_telegram_id(self):
        tg_id = self.cleaned_data.get('telegram_id')

        if not tg_id:
            raise forms.ValidationError("Telegram ID majburiy!")

        if not tg_id.isdigit():
            raise forms.ValidationError("Telegram ID faqat raqam bo‘lishi kerak")

        return tg_id


# ========================
# LOGIN FORM
# ========================
class LoginForm(BootstrapMixin, AuthenticationForm):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


# ========================
# PROFILE EDIT FORM
# ========================
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
            'telegram_username',
            'telegram_id',
            'instagram',
            'bio',
            'avatar',
        ]

    def clean_telegram_username(self):
        tg = self.cleaned_data.get('telegram_username')

        if tg:
            if not re.match(r'^@[\w\d_]{4,}$', tg):
                raise forms.ValidationError("Telegram username noto‘g‘ri")

        return tg

    def clean_telegram_id(self):
        tg_id = self.cleaned_data.get('telegram_id')

        if tg_id and not tg_id.isdigit():
            raise forms.ValidationError("Telegram ID faqat raqam bo‘lishi kerak")

        return tg_id