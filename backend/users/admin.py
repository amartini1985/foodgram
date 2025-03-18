from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from users.models import Subscription

User = get_user_model()


@admin.register(User)
class UserAdmin(UserAdmin):
    """Настройки админки для модели ModifiedUser."""

    model = User
    admin.site.unregister(Group)
    list_display = (
        'username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')
    ordering = ('username',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'following'
    )
    search_fields = ('user',)
