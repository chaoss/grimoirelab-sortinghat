"""Sortinghat URL Configuration"""


from django.conf import settings
from django.urls import path, re_path
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from sortinghat.core.views import (SortingHatGraphQLView, change_password, api_login)

from .schema import schema

urlpatterns = [
    path('api/', csrf_exempt(SortingHatGraphQLView.as_view(graphiql=settings.DEBUG, schema=schema))),
    path('api/login/', api_login, name='api_login'),
    path('password_change/', change_password, name='password_change'),
    re_path(r'^(?!static).*$', TemplateView.as_view(template_name="index.html"))
]
