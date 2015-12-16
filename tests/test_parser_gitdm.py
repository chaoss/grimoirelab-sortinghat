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

from __future__ import unicode_literals

import datetime
import re
import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat.db.model import UniqueIdentity, Identity, Enrollment, Organization, Domain
from sortinghat.exceptions import InvalidFormatError
from sortinghat.parsing.gitdm import GitdmParser


DOMAINS_INVALID_FORMAT_ERROR = "line %(line)s: invalid format"


class TestBaseCase(unittest.TestCase):
    """Defines common methods for unit tests"""

    def read_file(self, filename):
        if sys.version_info[0] >= 3: # Python 3
            with open(filename, 'r', encoding='UTF-8') as f:
                content = f.read()
        else: # Python 2
            with open(filename, 'r') as f:
                content = f.read().decode('UTF-8')
        return content


class TestGidmParser(TestBaseCase):
    """Test Gitdm parser"""

    def test_aliases_parser(self):
        aliases = self.read_file('data/gitdm_email_aliases_valid.txt')

        parser = GitdmParser(email_aliases=aliases)

        # Parsed unique identities
        uids = parser.identities
        self.assertEqual(len(uids), 2)

        # jdoe@example.com & john_doe@example.net
        uid = uids[0]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jdoe@example.com')

        self.assertIsInstance(uid, UniqueIdentity)

        ids = uid.identities
        self.assertEqual(len(ids), 2)

        id0 = ids[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.name, None)
        self.assertEqual(id0.email, 'jdoe@example.com')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'gitdm')
        self.assertEqual(id0.uuid, None)

        id1 = ids[1]
        self.assertIsInstance(id1, Identity)
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'john_doe@example.net')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'gitdm')
        self.assertEqual(id1.uuid, None)

        self.assertEqual(len(uid.enrollments), 0)

        # jrae@example.net & jrae@example.com
        uid = uids[1]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jrae@example.net')

        ids = uid.identities
        self.assertEqual(len(ids), 2)

        id0 = ids[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.name, None)
        self.assertEqual(id0.email, 'jrae@example.net')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'gitdm')
        self.assertEqual(id0.uuid, None)

        id0 = ids[1]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.name, None)
        self.assertEqual(id0.email, 'jrae@example.com')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'gitdm')
        self.assertEqual(id0.uuid, None)

        self.assertEqual(len(uid.enrollments), 0)

    def test_enrollments_parser(self):
        aliases = self.read_file('data/gitdm_email_aliases_valid.txt')
        email_to_employer = self.read_file('data/gitdm_email_to_employer_valid.txt')

        parser = GitdmParser(email_aliases=aliases,
                             email_to_employer=email_to_employer,
                             source='unknown')

        # Parsed unique identities
        uids = parser.identities
        self.assertEqual(len(uids), 3)

        # jdoe@example.com & john_doe@example.net
        uid = uids[0]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jdoe@example.com')

        self.assertIsInstance(uid, UniqueIdentity)

        ids = uid.identities
        self.assertEqual(len(ids), 2)

        id0 = ids[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.name, None)
        self.assertEqual(id0.email, 'jdoe@example.com')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'unknown')
        self.assertEqual(id0.uuid, None)

        id1 = ids[1]
        self.assertIsInstance(id1, Identity)
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'john_doe@example.net')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'unknown')
        self.assertEqual(id1.uuid, None)

        enrollments = uid.enrollments
        enrollments.sort(key=lambda x: x.organization.name)
        self.assertEqual(len(uid.enrollments), 2)

        rol = uid.enrollments[0]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.organization.name, 'Example Company')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1, 0, 0))

        rol = uid.enrollments[1]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.organization.name, 'LibreSoft')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1, 0, 0))

        # jrae@example.net & jrae@example.com
        uid = uids[1]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jrae@example.net')

        ids = uid.identities
        self.assertEqual(len(ids), 2)

        id0 = ids[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.name, None)
        self.assertEqual(id0.email, 'jrae@example.net')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'unknown')
        self.assertEqual(id0.uuid, None)

        id0 = ids[1]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.name, None)
        self.assertEqual(id0.email, 'jrae@example.com')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'unknown')
        self.assertEqual(id0.uuid, None)

        self.assertEqual(len(uid.enrollments), 1)

        rol = uid.enrollments[0]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.organization.name, 'Bitergia')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1, 0, 0))

        # jsmith@example.com
        uid = uids[2]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jsmith@example.com')

        ids = uid.identities
        self.assertEqual(len(ids), 1)

        id0 = ids[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.name, None)
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'unknown')
        self.assertEqual(id0.uuid, None)

        self.assertEqual(len(uid.enrollments), 2)

        rol = uid.enrollments[0]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.organization.name, 'Bitergia')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(rol.end, datetime.datetime(2015, 1, 1, 0, 0))

        rol = uid.enrollments[1]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.organization.name, 'Example Company')
        self.assertEqual(rol.start, datetime.datetime(2015, 1, 1, 0, 0))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1, 0, 0))

        # Parsed organizations
        orgs = parser.organizations
        self.assertEqual(len(orgs), 3)

        org = orgs[0]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Bitergia')

        org = orgs[1]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Example Company')

        org = orgs[2]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'LibreSoft')

    def test_organizations_parser(self):
        """Check whether it parses a valid organizations file"""

        stream = self.read_file('data/gitdm_orgs_valid.txt')

        parser = GitdmParser(domain_to_employer=stream)

        # Parsed unique identities
        uids = parser.identities
        self.assertEqual(len(uids), 0)

        # Parsed organizations
        orgs = parser.organizations

        self.assertEqual(len(orgs), 3)

        # Bitergia entries
        org = orgs[0]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Bitergia')

        doms = org.domains
        self.assertEqual(len(doms), 3)

        dom = doms[0]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'bitergia.com')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[1]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'bitergia.net')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[2]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'example.com')
        self.assertEqual(dom.is_top_domain, False)

        # Example entries
        org = orgs[1]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Example')

        doms = org.domains
        self.assertEqual(len(doms), 3)

        dom = doms[0]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'example.com')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[1]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'example.org')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[2]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'example.net')
        self.assertEqual(dom.is_top_domain, False)

        # GSyC/Libresof entries
        org = orgs[2]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'GSyC/LibreSoft')

        doms = org.domains
        self.assertEqual(len(doms), 2)

        dom = doms[0]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'libresoft.es')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[1]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'gsyc.es')
        self.assertEqual(dom.is_top_domain, False)

    def test_not_valid_organizations_stream(self):
        """Check whether it raises an error when parsing invalid streams"""

        with self.assertRaisesRegexp(InvalidFormatError,
                                     DOMAINS_INVALID_FORMAT_ERROR % {'line' : '10'}):
            stream = self.read_file('data/gitdm_orgs_invalid_comments.txt')
            GitdmParser(domain_to_employer=stream)

        with self.assertRaisesRegexp(InvalidFormatError,
                                     DOMAINS_INVALID_FORMAT_ERROR % {'line' : '8'}):
            stream = self.read_file('data/gitdm_orgs_invalid_entries.txt')
            GitdmParser(domain_to_employer=stream)


