from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import Recipe

User = get_user_model()


class ShortLinkRedirectView(APIView):
    """Представление для получения короткой ссылки"""
    def get(self, request, short_code):
        try:
            recipe = Recipe.objects.get(short_code=short_code)
        except Recipe.DoesNotExist:
            return Response({"detail": "Рецепт не найден"},
                            status=status.HTTP_404_NOT_FOUND)
        scheme = request.scheme
        host = request.get_host()
        return (redirect(f'{scheme}://{host}/recipes/{recipe.id}'))
