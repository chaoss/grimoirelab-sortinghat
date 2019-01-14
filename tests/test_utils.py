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
#

from django.test import TestCase

from sortinghat.core.utils import unaccent_string


UNACCENT_TYPE_ERROR = "argument must be a string; int given"


class TestUnnacentString(TestCase):
    """Unit tests for unaccent_string"""

    def test_unaccent(self):
        """Check unicode casting removing accents"""

        result = unaccent_string('Tomáš Čechvala')
        self.assertEqual(result, 'Tomas Cechvala')

        result = unaccent_string('Tomáš Čechvala')
        self.assertEqual(result, 'Tomas Cechvala')

        result = unaccent_string('Santiago Dueñas')
        self.assertEqual(result, 'Santiago Duenas')

    def test_no_string(self):
        """Check if an exception is raised when the type is not a string"""

        with self.assertRaisesRegex(TypeError, UNACCENT_TYPE_ERROR):
            unaccent_string(1234)
