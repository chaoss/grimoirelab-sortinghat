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
from sortinghat.exceptions import MatcherNotSupportedError
from sortinghat.matcher import IdentityMatcher, create_identity_matcher, match
from sortinghat.matching import EmailMatcher, EmailNameMatcher


class TestCreateIdentityMatcher(unittest.TestCase):

    def test_identity_matcher_instance(self):
        """Test if the factory function returns an identity matcher instance"""

        matcher = create_identity_matcher('default')
        self.assertIsInstance(matcher, IdentityMatcher)

        matcher = create_identity_matcher('email')
        self.assertIsInstance(matcher, EmailMatcher)

        matcher = create_identity_matcher('email-name')
        self.assertIsInstance(matcher, EmailNameMatcher)

    def test_identity_matcher_instance_with_blacklist(self):
        """Test if the factory function adds a blacklist to the matcher instance"""

        # The blacklist is empty
        matcher = create_identity_matcher('default')
        self.assertIsInstance(matcher, IdentityMatcher)
        self.assertEqual(len(matcher.blacklist), 0)

        # Create a matcher with a blacklist
        blacklist = [MatchingBlacklist(excluded='JSMITH@example.com'),
                     MatchingBlacklist(excluded='jrae@example.com'),
                     MatchingBlacklist(excluded='jrae@example.net'),
                     MatchingBlacklist(excluded='John Smith'),
                     MatchingBlacklist(excluded='root')]

        matcher = create_identity_matcher('default', blacklist=blacklist)
        self.assertIsInstance(matcher, IdentityMatcher)
        self.assertEqual(len(matcher.blacklist), 5)

    def test_identity_matcher_instance_with_sources_list(self):
        """Test if the factory function adds a sources list to the matcher instance"""

        # The sources list is None
        matcher = create_identity_matcher('default')
        self.assertIsInstance(matcher, IdentityMatcher)
        self.assertEqual(matcher.sources, None)

        # Create a matcher with a sources list
        sources = ['git', 'jira', 'github']

        matcher = create_identity_matcher('default', sources=sources)
        self.assertIsInstance(matcher, IdentityMatcher)
        self.assertEqual(len(matcher.sources), 3)

    def test_identity_matcher_instance_with_strict(self):
        """Test if the factory function adds the strict mode to the matcher instance"""

        matcher = create_identity_matcher('default')
        self.assertIsInstance(matcher, IdentityMatcher)
        self.assertEqual(matcher.strict, True)

        matcher = create_identity_matcher('default', strict=False)
        self.assertIsInstance(matcher, IdentityMatcher)
        self.assertEqual(matcher.strict, False)

    def test_not_supported_matcher(self):
        """Check if an exception is raised when the given matcher type is not supported"""

        self.assertRaises(MatcherNotSupportedError,
                          create_identity_matcher, 'custom')


class TestIdentityMatcher(unittest.TestCase):
    """Test IdentityMatcher class"""

    def test_blacklist(self):
        """Test blacklist contents"""

        m = IdentityMatcher()
        self.assertListEqual(m.blacklist, [])

        m = IdentityMatcher(blacklist=[])
        self.assertListEqual(m.blacklist, [])

        blacklist = [MatchingBlacklist(excluded='JSMITH@example.com'),
                     MatchingBlacklist(excluded='jrae@example.com'),
                     MatchingBlacklist(excluded='jrae@example.net'),
                     MatchingBlacklist(excluded='John Smith'),
                     MatchingBlacklist(excluded='root')]

        m = IdentityMatcher(blacklist=blacklist)

        self.assertListEqual(m.blacklist, ['john smith', 'jrae@example.com',
                                           'jrae@example.net', 'jsmith@example.com',
                                           'root'])

    def test_sources_list(self):
        """Test sources list contents"""

        m = IdentityMatcher()
        self.assertEqual(m.sources, None)

        m = IdentityMatcher(sourecs=[])
        self.assertEqual(m.sources, None)

        sources = ['git', 'Jira', 'GitHub']
        m = IdentityMatcher(sources=sources)

        self.assertListEqual(m.sources, ['git', 'github', 'jira'])

    def test_strict_mode(self):
        """Test strict mode value"""

        m = IdentityMatcher()
        self.assertEqual(m.strict, True)

        m = IdentityMatcher(strict=False)
        self.assertEqual(m.strict, False)


