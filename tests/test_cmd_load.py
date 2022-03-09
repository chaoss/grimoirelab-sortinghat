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

import datetime
import sys
import unittest
import warnings

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.load import Load
from sortinghat.db.model import Country
from sortinghat.parsing.sh import SortingHatParser
from sortinghat.exceptions import CODE_MATCHER_NOT_SUPPORTED_ERROR, CODE_INVALID_FORMAT_ERROR

from tests.base import TestCommandCaseBase, datadir

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

=====
+ Processing 0000000000000000000000000000000000000000
-- 0000000000000000000000000000000000000000 not found. Generating a new UUID.
=====

=====
+ Processing 03e12d00e37fd45593c49a5a5a1652deca4cf302
-- 03e12d00e37fd45593c49a5a5a1652deca4cf302 not found. Generating a new UUID.
-- using a9b403e150dd4af8953a52a4bb841051e4b705d9 for 03e12d00e37fd45593c49a5a5a1652deca4cf302 unique identity.
-- loading identities
-- identities loaded
-- profile a9b403e150dd4af8953a52a4bb841051e4b705d9 updated
-- loading enrollments
-- enrollments loaded
+ a9b403e150dd4af8953a52a4bb841051e4b705d9 (old 03e12d00e37fd45593c49a5a5a1652deca4cf302) loaded
=====

=====
+ Processing 52e0aa0a14826627e633fd15332988686b730ab3
-- 52e0aa0a14826627e633fd15332988686b730ab3 not found. Generating a new UUID.
-- using 17ab00ed3825ec2f50483e33c88df223264182ba for 52e0aa0a14826627e633fd15332988686b730ab3 unique identity.
-- loading identities
-- identities loaded
-- profile 17ab00ed3825ec2f50483e33c88df223264182ba updated
-- loading enrollments
-- enrollments loaded
+ 17ab00ed3825ec2f50483e33c88df223264182ba (old 52e0aa0a14826627e633fd15332988686b730ab3) loaded
=====
2/3 unique identities loaded"""

# Identities outputs

LOAD_IDENTITIES_OUTPUT = """Loading blacklist...
Entry  added to the blacklist
Entry  added to the blacklist
2/2 blacklist entries loaded
Loading unique identities...

=====
+ Processing 0000000000000000000000000000000000000000
-- 0000000000000000000000000000000000000000 not found. Generating a new UUID.
=====

=====
+ Processing 03e12d00e37fd45593c49a5a5a1652deca4cf302
-- 03e12d00e37fd45593c49a5a5a1652deca4cf302 not found. Generating a new UUID.
-- using a9b403e150dd4af8953a52a4bb841051e4b705d9 for 03e12d00e37fd45593c49a5a5a1652deca4cf302 unique identity.
-- loading identities
-- identities loaded
-- profile a9b403e150dd4af8953a52a4bb841051e4b705d9 updated
-- loading enrollments
-- enrollments loaded
+ a9b403e150dd4af8953a52a4bb841051e4b705d9 (old 03e12d00e37fd45593c49a5a5a1652deca4cf302) loaded
=====

=====
+ Processing 52e0aa0a14826627e633fd15332988686b730ab3
-- 52e0aa0a14826627e633fd15332988686b730ab3 not found. Generating a new UUID.
-- using 17ab00ed3825ec2f50483e33c88df223264182ba for 52e0aa0a14826627e633fd15332988686b730ab3 unique identity.
-- loading identities
-- identities loaded
-- profile 17ab00ed3825ec2f50483e33c88df223264182ba updated
-- loading enrollments
-- enrollments loaded
+ 17ab00ed3825ec2f50483e33c88df223264182ba (old 52e0aa0a14826627e633fd15332988686b730ab3) loaded
=====
2/3 unique identities loaded"""

LOAD_IDENTITIES_OUTPUT_ERROR = """Error: not enough info to load 0000000000000000000000000000000000000000 unique identity. Skipping.
Warning: Organization 'Bitergia' already exists in the registry. Organization not updated.
Warning: Organization 'Example' already exists in the registry. Organization not updated."""

LOAD_IDENTITIES_NO_STRICT_OUTPUT = """Loading blacklist...
0/0 blacklist entries loaded
Loading unique identities...

