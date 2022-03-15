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

from sortinghat.db.model import UniqueIdentity, Organization, Domain, MatchingBlacklist
from sortinghat.exceptions import InvalidFormatError
from sortinghat.parsing.sh import SortingHatParser

from tests.base import datadir


SH_INVALID_JSON_FORMAT_ERROR = "invalid json format\\. Expecting ',' delimiter"
SH_BL_EMPTY_STRING_ERROR = "invalid json format. Blacklist entries cannot be null or empty"
SH_IDS_MISSING_KEYS_ERROR = "Attribute uuid not found"
SH_IDS_DATETIME_ERROR = "2100-01-32T00:00:00 is not a valid date"
SH_IDS_IS_BOT_ERROR = "'is_bot' must have a bool value"
SH_IDS_GENDER_ACC_TYPE_ERROR = "'gender_acc' must have an integer value"
SH_IDS_GENDER_ACC_RANGE_ERROR = "'gender_acc' is not in range"
SH_ORGS_MISSING_KEYS_ERROR = "Attribute is_top not found"
SH_ORGS_IS_TOP_ERROR = "'is_top' must have a bool value"

ORGS_INVALID_JSON_FORMAT_ERROR = "invalid json format. Expecting object"
ORGS_MISSING_KEYS_ERROR = "Attribute is_top not found"
ORGS_IS_TOP_ERROR = "'is_top' must have a bool value"
ORGS_STREAM_INVALID_ERROR = "stream cannot be empty or None"


class TestBaseCase(unittest.TestCase):
    """Defines common methods for unit tests"""

    def read_file(self, filename):
        with open(filename, 'r', encoding='UTF-8') as f:
            content = f.read()

        return content


