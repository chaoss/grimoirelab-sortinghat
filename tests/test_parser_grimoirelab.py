#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Bitergia
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
#     Luis Cañas-Díaz <lcanas@bitergia.com>
#

from __future__ import unicode_literals

import datetime
import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat.db.model import UniqueIdentity, Identity, Enrollment, Organization, Domain
from sortinghat.exceptions import InvalidFormatError
from sortinghat.parsing.grimoirelab import GrimoireLabParser

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


class TestGrimoreLabParser(TestBaseCase):
    """Test GrimoireLabParser parser"""

    def test_call_with_empty_parameters(self):
        """Check if library accepts a call with None parameters"""
        with self.assertRaises(ValueError):
            GrimoireLabParser(None, None)

    def test_identities_parser(self):
        """Check whether it parses a valid identities file"""

        stream_ids = self.read_file('data/grimoirelab_valid.yml')

        parser = GrimoireLabParser(stream_ids)

        # Parsed unique identities
        uids = parser.identities
        self.assertEqual(len(uids), 3)

        # J. Manrique Lopez de la Fuente
        uid = uids[0]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'J. Manrique Lopez de la Fuentejsmanrique@bitergia.comjsmanrique')
        self.assertFalse(uid.profile.is_bot)
        self.assertEqual(uid.profile.name,'J. Manrique Lopez de la Fuente')

        ids = uid.identities
        self.assertEqual(len(ids), 4)

        id0 = ids[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.name, 'J. Manrique Lopez de la Fuente')
        self.assertEqual(id0.email, None)
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'grimoirelab')
        self.assertEqual(id0.uuid, None)

        id1 = ids[1]
        self.assertIsInstance(id1, Identity)
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jsmanrique@bitergia.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'grimoirelab')
        self.assertEqual(id1.uuid, None)

        id1 = ids[2]
        self.assertIsInstance(id1, Identity)
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, None)
        self.assertEqual(id1.username, 'jsmanrique')
        self.assertEqual(id1.source, 'github')
        self.assertEqual(id1.uuid, None)

        id1 = ids[3]
        self.assertIsInstance(id1, Identity)
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, None)
        self.assertEqual(id1.username, 'jsm')
        self.assertEqual(id1.source, 'jira')
        self.assertEqual(id1.uuid, None)

        # Luis Cañas-Díaz
        uid = uids[1]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'Luis Cañas-Díazlcanas@bitergia.comsanacl')
        self.assertFalse(uid.profile.is_bot)
        self.assertEqual(uid.profile.name,'Luis Cañas-Díaz')

        self.assertIsInstance(uid, UniqueIdentity)

        ids = uid.identities
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.name, 'Luis Cañas-Díaz')
        self.assertEqual(id0.email, None)
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'grimoirelab')
        self.assertEqual(id0.uuid, None)

        id1 = ids[1]
        self.assertIsInstance(id1, Identity)
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'lcanas@bitergia.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'grimoirelab')
        self.assertEqual(id1.uuid, None)

        id1 = ids[2]
        self.assertIsInstance(id1, Identity)
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, None)
        self.assertEqual(id1.username, 'sanacl')
        self.assertEqual(id1.source, 'github')
        self.assertEqual(id1.uuid, None)

        # owlbot
        uid = uids[2]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'Owl Botowlbot@bitergia.com')
        self.assertTrue(uid.profile.is_bot)

        self.assertIsInstance(uid, UniqueIdentity)

        ids = uid.identities
        self.assertEqual(len(ids), 2)

        id0 = ids[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.name, 'Owl Bot')
        self.assertEqual(id0.email, None)
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'grimoirelab')
        self.assertEqual(id0.uuid, None)

        id0 = ids[1]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.name, None)
        self.assertEqual(id0.email, 'owlbot@bitergia.com')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.source, 'grimoirelab')
        self.assertEqual(id0.uuid, None)

    def test_organizations_parser(self):
        """Check whether it parses a valid organizations file"""

        stream_orgs = self.read_file('data/grimoirelab_orgs_valid.yml')

        parser = GrimoireLabParser(domain_employer=stream_orgs)

        # Parsed organizations
        orgs = parser.organizations

        self.assertEqual(len(orgs), 3)

        # Bitergia entries
        org = orgs[0]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Bitergia')

        doms = org.domains
        self.assertEqual(len(doms), 2)

        dom = doms[0]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'bitergia.com')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[1]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'bitergia.net')
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

    def test_enrollments_parser(self):
        """Check whether enrollments are correctly parsed"""

        stream_ids = self.read_file('data/grimoirelab_valid.yml')

        parser = GrimoireLabParser(stream_ids)

        # Parsed unique identities
        uids = parser.identities

        # J. Manrique Lopez de la Fuente
        uid = uids[0]
        rol = uid.enrollments[0]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.organization.name, 'Bitergia')
        self.assertEqual(rol.start, datetime.datetime(2013, 1, 1, 0, 0))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1, 0, 0))

        # Luis Cañas-Díaz
        uid = uids[1]
        rol = uid.enrollments[0]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.organization.name, 'GSyC/LibreSoft')
        self.assertEqual(rol.start, datetime.datetime(2003, 1, 1, 0, 0))
        self.assertEqual(rol.end, datetime.datetime(2011, 12, 31, 0, 0))

        rol = uid.enrollments[1]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.organization.name, 'Bitergia')
        self.assertEqual(rol.start, datetime.datetime(2012, 1, 1, 0, 0))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1, 0, 0))

    def test_not_valid_organizations_stream(self):
        """Check whether it parses invalid organizations files"""

        # empty domains
        stream_orgs = self.read_file('data/grimoirelab_orgs_invalid_empty_domains.yml')
        with self.assertRaises(InvalidFormatError):
            GrimoireLabParser(domain_employer=stream_orgs)

        # one of the domains is empty
        stream_orgs = self.read_file('data/grimoirelab_orgs_invalid_domains_list_with_empty_value.yml')
        with self.assertRaises(InvalidFormatError):
            GrimoireLabParser(domain_employer=stream_orgs)

        # domains got a string instead of a list
        stream_orgs = self.read_file('data/grimoirelab_orgs_invalid_wrong_domains_type.yml')
        with self.assertRaises(InvalidFormatError):
            GrimoireLabParser(domain_employer=stream_orgs)

        # organization key missing
        stream_orgs = self.read_file('data/grimoirelab_orgs_invalid_missing_key.yml')
        with self.assertRaises(InvalidFormatError):
            GrimoireLabParser(domain_employer=stream_orgs)

        # organization key with empty value
        stream_orgs = self.read_file('data/grimoirelab_orgs_invalid_key_with_no_value.yml')
        with self.assertRaises(InvalidFormatError):
            GrimoireLabParser(domain_employer=stream_orgs)

    def test_not_valid_identities_stream(self):
        """Check whether it parses invalid identities files"""

        stream_ids = self.read_file('data/grimoirelab_invalid_email.yml')
        with self.assertRaises(InvalidFormatError):
            GrimoireLabParser(stream_ids)

        stream_ids = self.read_file('data/grimoirelab_invalid_structure.yml')
        with self.assertRaises(InvalidFormatError):
            GrimoireLabParser(stream_ids)

        stream_ids = self.read_file('data/grimoirelab_invalid_missing_accounts.yml')
        with self.assertRaises(InvalidFormatError):
            GrimoireLabParser(stream_ids)

        stream_ids = self.read_file('data/grimoirelab_invalid_missing_profile_name_isbot.yml')
        with self.assertRaises(InvalidFormatError):
            GrimoireLabParser(stream_ids)

        stream_ids = self.read_file('data/grimoirelab_invalid_missing_profile.yml')
        with self.assertRaises(InvalidFormatError):
            GrimoireLabParser(stream_ids)

        stream_ids = self.read_file('data/grimoirelab_invalid_missing_organization_name.yml')
        with self.assertRaises(InvalidFormatError):
            GrimoireLabParser(stream_ids)

    def test_not_valid_enrollments_parser(self):
        """Check whether data from both identites and organizations files is coherent"""

        stream_ids = self.read_file('data/grimoirelab_invalid_datetime.yml')
        stream_orgs = self.read_file('data/grimoirelab_orgs_valid.yml')

        with self.assertRaises(InvalidFormatError):
            GrimoireLabParser(stream_ids, stream_orgs)


if __name__ == "__main__":
    unittest.main(buffer=False, exit=False)
