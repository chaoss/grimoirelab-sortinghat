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
import json
import os
import sys
import tempfile
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.export import Export,\
    SortingHatIdentitiesExporter, SortingHatOrganizationsExporter
from sortinghat.db.model import Country

from tests.base import TestCommandCaseBase


class TestExportCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on export unit tests"""

    cmd_klass = Export

    def setUp(self):
        super(TestExportCaseBase, self).setUp()
        # Temporary file for outputs
        self.tmpfile = tempfile.mkstemp()[1]

    def tearDown(self):
        super(TestExportCaseBase, self).tearDown()
        os.remove(self.tmpfile)

    def read_json(self, filename):
        if sys.version_info[0] >= 3: # Python 3
            with open(filename, 'r', encoding='UTF-8') as f:
                content = f.read()
        else: # Python 2
            with open(filename, 'r') as f:
                content = f.read().decode('UTF-8')

        obj = json.loads(content)
        return obj

    def load_test_dataset(self):
        # Add country
        with self.db.connect() as session:
            # Add a country
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)

        # Add organizations
        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com', is_top_domain=True)
        api.add_domain(self.db, 'Example', 'example.net', is_top_domain=True)

        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.net', is_top_domain=True)
        api.add_domain(self.db, 'Bitergia', 'bitergia.com', is_top_domain=True)
        api.add_domain(self.db, 'Bitergia', 'api.bitergia.com', is_top_domain=False)
        api.add_domain(self.db, 'Bitergia', 'test.bitergia.com', is_top_domain=False)

        api.add_organization(self.db, 'Unknown')

        # Add John Smith identity
        jsmith_uuid = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                       'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com', 'John Smith',
                         uuid=jsmith_uuid)
        api.edit_profile(self.db, jsmith_uuid, email='jsmith@example.com', is_bot=True)

        # Add Joe Roe identity
        jroe_uuid = api.add_identity(self.db, 'scm', 'jroe@example.com',
                                     'Jane Roe', 'jroe')
        api.add_identity(self.db, 'scm', 'jroe@example.com',
                         uuid=jroe_uuid)
        api.add_identity(self.db, 'unknown', 'jroe@bitergia.com',
                         uuid=jroe_uuid)
        api.edit_profile(self.db, jroe_uuid, name='Jane Roe', email='jroe@example.com',
                         is_bot=False, country_code='US')

        # Add unique identity, this one won't have neither identities
        # nor enrollments
        api.add_unique_identity(self.db,
                                '0000000000000000000000000000000000000000')

        # Add enrollments
        api.add_enrollment(self.db, jsmith_uuid, 'Example')

        api.add_enrollment(self.db, jroe_uuid, 'Example')
        api.add_enrollment(self.db, jroe_uuid, 'Bitergia',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2000, 1, 1))
        api.add_enrollment(self.db, jroe_uuid, 'Bitergia',
                           datetime.datetime(2006, 1, 1),
                           datetime.datetime(2008, 1, 1))

        # Add blacklist
        api.add_to_matching_blacklist(self.db, 'jroe@example.com')
        api.add_to_matching_blacklist(self.db, 'John Smith')


class TestExportCommand(TestExportCaseBase):
    """Export command unit tests"""

    def test_export_identities(self):
        """Test to export identities to a file"""

        code = self.cmd.run('--identities', self.tmpfile)
        self.assertEqual(code, CMD_SUCCESS)

        # Read results and pre-generated file to tests whether
        # both are the same. To compare, we generate a dict object
        # removing 'time' key.
        a = self.read_json(self.tmpfile)
        b = self.read_json('data/sortinghat_identities_valid.json')

        a.pop('time')
        b.pop('time')

        self.assertEqual(a, b)

    def test_export_identities_source(self):
        """Check the export indentities to a file filtering by source"""

        code = self.cmd.run('--identities', '--source', 'unknown',
                           self.tmpfile)
        self.assertEqual(code, CMD_SUCCESS)

        a = self.read_json(self.tmpfile)
        b = self.read_json('data/sortinghat_identities_source.json')

        a.pop('time')
        b.pop('time')

        self.assertEqual(a, b)

    def test_export_organizations(self):
        """Test to export organizations to a file"""

        code = self.cmd.run('--orgs', self.tmpfile)
        self.assertEqual(code, CMD_SUCCESS)

        # Read results and pre-generated file to tests whether
        # both are the same. To compare, we generate a dict object
        # removing 'time' key.
        a = self.read_json(self.tmpfile)
        b = self.read_json('data/sortinghat_orgs.json')

        a.pop('time')
        b.pop('time')

        self.assertEqual(a, b)


class TestExportIdentities(TestExportCaseBase):
    """Test export_identities method with some inputs"""

    def test_export_identities(self):
        """Check the output of export_identities method"""

        with open(self.tmpfile, 'w') as f:
            code = self.cmd.export_identities(f)
            self.assertEqual(code, CMD_SUCCESS)

        # Read results and pre-generated file to tests whether
        # both are the same. To compare, we generate a dict object
        # removing 'time' key.
        a = self.read_json(self.tmpfile)
        b = self.read_json('data/sortinghat_identities_valid.json')

        a.pop('time')
        b.pop('time')

        self.assertEqual(a, b)

    def test_export_identities_source(self):
        """Check the output of export_identities method setting a source"""

        with open(self.tmpfile, 'w') as f:
            code = self.cmd.export_identities(f, source='unknown')
            self.assertEqual(code, CMD_SUCCESS)

        a = self.read_json(self.tmpfile)
        b = self.read_json('data/sortinghat_identities_source.json')

        a.pop('time')
        b.pop('time')

        self.assertEqual(a, b)

    def test_export_identities_empty_registry(self):
        """Check the output when registry is empty"""

        # Remove pre-loaded test dataset
        self.db.clear()

        with open(self.tmpfile, 'w') as f:
            code = self.cmd.export_identities(f)
            self.assertEqual(code, CMD_SUCCESS)

        a = self.read_json(self.tmpfile)

        self.assertEqual(a['source'], None)
        self.assertIn('time', a)
        self.assertEqual(len(a['uidentities']), 0)


class TestSortingHatIdentitiesExporter(TestExportCaseBase):
    """Test Sorting Hat exporter"""

    def test_export(self):
        """Test the output from export"""

        exporter = SortingHatIdentitiesExporter(self.db)
        dump = exporter.export()

        # The best way to check this is to build a JSON object
        # with the output from export()
        obj = json.loads(dump)

        self.assertEqual(obj['source'], None)
        self.assertIn('time', obj)

        uidentities = obj['uidentities']
        self.assertEqual(len(uidentities), 3)

        uid0 = uidentities['0000000000000000000000000000000000000000']
        self.assertEqual(uid0['uuid'], '0000000000000000000000000000000000000000')
        self.assertEqual(uid0['profile'], None)
        self.assertEqual(len(uid0['identities']), 0)

        # Jane Roe
        uid1 = uidentities['52e0aa0a14826627e633fd15332988686b730ab3']
        self.assertEqual(uid1['uuid'], '52e0aa0a14826627e633fd15332988686b730ab3')

        self.assertEqual(uid1['profile']['uuid'], '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(uid1['profile']['name'], 'Jane Roe')
        self.assertEqual(uid1['profile']['email'], 'jroe@example.com')
        self.assertEqual(uid1['profile']['is_bot'], False)
        self.assertEqual(uid1['profile']['country']['alpha3'], 'USA')
        self.assertEqual(uid1['profile']['country']['code'], 'US')
        self.assertEqual(uid1['profile']['country']['name'], 'United States of America')

        ids = uid1['identities']
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertEqual(id0['id'], '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(id0['name'], 'Jane Roe')
        self.assertEqual(id0['email'], 'jroe@example.com')
        self.assertEqual(id0['username'], 'jroe')
        self.assertEqual(id0['source'], 'scm')
        self.assertEqual(id0['uuid'], '52e0aa0a14826627e633fd15332988686b730ab3')

        id1 = ids[1]
        self.assertEqual(id1['id'], 'cbfb7bd31d556322c640f5bc7b31d58a12b15904')
        self.assertEqual(id1['name'], None)
        self.assertEqual(id1['email'], 'jroe@bitergia.com')
        self.assertEqual(id1['username'], None)
        self.assertEqual(id1['source'], 'unknown')
        self.assertEqual(id1['uuid'], '52e0aa0a14826627e633fd15332988686b730ab3')

        id2 = ids[2]
        self.assertEqual(id2['id'], 'fef873c50a48cfc057f7aa19f423f81889a8907f')
        self.assertEqual(id2['name'], None)
        self.assertEqual(id2['email'], 'jroe@example.com')
        self.assertEqual(id2['username'], None)
        self.assertEqual(id2['source'], 'scm')
        self.assertEqual(id2['uuid'], '52e0aa0a14826627e633fd15332988686b730ab3')

        enrollments = uid1['enrollments']
        self.assertEqual(len(enrollments), 3)

        rol0 = enrollments[0]
        self.assertEqual(rol0['uuid'], '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(rol0['organization'], 'Bitergia')
        self.assertEqual(rol0['start'], '1999-01-01T00:00:00')
        self.assertEqual(rol0['end'], '2000-01-01T00:00:00')

        rol1 = enrollments[1]
        self.assertEqual(rol1['uuid'], '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(rol1['organization'], 'Bitergia')
        self.assertEqual(rol1['start'], '2006-01-01T00:00:00')
        self.assertEqual(rol1['end'], '2008-01-01T00:00:00')

        rol2 = enrollments[2]
        self.assertEqual(rol2['uuid'], '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(rol2['organization'], 'Example')
        self.assertEqual(rol2['start'], '1900-01-01T00:00:00')
        self.assertEqual(rol2['end'], '2100-01-01T00:00:00')

        # John Smith
        uid2 = uidentities['03e12d00e37fd45593c49a5a5a1652deca4cf302']
        self.assertEqual(uid2['uuid'], '03e12d00e37fd45593c49a5a5a1652deca4cf302')

        self.assertEqual(uid2['profile']['uuid'], '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(uid2['profile']['name'], None)
        self.assertEqual(uid2['profile']['email'], 'jsmith@example.com')
        self.assertEqual(uid2['profile']['is_bot'], True)

        ids = uid2['identities']
        self.assertEqual(len(ids), 2)

        id0 = ids[0]
        self.assertEqual(id0['id'], '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(id0['name'], 'John Smith')
        self.assertEqual(id0['email'], 'jsmith@example.com')
        self.assertEqual(id0['username'], 'jsmith')
        self.assertEqual(id0['source'], 'scm')
        self.assertEqual(id0['uuid'], '03e12d00e37fd45593c49a5a5a1652deca4cf302')

        id1 = ids[1]
        self.assertEqual(id1['id'], '75d95d6c8492fd36d24a18bd45d62161e05fbc97')
        self.assertEqual(id1['name'], 'John Smith')
        self.assertEqual(id1['email'], 'jsmith@example.com')
        self.assertEqual(id1['username'], None)
        self.assertEqual(id1['source'], 'scm')
        self.assertEqual(id1['uuid'], '03e12d00e37fd45593c49a5a5a1652deca4cf302')

        enrollments = uid2['enrollments']
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertEqual(rol0['uuid'], '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(rol0['organization'], 'Example')
        self.assertEqual(rol0['start'], '1900-01-01T00:00:00')
        self.assertEqual(rol0['end'], '2100-01-01T00:00:00')

        # Check blacklist
        blacklist = obj['blacklist']
        self.assertEqual(len(blacklist), 2)

        bl0 = blacklist[0]
        self.assertEqual(bl0, 'John Smith')

        bl1 = blacklist[1]
        self.assertEqual(bl1, 'jroe@example.com')

    def test_source(self):
        """Check output when source is given"""

        exporter = SortingHatIdentitiesExporter(self.db)

        # There's no identity with this source, thus the result
        # should be empty
        dump = exporter.export(source='its')
        obj = json.loads(dump)

        self.assertEqual(obj['source'], 'its')
        self.assertEqual(len(obj['uidentities']), 0)

        # Using 'unknown' source should return the uidentity
        # of Jane Roe
        dump = exporter.export(source='unknown')
        obj = json.loads(dump)

        self.assertEqual(obj['source'], 'unknown')

        uidentities = obj['uidentities']
        self.assertEqual(len(uidentities), 1)

        uid = uidentities['52e0aa0a14826627e633fd15332988686b730ab3']
        self.assertEqual(uid['uuid'], '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(len(uid['identities']), 3)
        self.assertEqual(len(uid['enrollments']), 3)

        # Check blacklist
        blacklist = obj['blacklist']
        self.assertEqual(len(blacklist), 2)

        bl0 = blacklist[0]
        self.assertEqual(bl0, 'John Smith')

        bl1 = blacklist[1]
        self.assertEqual(bl1, 'jroe@example.com')

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Remove pre-loaded test dataset
        self.db.clear()

        exporter = SortingHatIdentitiesExporter(self.db)
        dump = exporter.export()
        obj = json.loads(dump)

        self.assertEqual(obj['source'], None)
        self.assertIn('time', obj)
        self.assertEqual(len(obj['uidentities']), 0)
        self.assertEqual(len(obj['blacklist']), 0)


class TestExportOrganizations(TestExportCaseBase):
    """Test export_organizations method with some inputs"""

    def test_export_organizations(self):
        """Check the output of export_identities method"""

        with open(self.tmpfile, 'w') as f:
            self.cmd.export_organizations(f)

        # Read results and pre-generated file to tests whether
        # both are the same. To compare, we generate a dict object
        # removing 'time' key.
        a = self.read_json(self.tmpfile)
        b = self.read_json('data/sortinghat_orgs.json')

        a.pop('time')
        b.pop('time')

        self.assertEqual(a, b)

    def test_export_organizations_empty_registry(self):
        """Check the output when registry is empty"""

        # Remove pre-loaded test dataset
        self.db.clear()

        with open(self.tmpfile, 'w') as f:
            self.cmd.export_organizations(f)

        a = self.read_json(self.tmpfile)

        self.assertIn('time', a)
        self.assertEqual(len(a['organizations']), 0)


class TestSortingHatOrganizationsExporter(TestExportCaseBase):
    """Test Sorting Hat exporter"""

    def test_export(self):
        """Test the output from export"""

        exporter = SortingHatOrganizationsExporter(self.db)
        dump = exporter.export()

        # The best way to check this is to build a JSON object
        # with the output from export()
        obj = json.loads(dump)

        self.assertIn('time', obj)

        orgs = obj['organizations']
        self.assertEqual(len(orgs), 3)

        # Bitergia
        org0 = orgs['Bitergia']
        self.assertEqual(len(org0), 4)

        dom0 = org0[0]
        self.assertEqual(dom0['domain'], 'api.bitergia.com')
        self.assertEqual(dom0['is_top'], False)

        dom1 = org0[1]
        self.assertEqual(dom1['domain'], 'bitergia.com')
        self.assertEqual(dom1['is_top'], True)

        dom2 = org0[2]
        self.assertEqual(dom2['domain'], 'bitergia.net')
        self.assertEqual(dom2['is_top'], True)

        dom3 = org0[3]
        self.assertEqual(dom3['domain'], 'test.bitergia.com')
        self.assertEqual(dom3['is_top'], False)

        # Example
        org1 = orgs['Example']
        self.assertEqual(len(org1), 2)

        dom0 = org1[0]
        self.assertEqual(dom0['domain'], 'example.com')
        self.assertEqual(dom0['is_top'], True)

        dom1 = org1[1]
        self.assertEqual(dom1['domain'], 'example.net')
        self.assertEqual(dom1['is_top'], True)

        # Unknown (empty list of domains)
        org2 = orgs['Unknown']
        self.assertEqual(len(org2), 0)

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Remove pre-loaded test dataset
        self.db.clear()

        exporter = SortingHatOrganizationsExporter(self.db)
        dump = exporter.export()
        obj = json.loads(dump)

        self.assertIn('time', obj)
        self.assertEqual(len(obj['organizations']), 0)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
