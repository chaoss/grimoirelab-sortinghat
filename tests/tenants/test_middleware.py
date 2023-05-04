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

import unittest.mock

import django.test

from sortinghat.core import tenant
from sortinghat.core.middleware import TenantDatabaseMiddleware


class TestTenantMiddleware(django.test.TestCase):
    """Unit tests for the tenant middleware"""

    def setUp(self):
        """Set queries context"""

        self.factory = django.test.RequestFactory()

    @unittest.mock.patch('sortinghat.core.tenant.tenant_from_username_header')
    def test_middleware(self, mock_user_tenant):
        """Test if the middleware returns the response correctly"""

        mock_user_tenant.return_value = 'tenant_1'

        get_response = unittest.mock.MagicMock()
        request = self.factory.get('/')

        middleware = TenantDatabaseMiddleware(get_response)
        response = middleware(request)

        # ensure get_response has been returned
        self.assertEqual(get_response.return_value, response)

    @unittest.mock.patch('sortinghat.core.tenant.tenant_from_username_header')
    def test_middleware_tenant(self, mock_user_tenant):
        """Test if the middleware assign the tenant correctly"""

        def get_response(r):
            return tenant.get_db_tenant()

        mock_user_tenant.return_value = 'tenant_1'

        request = self.factory.get('/')

        middleware = TenantDatabaseMiddleware(get_response)
        response = middleware(request)

        self.assertEqual(response, 'tenant_1')

        # The tenant is removed after the call
        self.assertEqual(tenant.get_db_tenant(), None)
