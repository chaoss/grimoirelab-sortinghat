#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Bitergia
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

import datetime
import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat.exceptions import InvalidDateError
from sortinghat.utils import str_to_datetime, uuid


SOURCE_NONE_OR_EMPTY_ERROR = "source cannot be"
IDENTITY_NONE_OR_EMPTY_ERROR = "identity data cannot be None or empty"


class TestStrToDatetime(unittest.TestCase):
    """Unit tests for str_to_datetime function"""

    def test_dates(self):
        """Check if it converts some dates to datetime objects"""

        date = str_to_datetime('2001-12-01')
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, datetime.datetime(2001, 12, 1))

        date = str_to_datetime('13-01-2001')
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, datetime.datetime(2001, 1, 13))

        date = str_to_datetime('12-01-01')
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, datetime.datetime(2001, 12, 1))

        date = str_to_datetime('2001-12-01 23:15:32')
        self.assertIsInstance(date, datetime.datetime)
        self.assertEqual(date, datetime.datetime(2001, 12, 1, 23, 15, 32))

    def test_invalid_date(self):
        """Check whether it fails with an invalid date"""

        self.assertRaises(InvalidDateError, str_to_datetime, '2001-13-01')
        self.assertRaises(InvalidDateError, str_to_datetime, '2001-04-31')

    def test_invalid_format(self):
        """Check whether it fails with invalid formats"""

        self.assertRaises(InvalidDateError, str_to_datetime, '2001-12-01mm')
        self.assertRaises(InvalidDateError, str_to_datetime, 'nodate')

    def test_none_string(self):
        """Check if it returns None when giving None objects"""

        date = str_to_datetime(None)
        self.assertEqual(date, None)

    def test_empty_string(self):
        """Check if it returns None when giving empty strings"""

        date = str_to_datetime('')
        self.assertEqual(date, None)


class TestUUID(unittest.TestCase):
    """Unit tests for uuid function"""

    def test_uuid(self):
        """Check whether the function returns the expected UUID"""

        result = uuid('scm', email='jsmith@example.com',
                      name='John Smith', username='jsmith')
        self.assertEqual(result, '03e12d00e37fd45593c49a5a5a1652deca4cf302')

        result = uuid('scm', email='jsmith@example.com')
        self.assertEqual(result, 'a4d4845e1b1e0edb85e37b04553026a6b76fc4ac')

        result= uuid('scm', email='', name='John Smith',
                     username='jsmith')
        self.assertEqual(result, 'b63e8e4e67381271e67e55d46a63b63fc306119f')

        result = uuid('scm', email='', name='John Smith',
                      username='')
        self.assertEqual(result, 'e2189be970c39c26b84d815f913b32ca953db940')

        result = uuid('scm', email='', name='', username='jsmith')
        self.assertEqual(result, '6e7ce2426673f8a23a72a343b1382dda84c0078b')

    def test_none_source(self):
        """Check whether uuid cannot be obtained giving a None source"""

        self.assertRaisesRegexp(ValueError, SOURCE_NONE_OR_EMPTY_ERROR,
                                uuid, None)

    def test_empty_source(self):
        """Check whether uuid cannot be obtained giving aadded to the registry"""

        self.assertRaisesRegexp(ValueError, SOURCE_NONE_OR_EMPTY_ERROR,
                                uuid, '')

    def test_none_or_empty_data(self):
        """Check whether uuid cannot be obtained when identity data is None or empty"""

        self.assertRaisesRegexp(ValueError, IDENTITY_NONE_OR_EMPTY_ERROR,
                                uuid, 'scm', None, '', None)
        self.assertRaisesRegexp(ValueError, IDENTITY_NONE_OR_EMPTY_ERROR,
                                uuid, 'scm', '', '', '')


if __name__ == "__main__":
    unittest.main()
