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

import re
import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat.db.model import Organization, Domain
from sortinghat.exceptions import InvalidFormatError
from sortinghat.parsing.gitdm import GitdmOrganizationsParser


DOMAINS_INVALID_FORMAT_ERROR = "invalid format on line %(line)s"
ORGS_STREAM_INVALID_ERROR = "stream cannot be empty or None"


class TestBaseCase(unittest.TestCase):
    """Defines common methods for unit tests"""

    def read_file(self, filename):
        with open(filename, 'r') as f:
            content = f.read().decode('UTF-8')
        return content


class TestGitdmDomainsRegEx(unittest.TestCase):
    """Test regular expressions used while parsing Gitdm inputs"""

    def test_lines_to_ignore(self):
        """Check whether it parsers blank or comment lines"""

        parser = re.compile(GitdmOrganizationsParser.LINES_TO_IGNORE_REGEX,
                            re.UNICODE)

        # Parse some valid blank lines
        m = parser.match("")
        self.assertIsNotNone(m)

        m = parser.match("\n\n\n")
        self.assertIsNotNone(m)

        m = parser.match("      \t    \r\n ")
        self.assertIsNotNone(m)

        m = parser.match("\t\t  \n  \t\n")
        self.assertIsNotNone(m)

        # Do not parse invalid blank lines
        m = parser.match("\ndomain organization\n\n")
        self.assertIsNone(m)

        m = parser.match(" domain \t organization  \r\n ")
        self.assertIsNone(m)

        m = parser.match("\t   domain organization\t  \n  \n")
        self.assertIsNone(m)

        # Parse some valid comments
        m = parser.match("#    \t\n\r")
        self.assertIsNotNone(m)

        m = parser.match("#|tcomment #1\r\n")
        self.assertIsNotNone(m)

    def test_domains_line(self):
        """Check whether it parsers domain - organization lines"""

        parser = re.compile(GitdmOrganizationsParser.DOMAINS_LINE_REGEX,
                            re.UNICODE)

        # Parse some valid domain lines
        m = parser.match("example.org    Example")
        self.assertIsNotNone(m)

        m = parser.match("example.org\tExample")
        self.assertIsNotNone(m)

        m = parser.match("example.org    \t  \t  Example/n' Co. ")
        self.assertIsNotNone(m)

        m = parser.match("ex-amp'le.org Example")
        self.assertIsNotNone(m)

        # Do not parse invalid domain lines
        m = parser.match("   example.org   Example")
        self.assertIsNone(m)

        m = parser.match("example.org \n Example")
        self.assertIsNone(m)

        m = parser.match("   example.org   Example\t\n")
        self.assertIsNone(m)

        m = parser.match("\texample.org   Example")
        self.assertIsNone(m)

        m = parser.match("example.org   Exa\tmple")
        self.assertIsNone(m)

        m = parser.match("example.org   Exa\nmple")
        self.assertIsNone(m)

        # Parse some valid comments
        m = parser.match("example.org organization ### comment")
        self.assertIsNotNone(m)

        m = parser.match("domain organization #   \t\r")
        self.assertIsNotNone(m)

        m = parser.match("domain organization\t   #\tcomment #1\r\n")
        self.assertIsNotNone(m)

        # Domains and organizations must start with a
        # alpha numeric or underscores characters

        # These must work
        m = parser.match("__example.org    Example")
        self.assertIsNotNone(m)

        m = parser.match("_example.org    0Example")
        self.assertIsNotNone(m)

        m = parser.match("9example.org    _Example")
        self.assertIsNotNone(m)

        # While these won't work
        m = parser.match("'_example.org    Example")
        self.assertIsNone(m)

        m = parser.match("/example.org    Example")
        self.assertIsNone(m)

        m = parser.match("example.org    'Example")
        self.assertIsNone(m)

        m = parser.match("example.org    /Example")
        self.assertIsNone(m)

        m = parser.match("example.org    -Example")
        self.assertIsNone(m)

        m = parser.match("example.org    ")
        self.assertIsNone(m)

        # Unicode characters
        m = parser.match(u"example.org     Examplé")
        self.assertIsNotNone(m)


