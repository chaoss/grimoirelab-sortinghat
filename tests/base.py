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

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat.db.database import Database

from tests.config import (DB_USER,
                          DB_PASSWORD,
                          DB_NAME,
                          DB_HOST,
                          DB_PORT)


class TestDatabaseCaseBase(unittest.TestCase):
    """Defines common setup and teardown methods for database-based tests.

    When a class inherits from this one and it is instantiated,
    it creates a connection to the test database. This connection
    will be useful to check the contents of the registry during
    the tests. Any content of the database will be removed after
    the connection is reated and before and after of any unit test.

    Classes that inherit from this must implement `load_test_dataset`
    method. This method is called before any unit test is run.
    """
    @classmethod
    def setUpClass(cls):
        cls.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)
        cls.db.clear()

    def setUp(self):
        self.db.clear()
        self.load_test_dataset()

    def tearDown(self):
        self.db.clear()

    def load_test_dataset(self):
        raise NotImplementedError


class TestCommandCaseBase(TestDatabaseCaseBase):
    """Defines common setup and teardown methods for commands testing.

    To inherit from this class, a command class must be assigned to
    `cmd_klass`. Durint its instantiation, the class will instantiate
    the command class too.

    Classes that inherit from this must implement `load_test_dataset`
    method. This method is called before any unit test is run.
    """
    cmd_klass = None

    @classmethod
    def setUpClass(cls):
        super(TestCommandCaseBase, cls).setUpClass()

        kwargs = {'user' : DB_USER,
                  'password' : DB_PASSWORD,
                  'database' :DB_NAME,
                  'host' : DB_HOST,
                  'port' : DB_PORT}
        cls.cmd = cls.cmd_klass(**kwargs)

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue') and not hasattr(sys.stderr, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')
        super(TestCommandCaseBase, self).setUp()

    def load_test_dataset(self):
        raise NotImplementedError
