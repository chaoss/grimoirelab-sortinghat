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

from sortinghat.utils import unaccent_string, generate_uuid

UNACCENT_TYPE_ERROR = "argument must be a string; int given"
IDENTITY_NONE_OR_EMPTY_ERROR = "identity data cannot be empty"
SOURCE_NONE_OR_EMPTY_ERROR = "'source' cannot be"


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


class TestUUID(TestCase):
    """Unit tests for generate_uuid function"""

    def test_uuid(self):
        """Check whether the function returns the expected UUID"""

        result = generate_uuid('scm', email='jsmith@example.com',
                               name='John Smith', username='jsmith')
        self.assertEqual(result, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        result = generate_uuid('scm', email='jsmith@example.com')
        self.assertEqual(result, '334da68fcd3da4e799791f73dfada2afb22648c6')

        result = generate_uuid('scm', email='', name='John Smith', username='jsmith')
        self.assertEqual(result, 'a4b4591c3a2171710c157d7c278ea3cc03becf81')

        result = generate_uuid('scm', email='', name='John Smith', username='')
        self.assertEqual(result, '76e3624e24aacae178d05352ad9a871dfaf81c13')

        result = generate_uuid('scm', email='', name='', username='jsmith')
        self.assertEqual(result, '6e7ce2426673f8a23a72a343b1382dda84c0078b')

        result = generate_uuid('scm', email='', name='John Ca\xf1as', username='jcanas')
        self.assertEqual(result, 'c88e126749ff006eb1eea25e4bb4c1c125185ed2')

        result = generate_uuid('scm', email='', name="Max Müster", username='mmuester')
        self.assertEqual(result, '9a0498297d9f0b7e4baf3e6b3740d22d2257367c')

    def test_case_insensitive(self):
        """Check if same values in lower or upper case produce the same UUID"""

        uuid_a = generate_uuid('scm', email='jsmith@example.com',
                               name='John Smith', username='jsmith')
        uuid_b = generate_uuid('SCM', email='jsmith@example.com',
                               name='John Smith', username='jsmith')
        self.assertEqual(uuid_a, uuid_b)

        uuid_c = generate_uuid('scm', email='jsmith@example.com',
                               name='john smith', username='jsmith')
        self.assertEqual(uuid_c, uuid_a)

        uuid_d = generate_uuid('scm', email='jsmith@example.com',
                               name='John Smith', username='JSmith')
        self.assertEqual(uuid_d, uuid_a)

        uuid_e = generate_uuid('scm', email='JSMITH@example.com',
                               name='John Smith', username='jsmith')
        self.assertEqual(uuid_e, uuid_a)

    def test_case_unaccent_name(self):
        """Check if same values accent or unaccent produce the same UUID"""

        accent_result = generate_uuid('scm', email='', name="Max Müster", username='mmuester')
        unaccent_result = generate_uuid('scm', email='', name="Max Muster", username='mmuester')
        self.assertEqual(accent_result, unaccent_result)
        self.assertEqual(accent_result, '9a0498297d9f0b7e4baf3e6b3740d22d2257367c')

        accent_result = generate_uuid('scm', email='', name="Santiago Dueñas", username='')
        unaccent_result = generate_uuid('scm', email='', name="Santiago Duenas", username='')
        self.assertEqual(accent_result, unaccent_result)
        self.assertEqual(accent_result, '0f1dd18839007ee8a11d02572ca0a0f4eedaf2cd')

        accent_result = generate_uuid('scm', email='', name="Tomáš Čechvala", username='')
        partial_accent_result = generate_uuid('scm', email='', name="Tomáš Cechvala", username='')
        unaccent_result = generate_uuid('scm', email='', name="Tomas Cechvala", username='')
        self.assertEqual(accent_result, unaccent_result)
        self.assertEqual(accent_result, partial_accent_result)

    def test_surrogate_escape(self):
        """Check if no errors are raised for invalid UTF-8 chars"""

        result = generate_uuid('scm', name="Mishal\udcc5 Pytasz")
        self.assertEqual(result, '625166bdc2c4f1a207d39eb8d25315010babd73b')

    def test_none_source(self):
        """Check whether UUID cannot be obtained giving a None source"""

        with self.assertRaisesRegex(ValueError, SOURCE_NONE_OR_EMPTY_ERROR):
            generate_uuid(None)

    def test_empty_source(self):
        """Check whether UUID cannot be obtained giving aadded to the registry"""

        with self.assertRaisesRegex(ValueError, SOURCE_NONE_OR_EMPTY_ERROR):
            generate_uuid('')

    def test_none_or_empty_data(self):
        """Check whether UUID cannot be obtained when identity data is None or empty"""

        with self.assertRaisesRegex(ValueError, IDENTITY_NONE_OR_EMPTY_ERROR):
            generate_uuid('scm', email=None, name='', username=None)

        with self.assertRaisesRegex(ValueError, IDENTITY_NONE_OR_EMPTY_ERROR):
            generate_uuid('scm', email='', name='', username='')
