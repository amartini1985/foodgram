import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag
)
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователя."""
    password = serializers.CharField(required=True)

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )

    def to_representation(self, instance):
        representation = super(
            UserCreateSerializer, self).to_representation(instance)
        del representation['password']
        return representation


class EmailAuthTokenSerializer(serializers.Serializer):
    """Сериализатор для получения токена."""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'})

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "Пользователь с таким email не найден"},
                code='authorization')
        if not user.check_password(password):
            raise serializers.ValidationError(
                {"password": "Неверный пароль"},
                code='authorization')
        data['user'] = user
        return data


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
        try:
            user = self.context['request'].user
            if user.is_anonymous:
                return False
            return obj.follower.filter(user=user).exists()
        except Exception:
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
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ["id", "amount"]


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов на чтение."""
    author = UserSerializer()
    ingredients = serializers.SerializerMethodField()
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

    def get_ingredients(self, obj):
        recipe_ingredients = obj.recipeingredient_set.all()
        ingredients = []
        for ri in recipe_ingredients:
            ingredient_dict = {
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                "measurement_unit": ri.ingredient.measurement_unit,
                'amount': ri.amount,
            }
            ingredients.append(ingredient_dict)
        return ingredients

    def get_is_favorited(self, obj):
        try:
            user = self.context['request'].user
            if user.is_anonymous:
                return False
            return obj.favoriterecipe.filter(user=user).exists()
        except Exception:
            return False

    def get_is_in_shopping_cart(self, obj):
        try:
            user = self.context['request'].user
            if user.is_anonymous:
                return False
            return obj.shoppingcartrecipe.filter(user=user).exists()
        except Exception:
            return False


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов на запись."""
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    ingredients = RecipeIngredientSerializer(
        many=True,
        required=True,
        allow_null=False
    )
    image = Base64ImageField(required=True, allow_null=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )

    class Meta:
        model = Recipe
        fields = ("id", "name", "text", "cooking_time", 'ingredients',
                  'image', 'author', 'tags')

    def validate_ingredients(self, value):
        if len(value) == 0:
            raise ValidationError("Список ингредиентов не может быть пустым.")
        return value

    def validate_tags(self, value):
        if len(value) == 0:
            raise ValidationError("Список меток не может быть пустым.")
        return value

    def to_representation(self, instance):
        return RecipeReadSerializer(instance).data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""
    user = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    following = serializers.SlugRelatedField(
        queryset=User.objects.all(),
        slug_field='username'
    )

    class Meta:
        model = Subscription
        fields = '__all__'

        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'following')
            )
        ]


class ShortRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для коротких данных о рецепте."""
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = ["id", "name", 'image', "cooking_time"]
        read_only_fields = fields


class UserSubscribeWithRecipesCountSerializer(serializers.Serializer):
    """Сериализатор для списка подписок пользователя."""
    email = serializers.EmailField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)
    recipes = ShortRecipeReadSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.follower.filter(user=user).exists()

    def to_representation(self, instance):
        retpresentation = super().to_representation(instance)
        limit = self.context.get('recipes_limit', None)
        if limit:
            retpresentation['recipes'] = (
                retpresentation['recipes'][:int(limit)]
            )
        return retpresentation
