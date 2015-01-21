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

import datetime
import re
import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.cmd.load import Load,\
    GrimoireIdentitiesLoader, EclipseIdentitiesLoader,\
    GitdmOrganizationsParser
from sortinghat.db.database import Database
from sortinghat.db.model import Organization, Domain
from sortinghat.exceptions import BadFileFormatError, LoadError
from sortinghat.matcher import create_identity_matcher

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


LOAD_IDENTITIES_IVALID_JSON_FORMAT_ERROR = "Error: invalid json format. Expecting ':' delimiter: line 19 column 15 (char 844)"
LOAD_IDENTITIES_MATCHING_ERROR = "Error: mock identity matcher is not supported"
LOAD_IDENTITIES_MISSING_KEYS_ERROR = "Error: invalid json format. Attribute active not found"
LOAD_IDENTITIES_NOT_SUPPORTED_FORMAT = "Error: format not supported"
LOAD_GRIMOIRE_IDS_MISSING_KEYS_ERROR = "invalid json format. Attribute name not found"
LOAD_ECLIPSE_IDS_MISSING_KEYS_ERROR_ALT = "invalid json format. Attribute active not found"


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

DOMAINS_INVALID_FORMAT_ERROR = "invalid format on line %(line)s"


class TestBaseCase(unittest.TestCase):
    """Defines common setup and teardown methods on show unit tests"""

    def setUp(self):
        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to be run in buffered mode')

        # Create a connection to check the contents of the registry
        self.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

        # Create command
        self.kwargs = {'user' : DB_USER,
                       'password' : DB_PASSWORD,
                       'database' : DB_NAME,
                       'host' : DB_HOST,
                       'port' : DB_PORT}
        self.cmd = Load(**self.kwargs)

    def tearDown(self):
        self.db.clear()

    def read_json(self, filename):
        import json

        with open(filename, 'r') as f:
            content = f.read().decode('UTF-8')
            obj = json.loads(content)
        return obj

    def read_file(self, filename):
        with open(filename, 'r') as f:
            content = f.read().decode('UTF-8')
        return content


class TestLoadCommand(TestBaseCase):
    """Load command unit tests"""

    def test_load_identities(self):
        """Test to load identities from a file"""

        self.cmd.run('--identities', 'data/eclipse_identities_valid.json')
        self.cmd.run('--identities', 'data/grimoire_identities_valid.json')

    def test_load_identities_with_default_matching(self):
        """Test to load identities from a file using default matching"""

        self.cmd.run('--identities', '--matching', 'default',
                     'data/eclipse_identities_valid.json')
        self.cmd.run('--identities', '--matching', 'default',
                     'data/grimoire_identities_valid.json')

    def test_load_identities_invalid_file(self):
        """Test whether it prints error messages while reading invalid files"""

        self.cmd.run('--identities', 'data/eclipse_identities_invalid_file.json')
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, LOAD_IDENTITIES_IVALID_JSON_FORMAT_ERROR)

        self.cmd.run('--identities', 'data/identities_format_not_supported.json')
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, LOAD_IDENTITIES_NOT_SUPPORTED_FORMAT)

    def test_load_invalid_identity_matcher(self):
        """Test errors on invalid or not supported identity matcher"""

        self.cmd.run('--identities', '--matching', 'mock',
                     'data/eclipse_identities_valid.json')

        self.cmd.run('--identities', 'data/eclipse_identities_invalid_file.json')
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, LOAD_IDENTITIES_MATCHING_ERROR)

    def test_load_organizations(self):
        """Test to load organizations from a file"""

        self.cmd.run('--orgs', 'data/gitdm_orgs_valid.txt')

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_DOMAINS_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_DOMAINS_OUTPUT_WARNING)

    def test_load_organizations_overwrite(self):
        """Test to load organizations from a file with overwrite parameter set"""

        self.cmd.run('--orgs', '--overwrite',
                     'data/gitdm_orgs_valid.txt')
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_DOMAINS_OVERWRITE_OUTPUT)

    def test_load_organizations_invalid_file(self):
        """Test whether it prints error messages while reading invalid files"""

        self.cmd.run('--orgs', 'data/gitdm_orgs_invalid_comments.txt')
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, "Error: invalid format on line 10")

        self.cmd.run('--orgs', 'data/gitdm_orgs_invalid_entries.txt')
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, "Error: invalid format on line 8")


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


