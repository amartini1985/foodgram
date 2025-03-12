from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.views import APIView

from api.base_views import TagIngredientBaseViewSet
from api.filters import RecipeFilter
from api.pagination import RecipePagination
from api.permissions import IsAuthorOrReadOnly
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingcartRecipe,
    ShortLink,
    Subscription,
    Tag
)
from api.serializers import (
    AvatarSerializer,
    CustomUserCreateSerializer,
    EmailAuthTokenSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShortLinkSerializer,
    TagSerializer,
    UserSerializer,
    UserSubscribeSerializers,
    UserSubscribeWithRecipesCountSerializer
)
from django.db.models import Q

User = get_user_model()


class TagViewSet(TagIngredientBaseViewSet):
    """Представление для меток."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(TagIngredientBaseViewSet):
    """Представление для Ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Представление для рецептов."""

    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = RecipePagination

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_permissions(self):
        if self.action == 'partial_update':
            permission_classes = [IsAuthorOrReadOnly]
        else:

            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        is_favorited = self.request.query_params.get(
            'is_favorited', None)
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart', None)
        tags = self.request.query_params.getlist(
            'tags', None)
        if is_favorited == '1':
            queryset = queryset.filter(favorites__user=user)
        if is_in_shopping_cart == '1':
            queryset = queryset.filter(shopping__user=user)
        if tags is not None:
            conditions = [Q(tags__slug=tag) for tag in tags]
        # Объединяем условия OR
            query = conditions.pop() if conditions else Q()
            for condition in conditions:
                query |= condition
        # Применяем фильтрацию
                queryset = queryset.filter(query).distinct()
        return queryset

    def create(self, request, *args, **kwargs):
        """ Добавление рецепта """
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        tags_data = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop("ingredients", [])
        recipe = serializer.save(author=self.request.user)
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(
                Ingredient,
                id=ingredient_data['id']
            )
            RecipeIngredient.objects.update_or_create(
                recipe=recipe,
                ingredient=ingredient,
                defaults={'amount': ingredient_data['amount']}
            )
        return Response(self.get_serializer(recipe).data,
                        status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """ Частичное обновление рецепта """
        instance = self.get_object()
        serializer = self.get_serializer(instance,
                                         data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        tags_data = validated_data.pop('tags', instance.tags.all())
        if validated_data.get('ingredients') is None:

            updated_recipe = serializer.save()
            updated_recipe.tags.set(tags_data)
            return Response(self.get_serializer(updated_recipe).data,
                            status=status.HTTP_200_OK)
        ingredients_data = validated_data.pop("ingredients")
        updated_recipe = serializer.save()
        updated_recipe.tags.set(tags_data)
        updated_recipe.ingredients.set([])
        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(
                Ingredient,
                id=ingredient_data['id']
            )
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
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if FavoriteRecipe.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response({'detail': 'Рецепт уже добавлен в избранные'},
                                status=status.HTTP_400_BAD_REQUEST)
            FavoriteRecipe.objects.create(user=user, recipe=recipe)
            return Response({'detail': 'Рецепт добавлен в избранное'},
                            status=status.HTTP_201_CREATED)
        favorite_recipe = FavoriteRecipe.objects.get(user=user, recipe=recipe)
        favorite_recipe.delete()
        return Response({'detail': 'Рецепт удален из избранного'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        """Добавление рецпта в список покупок"""
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            if ShoppingcartRecipe.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response({'detail': 'Рецепт уже добавлен в корзину'},
                                status=status.HTTP_400_BAD_REQUEST)
            ShoppingcartRecipe.objects.create(user=user, recipe=recipe)
            return Response({'detail': 'Рецепт добавлен в корзину'},
                            status=status.HTTP_201_CREATED)
        favorite_recipe = ShoppingcartRecipe.objects.get(
            user=user,
            recipe=recipe
        )
        favorite_recipe.delete()
        return Response({'detail': 'Рецепт удален из корзины'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='get-link')
    def short_link(self, request, pk=None):
        """ Получение короткой ссылки на рецептк."""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link, created = ShortLink.objects.get_or_create(recipe=recipe)
        serializer = ShortLinkSerializer(short_link)
        scheme = request.scheme
        host = request.get_host()
        data = serializer.data['short_code']
        return Response({
            "short-link": f"{scheme}://{host}/s/{data}"
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def download_shopping_cart(self, request):
        """ Возвращает TXT-файл со списком покупок. """
        user = request.user
        recipes = self.get_queryset().filter(shopping__user=user)
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
        short_link = get_object_or_404(ShortLink, short_code=short_code)
        recipe = short_link.recipe
        scheme = request.scheme
        host = request.get_host()
        return (redirect(f'{scheme}://{host}/recipes/{recipe.id}'))


class ObtainAuthTokenView(APIView):
    """Представление для получения token."""
    serializer_class = EmailAuthTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            print(2, '___________')
            token, created = Token.objects.get_or_create(user=user)
            return Response({'auth_token': token.key})
        else:
            raise ValidationError(serializer.errors)


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
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            serializer = AvatarSerializer(user, data=request.data,
                                          partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"avatar": serializer.data['avatar']},
                                status=status.HTTP_200_OK)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        user.avatar = None
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        """Смена пароля текущего пользователя."""
        data = request.data
        old_password = data.get('current_password')
        new_password = data.get('new_password')
        user = request.user
        if not user.check_password(old_password):
            return Response({"error": "Неверный старый пароль."},
                            status=status.HTTP_400_BAD_REQUEST)
        user.password = make_password(new_password)
        user.save()
        return Response({"success": "Пароль успешно обновлен."},
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'],
            url_path='subscribe', permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        """Подписка на пользователя."""
        following = self.get_object()
        user = request.user
        if request.method == 'POST':
            if Subscription.objects.filter(user=user,
                                           following=following).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, following=following)
            foll = get_object_or_404(User, username=following)
            foll.is_subscribed = True
            serializer = UserSubscribeSerializers(foll,
                                                  context={'request': request})
            return Response(serializer.data, status=201)
        favorite_recipe = Subscription.objects.get(user=user,
                                                   following=following)
        favorite_recipe.delete()
        return Response({'detail': 'Вы отписались от пользователя'},
                        status=status.HTTP_204_NO_CONTENT)

    def get_recipes_limit(self, request):
        """Вспомогательная функция для сокращения длины строки"""
        return request.query_params.get('recipes_limit')

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated], )
    def subscriptions(self, request):
        """Список подписок."""
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        result = []
        for subscription in subscriptions:
            foll = get_object_or_404(User, username=subscription.following)
            serializer = UserSubscribeWithRecipesCountSerializer(
                foll,
                context={'request': request,
                         'recipes_limit': self.get_recipes_limit(request)}
            )
            result.append(serializer.data)
        paginator = self.pagination_class()
        paginated_result = paginator.paginate_queryset(result, request)
        return paginator.get_paginated_response(paginated_result)
