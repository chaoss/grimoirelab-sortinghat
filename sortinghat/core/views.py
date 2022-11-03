# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2020 Bitergia
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
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

import json
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordChangeForm

from graphene_django.views import GraphQLView as BaseGraphQLView
from graphql_jwt.exceptions import (PermissionDenied,
                                    JSONWebTokenExpired,
                                    JSONWebTokenError)

from .errors import (CODE_TOKEN_EXPIRED,
                     CODE_PERMISSION_DENIED,
                     CODE_INVALID_CREDENTIALS,
                     CODE_UNKNOWN_ERROR)

from .decorators import jwt_login_required


class SortingHatGraphQLView(BaseGraphQLView):
    """Base GraphQL view for SortingHat server."""

    @staticmethod
    def format_error(error):
        """Formats the GraphQL errors adding the error code to the response."""

        formatted_error = super(SortingHatGraphQLView, SortingHatGraphQLView).format_error(error)

        code = CODE_UNKNOWN_ERROR

        try:
            org_err = error.original_error

            if isinstance(org_err, JSONWebTokenExpired):
                code = CODE_TOKEN_EXPIRED
            elif isinstance(org_err, PermissionDenied):
                code = CODE_PERMISSION_DENIED
            elif isinstance(org_err, JSONWebTokenError):
                code = CODE_INVALID_CREDENTIALS
            else:
                code = error.original_error.code
        except AttributeError:
            pass
        finally:
            formatted_error['extensions'] = {'code': code}

        return formatted_error


@jwt_login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            response = {
                'updated': user.username
            }
            return HttpResponse(json.dumps(response),
                                content_type='application/json')
        else:
            response = {
                'errors': form.errors.get_json_data()
            }

            return HttpResponse(json.dumps(response),
                                content_type='application/json')
    else:
        return HttpResponse(status=405)
