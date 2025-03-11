from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Настройки админки для модели ModifiedUser."""

    model = CustomUser
    list_display = (
        'username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')
    ordering = ('username',)
