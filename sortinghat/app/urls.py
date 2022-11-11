"""Sortinghat URL Configuration"""


from django.conf import settings
from django.urls import path, re_path
from django.views.generic import TemplateView

from sortinghat.core.views import (SortingHatGraphQLView, change_password)

from .schema import schema

urlpatterns = [
    path('api/', SortingHatGraphQLView.as_view(graphiql=settings.DEBUG, schema=schema)),
    path('password_change/', change_password, name='password_change'),
    re_path(r'^(?!static).*$', TemplateView.as_view(template_name="index.html"))
]
