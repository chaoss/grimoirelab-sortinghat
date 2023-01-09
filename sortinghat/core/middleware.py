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

from graphql_jwt.compat import get_operation_name
from graphql_jwt.settings import jwt_settings


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
