#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2024 Bitergia
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

from django.test import TestCase

from sortinghat.core.errors import (BaseError,
                                    AlreadyExistsError,
                                    InvalidFormatError,
                                    LoadError,
                                    NotFoundError,
                                    InvalidValueError,
                                    InvalidFilterError,
                                    EqualIndividualError,
                                    ClosedTransactionError,
                                    LockedIdentityError,
                                    DuplicateRangeError,
                                    JobError,
                                    RecommendationEngineError)


# Mock classes to test BaseError class
class MockCode(BaseError):
    _msg = "Mock error with code"
    code = 9314


class MockErrorNoArgs(BaseError):
    _msg = "Mock error without args"


class MockErrorArgs(BaseError):
    _msg = "Mock error with args. Error: %(code)s %(msg)s"


class TestBaseError(TestCase):
    """Unit tests for BaseError"""

    def test_int_code_casting(self):
        """Check if the error can be casted into an error code"""

        e = MockCode()
        self.assertEqual(int(e), 9314)

    def test_subblass_with_no_args(self):
        """Check subclasses that do not require arguments.

        Arguments passed to the constructor should be ignored.
        """
        e = MockErrorNoArgs(code=1, msg='Fatal error')

        self.assertEqual("Mock error without args", str(e))

    def test_subclass_args(self):
        """Check subclasses that require arguments"""

        e = MockErrorArgs(code=1, msg='Fatal error')

        self.assertEqual("Mock error with args. Error: 1 Fatal error",
                         str(e))

    def test_subclass_invalid_args(self):
        """Check when required arguments are not given.

        When this happens, it raises a KeyError exception.
        """
        kwargs = {'code': 1, 'error': 'Fatal error'}
        self.assertRaises(KeyError, MockErrorArgs, **kwargs)


class TestAlreadyExistsError(TestCase):
    """Unit tests for AlreadyExistsError"""

    def test_message(self):
        """Make sure it prints the right error"""

        e = AlreadyExistsError(entity='Domain', eid='example.com')
        self.assertEqual(str(e),
                         "Domain 'example.com' already exists in the registry")

    def test_args(self):
        """Test whether attributes are set when they are given as arguments"""

        e = AlreadyExistsError(entity='Individual', eid='FFFFFFFFFFF')
        self.assertEqual(str(e), "Individual 'FFFFFFFFFFF' already exists in the registry")
        self.assertEqual(e.entity, 'Individual')
        self.assertEqual(e.eid, 'FFFFFFFFFFF')

    def test_no_args(self):
        """Check when required arguments are not given"""

        kwargs = {}
        self.assertRaises(KeyError, AlreadyExistsError, **kwargs)


class TestInvalidFormatError(TestCase):
    """Unit tests for InvalidFormatError"""

    def test_message(self):
        """Make sure it prints the right error"""

        e = InvalidFormatError(cause="line 30: invalid format")
        self.assertEqual(str(e), "line 30: invalid format")

    def test_no_args(self):
        """Check when required arguments are not given"""

        kwargs = {}
        self.assertRaises(KeyError, InvalidFormatError, **kwargs)


class TestLoadError(TestCase):
    """Unit tests for LoadError"""

    def test_message(self):
        """Make sure it prints the right error"""

        e = LoadError(cause="Load error message")
        self.assertEqual(str(e), "Load error message")

    def test_no_args(self):
        """Check when required arguments are not given"""

        kwargs = {}
        self.assertRaises(KeyError, LoadError, **kwargs)


class TestNotFoundError(TestCase):
    """Unit tests for NotFoundError"""

    def test_message(self):
        """Make sure that prints the right error"""

        e = NotFoundError(entity='example.com')
        self.assertEqual("example.com not found in the registry",
                         str(e))

    def test_no_args(self):
        """Check when required arguments are not given.

        When this happens, it raises a KeyError exception.
        """
        kwargs = {}
        self.assertRaises(KeyError, NotFoundError, **kwargs)