class TestMatch(unittest.TestCase):
    """Test match function"""

    def setUp(self):
        # Add some unique identities

        self.john_smith = UniqueIdentity('John Smith')
        self.john_smith.identities = [Identity(email='jsmith@example.com', name='John Smith',
                                               source='scm', uuid='John Smith'),
                                      Identity(name='John Smith',
                                               source='scm', uuid='John Smith'),
                                      Identity(username='jsmith',
                                               source='scm', uuid='John Smith')]

        self.jsmith = UniqueIdentity('J. Smith')
        self.jsmith.identities = [Identity(name='J. Smith', username='john_smith',
                                           source='alt', uuid='J. Smith'),
                                  Identity(name='John Smith', username='jsmith',
                                           source='alt', uuid='J. Smith'),
                                  Identity(email='jsmith',
                                           source='alt', uuid='J. Smith')]

        self.jane_rae = UniqueIdentity('Jane Rae')
        self.jane_rae.identities = [Identity(name='Janer Rae',
                                             source='mls', uuid='Jane Rae'),
                                    Identity(email='jane.rae@example.net', name='Jane Rae Doe',
                                             source='mls', uuid='Jane Rae')]

        self.js_alt = UniqueIdentity('john_smith')
        self.js_alt.identities = [Identity(name='J. Smith', username='john_smith',
                                           source='scm', uuid='john_smith'),
                                  Identity(username='john_smith',
                                           source='mls', uuid='john_smith'),
                                  Identity(username='Smith. J',
                                           source='mls', uuid='john_smith'),
                                  Identity(email='JSmith@example.com', name='Smith. J',
                                           source='mls', uuid='john_smith')]

        self.jrae = UniqueIdentity('jrae')
        self.jrae.identities = [Identity(email='jrae@example.net', name='Jane Rae Doe',
                                         source='mls', uuid='jrae'),
                                Identity(name='jrae', source='mls', uuid='jrae'),
                                Identity(name='jrae', source='scm', uuid='jrae')]

    def test_match_email(self):
        """Test whether the function finds every possible matching using email matcher"""

        uidentities = [self.jsmith, self.jrae, self.js_alt,
                       self.john_smith, self.jane_rae]

        matcher = EmailMatcher()

        result = match([], matcher)
        self.assertEqual(len(result), 0)

        result = match(uidentities, matcher)

        self.assertEqual(len(result), 4)
        self.assertListEqual(result,
                             [[self.john_smith, self.js_alt],
                              [self.jane_rae], [self.jrae], [self.jsmith]])

    def test_match_email_name(self):
        """Test whether the function finds every possible matching using email-name matcher"""

        uidentities = [self.jsmith, self.jrae, self.js_alt,
                       self.john_smith, self.jane_rae]

        matcher = EmailNameMatcher()

        result = match([], matcher)
        self.assertEqual(len(result), 0)

        result = match(uidentities, matcher)

        self.assertEqual(len(result), 2)
        self.assertListEqual(result,
                             [[self.jsmith, self.john_smith, self.js_alt],
                              [self.jane_rae, self.jrae]])

    def test_match_email_fast_mode(self):
        """Test matching in fast mode using email matcher"""

        uidentities = [self.jsmith, self.jrae, self.js_alt,
                       self.john_smith, self.jane_rae]

        matcher = EmailMatcher()

        result = match([], matcher, fastmode=True)
        self.assertEqual(len(result), 0)

        result = match(uidentities, matcher, fastmode=True)
        self.assertEqual(len(result), 4)
        self.assertListEqual(result,
                             [[self.john_smith, self.js_alt],
                              [self.jane_rae], [self.jrae], [self.jsmith]])

    def test_match_email_name_fast_mode(self):
        """Test matching in fast mode using email-name matcher"""

        uidentities = [self.jsmith, self.jrae, self.js_alt,
                       self.john_smith, self.jane_rae]

        matcher = EmailNameMatcher()

        result = match([], matcher, fastmode=True)
        self.assertEqual(len(result), 0)

        result = match(uidentities, matcher, fastmode=True)

        self.assertEqual(len(result), 2)
        self.assertListEqual(result,
                             [[self.jsmith, self.john_smith, self.js_alt],
                              [self.jane_rae, self.jrae]])

    def test_matcher_error(self):
        """Test if it raises an error when the matcher is not valid"""

        self.assertRaises(TypeError, match, [], None)
        self.assertRaises(TypeError, match, [], "")

    def test_matcher_not_supported_fast_mode(self):
        """Test if it raises and error when a matcher does not supports the fast mode"""

        matcher = IdentityMatcher()

        self.assertRaises(MatcherNotSupportedError,
                          match, [], matcher, True)


if __name__ == "__main__":
    unittest.main()