class TestLoadImportIdentities(TestBaseCase):
    """Test import_identities method with some inputs"""

    def test_valid_identities_files(self):
        """Check insertion of valid data from files with different formats"""

        # Metrics Grimoire format file
        f = open('data/grimoire_identities_valid.json', 'r')
        self.cmd.import_identities(f)

        # Eclipse format file
        f = open('data/eclipse_identities_valid.json', 'r')
        self.cmd.import_identities(f)

        # Check the contents of the registry. It inserts
        # only 5 identities because one of them is duplicated
        uidentities = api.unique_identities(self.db)
        self.assertEqual(len(uidentities), 5)

        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 3)

    def test_valid_identities_with_default_matching(self):
        """Check insertion, matching and merging of valid data from files with different formats"""

        # Metrics Grimoire format file
        f = open('data/grimoire_identities_valid.json', 'r')
        self.cmd.import_identities(f, matching='default')

        # Eclipse format file
        f = open('data/eclipse_identities_valid.json', 'r')
        self.cmd.import_identities(f, matching='default')

        # Check the contents of the registry. It inserts
        # only 4 identities because one of them is duplicated
        # and there are some matches of 'John Doe'
        uidentities = api.unique_identities(self.db)
        self.assertEqual(len(uidentities), 4)

        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 3)

    def test_setting_source_param(self):
        """Check if identities are imported setting the source param"""

        f = open('data/eclipse_identities_valid.json', 'r')

        self.cmd.import_identities(f, 'scm')

        # Check the contents of the registry
        uidentities = api.unique_identities(self.db)
        self.assertEqual(len(uidentities), 2)

        # John Smith unique identity
        uid0 = uidentities[0]
        self.assertEqual(uid0.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(len(uid0.identities), 2)

        id0 = uid0.identities[0]
        self.assertEqual(id0.id, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(id0.source, 'scm')

        id1 = uid0.identities[1]
        self.assertEqual(id1.id, 'bc3b356ba009880d3f2a25dfa32306ec4de7d8cf')
        self.assertEqual(id1.source, 'scm')

        # John Doe unique identity
        uid1 = uidentities[1]
        self.assertEqual(uid1.uuid, '8e9eac4c6449d2661d66dc62c1752529f935f0b1')
        self.assertEqual(len(uid1.identities), 1)

        id1 = uid1.identities[0]
        self.assertEqual(id1.id, '8e9eac4c6449d2661d66dc62c1752529f935f0b1')
        self.assertEqual(id1.source, 'scm')

    def test_not_valid_identities_file(self):
        """Check whether it prints an error when parsing invalid files"""

        f1 = open('data/eclipse_identities_invalid_file.json', 'r')
        self.cmd.import_identities(f1)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, LOAD_IDENTITIES_IVALID_JSON_FORMAT_ERROR)
        f1.close()

        f2 = open('data/eclipse_identities_missing_keys.json', 'r')
        self.cmd.import_identities(f2)
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, LOAD_IDENTITIES_MISSING_KEYS_ERROR)
        f2.close()

    def test_invalid_file(self):
        """Check if it raises a RuntimeError when an invalid file object is given"""

        self.assertRaises(RuntimeError, self.cmd.import_identities, None)
        self.assertRaises(RuntimeError, self.cmd.import_identities, 1)

    def test_not_supported_format(self):
        """Check if it prints an error when a format is not supported"""

        f = open('data/identities_format_not_supported.json', 'r')

        self.cmd.import_identities(f)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_NOT_SUPPORTED_FORMAT)

        f.close()

    def test_invalid_matching_method(self):
        """Check if it fails when an invalid matching method is given"""

        f = open('data/eclipse_identities_valid.json', 'r')

        self.cmd.import_identities(f, matching='mock')

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_MATCHING_ERROR)

        f.close()


