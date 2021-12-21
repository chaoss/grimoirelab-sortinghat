#!/usr/bin/env python
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

import datetime
import sys
import unittest

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat.exceptions import InvalidDateError
from sortinghat.utils import merge_date_ranges, str_to_datetime, \
    to_unicode, uuid

DATE_OUT_OF_BOUNDS_ERROR = "%(type)s %(date)s is out of bounds"
SOURCE_NONE_OR_EMPTY_ERROR = "source cannot be"
IDENTITY_NONE_OR_EMPTY_ERROR = "identity data cannot be None or empty"


class TestMergeDateRanges(unittest.TestCase):
    """Unit tests for merge_date_ranges function"""

    def test_merge_date_ranges(self):
        """Test function with several case inputs"""

        # Case 1
        dates = [(datetime.datetime(1900, 1, 1), datetime.datetime(2010, 1, 1)),
                 (datetime.datetime(2008, 1, 1), datetime.datetime(2100, 1, 1))]

        ranges = [r for r in merge_date_ranges(dates)]
        self.assertEqual(len(ranges), 1)
        self.assertEqual(ranges[0], (datetime.datetime(2008, 1, 1), datetime.datetime(2010, 1, 1)))

        # Case 2
        dates = [(datetime.datetime(1900, 1, 1), datetime.datetime(2010, 1, 1)),
                 (datetime.datetime(2010, 1, 2), datetime.datetime(2100, 1, 1)),
                 (datetime.datetime(2008, 1, 1), datetime.datetime(2010, 1, 1))]

        ranges = [r for r in merge_date_ranges(dates)]
        self.assertEqual(len(ranges), 2)
        self.assertEqual(ranges[0], (datetime.datetime(2008, 1, 1), datetime.datetime(2010, 1, 1)))
        self.assertEqual(ranges[1], (datetime.datetime(2010, 1, 2), datetime.datetime(2100, 1, 1)))

        # Case 3
        dates = [(datetime.datetime(1900, 1, 1), datetime.datetime(2010, 1, 1)),
                 (datetime.datetime(2010, 1, 2), datetime.datetime(2100, 1, 1))]

        ranges = [r for r in merge_date_ranges(dates)]
        self.assertEqual(len(ranges), 2)
        self.assertEqual(ranges[0], (datetime.datetime(1900, 1, 1), datetime.datetime(2010, 1, 1)))
        self.assertEqual(ranges[1], (datetime.datetime(2010, 1, 2), datetime.datetime(2100, 1, 1)))

        # Case 4
        dates = [(datetime.datetime(2005, 1, 1), datetime.datetime(2008, 1, 1)),
                 (datetime.datetime(2005, 10, 15), datetime.datetime(2010, 1, 1)),
                 (datetime.datetime(2008, 1, 5), datetime.datetime(2009, 1, 1))]

        ranges = [r for r in merge_date_ranges(dates)]
        self.assertEqual(len(ranges), 1)
        self.assertEqual(ranges[0], (datetime.datetime(2005, 1, 1), datetime.datetime(2010, 1, 1)))

        # Case 5
        dates = [(datetime.datetime(1900, 1, 1), datetime.datetime(2100, 1, 1))]

        ranges = [r for r in merge_date_ranges(dates)]
        self.assertEqual(len(ranges), 1)
        self.assertEqual(ranges[0], (datetime.datetime(1900, 1, 1), datetime.datetime(2100, 1, 1)))

        # Case 6
        dates = [(datetime.datetime(1900, 1, 1), datetime.datetime(2100, 1, 1)),
                 (datetime.datetime(1900, 1, 1), datetime.datetime(2100, 1, 1))]

        ranges = [r for r in merge_date_ranges(dates)]
        self.assertEqual(len(ranges), 1)
        self.assertEqual(ranges[0], (datetime.datetime(1900, 1, 1), datetime.datetime(2100, 1, 1)))

        # Case 7
        dates = [(datetime.datetime(1900, 1, 1), datetime.datetime(2005, 1, 1))]

        ranges = [r for r in merge_date_ranges(dates)]
        self.assertEqual(len(ranges), 1)
        self.assertEqual(ranges[0], (datetime.datetime(1900, 1, 1), datetime.datetime(2005, 1, 1)))

        # Case 8
        dates = [(datetime.datetime(2005, 1, 1), datetime.datetime(2100, 1, 1))]

        ranges = [r for r in merge_date_ranges(dates)]
        self.assertEqual(len(ranges), 1)
        self.assertEqual(ranges[0], (datetime.datetime(2005, 1, 1), datetime.datetime(2100, 1, 1)))

        # Case 9
        dates = [(datetime.datetime(2000, 1, 1), datetime.datetime(2100, 1, 1)),
                 (datetime.datetime(1900, 1, 1), datetime.datetime(2100, 1, 1))]

        ranges = [r for r in merge_date_ranges(dates)]
        self.assertEqual(len(ranges), 1)
        self.assertEqual(ranges[0], (datetime.datetime(2000, 1, 1), datetime.datetime(2100, 1, 1)))

        # Case 10
        dates = [(datetime.datetime(2006, 1, 1), datetime.datetime(2008, 1, 1)),
                 (datetime.datetime(1999, 1, 1), datetime.datetime(2000, 1, 1)),
                 (datetime.datetime(1900, 1, 1), datetime.datetime(2100, 1, 1))]

        ranges = [r for r in merge_date_ranges(dates)]
        self.assertEqual(len(ranges), 2)
        self.assertEqual(ranges[0], (datetime.datetime(1999, 1, 1), datetime.datetime(2000, 1, 1)))
        self.assertEqual(ranges[1], (datetime.datetime(2006, 1, 1), datetime.datetime(2008, 1, 1)))

        # Case 11
        dates = [(datetime.datetime(2009, 1, 1), datetime.datetime(2010, 1, 1)),
                 (datetime.datetime(2010, 1, 1), datetime.datetime(2100, 1, 1))]

        ranges = [r for r in merge_date_ranges(dates)]
        self.assertEqual(len(ranges), 2)
        self.assertEqual(ranges[0], (datetime.datetime(2009, 1, 1), datetime.datetime(2010, 1, 1)))
        self.assertEqual(ranges[1], (datetime.datetime(2010, 1, 1), datetime.datetime(2100, 1, 1)))

        # Case 12
        dates = [(datetime.datetime(2009, 1, 1), datetime.datetime(2009, 1, 1)),
                 (datetime.datetime(2009, 1, 1), datetime.datetime(2010, 1, 1)),
                 (datetime.datetime(2010, 1, 1), datetime.datetime(2010, 1, 1)),
                 (datetime.datetime(2010, 1, 1), datetime.datetime(2010, 1, 1)),
                 (datetime.datetime(2010, 1, 1), datetime.datetime(2020, 1, 1)),
                 (datetime.datetime(2011, 1, 1), datetime.datetime(2022, 1, 1)),
                 (datetime.datetime(2022, 1, 1), datetime.datetime(2100, 1, 1))]

        ranges = [r for r in merge_date_ranges(dates)]
        self.assertEqual(len(ranges), 5)
        self.assertEqual(ranges[0], (datetime.datetime(2009, 1, 1), datetime.datetime(2009, 1, 1)))
        self.assertEqual(ranges[1], (datetime.datetime(2009, 1, 1), datetime.datetime(2010, 1, 1)))
        self.assertEqual(ranges[2], (datetime.datetime(2010, 1, 1), datetime.datetime(2010, 1, 1)))
        self.assertEqual(ranges[3], (datetime.datetime(2010, 1, 1), datetime.datetime(2022, 1, 1)))
        self.assertEqual(ranges[4], (datetime.datetime(2022, 1, 1), datetime.datetime(2100, 1, 1)))

    def test_dates_out_of_bounds(self):
        """Check whether it raises an exception when dates are out of bounds"""

        # Case 1
        dates = [(datetime.datetime(2008, 1, 1), datetime.datetime(2100, 1, 1)),
                 (datetime.datetime(1800, 1, 1), datetime.datetime(2010, 1, 1))]

        with self.assertRaisesRegexp(ValueError,
                                     DATE_OUT_OF_BOUNDS_ERROR
                                     % {'type': 'start date',
                                        'date': '1800-01-01 00:00:00'}):
            [r for r in merge_date_ranges(dates)]

        # Case 2
        dates = [(datetime.datetime(2008, 1, 1), datetime.datetime(2100, 2, 1)),
                 (datetime.datetime(1900, 1, 1), datetime.datetime(2010, 1, 1))]

        with self.assertRaisesRegexp(ValueError,
                                     DATE_OUT_OF_BOUNDS_ERROR
                                     % {'type': 'end date',
                                        'date': '2100-02-01 00:00:00'}):
            [r for r in merge_date_ranges(dates)]

    def test_none_list_of_dates(self):
        """Check if the result is empty when the list of ranges is None"""

        ranges = [r for r in merge_date_ranges(None)]
        self.assertEqual(ranges, [])

    def test_empty_list_of_dates(self):
        """Check if the result is empty when the list of ranges is empty"""

        ranges = [r for r in merge_date_ranges([])]
        self.assertEqual(ranges, [])


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


