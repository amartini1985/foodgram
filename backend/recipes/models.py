"""Модели для рецептов"""
import random

from django.contrib.auth import get_user_model
from django.db import models

from recipes.constants import (
    MAX_LENGTH_NAME, MAX_LENGTH_SLUG
)

User = get_user_model()

MEASURES = (
    ('кг', 'Килограммы'),
    ('г', 'Граммы'),
    ('л', 'Литры'),
    ('мл', 'Миллилитры'),
    ('с. л.', 'Столовый ложки'),
    ('ч. л.', 'Чайные ложки'),
    ('шт.', 'Штуки'),
    ('капля', 'Капли'),
)


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        verbose_name='Название'
    )
    slug = models.SlugField(
        unique=True,
        max_length=MAX_LENGTH_SLUG,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'метка'
        verbose_name_plural = 'Метки'


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_NAME,
        choices=MEASURES,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipes', verbose_name='Автор')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиент'
    )

    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Метка'
    )
    image = models.ImageField(
        upload_to='recipes/images',
        null=True,
        default=None
    )
    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        verbose_name='Название'
    )
    text = models.TextField('Описание рецепта')
    cooking_time = models.IntegerField('Время приготовления')
    pub_date = models.DateTimeField('Дата пуликации', auto_now_add=True)
    is_favorited = models.BooleanField('Избранные', default=False)
    is_in_shopping_cart = models.BooleanField('Список покупок', default=False)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.FloatField('Количество')

    class Meta:
        verbose_name = 'Ингредиенты для рецепта'
        verbose_name_plural = 'Ингредиенты для рецепта'


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )

    class Meta:
        unique_together = ('user', 'following')
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipes'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'избранные'
        verbose_name_plural = 'Избранные'


class ShoppingcartRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_recipes'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping'
    )

    class Meta:
        unique_together = ('user', 'recipe')
        verbose_name = 'покупка'
        verbose_name_plural = 'Покупки'


class ShortLink(models.Model):
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='short_link'
    )
    short_code = models.CharField(max_length=8, unique=True)

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.generate_unique_shortcode()
        super().save(*args, **kwargs)

    def generate_unique_shortcode(self):
        code = ''
        allowed_chars = (
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        )
        while True:
            code = ''.join(random.choice(allowed_chars) for _ in range(8))
            if not ShortLink.objects.filter(short_code=code).exists():
                break
        return code