class TestGrimoireIdentitiesLoader(TestBaseCase):
    """Test Metrics Grimoire loader"""

    def test_valid_identities_file(self):
        """Check insertion of valid data from a file"""

        identities = self.read_json('data/grimoire_identities_valid.json')

        loader = GrimoireIdentitiesLoader(self.db)
        loader.warning = sys.stdout.write
        loader.load(identities, 'unknown')

        # Check the contents of the registry
        uidentities = api.unique_identities(self.db)
        self.assertEqual(len(uidentities), 4)

        # Jane Rae
        uid0 = uidentities[0]
        self.assertEqual(uid0.uuid, '24f76417b78d41f409d10e70bb3adfbccb21d6a9')
        self.assertEqual(len(uid0.identities), 1)

        id0 = uid0.identities[0]
        self.assertEqual(id0.id, '24f76417b78d41f409d10e70bb3adfbccb21d6a9')
        self.assertEqual(id0.name, None)
        self.assertEqual(id0.email, None)
        self.assertEqual(id0.username, 'jrae')
        self.assertEqual(id0.uuid, '24f76417b78d41f409d10e70bb3adfbccb21d6a9')
        self.assertEqual(id0.source, 'unknown')

        # John Smith
        uid1 = uidentities[1]
        self.assertEqual(uid1.uuid, '2cb7f5d70a3549f35f995d27085c14ea81c529cd')
        self.assertEqual(len(uid1.identities), 1)

        id0 = uid1.identities[0]
        self.assertEqual(id0.id, '2cb7f5d70a3549f35f995d27085c14ea81c529cd')
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, None)
        self.assertEqual(id0.username, 'jsmith')
        self.assertEqual(id0.uuid, '2cb7f5d70a3549f35f995d27085c14ea81c529cd')
        self.assertEqual(id0.source, 'unknown')

        # John Doe first unique identity
        uid2 = uidentities[2]
        self.assertEqual(uid2.uuid, 'a5923b2880b45315d2889c41100ed0db5cd01903')
        self.assertEqual(len(uid2.identities), 1)

        id0 = uid2.identities[0]
        self.assertEqual(id0.id, 'a5923b2880b45315d2889c41100ed0db5cd01903')
        self.assertEqual(id0.name, 'John Doe')
        self.assertEqual(id0.email, 'jdoe@example.com')
        self.assertEqual(id0.username, 'jdoe')
        self.assertEqual(id0.uuid, 'a5923b2880b45315d2889c41100ed0db5cd01903')
        self.assertEqual(id0.source, 'unknown')

        # John Doe second unique identity
        uid3 = uidentities[3]
        self.assertEqual(uid3.uuid, 'd4e07b257232ca7a0514a03c8d324ba327cc6934')
        self.assertEqual(len(uid3.identities), 1)

        id0 = uid3.identities[0]
        self.assertEqual(id0.id, 'd4e07b257232ca7a0514a03c8d324ba327cc6934')
        self.assertEqual(id0.name, 'John Doe')
        self.assertEqual(id0.email, 'jdoe@example.com')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.uuid, 'd4e07b257232ca7a0514a03c8d324ba327cc6934')
        self.assertEqual(id0.source, 'unknown')

    def test_valid_identities_with_default_matching(self):
        """Check insertion, matching and merging of valid data from a file"""

        identities = self.read_json('data/grimoire_identities_valid.json')
        matcher = create_identity_matcher('default')

        loader = GrimoireIdentitiesLoader(self.db)
        loader.warning = sys.stdout.write
        loader.load(identities, 'unknown', matcher)

        # Check the contents of the registry
        uidentities = api.unique_identities(self.db)
        self.assertEqual(len(uidentities), 3)

        # Jane Rae
        uid0 = uidentities[0]
        self.assertEqual(uid0.uuid, '24f76417b78d41f409d10e70bb3adfbccb21d6a9')
        self.assertEqual(len(uid0.identities), 1)

        # John Smith
        uid1 = uidentities[1]
        self.assertEqual(uid1.uuid, '2cb7f5d70a3549f35f995d27085c14ea81c529cd')
        self.assertEqual(len(uid1.identities), 1)

        # John Doe identities were merged into one
        uid2 = uidentities[2]
        self.assertEqual(uid2.uuid, 'd4e07b257232ca7a0514a03c8d324ba327cc6934')
        self.assertEqual(len(uid2.identities), 2)

        id0 = uid2.identities[0]
        self.assertEqual(id0.id, 'a5923b2880b45315d2889c41100ed0db5cd01903')
        self.assertEqual(id0.name, 'John Doe')
        self.assertEqual(id0.email, 'jdoe@example.com')
        self.assertEqual(id0.username, 'jdoe')
        self.assertEqual(id0.uuid, 'd4e07b257232ca7a0514a03c8d324ba327cc6934')
        self.assertEqual(id0.source, 'unknown')

        id1 = uid2.identities[1]
        self.assertEqual(id1.id, 'd4e07b257232ca7a0514a03c8d324ba327cc6934')
        self.assertEqual(id1.name, 'John Doe')
        self.assertEqual(id1.email, 'jdoe@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.uuid, 'd4e07b257232ca7a0514a03c8d324ba327cc6934')
        self.assertEqual(id1.source, 'unknown')

    def test_not_valid_schema(self):
        """Check whether it raises an error when loading invalid files"""

        loader = GrimoireIdentitiesLoader(self.db)
        loader.warning = sys.stdout.write

        ids0 = self.read_json('data/grimoire_identities_missing_keys.json')
        self.assertRaisesRegexp(LoadError, LOAD_GRIMOIRE_IDS_MISSING_KEYS_ERROR,
                                loader.load, ids0, 'unknown')


class TestEclipseIdentitiesLoader(TestBaseCase):
    """Test Eclipse loader"""

    def test_valid_identities_file(self):
        """Check insertion of valid data from a file"""

        identities = self.read_json('data/eclipse_identities_valid.json')

        loader = EclipseIdentitiesLoader(self.db)
        loader.warning = sys.stdout.write
        loader.load(identities, 'unknown')

        # Check the contents of the registry
        uidentities = api.unique_identities(self.db)
        self.assertEqual(len(uidentities), 2)

        # John Smith unique identity
        uid0 = uidentities[0]
        self.assertEqual(uid0.uuid, '924c44459f46e2375a94c3b2f517d866a1032cbf')
        self.assertEqual(len(uid0.identities), 2)

        id0 = uid0.identities[0]
        self.assertEqual(id0.id, '0fc271807a0c3107198ab6d51f21aad9f97465fc')
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, 'jsmith@bitergia.com')
        self.assertEqual(id0.username, 'jsmith')
        self.assertEqual(id0.uuid, '924c44459f46e2375a94c3b2f517d866a1032cbf')
        self.assertEqual(id0.source, 'unknown')

        id1 = uid0.identities[1]
        self.assertEqual(id1.id, '924c44459f46e2375a94c3b2f517d866a1032cbf')
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, 'jsmith')
        self.assertEqual(id1.uuid, '924c44459f46e2375a94c3b2f517d866a1032cbf')
        self.assertEqual(id1.source, 'unknown')

        enrollments = api.enrollments(self.db, uid0.uuid)
        self.assertEqual(len(enrollments), 2)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Bitergia')
        self.assertEqual(rol0.init, datetime.datetime(2011, 1, 1))
        self.assertEqual(rol0.end, datetime.datetime(2100, 1, 1))

        rol1 = enrollments[1]
        self.assertEqual(rol1.organization.name, 'Example')
        self.assertEqual(rol1.init, datetime.datetime(2010, 1, 1))
        self.assertEqual(rol1.end, datetime.datetime(2011, 1, 1))

        # John Doe unique identity
        uid1 = uidentities[1]
        self.assertEqual(uid1.uuid, 'a5923b2880b45315d2889c41100ed0db5cd01903')
        self.assertEqual(len(uid1.identities), 1)

        id0 = uid1.identities[0]
        self.assertEqual(id0.id, 'a5923b2880b45315d2889c41100ed0db5cd01903')
        self.assertEqual(id0.name, 'John Doe')
        self.assertEqual(id0.email, 'jdoe@example.com')
        self.assertEqual(id0.username, 'jdoe')
        self.assertEqual(id0.uuid, 'a5923b2880b45315d2889c41100ed0db5cd01903')
        self.assertEqual(id0.source, 'unknown')

        enrollments = api.enrollments(self.db, uid1.uuid)
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Example')
        self.assertEqual(rol0.init, datetime.datetime(2010, 1, 1))
        self.assertEqual(rol0.end, datetime.datetime(2100, 1, 1))

    def test_valid_identities_with_default_matching(self):
        """Check insertion, matching and merging of valid data from a file"""

        identities = self.read_json('data/eclipse_identities_valid.json')
        matcher = create_identity_matcher('default')

        loader = EclipseIdentitiesLoader(self.db)
        loader.warning = sys.stdout.write

        # Due to how Eclipse files are generated, each entry belongs to
        # a unique identity and all its different identities. That's why
        # we have to insert some identities first to check matching and
        # merge processes.
        api.add_identity(self.db, 'test', 'jdoe@example.com', None, 'jdoe')
        api.add_identity(self.db, 'test', 'jsmith@bitergia.com', None, None)

        loader.load(identities, 'unknown', matcher)

        uidentities = api.unique_identities(self.db)
        self.assertEqual(len(uidentities), 2)

        # John Smith unique identity
        uid0 = uidentities[0]
        self.assertEqual(uid0.uuid, 'b1e0bf50af778fc8190d48eafe83b42e06529424')
        self.assertEqual(len(uid0.identities), 3)

        id0 = uid0.identities[0]
        self.assertEqual(id0.id, '0fc271807a0c3107198ab6d51f21aad9f97465fc')
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, 'jsmith@bitergia.com')
        self.assertEqual(id0.username, 'jsmith')
        self.assertEqual(id0.uuid, 'b1e0bf50af778fc8190d48eafe83b42e06529424')
        self.assertEqual(id0.source, 'unknown')

        id1 = uid0.identities[1]
        self.assertEqual(id1.id, '924c44459f46e2375a94c3b2f517d866a1032cbf')
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, 'jsmith')
        self.assertEqual(id1.uuid, 'b1e0bf50af778fc8190d48eafe83b42e06529424')
        self.assertEqual(id1.source, 'unknown')

        id2 = uid0.identities[2]
        self.assertEqual(id2.id, 'b1e0bf50af778fc8190d48eafe83b42e06529424')
        self.assertEqual(id2.name, None)
        self.assertEqual(id2.email, 'jsmith@bitergia.com')
        self.assertEqual(id2.username, None)
        self.assertEqual(id2.uuid, 'b1e0bf50af778fc8190d48eafe83b42e06529424')
        self.assertEqual(id2.source, 'test')

        enrollments = api.enrollments(self.db, uid0.uuid)
        self.assertEqual(len(enrollments), 2)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Bitergia')
        self.assertEqual(rol0.init, datetime.datetime(2011, 1, 1))
        self.assertEqual(rol0.end, datetime.datetime(2100, 1, 1))

        rol1 = enrollments[1]
        self.assertEqual(rol1.organization.name, 'Example')
        self.assertEqual(rol1.init, datetime.datetime(2010, 1, 1))
        self.assertEqual(rol1.end, datetime.datetime(2011, 1, 1))

        # John Doe unique identity
        uid1 = uidentities[1]
        self.assertEqual(uid1.uuid, 'c0259e8a627ed751a812760e0e201f61a9cb46be')
        self.assertEqual(len(uid1.identities), 2)

        id0 = uid1.identities[0]
        self.assertEqual(id0.id, 'a5923b2880b45315d2889c41100ed0db5cd01903')
        self.assertEqual(id0.name, 'John Doe')
        self.assertEqual(id0.email, 'jdoe@example.com')
        self.assertEqual(id0.username, 'jdoe')
        self.assertEqual(id0.uuid, 'c0259e8a627ed751a812760e0e201f61a9cb46be')
        self.assertEqual(id0.source, 'unknown')

        id1 = uid1.identities[1]
        self.assertEqual(id1.id, 'c0259e8a627ed751a812760e0e201f61a9cb46be')
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jdoe@example.com')
        self.assertEqual(id1.username, 'jdoe')
        self.assertEqual(id1.uuid, 'c0259e8a627ed751a812760e0e201f61a9cb46be')
        self.assertEqual(id1.source, 'test')

        enrollments = api.enrollments(self.db, uid1.uuid)
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Example')
        self.assertEqual(rol0.init, datetime.datetime(2010, 1, 1))
        self.assertEqual(rol0.end, datetime.datetime(2100, 1, 1))

    def test_not_valid_schema(self):
        """Check whether it raises an error when loading invalid files"""

        loader = EclipseIdentitiesLoader(self.db)
        loader.warning = sys.stdout.write

        ids0 = self.read_json('data/eclipse_identities_missing_keys.json')
        self.assertRaisesRegexp(LoadError, LOAD_ECLIPSE_IDS_MISSING_KEYS_ERROR_ALT,
                                loader.load, ids0, 'unknown')


