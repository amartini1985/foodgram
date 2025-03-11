from django.contrib import admin

from .models import Tag, Ingredient


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'slug'
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'measurement_unit'
    )