class TestGitdmRegEx(unittest.TestCase):
    """Test regular expressions used while parsing Gitdm inputs"""

    def test_valid_lines(self):
        """Check whether it parses valid lines"""

        parser = re.compile(GitdmParser.VALID_LINE_REGEX, re.UNICODE)

        # Parse some valid lines
        m = parser.match("jdoe@example.com\tExample  Company\t# John Doe")
        self.assertIsNotNone(m)

        m = parser.match("jdoe@example.com\t\tExample < 2010-01-01\t\t# John Doe")
        self.assertIsNotNone(m)

        m = parser.match("jdoe@example.com\tExample  Company")
        self.assertIsNotNone(m)

        m = parser.match("jdoe@example.com\t\t\tjohndoe@example.com")
        self.assertIsNotNone(m)

        m = parser.match("example.org\t\tExample/n' Co. ")
        self.assertIsNotNone(m)

        m = parser.match("jdoe@example.org    Example")
        self.assertIsNotNone(m)

        # Parse some lines with valid comments
        m = parser.match("example.org\torganization\t### comment")
        self.assertIsNotNone(m)

        m = parser.match("jonhdoe@exampl.com\torganization\t#   \t\r")
        self.assertIsNotNone(m)

        m = parser.match("domain\torganization\t#\tcomment #1\r\n")
        self.assertIsNotNone(m)

        m = parser.match(u"example.org\tExamplé")
        self.assertIsNotNone(m)

        # It's weird but it's a valid line
        m = parser.match("jdoe@example.org\tjdoe@exa\tmple.com")
        self.assertIsNotNone(m)

        # These are examples or invalid lines
        m = parser.match("\texample.org\t\tExample")

        m = parser.match("   example.org   Example")
        self.assertIsNone(m)

        m = parser.match("jdoe@example.org\nExample\t\n")
        self.assertIsNone(m)

        m = parser.match("example.org\t\n\tExample")
        self.assertIsNone(m)

        m = parser.match("example.org\tExa\nmple")
        self.assertIsNone(m)

        m = parser.match("domain organization\t   # comment\n\t")
        self.assertIsNone(m)

    def test_lines_to_ignore(self):
        """Check whether it parsers blank or comment lines"""

        parser = re.compile(GitdmParser.LINES_TO_IGNORE_REGEX, re.UNICODE)

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

    def test_email(self):
        """Check email address pattern"""

        parser = re.compile(GitdmParser.EMAIL_ADDRESS_REGEX, re.UNICODE)

        # Parse some valid email addresses
        m = parser.match("johndoe@example.com")
        self.assertIsNotNone(m)

        m = parser.match("jonh.doe@exampel.com")
        self.assertIsNotNone(m)

        m = parser.match("?¡~,123@example.com")
        self.assertIsNotNone(m)

        # Do not parse invalid email addresses
        m = parser.match("jonh@doe@example.com")
        self.assertIsNone(m)

        m = parser.match("   johndoe@example.com")
        self.assertIsNone(m)

        m = parser.match("johndoe@example.com  ")
        self.assertIsNone(m)

        m = parser.match("johndoe@example.com\t")
        self.assertIsNone(m)

        m = parser.match("johndoe@.com")
        self.assertIsNone(m)

    def test_organization(self):
        """Check organization pattern"""

        parser = re.compile(GitdmParser.ORGANIZATION_REGEX, re.UNICODE)

        # Organizations must start with alpha numeric or underscore
        # characters. They can have spaces or other symbols, but
        # cannot include other separators like tabs or #

        # These must work
        m = parser.match("Example")
        self.assertIsNotNone(m)

        m = parser.match("0Example")
        self.assertIsNotNone(m)

        m = parser.match("_Example")
        self.assertIsNotNone(m)

        m = parser.match("My Example")
        self.assertIsNotNone(m)

        m = parser.match("Example\n")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "Example")

        m = parser.match("'Example")
        self.assertIsNotNone(m)

        m = parser.match("/Example")
        self.assertIsNotNone(m)

        m = parser.match("-Example")
        self.assertIsNotNone(m)

        # While these won't work
        m = parser.match("Example   ")
        self.assertIsNone(m)

        m = parser.match("Exa\tmple")
        self.assertIsNone(m)

        m = parser.match("Example #")
        self.assertIsNone(m)

        m = parser.match(" ")
        self.assertIsNone(m)

    def test_domain(self):
        """Check domain pattern"""

        parser = re.compile(GitdmParser.DOMAIN_REGEX, re.UNICODE)

        # Domains must start with alpha numeric or underscore
        # characters.

        # These must work
        m = parser.match("__example.org")
        self.assertIsNotNone(m)

        m = parser.match("9example.org")
        self.assertIsNotNone(m)

        # While these won't work
        m = parser.match("'_example.org")
        self.assertIsNone(m)

        m = parser.match("/example.org")
        self.assertIsNone(m)

        m = parser.match("exa\tmple.org")
        self.assertIsNone(m)

        m = parser.match(" example.org")
        self.assertIsNone(m)

    def test_enrollment(self):
        """Check enrollment pattern"""

        parser = re.compile(GitdmParser.ENROLLMENT_REGEX, re.UNICODE)

        # These must work
        m = parser.match("Example")
        self.assertIsNotNone(m)

        m = parser.match("0Example")
        self.assertIsNotNone(m)

        m = parser.match("_Example")
        self.assertIsNotNone(m)

        m = parser.match("My Example")
        self.assertIsNotNone(m)

        m = parser.match("Example < 2012-01-01")
        self.assertIsNotNone(m)

        m = parser.match("Example, Inc.")
        self.assertIsNotNone(m)

        m = parser.match("'Example")
        self.assertIsNotNone(m)

        m = parser.match("/Example")
        self.assertIsNotNone(m)

        m = parser.match("Example   < 2012-01-01")
        self.assertIsNotNone(m)

        m = parser.match("Exa\tmple")
        self.assertIsNotNone(m)

        # While these won't work
        m = parser.match("Example #")
        self.assertIsNone(m)

        m = parser.match(" ")
        self.assertIsNone(m)

        m = parser.match("Example <")
        self.assertIsNone(m)

        m = parser.match("Example<")
        self.assertIsNone(m)

        m = parser.match("Example < 200-01-01")
        self.assertIsNone(m)

        m = parser.match("Example < 2012-1-1")
        self.assertIsNone(m)

        m = parser.match("Example < 2012-01-1")
        self.assertIsNone(m)

        m = parser.match("Example < 1-1-2001")
        self.assertIsNone(m)

        m = parser.match("Example < 2012-01-01 <")
        self.assertIsNone(m)


if __name__ == "__main__":
    unittest.main(buffer=False, exit=False)
