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
from sortinghat.cmd.affiliate import Affiliate

from tests.base import TestCommandCaseBase


AFFILIATE_OUTPUT = """Unique identity 17ab00ed3825ec2f50483e33c88df223264182ba (jroe@example.com) affiliated to Example
Unique identity 17ab00ed3825ec2f50483e33c88df223264182ba (jroe@bitergia.com) affiliated to Bitergia
Unique identity dc31d2afbee88a6d1dbc1ef05ec827b878067744 (jsmith@us.example.com) affiliated to Example"""

AFFILIATE_OUTPUT_ALT = """Unique identity 108f508fea9861d86c8d07a197489cc630bec446 (janedoe@it.u.example.com) affiliated to Example Alt
Unique identity 17ab00ed3825ec2f50483e33c88df223264182ba (jroe@example.com) affiliated to Example
Unique identity 17ab00ed3825ec2f50483e33c88df223264182ba (jroe@bitergia.com) affiliated to Bitergia
Unique identity dc31d2afbee88a6d1dbc1ef05ec827b878067744 (jsmith@us.example.com) affiliated to Example"""

AFFILIATE_EMPTY_OUTPUT = ""

MULTIPLE_DOMAIN_WARNING = "Warning: multiple top domains for %(subdomain)s sub-domain. Domain %(domain)s selected."


class TestAffiliateCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on affiliate unit tests"""

    cmd_klass = Affiliate

    def load_test_dataset(self):
        # Add some domains
        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com', is_top_domain=True)

        api.add_organization(self.db, 'Example Alt')
        api.add_domain(self.db, 'Example Alt', 'u.example.com', is_top_domain=True)
        api.add_domain(self.db, 'Example Alt', 'es.u.example.com')
        api.add_domain(self.db, 'Example Alt', 'en.u.example.com')

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

        # Add no valid email identity
        api.add_identity(self.db, 'test', 'novalidemail@')


class TestAffiliateCommand(TestAffiliateCaseBase):
    """Unit tests for affiliate command"""

    def test_affiliate(self):
        """Check affiliate output"""

        code = self.cmd.run()
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, AFFILIATE_OUTPUT)

    def test_multiple_top_domains(self):
        """Check if it chooses the right domain when multiple top domains are available"""

        api.add_identity(self.db, 'scm', 'janedoe@it.u.example.com')

        code = self.cmd.run()
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, AFFILIATE_OUTPUT_ALT)

        wrn = sys.stderr.getvalue().strip()
        self.assertEqual(wrn,
                         MULTIPLE_DOMAIN_WARNING % {'subdomain': 'it.u.example.com',
                                                    'domain': 'u.example.com'})

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Delete the contents of the database
        self.db.clear()

        code = self.cmd.run()
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, AFFILIATE_EMPTY_OUTPUT)


class TestAffiliate(TestAffiliateCaseBase):
    """Unit tests for affiliate"""

    def test_affiliate(self):
        """Check affiliation"""

        code = self.cmd.affiliate()
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, AFFILIATE_OUTPUT)

    def test_multiple_top_domains(self):
        """Check if it choose the right domain when multiple top domains are available"""

        api.add_identity(self.db, 'scm', 'janedoe@it.u.example.com')

        code = self.cmd.affiliate()
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, AFFILIATE_OUTPUT_ALT)

        wrn = sys.stderr.getvalue().strip()
        self.assertEqual(wrn,
                         MULTIPLE_DOMAIN_WARNING % {'subdomain': 'it.u.example.com',
                                                    'domain': 'u.example.com'})

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Delete the contents of the database
        self.db.clear()

        code = self.cmd.affiliate()
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, AFFILIATE_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
