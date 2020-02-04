# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2019 Bitergia
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
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#

from django.conf import settings
from graphql_jwt.decorators import user_passes_test


# This custom decorator takes the `user` object from the request's
# context and checks the value of the `is_authenticated` variable
# and the `AUTHENTICATION_REQUIRED` variable from the config settings.
check_auth = user_passes_test(
    lambda u: u.is_authenticated or not settings.AUTHENTICATION_REQUIRED
)
