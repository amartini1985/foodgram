from django.contrib import admin

from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    ShoppingcartRecipe,
    Tag
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'text', 'author', 'display_tag', 'image', 'display_ingredient',
    )

    @admin.display(description='Tags')
    def display_tag(self, obj):
        return ', '.join([tags.name for tags in obj.tags.all()])

    @admin.display(description='Ingredients')
    def display_ingredient(self, obj):
        return ', '.join(
            [ingredient.name for ingredient in obj.ingredients.all()])


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(ShoppingcartRecipe)
class ShoppingcartRecipeAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