=====
+ Processing e8284285566fdc1f41c8a22bb84a295fc3c4cbb3
-- e8284285566fdc1f41c8a22bb84a295fc3c4cbb3 not found. Generating a new UUID.
-- using e8284285566fdc1f41c8a22bb84a295fc3c4cbb3 for e8284285566fdc1f41c8a22bb84a295fc3c4cbb3 unique identity.
-- loading identities
-- identities loaded
-- profile e8284285566fdc1f41c8a22bb84a295fc3c4cbb3 updated
-- loading enrollments
-- enrollments loaded

New match found

+ e8284285566fdc1f41c8a22bb84a295fc3c4cbb3
  * -	jsmith@example	-	scm

+ 8253035bc847e70ddd13f7a721faf6f3dd159d7a
  * -	jsmith@example	-	unknown
Unique identity e8284285566fdc1f41c8a22bb84a295fc3c4cbb3 merged on 8253035bc847e70ddd13f7a721faf6f3dd159d7a
+ 8253035bc847e70ddd13f7a721faf6f3dd159d7a (old e8284285566fdc1f41c8a22bb84a295fc3c4cbb3) loaded
=====
1/1 unique identities loaded"""

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

LOAD_ORGS_OUTPUT_WARNING = """Warning: Domain 'example.net' already exists in the registry. Not updated."""


class TestLoadCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on loadunit tests"""

    cmd_klass = Load

    def get_parser(self, filename):
        with open(filename, 'r', encoding='UTF-8') as f:
            content = f.read()

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

        code = self.cmd.run(datadir('sortinghat_valid.json'), '--verbose')
        self.assertEqual(code, CMD_SUCCESS)

        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 3)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_OUTPUT)

    def test_load_identities(self):
        """Test to load identities from a file"""

        code = self.cmd.run('--identities', datadir('sortinghat_valid.json'),
                            '--verbose')
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
                            datadir('sortinghat_valid.json'),
                            '--verbose')
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_OUTPUT_ERROR)

    def test_load_identities_no_strict_matching(self):
        """Test to load identities with no strict matching"""

        # First, insert the identity that will match with one
        # from the file
        api.add_identity(self.db, 'unknown', email='jsmith@example')

        code = self.cmd.run('--identities', '--matching', 'default',
                            '--no-strict-matching',
                            datadir('sortinghat_no_strict_valid.json'),
                            '--verbose')
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_NO_STRICT_OUTPUT)

    def test_load_identities_invalid_file(self):
        """Test whether it prints error messages while reading invalid files"""

        code = self.cmd.run('--identities', datadir('sortinghat_invalid.json'))
        self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
        output = sys.stderr.getvalue().strip().split('\n')[0]
        self.assertEqual(output, LOAD_IDENTITIES_INVALID_JSON_FORMAT_ERROR)

    def test_load_organizations(self):
        """Test to load organizations from a file"""

        code = self.cmd.run('--orgs', datadir('sortinghat_orgs_valid.json'))
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
                            datadir('sortinghat_orgs_valid.json'))
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, LOAD_ORGS_OVERWRITE_OUTPUT)

    def test_invalid_format(self):
        """Check whether it prints an error when parsing invalid files"""

        code = self.cmd.run(datadir('sortinghat_invalid.json'))
        self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
        output = sys.stderr.getvalue().strip('\n').split('\n')[0]
        self.assertEqual(output, LOAD_IDENTITIES_INVALID_JSON_FORMAT_ERROR)

        code = self.cmd.run(datadir('sortinghat_ids_missing_keys.json'))
        self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
        output = sys.stderr.getvalue().strip('\n').split('\n')[-1]
        self.assertEqual(output, LOAD_IDENTITIES_MISSING_KEYS_ERROR)

        # Context added to catch deprecation warnings raised on Python 3
        with warnings.catch_warnings(record=True):
            code = self.cmd.run(datadir('sortinghat_orgs_invalid_json.json'))
            self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
            output = sys.stderr.getvalue().strip('\n').split('\n')[-1]
            self.assertRegexpMatches(output, LOAD_ORGS_INVALID_FORMAT_ERROR)

        code = self.cmd.run(datadir('sortinghat_orgs_missing_keys.json'))
        self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
        output = sys.stderr.getvalue().strip('\n').split('\n')[-1]
        self.assertEqual(output, LOAD_ORGS_MISSING_KEYS_ERROR)

        code = self.cmd.run(datadir('sortinghat_orgs_invalid_top.json'))
        self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
        output = sys.stderr.getvalue().strip('\n').split('\n')[-1]
        self.assertEqual(output, LOAD_ORGS_IS_TOP_ERROR)

        code = self.cmd.run(datadir('sortinghat_blacklist_empty_strings.json'))
        self.assertEqual(code, CODE_INVALID_FORMAT_ERROR)
        output = sys.stderr.getvalue().strip('\n').split('\n')[-1]
        self.assertEqual(output, LOAD_BLACKLIST_EMPTY_STRINGS_ERROR)


