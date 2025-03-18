from django.urls import path

from recipes.views import ShortLinkRedirectView

urlpatterns = [
    path('<slug:short_code>/', ShortLinkRedirectView.as_view(),
         name='short_link')
]
