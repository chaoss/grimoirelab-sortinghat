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
from sortinghat.cmd.unify import Unify
from sortinghat.exceptions import CODE_MATCHER_NOT_SUPPORTED_ERROR

from tests.base import TestCommandCaseBase


UNIFY_DEFAULT_OUTPUT = """Total unique identities processed: 6
Total matches: 1
Total unique identities after merging: 5"""
UNIFY_EMAIL_NAME_OUTPUT = """Total unique identities processed: 6
Total matches: 3
Total unique identities after merging: 3"""
UNIFY_EMPTY_OUTPUT = """Total unique identities processed: 0
Total matches: 0
Total unique identities after merging: 0"""

UNIFY_MATCHING_ERROR = "Error: mock identity matcher is not supported"


class TestUnifyCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on unify unit tests"""

    cmd_klass = Unify

    def load_test_dataset(self):
        # Add some unique identities

        uuid = api.add_identity(self.db, source='scm', email='jsmith@example.com', name='John Smith')
        api.add_identity(self.db, source='scm', name='John Smith', uuid=uuid)
        api.add_identity(self.db, source='scm', username='jsmith', uuid=uuid)

        uuid = api.add_identity(self.db, source='alt', name='J. Smith', username='john_smith')
        api.add_identity(self.db, source='alt', name='John Smith', username='jsmith', uuid=uuid)
        api.add_identity(self.db, source='alt', email='jsmith', uuid=uuid)

        uuid = api.add_identity(self.db, source='scm', name='Jane Rae')
        api.add_identity(self.db, source='mls', email='jane.rae@example.net', name='Jane Rae Doe', uuid=uuid)

        uuid = api.add_identity(self.db, source='scm', name='J. Smith', username='john_smith')
        api.add_identity(self.db, source='scm', username='john_smith', uuid=uuid)
        api.add_identity(self.db, source='mls', username='Smith. J', uuid=uuid)
        api.add_identity(self.db, source='mls', email='JSmith@example.com', name='Smith. J', uuid=uuid)

        uuid = api.add_identity(self.db, source='mls', email='jrae@example.net', name='Jane Rae Doe')
        api.add_identity(self.db, source='mls', name='jrae', uuid=uuid)

        uuid = api.add_identity(self.db, source='scm', name='jrae')


class TestUnifyCommand(TestUnifyCaseBase):
    """Unify command unit tests"""

    def test_unify(self):
        """Test command"""

        code = self.cmd.run()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_DEFAULT_OUTPUT)

    def test_unify_fast_matching(self):
        """Test command with fast matching"""

        code = self.cmd.run('--fast-matching')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_DEFAULT_OUTPUT)

    def test_unify_email_name_matcher(self):
        """Test command using the email-name matcher"""

        code = self.cmd.run('--matching', 'email-name')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_EMAIL_NAME_OUTPUT)

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Delete the contents of the database
        self.db.clear()

        code = self.cmd.run()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_EMPTY_OUTPUT)


class TestUnify(TestUnifyCaseBase):
    """Unit tests for unify"""

    def test_unify(self):
        """Test unify method using a default matcher"""

        before = api.unique_identities(self.db)
        self.assertEqual(len(before), 6)

        code = self.cmd.unify(matching='default')
        self.assertEqual(code, CMD_SUCCESS)

        after = api.unique_identities(self.db)
        self.assertEqual(len(after), 5)

        # jsmith identities with same email address
        jsmith = after[1]
        self.assertEqual(jsmith.uuid, '72ae225d363c83456d788da14eeb0718efe7a0fc')

        identities = jsmith.identities
        identities.sort(key=lambda x: x.id)

        self.assertEqual(len(identities), 7)

        id_ = identities[0]
        self.assertEqual(id_.email, 'JSmith@example.com')
        self.assertEqual(id_.source, 'mls')

        id_ = identities[2]
        self.assertEqual(id_.email, 'jsmith@example.com')
        self.assertEqual(id_.source, 'scm')

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_DEFAULT_OUTPUT)

    def test_unify_fast_matching(self):
        """Test unify method using a default matcher and fast matching mode"""

        before = api.unique_identities(self.db)
        self.assertEqual(len(before), 6)

        code = self.cmd.unify(matching='default', fast_matching=True)
        self.assertEqual(code, CMD_SUCCESS)

        after = api.unique_identities(self.db)
        self.assertEqual(len(after), 5)

        # jsmith identities with same email address
        jsmith = after[1]
        self.assertEqual(jsmith.uuid, '72ae225d363c83456d788da14eeb0718efe7a0fc')

        identities = jsmith.identities
        identities.sort(key=lambda x: x.id)

        self.assertEqual(len(identities), 7)

        id_ = identities[0]
        self.assertEqual(id_.email, 'JSmith@example.com')
        self.assertEqual(id_.source, 'mls')

        id_ = identities[2]
        self.assertEqual(id_.email, 'jsmith@example.com')
        self.assertEqual(id_.source, 'scm')

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_DEFAULT_OUTPUT)

    def test_unify_with_blacklist(self):
        """Test unify method using a blacklist"""

        # Add some entries to the blacklist
        api.add_to_matching_blacklist(self.db, 'Jane Rae Doe')
        api.add_to_matching_blacklist(self.db, 'jsmith@example.com')

        before = api.unique_identities(self.db)
        self.assertEqual(len(before), 6)

        code = self.cmd.unify(matching='default')
        self.assertEqual(code, CMD_SUCCESS)

        # No match was found
        after = api.unique_identities(self.db)
        self.assertEqual(len(after), 6)

    def test_unify_email_name_matcher(self):
        """Test unify method using the email-name matcher"""

        before = api.unique_identities(self.db)
        self.assertEqual(len(before), 6)

        code = self.cmd.unify(matching='email-name')
        self.assertEqual(code, CMD_SUCCESS)

        after = api.unique_identities(self.db)
        self.assertEqual(len(after), 3)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_EMAIL_NAME_OUTPUT)

    def test_unify_email_name_matcher_with_blacklist(self):
        """Test unify method using a blacklist"""

        # Add some entries to the blacklist
        api.add_to_matching_blacklist(self.db, 'Jane Rae Doe')
        api.add_to_matching_blacklist(self.db, 'jsmith@example.com')

        before = api.unique_identities(self.db)
        self.assertEqual(len(before), 6)

        code = self.cmd.unify(matching='email-name')
        self.assertEqual(code, CMD_SUCCESS)

        after = api.unique_identities(self.db)
        self.assertEqual(len(after), 5)

        # Only two identities were merged due to the blacklist
        jsmith = after[2]
        self.assertEqual(jsmith.uuid, '75d95d6c8492fd36d24a18bd45d62161e05fbc97')
        self.assertEqual(len(jsmith.identities), 6)

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Delete the contents of the database
        self.db.clear()

        code = self.cmd.unify()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_EMPTY_OUTPUT)

    def test_invalid_matching_method(self):
        """Check if it fails when an invalid matching method is given"""

        code = self.cmd.unify(matching='mock')
        self.assertEqual(code, CODE_MATCHER_NOT_SUPPORTED_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, UNIFY_MATCHING_ERROR)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
