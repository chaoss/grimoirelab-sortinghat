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
from sortinghat.cmd.blacklist import Blacklist
from sortinghat.exceptions import (NotFoundError,
                                   CODE_ALREADY_EXISTS_ERROR,
                                   CODE_NOT_FOUND_ERROR)

from tests.base import TestCommandCaseBase


BLACKLIST_ALREADY_EXISTS_ERROR = "Error: root@example.com already exists in the registry"
BLACKLIST_NOT_FOUND_ERROR = "Error: root@example.net not found in the registry"
BLACKLIST_EMPTY_OUTPUT = ""

BLACKLIST_OUTPUT = """Bitergia
John Doe
John Smith
root@example.com"""

REGISTRY_OUTPUT_ALT = """Bitergia\tbitergia.net
Example\texample.com
Example\tbitergia.com
Example\texample.org
Example\texample.net
LibreSoft"""

BLACKLIST_OUTPUT_JOHN = """John Doe
John Smith"""

BLACKLIST_OUTPUT_ALT = """John Smith
root@example.com"""


class TestBlacklistCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on blacklist unit tests"""

    cmd_klass = Blacklist

    def load_test_dataset(self):
        pass


class TestBlacklistCommand(TestBlacklistCaseBase):
    """Blacklist command unit tests"""

    def load_test_dataset(self):
        self.cmd.add('root@example.com')
        self.cmd.add('John Smith')
        self.cmd.add('Bitergia')
        self.cmd.add('John Doe')

    def test_default_action(self):
        """Check whether when no action is given it runs --list"""

        code = self.cmd.run()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_OUTPUT)

    def test_list_without_args(self):
        """Test list action with and without arguments"""

        code = self.cmd.run('-l')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_OUTPUT)

    def test_list_with_args(self):
        """Test list action with arguments"""

        code = self.cmd.run('--list', 'ohn')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_OUTPUT_JOHN)

    def test_add_with_args(self):
        """Test add action"""

        # Remove pre-loaded dataset
        self.db.clear()

        code = self.cmd.run('--add', 'John Smith')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('-a', 'Bitergia')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('--add', 'John Doe')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('-a', 'root@example.com')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('--list')
        self.assertEqual(code, CMD_SUCCESS)

        # Check output
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_OUTPUT)

    def test_add_without_args(self):
        """Check when calling --add without args, it does not do anything"""

        # Remove pre-loaded dataset
        self.db.clear()

        code = self.cmd.run('--add')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('-l')
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_EMPTY_OUTPUT)

    def test_delete_with_args(self):
        """Test delete action"""

        # Delete contents
        code = self.cmd.run('--delete', 'Bitergia')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('-d', 'John Doe')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('--list')
        self.assertEqual(code, CMD_SUCCESS)

        # Check output
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_OUTPUT_ALT)

    def test_delete_without_args(self):
        """Check when calling --delete without args, it does not do anything"""

        code = self.cmd.run('--delete')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.run('-l')
        self.assertEqual(code, CMD_SUCCESS)

        # Check output
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_OUTPUT)

    def test_run_mixing_actions(self):
        """Check how it works when mixing actions"""

        # Remove pre-loaded dataset
        self.db.clear()

        self.cmd.run('--add', 'John Doe')
        self.cmd.run('-a', 'John Smith')
        self.cmd.run('-a', 'Example')
        self.cmd.run('--add', 'Bitergia')
        self.cmd.run('-d', 'Bitergia')
        self.cmd.run('--add', 'root@example.com')
        self.cmd.run('-a', 'root@example.net')
        self.cmd.run('--delete', 'John Doe')
        self.cmd.run('--delete', 'root@example.com')
        self.cmd.run('--add', 'root@example.com')
        self.cmd.run('-d', 'root@example.net')
        self.cmd.run('--delete', 'Example')
        self.cmd.run()

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_OUTPUT_ALT)


class TestAdd(TestBlacklistCaseBase):
    """Blacklist add sub-command unit tests"""

    def test_add(self):
        """Check whether everything works ok when adding entries"""

        self.cmd.add('root@example.com')
        self.cmd.add('John Smith')
        self.cmd.add('Bitergia')
        self.cmd.add('John Doe')

        # List the registry and check the output
        code = self.cmd.blacklist()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_OUTPUT)

    def test_existing_entry(self):
        """Check if it fails adding an entry that already exists"""

        code = self.cmd.add('root@example.com')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.add('root@example.com')
        self.assertEqual(code, CODE_ALREADY_EXISTS_ERROR)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, BLACKLIST_ALREADY_EXISTS_ERROR)

    def test_none_entry(self):
        """Check behavior adding None entries"""

        code = self.cmd.add(None)
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_EMPTY_OUTPUT)

        # The blacklist should be empty
        bl = api.blacklist(self.db)
        self.assertEqual(len(bl), 0)

    def test_empty_entry(self):
        """Check behavior adding empty organizations"""

        code = self.cmd.add('')
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_EMPTY_OUTPUT)

        # The blacklist should be empty
        bl = api.blacklist(self.db)
        self.assertEqual(len(bl), 0)


class TestDelete(TestBlacklistCaseBase):
    """Blacklist delete sub-command unit tests"""

    def test_delete(self):
        """Check whether everything works ok when deleting entries"""

        # First, add a set of entries
        self.cmd.add('root@example.com')
        self.cmd.add('John Smith')
        self.cmd.add('Bitergia')
        self.cmd.add('John Doe')

        # Delete an entry
        bl = api.blacklist(self.db, 'Bitergia')
        self.assertEqual(len(bl), 1)

        code = self.cmd.delete('Bitergia')
        self.assertEqual(code, CMD_SUCCESS)

        self.assertRaises(NotFoundError, api.blacklist,
                          self.db, 'Bitergia')

        code = self.cmd.delete('root@example.com')
        self.assertEqual(code, CMD_SUCCESS)

        # The final content of the registry should have
        # two entries
        bl = api.blacklist(self.db)
        self.assertEqual(len(bl), 2)

        e = bl[0]
        self.assertEqual(e.excluded, 'John Doe')

        e = bl[1]
        self.assertEqual(e.excluded, 'John Smith')

    def test_not_found_entry(self):
        """Check if it fails removing an entry that does not exists"""

        # It should print an error when the blacklist is empty
        code = self.cmd.delete('root@example.net')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, BLACKLIST_NOT_FOUND_ERROR)

        # Add a pair of entries to check delete with a blacklist
        # with contents
        self.cmd.add('John Smith')
        self.cmd.add('root@example.com')

        # The error should be the same
        code = self.cmd.delete('root@example.net')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip('\n').split('\n')[-1]
        self.assertEqual(output, BLACKLIST_NOT_FOUND_ERROR)

        # Nothing has been deleted from the registry
        bl = api.blacklist(self.db)
        self.assertEqual(len(bl), 2)


class TestBlacklist(TestBlacklistCaseBase):
    """Blacklist list sub-command unit tests"""

    def load_test_dataset(self):
        api.add_to_matching_blacklist(self.db, 'root@example.com')
        api.add_to_matching_blacklist(self.db, 'John Smith')
        api.add_to_matching_blacklist(self.db, 'Bitergia')
        api.add_to_matching_blacklist(self.db, 'John Doe')

    def test_blacklist(self):
        """Check blacklist output list"""

        code = self.cmd.blacklist()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_OUTPUT)

    def test_blacklist_term(self):
        """Check if it returns the info about entries using a search term"""

        code = self.cmd.blacklist('ohn')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_OUTPUT_JOHN)

    def test_not_found_term(self):
        """Check whether it prints an error for not existing entries"""

        code = self.cmd.blacklist('root@example.net')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, BLACKLIST_NOT_FOUND_ERROR)

    def test_empty_blacklist(self):
        """Check output when the blacklist is empty"""

        # Delete the contents of the database
        self.db.clear()

        code = self.cmd.blacklist()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, BLACKLIST_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
