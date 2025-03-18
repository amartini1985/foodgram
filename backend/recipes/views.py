from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from rest_framework.views import APIView

from recipes.models import Recipe

User = get_user_model()


class ShortLinkRedirectView(APIView):
    """Представление для получения короткой ссылки"""
    def get(self, request, short_code):
        recipe = get_object_or_404(Recipe, short_code=short_code)
        scheme = request.scheme
        host = request.get_host()
        return (redirect(f'{scheme}://{host}/recipes/{recipe.id}'))
