from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response


def add_recipe_to(user, recipe, serializer):
    """Общий метод для добавления рецепта в избранное или корзину."""
    data = {'user': user.id, 'recipe': recipe.id}
    serializer = serializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def remove_recipe_from(user, recipe, model):
    """Обощий метод для удаления рецепта из избранного или корзины."""
    deleted_count, _ = model.objects.filter(
        user=user, recipe=recipe).delete()
    if deleted_count == 0:
        return Response({'detail': 'Рецепт не найден'},
                        status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail': 'Рецепт удален'},
                    status=status.HTTP_204_NO_CONTENT)


def create_file(total_ingredients):
    """Формирование файла покупок."""
    content = ''
    for ingredient in total_ingredients:
        ingredient_name = ingredient['ingredient__name']
        unit = ingredient['ingredient__measurement_unit']
        total_amount = ingredient['total_amount']
        ingredient_name = f"{ingredient_name} ({unit})"
        content += f"{ingredient_name} - {total_amount}\n"
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = (
        'attachment; filename="shopping_list.txt"'
    )
    return response
