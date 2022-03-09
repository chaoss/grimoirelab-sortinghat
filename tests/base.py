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
import os.path
import sys
import unittest

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat.db.database import Database

__dir__ = os.path.dirname(os.path.realpath(__file__))
__datadir__ = os.path.join(__dir__, 'data')
CONFIG_FILE = os.path.join(__dir__, 'tests.conf')


def datadir(filename):
    """Return the path of the file in the tests data dir"""

    return(os.path.join(__datadir__, filename))


class TestDatabaseCaseBase(unittest.TestCase):
    """Defines common setup and teardown methods for database-based tests.

    When a class inherits from this one and it is instantiated,
    it creates a connection to the test database. This connection
    will be useful to check the contents of the registry during
    the tests. Any content of the database will be removed after
    the connection is reated and before and after of any unit test.
    Additionally, if 'create' is True in the configuration file,
    a new database will be created, and dropped when the class is done.

    Classes that inherit from this must implement `load_test_dataset`
    method. This method is called before any unit test is run.
    """
    @classmethod
    def setUpClass(cls):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        cls.db_kwargs = {'user': config['Database']['user'],
                         'password': config['Database']['password'],
                         'database': config['Database']['name'],
                         'host': config['Database']['host'],
                         'port': config['Database']['port']}
        if 'create' in config['Database']:
            cls.create = config['Database'].getboolean('create')
        else:
            cls.create = False
        if cls.create:
            Database.create(**cls.db_kwargs)
        cls.db = Database(**cls.db_kwargs)
        cls.db.clear()

    @classmethod
    def tearDownClass(cls):
        if cls.create:
            Database.drop(**cls.db_kwargs)

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

        cls.cmd = cls.cmd_klass(**cls.db_kwargs)

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue') and not hasattr(sys.stderr, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')
        super(TestCommandCaseBase, self).setUp()

    def load_test_dataset(self):
        raise NotImplementedError
