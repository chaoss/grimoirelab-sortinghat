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

import datetime
import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.cmd.merge import Merge
from sortinghat.db.database import Database

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


MERGE_FROM_UUID_NOT_FOUND_ERROR = "Error: Jane Rae not found in the registry"
MERGE_TO_UUID_NOT_FOUND_ERROR = "Error: Jane Doe not found in the registry"

MERGE_OUTPUT = """Unique identity John Doe merged on John Smith"""
MERGE_EMPTY_OUTPUT = ""


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
        self.cmd = Merge(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def _load_test_dataset(self):
        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com', 'John Smith',
                         uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         uuid='John Doe')

        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_enrollment(self.db, 'John Doe', 'Example')

        api.add_organization(self.db, 'Bitergia')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia')
        api.add_enrollment(self.db, 'John Doe', 'Bitergia',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2000, 1, 1))

        api.add_organization(self.db, 'LibreSoft')


class TestMerge(TestBaseCase):
    """Unit tests for merge"""

    def test_merge(self):
        """Check behaviour merging two unique identities"""

        self.cmd.merge('John Doe', 'John Smith')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, MERGE_OUTPUT)

    def test_non_existing_unique_identities(self):
        """Check if it fails merging unique identities that do not exist"""

        self.cmd.merge('Jane Rae', 'John Smith')
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, MERGE_FROM_UUID_NOT_FOUND_ERROR)

        self.cmd.merge('John Smith', 'Jane Doe')
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, MERGE_TO_UUID_NOT_FOUND_ERROR)

    def test_none_uuids(self):
        """Check behavior merging None uuids"""

        self.cmd.merge(None, 'John Smith')
        self.cmd.merge('John Smith', None)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, MERGE_EMPTY_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, MERGE_EMPTY_OUTPUT)

    def test_empty_uuids(self):
        """Check behavior merging empty uuids"""

        self.cmd.merge('', 'John Smith')
        self.cmd.merge('John Smith', '')

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, MERGE_EMPTY_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, MERGE_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
