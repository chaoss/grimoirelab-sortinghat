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
from sortinghat.matching.email_name import EmailNameMatcher, EmailNameIdentity


class TestEmailNameMatcher(unittest.TestCase):

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

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm'),
                           Identity(name='Jane Rae Doe', email='jane.rae@example.net', source='mls')]

        jrae_doe = UniqueIdentity(uuid='jraedoe')
        jrae_doe.identities = [Identity(name='Jane Rae Doe', email='jrae@example.com', source='mls'),
                               Identity(name='jrae', source='scm')]

        jrae_no_name = UniqueIdentity(uuid='Jane Rae')
        jrae_no_name.identities = [Identity(name='jrae', source='scm')]

        # Tests
        matcher = EmailNameMatcher()

        # First two unique identities must match
        result = matcher.match(jsmith, john_smith)
        self.assertEqual(result, True)

        result = matcher.match(john_smith, jsmith)
        self.assertEqual(result, True)

        # Comparing with the third only the first one
        # produces a match because of "John Smith" name
        result = matcher.match(jsmith, jsmith_alt)
        self.assertEqual(result, True)

        result = matcher.match(jsmith_alt, jsmith)
        self.assertEqual(result, True)

        result = matcher.match(john_smith, jsmith_alt)
        self.assertEqual(result, False)

        result = matcher.match(jsmith_alt, john_smith)
        self.assertEqual(result, False)

        # Jane Rae matches Jane Rae Doe because they share
        # the same name "Jane Rae Doe"
        result = matcher.match(jrae, jrae_doe)
        self.assertEqual(result, True)

        result = matcher.match(jrae, jrae_doe)
        self.assertEqual(result, True)

        # No match with Jane Rae
        result = matcher.match(jsmith, jrae)
        self.assertEqual(result, False)

        result = matcher.match(jsmith, jrae_doe)
        self.assertEqual(result, False)

        result = matcher.match(john_smith, jrae)
        self.assertEqual(result, False)

        result = matcher.match(john_smith, jrae_doe)
        self.assertEqual(result, False)

        result = matcher.match(jsmith_alt, jrae)
        self.assertEqual(result, False)

        result = matcher.match(jsmith_alt, jrae_doe)
        self.assertEqual(result, False)

        # This two unique identities have the same email address
        # but due to 'jsmith' is not a valid email address, they
        # do not match
        result = matcher.match(jsmith_alt, jsmith_not_email)
        self.assertEqual(result, False)

        # This two do not match although they share the same name.
        # In this case the name is invalid because is not formed
        # like "firstname lastname"
        result = matcher.match(jrae_doe, jrae_no_name)
        self.assertEqual(result, False)

    def test_match_with_blacklist(self):
        """Test match when there are entries in the blacklist"""

        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', email='jsmith@example.com', source='scm'),
                             Identity(name='John Smith', source='scm'),
                             Identity(username='jsmith', source='scm'),
                             Identity(email='', source='scm')]

        john_smith = UniqueIdentity(uuid='js')
        john_smith.identities = [Identity(name='John Smith JR', username='john_smith', source='scm'),
                                 Identity(username='john_smith', source='scm'),
                                 Identity(name='Smith. J', source='mls'),
                                 Identity(name='Smith. J', email='JSmith@example.com', source='mls')]

        jsmith_alt = UniqueIdentity(uuid='J. Smith')
        jsmith_alt.identities = [Identity(name='John Smith JR', username='john_smith', source='alt'),
                                 Identity(name='John Smith', username='jsmith', source='alt'),
                                 Identity(email='', source='alt'),
                                 Identity(email='jsmith', source='alt')]

        # Tests
        bl = [MatchingBlacklist(excluded='John Smith'),
              MatchingBlacklist(excluded='jsmith@example.com')]

        matcher = EmailNameMatcher(blacklist=bl)

        result = matcher.match(jsmith, john_smith)
        self.assertEqual(result, False)

        result = matcher.match(john_smith, jsmith)
        self.assertEqual(result, False)

        # John Smith is blacklisted, so no match
        result = matcher.match(jsmith, jsmith_alt)
        self.assertEqual(result, False)

        result = matcher.match(jsmith_alt, jsmith)
        self.assertEqual(result, False)

        result = matcher.match(john_smith, jsmith_alt)
        self.assertEqual(result, True)

        result = matcher.match(jsmith_alt, john_smith)
        self.assertEqual(result, True)

    def test_match_with_sources_list(self):
        """Test match when a list of sources to filter is given"""

        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', email='jsmith@example.com', source='scm'),
                             Identity(name='John Smith', source='scm'),
                             Identity(username='jsmith', source='scm'),
                             Identity(email='', source='scm')]

        jsmith_alt = UniqueIdentity(uuid='J. Smith')
        jsmith_alt.identities = [Identity(name='John Smith JR', username='john_smith', source='alt'),
                                 Identity(name='John Smith', username='jsmith', source='alt'),
                                 Identity(email='', source='alt'),
                                 Identity(email='jsmith', source='alt')]

        # With these lists there are not matches
        matcher = EmailNameMatcher(sources=['github'])
        result = matcher.match(jsmith, jsmith_alt)
        self.assertEqual(result, False)

        matcher = EmailNameMatcher(sources=['scm'])
        result = matcher.match(jsmith, jsmith_alt)
        self.assertEqual(result, False)

        # Only when scm and alt are combined there is a match
        matcher = EmailNameMatcher(sources=['scm', 'alt'])
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

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm'),
                           Identity(name='Jane Rae Doe', email='jane.rae@example.net', source='mls')]

        jrae_doe = UniqueIdentity(uuid='jraedoe')
        jrae_doe.identities = [Identity(name='Jane Rae Doe', email='jrae@example.com', source='mls'),
                               Identity(name='jrae', source='scm')]

        jrae_no_name = UniqueIdentity(uuid='Jane Rae')
        jrae_no_name.identities = [Identity(name='jrae', source='scm')]

        # Tests
        strict_matcher = EmailNameMatcher(strict=True)
        no_strict_matcher = EmailNameMatcher(strict=False)

        # This two unique identities have the same email address
        # but due to 'jsmith' is not a valid email address, they
        # do not match
        result = strict_matcher.match(jsmith_alt, jsmith_not_email)
        self.assertEqual(result, False)

        # But with strict mode off they do
        result = no_strict_matcher.match(jsmith_alt, jsmith_not_email)
        self.assertEqual(result, True)

        # This two do not match although they share the same name.
        # In this case the name is invalid because is not formed
        # like "firstname lastname"
        result = strict_matcher.match(jrae_doe, jrae_no_name)
        self.assertEqual(result, False)

        # But with strict mode off they do
        result = no_strict_matcher.match(jrae_doe, jrae_no_name)
        self.assertEqual(result, True)

    def test_match_same_identity(self):
        """Test whether there is a match comparing the same identity"""

        uid = UniqueIdentity(uuid='John Smith')

        matcher = EmailNameMatcher()
        result = matcher.match(uid, uid)

        self.assertEqual(result, True)

    def test_match_same_uuid(self):
        """Test if there is a match when compares identities with the same UUID"""

        uid1 = UniqueIdentity(uuid='John Smith')
        uid2 = UniqueIdentity(uuid='John Smith')

        matcher = EmailNameMatcher()

        result = matcher.match(uid1, uid2)
        self.assertEqual(result, True)

        result = matcher.match(uid2, uid1)
        self.assertEqual(result, True)

        # None UUIDs do not produce a positive match
        uid1 = UniqueIdentity(uuid=None)
        uid2 = UniqueIdentity(uuid=None)

        matcher = EmailNameMatcher()

        result = matcher.match(uid1, uid2)
        self.assertEqual(result, False)

        result = matcher.match(uid2, uid1)
        self.assertEqual(result, False)

    def test_match_identities_instances(self):
        """Test whether it raises an error when ids are not UniqueIdentities"""

        uid = UniqueIdentity(uuid='John Smith')

        matcher = EmailNameMatcher()

        self.assertRaises(ValueError, matcher.match, 'John Smith', uid)
        self.assertRaises(ValueError, matcher.match, uid, 'John Smith')
        self.assertRaises(ValueError, matcher.match, None, uid)
        self.assertRaises(ValueError, matcher.match, uid, None)
        self.assertRaises(ValueError, matcher.match, 'John Smith', 'John Doe')

    def test_match_filtered_identities(self):
        """Test whether filtered identities match"""

        jsmith = EmailNameIdentity('1', None, 'jsmith@example.com', 'john smith')
        jsmith_alt = EmailNameIdentity('2', 'jsmith', None, 'john smith')
        jsmith_uuid = EmailNameIdentity('3', 'jsmith', 'john.smith@example.com', 'john')
        jsmith_none = EmailNameIdentity('4', 'jsmith', 'john.smith@example.com', None)
        jdoe_none = EmailNameIdentity('4', 'jdoe', 'jdoe@example.com', None)

        matcher = EmailNameMatcher()

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

        # Although the UUID is equal to None, these two does not match
        result = matcher.match_filtered_identities(jsmith_none, jdoe_none)
        self.assertEqual(result, False)

    def test_match_filtered_identities_instances(self):
        """Test whether it raises an error when ids are not EmailNameIdentities"""

        fid = EmailNameIdentity('1', None, 'jsmith@example.com', 'john smith')

        matcher = EmailNameMatcher()

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
                             Identity(email='', source='scm', uuid='jsmith')]

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', email='jane.rae@example.net', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(email='JRAE@example.net', source='scm', uuid='jrae')]

        matcher = EmailNameMatcher()

        result = matcher.filter(jsmith)
        self.assertEqual(len(result), 2)

        fid = result[0]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jsmith')
        self.assertEqual(fid.name, 'john smith')
        self.assertEqual(fid.email, 'jsmith@example.com')

        fid = result[1]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jsmith')
        self.assertEqual(fid.name, 'john smith')
        self.assertEqual(fid.email, None)

        result = matcher.filter(jrae)
        self.assertEqual(len(result), 3)

        fid = result[0]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.name, 'jane rae')
        self.assertEqual(fid.email, None)

        fid = result[1]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.name, 'jane rae doe')
        self.assertEqual(fid.email, 'jane.rae@example.net')

        fid = result[2]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.name, None)
        self.assertEqual(fid.email, 'jrae@example.net')

    def test_filter_identities_with_blacklist(self):
        """Test if identities are filtered when there is a blacklist"""

        # Let's define some identities first
        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', email='jsmith@example.com', source='scm', uuid='jsmith'),
                             Identity(name='John Smith', source='scm', uuid='jsmith'),
                             Identity(name='John Smith JR', source='scm', uuid='jsmith'),
                             Identity(username='jsmith', source='scm', uuid='jsmith'),
                             Identity(email='', source='scm', uuid='jsmith')]

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', email='jane.rae@example.net', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(email='JRAE@example.net', source='scm', uuid='jrae')]

        # Tests
        bl = [MatchingBlacklist(excluded='John Smith'),
              MatchingBlacklist(excluded='jrae@example.net')]

        matcher = EmailNameMatcher(blacklist=bl)

        result = matcher.filter(jsmith)
        self.assertEqual(len(result), 1)

        fid = result[0]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jsmith')
        self.assertEqual(fid.name, 'john smith jr')
        self.assertEqual(fid.email, None)

        result = matcher.filter(jrae)
        self.assertEqual(len(result), 2)

        fid = result[0]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.name, 'jane rae')
        self.assertEqual(fid.email, None)

        fid = result[1]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.name, 'jane rae doe')
        self.assertEqual(fid.email, 'jane.rae@example.net')

    def test_filter_identities_no_strict(self):
        """Test if identities are filtered in no strict mode"""

        # Let's define some identities first
        jsmith = UniqueIdentity(uuid='jsmith')
        jsmith.identities = [Identity(name='John Smith', email='jsmith@example.com', source='scm', uuid='jsmith'),
                             Identity(name='John Smith', source='scm', uuid='jsmith'),
                             Identity(username='jsmith', source='scm', uuid='jsmith'),
                             Identity(email='jsmith@test', source='scm', uuid='jsmith'),
                             Identity(email='', source='scm', uuid='jsmith')]

        jrae = UniqueIdentity(uuid='jrae')
        jrae.identities = [Identity(name='Jane Rae', source='scm', uuid='jrae'),
                           Identity(name='Jane Rae Doe', email='jane.rae@example.net', source='mls', uuid='jrae'),
                           Identity(name='jrae', source='scm', uuid='jrae'),
                           Identity(email='JRAE@example.net', source='scm', uuid='jrae')]

        matcher = EmailNameMatcher(strict=False)

        result = matcher.filter(jsmith)
        self.assertEqual(len(result), 3)

        fid = result[0]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jsmith')
        self.assertEqual(fid.name, 'john smith')
        self.assertEqual(fid.email, 'jsmith@example.com')

        fid = result[1]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jsmith')
        self.assertEqual(fid.name, 'john smith')
        self.assertEqual(fid.email, None)

        fid = result[2]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jsmith')
        self.assertEqual(fid.email, 'jsmith@test')

        result = matcher.filter(jrae)
        self.assertEqual(len(result), 4)

        fid = result[0]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.name, 'jane rae')
        self.assertEqual(fid.email, None)

        fid = result[1]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.name, 'jane rae doe')
        self.assertEqual(fid.email, 'jane.rae@example.net')

        fid = result[2]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.name, 'jrae')
        self.assertEqual(fid.email, None)

        fid = result[3]
        self.assertIsInstance(fid, EmailNameIdentity)
        self.assertEqual(fid.uuid, 'jrae')
        self.assertEqual(fid.name, None)
        self.assertEqual(fid.email, 'jrae@example.net')

    def test_filter_identities_instances(self):
        """Test whether it raises an error when id is not a UniqueIdentity"""

        matcher = EmailNameMatcher()

        self.assertRaises(ValueError, matcher.filter, 'John Smith')
        self.assertRaises(ValueError, matcher.filter, None)

    def test_matching_criteria(self):
        """Test whether it returns the matching criteria keys"""

        criteria = EmailNameMatcher.matching_criteria()

        self.assertListEqual(criteria, ['email', 'name'])


if __name__ == "__main__":
    unittest.main()