class TestLoadBlacklist(TestLoadCaseBase):
    """Test import_blacklist method with some Sorting Hat inputs"""

    def test_valid_file(self):
        """Check insertion of valid data from a file"""

        parser = self.get_parser(datadir('sortinghat_valid.json'))

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

        parser = self.get_parser(datadir('sortinghat_valid.json'))

        code = self.cmd.import_identities(parser)
        self.assertEqual(code, CMD_SUCCESS)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        # Jane Roe
        uid = uids[0]
        self.assertEqual(uid.uuid, '17ab00ed3825ec2f50483e33c88df223264182ba')

        prf = uid.profile
        self.assertEqual(prf.uuid, '17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(prf.name, 'Jane Roe')
        self.assertEqual(prf.email, 'jroe@example.com')
        self.assertEqual(prf.gender, None)
        self.assertEqual(prf.gender_acc, None)
        self.assertEqual(prf.is_bot, False)
        self.assertEqual(prf.country_code, 'US')
        self.assertEqual(prf.country.alpha3, 'USA')
        self.assertEqual(prf.country.code, 'US')
        self.assertEqual(prf.country.name, 'United States of America')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertEqual(id0.id, '17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(id0.name, 'Jane Roe')
        self.assertEqual(id0.email, 'jroe@example.com')
        self.assertEqual(id0.username, 'jroe')
        self.assertEqual(id0.source, 'scm')

        id1 = ids[1]
        self.assertEqual(id1.id, '22d1b20763c6f5822bdda8508957486c547bb9de')
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jroe@bitergia.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'unknown')

        id2 = ids[2]
        self.assertEqual(id2.id, '322397ed782a798ffd9d0bc7e293df4292fe075d')
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

        # John Smith
        uid = uids[1]
        self.assertEqual(uid.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 2)

        prf = uid.profile
        self.assertEqual(prf.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(prf.name, None)
        self.assertEqual(prf.email, 'jsmith@example.com')
        self.assertEqual(prf.gender, 'male')
        self.assertEqual(prf.gender_acc, 100)
        self.assertEqual(prf.is_bot, True)
        self.assertEqual(prf.country_code, None)
        self.assertEqual(prf.country, None)

        id0 = ids[0]
        self.assertEqual(id0.id, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'scm')

        id1 = ids[1]
        self.assertEqual(id1.id, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, 'jsmith')
        self.assertEqual(id1.source, 'scm')

        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Example')
        self.assertEqual(rol0.start, datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(rol0.end, datetime.datetime(2100, 1, 1, 0, 0))

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

        parser = self.get_parser(datadir('sortinghat_valid.json'))

        code = self.cmd.import_identities(parser, matching='default')
        self.assertEqual(code, CMD_SUCCESS)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        # Jane Roe
        uid = uids[0]
        self.assertEqual(uid.uuid, '17ab00ed3825ec2f50483e33c88df223264182ba')

        prf = uid.profile
        self.assertEqual(prf.uuid, '17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(prf.name, 'Jane Roe')
        self.assertEqual(prf.email, 'jroe@example.com')
        self.assertEqual(prf.gender, None)
        self.assertEqual(prf.gender_acc, None)
        self.assertEqual(prf.is_bot, False)
        self.assertEqual(prf.country_code, 'US')
        self.assertEqual(prf.country.alpha3, 'USA')
        self.assertEqual(prf.country.code, 'US')
        self.assertEqual(prf.country.name, 'United States of America')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertEqual(id0.id, '17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(id0.name, 'Jane Roe')
        self.assertEqual(id0.email, 'jroe@example.com')
        self.assertEqual(id0.username, 'jroe')
        self.assertEqual(id0.source, 'scm')

        id1 = ids[1]
        self.assertEqual(id1.id, '22d1b20763c6f5822bdda8508957486c547bb9de')
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jroe@bitergia.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'unknown')

        id2 = ids[2]
        self.assertEqual(id2.id, '322397ed782a798ffd9d0bc7e293df4292fe075d')
        self.assertEqual(id2.name, None)
        self.assertEqual(id2.email, 'jroe@example.com')
        self.assertEqual(id2.username, None)
        self.assertEqual(id2.source, 'scm')

        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 3)

        # John Smith
        uid = uids[1]
        self.assertEqual(uid.uuid, '2371a34a0ac65fbd9d631464ee41d583ec0e1e88')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 3)

        # The profile was merged
        prf = uid.profile
        self.assertEqual(prf.uuid, '2371a34a0ac65fbd9d631464ee41d583ec0e1e88')
        self.assertEqual(prf.name, 'John Smith')
        self.assertEqual(prf.email, 'jsmith@example.com')
        self.assertEqual(prf.gender, 'male')
        self.assertEqual(prf.gender_acc, 100)
        self.assertEqual(prf.is_bot, True)
        self.assertEqual(prf.country_code, 'US')
        self.assertEqual(prf.country.code, 'US')
        self.assertEqual(prf.country.name, 'United States of America')

        id0 = ids[0]
        self.assertEqual(id0.id, '2371a34a0ac65fbd9d631464ee41d583ec0e1e88')
        self.assertEqual(id0.name, None)
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'unknown')

        id1 = ids[1]
        self.assertEqual(id1.id, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'scm')

        id2 = ids[2]
        self.assertEqual(id2.id, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(id2.name, 'John Smith')
        self.assertEqual(id2.email, 'jsmith@example.com')
        self.assertEqual(id2.username, 'jsmith')
        self.assertEqual(id2.source, 'scm')

        # Enrollments were merged
        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertEqual(rol0.organization.name, 'Example')
        self.assertEqual(rol0.start, datetime.datetime(2000, 1, 1, 0, 0))
        self.assertEqual(rol0.end, datetime.datetime(2100, 1, 1, 0, 0))

    def test_match_new_identities(self):
        """Check whether it matches only new identities"""

        parser = self.get_parser(datadir('sortinghat_valid.json'))

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
        parser = self.get_parser(datadir('sortinghat_valid_updated.json'))

        code = self.cmd.import_identities(parser, matching='default',
                                          match_new=True)
        self.assertEqual(code, CMD_SUCCESS)

        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 3)

        # Jane Roe
        uid = uids[0]
        self.assertEqual(uid.uuid, '17ab00ed3825ec2f50483e33c88df223264182ba')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 4)

        self.assertEqual(ids[0].id, '17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(ids[1].id, '22d1b20763c6f5822bdda8508957486c547bb9de')
        self.assertEqual(ids[2].id, '322397ed782a798ffd9d0bc7e293df4292fe075d')
        self.assertEqual(ids[3].id, '8ff87accaf518070bdb494b87f4d5a10e7605b47')

        # Now, if we reload again the file but setting 'match_new' to false,
        # the identity that we inserted before will match "John Smith"
        parser = self.get_parser(datadir('sortinghat_valid_updated.json'))

        code = self.cmd.import_identities(parser, matching='default')
        self.assertEqual(code, CMD_SUCCESS)

        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        # John Smith
        uid = uids[1]
        self.assertEqual(uid.uuid, '2371a34a0ac65fbd9d631464ee41d583ec0e1e88')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 3)

        self.assertEqual(ids[0].id, '2371a34a0ac65fbd9d631464ee41d583ec0e1e88')
        self.assertEqual(ids[0].id, jsmith_uuid)
        self.assertEqual(ids[1].id, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(ids[2].id, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

    def test_matching_no_strict(self):
        """Check if identities with no strict matching are merged"""

        # First, insert the identity that will match with one
        # from the file
        api.add_identity(self.db, 'unknown', email='jsmith@example')

        parser = self.get_parser(datadir('sortinghat_no_strict_valid.json'))

        code = self.cmd.import_identities(parser, matching='default',
                                          no_strict_matching=True)
        self.assertEqual(code, CMD_SUCCESS)

        # Check whether identities were merged
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 1)
        self.assertEqual(len(uids[0].identities), 2)

    def test_valid_identities_already_exist(self):
        """Check method when an identity already exists but with distinct UUID"""

        # The identity already exists but with a different UUID
        uuid = api.add_identity(self.db, 'unknown', email='jsmith@example.com')
        api.add_identity(self.db, source='scm', email='jsmith@example.com',
                         name='John Smith', username='jsmith', uuid=uuid)
        api.edit_profile(self.db, uuid, name='John Smith', is_bot=False,
                         country_code='US')

        parser = self.get_parser(datadir('sortinghat_valid.json'))

        code = self.cmd.import_identities(parser)
        self.assertEqual(code, CMD_SUCCESS)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 2)

        # John Smith
        uid = uids[1]
        self.assertEqual(uid.uuid, '2371a34a0ac65fbd9d631464ee41d583ec0e1e88')

        # The profile is updated because a new one was given
        prf = uid.profile
        self.assertEqual(prf.uuid, '2371a34a0ac65fbd9d631464ee41d583ec0e1e88')
        self.assertEqual(prf.name, None)
        self.assertEqual(prf.email, 'jsmith@example.com')
        self.assertEqual(prf.gender, 'male')
        self.assertEqual(prf.gender_acc, 100)
        self.assertEqual(prf.is_bot, True)
        self.assertEqual(prf.country, None)

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertEqual(id0.id, '2371a34a0ac65fbd9d631464ee41d583ec0e1e88')
        self.assertEqual(id0.name, None)
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'unknown')

        id1 = ids[1]
        self.assertEqual(id1.id, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'scm')

        id2 = ids[2]
        self.assertEqual(id2.id, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(id2.name, 'John Smith')
        self.assertEqual(id2.email, 'jsmith@example.com')
        self.assertEqual(id2.username, 'jsmith')
        self.assertEqual(id2.source, 'scm')

    def test_create_profile_from_identities(self):
        """Check whether a profile is created using the data identities"""

        parser = self.get_parser(datadir('sortinghat_identities_profiles.json'))

        code = self.cmd.import_identities(parser)
        self.assertEqual(code, CMD_SUCCESS)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 3)

        # Jane Rae
        uid = uids[0]
        self.assertEqual(uid.uuid, '17ab00ed3825ec2f50483e33c88df223264182ba')

        prf = uid.profile
        self.assertEqual(prf.uuid, '17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(prf.name, 'Jane Roe')
        self.assertEqual(prf.email, 'jroe@example.com')
        self.assertEqual(prf.gender, None)
        self.assertEqual(prf.gender_acc, None)
        self.assertEqual(prf.is_bot, False)
        self.assertEqual(prf.country_code, None)
        self.assertEqual(prf.country, None)

        # John Smith
        uid = uids[1]
        self.assertEqual(uid.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        prf = uid.profile
        self.assertEqual(prf.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(prf.name, 'John Smith')
        self.assertEqual(prf.email, 'jsmith@example.com')
        self.assertEqual(prf.gender, None)
        self.assertEqual(prf.gender_acc, None)
        self.assertEqual(prf.is_bot, False)
        self.assertEqual(prf.country_code, None)
        self.assertEqual(prf.country, None)

        # John Doe
        uid = uids[2]
        self.assertEqual(uid.uuid, 'c2f8c3d7b49cdbfb0af9fc9db2ca098ec6c06c2f')

        prf = uid.profile
        self.assertEqual(prf.uuid, 'c2f8c3d7b49cdbfb0af9fc9db2ca098ec6c06c2f')
        self.assertEqual(prf.name, 'jdoe')
        self.assertEqual(prf.email, 'jdoe@example.com')
        self.assertEqual(prf.gender, None)
        self.assertEqual(prf.gender_acc, None)
        self.assertEqual(prf.is_bot, False)
        self.assertEqual(prf.country_code, None)
        self.assertEqual(prf.country, None)

    def test_reset(self):
        """Check if stored relationships and enrollments are removed before loading"""

        # These identities will be split and enrollments removed
        uuid = api.add_identity(self.db, 'unknown', email='jsmith@example.com')
        api.add_identity(self.db, source='scm', email='jsmith@example.com',
                         name='John Smith', username='jsmith', uuid=uuid)

        api.add_organization(self.db, 'LibreSoft')
        api.add_enrollment(self.db, uuid, 'LibreSoft',
                           datetime.datetime(2000, 1, 1, 0, 0),
                           datetime.datetime(2100, 1, 1, 0, 0))

        parser = self.get_parser(datadir('sortinghat_valid.json'))

        code = self.cmd.import_identities(parser, reset=True)
        self.assertEqual(code, CMD_SUCCESS)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 3)

        # Jane Roe
        uid = uids[0]
        self.assertEqual(uid.uuid, '17ab00ed3825ec2f50483e33c88df223264182ba')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertEqual(id0.id, '17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(id0.name, 'Jane Roe')
        self.assertEqual(id0.email, 'jroe@example.com')
        self.assertEqual(id0.username, 'jroe')
        self.assertEqual(id0.source, 'scm')

        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 3)

        # jsmith@example.com
        uid = uids[1]
        self.assertEqual(uid.uuid, '2371a34a0ac65fbd9d631464ee41d583ec0e1e88')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 1)

        id0 = ids[0]
        self.assertEqual(id0.id, '2371a34a0ac65fbd9d631464ee41d583ec0e1e88')
        self.assertEqual(id0.name, None)
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'unknown')

        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 0)

        # John Smith
        uid = uids[2]
        self.assertEqual(uid.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        ids = self.sort_identities(uid.identities)
        self.assertEqual(len(ids), 2)

        id1 = ids[0]
        self.assertEqual(id1.id, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'scm')

        id2 = ids[1]
        self.assertEqual(id2.id, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(id2.name, 'John Smith')
        self.assertEqual(id2.email, 'jsmith@example.com')
        self.assertEqual(id2.username, 'jsmith')
        self.assertEqual(id2.source, 'scm')

        enrollments = api.enrollments(self.db, uid.uuid)
        self.assertEqual(len(enrollments), 1)

    def test_dates_out_of_bounds(self):
        """Check dates when they are out of bounds"""

        parser = self.get_parser(datadir('sortinghat_ids_dates_out_of_bounds.json'))

        # This command returns a success value even when some data is wrong
        code = self.cmd.import_identities(parser)
        self.assertEqual(code, CMD_SUCCESS)

        # Check the contents of the registry
        uids = api.unique_identities(self.db)
        self.assertEqual(len(uids), 1)

        # Jane Roe
        uid = uids[0]
        self.assertEqual(uid.uuid, '17ab00ed3825ec2f50483e33c88df223264182ba')

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

        parser = self.get_parser(datadir('sortinghat_valid.json'))

        code = self.cmd.import_identities(parser, matching='mock')
        self.assertEqual(code, CODE_MATCHER_NOT_SUPPORTED_ERROR)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, LOAD_IDENTITIES_MATCHING_ERROR)


class TestLoadSortingHatImportOrganizations(TestLoadCaseBase):
    """Test import_organizations method with some Sorting Hat inputs"""

    def test_valid_organizations_file(self):
        """Check insertion of valid data from a file"""

        parser = self.get_parser(datadir('sortinghat_orgs_valid.json'))

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
        self.assertEqual(dom.domain, 'example.net')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[4]
        self.assertEqual(dom.domain, 'test.bitergia.com')
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
        parser = self.get_parser(datadir('sortinghat_orgs_valid_alt.json'))

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
