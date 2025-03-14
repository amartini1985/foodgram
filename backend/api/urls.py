from django.urls import include, path
from rest_framework import routers

from api.views import (
    IngredientViewSet,
    LogoutView,
    ObtainAuthTokenView,
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
    path('auth/token/login/', ObtainAuthTokenView.as_view(),
         name='token_obtain_pair'),
    path('auth/token/logout/', LogoutView.as_view(),
         name='token_logout'),
    path('', include(router.urls))

]
