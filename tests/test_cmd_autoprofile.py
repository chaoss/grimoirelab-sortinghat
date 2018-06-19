#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2017 Bitergia
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

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.autoprofile import AutoProfile
from sortinghat.db.model import Country

from tests.base import TestCommandCaseBase


PROFILE_AUTOCOMPLETE = """unique identity eb10fb9519d69d75a6cdcd76707943a513685c09 profile updated using its source
unique identity ffefc2e3f2a255e9450ac9e2d36f37c28f51bd73 profile updated using mls source"""


class TestAutoProfileCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on autoprofile unit tests"""

    cmd_klass = AutoProfile

    def load_test_dataset(self):
        # Add country
        with self.db.connect() as session:
            # Add a country
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)

        # Add identities
        api.add_identity(self.db, 'scm', 'jroe@example.com',
                         'Jane Roe', 'jroe')

        jsmith_uuid = api.add_identity(self.db, 'mls', 'jsmith@example.com',
                                       None, None)
        api.add_identity(self.db, 'its', 'jsmith@example.net',
                         None, 'jsmith', uuid=jsmith_uuid)
        api.add_identity(self.db, 'mls', 'jsmith@example.com',
                         'John Smith', 'jsmith', uuid=jsmith_uuid)
        api.add_identity(self.db, 'mls', 'jsmith@example.com',
                         'J S', None, uuid=jsmith_uuid)

        jdoe_uuid = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                     None, 'jdoe')
        api.add_identity(self.db, 'its', None,
                         None, 'jdoe', uuid=jdoe_uuid)


class TestAutoProfileCommand(TestAutoProfileCaseBase):
    """Unit tests for autoprofile command"""

    def test_autocomplete(self):
        """Test autocomolete command"""

        code = self.cmd.run('mls', 'its')

        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, PROFILE_AUTOCOMPLETE)

    def test_autocomplete_no_sources(self):
        """Check whether it does nothing when there are no identities from a source"""

        code = self.cmd.run('source1', 'source2')

        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, "")

        # Unique identities remain without profiles
        uids = api.unique_identities(self.db)

        self.assertEqual(uids[0].profile.name, None)
        self.assertEqual(uids[0].profile.email, None)
        self.assertEqual(uids[1].profile.name, None)
        self.assertEqual(uids[1].profile.email, None)
        self.assertEqual(uids[2].profile.name, None)
        self.assertEqual(uids[2].profile.email, None)


    def test_autocomplete_profiles(self):
        """Check whether it autocompletes the profiles based on a priority list"""

        code = self.cmd.autocomplete(['mls', 'its'])

        uids = api.unique_identities(self.db)

        # Unique identities without identities from
        # the given sources are not updated
        self.assertEqual(uids[0].uuid, '17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(uids[0].profile.name, None)
        self.assertEqual(uids[0].profile.email, None)

        # Only one source available
        self.assertEqual(uids[1].uuid, 'eb10fb9519d69d75a6cdcd76707943a513685c09')
        self.assertEqual(uids[1].profile.name, 'jdoe')
        self.assertEqual(uids[1].profile.email, None)

        # It mixes the information of the identities with
        # maximum priority, using the longest name value
        self.assertEqual(uids[2].uuid, 'ffefc2e3f2a255e9450ac9e2d36f37c28f51bd73')
        self.assertEqual(uids[2].profile.name, 'John Smith')
        self.assertEqual(uids[2].profile.email, 'jsmith@example.com')


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
