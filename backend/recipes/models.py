"""Модели для рецептов!"""
import random

from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth import get_user_model
from django.db import models

from recipes.constants import (
    MAX_LENGTH_NAME_INGREDIENT,
    MAX_LENGTH_NAME_RECIPE,
    MAX_LENGTH_NAME_TAG,
    MIN_TIME,
    MAX_TIME,
    MAX_LENGTH_SLUG,
    MIN_AMOUNT,
    MAX_AMOUNT,
    MAX_LENGTH_M_UNIT,
    RETURN_TEXT_LEN,
)

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        unique=True,
        max_length=MAX_LENGTH_NAME_TAG,
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

    def __str__(self):
        return self.name[:RETURN_TEXT_LEN]


class Ingredient(models.Model):
    name = models.CharField(
        unique=True,
        max_length=MAX_LENGTH_NAME_INGREDIENT,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_M_UNIT,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit'
            ),
        )

    def __str__(self):
        return self.name[:RETURN_TEXT_LEN]


class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipes', verbose_name='Автор')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиент',
    )

    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Метка',
    )
    image = models.ImageField(
        upload_to='recipes/images',
        default=None
    )
    name = models.CharField(
        max_length=MAX_LENGTH_NAME_RECIPE,

        verbose_name='Название'
    )
    text = models.TextField('Описание рецепта')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(MIN_TIME),
            MaxValueValidator(MAX_TIME)]
    )
    pub_date = models.DateTimeField('Дата пуликации', auto_now_add=True)
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
            if not Recipe.objects.filter(short_code=code).exists():
                break
        return code

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name[:RETURN_TEXT_LEN]


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Метка для рецпта'
        verbose_name_plural = 'Метки для рецепта'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'tag'),
                name='unique_recipe_tag'
            ),
        )

    def __str__(self):
        return self.recipe.name[:RETURN_TEXT_LEN]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField('Количество', validators=[
        MinValueValidator(MIN_AMOUNT),
        MaxValueValidator(MAX_AMOUNT)]
    )

    class Meta:
        verbose_name = 'Ингредиенты для рецепта'
        verbose_name_plural = 'Ингредиенты для рецепта'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            ),
        )

    def __str__(self):
        return self.recipe.name[:RETURN_TEXT_LEN]


class BaseFavoriteAndCartModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='%(model_name)s'
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipe_user_%(class)s'
            ),
        )

    def __str__(self):
        return self.recipe.name[:RETURN_TEXT_LEN]


class FavoriteRecipe(BaseFavoriteAndCartModel):
    class Meta(BaseFavoriteAndCartModel.Meta):
        verbose_name = 'избранные'
        verbose_name_plural = 'Избранные'


class ShoppingcartRecipe(BaseFavoriteAndCartModel):
    class Meta(BaseFavoriteAndCartModel.Meta):
        verbose_name = 'покупка'
        verbose_name_plural = 'Покупки'
