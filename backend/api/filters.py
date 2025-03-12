"""Фильтры представлений."""
from django_filters import rest_framework as filters
from recipes.models import Recipe


class RecipeFilter(filters.FilterSet):
    author = filters.CharFilter(
        field_name='author__id',
        lookup_expr='icontains'
    )

    class Meta:
        model = Recipe
        fields = ['author']
