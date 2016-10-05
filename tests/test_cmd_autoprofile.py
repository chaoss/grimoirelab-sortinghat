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
from sortinghat.cmd.autoprofile import AutoProfile
from sortinghat.db.model import Country
from sortinghat.exceptions import CODE_NOT_FOUND_ERROR

from tests.base import TestCommandCaseBase


PROFILE_AUTOCOMPLETE = """unique identity 02f161840469eb5348dec798166a171b34f0bc8a profile updated using mls source
unique identity 65fa77134a2d0bb4ed9252b853d9074e4d4c2eb4 profile updated using its source"""


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

        jdoe_uuid = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                     None, 'jdoe')
        api.add_identity(self.db, 'its', None,
                         'John Doe', None, uuid=jdoe_uuid)


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

        self.assertEqual(uids[0].profile, None)
        self.assertEqual(uids[1].profile, None)
        self.assertEqual(uids[2].profile, None)

    def test_autocomplete_profiles(self):
        """Check whether it autocompletes the profiles based on a priority list"""

        code = self.cmd.autocomplete(['mls', 'its'])

        uids = api.unique_identities(self.db)

        # It chooses the first identity with maximum priority
        self.assertEqual(uids[0].uuid, '02f161840469eb5348dec798166a171b34f0bc8a')
        self.assertEqual(uids[0].profile.name, None)
        self.assertEqual(uids[0].profile.email, 'jsmith@example.com')

        # Unique identities without identities from
        # the given sources are not updated
        self.assertEqual(uids[1].uuid, '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(uids[1].profile, None)

        # Only one source available
        self.assertEqual(uids[2].uuid, '65fa77134a2d0bb4ed9252b853d9074e4d4c2eb4')
        self.assertEqual(uids[2].profile.name, 'John Doe')
        self.assertEqual(uids[2].profile.email, None)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
