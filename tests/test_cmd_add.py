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
from sortinghat.cmd.add import Add
from sortinghat.exceptions import (CODE_ALREADY_EXISTS_ERROR,
                                   CODE_MATCHER_NOT_SUPPORTED_ERROR,
                                   CODE_NOT_FOUND_ERROR,
                                   CODE_VALUE_ERROR)

from tests.base import TestCommandCaseBase


ADD_EXISTING_ERROR = "Error: unique identity 'a9b403e150dd4af8953a52a4bb841051e4b705d9' already exists in the registry"
ADD_IDENTITY_NONE_OR_EMPTY_ERROR = "Error: identity data cannot be None or empty"
ADD_MATCHING_ERROR = "Error: mock identity matcher is not supported"
ADD_SOURCE_NONE_ERROR = "Error: source cannot be None"
ADD_SOURCE_EMPTY_ERROR = "Error: source cannot be an empty string"
ADD_UUID_NOT_FOUND_ERROR = "Error: FFFFFFFFFFFFFFF not found in the registry"

ADD_OUTPUT = """New identity eda9f62ad321b1fbe5f283cc05e2484516203117 added to eda9f62ad321b1fbe5f283cc05e2484516203117
New identity 322397ed782a798ffd9d0bc7e293df4292fe075d added to 322397ed782a798ffd9d0bc7e293df4292fe075d
New identity d8647b37dc8f6c03936ec7f97a8c9a52bf6e01b7 added to d8647b37dc8f6c03936ec7f97a8c9a52bf6e01b7
New identity ffefc2e3f2a255e9450ac9e2d36f37c28f51bd73 added to a9b403e150dd4af8953a52a4bb841051e4b705d9"""

ADD_OUTPUT_MATCHING = """New identity ffefc2e3f2a255e9450ac9e2d36f37c28f51bd73 added to ffefc2e3f2a255e9450ac9e2d36f37c28f51bd73

New match found

+ ffefc2e3f2a255e9450ac9e2d36f37c28f51bd73
  * -\tjsmith@example.com\t-\tmls

+ 880b3dfcb3a08712e5831bddc3dfe81fc5d7b331
  * John Smith\tjsmith@example.com\t-\tscm
Unique identity ffefc2e3f2a255e9450ac9e2d36f37c28f51bd73 merged on 880b3dfcb3a08712e5831bddc3dfe81fc5d7b331

New match found

+ 880b3dfcb3a08712e5831bddc3dfe81fc5d7b331
  * John Smith\tjsmith@example.com\t-\tscm
  * -\tjsmith@example.com\t-\tmls

+ a9b403e150dd4af8953a52a4bb841051e4b705d9
  * John Smith\tjsmith@example.com\tjsmith\tscm
Unique identity 880b3dfcb3a08712e5831bddc3dfe81fc5d7b331 merged on a9b403e150dd4af8953a52a4bb841051e4b705d9"""

ADD_OUTPUT_BLACKLIST = """New identity c481adf086d486418e08e76bf9378db7573e25c9 added to c481adf086d486418e08e76bf9378db7573e25c9

New match found

+ c481adf086d486418e08e76bf9378db7573e25c9
  * John Smith\tjsmith@example.com\t-\tunknown

+ 880b3dfcb3a08712e5831bddc3dfe81fc5d7b331
  * John Smith\tjsmith@example.com\t-\tscm
Unique identity c481adf086d486418e08e76bf9378db7573e25c9 merged on 880b3dfcb3a08712e5831bddc3dfe81fc5d7b331

New match found

+ 880b3dfcb3a08712e5831bddc3dfe81fc5d7b331
  * John Smith\tjsmith@example.com\t-\tscm
  * John Smith\tjsmith@example.com\t-\tunknown

+ a9b403e150dd4af8953a52a4bb841051e4b705d9
  * John Smith\tjsmith@example.com\tjsmith\tscm
Unique identity 880b3dfcb3a08712e5831bddc3dfe81fc5d7b331 merged on a9b403e150dd4af8953a52a4bb841051e4b705d9
New identity d53a33722a47de80cf7adcedcd4a50bc4a4a1639 added to d53a33722a47de80cf7adcedcd4a50bc4a4a1639
New identity 18f8e6d693a2b71157bfa579cc623718b29e3240 added to 18f8e6d693a2b71157bfa579cc623718b29e3240"""


class TestAddCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on add unit tests"""

    cmd_klass = Add

    def load_test_dataset(self):
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         'John Smith')


class TestAddCommand(TestAddCaseBase):
    """Add command unit tests"""

    def test_add(self):
        """Check how it works when adding identities"""

        # Create new identities
        self.cmd.run('--name', 'Jane Roe', '--email', 'jroe@example.com',
                     '--username', 'jrae', '--source', 'scm')
        self.cmd.run('--email', 'jroe@example.com', '--source', 'scm')

        # Source set to default value 'unknown'
        self.cmd.run('--email', 'jroe@example.com')

        # Assign to John Smith - a9b403e150dd4af8953a52a4bb841051e4b705d9
        # unique identity
        code = self.cmd.run('--email', 'jsmith@example.com', '--source', 'mls',
                            '--uuid', 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(code, CMD_SUCCESS)

        # Check output
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, ADD_OUTPUT)

    def test_add_with_matching(self):
        """Check how it works when using matching methods"""

        code = self.cmd.run('--email', 'jsmith@example.com', '--source', 'mls',
                            '--matching', 'default')
        self.assertEqual(code, CMD_SUCCESS)

        # Check output
        x = sys.stdout.getvalue()
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, ADD_OUTPUT_MATCHING)


class TestAdd(TestAddCaseBase):
    """Unit tests for add"""

    def test_add_new_identities(self):
        """Check if everything goes OK when adding a set of new identities"""

        self.cmd.add('scm', 'jroe@example.com', 'Jane Roe', 'jrae')
        self.cmd.add('scm', 'jroe@example.com')
        self.cmd.add('unknown', 'jroe@example.com')

        # Add this identity to 'Jonh Smith' - a9b403e150dd4af8953a52a4bb841051e4b705d9
        code = self.cmd.add('mls', email='jsmith@example.com',
                            uuid='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(code, CMD_SUCCESS)

        # Check output first
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, ADD_OUTPUT)

    def test_non_existing_uuid(self):
        """Check if it fails adding identities to unique identities that do not exist"""

        code = self.cmd.add('scm', email='jroe@example.com', uuid='FFFFFFFFFFFFFFF')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)

        output = sys.stderr.getvalue().strip('\n').strip()
        self.assertEqual(output, ADD_UUID_NOT_FOUND_ERROR)

    def test_existing_identity(self):
        """Check if it fails adding an identity that already exists"""

        code = self.cmd.add('scm', 'jsmith@example.com', 'John Smith', 'jsmith')
        self.assertEqual(code, CODE_ALREADY_EXISTS_ERROR)
        output = sys.stderr.getvalue().strip('\n').strip()
        self.assertEqual(output, ADD_EXISTING_ERROR)

        # Different case letters, but same identity
        code = self.cmd.add('scm', 'jsmith@example.com', 'john smith', 'jsmith')
        self.assertEqual(code, CODE_ALREADY_EXISTS_ERROR)
        output = sys.stderr.getvalue().strip('\n').split('\n')[-1]
        self.assertEqual(output, ADD_EXISTING_ERROR)

        # Different accents, but same identity
        code = self.cmd.add('scm', 'jsmith@example.com', 'Jöhn Smith', 'jsmith')
        self.assertEqual(code, CODE_ALREADY_EXISTS_ERROR)
        output = sys.stderr.getvalue().strip('\n').split('\n')[-1]
        self.assertEqual(output, ADD_EXISTING_ERROR)

    def test_none_or_empty_source(self):
        """Check whether new identities cannot be added when giving a None or empty source"""

        code = self.cmd.add(None)
        self.assertEqual(code, CODE_VALUE_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, ADD_SOURCE_NONE_ERROR)

        code = self.cmd.add('')
        self.assertEqual(code, CODE_VALUE_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[-1]
        self.assertEqual(output, ADD_SOURCE_EMPTY_ERROR)

    def test_none_or_empty_data(self):
        """Check whether new identities cannot be added when identity data is None or empty"""

        code = self.cmd.add('scm', None, '', None)
        self.assertEqual(code, CODE_VALUE_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[-1]
        self.assertEqual(output, ADD_IDENTITY_NONE_OR_EMPTY_ERROR)

        code = self.cmd.add('scm', '', '', '')
        self.assertEqual(code, CODE_VALUE_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[-1]
        self.assertEqual(output, ADD_IDENTITY_NONE_OR_EMPTY_ERROR)

    def test_invalid_matching_method(self):
        """Check if it fails when an invalid matching method is given"""

        code = self.cmd.add('scm', 'jsmith@example.com', matching='mock')
        self.assertEqual(code, CODE_MATCHER_NOT_SUPPORTED_ERROR)
        output = sys.stderr.getvalue().strip('\n').strip()
        self.assertEqual(output, ADD_MATCHING_ERROR)

    def test_default_matching_method(self):
        """Check whether new identities are merged using the default matching method"""

        # Add this identity to 'Jonh Smith' and merge
        code = self.cmd.add('mls', email='jsmith@example.com', matching='default')
        self.assertEqual(code, CMD_SUCCESS)

        # Check output
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, ADD_OUTPUT_MATCHING)

    def test_default_matching_method_with_blacklist(self):
        """Check whether new identities are merged using a blacklist"""

        # Add some entries to the blacklist
        api.add_to_matching_blacklist(self.db, 'John Smith')
        api.add_to_matching_blacklist(self.db, 'jrae@example.com')

        # Add this identity to 'Jonh Smith' and merge
        code = self.cmd.add('unknown', name='John Smith', email='jsmith@example.com',
                            matching='default')
        self.assertEqual(code, CMD_SUCCESS)

        # These two will not match due to the blacklist
        code1 = self.cmd.add('scm', name='Jane Rae', email='jrae@example.com',
                             matching='default')
        code2 = self.cmd.add('mls', name='Jane Rae', email='jrae@example.com',
                             matching='default')
        self.assertEqual(code1, CMD_SUCCESS)
        self.assertEqual(code2, CMD_SUCCESS)

        # Check output
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, ADD_OUTPUT_BLACKLIST)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
