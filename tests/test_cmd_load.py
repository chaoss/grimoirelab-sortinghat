#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Bitergia
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

from sortinghat import api
from sortinghat.cmd.load import Load, LINES_TO_IGNORE_REGEX, DOMAINS_LINE_REGEX
from sortinghat.db.database import Database

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


LOAD_DOMAINS_OUTPUT = """Domain example.com added to organization Example
Domain example.org added to organization Example
Domain example.net added to organization Example
Domain bitergia.com added to organization Bitergia
Domain bitergia.net added to organization Bitergia
Domain libresoft.es added to organization GSyC/LibreSoft
Domain gsyc.es added to organization GSyC/LibreSoft"""

LOAD_DOMAINS_OUTPUT_WARNING = """Warning: example.com already exists in the registry. Not updated."""

LOAD_DOMAINS_OVERWRITE_OUTPUT = """Domain example.com added to organization Example
Domain example.org added to organization Example
Domain example.net added to organization Example
Domain bitergia.com added to organization Bitergia
Domain bitergia.net added to organization Bitergia
Domain example.com added to organization Bitergia
Domain libresoft.es added to organization GSyC/LibreSoft
Domain gsyc.es added to organization GSyC/LibreSoft"""


class TestLoadCommand(unittest.TestCase):
    """Load command unit tests"""

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create a connection to check the contents of the registry
        self.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' :DB_NAME,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Load(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def test_load_domains(self):
        """Test to load domains from a file"""

        self.cmd.run('--domains', 'data/domains_orgs_valid.txt')

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_DOMAINS_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_DOMAINS_OUTPUT_WARNING)

    def test_load_domains_overwrite(self):
        """Test to load domains from a file with overwrite parameter set"""

        self.cmd.run('--domains', '--overwrite',
                     'data/domains_orgs_valid.txt')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_DOMAINS_OVERWRITE_OUTPUT)

    def test_load_domains_invalid_file(self):
        """Test whether it prints error messages while reading invalid files"""

        self.cmd.run('--domains', 'data/domains_orgs_invalid_comments.txt')
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, "Error: invalid format on line 10")

        self.cmd.run('--domains', 'data/domains_orgs_invalid_entries.txt')
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, "Error: invalid format on line 8")


class TestDomainsRegEx(unittest.TestCase):
    """Test regular expressions used while parsing domains inputs"""

    def test_lines_to_ignore(self):
        """Check whether it parsers blank or comment lines"""

        parser = re.compile(LINES_TO_IGNORE_REGEX)

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

        parser = re.compile(DOMAINS_LINE_REGEX, re.UNICODE)

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


class TestLoadImportDomains(unittest.TestCase):
    """Test import_domains method with some inputs"""

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create a connection to check the contents of the registry
        self.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' :DB_NAME,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Load(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def test_valid_domain_file(self):
        """Check insertion of valid data from a file"""

        f = open('data/domains_orgs_valid.txt', 'r')

        self.cmd.import_domains(f)

        # Check the contents of the registry
        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 3)

        # Bitergia organization
        org1 = orgs[0]
        self.assertEqual(org1.name, 'Bitergia')

        doms1 = org1.domains
        self.assertEqual(len(doms1), 2)
        self.assertEqual(doms1[0].domain, 'bitergia.com')
        self.assertEqual(doms1[1].domain, 'bitergia.net')

        # Example organization
        org2 = orgs[1]
        self.assertEqual(org2.name, 'Example')

        doms2 = org2.domains
        self.assertEqual(len(doms2), 3)
        self.assertEqual(doms2[0].domain, 'example.com')
        self.assertEqual(doms2[1].domain, 'example.org')
        self.assertEqual(doms2[2].domain, 'example.net')

        # LibreSoft organization
        org3 = orgs[2]
        self.assertEqual(org3.name, 'GSyC/LibreSoft')

        doms3 = org3.domains
        self.assertEqual(len(doms3), 2)
        self.assertEqual(doms3[0].domain, 'libresoft.es')
        self.assertEqual(doms3[1].domain, 'gsyc.es')

        f.close()

    def test_overwrite_domains(self):
        """Test whether domains are reasigned when overwrite is given"""

        f = open('data/domains_orgs_valid.txt', 'r')

        self.cmd.import_domains(f, True)

        # Check the contents of the registry
        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 3)

        # Bitergia organization
        org1 = orgs[0]
        self.assertEqual(org1.name, 'Bitergia')

        doms1 = org1.domains
        self.assertEqual(len(doms1), 3)
        self.assertEqual(doms1[0].domain, 'example.com')
        self.assertEqual(doms1[1].domain, 'bitergia.com')
        self.assertEqual(doms1[2].domain, 'bitergia.net')

        # Example organization
        org2 = orgs[1]
        self.assertEqual(org2.name, 'Example')

        doms2 = org2.domains
        self.assertEqual(len(doms2), 2)
        self.assertEqual(doms2[0].domain, 'example.org')
        self.assertEqual(doms2[1].domain, 'example.net')

        f.close()

    def test_import_to_non_empty_registry(self):
        """Test load process in a registry with some contents"""

        # First, load some data
        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com')

        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.net')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')

        # Import new data, overwriting existing relationships
        f = open('data/domains_orgs_valid_alt.txt', 'r')

        self.cmd.import_domains(f, True)

        # Check the contents of the registry
        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 5)

        # Alt'Co. organization
        org1 = orgs[0]
        self.assertEqual(org1.name, 'Alt\'Co.')

        doms1 = org1.domains
        self.assertEqual(len(doms1), 1)
        self.assertEqual(doms1[0].domain, 'alt-co.com')

        # Bitergia organization
        org2 = orgs[1]
        self.assertEqual(org2.name, 'Bitergia')

        doms2 = org2.domains
        self.assertEqual(len(doms2), 1)
        self.assertEqual(doms2[0].domain, 'bitergia.com')

        # Example organization
        org3 = orgs[2]
        self.assertEqual(org3.name, 'Example')

        doms3 = org3.domains
        self.assertEqual(len(doms3), 4)
        self.assertEqual(doms3[0].domain, 'example.com')
        self.assertEqual(doms3[1].domain, 'bitergia.net')
        self.assertEqual(doms3[2].domain, 'example.org')
        self.assertEqual(doms3[3].domain, 'example.net')

        # GSyC organizations
        org4 = orgs[3]
        self.assertEqual(org4.name, 'GSyC')

        doms4 = org4.domains
        self.assertEqual(len(doms4), 2)
        self.assertEqual(doms4[0].domain, 'gsyc.escet.urjc.es')
        self.assertEqual(doms4[1].domain, 'gsyc.es')

        # LibreSoft organization
        org5 = orgs[4]
        self.assertEqual(org5.name, 'GSyC/LibreSoft')

        doms5 = org5.domains
        self.assertEqual(len(doms5), 1)
        self.assertEqual(doms5[0].domain, 'libresoft.es')

    def test_not_valid_domain_file(self):
        """Check whether it prints an error when parsing invalid files"""

        f1 = open('data/domains_orgs_invalid_comments.txt', 'r')
        self.cmd.import_domains(f1)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, "Error: invalid format on line 10")
        f1.close()

        f2 = open('data/domains_orgs_invalid_entries.txt', 'r')
        self.cmd.import_domains(f2)
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, "Error: invalid format on line 8")
        f2.close()

    def test_invalid_file(self):
        """Check if it raises a RuntimeError when an invalid file object is given"""

        self.assertRaises(RuntimeError, self.cmd.import_domains, None)
        self.assertRaises(RuntimeError, self.cmd.import_domains, 1)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
