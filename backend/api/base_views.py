"""Базовые представления для проекта API"""
from rest_framework import filters, mixins, viewsets


class TagIngredientBaseViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """Базовое представление для меток и ингредиентов """

    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    pagination_class = None
