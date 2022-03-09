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

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat.db.model import UniqueIdentity, Identity, Organization
from sortinghat.exceptions import InvalidFormatError
from sortinghat.parsing.mailmap import MailmapParser

from tests.base import datadir


class TestBaseCase(unittest.TestCase):
    """Defines common methods for unit tests"""

    def read_file(self, filename):
        with open(filename, 'r', encoding='UTF-8') as f:
            content = f.read()

        return content


class TestMailmapParser(TestBaseCase):
    """Test Mailmap parser with some inputs"""

    def test_valid_identities_stream(self):
        """Check parsed identities from a valid file"""

        stream = self.read_file(datadir('mailmap_identities.txt'))
        parser = MailmapParser(stream, source='unknown')

        # Check parsed identities
        uids = parser.identities

        self.assertEqual(len(uids), 3)

        # John Doe identity
        uid = uids[0]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'j@doe.com')
        self.assertEqual(len(uid.identities), 3)

        id_ = uid.identities[0]
        self.assertIsInstance(id_, Identity)
        self.assertEqual(id_.id, None)
        self.assertEqual(id_.name, 'John Doe')
        self.assertEqual(id_.email, 'j@doe.com')
        self.assertEqual(id_.username, None)
        self.assertEqual(id_.uuid, 'j@doe.com')
        self.assertEqual(id_.source, 'unknown')

        id_ = uid.identities[1]
        self.assertIsInstance(id_, Identity)
        self.assertEqual(id_.id, None)
        self.assertEqual(id_.name, 'John Doe')
        self.assertEqual(id_.email, 'jdoe@example.net')
        self.assertEqual(id_.username, None)
        self.assertEqual(id_.uuid, 'j@doe.com')
        self.assertEqual(id_.source, 'unknown')

        id_ = uid.identities[2]
        self.assertIsInstance(id_, Identity)
        self.assertEqual(id_.id, None)
        self.assertEqual(id_.name, 'Doe J')
        self.assertEqual(id_.email, 'jdoe@example.net')
        self.assertEqual(id_.username, None)
        self.assertEqual(id_.uuid, 'j@doe.com')
        self.assertEqual(id_.source, 'unknown')

        self.assertEqual(len(uid.enrollments), 0)

        # Jane Rae identity
        uid = uids[1]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jrae@nomail.net')
        self.assertEqual(len(uid.identities), 3)

        id_ = uid.identities[0]
        self.assertIsInstance(id_, Identity)
        self.assertEqual(id_.id, None)
        self.assertEqual(id_.name, 'Jane Rae')
        self.assertEqual(id_.email, 'jrae@nomail.net')
        self.assertEqual(id_.username, None)
        self.assertEqual(id_.uuid, 'jrae@nomail.net')
        self.assertEqual(id_.source, 'unknown')

        id_ = uid.identities[1]
        self.assertIsInstance(id_, Identity)
        self.assertEqual(id_.id, None)
        self.assertEqual(id_.name, 'Jane R. Rae')
        self.assertEqual(id_.email, 'jrae@example.net')
        self.assertEqual(id_.username, None)
        self.assertEqual(id_.uuid, 'jrae@nomail.net')
        self.assertEqual(id_.source, 'unknown')

        id_ = uid.identities[2]
        self.assertIsInstance(id_, Identity)
        self.assertEqual(id_.id, None)
        self.assertEqual(id_.name, 'Jane')
        self.assertEqual(id_.email, 'jrae@example.net')
        self.assertEqual(id_.username, None)
        self.assertEqual(id_.uuid, 'jrae@nomail.net')
        self.assertEqual(id_.source, 'unknown')

        self.assertEqual(len(uid.enrollments), 0)

        # Jonh Smith identity
        uid = uids[2]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jsmith@example.com')
        self.assertEqual(len(uid.identities), 2)

        id_ = uid.identities[0]
        self.assertIsInstance(id_, Identity)
        self.assertEqual(id_.id, None)
        self.assertEqual(id_.name, 'John Smith')
        self.assertEqual(id_.email, 'jsmith@example.com')
        self.assertEqual(id_.username, None)
        self.assertEqual(id_.uuid, 'jsmith@example.com')
        self.assertEqual(id_.source, 'unknown')

        id_ = uid.identities[1]
        self.assertIsInstance(id_, Identity)
        self.assertEqual(id_.id, None)
        self.assertEqual(id_.name, 'John Smith')
        self.assertEqual(id_.email, 'jsmith@example.net')
        self.assertEqual(id_.username, None)
        self.assertEqual(id_.uuid, 'jsmith@example.com')
        self.assertEqual(id_.source, 'unknown')

        # No organizations were parsed
        orgs = parser.organizations
        self.assertEqual(len(orgs), 0)

    def test_valid_organizations_stream(self):
        """Check parsed orgs and identities from a valid file"""

        stream = self.read_file(datadir('mailmap_orgs.txt'))
        parser = MailmapParser(stream, has_orgs=True, source='unknown')

        # Check parsed organizations
        # Unaffiliated was not included because it is not considered
        # as an organization
        orgs = parser.organizations

        self.assertEqual(len(orgs), 2)

        org = orgs[0]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Bitergia')
        self.assertEqual(len(org.domains), 0)

        org = orgs[1]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Example Inc.')
        self.assertEqual(len(org.domains), 0)

        # Check identities and enrollments
        uids = parser.identities

        self.assertEqual(len(uids), 3)

        # John Doe identity
        uid = uids[0]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jdoe@bitergia.com')
        self.assertEqual(len(uid.identities), 1)

        id0 = uid.identities[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.id, None)
        self.assertEqual(id0.name, 'John Doe')
        self.assertEqual(id0.email, 'jdoe@bitergia.com')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.uuid, 'jdoe@bitergia.com')
        self.assertEqual(id0.source, 'unknown')

        enrollments = uid.enrollments
        self.assertEqual(len(enrollments), 1)

        rol = enrollments[0]
        self.assertIsInstance(rol.organization, Organization)
        self.assertEqual(rol.organization.name, 'Bitergia')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1, 0, 0, 0))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1, 0, 0, 0))

        # Jane Rae identity
        uid = uids[1]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jrae@nomail.net')
        self.assertEqual(len(uid.identities), 1)

        id0 = uid.identities[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.id, None)
        self.assertEqual(id0.name, 'Jane Rae')
        self.assertEqual(id0.email, 'jrae@nomail.net')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.uuid, 'jrae@nomail.net')
        self.assertEqual(id0.source, 'unknown')

        enrollments = uid.enrollments
        self.assertEqual(len(enrollments), 0)

        # John Smith identity
        uid = uids[2]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jsmith@example.com')
        self.assertEqual(len(uid.identities), 1)

        id0 = uid.identities[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.id, None)
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.uuid, 'jsmith@example.com')
        self.assertEqual(id0.source, 'unknown')

        enrollments = uid.enrollments
        self.assertEqual(len(enrollments), 2)

        rol = enrollments[0]
        self.assertIsInstance(rol.organization, Organization)
        self.assertEqual(rol.organization.name, 'Bitergia')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1, 0, 0, 0))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1, 0, 0, 0))

        rol = enrollments[1]
        self.assertIsInstance(rol.organization, Organization)
        self.assertEqual(rol.organization.name, 'Example Inc.')
        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1, 0, 0, 0))
        self.assertEqual(rol.end, datetime.datetime(2100, 1, 1, 0, 0, 0))

    def test_not_valid_stream(self):
        """Check whether it prints an error when parsing invalid streams"""

        with self.assertRaises(InvalidFormatError):
            s = self.read_file(datadir('mailmap_invalid.txt'))
            MailmapParser(s)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
