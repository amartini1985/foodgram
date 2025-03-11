import base64
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers

from api.constants import (
    MAX_LENGTH_USERNAME,
    MAX_LENGTH_EMAIL
)
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShortLink,
    Subscription,
    Tag
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):

    username = serializers.CharField(
        max_length=MAX_LENGTH_USERNAME,
        required=True
    )
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        required=True,
    )
    first_name = serializers.CharField(
        max_length=MAX_LENGTH_USERNAME,
        required=True,
    )
    last_name = serializers.CharField(
        max_length=MAX_LENGTH_USERNAME,
        required=True
    )
    password = serializers.CharField(
        required=True
    )

    def validate(self, data):
        """Проверка, что email и username не были зарегистрированы."""
        username = data.get('username')
        email = data.get('email')
        if User.objects.filter(
                email=email
        ).exclude(username=username).exists():
            raise serializers.ValidationError(
                "Такой email уже зарегистрирован."
            )
        if User.objects.filter(
                username=username
        ).exclude(email=email).exists():
            raise serializers.ValidationError(
                "Такой username уже зарегистрирован."
            )
        return data

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
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'})

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = get_object_or_404(User, email=email)
            if not user or not user.check_password(password):
                print('_________________')
                message = ('Неверный email или password')
                raise serializers.ValidationError(message, code='authorization')
        else:
            message = ('Отсутсвуют данные в поле email или password')
            raise serializers.ValidationError(message, code='authorization')
        data['user'] = user
        return data


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'avatar')


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Класс Meta."""

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
    """Сериализатор для категорий."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для категорий."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    amount = serializers.FloatField()
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ["id", "amount"]


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField(required=False, allow_null=True)
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
            return obj.favorites.filter(user=user).exists()
        except Exception:
            return False

    def get_is_in_shopping_cart(self, obj):
        try:
            user = self.context['request'].user
            if user.is_anonymous:
                return False
            return obj.shopping.filter(user=user).exists()
        except Exception:
            return False


class RecipeWriteSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )

    class Meta:
        model = Recipe
        fields = ("id", "name", "text", "cooking_time", 'ingredients',
                  'image', 'author', 'tags')

    def to_representation(self, instance):
        return RecipeReadSerializer(instance).data


class SubscriptionSerializer(serializers.ModelSerializer):
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


class UserSubscribeWithRecipesCountSerializer(serializers.Serializer):
    email = serializers.EmailField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)
    recipes = RecipeReadSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def to_representation(self, instance):
        retpresentation = super().to_representation(instance)
        limit = self.context.get('recipes_limit', None)
        if limit:
            retpresentation['recipes'] = (
                retpresentation['recipes'][:int(limit)]
            )
        return retpresentation


class ShortRecipeReadSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = ["id", "name", 'image', "cooking_time"]
        read_only_fields = fields


class UserSubscribeSerializers(serializers.ModelSerializer):
    recipes = ShortRecipeReadSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'avatar')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return obj.follower.filter(user=user).exists()


class ShortLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShortLink
        fields = ['short_code']
