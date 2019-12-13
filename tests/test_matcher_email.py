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

from sortinghat.db.model import UniqueIdentity, Identity, MatchingBlacklist
from sortinghat.matching.email import EmailMatcher, EmailIdentity


class TestEmailMatcher(unittest.TestCase):

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

        jsmith_not_email = UniqueIdentity(uuid='John Smith')
        jsmith_not_email.identities = [Identity(email='jsmith', source='mls')]

        # Tests
        matcher = EmailMatcher()

        # First two unique identities must match
        result = matcher.match(jsmith, john_smith)
        self.assertEqual(result, True)

        result = matcher.match(john_smith, jsmith)
        self.assertEqual(result, True)

        # Comparing with the third does not produce any match
        result = matcher.match(jsmith, jsmith_alt)
        self.assertEqual(result, False)

        result = matcher.match(jsmith_alt, jsmith)
        self.assertEqual(result, False)

        result = matcher.match(john_smith, jsmith_alt)
        self.assertEqual(result, False)

        result = matcher.match(jsmith_alt, john_smith)
        self.assertEqual(result, False)

        # This two unique identities have the same email address
        # but due to 'jsmith' is not a valid email address, they
        # do not match
        result = matcher.match(jsmith_alt, jsmith_not_email)
        self.assertEqual(result, False)

    def test_match_with_blacklist(self):
        """Test match when there are entries in the blacklist"""

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

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', email='jane.rae@example.net', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(email='JRAE@example.net', source='scm', uuid='jrae')]

        jane_rae = UniqueIdentity(uuid='Jane Rae')
        jane_rae.identities = [Identity(name='Jane Rae', source='scm', uuid='Jane Rae'),
                               Identity(email='jrae@example.net', source='mls', uuid='Jane Rae')]

        # Check matching
        matcher = EmailMatcher()

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
        bl = [MatchingBlacklist(excluded='Jsmith@example.com'),
              MatchingBlacklist(excluded='jrae@example.com')]

        matcher = EmailMatcher(blacklist=bl)

        result = matcher.match(jsmith, john_smith)
        self.assertEqual(result, False)

        result = matcher.match(john_smith, jsmith)
        self.assertEqual(result, False)

        result = matcher.match(jrae, jane_rae)
        self.assertEqual(result, True)

        result = matcher.match(jane_rae, jrae)
        self.assertEqual(result, True)

        # In this case, no match will be found
        bl = [MatchingBlacklist(excluded='Jsmith@example.com'),
              MatchingBlacklist(excluded='jrae@example.com'),
              MatchingBlacklist(excluded='jrae@example.net')]

        matcher = EmailMatcher(blacklist=bl)

        result = matcher.match(jsmith, john_smith)
        self.assertEqual(result, False)

        result = matcher.match(john_smith, jsmith)
        self.assertEqual(result, False)

        result = matcher.match(jrae, jane_rae)
        self.assertEqual(result, False)

        result = matcher.match(jane_rae, jrae)
        self.assertEqual(result, False)

    def test_match_with_blacklist_not_strict(self):
        """Test match when there are entries in the blacklist and strict mode is False"""

        # Let's define some identities first
        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', email='jsmith_at_example.com', source='scm'),
                             Identity(name='John Smith', source='scm'),
                             Identity(username='jsmith', source='scm'),
                             Identity(email='', source='scm')]

        john_smith = UniqueIdentity(uuid='js')
        john_smith.identities = [Identity(name='J. Smith', username='john_smith', source='scm'),
                                 Identity(username='john_smith', source='scm'),
                                 Identity(name='Smith. J', source='mls'),
                                 Identity(name='Smith. J', email='JSmith_at_example.com', source='mls')]

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', email='jane.rae_at_example.net', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(email='JRAE_at_example.net', source='scm', uuid='jrae')]

        jane_rae = UniqueIdentity(uuid='Jane Rae')
        jane_rae.identities = [Identity(name='Jane Rae', source='scm', uuid='Jane Rae'),
                               Identity(email='jrae_at_example.net', source='mls', uuid='Jane Rae')]

        # Check matching
        matcher = EmailMatcher(strict=False)

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
        bl = [MatchingBlacklist(excluded='Jsmith_at_example.com'),
              MatchingBlacklist(excluded='jrae_at_example.com')]

        matcher = EmailMatcher(blacklist=bl, strict=False)

        result = matcher.match(jsmith, john_smith)
        self.assertEqual(result, False)

        result = matcher.match(john_smith, jsmith)
        self.assertEqual(result, False)

        result = matcher.match(jrae, jane_rae)
        self.assertEqual(result, True)

        result = matcher.match(jane_rae, jrae)
        self.assertEqual(result, True)

        # In this case, no match will be found
        bl = [MatchingBlacklist(excluded='Jsmith_at_example.com'),
              MatchingBlacklist(excluded='jrae_at_example.com'),
              MatchingBlacklist(excluded='jrae_at_example.net')]

        matcher = EmailMatcher(blacklist=bl, strict=False)

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
        matcher = EmailMatcher(sources=['github'])
        result = matcher.match(jsmith, jsmith_alt)
        self.assertEqual(result, False)

        matcher = EmailMatcher(sources=['scm'])
        result = matcher.match(jsmith, jsmith_alt)
        self.assertEqual(result, False)

        # Only when scm and alt are combined there is a match
        matcher = EmailMatcher(sources=['scm', 'alt'])
        result = matcher.match(jsmith, jsmith_alt)
        self.assertEqual(result, True)

    def test_match_strict(self):
        """Test strict matching"""

        # Let's define some identities first
        jsmith_alt = UniqueIdentity(uuid='J. Smith')
        jsmith_alt.identities = [Identity(name='J. Smith', username='john_smith', source='alt'),
                                 Identity(name='John Smith', username='jsmith', source='alt'),
                                 Identity(email='', source='alt'),
                                 Identity(email='jsmith', source='alt')]

        jsmith_not_email = UniqueIdentity(uuid='John Smith')
        jsmith_not_email.identities = [Identity(email='jsmith', source='mls')]

        # Tests
        strict_matcher = EmailMatcher(strict=True)
        no_strict_matcher = EmailMatcher(strict=False)

        # This two unique identities have the same email address
        # but due to 'jsmith' is not a valid email address, they
        # do not match
        result = strict_matcher.match(jsmith_alt, jsmith_not_email)
        self.assertEqual(result, False)

        # With strict mode set to False, both identities match
        result = no_strict_matcher.match(jsmith_alt, jsmith_not_email)
        self.assertEqual(result, True)

    def test_match_same_identity(self):
        """Test whether there is a match comparing the same identity"""

        uid = UniqueIdentity(uuid='John Smith')

        matcher = EmailMatcher()
        result = matcher.match(uid, uid)

        self.assertEqual(result, True)

    def test_match_same_uuid(self):
        """Test if there is a match when compares identities with the same UUID"""

        uid1 = UniqueIdentity(uuid='John Smith')
        uid2 = UniqueIdentity(uuid='John Smith')

        matcher = EmailMatcher()

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

        matcher = EmailMatcher()

        self.assertRaises(ValueError, matcher.match, 'John Smith', uid)
        self.assertRaises(ValueError, matcher.match, uid, 'John Smith')
        self.assertRaises(ValueError, matcher.match, None, uid)
        self.assertRaises(ValueError, matcher.match, uid, None)
        self.assertRaises(ValueError, matcher.match, 'John Smith', 'John Doe')

    def test_match_filtered_identities(self):
        """Test whether filtered identities match"""

        jsmith = EmailIdentity('1', None, 'jsmith@example.com')
        jsmith_alt = EmailIdentity('2', 'jsmith', 'jsmith@example.com')
        jsmith_uuid = EmailIdentity('3', 'jsmith', 'john.smith@example.com')

        matcher = EmailMatcher()

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

        jsmith = EmailIdentity('1', None, 'jsmith@example.com')
        jsmith_alt = EmailIdentity('2', 'jsmith', 'jsmith@example.com')
        jsmith_uuid = EmailIdentity('3', 'jsmith', 'john.smith@example.com')
        john_alt = EmailIdentity('4', None, 'john.smith@example.com')
        jsmith_none = EmailIdentity('4', 'john.smith@example.com', None)
        jdoe_none = EmailIdentity('4', 'jdoe@example.com', None)

        bl = [MatchingBlacklist(excluded='JSMITH@example.com')]

        matcher = EmailMatcher(blacklist=bl)

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
        """Test whether it raises an error when ids are not EmailNameIdentities"""

        fid = EmailIdentity('1', None, 'jsmith@example.com')

        matcher = EmailMatcher()

        self.assertRaises(ValueError, matcher.match_filtered_identities, 'John Smith', fid)
        self.assertRaises(ValueError, matcher.match_filtered_identities, fid, 'John Smith')
        self.assertRaises(ValueError, matcher.match_filtered_identities, None, fid)
        self.assertRaises(ValueError, matcher.match_filtered_identities, fid, None)
        self.assertRaises(ValueError, matcher.match_filtered_identities, 'John Smith', 'John Doe')

    def test_filter_identities(self):
        """Test if identities are filtered"""

        # Let's define some identities first
        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', email='jsmith@example.com', source='scm', uuid='jsmith'),
                             Identity(name='John Smith', source='scm', uuid='jsmith'),
                             Identity(username='jsmith', source='scm', uuid='jsmith'),
                             Identity(email='jsmith@test', uuid='jsmith'),
                             Identity(email='', source='scm', uuid='jsmith')]

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', email='jane.rae@example.net', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(email='JRAE@example.net', source='scm', uuid='jrae')]

        matcher = EmailMatcher()

        result = matcher.filter(jsmith)
        self.assertEqual(len(result), 1)

        fid = result[0]
        self.assertIsInstance(fid, EmailIdentity)
        self.assertEqual(fid.uuid, 'jsmith')
        self.assertEqual(fid.email, 'jsmith@example.com')

        result = matcher.filter(jrae)
        self.assertEqual(len(result), 2)

        fid = result[0]
        self.assertIsInstance(fid, EmailIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.email, 'jane.rae@example.net')

        fid = result[1]
        self.assertIsInstance(fid, EmailIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.email, 'jrae@example.net')

    def test_filter_identities_with_blacklist(self):
        """Test if identities are filtered when there is a blacklist"""

        # Let's define some identities first
        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', email='jsmith@example.com', source='scm', uuid='jsmith'),
                             Identity(name='John Smith', source='scm', uuid='jsmith'),
                             Identity(username='jsmith', source='scm', uuid='jsmith'),
                             Identity(email='', source='scm', uuid='jsmith')]

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', email='jane.rae@example.net', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(email='JRAE@example.net', source='scm', uuid='jrae')]

        bl = [MatchingBlacklist(excluded='jrae@example.net')]

        matcher = EmailMatcher(blacklist=bl)

        result = matcher.filter(jsmith)
        self.assertEqual(len(result), 1)

        fid = result[0]
        self.assertIsInstance(fid, EmailIdentity)
        self.assertEqual(fid.uuid, 'jsmith')
        self.assertEqual(fid.email, 'jsmith@example.com')

        result = matcher.filter(jrae)
        self.assertEqual(len(result), 1)

        fid = result[0]
        self.assertIsInstance(fid, EmailIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.email, 'jane.rae@example.net')

    def test_filter_identities_with_blacklist_not_strict(self):
        """Test if identities are filtered when there is a blacklist and strict mode is False"""

        # Let's define some identities first
        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', email='jsmith_at_example.com', source='scm', uuid='jsmith'),
                             Identity(name='John Smith', source='scm', uuid='jsmith'),
                             Identity(username='jsmith', source='scm', uuid='jsmith'),
                             Identity(email='', source='scm', uuid='jsmith')]

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', email='jane.rae_at_example.net', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(email='JRAE_at_example.net', source='scm', uuid='jrae')]

        bl = [MatchingBlacklist(excluded='jrae_at_example.net')]

        matcher = EmailMatcher(blacklist=bl, strict=False)

        result = matcher.filter(jsmith)
        self.assertEqual(len(result), 1)

        fid = result[0]
        self.assertIsInstance(fid, EmailIdentity)
        self.assertEqual(fid.uuid, 'jsmith')
        self.assertEqual(fid.email, 'jsmith_at_example.com')

        result = matcher.filter(jrae)
        self.assertEqual(len(result), 1)

        fid = result[0]
        self.assertIsInstance(fid, EmailIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.email, 'jane.rae_at_example.net')

    def test_filter_identities_with_sources_list(self):
        """Test if identities are filtered when there is a sources list"""

        # Let's define some identities first
        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', email='jsmith@example.com', source='scm', uuid='jsmith'),
                             Identity(name='John Smith', source='scm', uuid='jsmith'),
                             Identity(name='John Smith JR', source='scm', uuid='jsmith'),
                             Identity(username='jsmith', source='mls', uuid='jsmith'),
                             Identity(email='', source='scm', uuid='jsmith')]

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', email='jane.rae@example.net', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(email='JRAE@example.net', source='scm', uuid='jrae')]

        # Tests
        matcher = EmailMatcher(sources=['mls', 'alt'])

        result = matcher.filter(jsmith)
        self.assertEqual(len(result), 0)

        result = matcher.filter(jrae)
        self.assertEqual(len(result), 1)

        fid = result[0]
        self.assertIsInstance(fid, EmailIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.email, 'jane.rae@example.net')

    def test_filter_identities_no_strict(self):
        """Test if identities are filtered in no strict mode"""

        # Let's define some identities first
        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', email='jsmith@example.com', source='scm', uuid='jsmith'),
                             Identity(name='John Smith', source='scm', uuid='jsmith'),
                             Identity(username='jsmith', source='scm', uuid='jsmith'),
                             Identity(email='jsmith@test', uuid='jsmith'),
                             Identity(email='', source='scm', uuid='jsmith')]

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', email='jane.rae@example.net', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(email='JRAE@example.net', source='scm', uuid='jrae')]

        matcher = EmailMatcher(strict=False)

        result = matcher.filter(jsmith)
        self.assertEqual(len(result), 2)

        fid = result[0]
        self.assertIsInstance(fid, EmailIdentity)
        self.assertEqual(fid.uuid, 'jsmith')
        self.assertEqual(fid.email, 'jsmith@example.com')

        fid = result[1]
        self.assertIsInstance(fid, EmailIdentity)
        self.assertEqual(fid.uuid, 'jsmith')
        self.assertEqual(fid.email, 'jsmith@test')

        result = matcher.filter(jrae)
        self.assertEqual(len(result), 2)

        fid = result[0]
        self.assertIsInstance(fid, EmailIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.email, 'jane.rae@example.net')

        fid = result[1]
        self.assertIsInstance(fid, EmailIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.email, 'jrae@example.net')

    def test_filter_identities_instances(self):
        """Test whether it raises an error when id is not a UniqueIdentity"""

        matcher = EmailMatcher()

        self.assertRaises(ValueError, matcher.filter, 'John Smith')
        self.assertRaises(ValueError, matcher.filter, None)

    def test_matching_criteria(self):
        """Test whether it returns the matching criteria keys"""

        criteria = EmailMatcher.matching_criteria()

        self.assertListEqual(criteria, ['email'])


if __name__ == "__main__":
    unittest.main()
