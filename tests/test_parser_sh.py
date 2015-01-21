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

import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat.db.model import Organization, Domain
from sortinghat.exceptions import InvalidFormatError
from sortinghat.parsing.sh import SortingHatOrganizationsParser


ORGS_INVALID_JSON_FORMAT_ERROR = "invalid json format. Expecting object"
ORGS_MISSING_KEYS_ERROR = "Attribute is_top not found"
ORGS_IS_TOP_ERROR = "'is_top' must have a bool value"
ORGS_STREAM_INVALID_ERROR = "stream cannot be empty or None"


class TestBaseCase(unittest.TestCase):
    """Defines common methods for unit tests"""

    def read_file(self, filename):
        with open(filename, 'r') as f:
            content = f.read().decode('UTF-8')
        return content


class TestSortingHatOrganizationsParser(TestBaseCase):
    """Test SortingHat parser with some inputs"""

    def test_valid_organizations_stream(self):
        """Check whether it parses a valid stream"""

        stream = self.read_file('data/sortinghat_orgs_valid.json')

        parser = SortingHatOrganizationsParser()
        orgs = [org for org in parser.organizations(stream)]

        # Check parsed organizations
        self.assertEqual(len(orgs), 3)

        # Unknown entry
        org = orgs[0]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Unknown')

        doms = org.domains
        self.assertEqual(len(doms), 0)

        # Bitergia entry
        org = orgs[1]
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
        org = orgs[2]
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

    def test_not_valid_organizations_stream(self):
        """Check whether it prints an error when parsing invalid streams"""

        parser = SortingHatOrganizationsParser()

        with self.assertRaisesRegexp(InvalidFormatError,
                                     ORGS_INVALID_JSON_FORMAT_ERROR):
            s1 = self.read_file('data/sortinghat_orgs_invalid_json.json')
            [org for org in parser.organizations(s1)]

        with self.assertRaisesRegexp(InvalidFormatError,
                                     ORGS_MISSING_KEYS_ERROR):
            s2 = self.read_file('data/sortinghat_orgs_missing_keys.json')
            [org for org in parser.organizations(s2)]

        with self.assertRaisesRegexp(InvalidFormatError,
                                     ORGS_IS_TOP_ERROR):
            s3 = self.read_file('data/sortinghat_orgs_invalid_top.json')
            [org for org in parser.organizations(s3)]

    def test_empty_organizations_stream(self):
        """Check whether it raises an exception when the stream is empty"""

        parser = SortingHatOrganizationsParser()

        with self.assertRaisesRegexp(InvalidFormatError,
                                     ORGS_STREAM_INVALID_ERROR):
            [org for org in parser.organizations("")]

    def test_none_organizations_stream(self):
        """Check whether it raises an exception when the stream is None"""

        parser = SortingHatOrganizationsParser()

        with self.assertRaisesRegexp(InvalidFormatError,
                                     ORGS_STREAM_INVALID_ERROR):
            [org for org in parser.organizations(None)]


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
