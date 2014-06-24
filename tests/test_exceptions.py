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

import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat.exceptions import BaseError, AlreadyExistsError, NotFoundError


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
        self.assertEqual(u"Mock error without args", unicode(e))

    def test_subclass_args(self):
        """Check subclasses that require arguments"""

        e = MockErrorArgs(code=1, msg='Fatal error')

        self.assertEqual("Mock error with args. Error: 1 Fatal error",
                         str(e))
        self.assertEqual(u"Mock error with args. Error: 1 Fatal error",
                         unicode(e))

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
        self.assertEqual('example.com already exists in the registry',
                         str(e))
        self.assertEqual(u'example.com already exists in the registry',
                         unicode(e))

    def test_no_args(self):
        """Check whether it raises a KeyError exception when
        required parameters are not given"""
        kwargs = {}
        self.assertRaises(KeyError, AlreadyExistsError, **kwargs)


class TestNotFoundError(unittest.TestCase):

    def test_message(self):
        """Make sure that prints the correct error"""

        e = NotFoundError(entity='example.com')
        self.assertEqual('example.com not found in the registry',
                         str(e))
        self.assertEqual(u'example.com not found in the registry',
                         unicode(e))

    def test_no_args(self):
        """Check whether it raises a KeyError exception when
        required parameters are not given"""
        kwargs = {}
        self.assertRaises(KeyError, NotFoundError, **kwargs)


if __name__ == "__main__":
    unittest.main()