class TestInvalidValueError(TestCase):
    """Unit tests for InvalidValueError"""

    def test_message(self):
        """Make sure that prints the right error"""

        e = InvalidValueError(msg="invalid value")
        self.assertEqual("invalid value", str(e))

    def test_no_args(self):
        """Check when required arguments are not given.

        When this happens, it raises a KeyError exception.
        """
        kwargs = {}
        self.assertRaises(KeyError, InvalidValueError, **kwargs)


class TestInvalidFilterError(TestCase):
    """Unit tests for InvalidFilterError"""

    def test_message(self):
        """Make sure that prints the right error"""

        e = InvalidFilterError(filter_name='example', msg="invalid filter")
        self.assertEqual("Error in example filter: invalid filter", str(e))

    def test_no_args(self):
        """Check when required arguments are not given.

        When this happens, it raises a KeyError exception.
        """
        kwargs = {}
        self.assertRaises(KeyError, InvalidFilterError, **kwargs)


class TestEqualIndividualError(TestCase):
    """Unit tests for EqualIndividualError"""

    def test_message(self):
        """Make sure that prints the right error"""

        e = EqualIndividualError(msg="'from_uuid' and 'to_uuid' cannot be equal")
        self.assertEqual("'from_uuid' and 'to_uuid' cannot be equal", str(e))

    def test_no_args(self):
        """Check when required arguments are not given.

        When this happens, it raises a KeyError exception.
        """
        kwargs = {}
        self.assertRaises(KeyError, EqualIndividualError, **kwargs)


class TestClosedTransactionError(TestCase):
    """Unit tests for ClosedTransactionError"""

    def test_message(self):
        """Make sure that prints the right error"""

        e = ClosedTransactionError(msg="transaction already closed")
        self.assertEqual("transaction already closed", str(e))

    def test_no_args(self):
        """Check when required arguments are not given.

        When this happens, it raises a KeyError exception.
        """
        kwargs = {}
        self.assertRaises(KeyError, ClosedTransactionError, **kwargs)


class TestLockedIdentityError(TestCase):
    """Unit tests for LockedIdentityError"""

    def test_message(self):
        """Make sure that prints the right error"""

        e = LockedIdentityError(uuid='0123456789abcdef')
        self.assertEqual("Individual 0123456789abcdef is locked", str(e))

    def test_no_args(self):
        """Check when required arguments are not given.

        When this happens, it raises a KeyError exception.
        """
        kwargs = {}
        self.assertRaises(KeyError, LockedIdentityError, **kwargs)


class TestEnrollmentRangeError(TestCase):
    """Unit tests for EnrollmentRangeError"""

    def test_message(self):
        """Make sure that prints the right error"""

        start = '2005-01-01 00:00:00+00:00'
        end = '2006-01-01 00:00:00+00:00'
        org = 'Example'
        e = DuplicateRangeError(start=start, end=end, group=org)
        msg = "range date '{}'-'{}' is part of an existing range for {}"
        msg = msg.format(start, end, org)
        self.assertEqual(msg, str(e))

    def test_no_args(self):
        """Check when required arguments are not given.

        When this happens, it raises a KeyError exception.
        """
        kwargs = {}
        self.assertRaises(KeyError, DuplicateRangeError, **kwargs)


class TestJobError(TestCase):
    """Unit tests for JobError"""

    def test_message(self):
        """Make sure that prints the right error"""

        e = JobError(msg="job error")
        self.assertEqual("job error", str(e))

    def test_no_args(self):
        """Check when required arguments are not given.

        When this happens, it raises a KeyError exception.
        """
        kwargs = {}
        self.assertRaises(KeyError, JobError,
                          **kwargs)


class TestRecommendationEngineError(TestCase):
    """Unit tests for RecommendationEngineError"""

    def test_message(self):
        """Make sure that prints the right error"""

        e = RecommendationEngineError(msg="invalid engine")
        self.assertEqual("invalid engine", str(e))

    def test_no_args(self):
        """Check when required arguments are not given.

        When this happens, it raises a KeyError exception.
        """
        kwargs = {}
        self.assertRaises(KeyError, RecommendationEngineError,
                          **kwargs)
