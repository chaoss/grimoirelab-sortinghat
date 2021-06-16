"""Sortinghat URL Configuration"""


from django.conf import settings
from django.urls import path
from django.views.generic import TemplateView

from sortinghat.core.views import SortingHatGraphQLView

from .schema import schema

urlpatterns = [
    path('', TemplateView.as_view(template_name="index.html")),
    path('api/', SortingHatGraphQLView.as_view(graphiql=settings.DEBUG, schema=schema))
]