class TestSortingHatParser(TestBaseCase):
    """Test SortingHat parser with some inputs"""

    def test_valid_blacklist_stream(self):
        """Check whether it parsers blacklist section from a valid stream"""

        stream = self.read_file(datadir('sortinghat_valid.json'))

        parser = SortingHatParser(stream)
        bl = parser.blacklist

        # Check parsed blacklist
        self.assertEqual(len(bl), 2)

        b = bl[0]
        self.assertIsInstance(b, MatchingBlacklist)
        self.assertEqual(b.excluded, 'John Smith')

        b = bl[1]
        self.assertIsInstance(b, MatchingBlacklist)
        self.assertEqual(b.excluded, 'jroe@example.com')

    def test_valid_identities_stream(self):
        """Check whether it parsers identities section from a valid stream"""

        stream = self.read_file(datadir('sortinghat_valid.json'))

        parser = SortingHatParser(stream)
        uids = parser.identities

        # Check parsed identities
        self.assertEqual(len(uids), 3)

        # 00000 identity
        uid = uids[0]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, '0000000000000000000000000000000000000000')

        prf = uid.profile
        self.assertEqual(prf.uuid, '0000000000000000000000000000000000000000')
        self.assertEqual(prf.name, None)
        self.assertEqual(prf.email, None)
        self.assertEqual(prf.gender, None)
        self.assertEqual(prf.gender_acc, None)
        self.assertEqual(prf.is_bot, False)
        self.assertEqual(prf.country_code, None)
        self.assertEqual(prf.country, None)

        self.assertEqual(len(uid.identities), 0)
        self.assertEqual(len(uid.enrollments), 0)

        # John Smith
        uid = uids[1]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')

        prf = uid.profile
        self.assertEqual(prf.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(prf.name, None)
        self.assertEqual(prf.email, 'jsmith@example.com')
        self.assertEqual(prf.gender, 'male')
        self.assertEqual(prf.gender_acc, 100)
        self.assertEqual(prf.is_bot, True)
        self.assertEqual(prf.country_code, None)
        self.assertEqual(prf.country, None)

        ids = uid.identities
        self.assertEqual(len(ids), 2)

        id0 = ids[0]
        self.assertEqual(id0.id, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(id0.name, 'John Smith')
        self.assertEqual(id0.email, 'jsmith@example.com')
        self.assertEqual(id0.username, 'jsmith')
        self.assertEqual(id0.source, 'scm')
        self.assertEqual(id0.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')

        id1 = ids[1]
        self.assertEqual(id1.id, '75d95d6c8492fd36d24a18bd45d62161e05fbc97')
        self.assertEqual(id1.name, 'John Smith')
        self.assertEqual(id1.email, 'jsmith@example.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'scm')
        self.assertEqual(id1.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')

        enrollments = uid.enrollments
        self.assertEqual(len(enrollments), 1)

        rol0 = enrollments[0]
        self.assertIsInstance(rol0.organization, Organization)
        self.assertEqual(rol0.organization.name, 'Example')
        self.assertEqual(rol0.start, datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(rol0.end, datetime.datetime(2100, 1, 1, 0, 0))

        # Jane Roe
        uid = uids[2]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')

        prf = uid.profile
        self.assertEqual(prf.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(prf.name, 'Jane Roe')
        self.assertEqual(prf.email, 'jroe@example.com')
        self.assertEqual(prf.gender, None)
        self.assertEqual(prf.gender_acc, None)
        self.assertEqual(prf.is_bot, False)
        self.assertEqual(prf.country_code, 'US')
        self.assertEqual(prf.country.alpha3, 'USA')
        self.assertEqual(prf.country.code, 'US')
        self.assertEqual(prf.country.name, 'United States of America')

        ids = uid.identities
        self.assertEqual(len(ids), 3)

        id0 = ids[0]
        self.assertEqual(id0.id, '52e0aa0a14826627e633fd15332988686b730ab3')
        self.assertEqual(id0.name, 'Jane Roe')
        self.assertEqual(id0.email, 'jroe@example.com')
        self.assertEqual(id0.username, 'jroe')
        self.assertEqual(id0.source, 'scm')
        self.assertEqual(id0.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')

        id1 = ids[1]
        self.assertEqual(id1.id, 'cbfb7bd31d556322c640f5bc7b31d58a12b15904')
        self.assertEqual(id1.name, None)
        self.assertEqual(id1.email, 'jroe@bitergia.com')
        self.assertEqual(id1.username, None)
        self.assertEqual(id1.source, 'unknown')
        self.assertEqual(id0.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')

        id2 = ids[2]
        self.assertEqual(id2.id, 'fef873c50a48cfc057f7aa19f423f81889a8907f')
        self.assertEqual(id2.name, None)
        self.assertEqual(id2.email, 'jroe@example.com')
        self.assertEqual(id2.username, None)
        self.assertEqual(id2.source, 'scm')
        self.assertEqual(id0.uuid, '52e0aa0a14826627e633fd15332988686b730ab3')

        enrollments = uid.enrollments
        self.assertEqual(len(enrollments), 3)

        rol0 = enrollments[0]
        self.assertIsInstance(rol0.organization, Organization)
        self.assertEqual(rol0.organization.name, 'Bitergia')
        self.assertEqual(rol0.start, datetime.datetime(1999, 1, 1, 0, 0))
        self.assertEqual(rol0.end, datetime.datetime(2000, 1, 1, 0, 0))

        rol1 = enrollments[1]
        self.assertIsInstance(rol0.organization, Organization)
        self.assertEqual(rol1.organization.name, 'Bitergia')
        self.assertEqual(rol1.start, datetime.datetime(2006, 1, 1, 0, 0))
        self.assertEqual(rol1.end, datetime.datetime(2008, 1, 1, 0, 0))

        rol2 = enrollments[2]
        self.assertIsInstance(rol0.organization, Organization)
        self.assertEqual(rol2.organization.name, 'Example')
        self.assertEqual(rol2.start, datetime.datetime(1900, 1, 1, 0, 0))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, 0, 0))

    def test_no_gender(self):
        """Check whether if parses identidies without gender information"""

        stream = self.read_file(datadir('sortinghat_valid_no_gender.json'))

        parser = SortingHatParser(stream)
        uids = parser.identities

        # Check parsed identities
        self.assertEqual(len(uids), 1)

        # John Smith
        uid = uids[0]
        self.assertIsInstance(uid, UniqueIdentity)
        self.assertEqual(uid.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')

        prf = uid.profile
        self.assertEqual(prf.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(prf.name, None)
        self.assertEqual(prf.email, 'jsmith@example.com')
        self.assertEqual(prf.gender, None)
        self.assertEqual(prf.gender_acc, None)
        self.assertEqual(prf.is_bot, True)
        self.assertEqual(prf.country_code, None)
        self.assertEqual(prf.country, None)

    def test_valid_organizations_stream(self):
        """Check whether it parses organizations section from a valid stream"""

        stream = self.read_file(datadir('sortinghat_valid.json'))

        parser = SortingHatParser(stream)
        orgs = parser.organizations

        # Check parsed organizations
        self.assertEqual(len(orgs), 3)

        # Bitergia entry
        org = orgs[0]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Bitergia')

        doms = org.domains
        self.assertEqual(len(doms), 4)

        dom = doms[0]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'api.bitergia.com')
        self.assertEqual(dom.is_top_domain, False)

        dom = doms[1]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'bitergia.com')
        self.assertEqual(dom.is_top_domain, True)

        dom = doms[2]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'bitergia.net')
        self.assertEqual(dom.is_top_domain, True)

        dom = doms[3]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'test.bitergia.com')
        self.assertEqual(dom.is_top_domain, False)

        # Example entry
        org = orgs[1]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Example')

        doms = org.domains
        self.assertEqual(len(doms), 2)

        dom = doms[0]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'example.com')
        self.assertEqual(dom.is_top_domain, True)

        dom = doms[1]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'example.net')
        self.assertEqual(dom.is_top_domain, True)

        # Unknown entry
        org = orgs[2]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Unknown')

        doms = org.domains
        self.assertEqual(len(doms), 0)

    def test_not_valid_stream(self):
        """Check whether it prints an error when parsing invalid streams"""

        with self.assertRaisesRegex(InvalidFormatError,
                                    SH_INVALID_JSON_FORMAT_ERROR):
            s = self.read_file(datadir('sortinghat_invalid.json'))
            SortingHatParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    SH_BL_EMPTY_STRING_ERROR):
            s = self.read_file(datadir('sortinghat_blacklist_empty_strings.json'))
            SortingHatParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    SH_IDS_MISSING_KEYS_ERROR):
            s = self.read_file(datadir('sortinghat_ids_missing_keys.json'))
            SortingHatParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    SH_ORGS_MISSING_KEYS_ERROR):
            s = self.read_file(datadir('sortinghat_orgs_missing_keys.json'))
            SortingHatParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    SH_IDS_DATETIME_ERROR):
            s = self.read_file(datadir('sortinghat_ids_invalid_date.json'))
            SortingHatParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    SH_IDS_IS_BOT_ERROR):
            s = self.read_file(datadir('sortinghat_ids_invalid_is_bot.json'))
            SortingHatParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    SH_IDS_GENDER_ACC_TYPE_ERROR):
            s = self.read_file(datadir('sortinghat_ids_invalid_type_gender_acc.json'))
            SortingHatParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    SH_IDS_GENDER_ACC_RANGE_ERROR):
            s = self.read_file(datadir('sortinghat_ids_invalid_range_gender_acc.json'))
            SortingHatParser(s)

        with self.assertRaisesRegex(InvalidFormatError,
                                    SH_ORGS_IS_TOP_ERROR):
            s = self.read_file(datadir('sortinghat_orgs_invalid_top.json'))
            SortingHatParser(s)

    def test_empty_stream(self):
        """Check whether it raises an exception when the stream is empty"""

        with self.assertRaisesRegex(InvalidFormatError,
                                    ORGS_STREAM_INVALID_ERROR):
            SortingHatParser("")

    def test_none_stream(self):
        """Check whether it raises an exception when the stream is None"""

        with self.assertRaisesRegex(InvalidFormatError,
                                    ORGS_STREAM_INVALID_ERROR):
            SortingHatParser(None)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
