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
from sortinghat.parsing.mozilla import MOZILLIANS_ORG, MozilliansParser

from tests.base import datadir


MOZILLIANS_INVALID_JSON_FORMAT_ERROR = r"invalid json format\. Expecting ':' delimiter"
MOZILLIANS_IDS_MISSING_KEYS_ERROR = "Attribute full_name not found"
MOZILLIANS_STREAM_INVALID_ERROR = "stream cannot be empty or None"


class TestBaseCase(unittest.TestCase):
    """Defines common methods for unit tests"""

    def read_file(self, filename):
        with open(filename, 'r', encoding='UTF-8') as f:
            content = f.read()

        return content


class TestMozilliansParser(TestBaseCase):
    """Test Mozillians parser with some inputs"""

    def test_valid_identities_stream(self):
        """Check insertion of valid data from a file"""

        stream = self.read_file(datadir('mozillians_valid.json'))

        parser = MozilliansParser(stream, source='unknown')
        uids = parser.identities

        # Check parsed identities
        self.assertEqual(len(uids), 3)

        # John Doe identity
        uid = uids[0]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'john_doe')
        self.assertEqual(len(uid.identities), 2)

        id0 = uid.identities[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.id, None)
        self.assertEqual(id0.name, None)
        self.assertEqual(id0.email, None)
        self.assertEqual(id0.username, 'john_doe')
        self.assertEqual(id0.uuid, 'john_doe')
        self.assertEqual(id0.source, 'unknown')

        # IRC identity
        id1 = uid.identities[1]
        self.assertIsInstance(id1, Identity)
        self.assertEqual(id1.id, None)
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, None)
        self.assertEqual(id1.username, 'jdoe')
        self.assertEqual(id1.uuid, 'john_doe')
        self.assertEqual(id1.source, 'unknown')

        enrollments = uid.enrollments
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertIsInstance(rol0.organization, Organization)
        self.assertEqual(rol0.organization.name, MOZILLIANS_ORG)
        self.assertEqual(rol0.start, datetime.datetime(2015, 6, 1, 0, 0, 0))

        # Jane Rae unique identity
        uid = uids[1]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jrae')
        self.assertEqual(len(uid.identities), 3)

        id0 = uid.identities[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.id, None)
        self.assertEqual(id0.name, 'Jane Rae')
        self.assertEqual(id0.email, None)
        self.assertEqual(id0.username, 'jrae')
        self.assertEqual(id0.uuid, 'jrae')
        self.assertEqual(id0.source, 'unknown')

        id1 = uid.identities[1]
        self.assertIsInstance(id1, Identity)
        self.assertEqual(id1.id, None)
        self.assertEqual(id1.name, 'Jane Rae')
        self.assertEqual(id1.email, 'janerae@example.com')
        self.assertEqual(id1.username, 'jrae')
        self.assertEqual(id1.uuid, 'jrae')
        self.assertEqual(id1.source, 'unknown')

        id2 = uid.identities[2]
        self.assertIsInstance(id2, Identity)
        self.assertEqual(id2.id, None)
        self.assertEqual(id2.name, 'Jane Rae')
        self.assertEqual(id2.email, 'jrae@example.org')
        self.assertEqual(id2.username, 'jrae')
        self.assertEqual(id2.uuid, 'jrae')
        self.assertEqual(id2.source, 'unknown')

        enrollments = uid.enrollments
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertIsInstance(rol0.organization, Organization)
        self.assertEqual(rol0.organization.name, MOZILLIANS_ORG)
        self.assertEqual(rol0.start, datetime.datetime(1900, 1, 1, 0, 0, 0))

        # John Smith unique identity
        uid = uids[2]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jsmith')
        self.assertEqual(len(uid.identities), 1)

        # Only one identity found. No alternative emails
        # and ircname is equal to username value
        id0 = uid.identities[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.id, None)
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, 'jsmith')
        self.assertEqual(id0.uuid, 'jsmith')
        self.assertEqual(id0.source, 'unknown')

        enrollments = uid.enrollments
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertIsInstance(rol0.organization, Organization)
        self.assertEqual(rol0.organization.name, MOZILLIANS_ORG)
        self.assertEqual(rol0.start, datetime.datetime(1900, 1, 1, 0, 0, 0))

    def test_valid_organizations_stream(self):
        """Check whether it parses organizations section from a valid stream"""

        stream = self.read_file(datadir('mozillians_valid.json'))

        parser = MozilliansParser(stream)
        orgs = parser.organizations

        # Check parsed organizations
        self.assertEqual(len(orgs), 1)

        org = orgs[0]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, MOZILLIANS_ORG)

    def test_not_valid_stream(self):
        """Check whether it prints an error when parsing invalid streams"""

        with self.assertRaisesRegex(InvalidFormatError,
                                    MOZILLIANS_INVALID_JSON_FORMAT_ERROR):
            s = self.read_file(datadir('mozillians_invalid.json'))
            MozilliansParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    MOZILLIANS_IDS_MISSING_KEYS_ERROR):
            s = self.read_file(datadir('mozillians_ids_missing_keys.json'))
            MozilliansParser(s)

    def test_empty_stream(self):
        """Check whether it raises an exception when the stream is empty"""

        with self.assertRaisesRegex(InvalidFormatError,
                                    MOZILLIANS_STREAM_INVALID_ERROR):
            MozilliansParser("")

    def test_none_stream(self):
        """Check whether it raises an exception when the stream is None"""

        with self.assertRaisesRegex(InvalidFormatError,
                                    MOZILLIANS_STREAM_INVALID_ERROR):
            MozilliansParser(None)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
