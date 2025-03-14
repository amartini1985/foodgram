"""Фильтры представлений."""
from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe
import django_filters


class RecipeFilter(filters.FilterSet):
    author = filters.CharFilter(
        field_name='author__id',
        lookup_expr='icontains'
    )
    is_favorited = django_filters.CharFilter(
        method='filter_is_favorited')
    is_in_shopping_cart = django_filters.CharFilter(
        method='filter_is_in_shopping_cart')
    tags = django_filters.CharFilter(method='filter_tags')

    class Meta:
        model = Recipe
        fields = ['author', 'is_favorited', 'is_in_shopping_cart', 'tags']

    def filter_tags(self, queryset, name, values):
        tag_values = self.request.query_params.getlist('tags')
        queryset = queryset.filter(tags__slug__in=tag_values).distinct()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        if value in ('1', '0') and self.request.user.is_authenticated:
            favorited = bool(int(value))
            return (
                queryset.filter(favoriterecipe__user=self.request.user)
                if favorited
                else queryset.exclude(favoriterecipe__user=self.request.user)
            )
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value in ('1', '0') and self.request.user.is_authenticated:
            in_cart = bool(int(value))
            return (
                queryset.filter(shoppingcartrecipe__user=self.request.user)
                if in_cart
                else queryset.exclude(
                    shoppingcartrecipe__user=self.request.user)
            )
        return queryset


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='startswith'
    )

    class Meta:
        model = Ingredient
        fields = ['name']
