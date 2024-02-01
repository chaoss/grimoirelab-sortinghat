# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from django.http import Http404
from graphql_jwt.compat import get_operation_name
from graphql_jwt.settings import jwt_settings

from . import tenant


def allow_any(info, **kwargs):
    # This code is based on S.B. answer to StackOverflow question
    # "How to solve 'NoneType' object has no attribute 'fields' in
    # Graphene-django" (https://stackoverflow.com/a/71296685).
    try:
        operation_name = get_operation_name(info.operation.operation).title()
        operation_type = info.schema.get_type(operation_name)

        if hasattr(operation_type, 'fields'):

            field = operation_type.fields.get(info.field_name)

            if field is None:
                return False

        else:
            return False

        graphene_type = getattr(field.type, "graphene_type", None)

        return graphene_type is not None and issubclass(
            graphene_type, tuple(jwt_settings.JWT_ALLOW_ANY_CLASSES)
        )
    except Exception as e:
        return False


class TenantDatabaseMiddleware:
    """
    Middleware to select a database depending on the user and the header.
    When the pair user-header is not available for any tenant it returns a 404 error.
    For unauthenticated users it will return the 'default' database to allow login.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        database = tenant.tenant_from_username_header(request)
        if database:
            tenant.set_db_tenant(database)
            response = self.get_response(request)
            tenant.unset_db_tenant()
            return response
        else:
            raise Http404("Tenant not found in SortingHat.")


class TenantDatabaseRouter:
    """
    This class routes database queries to the right database.
    Queries to applications with labels in 'auth_app_labels' will use the 'default' database.
    Queries to 'core.tenant' model will use the 'default' database too.
    Queries to a different model will obtain the database name from a threading local variable
    that is set for every request using a middleware.
    """

    auth_app_labels = {'auth', 'contenttypes', 'admin', 'sessions'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.auth_app_labels:
            return 'default'
        elif model._meta.app_label == 'core' and model._meta.model_name == 'tenant':
            return 'default'
        return tenant.get_db_tenant()

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.auth_app_labels:
            return 'default'
        elif model._meta.app_label == 'core' and model._meta.model_name == 'tenant':
            return 'default'
        return tenant.get_db_tenant()

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the auth or contenttypes apps is
        involved.
        """
        if (
            obj1._meta.app_label in self.auth_app_labels or
            obj2._meta.app_label in self.auth_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the 'auth', 'contenttypes', 'admin' and 'core.tenant' apps
        and models only appear in the 'default' database. Don't include any
        other model in that database.
        """
        if app_label in self.auth_app_labels:
            return db == 'default'
        elif app_label == 'core' and model_name == 'tenant':
            return db == 'default'
        elif db == 'default':
            return False
        else:
            return None
