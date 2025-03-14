from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.views import APIView

from api.base_views import TagIngredientBaseViewSet
from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingcartRecipe,
    Tag
)
from api.serializers import (
    AvatarSerializer,
    CustomUserCreateSerializer,
    EmailAuthTokenSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingcartSerializer,
    TagSerializer,
    UserSerializer,
    UserSubscribeWithRecipesCountSerializer
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

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_permissions(self):
        if self.action in ['partial_update', 'destroy']:
            permission_classes = [IsAuthorOrReadOnly]
        else:

            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        filter_set = RecipeFilter(
            self.request.GET, queryset=queryset, request=self.request)
        return filter_set.qs.distinct()

    def all_unique(self, data):
        """Проверяет, все ли элементы в последовательности уникальные."""
        return len(data) == len(set(data))

    def all_unique_dicts(self, items):
        """Проверяет, все ли элементы в словаре уникальные."""
        seen = set()
        for item in items:
            frozen_item = tuple(sorted(item.items()))
            if frozen_item in seen:
                return False
            seen.add(frozen_item)
        return True

    def create(self, request, *args, **kwargs):
        """ Добавление рецепта """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        tags_data = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop("ingredients", [])
        if not self.all_unique(tags_data):
            return Response({'error': 'Одинаковые метки недопустимы'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not self.all_unique_dicts(ingredients_data):
            return Response({'error': 'Одинаковые ингредиенты недопустимы'},
                            status=status.HTTP_400_BAD_REQUEST)
        recipe = serializer.save(author=self.request.user)
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            if not Ingredient.objects.filter(
                id=ingredient_data['id']
            ).exists():
                return Response({'error': 'Ингредиент не найден'},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                ingredient = Ingredient.objects.get(
                    id=ingredient_data['id']
                )
                RecipeIngredient.objects.update_or_create(
                    recipe=recipe,
                    ingredient=ingredient,
                    defaults={'amount': ingredient_data['amount']}
                )
        return Response(self.get_serializer(recipe).data,
                        status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """ Частичное обновление рецепта """
        instance = self.get_object()
        serializer = self.get_serializer(instance,
                                         data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        tags_data = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)
        if tags_data is None or ingredients_data is None:
            return Response({'error': 'Ингредиент или метки не заданы'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not self.all_unique(tags_data):
            return Response({'error': 'Одинаковые метки недопустимы'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not self.all_unique_dicts(ingredients_data):
            return Response({'error': 'Одинаковые ингредиенты недопустимы'},
                            status=status.HTTP_400_BAD_REQUEST)
        updated_recipe = serializer.save()
        updated_recipe.tags.set(tags_data)
        updated_recipe.ingredients.set([])
        for ingredient_data in ingredients_data:
            if not Ingredient.objects.filter(
                id=ingredient_data['id']
            ).exists():
                return Response({'error': 'Ингредиент не найден'},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                ingredient = Ingredient.objects.get(
                    id=ingredient_data['id'])
                RecipeIngredient.objects.update_or_create(
                    recipe=updated_recipe,
                    ingredient=ingredient,
                    defaults={'amount': ingredient_data['amount']}
                )
        return Response(self.get_serializer(updated_recipe).data,
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        """Добавление рецепта в избранные"""
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {'user': user.username, 'recipe': recipe.id}
        if request.method == 'POST':
            serializer = FavoriteSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        fav_recipe = FavoriteRecipe.objects.filter(user=user, recipe=recipe)
        if not fav_recipe.exists():
            return Response({'detail': 'Рецепт не найден в избранном'},
                            status=status.HTTP_400_BAD_REQUEST)
        fav_recipe.delete()
        return Response({'detail': 'Рецепт удален из избранного'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        """Добавление рецпта в список покупок"""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        data = {'user': user.username, 'recipe': recipe.id}
        if request.method == 'POST':
            serializer = ShoppingcartSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        shop_cart = ShoppingcartRecipe.objects.filter(user=user, recipe=recipe)
        if not shop_cart.exists():
            return Response({'detail': 'Рецепт не найден в корзине'},
                            status=status.HTTP_400_BAD_REQUEST)
        shop_cart.delete()
        return Response({'detail': 'Рецепт удален из корзины'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='get-link')
    def short_link(self, request, pk=None):
        """ Получение короткой ссылки на рецептк."""
        recipe = get_object_or_404(Recipe, pk=pk)
        scheme = request.scheme
        host = request.get_host()
        data = recipe.short_code
        return Response({
            "short-link": f"{scheme}://{host}/s/{data}"},
            status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        """ Возвращает TXT-файл со списком покупок. """
        user = request.user
        recipes = self.get_queryset().filter(shoppingcartrecipe__user=user)
        total_ingredients = {}
        for recipe in recipes:
            ingredients = recipe.recipeingredient_set.all()
            for ingredient in ingredients:
                ingredient_name = f'{ingredient.ingredient.name},' \
                    f'({ingredient.ingredient.measurement_unit})'
                if total_ingredients.get(ingredient_name) is None:
                    total_ingredients[ingredient_name] = ingredient.amount
                else:
                    total_ingredients[ingredient_name] += ingredient.amount
        content = ''
        for ingredient_name, amount in total_ingredients.items():
            content += f"- {ingredient_name}: {amount}\n"
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response


class ShortLinkRedirectView(APIView):
    """Представление для получения короткой ссылки"""
    def get(self, request, short_code):
        recipe = get_object_or_404(Recipe, short_code=short_code)
        scheme = request.scheme
        host = request.get_host()
        return (redirect(f'{scheme}://{host}/recipes/{recipe.id}'))


class ObtainAuthTokenView(APIView):
    """Представление для получения token."""
    serializer_class = EmailAuthTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Представление для logout."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({'message': 'Вы успешно вышли'},
                            status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserViewSet(viewsets.ModelViewSet):
    """Представление для управления пользователями."""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        """Регистрация пользователя."""
        serializer = CustomUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        """Смена пароля текущего пользователя."""
        user = request.user
        old_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if not user.check_password(old_password):
            return Response({"detail": "Неверный старый пароль."},
                            status=status.HTTP_400_BAD_REQUEST)
        user.password = make_password(new_password)
        user.save()
        return Response({"detail": "Пароль успешно обновлен."},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            url_path='subscribe', permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Подписка на пользователя."""
        following = self.get_object()
        recipes_limit = int(request.query_params.get('recipes_limit', 10))
        user = request.user
        if user == following:
            return Response(
                {'detail': 'Невозможно подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'POST':
            if Subscription.objects.filter(user=user,
                                           following=following).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST)
            Subscription.objects.create(user=user, following=following)
            foll = get_object_or_404(User, email=following.email)
            foll.is_subscribed = True
            serializer = UserSubscribeWithRecipesCountSerializer(
                foll,
                context={
                    'request': request,
                    'recipes_limit': recipes_limit
                }
            )
            return Response(serializer.data, status=201)
        subscribe = Subscription.objects.filter(
            user=user,
            following=following
        )
        if not subscribe.exists():
            return Response({'detail': 'Вы не подписаны на пользователя'},
                            status=status.HTTP_400_BAD_REQUEST)

        subscribe.delete()
        return Response({'detail': 'Вы отписались от пользователя'},
                        status=status.HTTP_204_NO_CONTENT)

    def get_recipes_limit(self, request):
        """Вспомогательная функция для сокращения длины строки"""
        return request.query_params.get('recipes_limit')

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Список подписок."""
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        result = []
        for subscription in subscriptions:
            foll = get_object_or_404(User, email=subscription.following.email)
            serializer = UserSubscribeWithRecipesCountSerializer(
                foll,
                context={'request': request,
                         'recipes_limit': self.get_recipes_limit(request)}
            )
            result.append(serializer.data)
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        return paginator.get_paginated_response(paginated_result)
