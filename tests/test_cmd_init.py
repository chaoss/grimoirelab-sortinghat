#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2016 Bitergia
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

from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import unittest
import uuid
import warnings

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.init import Init
from sortinghat.db.database import Database
from sortinghat.exceptions import CODE_DATABASE_ERROR

from tests.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT


DB_ACCESS_ERROR = r".+Access denied for user '%(user)s'@'localhost' \(using password: YES\)"
DB_EXISTS_ERROR = r".+Can't create database '%(database)s'; database exists \(err: 1007\)"


class TestInitCaseBase(unittest.TestCase):
    """Defines common setup and teardown methods on init unit tests"""

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue') and not hasattr(sys.stderr, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create a temporal name for the registry
        self.name = 'tmp' + uuid.uuid4().hex

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' : self.name,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Init(**self.kwargs)

    def tearDown(self):
        Database.drop(self.kwargs['user'], self.kwargs['password'],
                      self.name, self.kwargs['host'],
                      self.kwargs['port'])


class TestInitCommand(TestInitCaseBase):
    """Unit tests for init command"""

    def test_init(self):
        """Check registry initialization"""

        code = self.cmd.run(self.name)
        self.assertEqual(code, CMD_SUCCESS)

        db = Database(self.kwargs['user'], self.kwargs['password'], self.name,
                      self.kwargs['host'], self.kwargs['port'])
        self.assertIsInstance(db, Database)

        # Check if the list of countries was loaded
        countries = api.countries(db)
        self.assertEqual(len(countries), 249)

    def test_connection_error(self):
        """Check connection errors"""

        kwargs = {'user' : 'nouser',
                  'password' : 'nopassword',
                  'database' : None,
                  'host' : 'localhost',
                  'port' : '3306'}

        cmd = Init(**kwargs)
        code = cmd.run(self.name)
        self.assertEqual(code, CODE_DATABASE_ERROR)

        with warnings.catch_warnings(record=True):
            output = sys.stderr.getvalue().strip()
            self.assertRegexpMatches(output,
                                     DB_ACCESS_ERROR % {'user' : 'nouser'})

    def test_existing_db_error(self):
        """Check if it returns an error when tries to create the registry twice"""

        code1 = self.cmd.run(self.name)
        self.assertEqual(code1, CMD_SUCCESS)

        code2 = self.cmd.run(self.name)
        self.assertEqual(code2, CODE_DATABASE_ERROR)

        # Context added to catch deprecation warnings raised on Python 3
        with warnings.catch_warnings(record=True):
            output = sys.stderr.getvalue().strip()
            self.assertRegexpMatches(output,
                                     DB_EXISTS_ERROR % {'database' : self.name})


class TestInitialize(TestInitCaseBase):
    """Unit tests for init command"""

    def test_initialize(self):
        """Check registry initialization"""

        code = self.cmd.initialize(self.name)
        self.assertEqual(code, CMD_SUCCESS)

        db = Database(self.kwargs['user'], self.kwargs['password'], self.name,
                      self.kwargs['host'], self.kwargs['port'])
        self.assertIsInstance(db, Database)

        # Check if the list of countries was loaded
        countries = api.countries(db)
        self.assertEqual(len(countries), 249)

    def test_connection_error(self):
        """Check connection errors"""

        kwargs = {'user' : 'nouser',
                  'password' : 'nopassword',
                  'database' : None,
                  'host' : 'localhost',
                  'port' : '3306'}

        cmd = Init(**kwargs)
        code = cmd.initialize(self.name)
        self.assertEqual(code, CODE_DATABASE_ERROR)

        # Context added to catch deprecation warnings raised on Python 3
        with warnings.catch_warnings(record=True):
            output = sys.stderr.getvalue().strip()
            self.assertRegexpMatches(output,
                                     DB_ACCESS_ERROR % {'user' : 'nouser'})

    def test_existing_db_error(self):
        """Check if it returns an error when tries to create the registry twice"""

        code1 = self.cmd.initialize(self.name)
        self.assertEqual(code1, CMD_SUCCESS)

        code2 = self.cmd.initialize(self.name)
        self.assertEqual(code2, CODE_DATABASE_ERROR)

        # Context added to catch deprecation warnings raised on Python 3
        with warnings.catch_warnings(record=True):
            output = sys.stderr.getvalue().strip()
            self.assertRegexpMatches(output,
                                     DB_EXISTS_ERROR % {'database' : self.name})


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
