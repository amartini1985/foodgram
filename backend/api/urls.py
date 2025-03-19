from django.urls import include, path, re_path
from rest_framework import routers

from api.views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    UserViewSet
)

router = routers.DefaultRouter()
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')

urlpatterns = [
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))

]
