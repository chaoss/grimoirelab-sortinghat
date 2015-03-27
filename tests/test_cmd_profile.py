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

import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.cmd.profile import Profile
from sortinghat.db.database import Database
from sortinghat.db.model import Country

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


PROFILE_UUID_NOT_FOUND_ERROR = "Error: FFFFFFFFFFFFFFF not found in the registry"
PROFILE_COUNTRY_NOT_FOUND_ERROR = "Error: country code ES not found in the registry"

PROFILE_OUTPUT = """unique identity 52e0aa0a14826627e633fd15332988686b730ab3

Profile:
    * Name: Jane Roe
    * E-Mail: jroe@example.com
    * Bot: Yes
    * Country: US - United States of America
unique identity 52e0aa0a14826627e633fd15332988686b730ab3

Profile:
    * Name: Jane Roe
    * E-Mail: jroe@example.com
    * Bot: No
    * Country: US - United States of America"""

PROFILE_UUID_OUTPUT = """unique identity 52e0aa0a14826627e633fd15332988686b730ab3

Profile:
    * Name: -
    * E-Mail: -
    * Bot: No
    * Country: -"""


class TestBaseCase(unittest.TestCase):
    """Defines common setup and teardown methods on profile unit tests"""

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create a connection to check the contents of the registry
        self.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

        # Import predefined dataset for testing
        self._load_test_dataset()

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' :DB_NAME,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Profile(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def _load_test_dataset(self):
        # Add country
        with self.db.connect() as session:
            # Add a country
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)

        # Add identity
        api.add_identity(self.db, 'scm', 'jroe@example.com',
                         'Jane Roe', 'jroe')


class TestProfileCommand(TestBaseCase):
    """Unit tests for profile command"""

    def test_profile(self):
        """Check profile output"""

        self.cmd.run('52e0aa0a14826627e633fd15332988686b730ab3',
                     '--name', 'Jane Roe', '--email', 'jroe@example.com',
                     '--bot', '--country', 'US')

        self.cmd.run('52e0aa0a14826627e633fd15332988686b730ab3',
                     '--no-bot')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, PROFILE_OUTPUT)

    def test_profile_uuid(self):
        """Check profile output using a uuid"""

        self.cmd.run('52e0aa0a14826627e633fd15332988686b730ab3')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, PROFILE_UUID_OUTPUT)

    def test_not_found_uuid(self):
        """Check whether it raises an error when the uiid is not available"""

        self.cmd.run('FFFFFFFFFFFFFFF')
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, PROFILE_UUID_NOT_FOUND_ERROR)

    def test_not_found_country(self):
        """Check whether it raises an error when the code country is not available"""

        self.cmd.run('52e0aa0a14826627e633fd15332988686b730ab3', '--country', 'ES')
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, PROFILE_COUNTRY_NOT_FOUND_ERROR)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
