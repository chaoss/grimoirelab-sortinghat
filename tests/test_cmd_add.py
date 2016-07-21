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

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.add import Add
from sortinghat.exceptions import (CODE_ALREADY_EXISTS_ERROR,
                                   CODE_MATCHER_NOT_SUPPORTED_ERROR,
                                   CODE_NOT_FOUND_ERROR,
                                   CODE_VALUE_ERROR)

from tests.base import TestCommandCaseBase


ADD_EXISTING_ERROR = "Error: scm-jsmith@example.com-John Smith-jsmith already exists in the registry"
ADD_IDENTITY_NONE_OR_EMPTY_ERROR = "Error: identity data cannot be None or empty"
ADD_MATCHING_ERROR = "Error: mock identity matcher is not supported"
ADD_SOURCE_NONE_ERROR = "Error: source cannot be None"
ADD_SOURCE_EMPTY_ERROR = "Error: source cannot be an empty string"
ADD_UUID_NOT_FOUND_ERROR = "Error: FFFFFFFFFFFFFFF not found in the registry"

ADD_OUTPUT = """New identity 0b7c0ba5f9fc01e4799d684e0a1c3561b53d93d5 added to 0b7c0ba5f9fc01e4799d684e0a1c3561b53d93d5
New identity fef873c50a48cfc057f7aa19f423f81889a8907f added to fef873c50a48cfc057f7aa19f423f81889a8907f
New identity 7367d83759d7b12790d0a44bf615c5215aa867d4 added to 7367d83759d7b12790d0a44bf615c5215aa867d4
New identity 02f161840469eb5348dec798166a171b34f0bc8a added to 03e12d00e37fd45593c49a5a5a1652deca4cf302"""

ADD_OUTPUT_MATCHING = """New identity 02f161840469eb5348dec798166a171b34f0bc8a added to 02f161840469eb5348dec798166a171b34f0bc8a

New match found

+ 02f161840469eb5348dec798166a171b34f0bc8a
  * -\tjsmith@example.com\t-\tmls

+ 03e12d00e37fd45593c49a5a5a1652deca4cf302
  * John Smith\tjsmith@example.com\tjsmith\tscm
Unique identity 02f161840469eb5348dec798166a171b34f0bc8a merged on 03e12d00e37fd45593c49a5a5a1652deca4cf302

New match found

+ 03e12d00e37fd45593c49a5a5a1652deca4cf302
  * -\tjsmith@example.com\t-\tmls
  * John Smith\tjsmith@example.com\tjsmith\tscm

+ 75d95d6c8492fd36d24a18bd45d62161e05fbc97
  * John Smith\tjsmith@example.com\t-\tscm
Unique identity 03e12d00e37fd45593c49a5a5a1652deca4cf302 merged on 75d95d6c8492fd36d24a18bd45d62161e05fbc97"""

ADD_OUTPUT_BLACKLIST = """New identity 1be5376d8d87bc3a391459a18ec0b41d1c8080d5 added to 1be5376d8d87bc3a391459a18ec0b41d1c8080d5

New match found

+ 1be5376d8d87bc3a391459a18ec0b41d1c8080d5
  * John Smith\tjsmith@example.com\t-\tunknown

+ 03e12d00e37fd45593c49a5a5a1652deca4cf302
  * John Smith\tjsmith@example.com\tjsmith\tscm
Unique identity 1be5376d8d87bc3a391459a18ec0b41d1c8080d5 merged on 03e12d00e37fd45593c49a5a5a1652deca4cf302

New match found

+ 03e12d00e37fd45593c49a5a5a1652deca4cf302
  * John Smith\tjsmith@example.com\tjsmith\tscm
  * John Smith\tjsmith@example.com\t-\tunknown

+ 75d95d6c8492fd36d24a18bd45d62161e05fbc97
  * John Smith\tjsmith@example.com\t-\tscm
Unique identity 03e12d00e37fd45593c49a5a5a1652deca4cf302 merged on 75d95d6c8492fd36d24a18bd45d62161e05fbc97
New identity 24769e96010fa84fd7af86586c3eb6090e66e319 added to 24769e96010fa84fd7af86586c3eb6090e66e319
New identity 9ba1f605f3621fa10d98335ddad36b77b57fae99 added to 9ba1f605f3621fa10d98335ddad36b77b57fae99"""


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

        # Assign to John Smith - 03e12d00e37fd45593c49a5a5a1652deca4cf302
        # unique identity
        code = self.cmd.run('--email', 'jsmith@example.com', '--source', 'mls',
                            '--uuid', '03e12d00e37fd45593c49a5a5a1652deca4cf302')
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
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, ADD_OUTPUT_MATCHING)


class TestAdd(TestAddCaseBase):
    """Unit tests for add"""

    def test_add_new_identities(self):
        """Check if everything goes OK when adding a set of new identities"""

        self.cmd.add('scm', 'jroe@example.com', 'Jane Roe', 'jrae')
        self.cmd.add('scm', 'jroe@example.com')
        self.cmd.add('unknown', 'jroe@example.com')

        # Add this identity to 'Jonh Smith' - 03e12d00e37fd45593c49a5a5a1652deca4cf302
        code = self.cmd.add('mls', email='jsmith@example.com',
                            uuid='03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(code, CMD_SUCCESS)

        # Check output first
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, ADD_OUTPUT)

    def test_non_existing_uuid(self):
        """Check if it fails adding identities to unique identities that do not exist"""

        code = self.cmd.add('scm', email='jroe@example.com', uuid='FFFFFFFFFFFFFFF')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, ADD_UUID_NOT_FOUND_ERROR)

    def test_existing_identity(self):
        """Check if it fails adding an identity that already exists"""

        code = self.cmd.add('scm', 'jsmith@example.com', 'John Smith', 'jsmith')
        self.assertEqual(code, CODE_ALREADY_EXISTS_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, ADD_EXISTING_ERROR)

    def test_none_or_empty_source(self):
        """Check whether new identities cannot be added when giving a None or empty source"""

        code = self.cmd.add(None)
        self.assertEqual(code, CODE_VALUE_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, ADD_SOURCE_NONE_ERROR)

        code = self.cmd.add('')
        self.assertEqual(code, CODE_VALUE_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, ADD_SOURCE_EMPTY_ERROR)

    def test_none_or_empty_data(self):
        """Check whether new identities cannot be added when identity data is None or empty"""

        code = self.cmd.add('scm', None, '', None)
        self.assertEqual(code, CODE_VALUE_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, ADD_IDENTITY_NONE_OR_EMPTY_ERROR)

        code = self.cmd.add('scm', '', '', '')
        self.assertEqual(code, CODE_VALUE_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, ADD_IDENTITY_NONE_OR_EMPTY_ERROR)

    def test_invalid_matching_method(self):
        """Check if it fails when an invalid matching method is given"""

        code = self.cmd.add('scm', 'jsmith@example.com', matching='mock')
        self.assertEqual(code, CODE_MATCHER_NOT_SUPPORTED_ERROR)
        output = sys.stderr.getvalue().strip()
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
