from django.contrib.auth.models import AbstractUser
from django.db import models

from users.constants import (
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_USERNAME
)


class CustomUser(AbstractUser):
    """Модель пользователя (измененная)."""
    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        unique=True
    )
    username = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
        unique=True
    )
    first_name = models.CharField(max_length=MAX_LENGTH_USERNAME)
    last_name = models.CharField(max_length=MAX_LENGTH_USERNAME)
    avatar = models.ImageField(
        upload_to='users/',
        null=True,
        default=None
    )
    is_subscribed = models.BooleanField(default=False)

    class Meta:
        """Класс Meta."""
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']
