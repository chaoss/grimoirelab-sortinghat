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


import datetime

from dateutil.tz import UTC

from django.test import TestCase

from sortinghat.core.aux import merge_datetime_ranges, validate_field

CANT_COMPARE_DATES_ERROR = "can't compare offset-naive and offset-aware datetimes"
DATE_OUT_OF_BOUNDS_ERROR = "'{type}' date {date} is out of bounds"
FIELD_NONE_ERROR = "'{name}' cannot be None"
FIELD_EMPTY_ERROR = "'{name}' cannot be an empty string"
FIELD_WHITESPACES_ERROR = "'{name}' cannot be composed by whitespaces only"
FIELD_TYPE_ERROR = "field value must be a string; int given"


class TestMergeDatetimeRanges(TestCase):
    """Unit tests for merge_datetime_ranges function"""

    def test_merge_datetime_ranges(self):
        """Test function with several case scenarios"""

        # Case 1: merge overlapped ranges
        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2008, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 2: merge a range contained within other ranges
        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2010, 1, 2, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2008, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2010, 1, 2, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 3: merge a set of ranges contained within another one
        dates = [
            (datetime.datetime(2006, 1, 1, tzinfo=UTC), datetime.datetime(2008, 1, 1, tzinfo=UTC)),
            (datetime.datetime(1999, 1, 1, tzinfo=UTC), datetime.datetime(2000, 1, 1, tzinfo=UTC)),
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 4: merge disjoint ranges
        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2010, 1, 2, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2010, 1, 2, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 5: merge ranges where part of them are contained within others
        dates = [
            (datetime.datetime(2005, 1, 1, tzinfo=UTC), datetime.datetime(2008, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2005, 10, 15, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2008, 1, 5, tzinfo=UTC), datetime.datetime(2009, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates)]
        expected = [
            (datetime.datetime(2005, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 6: min limit is not excluded but ranges are merged
        dates = [
            (datetime.datetime(2000, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC)),
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 7: max limit is not excluded but ranges are merged
        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2000, 1, 1, tzinfo=UTC)),
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 8: limit ranges are not excluded
        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 8a: min limit range is not excluded
        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2005, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2005, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 8b: max limit range is not excluded
        dates = [
            (datetime.datetime(2005, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates)]
        expected = [
            (datetime.datetime(2005, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

    def test_merge_duplicated_ranges(self):
        """Test if duplicated ranges are merged into one"""

        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC)),
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

    def test_merge_excluding_limits(self):
        """Test function with several case inputs when exclude_limits is set"""

        # Case 1: merge overlapped ranges excluding min and max limits
        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2008, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates, exclude_limits=True)]
        expected = [
            (datetime.datetime(2008, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 2: merge a range contained within other ranges excluding min and max limits
        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2010, 1, 2, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2008, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates, exclude_limits=True)]
        expected = [
            (datetime.datetime(2008, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2010, 1, 2, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 3: merge a set of ranges contained within another one excluding min and max limits
        dates = [
            (datetime.datetime(2006, 1, 1, tzinfo=UTC), datetime.datetime(2008, 1, 1, tzinfo=UTC)),
            (datetime.datetime(1999, 1, 1, tzinfo=UTC), datetime.datetime(2000, 1, 1, tzinfo=UTC)),
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates, exclude_limits=True)]
        expected = [
            (datetime.datetime(1999, 1, 1, tzinfo=UTC), datetime.datetime(2000, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2006, 1, 1, tzinfo=UTC), datetime.datetime(2008, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 4: merge disjoint ranges; as they are disjoint, limits are not excluded
        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2010, 1, 2, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates, exclude_limits=True)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2010, 1, 2, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 5: merge ranges where part of them are contained within others
        dates = [
            (datetime.datetime(2005, 1, 1, tzinfo=UTC), datetime.datetime(2008, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2005, 10, 15, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC)),
            (datetime.datetime(2008, 1, 5, tzinfo=UTC), datetime.datetime(2009, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates, exclude_limits=True)]
        expected = [
            (datetime.datetime(2005, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 6: min limit is excluded and ranges are merged
        dates = [
            (datetime.datetime(2000, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC)),
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates, exclude_limits=True)]
        expected = [
            (datetime.datetime(2000, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 7: max limit is excluded and ranges are merged
        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2000, 1, 1, tzinfo=UTC)),
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates, exclude_limits=True)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2000, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 8: limit ranges are not excluded
        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates, exclude_limits=True)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 8a: min limit range is not excluded
        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2005, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates, exclude_limits=True)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2005, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

        # Case 8b: max limit range is not excluded
        dates = [
            (datetime.datetime(2005, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates, exclude_limits=True)]
        expected = [
            (datetime.datetime(2005, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

    def test_merge_duplicated_ranges_excluding_limits(self):
        """Test if duplicated ranges are merged excluding limits"""

        # On this case, limits will not be excluded due to there is only one range
        dates = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC)),
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]

        ranges = [r for r in merge_datetime_ranges(dates, exclude_limits=True)]
        expected = [
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC))
        ]
        self.assertListEqual(ranges, expected)

    def test_none_list_of_dates(self):
        """Check if the result is empty when the list of ranges is None"""

        ranges = [r for r in merge_datetime_ranges(None)]
        self.assertEqual(ranges, [])

    def test_empty_list_of_dates(self):
        """Check if the result is empty when the list of ranges is empty"""

        ranges = [r for r in merge_datetime_ranges([])]
        self.assertEqual(ranges, [])

    def test_dates_out_of_bounds(self):
        """Check whether it raises an exception when dates are out of bounds"""

        # Case 1
        dates = [
            (datetime.datetime(2008, 1, 1, tzinfo=UTC), datetime.datetime(2100, 1, 1, tzinfo=UTC)),
            (datetime.datetime(1800, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC))
        ]

        expected = DATE_OUT_OF_BOUNDS_ERROR.format(type='start',
                                                   date=r'1800-01-01 00:00:00\+00:00')
        with self.assertRaisesRegexp(ValueError, expected):
            _ = [r for r in merge_datetime_ranges(dates)]

        # Case 2
        dates = [
            (datetime.datetime(2008, 1, 1, tzinfo=UTC), datetime.datetime(2100, 2, 1, tzinfo=UTC)),
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC))
        ]

        expected = DATE_OUT_OF_BOUNDS_ERROR.format(type='end',
                                                   date=r'2100-02-01 00:00:00\+00:00')
        with self.assertRaisesRegexp(ValueError, expected):
            _ = [r for r in merge_datetime_ranges(dates)]

    def test_dates_no_timezone(self):
        """Check whether it raises an exception when dates without timezone are given"""

        # Case 1
        dates = [
            (datetime.datetime(2008, 1, 1), datetime.datetime(2100, 1, 1, tzinfo=UTC)),
            (datetime.datetime(1800, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1, tzinfo=UTC))
        ]

        with self.assertRaisesRegexp(TypeError, CANT_COMPARE_DATES_ERROR):
            _ = [r for r in merge_datetime_ranges(dates)]

        # Case 2
        dates = [
            (datetime.datetime(2008, 1, 1, tzinfo=UTC), datetime.datetime(2100, 2, 1, tzinfo=UTC)),
            (datetime.datetime(1900, 1, 1, tzinfo=UTC), datetime.datetime(2010, 1, 1))
        ]

        with self.assertRaisesRegexp(TypeError, CANT_COMPARE_DATES_ERROR):
            _ = [r for r in merge_datetime_ranges(dates)]


class TestValidateField(TestCase):
    """Unit tests for validate_field"""

    def test_validate_string(self):
        """Check valid fields"""

        # If the field is valid, the method does not raise any exception
        validate_field('test_field', 'Test')

    def test_invalid_string(self):
        """Check invalid string fields"""

        expected = FIELD_EMPTY_ERROR.format(name='test_field')
        with self.assertRaisesRegex(ValueError, expected):
            validate_field('test_field', '')

        expected = FIELD_WHITESPACES_ERROR.format(name='test_field')
        with self.assertRaisesRegex(ValueError, expected):
            validate_field('test_field', '\t')

        expected = FIELD_WHITESPACES_ERROR.format(name='test_field')
        with self.assertRaisesRegex(ValueError, expected):
            validate_field('test_field', '  \t ')

    def test_allow_none(self):
        """Check valid and invalid fields allowing `None` values"""

        validate_field('test_field', None, allow_none=True)

        expected = FIELD_NONE_ERROR.format(name='test_field')
        with self.assertRaisesRegex(ValueError, expected):
            validate_field('test_field', None, allow_none=False)

        expected = FIELD_EMPTY_ERROR.format(name='test_field')
        with self.assertRaisesRegex(ValueError, expected):
            validate_field('test_field', '', allow_none=True)

        expected = FIELD_WHITESPACES_ERROR.format(name='test_field')
        with self.assertRaisesRegex(ValueError, expected):
            validate_field('test_field', ' \t ', allow_none=True)

    def test_no_string(self):
        """Check if an exception is raised when the value type is not a string"""

        with self.assertRaisesRegex(TypeError, FIELD_TYPE_ERROR):
            validate_field('test_field', 42)
