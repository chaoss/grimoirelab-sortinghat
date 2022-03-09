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

import configparser
import sys
import unittest
import uuid
import warnings

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.init import Init
from sortinghat.db.database import Database
from sortinghat.exceptions import CODE_DATABASE_ERROR, CODE_DATABASE_EXISTS, \
    CODE_VALUE_ERROR


DB_ACCESS_ERROR = r".+Access denied for user '%(user)s'@"
DB_EXISTS_ERROR = r".+Can't create database '%(database)s'; database exists \(err: 1007\)"

from tests.base import CONFIG_FILE


class TestInitCaseBase(unittest.TestCase):
    """Defines common setup and teardown methods on init unit tests"""

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue') and not hasattr(sys.stderr, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create temporal names for the registry
        self.name = 'tmp' + uuid.uuid4().hex
        self.name_reuse = 'tmp' + uuid.uuid4().hex

        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        # Create command
        self.kwargs = {'user': config['Database']['user'],
                       'password': config['Database']['password'],
                       'host': config['Database']['host'],
                       'port': config['Database']['port']}
        self.cmd = Init(database=self.name, **self.kwargs)
        self.cmd_reuse = Init(database=self.name_reuse, **self.kwargs)

    def tearDown(self):
        Database.drop(database=self.name, **self.kwargs)
        Database.drop(database=self.name_reuse, **self.kwargs)


class TestInitCommand(TestInitCaseBase):
    """Unit tests for init command"""

    def test_init(self):
        """Check registry initialization"""

        code = self.cmd.run(self.name)
        self.assertEqual(code, CMD_SUCCESS)

        db = Database(database=self.name, **self.kwargs)
        self.assertIsInstance(db, Database)

        # Check if the list of countries was loaded
        countries = api.countries(db)
        self.assertEqual(len(countries), 249)

    def test_connection_error(self):
        """Check connection errors"""

        kwargs = {
            'user': 'nouser',
            'password': 'nopassword',
            'database': None,
            'host': self.kwargs['host'],
            'port': self.kwargs['port']
        }

        cmd = Init(**kwargs)
        code = cmd.run(self.name)
        self.assertEqual(code, CODE_DATABASE_ERROR)

        with warnings.catch_warnings(record=True):
            output = sys.stderr.getvalue().strip()
            self.assertRegexpMatches(output,
                                     DB_ACCESS_ERROR % {'user': 'nouser'})

    def test_existing_db_error(self):
        """Check if it returns an error when tries to create the registry twice"""

        code1 = self.cmd.run(self.name)
        self.assertEqual(code1, CMD_SUCCESS)

        code2 = self.cmd.run(self.name)
        self.assertEqual(code2, CODE_DATABASE_EXISTS)

        # Context added to catch deprecation warnings raised on Python 3
        with warnings.catch_warnings(record=True):
            output = sys.stderr.getvalue().strip()
            self.assertRegexpMatches(output,
                                     DB_EXISTS_ERROR % {'database': self.name})

    def test_existing_db_reuse(self):
        """Check that no error is returned when creating the registry twice"""

        code1 = self.cmd_reuse.run('--reuse', self.name_reuse)
        self.assertEqual(code1, CMD_SUCCESS)

        code2 = self.cmd_reuse.run('--reuse', self.name_reuse)
        self.assertEqual(code2, CMD_SUCCESS)


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

        kwargs = {
            'user': 'nouser',
            'password': 'nopassword',
            'database': None,
            'host': self.kwargs['host'],
            'port': self.kwargs['port'],
            'reuse': False
        }

        cmd = Init(**kwargs)
        code = cmd.initialize(self.name)
        self.assertEqual(code, CODE_DATABASE_ERROR)

        # Context added to catch deprecation warnings raised on Python 3
        with warnings.catch_warnings(record=True):
            output = sys.stderr.getvalue().strip()
            self.assertRegexpMatches(output,
                                     DB_ACCESS_ERROR % {'user': 'nouser'})

    def test_existing_db_error(self):
        """Check if it returns an error when tries to create the registry twice"""

        code1 = self.cmd.initialize(self.name)
        self.assertEqual(code1, CMD_SUCCESS)

        code2 = self.cmd.initialize(self.name)
        self.assertEqual(code2, CODE_DATABASE_EXISTS)

        # Context added to catch deprecation warnings raised on Python 3
        with warnings.catch_warnings(record=True):
            output = sys.stderr.getvalue().strip()
            self.assertRegexpMatches(output,
                                     DB_EXISTS_ERROR % {'database': self.name})

    def test_existing_db_reuse(self):
        """Check reusing works as intended when registriy is "created" twice"""

        code1 = self.cmd_reuse.initialize(self.name_reuse, reuse=True)
        self.assertEqual(code1, CMD_SUCCESS)

        code2 = self.cmd_reuse.initialize(self.name_reuse, reuse=True)
        self.assertEqual(code2, CMD_SUCCESS)

        code3 = self.cmd_reuse.initialize(self.name, reuse=True)
        self.assertEqual(code3, CMD_SUCCESS)

    def test_invalid_name_error(self):
        """Check if it returns an error when an invalid database name is given"""

        code = self.cmd.initialize('invalid-name')
        self.assertEqual(code, CODE_VALUE_ERROR)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
