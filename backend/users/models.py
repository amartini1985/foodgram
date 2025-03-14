from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models


from users.constants import (
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_USERNAME,
    RETURN_TEXT_LEN
)


class Chef(AbstractUser):
    """Модель пользователя (измененная)."""

    USERNAME_FIELD = 'email'

    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        unique=True
    )
    username = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        validators=(UnicodeUsernameValidator(),)
    )
    first_name = models.CharField(max_length=MAX_LENGTH_USERNAME)
    last_name = models.CharField(max_length=MAX_LENGTH_USERNAME)
    avatar = models.ImageField(
        upload_to='users/',
        null=True,
        default=None
    )

    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        """Класс Meta."""
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.email[:RETURN_TEXT_LEN]


class Subscription(models.Model):
    user = models.ForeignKey(
        Chef,
        on_delete=models.CASCADE,
        related_name='following'
    )
    following = models.ForeignKey(
        Chef,
        on_delete=models.CASCADE,
        related_name='follower'
    )

    def clean(self):
        if self.user == self.following:
            raise ValidationError("Нельзя подписаться на самого себя.")

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='unique_user_following'
            ),
        )

    def __str__(self):
        return self.user[:RETURN_TEXT_LEN]
