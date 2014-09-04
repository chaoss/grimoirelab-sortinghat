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

from sortinghat import api
from sortinghat.cmd.add import Add
from sortinghat.db.database import Database

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


ADD_EXISTING_ERROR = "Error: scm-jsmith@example.com-John Smith-jsmith already exists in the registry"
ADD_IDENTITY_NONE_OR_EMPTY_ERROR = "Error: identity data cannot be None or empty"
ADD_SOURCE_NONE_ERROR = "Error: source cannot be None"
ADD_SOURCE_EMPTY_ERROR = "Error: source cannot be an empty string"
ADD_UUID_NOT_FOUND_ERROR = "Error: FFFFFFFFFFFFFFF not found in the registry"

ADD_OUTPUT = """New identity added to 0b7c0ba5f9fc01e4799d684e0a1c3561b53d93d5
New identity added to fef873c50a48cfc057f7aa19f423f81889a8907f
New identity added to 7367d83759d7b12790d0a44bf615c5215aa867d4
New identity added to 03e12d00e37fd45593c49a5a5a1652deca4cf302"""


class TestBaseCase(unittest.TestCase):
    """Defines common setup and teardown methods on add unit tests"""

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue') and not hasattr(sys.stderr, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create a connection to check the contents of the registry
        self.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

        self._load_test_dataset()

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' :DB_NAME,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Add(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def _load_test_dataset(self):
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         'John Smith')

class TestAddCommand(TestBaseCase):
    """Add command unit tests"""

    def test_add(self):
        """Check how it works when adding identities"""

        # Create new identities
        self.cmd.run('--name', 'Jane Roe', '--email', 'jroe@example.com',
                     '--username', 'jrae', '--source', 'scm')
        self.cmd.run('--email', 'jroe@example.com', '--source', 'scm')

        # Source set to default value 'unknown'
        self.cmd.run('--email', 'jroe@example.com')

        # Assign to John Smith - 03e12d00e37fd45593c49a5a5a1652deca4cf302
        # unique identity
        self.cmd.run('--email', 'jsmith@example.com', '--source', 'mls',
                     '--uuid', '03e12d00e37fd45593c49a5a5a1652deca4cf302')

        # Check output first
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, ADD_OUTPUT)

class TestAdd(TestBaseCase):
    """Unit tests for add"""

    def test_add_new_identities(self):
        """Check if everything goes OK when adding a set of new identities"""

        self.cmd.add('scm', 'jroe@example.com', 'Jane Roe', 'jrae')
        self.cmd.add('scm', 'jroe@example.com')
        self.cmd.add('unknown', 'jroe@example.com')

        # Add this identity to 'Jonh Smith' - 03e12d00e37fd45593c49a5a5a1652deca4cf302
        self.cmd.add('mls', email='jsmith@example.com',
                     uuid='03e12d00e37fd45593c49a5a5a1652deca4cf302')

        # Check output first
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, ADD_OUTPUT)

    def test_non_existing_uuid(self):
        """Check if it fails adding identities to unique identities that do not exist"""

        self.cmd.add('scm', email='jroe@example.com', uuid='FFFFFFFFFFFFFFF')
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, ADD_UUID_NOT_FOUND_ERROR)

    def test_existing_identity(self):
        """Check if it fails adding an identity that already exists"""

        self.cmd.add('scm', 'jsmith@example.com', 'John Smith', 'jsmith')
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, ADD_EXISTING_ERROR)

    def test_none_or_empty_source(self):
        """Check whether new identities cannot be added when giving a None or empty source"""

        self.cmd.add(None)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, ADD_SOURCE_NONE_ERROR)

        self.cmd.add('')
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, ADD_SOURCE_EMPTY_ERROR)

    def test_none_or_empty_data(self):
        """Check whether new identities cannot be added when identity data is None or empty"""

        self.cmd.add('scm', None, '', None)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, ADD_IDENTITY_NONE_OR_EMPTY_ERROR)

        self.cmd.add('scm', '', '', '')
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, ADD_IDENTITY_NONE_OR_EMPTY_ERROR)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
