from django.contrib.auth import get_user_model
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
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj:
            return obj.follower.filter(user=request.user).exists()
        return False


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
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj:
            return obj.favoriterecipe.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj:
            return obj.shoppingcartrecipe.filter(user=request.user).exists()
        return False


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов на запись."""
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True)
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
                  'image', 'author', 'tags')

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
        print(tags_data, ingredients_data)
        if ingredients_data is None or tags_data is None:
            raise ValidationError(
                'Поля tags и ingredients обязательны для заполнения')
        if len(ingredients_data) == 0:
            raise ValidationError(
                'Список ингредиентов не может быть пустым.')
        if len(tags_data) == 0:
            raise ValidationError(
                'Список ингредиентов не может быть пустым.')
        if not self.all_unique(tags_data):
            raise serializers.ValidationError(
                'Одинаковые метки недопустимы')
        if not self.all_unique_dicts(ingredients_data):
            raise serializers.ValidationError(
                'Одинаковые ингредиенты недопустимы')
        return data

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredients', [])
        author = validated_data.pop('author')
        recipe = Recipe.objects.create(**validated_data, author=author)
        for tag_data in tags_data:
            tag = Tag.objects.get(id=tag_data.id)
            recipe.tags.add(tag)
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id'].id
            amount = ingredient_data['amount']
            ingredient = Ingredient.objects.get(id=ingredient_id)
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount)
        return recipe

    def update(self, instance, validated_data):
        """ Обновляет существующий объект Recipe. """
        tags_data = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredients', [])
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)
        instance.save()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id'].id
            amount = ingredient_data['amount']
            ingredient = Ingredient.objects.get(id=ingredient_id)
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient,
                amount=amount)
        instance.tags.clear()
        for tag_data in tags_data:
            tag = Tag.objects.get(id=tag_data.id)
            instance.tags.add(tag)
        return instance

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


class UserSubscribeRecipesCountSerializer(serializers.ModelSerializer):
    """Сериализатор для списка подписок пользователя."""
    is_subscribed = serializers.SerializerMethodField()
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

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.follower.filter(user=user).exists()

    def to_representation(self, instance):
        retpresentation = super().to_representation(instance)
        limit = self.context['request'].query_params.get('recipes_limit', 6)
        if limit:
            retpresentation['recipes'] = (
                retpresentation['recipes'][:int(limit)]
            )
        return retpresentation
