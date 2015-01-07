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
from sortinghat.cmd.affiliate import Affiliate
from sortinghat.db.database import Database

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


AFFILIATE_OUTPUT = """Unique identity 52e0aa0a14826627e633fd15332988686b730ab3 (jroe@example.com) affiliated to Example
Unique identity 52e0aa0a14826627e633fd15332988686b730ab3 (jroe@bitergia.com) affiliated to Bitergia
Unique identity 5b59daf41755fa6f65c1c85b0a75ca138c1baaa6 (jsmith@us.example.com) affiliated to Example"""

AFFILIATE_EMPTY_OUTPUT = ""

MULTIPLE_DOMAIN_RUNTIME_ERROR = "multiple top domains for %(domain)s sub-domain. Please fix it before continue"


class TestBaseCase(unittest.TestCase):
    """Defines common setup and teardown methods on affiliate unit tests"""

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
        self.cmd = Affiliate(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def _load_test_dataset(self):
        # Add some domains
        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com', is_top_domain=True)
        api.add_domain(self.db, 'Example', 'u.example.com', is_top_domain=True)
        api.add_domain(self.db, 'Example', 'es.u.example.com')
        api.add_domain(self.db, 'Example', 'en.u.example.com')

        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')
        api.add_domain(self.db, 'Bitergia', 'bitergia.org')

        api.add_organization(self.db, 'LibreSoft')

        # Add some unique identities
        jsmith_uuid = api.add_identity(self.db, 'scm', 'jsmith@us.example.com',
                                       'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@example.net', 'John Smith',
                         uuid=jsmith_uuid)
        api.add_identity(self.db, 'scm', 'jsmith@bitergia.com', 'John Smith', 'jsmith',
                         uuid=jsmith_uuid)
        api.add_enrollment(self.db, jsmith_uuid, 'Bitergia')

        # Add John Doe identity
        api.add_identity(self.db, 'unknown', None, 'John Doe', 'jdoe')

        # Add Jane Rae identity
        jroe_uuid = api.add_identity(self.db, 'scm', 'jroe@example.com',
                                     'Jane Roe', 'jroe')
        api.add_identity(self.db, 'scm', 'jroe@example.com',
                         uuid=jroe_uuid)
        api.add_identity(self.db, 'unknown', 'jroe@bitergia.com',
                         uuid=jroe_uuid)


class TestAffiliateCommand(TestBaseCase):
    """Unit tests for affiliate command"""

    def test_affiliate(self):
        """Check affiliate output"""

        self.cmd.run()
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, AFFILIATE_OUTPUT)

    def test_multiple_top_domains_error(self):
        """Check if it raises a RuntimeError on multiple top domains"""

        # To check this, add a new top domain to an existing organization
        api.add_domain(self.db, 'Example', '.com', is_top_domain=True)

        self.assertRaisesRegexp(RuntimeError,
                                MULTIPLE_DOMAIN_RUNTIME_ERROR % {'domain' : 'us.example.com'},
                                self.cmd.run)

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Delete the contents of the database
        self.db.clear()

        self.cmd.run()
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, AFFILIATE_EMPTY_OUTPUT)


class TestAffiliate(TestBaseCase):
    """Unit tests for affiliate"""

    def test_affiliate(self):
        """Check affiliation"""

        self.cmd.affiliate()
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, AFFILIATE_OUTPUT)

    def test_multiple_top_domains_error(self):
        """Check if it raises a RuntimeError on multiple top domains"""

        # To check this, add a new top domain to an existing organization
        api.add_domain(self.db, 'Example', '.com', is_top_domain=True)

        self.assertRaisesRegexp(RuntimeError,
                                MULTIPLE_DOMAIN_RUNTIME_ERROR % {'domain' : 'us.example.com'},
                                self.cmd.affiliate)

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Delete the contents of the database
        self.db.clear()

        self.cmd.affiliate()
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, AFFILIATE_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
