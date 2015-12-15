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

from __future__ import absolute_import

import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS, CMD_FAILURE
from sortinghat.cmd.remove import Remove
from sortinghat.db.database import Database

from .config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


REMOVE_UUID_NOT_FOUND_ERROR = "Error: 62cce16ac0a5c391b4e0c3ccb3e924d65de8c345 not found in the registry"
REMOVE_ID_NOT_FOUND_ERROR = "Error: FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF not found in the registry"

REMOVE_UUID_OUTPUT = """Unique identity FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF removed"""
REMOVE_ID_OUTPUT = """Identity 62cce16ac0a5c391b4e0c3ccb3e924d65de8c345 removed"""
REMOVE_EMPTY_OUTPUT = ""


class TestBaseCase(unittest.TestCase):
    """Defines common setup and teardown methods on add unit tests"""

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue') and not hasattr(sys.stderr, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create a connection to check the contents of the registry
        self.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

        self.db.clear()

        self._load_test_dataset()

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' :DB_NAME,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Remove(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def _load_test_dataset(self):
        api.add_unique_identity(self.db, 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         'John Smith', uuid='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        api.add_identity(self.db, 'scm', 'jsmith@example.net',
                         'John Smith', 'jsmith', uuid='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

        api.add_identity(self.db, 'scm', 'jdoeh@example.com',
                         'John Doe', 'jdoe')


class TestRemoveCommand(TestBaseCase):
    """Remove command unit tests"""

    def test_remove(self):
        """Check how it works when removing unique identities and identities"""

        # Remove an identity
        code = self.cmd.run('--identity', '62cce16ac0a5c391b4e0c3ccb3e924d65de8c345')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip('\n').split('\n')[0]
        self.assertEqual(output, REMOVE_ID_OUTPUT)

        # Remove a unique identity
        code = self.cmd.run('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip('\n').split('\n')[1]
        self.assertEqual(output, REMOVE_UUID_OUTPUT)


class TestRemove(TestBaseCase):
    """Unit tests for remove"""

    def test_remove_unique_identity(self):
        """Check behavior removing a unique identity"""

        code = self.cmd.remove('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REMOVE_UUID_OUTPUT)

    def test_remove_identity(self):
        """Check behavior removing an identity"""

        code = self.cmd.remove('62cce16ac0a5c391b4e0c3ccb3e924d65de8c345', identity=True)
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REMOVE_ID_OUTPUT)

    def test_non_existing_unique_identity(self):
        """Check if it fails removing a unique identities that do not exist"""

        # The given id is assigned to an identity, this test
        # should not remove anything
        code = self.cmd.remove('62cce16ac0a5c391b4e0c3ccb3e924d65de8c345')
        self.assertEqual(code, CMD_FAILURE)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, REMOVE_UUID_NOT_FOUND_ERROR)

    def test_non_existing_identity(self):
        """Check if it fails removing an identity that do not exist"""

        # The given id is assigned to a unique identity, this test
        # should not remove anything
        code = self.cmd.remove('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF', identity=True)
        self.assertEqual(code, CMD_FAILURE)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, REMOVE_ID_NOT_FOUND_ERROR)

    def test_none_uuid_or_id(self):
        """Check behavior removing None uuids"""

        code = self.cmd.remove(None)
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.remove(None, identity=True)
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REMOVE_EMPTY_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, REMOVE_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
