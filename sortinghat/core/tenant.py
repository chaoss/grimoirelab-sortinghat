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
#
# Authors:
#     Jose Javier Merchante <jjmerchante@bitergia.com>
#

import threading
import logging

from graphql_jwt.shortcuts import get_user_by_token
from graphql_jwt.utils import get_credentials

from .models import Tenant


# This threading variable is used to store the name
# of the database that will be used during a request
# or a job execution.
TenantThreadLocal = threading.local()

logger = logging.getLogger(__name__)


def get_db_tenant():
    return getattr(TenantThreadLocal, 'database', None)


def set_db_tenant(database='default'):
    setattr(TenantThreadLocal, 'database', database)


def unset_db_tenant():
    delattr(TenantThreadLocal, 'database')


def default_tenant_resolver(request):
    return 'default'


def tenant_from_username_header(request):
    """
    Return a database name depending on the authenticated user using JWT
    and the header for the request.
    The tenant name is retrieved from a global table in the database.
    If the user is not authenticated return the 'default' database which
    can't be used to store data for tenants.
    """
    # Get user from JWT, the same way JWT middleware works
    token = get_credentials(request)
    if token is not None:
        request.user = get_user_by_token(token, request)
    if request.user and request.user.is_authenticated:
        header = request.headers.get('sortinghat-tenant')
        try:
            tenant = Tenant.objects.get(user=request.user, header=header)
            return tenant.database
        except Tenant.DoesNotExist:
            logger.warning(f"Tenant for User<{request.user.username}> and Header<{header}> not defined.")
            return None
    else:
        # Probably not authenticated
        return 'default'
