#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2018 Bitergia
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

import dateutil

import django.test
import graphene
import graphene.test

from sortinghat.core.models import (Organization,
                                    Domain)
from sortinghat.core.schema import SortingHatQuery


# Test queries
SH_ORGS_QUERY = """{
  organizations {
    name
    domains {
      domain
      isTopDomain
    }
  }
}"""


class TestQuery(SortingHatQuery, graphene.ObjectType):
    pass


schema = graphene.Schema(query=TestQuery)


class TestSQueryOrganizations(django.test.TestCase):
    """Unit tests for organization queries"""

    def test_organizations(self):
        """Check if it returns the registry of organizations"""

        org = Organization.objects.create(name='Example')
        Domain.objects.create(domain='example.com', organization=org)
        Domain.objects.create(domain='example.org', organization=org)
        org = Organization.objects.create(name='Bitergia')
        Domain.objects.create(domain='bitergia.com', organization=org)
        _ = Organization.objects.create(name='LibreSoft')

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_ORGS_QUERY)

        orgs = executed['data']['organizations']
        self.assertEqual(len(orgs), 3)

        org1 = orgs[0]
        self.assertEqual(org1['name'], 'Bitergia')
        self.assertEqual(len(org1['domains']), 1)

        org2 = orgs[1]
        self.assertEqual(org2['name'], 'Example')
        self.assertEqual(len(org2['domains']), 2)

        org3 = orgs[2]
        self.assertEqual(org3['name'], 'LibreSoft')
        self.assertEqual(len(org3['domains']), 0)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_ORGS_QUERY)

        orgs = executed['data']['organizations']
        self.assertListEqual(orgs, [])

