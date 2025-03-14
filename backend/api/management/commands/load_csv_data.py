"""Модуль для загрузки csv файлов!."""
import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """Класс для загрузки csv файлов."""

    def handle(self, *args, **kwargs):
        """Основной метод."""
        data_dir = os.path.join(settings.BASE_DIR, 'data')
        self.stdout.write(self.style.SUCCESS('Пошла загрузка...'))
        self.import_ingredients(data_dir)
        self.import_tags(data_dir)
        self.stdout.write(self.style.SUCCESS('Загрузка прошла успешно!'))

    def import_ingredients(self, data_dir):
        """Импортирует ингредиенты."""
        ingredients_file = os.path.join(data_dir, 'ingredients.csv')
        ingredients_to_create = []
        with open(ingredients_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ingredient_data = {
                    'name': row['name'],
                    'measurement_unit': row['measurement_unit']
                }
                ingredients_to_create.append(Ingredient(**ingredient_data))
        try:
            Ingredient.objects.bulk_create(
                ingredients_to_create, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS('Все ингредиенты загружены'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Произошла ошибка при загрузке ингредиентов: {e}'))

    def import_tags(self, data_dir):
        """Импортирует метки."""
        tags_file = os.path.join(data_dir, 'tags.csv')
        tags_to_create = []
        with open(tags_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                tags_data = {
                    'name': row['name'],
                    'slug': row['slug']
                }
                tags_to_create.append(Tag(**tags_data))
        try:
            Tag.objects.bulk_create(tags_to_create, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS('Все метки загружены'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Произошла ошибка при загрузке меток: {e}'))
