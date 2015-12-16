#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Bitergia
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

from __future__ import unicode_literals

import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat.exceptions import BaseError, AlreadyExistsError, BadFileFormatError,\
    DatabaseError, InvalidDateError, InvalidFormatError, LoadError,\
    MatcherNotSupportedError, NotFoundError


# Mock classes to test BaseError class
class MockErrorNoArgs(BaseError):
    message = "Mock error without args"


class MockErrorArgs(BaseError):
    message = "Mock error with args. Error: %(code)s %(msg)s"


class TestBaseError(unittest.TestCase):

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
        kwargs = {'code' : 1, 'error' : 'Fatal error'}
        self.assertRaises(KeyError, MockErrorArgs, **kwargs)


class TestAlreadyExistsError(unittest.TestCase):

    def test_message(self):
        """Make sure that prints the correct error"""

        e = AlreadyExistsError(entity='example.com')
        self.assertEqual(str(e),
                         "example.com already exists in the registry")

    def test_uuid_arg(self):
        """Test that uuid attribute is set when given as argument"""

        e = AlreadyExistsError(uuid='FFFFFFFFFFF', entity='FFFFFFFFFFF')
        self.assertEqual(str(e),
                         u"FFFFFFFFFFF already exists in the registry")
        self.assertEqual(e.uuid, 'FFFFFFFFFFF')

    def test_no_args(self):
        """Check whether it raises a KeyError exception when
        required parameters are not given"""

        kwargs = {}
        self.assertRaises(KeyError, AlreadyExistsError, **kwargs)


class TestBadFileFormatError(unittest.TestCase):

    def test_message(self):
        """Make sure that prints the correct error"""

        e = BadFileFormatError(cause='Invalid file format')
        self.assertEqual("Invalid file format", str(e))

    def test_no_args(self):
        """Check whether it raises a KeyError exception when
        required parameters are not given"""
        kwargs = {}
        self.assertRaises(KeyError, BadFileFormatError, **kwargs)


class TestDatabaseError(unittest.TestCase):

    def test_message(self):
        """Make sure that prints the correct error"""

        e = DatabaseError(error="Unknown database 'mydb'", code=1049)
        self.assertEqual("Unknown database 'mydb' (err: 1049)", str(e))

    def test_no_args(self):
        """Check whether it raises a KeyError exception when
        required parameters are not given"""
        kwargs = {}
        self.assertRaises(KeyError, DatabaseError, **kwargs)

        kwargs = {'error' : "Unknown database 'mydb'"}
        self.assertRaises(KeyError, DatabaseError, **kwargs)

        kwargs = {'code' : 1049}
        self.assertRaises(KeyError, DatabaseError, **kwargs)


class TestInvalidDateError(unittest.TestCase):

    def test_message(self):
        """Make sure that prints the correct error"""

        e = InvalidDateError(date='1900-13-01')
        self.assertEqual("1900-13-01 is not a valid date",
                         str(e))

    def test_no_args(self):
        """Check whether it raises a KeyError exception when
        required parameters are not given"""
        kwargs = {}
        self.assertRaises(KeyError, InvalidDateError, **kwargs)


class TestInvalidFormatError(unittest.TestCase):

    def test_message(self):
        """Make sure that prints the correct error"""

        e = InvalidFormatError(cause='error on line 10')
        self.assertEqual("error on line 10", str(e))

    def test_no_args(self):
        """Check whether it raises a KeyError exception when
        required parameters are not given"""
        kwargs = {}
        self.assertRaises(KeyError, InvalidFormatError, **kwargs)


class TestLoadError(unittest.TestCase):

    def test_message(self):
        """Make sure that prints the correct error"""

        e = LoadError(cause='Invalid json format')
        self.assertEqual("Invalid json format", str(e))

    def test_no_args(self):
        """Check whether it raises a KeyError exception when
        required parameters are not given"""
        kwargs = {}
        self.assertRaises(KeyError, LoadError, **kwargs)


class TestMatcherNotSupported(unittest.TestCase):

    def test_message(self):
        """Make sure that prints the correct error"""

        e = MatcherNotSupportedError(matcher='custom')
        self.assertEqual("custom identity matcher is not supported",
                         str(e))

    def test_no_args(self):
        """Check whether it raises a KeyError exception when
        required parameters are not given"""
        kwargs = {}
        self.assertRaises(KeyError, InvalidDateError, **kwargs)


class TestNotFoundError(unittest.TestCase):

    def test_message(self):
        """Make sure that prints the correct error"""

        e = NotFoundError(entity='example.com')
        self.assertEqual("example.com not found in the registry",
                         str(e))

    def test_no_args(self):
        """Check whether it raises a KeyError exception when
        required parameters are not given"""
        kwargs = {}
        self.assertRaises(KeyError, NotFoundError, **kwargs)


if __name__ == "__main__":
    unittest.main()
