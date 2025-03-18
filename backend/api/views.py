from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response

from api.base_views import TagIngredientBaseViewSet
from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingcartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSerializer,
    UserSubscribeRecipesCountSerializer
)
from api.utils import add_recipe_to, create_file, remove_recipe_from
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingcartRecipe,
    Tag
)
from users.models import Subscription

User = get_user_model()


class TagViewSet(TagIngredientBaseViewSet):
    """Представление для меток."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(TagIngredientBaseViewSet):
    """Представление для Ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для рецептов."""

    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = [IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        """Добавление рецепта в избранные."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            return add_recipe_to(user, recipe, FavoriteSerializer)
        else:
            return remove_recipe_from(user, recipe, FavoriteRecipe)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        """Добавление рецепта в список покупок."""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            return add_recipe_to(user, recipe, ShoppingcartSerializer)
        else:
            return remove_recipe_from(user, recipe, ShoppingcartRecipe)

    @action(detail=True, methods=['get'], url_path='get-link')
    def short_link(self, request, pk=None):
        """Получение короткой ссылки на рецептк."""
        recipe = get_object_or_404(Recipe, pk=pk)
        scheme = request.scheme
        host = request.get_host()
        data = recipe.short_code
        return Response({
            "short-link": f"{scheme}://{host}/s/{data}"},
            status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        """Возвращает TXT-файл со списком покупок."""
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcartrecipe__user=user).values(
                'ingredient__name', 'ingredient__measurement_unit').order_by(
                    'ingredient__name').annotate(total_amount=Sum('amount'))
        return create_file(ingredients)


class UserViewSet(DjoserUserViewSet):
    """Представление для управления пользователями."""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def me(self, request):
        """Получение данных текущего пользователя."""
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request):
        """Добавить или удалить аватар текущего пользователя."""
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"avatar": serializer.data['avatar']},
                            status=status.HTTP_200_OK)
        if user.avatar:
            user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            url_path='subscribe', permission_classes=[IsAuthenticated])
    def subscribe(self, request, **kwargs):
        """Подписка на пользователя."""
        pk = kwargs.get('id')
        user = request.user
        following = get_object_or_404(User, pk=pk)
        data = {'user': user.id, 'following': following.id}
        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data=data,
                context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=201)
        Subscription.objects.filter(user=user, following=following)
        deleted_count, _ = Subscription.objects.filter(
            user=user, following=following).delete()
        if deleted_count == 0:
            return Response({'detail': 'Вы не подписаны на пользователя'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'Вы отписались от пользователя'},
                        status=status.HTTP_204_NO_CONTENT)

    def get_recipes_limit(self, request):
        """Вспомогательная функция для сокращения длины строки"""
        return request.query_params.get('recipes_limit')

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Список подписок пользователя."""
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        result = []
        for subscription in subscriptions:
            foll = get_object_or_404(User, email=subscription.following.email)
            serializer = UserSubscribeRecipesCountSerializer(
                foll,
                context={'request': request,
                         'recipes_limit': self.get_recipes_limit(request)}
            )
            result.append(serializer.data)
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        return paginator.get_paginated_response(paginated_result)
