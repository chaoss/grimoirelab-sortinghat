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

from sortinghat.db.model import MIN_PERIOD_DATE, MAX_PERIOD_DATE, \
    UniqueIdentity, Identity, Enrollment, Organization, Domain
from sortinghat.exceptions import InvalidFormatError
from sortinghat.parsing.stackalytics import StackalyticsParser

from tests.base import datadir


STACKALYTICS_INVALID_JSON_FORMAT_ERROR = r"invalid json format\. Expecting ':' delimiter"
STACKALYTICS_IDS_MISSING_KEYS_ERROR = "Attribute companies not found"
STACKALYTICS_ORGS_MISSING_KEYS_ERROR = "Attribute end_date not found"
STACKALYTICS_STREAM_INVALID_ERROR = "stream cannot be empty or None"


class TestBaseCase(unittest.TestCase):
    """Defines common methods for unit tests"""

    def read_file(self, filename):
        with open(filename, 'r', encoding='UTF-8') as f:
            content = f.read()

        return content


class TestStackalyticsParser(TestBaseCase):
    """Test Stackalytics parser with some inputs"""

    def test_valid_identities_stream(self):
        """Check insertion of valid data from a file"""

        stream = self.read_file(datadir('stackalytics_valid.json'))

        parser = StackalyticsParser(stream, source='unknown')
        uids = parser.identities

        # Check parsed identities
        self.assertEqual(len(uids), 2)

        # John Doe unique identity
        uid = uids[0]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'John Doe')
        self.assertEqual(len(uid.identities), 3)

        id0 = uid.identities[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.id, None)
        self.assertEqual(id0.name, 'John Doe')
        self.assertEqual(id0.email, None)
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.uuid, 'John Doe')
        self.assertEqual(id0.source, 'unknown')

        enrollments = uid.enrollments
        self.assertEqual(len(enrollments), 2)

        rol0 = enrollments[0]
        self.assertIsInstance(rol0, Enrollment)
        self.assertIsInstance(rol0.organization, Organization)
        self.assertEqual(rol0.organization.name, 'Bitergia')
        self.assertEqual(rol0.start, MIN_PERIOD_DATE)
        self.assertEqual(rol0.end, MAX_PERIOD_DATE)

        rol1 = enrollments[1]
        self.assertIsInstance(rol1, Enrollment)
        self.assertIsInstance(rol1.organization, Organization)
        self.assertEqual(rol1.organization.name, 'Example')
        self.assertEqual(rol1.start, MIN_PERIOD_DATE)
        self.assertEqual(rol1.end, datetime.datetime(2010, 1, 1, 0, 0, 0))

        # John Smith unique identity
        uid = uids[1]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, 'John Smith')
        self.assertEqual(len(uid.identities), 4)

        id0 = uid.identities[0]
        self.assertIsInstance(id0, Identity)
        self.assertEqual(id0.id, None)
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, None)
        self.assertEqual(id0.username, None)
        self.assertEqual(id0.uuid, 'John Smith')
        self.assertEqual(id0.source, 'unknown')

        id1 = uid.identities[1]
        self.assertIsInstance(id1, Identity)
        self.assertEqual(id1.id, None)
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.uuid, 'John Smith')
        self.assertEqual(id1.source, 'unknown')

        id2 = uid.identities[2]
        self.assertIsInstance(id2, Identity)
        self.assertEqual(id2.id, None)
        self.assertEqual(id2.name, 'John Smith')
        self.assertEqual(id2.email, None)
        self.assertEqual(id2.username, 'jsmith')
        self.assertEqual(id2.uuid, 'John Smith')
        self.assertEqual(id2.source, 'unknown:gerrit')

        id3 = uid.identities[3]
        self.assertIsInstance(id3, Identity)
        self.assertEqual(id3.id, None)
        self.assertEqual(id3.name, 'John Smith')
        self.assertEqual(id3.email, None)
        self.assertEqual(id3.username, '0-jsmith')
        self.assertEqual(id3.uuid, 'John Smith')
        self.assertEqual(id3.source, 'unknown:launchpad')

        enrollments = uid.enrollments
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertIsInstance(rol0, Enrollment)
        self.assertIsInstance(rol0.organization, Organization)
        self.assertEqual(rol0.organization.name, 'Example')
        self.assertEqual(rol0.start, MIN_PERIOD_DATE)
        self.assertEqual(rol0.end, MAX_PERIOD_DATE)

    def test_valid_organizations_stream(self):
        """Check whether it parses organizations section from a valid stream"""

        stream = self.read_file(datadir('stackalytics_valid.json'))

        parser = StackalyticsParser(stream)
        orgs = parser.organizations
        orgs.sort(key=lambda x: x.name)

        # Check parsed organizations
        self.assertEqual(len(orgs), 2)

        # Bitergia entry
        org = orgs[0]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Bitergia')

        doms = org.domains
        self.assertEqual(len(org.domains), 2)

        dom = doms[0]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'bitergia.net')

        dom = doms[1]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'bitergia.com')

        # Example entry
        org = orgs[1]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Example')
        self.assertEqual(len(org.domains), 0)

    def test_not_valid_stream(self):
        """Check whether it prints an error when parsing invalid streams"""

        with self.assertRaisesRegex(InvalidFormatError,
                                    STACKALYTICS_INVALID_JSON_FORMAT_ERROR):
            s = self.read_file(datadir('stackalytics_invalid.json'))
            StackalyticsParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    STACKALYTICS_IDS_MISSING_KEYS_ERROR):
            s = self.read_file(datadir('stackalytics_ids_missing_keys.json'))
            StackalyticsParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    STACKALYTICS_ORGS_MISSING_KEYS_ERROR):
            s = self.read_file(datadir('stackalytics_orgs_missing_keys.json'))
            StackalyticsParser(s)

    def test_empty_stream(self):
        """Check whether it raises an exception when the stream is empty"""

        with self.assertRaisesRegex(InvalidFormatError,
                                    STACKALYTICS_STREAM_INVALID_ERROR):
            StackalyticsParser("")

    def test_none_stream(self):
        """Check whether it raises an exception when the stream is None"""

        with self.assertRaisesRegex(InvalidFormatError,
                                    STACKALYTICS_STREAM_INVALID_ERROR):
            StackalyticsParser(None)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
