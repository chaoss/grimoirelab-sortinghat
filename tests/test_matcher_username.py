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
#     Alvaro del Castillo <acs@bitergia.com>
#

import sys
import unittest

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat.db.model import UniqueIdentity, Identity, MatchingBlacklist
from sortinghat.matching.username import UsernameMatcher, UsernameIdentity


class TestUsernameMatcher(unittest.TestCase):

    def test_match(self):
        """Test match method"""

        # Let's define some identities first
        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', email='jsmith@example.com', source='scm'),
                             Identity(name='John Smith', source='scm'),
                             Identity(username='jsmith', source='scm'),
                             Identity(email='', source='scm')]

        john_smith = UniqueIdentity(uuid='js')
        john_smith.identities = [Identity(name='J. Smith', username='john_smith', source='scm'),
                                 Identity(username='john_smith', source='scm'),
                                 Identity(name='Smith. J', source='mls'),
                                 Identity(name='Smith. J', email='JSmith@example.com', source='mls')]

        jsmith_alt = UniqueIdentity(uuid='J. Smith')
        jsmith_alt.identities = [Identity(name='J. Smith', username='john_smith', source='alt'),
                                 Identity(name='John Smith', username='jsmith', source='alt'),
                                 Identity(email='', source='alt'),
                                 Identity(email='jsmith', source='alt')]

        # Tests
        matcher = UsernameMatcher()

        # First two unique does not produce any match
        result = matcher.match(jsmith, john_smith)
        self.assertEqual(result, False)

        result = matcher.match(john_smith, jsmith)
        self.assertEqual(result, False)

        # Comparing the third match with the second
        result = matcher.match(jsmith, jsmith_alt)
        self.assertEqual(result, True)

        result = matcher.match(jsmith_alt, jsmith)
        self.assertEqual(result, True)

        result = matcher.match(john_smith, jsmith_alt)
        self.assertEqual(result, True)

        result = matcher.match(jsmith_alt, john_smith)
        self.assertEqual(result, True)

    def test_match_with_blacklist(self):
        """Test match when there are entries in the blacklist"""

        # Let's define some identities first
        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', username='John_Smith', source='scm'),
                             Identity(name='John Smith', source='scm'),
                             Identity(username='jsmith', source='scm'),
                             Identity(email='', source='scm')]

        john_smith = UniqueIdentity(uuid='js')
        john_smith.identities = [Identity(name='J. Smith', email='JSmith@example.com', source='scm'),
                                 Identity(username='john_smith', source='scm'),
                                 Identity(name='Smith. J', source='mls'),
                                 Identity(name='Smith. J', username='john_smith', source='mls')]

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', username='jane.rae',
                                    email='jane.rae@example.net', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(email='JRAE@example.net', source='scm', uuid='jrae')]

        jane_rae = UniqueIdentity(uuid='Jane Rae')
        jane_rae.identities = [Identity(name='Jane Rae', source='scm', uuid='Jane Rae'),
                               Identity(email='jrae@example.net', username='Jane.rae', source='mls', uuid='Jane Rae')]

        # Check matching
        matcher = UsernameMatcher()

        # First two unique identities must match
        result = matcher.match(jsmith, john_smith)
        self.assertEqual(result, True)

        result = matcher.match(john_smith, jsmith)
        self.assertEqual(result, True)

        result = matcher.match(jrae, jane_rae)
        self.assertEqual(result, True)

        result = matcher.match(jane_rae, jrae)
        self.assertEqual(result, True)

        # Add a blacklist
        bl = [MatchingBlacklist(excluded='john_smith')]

        matcher = UsernameMatcher(blacklist=bl)

        result = matcher.match(jsmith, john_smith)
        self.assertEqual(result, False)

        result = matcher.match(john_smith, jsmith)
        self.assertEqual(result, False)

        result = matcher.match(jrae, jane_rae)
        self.assertEqual(result, True)

        result = matcher.match(jane_rae, jrae)
        self.assertEqual(result, True)

        # In this case, no match will be found
        bl = [MatchingBlacklist(excluded='John_Smith'),
              MatchingBlacklist(excluded='Jane.rae')]

        matcher = UsernameMatcher(blacklist=bl)

        result = matcher.match(jsmith, john_smith)
        self.assertEqual(result, False)

        result = matcher.match(john_smith, jsmith)
        self.assertEqual(result, False)

        result = matcher.match(jrae, jane_rae)
        self.assertEqual(result, False)

        result = matcher.match(jane_rae, jrae)
        self.assertEqual(result, False)

    def test_match_with_sources_list(self):
        """Test match when a list of sources to filter is given"""

        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', email='jsmith@example.com', source='scm'),
                             Identity(name='John Smith', source='scm'),
                             Identity(username='jsmith', source='scm'),
                             Identity(email='', source='scm')]

        jsmith_alt = UniqueIdentity(uuid='J. Smith')
        jsmith_alt.identities = [Identity(name='John Smith JR', email='jsmith@example.com', source='alt'),
                                 Identity(name='John Smith', username='jsmith', source='alt'),
                                 Identity(email='', source='alt'),
                                 Identity(email='jsmith', source='alt')]

        # With these lists there are not matches
        matcher = UsernameMatcher(sources=['github'])
        result = matcher.match(jsmith, jsmith_alt)
        self.assertEqual(result, False)

        matcher = UsernameMatcher(sources=['scm'])
        result = matcher.match(jsmith, jsmith_alt)
        self.assertEqual(result, False)

        # Only when scm and alt are combined there is a match
        matcher = UsernameMatcher(sources=['scm', 'alt'])
        result = matcher.match(jsmith, jsmith_alt)
        self.assertEqual(result, True)

    def test_match_same_identity(self):
        """Test whether there is a match comparing the same identity"""

        uid = UniqueIdentity(uuid='John Smith')

        matcher = UsernameMatcher()
        result = matcher.match(uid, uid)

        self.assertEqual(result, True)

    def test_match_same_uuid(self):
        """Test if there is a match when compares identities with the same UUID"""

        uid1 = UniqueIdentity(uuid='John Smith')
        uid2 = UniqueIdentity(uuid='John Smith')

        matcher = UsernameMatcher()

        result = matcher.match(uid1, uid2)
        self.assertEqual(result, True)

        result = matcher.match(uid2, uid1)
        self.assertEqual(result, True)

        uid1 = UniqueIdentity(uuid=None)
        uid2 = UniqueIdentity(uuid=None)

        result = matcher.match(uid1, uid2)
        self.assertEqual(result, False)

    def test_match_identities_instances(self):
        """Test whether it raises an error when ids are not UniqueIdentities"""

        uid = UniqueIdentity(uuid='John Smith')

        matcher = UsernameMatcher()

        self.assertRaises(ValueError, matcher.match, 'John Smith', uid)
        self.assertRaises(ValueError, matcher.match, uid, 'John Smith')
        self.assertRaises(ValueError, matcher.match, None, uid)
        self.assertRaises(ValueError, matcher.match, uid, None)
        self.assertRaises(ValueError, matcher.match, 'John Smith', 'John Doe')

    def test_match_filtered_identities(self):
        """Test whether filtered identities match"""

        jsmith = UsernameIdentity('1', None, 'jsmith')
        jsmith_alt = UsernameIdentity('2', 'jsmith', 'jsmith')
        jsmith_uuid = UsernameIdentity('3', 'jsmith', 'john.smith')

        matcher = UsernameMatcher()

        result = matcher.match_filtered_identities(jsmith, jsmith_alt)
        self.assertEqual(result, True)

        result = matcher.match_filtered_identities(jsmith, jsmith_uuid)
        self.assertEqual(result, False)

        result = matcher.match_filtered_identities(jsmith_alt, jsmith)
        self.assertEqual(result, True)

        result = matcher.match_filtered_identities(jsmith_alt, jsmith_uuid)
        self.assertEqual(result, True)

        result = matcher.match_filtered_identities(jsmith_uuid, jsmith)
        self.assertEqual(result, False)

        result = matcher.match_filtered_identities(jsmith_uuid, jsmith_alt)
        self.assertEqual(result, True)

    def test_match_filtered_identities_with_blacklist(self):
        """Test whether filtered identities match when there is a blacklist"""

        jsmith = UsernameIdentity('1', None, 'jsmith')
        jsmith_alt = UsernameIdentity('2', 'jsmith', 'jsmith')
        jsmith_uuid = UsernameIdentity('3', 'jsmith', 'john.smith')
        john_alt = UsernameIdentity('4', None, 'john.smith')
        jsmith_none = UsernameIdentity('4', 'john.smith', None)
        jdoe_none = UsernameIdentity('4', 'jdoe', None)

        bl = [MatchingBlacklist(excluded='JSMITH')]

        matcher = UsernameMatcher(blacklist=bl)

        result = matcher.match_filtered_identities(jsmith, jsmith_alt)
        self.assertEqual(result, False)

        result = matcher.match_filtered_identities(jsmith, jsmith_uuid)
        self.assertEqual(result, False)

        result = matcher.match_filtered_identities(jsmith_alt, jsmith)
        self.assertEqual(result, False)

        # Same UUID
        result = matcher.match_filtered_identities(jsmith_alt, jsmith_uuid)
        self.assertEqual(result, True)

        result = matcher.match_filtered_identities(jsmith_uuid, jsmith)
        self.assertEqual(result, False)

        # Same UUID
        result = matcher.match_filtered_identities(jsmith_uuid, jsmith_alt)
        self.assertEqual(result, True)

        result = matcher.match_filtered_identities(jsmith_uuid, john_alt)
        self.assertEqual(result, True)

        result = matcher.match_filtered_identities(john_alt, jsmith_uuid)
        self.assertEqual(result, True)

        # Although the UUID is equal to None, these two does not match
        result = matcher.match_filtered_identities(jsmith_none, jdoe_none)
        self.assertEqual(result, False)

    def test_match_filtered_identities_instances(self):
        """Test whether it raises an error when ids are not UsernameIdentities"""

        fid = UsernameIdentity('1', None, 'jsmith')

        matcher = UsernameMatcher()

        self.assertRaises(ValueError, matcher.match_filtered_identities, 'John Smith', fid)
        self.assertRaises(ValueError, matcher.match_filtered_identities, fid, 'John Smith')
        self.assertRaises(ValueError, matcher.match_filtered_identities, None, fid)
        self.assertRaises(ValueError, matcher.match_filtered_identities, fid, None)
        self.assertRaises(ValueError, matcher.match_filtered_identities, 'John Smith', 'John Doe')

    def test_filter_identities(self):
        """Test if identities are filtered"""

        # Let's define some identities first
        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', username='jsmith', source='scm', uuid='jsmith'),
                             Identity(name='John Smith', source='scm', uuid='jsmith'),
                             Identity(email='jsmith@example.com', source='scm', uuid='jsmith'),
                             Identity(username='', source='scm', uuid='jsmith')]

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', username='jane.rae', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(username='JRAE', source='scm', uuid='jrae')]

        matcher = UsernameMatcher()

        result = matcher.filter(jsmith)
        self.assertEqual(len(result), 1)

        fid = result[0]
        self.assertIsInstance(fid, UsernameIdentity)
        self.assertEqual(fid.uuid, 'jsmith')
        self.assertEqual(fid.username, 'jsmith')

        result = matcher.filter(jrae)
        self.assertEqual(len(result), 2)

        fid = result[0]
        self.assertIsInstance(fid, UsernameIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.username, 'jane.rae')

        fid = result[1]
        self.assertIsInstance(fid, UsernameIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.username, 'jrae')

    def test_filter_identities_with_blacklist(self):
        """Test if identities are filtered when there is a blacklist"""

        # Let's define some identities first
        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', username='jsmith', source='scm', uuid='jsmith'),
                             Identity(name='John Smith', source='scm', uuid='jsmith'),
                             Identity(email='jsmith@example.com', source='scm', uuid='jsmith'),
                             Identity(email='', source='scm', uuid='jsmith')]

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', username='jane.rae', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(username='JRAE', source='scm', uuid='jrae')]

        bl = [MatchingBlacklist(excluded='jrae')]

        matcher = UsernameMatcher(blacklist=bl)

        result = matcher.filter(jsmith)
        self.assertEqual(len(result), 1)

        fid = result[0]
        self.assertIsInstance(fid, UsernameIdentity)
        self.assertEqual(fid.uuid, 'jsmith')
        self.assertEqual(fid.username, 'jsmith')

        result = matcher.filter(jrae)
        self.assertEqual(len(result), 1)

        fid = result[0]
        self.assertIsInstance(fid, UsernameIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.username, 'jane.rae')

    def test_filter_identities_with_sources_list(self):
        """Test if identities are filtered when there is a sources list"""

        # Let's define some identities first
        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', username='jsmith', source='scm', uuid='jsmith'),
                             Identity(name='John Smith', source='scm', uuid='jsmith'),
                             Identity(email='jsmith@example.com', source='scm', uuid='jsmith'),
                             Identity(email='', source='scm', uuid='jsmith')]

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', username='jane.rae', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(username='JRAE', source='scm', uuid='jrae')]

        # Tests
        matcher = UsernameMatcher(sources=['mls', 'alt'])

        result = matcher.filter(jsmith)
        self.assertEqual(len(result), 0)

        result = matcher.filter(jrae)
        self.assertEqual(len(result), 1)

        fid = result[0]
        self.assertIsInstance(fid, UsernameIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.username, 'jane.rae')

    def test_filter_identities_instances(self):
        """Test whether it raises an error when id is not a UniqueIdentity"""

        matcher = UsernameMatcher()

        self.assertRaises(ValueError, matcher.filter, 'John Smith')
        self.assertRaises(ValueError, matcher.filter, None)

    def test_matching_criteria(self):
        """Test whether it returns the matching criteria keys"""

        criteria = UsernameMatcher.matching_criteria()

        self.assertListEqual(criteria, ['username'])


if __name__ == "__main__":
    unittest.main()
