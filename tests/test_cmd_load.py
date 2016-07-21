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

import datetime
import sys
import unittest
import warnings

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.load import Load
from sortinghat.db.model import Country
from sortinghat.parsing.sh import SortingHatParser
from sortinghat.exceptions import CODE_MATCHER_NOT_SUPPORTED_ERROR, CODE_INVALID_FORMAT_ERROR

from tests.base import TestCommandCaseBase


LOAD_BLACKLIST_EMPTY_STRINGS_ERROR = "Error: invalid json format. Blacklist entries cannot be null or empty"
LOAD_IDENTITIES_INVALID_JSON_FORMAT_ERROR = "Error: invalid json format. Expecting ',' delimiter: line 86 column 17 (char 2821)"
LOAD_IDENTITIES_MISSING_KEYS_ERROR = "Error: invalid json format. Attribute uuid not found"
LOAD_IDENTITIES_MATCHING_ERROR = "Error: mock identity matcher is not supported"
LOAD_ORGS_INVALID_FORMAT_ERROR = r"Error: invalid json format\. Expecting .+ line \d+ column \d+ \(char \d+\)"
LOAD_ORGS_MISSING_KEYS_ERROR = "Error: invalid json format. Attribute is_top not found"
LOAD_ORGS_IS_TOP_ERROR = "Error: invalid json format. 'is_top' must have a bool value"

# Output

LOAD_OUTPUT = """Domain api.bitergia.com added to organization Bitergia
Domain bitergia.com added to organization Bitergia
Domain bitergia.net added to organization Bitergia
Domain test.bitergia.com added to organization Bitergia
Domain example.com added to organization Example
Domain example.net added to organization Example
Loading blacklist...
Entry  added to the blacklist
Entry  added to the blacklist
2/2 blacklist entries loaded
Loading unique identities...
+ 03e12d00e37fd45593c49a5a5a1652deca4cf302 (old 03e12d00e37fd45593c49a5a5a1652deca4cf302) loaded
+ 52e0aa0a14826627e633fd15332988686b730ab3 (old 52e0aa0a14826627e633fd15332988686b730ab3) loaded
2/3 unique identities loaded"""

# Identities outputs

LOAD_IDENTITIES_OUTPUT = """Loading blacklist...
Entry  added to the blacklist
Entry  added to the blacklist
2/2 blacklist entries loaded
Loading unique identities...
+ 03e12d00e37fd45593c49a5a5a1652deca4cf302 (old 03e12d00e37fd45593c49a5a5a1652deca4cf302) loaded
+ 52e0aa0a14826627e633fd15332988686b730ab3 (old 52e0aa0a14826627e633fd15332988686b730ab3) loaded
2/3 unique identities loaded"""

LOAD_IDENTITIES_OUTPUT_ERROR = """Error: not enough info to load 0000000000000000000000000000000000000000 unique identity. Skipping."""

# Organization outputs

LOAD_SH_ORGS_OUTPUT = """Domain api.bitergia.com added to organization Bitergia
Domain bitergia.com added to organization Bitergia
Domain bitergia.net added to organization Bitergia
Domain test.bitergia.com added to organization Bitergia
Domain example.net added to organization Bitergia
Domain example.com added to organization Example"""

LOAD_ORGS_OVERWRITE_OUTPUT = """Domain api.bitergia.com added to organization Bitergia
Domain bitergia.com added to organization Bitergia
Domain bitergia.net added to organization Bitergia
Domain test.bitergia.com added to organization Bitergia
Domain example.net added to organization Bitergia
Domain example.com added to organization Example
Domain example.net added to organization Example"""

LOAD_ORGS_OUTPUT_WARNING = """Warning: example.net (Bitergia) already exists in the registry. Not updated."""


class TestLoadCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on loadunit tests"""

    cmd_klass = Load

    def get_parser(self, filename):
        if sys.version_info[0] >= 3: # Python 3
            with open(filename, 'r', encoding='UTF-8') as f:
                content = f.read()
        else: # Python 2
            with open(filename, 'r') as f:
                content = f.read().decode('UTF-8')
        return SortingHatParser(content)

    def sort_identities(self, ids):
        return sorted(ids, key=lambda x: x.id)

    def load_test_dataset(self):
        # Add country
        with self.db.connect() as session:
            # Add a country
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)


class TestLoadCommand(TestLoadCaseBase):
    """Load command unit tests"""

    def test_load(self):
        """Test to load identities and organizations from a file"""

        code = self.cmd.run('data/sortinghat_valid.json')
        self.assertEqual(code, CMD_SUCCESS)

        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 3)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_OUTPUT)

    def test_load_identities(self):
        """Test to load identities from a file"""

        code = self.cmd.run('--identities', 'data/sortinghat_valid.json')
        self.assertEqual(code, CMD_SUCCESS)

        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        # This has imported the organizations from the enrollments,
        # not thouse from organizations section
        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 2)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_OUTPUT_ERROR)

    def test_load_identities_with_default_matching(self):
        """Test to load identities from a file using default matching"""

        code = self.cmd.run('--identities', '--matching', 'default',
                            'data/sortinghat_valid.json')
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_OUTPUT_ERROR)

    def test_load_identities_invalid_file(self):
        """Test whether it prints error messages while reading invalid files"""

        code = self.cmd.run('--identities', 'data/sortinghat_invalid.json')
        self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, LOAD_IDENTITIES_INVALID_JSON_FORMAT_ERROR)

    def test_load_organizations(self):
        """Test to load organizations from a file"""

        code = self.cmd.run('--orgs', 'data/sortinghat_orgs_valid.json')
        self.assertEqual(code, CMD_SUCCESS)

        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 0)

        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 3)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_SH_ORGS_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_ORGS_OUTPUT_WARNING)

    def test_load_organizations_overwrite(self):
        """Test to load organizations from a file with overwrite parameter set"""

        code = self.cmd.run('--orgs', '--overwrite',
                            'data/sortinghat_orgs_valid.json')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_ORGS_OVERWRITE_OUTPUT)

    def test_invalid_format(self):
        """Check whether it prints an error when parsing invalid files"""

        code = self.cmd.run('data/sortinghat_invalid.json')
        self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, LOAD_IDENTITIES_INVALID_JSON_FORMAT_ERROR)

        code = self.cmd.run('data/sortinghat_ids_missing_keys.json')
        self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[1]
        self.assertEqual(output, LOAD_IDENTITIES_MISSING_KEYS_ERROR)

        # Context added to catch deprecation warnings raised on Python 3
        with warnings.catch_warnings(record=True):
            code = self.cmd.run('data/sortinghat_orgs_invalid_json.json')
            self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
            output = sys.stderr.getvalue().strip().split('\n')[2]
            self.assertRegexpMatches(output, LOAD_ORGS_INVALID_FORMAT_ERROR)

        code = self.cmd.run('data/sortinghat_orgs_missing_keys.json')
        self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[3]
        self.assertEqual(output, LOAD_ORGS_MISSING_KEYS_ERROR)

        code = self.cmd.run('data/sortinghat_orgs_invalid_top.json')
        self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[4]
        self.assertEqual(output, LOAD_ORGS_IS_TOP_ERROR)

        code = self.cmd.run('data/sortinghat_blacklist_empty_strings.json')
        self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[5]
        self.assertEqual(output, LOAD_BLACKLIST_EMPTY_STRINGS_ERROR)


class TestLoadBlacklist(TestLoadCaseBase):
    """Test import_blacklist method with some Sorting Hat inputs"""

    def test_valid_file(self):
        """Check insertion of valid data from a file"""

        parser = self.get_parser('data/sortinghat_valid.json')

        self.cmd.import_blacklist(parser)

        # Check the contents of the registry
        bl = api.blacklist(self.db)
        self.assertEqual(len(bl), 2)

        # John Smith
        b = bl[0]
        self.assertEqual(b.excluded, 'John Smith')

        b = bl[1]
        self.assertEqual(b.excluded, 'jroe@example.com')


class TestLoadIdentities(TestLoadCaseBase):
    """Test import_identities method with some Sorting Hat inputs"""

    def test_valid_identities_file(self):
        """Check insertion of valid data from a file"""

        parser = self.get_parser('data/sortinghat_valid.json')

        code = self.cmd.import_identities(parser)
        self.assertEqual(code, CMD_SUCCESS)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        # John Smith
        uid = uids[0]
        self.assertEqual(uid.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 2)

        prf = uid.profile
        self.assertEqual(prf.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(prf.name, None)
        self.assertEqual(prf.email, 'jsmith@example.com')
        self.assertEqual(prf.is_bot, True)
        self.assertEqual(prf.country_code, None)
        self.assertEqual(prf.country, None)

        id0 = ids[0]
        self.assertEqual(id0.id, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, 'jsmith')
        self.assertEqual(id0.source, 'scm')

        id1 = ids[1]
        self.assertEqual(id1.id, '75d95d6c8492fd36d24a18bd45d62161e05fbc97')
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'scm')

        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Example')
        self.assertEqual(rol0.start, datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(rol0.end, datetime.datetime(2100, 1, 1, 0, 0))

        # Jane Roe
        uid = uids[1]
        self.assertEqual(uid.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')

        prf = uid.profile
        self.assertEqual(prf.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(prf.name, 'Jane Roe')
        self.assertEqual(prf.email, 'jroe@example.com')
        self.assertEqual(prf.is_bot, False)
        self.assertEqual(prf.country_code, 'US')
        self.assertEqual(prf.country.alpha3, 'USA')
        self.assertEqual(prf.country.code, 'US')
        self.assertEqual(prf.country.name, 'United States of America')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertEqual(id0.id, '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(id0.name, 'Jane Roe')
        self.assertEqual(id0.email, 'jroe@example.com')
        self.assertEqual(id0.username, 'jroe')
        self.assertEqual(id0.source, 'scm')

        id1 = ids[1]
        self.assertEqual(id1.id, 'cbfb7bd31d556322c640f5bc7b31d58a12b15904')
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jroe@bitergia.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'unknown')

        id2 = ids[2]
        self.assertEqual(id2.id, 'fef873c50a48cfc057f7aa19f423f81889a8907f')
        self.assertEqual(id2.name, None)
        self.assertEqual(id2.email, 'jroe@example.com')
        self.assertEqual(id2.username, None)
        self.assertEqual(id2.source, 'scm')

        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 3)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Bitergia')
        self.assertEqual(rol0.start, datetime.datetime(1999, 1, 1, 0, 0))
        self.assertEqual(rol0.end, datetime.datetime(2000, 1, 1, 0, 0))

        rol1 = enrollments[1]
        self.assertEqual(rol1.organization.name, 'Bitergia')
        self.assertEqual(rol1.start, datetime.datetime(2006, 1, 1, 0, 0))
        self.assertEqual(rol1.end, datetime.datetime(2008, 1, 1, 0, 0))

        rol2 = enrollments[2]
        self.assertEqual(rol2.organization.name, 'Example')
        self.assertEqual(rol2.start, datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, 0, 0))

    def test_valid_identities_with_default_matching(self):
        """Check insertion, matching and merging of valid data"""

        # First, insert the identity that will match with one
        # from the file
        api.add_organization(self.db, 'Example')
        uuid = api.add_identity(self.db, 'unknown', email='jsmith@example.com')
        api.add_enrollment(self.db, uuid, 'Example',
                           datetime.datetime(2000, 1, 1, 0, 0),
                           datetime.datetime(2100, 1, 1, 0, 0))
        api.edit_profile(self.db, uuid, name='John Smith', is_bot=False,
                         country_code='US')

        parser = self.get_parser('data/sortinghat_valid.json')

        code = self.cmd.import_identities(parser, matching='default')
        self.assertEqual(code, CMD_SUCCESS)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        # John Smith
        uid = uids[0]
        self.assertEqual(uid.uuid, '23fe3a011190a27a7c5cf6f8925de38ff0994d8d')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 3)

        # The profile was merged
        prf = uid.profile
        self.assertEqual(prf.uuid, '23fe3a011190a27a7c5cf6f8925de38ff0994d8d')
        self.assertEqual(prf.name, 'John Smith')
        self.assertEqual(prf.email, 'jsmith@example.com')
        self.assertEqual(prf.is_bot, True)
        self.assertEqual(prf.country_code, 'US')
        self.assertEqual(prf.country.code, 'US')
        self.assertEqual(prf.country.name, 'United States of America')

        id0 = ids[0]
        self.assertEqual(id0.id, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, 'jsmith')
        self.assertEqual(id0.source, 'scm')

        id1 = ids[1]
        self.assertEqual(id1.id, '23fe3a011190a27a7c5cf6f8925de38ff0994d8d')
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'unknown')

        id2 = ids[2]
        self.assertEqual(id2.id, '75d95d6c8492fd36d24a18bd45d62161e05fbc97')
        self.assertEqual(id2.name, 'John Smith')
        self.assertEqual(id2.email, 'jsmith@example.com')
        self.assertEqual(id2.username, None)
        self.assertEqual(id2.source, 'scm')

        # Enrollments were merged
        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Example')
        self.assertEqual(rol0.start, datetime.datetime(2000, 1, 1, 0, 0))
        self.assertEqual(rol0.end, datetime.datetime(2100, 1, 1, 0, 0))

        # Jane Roe
        uid = uids[1]
        self.assertEqual(uid.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')

        prf = uid.profile
        self.assertEqual(prf.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(prf.name, 'Jane Roe')
        self.assertEqual(prf.email, 'jroe@example.com')
        self.assertEqual(prf.is_bot, False)
        self.assertEqual(prf.country_code, 'US')
        self.assertEqual(prf.country.alpha3, 'USA')
        self.assertEqual(prf.country.code, 'US')
        self.assertEqual(prf.country.name, 'United States of America')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertEqual(id0.id, '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(id0.name, 'Jane Roe')
        self.assertEqual(id0.email, 'jroe@example.com')
        self.assertEqual(id0.username, 'jroe')
        self.assertEqual(id0.source, 'scm')

        id1 = ids[1]
        self.assertEqual(id1.id, 'cbfb7bd31d556322c640f5bc7b31d58a12b15904')
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jroe@bitergia.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'unknown')

        id2 = ids[2]
        self.assertEqual(id2.id, 'fef873c50a48cfc057f7aa19f423f81889a8907f')
        self.assertEqual(id2.name, None)
        self.assertEqual(id2.email, 'jroe@example.com')
        self.assertEqual(id2.username, None)
        self.assertEqual(id2.source, 'scm')

        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 3)

    def test_match_new_identities(self):
        """Check whether it matches only new identities"""

        parser = self.get_parser('data/sortinghat_valid.json')

        code = self.cmd.import_identities(parser, matching='default')
        self.assertEqual(code, CMD_SUCCESS)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        # We add a new identity that matches with some of the
        # already inserted
        jsmith_uuid = api.add_identity(self.db, 'unknown', email='jsmith@example.com')

        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 3)

        # This file has a new identity, only Jane Roe will match.
        parser = self.get_parser('data/sortinghat_valid_updated.json')

        code = self.cmd.import_identities(parser, matching='default',
                                          match_new=True)
        self.assertEqual(code, CMD_SUCCESS)

        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 3)

        # Jane Roe
        uid = uids[2]
        self.assertEqual(uid.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 4)

        self.assertEqual(ids[0].id, '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(ids[1].id, '684bb801b0ab02a8c0b6867711a994c695cbed4a')
        self.assertEqual(ids[2].id, 'cbfb7bd31d556322c640f5bc7b31d58a12b15904')
        self.assertEqual(ids[3].id, 'fef873c50a48cfc057f7aa19f423f81889a8907f')

        # Now, if we reload again the file but setting 'match_new' to false,
        # the identity that we inserted before will match "John Smith"
        parser = self.get_parser('data/sortinghat_valid_updated.json')

        code = self.cmd.import_identities(parser, matching='default')
        self.assertEqual(code, CMD_SUCCESS)

        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        # John Smith
        uid = uids[0]
        self.assertEqual(uid.uuid, '23fe3a011190a27a7c5cf6f8925de38ff0994d8d')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 3)

        self.assertEqual(ids[0].id, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(ids[1].id, '23fe3a011190a27a7c5cf6f8925de38ff0994d8d')
        self.assertEqual(ids[1].id, jsmith_uuid)
        self.assertEqual(ids[2].id, '75d95d6c8492fd36d24a18bd45d62161e05fbc97')

    def test_valid_identities_already_exist(self):
        """Check method when an identity already exists but with distinct UUID"""

        # The identity already exists but with a different UUID
        uuid = api.add_identity(self.db, 'unknown', email='jsmith@example.com')
        api.add_identity(self.db, source='scm', email='jsmith@example.com',
                         name='John Smith', username='jsmith', uuid=uuid)
        api.edit_profile(self.db, uuid, name='John Smith', is_bot=False,
                         country_code='US')

        parser = self.get_parser('data/sortinghat_valid.json')

        code = self.cmd.import_identities(parser)
        self.assertEqual(code, CMD_SUCCESS)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        # John Smith
        uid = uids[0]
        self.assertEqual(uid.uuid, '23fe3a011190a27a7c5cf6f8925de38ff0994d8d')

        # The profile was not updated because it was already available
        prf = uid.profile
        self.assertEqual(prf.uuid, '23fe3a011190a27a7c5cf6f8925de38ff0994d8d')
        self.assertEqual(prf.name, 'John Smith')
        self.assertEqual(prf.email, None)
        self.assertEqual(prf.is_bot, False)
        self.assertEqual(prf.country_code, 'US')
        self.assertEqual(prf.country.code, 'US')
        self.assertEqual(prf.country.name, 'United States of America')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertEqual(id0.id, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, 'jsmith')
        self.assertEqual(id0.source, 'scm')

        id1 = ids[1]
        self.assertEqual(id1.id, '23fe3a011190a27a7c5cf6f8925de38ff0994d8d')
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'unknown')

        id2 = ids[2]
        self.assertEqual(id2.id, '75d95d6c8492fd36d24a18bd45d62161e05fbc97')
        self.assertEqual(id2.name, 'John Smith')
        self.assertEqual(id2.email, 'jsmith@example.com')
        self.assertEqual(id2.username, None)
        self.assertEqual(id2.source, 'scm')

    def test_create_profile_from_identities(self):
        """Check whether a profile is created using the data identities"""

        parser = self.get_parser('data/sortinghat_identities_profiles.json')

        code = self.cmd.import_identities(parser)
        self.assertEqual(code, CMD_SUCCESS)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 3)

        # John Smith
        uid = uids[0]
        self.assertEqual(uid.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')

        prf = uid.profile
        self.assertEqual(prf.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(prf.name, 'John Smith')
        self.assertEqual(prf.email, 'jsmith@example.com')
        self.assertEqual(prf.is_bot, False)
        self.assertEqual(prf.country_code, None)
        self.assertEqual(prf.country, None)

        # John Doe
        uid = uids[1]
        self.assertEqual(uid.uuid, '3c3c71c67952135eb92a9cace538ffbe6cb39d88')

        prf = uid.profile
        self.assertEqual(prf.uuid, '3c3c71c67952135eb92a9cace538ffbe6cb39d88')
        self.assertEqual(prf.name, 'jdoe')
        self.assertEqual(prf.email, 'jdoe@example.com')
        self.assertEqual(prf.is_bot, False)
        self.assertEqual(prf.country_code, None)
        self.assertEqual(prf.country, None)

        # Jane Rae
        uid = uids[2]
        self.assertEqual(uid.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')

        prf = uid.profile
        self.assertEqual(prf.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(prf.name, 'Jane Roe')
        self.assertEqual(prf.email, 'jroe@example.com')
        self.assertEqual(prf.is_bot, False)
        self.assertEqual(prf.country_code, None)
        self.assertEqual(prf.country, None)

    def test_dates_out_of_bounds(self):
        """Check dates when they are out of bounds"""

        parser = self.get_parser('data/sortinghat_ids_dates_out_of_bounds.json')

        # This command returns a success value even when some data is wrong
        code = self.cmd.import_identities(parser)
        self.assertEqual(code, CMD_SUCCESS)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 1)

        # Jane Roe
        uid = uids[0]
        self.assertEqual(uid.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')

        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 2)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Bitergia')
        self.assertEqual(rol0.start, datetime.datetime(1999, 1, 1, 0, 0))
        # The json file has 2200-01-01T00:00:00
        self.assertEqual(rol0.end, datetime.datetime(2100, 1, 1, 0, 0))

        rol1 = enrollments[1]
        self.assertEqual(rol1.organization.name, 'Example')
        # The json file has 1800-01-01T00:00:00
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1, 0, 0))

    def test_invalid_matching_method(self):
        """Check if it fails when an invalid matching method is given"""

        parser = self.get_parser('data/sortinghat_valid.json')

        code = self.cmd.import_identities(parser, matching='mock')
        self.assertEqual(code, CODE_MATCHER_NOT_SUPPORTED_ERROR)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_MATCHING_ERROR)


class TestLoadSortingHatImportOrganizations(TestLoadCaseBase):
    """Test import_organizations method with some Sorting Hat inputs"""

    def test_valid_organizations_file(self):
        """Check insertion of valid data from a file"""

        parser = self.get_parser('data/sortinghat_orgs_valid.json')

        self.cmd.import_organizations(parser)

        # Check the contents of the registry
        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 3)

        # Bitergia
        org = orgs[0]
        self.assertEqual(org.name, 'Bitergia')

        doms = org.domains
        self.assertEqual(len(doms), 5)

        dom = doms[0]
        self.assertEqual(dom.domain, 'api.bitergia.com')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[1]
        self.assertEqual(dom.domain, 'bitergia.com')
        self.assertEqual(dom.is_top_domain, True)

        dom = doms[2]
        self.assertEqual(dom.domain, 'bitergia.net')
        self.assertEqual(dom.is_top_domain, True)

        dom = doms[3]
        self.assertEqual(dom.domain, 'test.bitergia.com')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[4]
        self.assertEqual(dom.domain, 'example.net')
        self.assertEqual(dom.is_top_domain, False)

        # Example
        org = orgs[1]
        self.assertEqual(org.name, 'Example')

        doms = org.domains
        self.assertEqual(len(doms), 1)

        dom = doms[0]
        self.assertEqual(dom.domain, 'example.com')
        self.assertEqual(dom.is_top_domain, True)

        # Unknown
        org = orgs[2]
        self.assertEqual(org.name, 'Unknown')

        doms = org.domains
        self.assertEqual(len(doms), 0)

    def test_import_to_non_empty_registry(self):
        """Test load (and overwrite) process in a registry with some contents"""

        # First, load some data
        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com')

        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.net')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')

        # Import new data, overwriting existing relationships
        parser = self.get_parser('data/sortinghat_orgs_valid_alt.json')

        self.cmd.import_organizations(parser, True)

        # Check the contents of the registry
        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 4)

        # Bitergia
        org = orgs[0]
        self.assertEqual(org.name, 'Bitergia')

        doms = org.domains
        self.assertEqual(len(doms), 4)

        dom = doms[0]
        self.assertEqual(dom.domain, 'bitergia.net')
        self.assertEqual(dom.is_top_domain, True)

        dom = doms[1]
        self.assertEqual(dom.domain, 'bitergia.com')
        self.assertEqual(dom.is_top_domain, True)

        dom = doms[2]
        self.assertEqual(dom.domain, 'api.bitergia.com')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[3]
        self.assertEqual(dom.domain, 'test.bitergia.com')
        self.assertEqual(dom.is_top_domain, False)

        # Example
        org = orgs[1]
        self.assertEqual(org.name, 'Example')

        doms = org.domains
        self.assertEqual(len(doms), 1)

        dom = doms[0]
        self.assertEqual(dom.domain, 'example.net')
        self.assertEqual(dom.is_top_domain, True)

        # GSyC/LibreSoft
        org = orgs[2]
        self.assertEqual(org.name, 'GSyC/LibreSoft')

        doms = org.domains
        self.assertEqual(len(doms), 2)

        dom = doms[0]
        self.assertEqual(dom.domain, 'example.com')
        self.assertEqual(dom.is_top_domain, True)

        dom = doms[1]
        self.assertEqual(dom.domain, 'libresoft.es')
        self.assertEqual(dom.is_top_domain, True)

        # Unknown
        org = orgs[3]
        self.assertEqual(org.name, 'Unknown')

        doms = org.domains
        self.assertEqual(len(doms), 0)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