class TestToUnicode(unittest.TestCase):
    """Unit tests for to_unicode function"""

    def test_to_unicode(self):
        """Check unicode casting with several cases"""

        result = to_unicode('abcdefghijk')
        self.assertEqual(result, 'abcdefghijk')

        result = to_unicode(None)
        self.assertEqual(result, 'None')

        result = to_unicode(1234)
        self.assertEqual(result, '1234')

        result = to_unicode(1234.4321)
        self.assertEqual(result, '1234.4321')

    def test_unaccent(self):
        """Check unicode casting removing accents"""

        result = to_unicode('Tomáš Čechvala', unaccent=True)
        self.assertEqual(result, 'Tomas Cechvala')

        result = to_unicode('Santiago Dueñas', unaccent=True)
        self.assertEqual(result, 'Santiago Duenas')

        result = to_unicode(1234, unaccent=True)
        self.assertEqual(result, '1234')


class TestUUID(unittest.TestCase):
    """Unit tests for uuid function"""

    def test_uuid(self):
        """Check whether the function returns the expected UUID"""

        result = uuid('scm', email='jsmith@example.com',
                      name='John Smith', username='jsmith')
        self.assertEqual(result, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        result = uuid('scm', email='jsmith@example.com')
        self.assertEqual(result, '334da68fcd3da4e799791f73dfada2afb22648c6')

        result = uuid('scm', email='', name='John Smith',
                      username='jsmith')
        self.assertEqual(result, 'a4b4591c3a2171710c157d7c278ea3cc03becf81')

        result = uuid('scm', email='', name='John Smith',
                      username='')
        self.assertEqual(result, '76e3624e24aacae178d05352ad9a871dfaf81c13')

        result = uuid('scm', email='', name='', username='jsmith')
        self.assertEqual(result, '6e7ce2426673f8a23a72a343b1382dda84c0078b')

        result = uuid('scm', email='', name='John Ca\xf1as', username='jcanas')
        self.assertEqual(result, 'c88e126749ff006eb1eea25e4bb4c1c125185ed2')

        result = uuid('scm', email='', name="Max Müster", username='mmuester')
        self.assertEqual(result, '9a0498297d9f0b7e4baf3e6b3740d22d2257367c')

    def test_case_insensitive(self):
        """Check if same values in lower or upper case produce the same UUID"""

        uuid_a = uuid('scm', email='jsmith@example.com',
                      name='John Smith', username='jsmith')
        uuid_b = uuid('SCM', email='jsmith@example.com',
                      name='John Smith', username='jsmith')

        self.assertEqual(uuid_a, uuid_b)

        uuid_c = uuid('scm', email='jsmith@example.com',
                      name='john smith', username='jsmith')

        self.assertEqual(uuid_c, uuid_a)

        uuid_d = uuid('scm', email='jsmith@example.com',
                      name='John Smith', username='JSmith')

        self.assertEqual(uuid_d, uuid_a)

        uuid_e = uuid('scm', email='JSMITH@example.com',
                      name='John Smith', username='jsmith')

        self.assertEqual(uuid_e, uuid_a)

    def test_case_unaccent_name(self):
        """Check if same values accent or unaccent produce the same UUID"""

        accent_result = uuid('scm', email='', name="Max Müster", username='mmuester')
        unaccent_result = uuid('scm', email='', name="Max Muster", username='mmuester')
        self.assertEqual(accent_result, unaccent_result)
        self.assertEqual(accent_result, '9a0498297d9f0b7e4baf3e6b3740d22d2257367c')

        accent_result = uuid('scm', email='', name="Santiago Dueñas", username='')
        unaccent_result = uuid('scm', email='', name="Santiago Duenas", username='')
        self.assertEqual(accent_result, unaccent_result)
        self.assertEqual(accent_result, '0f1dd18839007ee8a11d02572ca0a0f4eedaf2cd')

        accent_result = uuid('scm', email='', name="Tomáš Čechvala", username='')
        partial_accent_result = uuid('scm', email='', name="Tomáš Cechvala", username='')
        unaccent_result = uuid('scm', email='', name="Tomas Cechvala", username='')
        self.assertEqual(accent_result, unaccent_result)
        self.assertEqual(accent_result, partial_accent_result)

    def test_surrogate_escape(self):
        """Check if no errors are raised for invalid UTF-8 chars"""

        result = uuid('scm', name="Mishal\udcc5 Pytasz")
        self.assertEqual(result, '625166bdc2c4f1a207d39eb8d25315010babd73b')

    def test_none_source(self):
        """Check whether uuid cannot be obtained giving a None source"""

        self.assertRaisesRegex(ValueError, SOURCE_NONE_OR_EMPTY_ERROR,
                               uuid, None)

    def test_empty_source(self):
        """Check whether uuid cannot be obtained giving aadded to the registry"""

        self.assertRaisesRegex(ValueError, SOURCE_NONE_OR_EMPTY_ERROR,
                               uuid, '')

    def test_none_or_empty_data(self):
        """Check whether uuid cannot be obtained when identity data is None or empty"""

        self.assertRaisesRegex(ValueError, IDENTITY_NONE_OR_EMPTY_ERROR,
                               uuid, 'scm', None, '', None)
        self.assertRaisesRegex(ValueError, IDENTITY_NONE_OR_EMPTY_ERROR,
                               uuid, 'scm', '', '', '')


if __name__ == "__main__":
    unittest.main()
