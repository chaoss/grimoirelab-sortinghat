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

from sortinghat.api import add_organization, add_domain
from sortinghat.cmd.organizations import Organizations
from sortinghat.db.database import Database

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


REGISTRY_NOT_FOUND_ERROR = "Error: Bitergium not found in the registry"
REGISTRY_EMPTY_OUTPUT = ""
REGISTRY_OUTPUT = """Bitergia    bitergia.net
Bitergia    bitergia.com
Example    example.com
Example    example.org
Example    example.net
LibreSoft"""


class TestOrgsRegistry(unittest.TestCase):

    def setUp(self):
        # Create a dataset to test the registry
        self.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

        add_organization(self.db, 'Example')
        add_domain(self.db, 'Example', 'example.com')
        add_domain(self.db, 'Example', 'example.org')
        add_domain(self.db, 'Example', 'example.net')

        add_organization(self.db, 'Bitergia')
        add_domain(self.db, 'Bitergia', 'bitergia.net')
        add_domain(self.db, 'Bitergia', 'bitergia.com')

        add_organization(self.db, 'LibreSoft')

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' :DB_NAME,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Organizations(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def test_registry(self):
        """Check registry output list"""

        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        self.cmd.registry()
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_OUTPUT)

    def test_not_found_organization(self):
        """Check whether it prints an error for not existing organizations"""

        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        self.cmd.registry('Bitergium')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_NOT_FOUND_ERROR)

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Delete the contents of the database
        self.db.clear()

        self.cmd.registry()
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, REGISTRY_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