class TestGitdmOrganizationsParser(TestBaseCase):
    """Test Gitdm parser with some inputs"""

    def test_valid_organizations_stream(self):
        """Check whether it parses a valid stream"""

        stream = self.read_file('data/gitdm_orgs_valid.txt')

        parser = GitdmOrganizationsParser()
        orgs = [org for org in parser.organizations(stream)]

        # Check parsed organizations
        self.assertEqual(len(orgs), 8)

        # Example entries
        org = orgs[0]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Example')

        doms = org.domains
        self.assertEqual(len(doms), 1)
        self.assertIsInstance(doms[0], Domain)
        self.assertEqual(doms[0].domain, 'example.com')

        org = orgs[1]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Example')

        doms = org.domains
        self.assertEqual(len(doms), 1)
        self.assertIsInstance(doms[0], Domain)
        self.assertEqual(doms[0].domain, 'example.org')

        org = orgs[2]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Example')

        doms = org.domains
        self.assertEqual(len(doms), 1)
        self.assertIsInstance(doms[0], Domain)
        self.assertEqual(doms[0].domain, 'example.net')

        # Bitergia entries
        org = orgs[3]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Bitergia')

        doms = org.domains
        self.assertEqual(len(doms), 1)
        self.assertIsInstance(doms[0], Domain)
        self.assertEqual(doms[0].domain, 'bitergia.com')

        org = orgs[4]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Bitergia')

        doms = org.domains
        self.assertEqual(len(doms), 1)
        self.assertIsInstance(doms[0], Domain)
        self.assertEqual(doms[0].domain, 'bitergia.net')

        org = orgs[5]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Bitergia')

        doms = org.domains
        self.assertEqual(len(doms), 1)
        self.assertIsInstance(doms[0], Domain)
        self.assertEqual(doms[0].domain, 'example.com')

        # GSyC/Libresof entries
        org = orgs[6]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'GSyC/LibreSoft')

        doms = org.domains
        self.assertEqual(len(doms), 1)
        self.assertIsInstance(doms[0], Domain)
        self.assertEqual(doms[0].domain, 'libresoft.es')

        org = orgs[7]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'GSyC/LibreSoft')

        doms = org.domains
        self.assertEqual(len(doms), 1)
        self.assertIsInstance(doms[0], Domain)
        self.assertEqual(doms[0].domain, 'gsyc.es')

    def test_check(self):
        """Test check method"""

        parser = GitdmOrganizationsParser()

        s = self.read_file('data/gitdm_orgs_valid.txt')
        result = parser.check(s)
        self.assertEqual(result, True)

        s = self.read_file('data/gitdm_orgs_valid_alt.txt')
        result = parser.check(s)
        self.assertEqual(result, True)

        s = self.read_file('data/gitdm_orgs_invalid_comments.txt')
        result = parser.check(s)
        self.assertEqual(result, False)

        s = self.read_file('data/gitdm_orgs_invalid_entries.txt')
        result = parser.check(s)
        self.assertEqual(result, False)

        # Error is beyond of the 10 first lines
        s = self.read_file('data/gitdm_orgs_invalid_entries_alt.txt')
        result = parser.check(s)
        self.assertEqual(result, True)

        result = parser.check("")
        self.assertEqual(result, False)

        result = parser.check(None)
        self.assertEqual(result, False)

    def test_not_valid_organizations_stream(self):
        """Check whether it prints an error when parsing invalid streams"""

        parser = GitdmOrganizationsParser()

        with self.assertRaisesRegexp(InvalidFormatError,
                                     DOMAINS_INVALID_FORMAT_ERROR % {'line' : '10'}):
            s1 = self.read_file('data/gitdm_orgs_invalid_comments.txt')
            [org for org in parser.organizations(s1)]

        with self.assertRaisesRegexp(InvalidFormatError,
                                     DOMAINS_INVALID_FORMAT_ERROR % {'line' : '8'}):
            s2 = self.read_file('data/gitdm_orgs_invalid_entries.txt')
            [org for org in parser.organizations(s2)]

    def test_empty_organizations_stream(self):
        """Check whether it raises an exception when the stream is empty"""

        parser = GitdmOrganizationsParser()

        with self.assertRaisesRegexp(InvalidFormatError,
                                     ORGS_STREAM_INVALID_ERROR):
            [org for org in parser.organizations("")]

    def test_none_organizations_stream(self):
        """Check whether it raises an exception when the stream is None"""

        parser = GitdmOrganizationsParser()

        with self.assertRaisesRegexp(InvalidFormatError,
                                     ORGS_STREAM_INVALID_ERROR):
            [org for org in parser.organizations(None)]


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
