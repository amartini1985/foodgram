from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from api.serializers_fields import Base64ImageField
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


class UserCreateSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователя."""
    password = serializers.CharField(write_only=True, required=True)

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления аватара пользователя."""
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request', False)
        return (request and request.user.is_authenticated
                and obj.follower.filter(user=request.user).exists())


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для меток."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для количество ингредиентов."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'amount']


class RecipeIngredientUtilSerializer(serializers.ModelSerializer):
    """Сериализатор формирования ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ["id", "name", "measurement_unit", 'amount']


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов на чтение."""
    author = UserSerializer()
    ingredients = RecipeIngredientUtilSerializer(
        many=True,
        source="recipeingredient_set")
    image = Base64ImageField()
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', "name", 'image',
                  "text", "cooking_time")
        read_only_fields = fields

    def get_is_favorited(self, obj):
        request = self.context.get('request', False)
        return (request and request.user.is_authenticated
                and obj.favoriterecipe.filter(user=request.user).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request', False)
        return (request and request.user.is_authenticated
                and obj.shoppingcartrecipe.filter(user=request.user).exists())


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов на запись."""
    ingredients = RecipeIngredientSerializer(
        many=True,
        required=True,
        allow_null=False)
    image = Base64ImageField(required=True, allow_null=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True)

    class Meta:
        model = Recipe
        fields = ("id", "name", "text", "cooking_time", 'ingredients',
                  'image', 'tags')

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

    def validate(self, data):
        tags_data = data.get('tags')
        ingredients_data = data.get('ingredients')
        if ingredients_data is None:
            raise ValidationError(
                'Поле ingredients обязательно для заполнения')
        if tags_data is None:
            raise ValidationError(
                'Поле tags обязательно для заполнения')
        if not ingredients_data:
            raise ValidationError(
                'Список ингредиентов не может быть пустым.')
        if not tags_data:
            raise ValidationError(
                'Список ингредиентов не может быть пустым.')
        if not self.all_unique(tags_data):
            raise serializers.ValidationError(
                'Одинаковые метки недопустимы')
        if not self.all_unique_dicts(ingredients_data):
            raise serializers.ValidationError(
                'Одинаковые ингредиенты недопустимы')
        return data

    def add_ingredients(self, recipe, ingredients_data):
        """Добавление ингредиентов в рецепт."""
        ingredients_to_create = []
        for ingredient_data in ingredients_data:
            ingredient = ingredient_data['id'].id
            amount = ingredient_data['amount']
            ingredient = Ingredient.objects.get(id=ingredient)
            ingredients_to_create.append(RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount
            ))
        RecipeIngredient.objects.bulk_create(ingredients_to_create,
                                             ignore_conflicts=True)

    @transaction.atomic
    def create(self, validated_data):
        """Создание рецепта."""
        author = self.context['request'].user
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        try:
            recipe = Recipe.objects.create(**validated_data, author=author)
            recipe.tags.set(tags_data)
            self.add_ingredients(recipe, ingredients_data)
            return recipe
        except Exception as e:
            raise ValidationError(f'Ошибка при создании рецепта: {str(e)}')

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        try:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self.add_ingredients(instance, ingredients_data)
            instance.tags.clear()
            instance.tags.set(tags_data)
            return instance
        except Exception as e:
            raise ValidationError(f'Ошибка при создании рецепта: {str(e)}')

    def to_representation(self, instance):
        return RecipeReadSerializer(instance).data


class ShortRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для коротких данных о рецепте."""
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = ["id", "name", 'image', "cooking_time"]
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    class Meta:
        model = Subscription
        fields = ['user', 'following']

        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'following'),
                message="Нельзя подписаться повторно."
            )
        ]

    def validate(self, data):
        """Проверка, что пользователь не подписывается на себя."""
        if data.get('user') == data.get('following'):
            raise serializers.ValidationError("Нельзя подписаться на себя.")
        return data

    def to_representation(self, instance):
        return UserSubscribeRecipesCountSerializer(instance.following,
                                                   context=self.context).data


class BaseRecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для избранных и корзины."""

    class Meta:
        abstract = True
        fields = ['user', 'recipe']

    def to_representation(self, instance):
        return ShortRecipeReadSerializer(instance.recipe,
                                         context=self.context).data


class FavoriteSerializer(BaseRecipeSerializer):
    """Сериализатор для избранных."""
    class Meta(BaseRecipeSerializer.Meta):
        model = FavoriteRecipe
        validators = [
            UniqueTogetherValidator(
                queryset=FavoriteRecipe.objects.all(),
                fields=('user', 'recipe'),
                message="Вы уже добавили этот рецепт в избранные."
            )
        ]


class ShoppingcartSerializer(BaseRecipeSerializer):
    """Сериализатор для корзины."""
    class Meta(BaseRecipeSerializer.Meta):
        model = ShoppingcartRecipe
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingcartRecipe.objects.all(),
                fields=('user', 'recipe'),
                message="Вы уже добавили этот рецепт в корзину."
            )
        ]


class UserSubscribeRecipesCountSerializer(UserSerializer):
    """Сериализатор для списка подписок пользователя."""
    recipes = ShortRecipeReadSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar', 'recipes', 'recipes_count']
        read_only_fields = ['email', 'id', 'username', 'first_name',
                            'last_name', 'avatar']

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def to_representation(self, instance):
        retpresentation = super().to_representation(instance)
        limit = self.context['request'].query_params.get('recipes_limit', 6)
        if limit:
            retpresentation['recipes'] = (
                retpresentation['recipes'][:int(limit)]
            )
        return retpresentation