class TestLoadImportOrganizations(TestBaseCase):
    """Test import_organizations method with some inputs"""

    def test_valid_organizations_file(self):
        """Check insertion of valid data from a file"""

        f = open('data/gitdm_orgs_valid.txt', 'r')

        self.cmd.import_organizations(f)

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
        """Test whether domains are reassigned when overwrite is given"""

        f = open('data/gitdm_orgs_valid.txt', 'r')

        self.cmd.import_organizations(f, True)

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
        f = open('data/gitdm_orgs_valid_alt.txt', 'r')

        self.cmd.import_organizations(f, True)

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

    def test_not_valid_organizations_file(self):
        """Check whether it prints an error when parsing invalid files"""

        f1 = open('data/gitdm_orgs_invalid_comments.txt', 'r')
        self.cmd.import_organizations(f1)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, "Error: invalid format on line 10")
        f1.close()

        f2 = open('data/gitdm_orgs_invalid_entries.txt', 'r')
        self.cmd.import_organizations(f2)
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, "Error: invalid format on line 8")
        f2.close()

    def test_invalid_file(self):
        """Check if it raises a RuntimeError when an invalid file object is given"""

        self.assertRaises(RuntimeError, self.cmd.import_organizations, None)
        self.assertRaises(RuntimeError, self.cmd.import_organizations, 1)

class TestGitdmOrganizationsParser(TestBaseCase):
    """Test Gitdm parser with some inputs"""

    def test_valid_organizations_file(self):
        """Check whether it parses a valid file"""

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

    def test_not_valid_organizations_file(self):
        """Check whether it prints an error when parsing invalid files"""

        parser = GitdmOrganizationsParser()

        with self.assertRaisesRegexp(BadFileFormatError,
                                     DOMAINS_INVALID_FORMAT_ERROR % {'line' : '10'}):
            s1 = self.read_file('data/gitdm_orgs_invalid_comments.txt')
            [org for org in parser.organizations(s1)]

        with self.assertRaisesRegexp(BadFileFormatError,
                                     DOMAINS_INVALID_FORMAT_ERROR % {'line' : '8'}):
            s2 = self.read_file('data/gitdm_orgs_invalid_entries.txt')
            [org for org in parser.organizations(s2)]


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
