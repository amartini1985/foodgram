"""Модуль для загрузки csv файлов!."""
import csv
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError
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
        with open(ingredients_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    Ingredient.objects.get_or_create(
                        name=row['name'],
                        measurement_unit=row['measurement_unit']
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f"Ингредиент {row['name']} загружен")
                    )
                except IntegrityError:
                    self.stdout.write(self.style.WARNING(
                        f"Ингредиент {row['name']} уже существует")
                    )

    def import_tags(self, data_dir):
        """Импортирует метки."""
        tags_file = os.path.join(data_dir, 'tags.csv')
        with open(tags_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    Tag.objects.get_or_create(
                        name=row['name'],
                        slug=row['slug']
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f"Метка {row['name']} загружена")
                    )
                except IntegrityError:
                    self.stdout.write(self.style.WARNING(
                        f"Метка {row['name']} уже существует")
                    )
