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

import sys
import unittest

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.remove import Remove
from sortinghat.exceptions import CODE_NOT_FOUND_ERROR

from tests.base import TestCommandCaseBase


REMOVE_UUID_NOT_FOUND_ERROR = "Error: 25e1e0b7b9b154e7f3faffa95674a6ced22ddf6b not found in the registry"
REMOVE_ID_NOT_FOUND_ERROR = "Error: FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF not found in the registry"

REMOVE_UUID_OUTPUT = """Unique identity FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF removed"""
REMOVE_ID_OUTPUT = """Identity 25e1e0b7b9b154e7f3faffa95674a6ced22ddf6b removed"""
REMOVE_EMPTY_OUTPUT = ""


class TestRemoveCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on remove unit tests"""

    cmd_klass = Remove

    def load_test_dataset(self):
        api.add_unique_identity(self.db, 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         'John Smith', uuid='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        api.add_identity(self.db, 'scm', 'jsmith@example.net',
                         'John Smith', 'jsmith', uuid='FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

        api.add_identity(self.db, 'scm', 'jdoeh@example.com',
                         'John Doe', 'jdoe')


class TestRemoveCommand(TestRemoveCaseBase):
    """Remove command unit tests"""

    def test_remove(self):
        """Check how it works when removing unique identities and identities"""

        # Remove an identity (jsmith@example.net)
        code = self.cmd.run('--identity', '25e1e0b7b9b154e7f3faffa95674a6ced22ddf6b')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip('\n').split('\n')[0]
        self.assertEqual(output, REMOVE_ID_OUTPUT)

        # Remove a unique identity
        code = self.cmd.run('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip('\n').split('\n')[1]
        self.assertEqual(output, REMOVE_UUID_OUTPUT)


class TestRemove(TestRemoveCaseBase):
    """Unit tests for remove"""

    def test_remove_unique_identity(self):
        """Check behavior removing a unique identity"""

        code = self.cmd.remove('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REMOVE_UUID_OUTPUT)

    def test_remove_identity(self):
        """Check behavior removing an identity"""

        # Remove an identity (jsmith@example.net)
        code = self.cmd.remove('25e1e0b7b9b154e7f3faffa95674a6ced22ddf6b', identity=True)
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REMOVE_ID_OUTPUT)

    def test_non_existing_unique_identity(self):
        """Check if it fails removing a unique identities that do not exist"""

        # The given id is assigned to an identity, this test
        # should not remove anything
        code = self.cmd.remove('25e1e0b7b9b154e7f3faffa95674a6ced22ddf6b')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, REMOVE_UUID_NOT_FOUND_ERROR)

    def test_non_existing_identity(self):
        """Check if it fails removing an identity that do not exist"""

        # The given id is assigned to a unique identity, this test
        # should not remove anything
        code = self.cmd.remove('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF', identity=True)
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
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
