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
                                    Domain,
                                    Country,
                                    UniqueIdentity,
                                    Identity,
                                    Profile,
                                    Enrollment)
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
SH_UIDS_QUERY = """{
  uidentities {
    uuid
    profile {
      name
      email
      gender
      isBot
      country {
        code
        name
      }
    }
    identities {
      id
      name
      email
      username
      source
    }
    enrollments {
      organization {
        name
      }
      start
      end
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


class TestUniqueIdentities(django.test.TestCase):
    """Unit tests for unique identities queries"""

    def test_unique_identities(self):
        """Check if it returns the registry of unique identities"""

        cn = Country.objects.create(code='US',
                                    name='United States of America',
                                    alpha3='USA')

        org_ex = Organization.objects.create(name='Example')
        org_bit = Organization.objects.create(name='Bitergia')

        uid = UniqueIdentity.objects.create(uuid='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        Profile.objects.create(name=None,
                               email='jsmith@example.com',
                               is_bot=True,
                               gender='M',
                               country=cn,
                               uidentity=uid)
        Identity.objects.create(id='A001',
                                name='John Smith',
                                email='jsmith@example.com',
                                username='jsmith',
                                source='scm',
                                uidentity=uid)
        Identity.objects.create(id='A002',
                                name=None,
                                email='jsmith@bitergia.com',
                                username=None,
                                source='scm',
                                uidentity=uid)
        Identity.objects.create(id='A003',
                                name=None,
                                email='jsmith@bitergia.com',
                                username=None,
                                source='mls',
                                uidentity=uid)
        Enrollment.objects.create(uidentity=uid, organization=org_ex)
        Enrollment.objects.create(uidentity=uid, organization=org_bit,
                                  start=datetime.datetime(1999, 1, 1, 0, 0, 0,
                                                          tzinfo=dateutil.tz.tzutc()),
                                  end=datetime.datetime(2000, 1, 1, 0, 0, 0,
                                                        tzinfo=dateutil.tz.tzutc()))

        uid = UniqueIdentity.objects.create(uuid='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               is_bot=False,
                               gender='M',
                               country=None,
                               uidentity=uid)
        Identity.objects.create(id='B001',
                                name='John Doe',
                                email='jdoe@example.com',
                                username='jdoe',
                                source='scm',
                                uidentity=uid)
        Identity.objects.create(id='B002',
                                name=None,
                                email='jdoe@libresoft.es',
                                username=None,
                                source='scm',
                                uidentity=uid)

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_UIDS_QUERY)

        uidentities = executed['data']['uidentities']
        self.assertEqual(len(uidentities), 2)

        # Test John Smith unique identity
        uid = uidentities[0]
        self.assertEqual(uid['uuid'], 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        self.assertEqual(uid['profile']['name'], None)
        self.assertEqual(uid['profile']['email'], 'jsmith@example.com')
        self.assertEqual(uid['profile']['isBot'], True)
        self.assertEqual(uid['profile']['country']['code'], 'US')
        self.assertEqual(uid['profile']['country']['name'], 'United States of America')

        identities = uid['identities']
        identities.sort(key=lambda x: x['id'])
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1['email'], 'jsmith@example.com')

        id2 = identities[1]
        self.assertEqual(id2['email'], 'jsmith@bitergia.com')
        self.assertEqual(id2['source'], 'scm')

        id3 = identities[2]
        self.assertEqual(id3['email'], 'jsmith@bitergia.com')
        self.assertEqual(id3['source'], 'mls')

        enrollments = uid['enrollments']
        enrollments.sort(key=lambda x: x['organization']['name'])
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1['organization']['name'], 'Bitergia')
        self.assertEqual(rol1['start'], '1999-01-01T00:00:00+00:00')
        self.assertEqual(rol1['end'], '2000-01-01T00:00:00+00:00')

        rol2 = enrollments[1]
        self.assertEqual(rol2['organization']['name'], 'Example')
        self.assertEqual(rol2['start'], '1900-01-01T00:00:00+00:00')
        self.assertEqual(rol2['end'], '2100-01-01T00:00:00+00:00')

        # Test John Doe unique identity
        uid = uidentities[1]
        self.assertEqual(uid['uuid'], 'c6d2504fde0e34b78a185c4b709e5442d045451c')

        self.assertEqual(uid['profile']['name'], None)
        self.assertEqual(uid['profile']['email'], None)

        identities = uid['identities']
        identities.sort(key=lambda x: x['id'])
        self.assertEqual(len(identities), 2)

        id1 = identities[0]
        self.assertEqual(id1['email'], 'jdoe@example.com')

        id2 = identities[1]
        self.assertEqual(id2['email'], 'jdoe@libresoft.es')

        enrollments = uid['enrollments']
        self.assertEqual(len(enrollments), 0)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_UIDS_QUERY)

        uids = executed['data']['uidentities']
        self.assertListEqual(uids, [])
