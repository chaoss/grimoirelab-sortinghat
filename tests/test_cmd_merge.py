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

import datetime
import sys
import unittest

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.merge import Merge
from sortinghat.db.model import Country
from sortinghat.exceptions import CODE_NOT_FOUND_ERROR

from tests.base import TestCommandCaseBase


MERGE_FROM_UUID_NOT_FOUND_ERROR = "Error: Jane Rae not found in the registry"
MERGE_TO_UUID_NOT_FOUND_ERROR = "Error: Jane Doe not found in the registry"

MERGE_OUTPUT = """Unique identity John Doe merged on John Smith"""
MERGE_EMPTY_OUTPUT = ""


class TestMergeCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on merge unit tests"""

    cmd_klass = Merge

    def load_test_dataset(self):
        # Add country
        with self.db.connect() as session:
            # Add a country
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)

        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com', 'John Smith',
                         uuid='John Smith')
        api.edit_profile(self.db, 'John Smith', name='John Smith', is_bot=False)

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         uuid='John Doe')
        api.edit_profile(self.db, 'John Doe', email='jdoe@example.com', is_bot=True,
                         country_code='US')

        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_enrollment(self.db, 'John Doe', 'Example')

        api.add_organization(self.db, 'Bitergia')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia')
        api.add_enrollment(self.db, 'John Doe', 'Bitergia',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2000, 1, 1))

        api.add_organization(self.db, 'LibreSoft')


class TestMergeCommand(TestMergeCaseBase):
    """Merge command unit tests"""

    def test_merge(self):
        """Check how it works when merging unique identities"""

        # Remove an identity
        code = self.cmd.run('John Doe', 'John Smith')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, MERGE_OUTPUT)


class TestMerge(TestMergeCaseBase):
    """Unit tests for merge"""

    def test_merge(self):
        """Check behaviour merging two unique identities"""

        code = self.cmd.merge('John Doe', 'John Smith')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, MERGE_OUTPUT)

    def test_non_existing_unique_identities(self):
        """Check if it fails merging unique identities that do not exist"""

        code = self.cmd.merge('Jane Rae', 'John Smith')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, MERGE_FROM_UUID_NOT_FOUND_ERROR)

        code = self.cmd.merge('John Smith', 'Jane Doe')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[-1]
        self.assertEqual(output, MERGE_TO_UUID_NOT_FOUND_ERROR)

    def test_none_uuids(self):
        """Check behavior merging None uuids"""

        code = self.cmd.merge(None, 'John Smith')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.merge('John Smith', None)
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, MERGE_EMPTY_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, MERGE_EMPTY_OUTPUT)

    def test_empty_uuids(self):
        """Check behavior merging empty uuids"""

        code = self.cmd.merge('', 'John Smith')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.merge('John Smith', '')
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, MERGE_EMPTY_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, MERGE_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
