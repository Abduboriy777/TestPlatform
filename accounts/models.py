from django.contrib.auth.models import AbstractUser
from django.db import models
import re


class User(AbstractUser):
    ROLE_CHOICES = (
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student'
    )

    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True
    )

    birth_date = models.DateField(
        blank=True,
        null=True
    )

    # Telegram username (@username)
    telegram_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Masalan: @username"
    )

    # Telegram chat ID (BOT uchun MUHIM)
    telegram_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Telegram chat ID (bot ishlashi uchun kerak)"
    )

    instagram = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    bio = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.username

    def clean(self):
        # telegram username tekshirish
        if self.telegram_username:
            if not re.match(r'^@[\w\d_]{4,}$', self.telegram_username):
                raise ValueError("Telegram username noto‘g‘ri formatda (@username)")

    @property
    def has_telegram(self):
        return bool(self.telegram_id)