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
from sortinghat.parsing.eclipse import EclipseParser

from tests.base import datadir


ECLIPSE_INVALID_JSON_FORMAT_ERROR = r"invalid json format\. Expecting ':' delimiter"
ECLIPSE_IDS_MISSING_KEYS_ERROR = "Attribute active not found"
ECLIPSE_ORGS_MISSING_KEYS_ERROR = "Attribute name not found"
ECLIPSE_DATETIME_ERROR = "2008-02-30 is not a valid date"
ECLIPSE_STREAM_INVALID_ERROR = "stream cannot be empty or None"


class TestBaseCase(unittest.TestCase):
    """Defines common methods for unit tests"""

    def read_file(self, filename):
        with open(filename, 'r', encoding='UTF-8') as f:
            content = f.read()

        return content


class TestEclipseParser(TestBaseCase):
    """Test Eclipse parser with some inputs"""

    def test_valid_identities_stream(self):
        """Check insertion of valid data from a file"""

        stream = self.read_file(datadir('eclipse_valid.json'))

        parser = EclipseParser(stream, source='unknown')
        uids = parser.identities

        # Check parsed identities
        self.assertEqual(len(uids), 3)

        # John Doe unique identity
        uid = uids[0]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jdoe')
        self.assertEqual(len(uid.identities), 1)

        id0 = uid.identities[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.id, None)
        self.assertEqual(id0.name, 'John Doe')
        self.assertEqual(id0.email, 'jdoe@example.com')
        self.assertEqual(id0.username, 'jdoe')
        self.assertEqual(id0.uuid, 'jdoe')
        self.assertEqual(id0.source, 'unknown')

        enrollments = uid.enrollments
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertIsInstance(rol0.organization, Organization)
        self.assertEqual(rol0.organization.name, 'Example')
        self.assertEqual(rol0.start, datetime.datetime(2010, 1, 1, 0, 0, 0))

        # The parsed end date shoud be 2100-01-01 but because there is
        # an inactive date for Example, this end date is set to the
        # inactive date
        self.assertEqual(rol0.end, datetime.datetime(2014, 9, 1, 0, 0, 0))

        # Jane Rae identity
        uid = uids[1]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jrae')
        self.assertEqual(len(uid.identities), 1)

        id0 = uid.identities[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.id, None)
        self.assertEqual(id0.name, 'Jane Rae')
        self.assertEqual(id0.email, 'jrae@example.com')
        self.assertEqual(id0.username, 'jrae')
        self.assertEqual(id0.uuid, 'jrae')
        self.assertEqual(id0.source, 'unknown')

        enrollments = uid.enrollments
        self.assertEqual(len(enrollments), 0)

        # John Smith unique identity
        uid = uids[2]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'jsmith')
        self.assertEqual(len(uid.identities), 2)

        id0 = uid.identities[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.id, None)
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, 'jsmith')
        self.assertEqual(id0.uuid, 'jsmith')
        self.assertEqual(id0.source, 'unknown')

        id1 = uid.identities[1]
        self.assertIsInstance(id1, Identity)
        self.assertEqual(id1.id, None)
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@bitergia.com')
        self.assertEqual(id1.username, 'jsmith')
        self.assertEqual(id1.uuid, 'jsmith')
        self.assertEqual(id1.source, 'unknown')

        enrollments = uid.enrollments
        enrollments.sort(key=lambda x: x.start)
        self.assertEqual(len(enrollments), 2)

        rol0 = enrollments[0]
        self.assertIsInstance(rol0.organization, Organization)
        self.assertEqual(rol0.organization.name, 'Example')
        self.assertEqual(rol0.start, datetime.datetime(2010, 1, 1))
        self.assertEqual(rol0.end, datetime.datetime(2011, 1, 1))

        rol1 = enrollments[1]
        self.assertIsInstance(rol1.organization, Organization)
        self.assertEqual(rol1.organization.name, 'Bitergia')

        # Active date for Bitergia is 2012-01-01, so this enrollment
        # has that date instead of 2011-01-01
        self.assertEqual(rol1.start, datetime.datetime(2012, 1, 1))
        self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1))

    def test_valid_organizations_stream(self):
        """Check whether it parses organizations section from a valid stream"""

        stream = self.read_file(datadir('eclipse_valid.json'))

        parser = EclipseParser(stream)
        orgs = parser.organizations
        orgs.sort(key=lambda x: x.name)

        # Check parsed organizations
        self.assertEqual(len(orgs), 2)

        # This objects store additional information
        # regarding when an organization is active or inactive

        # Bitergia entry
        org = orgs[0]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Bitergia')
        self.assertEqual(org.active, datetime.datetime(2012, 1, 1, 0, 0, 0))
        self.assertEqual(org.inactive, datetime.datetime(2100, 1, 1, 0, 0, 0))

        # Example entry
        org = orgs[1]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Example')
        self.assertEqual(org.active, datetime.datetime(2009, 1, 1, 0, 0, 0))
        self.assertEqual(org.inactive, datetime.datetime(2014, 9, 1, 0, 0, 0))

    def test_not_valid_stream(self):
        """Check whether it prints an error when parsing invalid streams"""

        with self.assertRaisesRegex(InvalidFormatError,
                                    ECLIPSE_INVALID_JSON_FORMAT_ERROR):
            s = self.read_file(datadir('eclipse_invalid.json'))
            EclipseParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    ECLIPSE_IDS_MISSING_KEYS_ERROR):
            s = self.read_file(datadir('eclipse_ids_missing_keys.json'))
            EclipseParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    ECLIPSE_ORGS_MISSING_KEYS_ERROR):
            s = self.read_file(datadir('eclipse_orgs_missing_keys.json'))
            EclipseParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    ECLIPSE_DATETIME_ERROR):
            s = self.read_file(datadir('eclipse_invalid_datetime.json'))
            EclipseParser(s)

    def test_empty_stream(self):
        """Check whether it raises an exception when the stream is empty"""

        with self.assertRaisesRegex(InvalidFormatError,
                                    ECLIPSE_STREAM_INVALID_ERROR):
            EclipseParser("")

    def test_none_stream(self):
        """Check whether it raises an exception when the stream is None"""

        with self.assertRaisesRegex(InvalidFormatError,
                                    ECLIPSE_STREAM_INVALID_ERROR):
            EclipseParser(None)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
