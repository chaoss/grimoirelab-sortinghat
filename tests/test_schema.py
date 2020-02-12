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
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#

import datetime

import dateutil

import django.core.exceptions
import django.test
import graphene
import graphene.test

from dateutil.tz import UTC

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from grimoirelab_toolkit.datetime import datetime_utcnow, str_to_datetime

from sortinghat.core import api
from sortinghat.core import db
from sortinghat.core.log import TransactionsLog
from sortinghat.core.models import (Organization,
                                    Domain,
                                    Country,
                                    UniqueIdentity,
                                    Identity,
                                    Profile,
                                    Enrollment,
                                    Transaction,
                                    Operation)
from sortinghat.core.schema import SortingHatQuery, SortingHatMutation


DUPLICATED_ORG_ERROR = "Organization 'Example' already exists in the registry"
DUPLICATED_DOM_ERROR = "Domain 'example.net' already exists in the registry"
DUPLICATED_UNIQUE_IDENTITY = "UniqueIdentity 'eda9f62ad321b1fbe5f283cc05e2484516203117' already exists in the registry"
DUPLICATED_ENROLLMENT_ERROR = "Enrollment '{}' already exists in the registry"
NAME_EMPTY_ERROR = "'name' cannot be an empty string"
DOMAIN_NAME_EMPTY_ERROR = "'domain_name' cannot be an empty string"
SOURCE_EMPTY_ERROR = "'source' cannot be an empty string"
IDENTITY_EMPTY_DATA_ERROR = 'identity data cannot be empty'
FROM_ID_EMPTY_ERROR = "'from_id' cannot be an empty string"
FROM_UUID_EMPTY_ERROR = "'from_uuid' cannot be an empty string"
FROM_UUIDS_EMPTY_ERROR = "'from_uuids' cannot be an empty list"
TO_UUID_EMPTY_ERROR = "'to_uuid' cannot be an empty string"
FROM_UUID_TO_UUID_EQUAL_ERROR = "'from_uuid' and 'to_uuid' cannot be equal"
UUID_EMPTY_ERROR = "'uuid' cannot be an empty string"
ORG_DOES_NOT_EXIST_ERROR = "Organization matching query does not exist."
DOMAIN_DOES_NOT_EXIST_ERROR = "Domain matching query does not exist."
DOMAIN_NOT_FOUND_ERROR = "example.net not found in the registry"
UID_DOES_NOT_EXIST_ERROR = "FFFFFFFFFFFFFFF not found in the registry"
ORGANIZATION_BITERGIA_DOES_NOT_EXIST_ERROR = "Bitergia not found in the registry"
ORGANIZATION_EXAMPLE_DOES_NOT_EXIST_ERROR = "Example not found in the registry"
ENROLLMENT_DOES_NOT_EXIST_ERROR = "'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3-Example-2050-01-01 00:00:00+00:00-2060-01-01 00:00:00+00:00' not found in the registry"
PAGINATION_NO_RESULTS_ERROR = "That page contains no results"
PAGINATION_PAGE_LESS_THAN_ONE_ERROR = "That page number is less than 1"
PAGINATION_PAGE_SIZE_NEGATIVE_ERROR = "Negative indexing is not supported."
PAGINATION_PAGE_SIZE_ZERO_ERROR = "division by zero"
AUTHENTICATION_ERROR = "You do not have permission to perform this action"


# Test queries
SH_ORGS_QUERY = """{
  organizations {
    entities {
      name
      domains {
        domain
        isTopDomain
      }
    }
  }
}"""
SH_ORGS_QUERY_FILTER = """{
  organizations (
    filters:{
      name:"%s"
    }
  ){
    entities {
      name
      domains {
        domain
        isTopDomain
      }
    }
  }
}"""
SH_ORGS_QUERY_PAGINATION = """{
  organizations (
    page: %d
    pageSize: %d
  ){
    entities {
      name
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_UIDS_QUERY = """{
  uidentities {
    entities {
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
  }
}"""
SH_UIDS_UUID_FILTER = """{
  uidentities(filters: {uuid: "a9b403e150dd4af8953a52a4bb841051e4b705d9"}) {
    entities {
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
  }
}"""
SH_UIDS_UUID_PAGINATION = """{
  uidentities(
    page: %d
    pageSize: %d
  ){
    entities {
      uuid
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}
"""
SH_TRANSACTIONS_QUERY = """{
  transactions {
    entities {
      name
      createdAt
      tuid
      isClosed
      closedAt
    }
  }
}"""
SH_TRANSACTIONS_QUERY_FILTER = """{
  transactions(
    filters: {
      tuid: "%s",
      name: "%s",
      fromDate: "%s"
    }
  ){
    entities {
      name
      createdAt
      tuid
      isClosed
      closedAt
    }
  }
}"""
SH_TRANSACTIONS_QUERY_PAGINATION = """{
  transactions(
    page: %d
    pageSize: %d
  ){
    entities {
      name
      createdAt
      tuid
      isClosed
      closedAt
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_OPERATIONS_QUERY = """{
  operations {
    entities {
      ouid
      opType
      entityType
      target
      timestamp
      args
      trx{
        name
        createdAt
        tuid
      }
    }
  }
}"""
SH_OPERATIONS_QUERY_FILTER = """{
  operations(
    filters:{
      opType:"%s",
      entityType:"%s",
      fromDate:"%s"
    }
  ){
    entities {
      ouid
      opType
      entityType
      target
      timestamp
      args
      trx{
        name
        createdAt
        tuid
      }
    }
  }
}"""
SH_OPERATIONS_QUERY_PAGINATION = """{
  operations(
    page: %d
    pageSize: %d
  ){
    entities{
      ouid
      opType
      entityType
      target
      timestamp
      args
      trx{
        name
        createdAt
        tuid
      }
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_OPERATIONS_QUERY_PAGINATION_NO_PAGE = """{
  operations(
    pageSize: %d
  ){
    entities{
      ouid
      opType
      entityType
      target
      timestamp
      args
      trx{
        name
        createdAt
        tuid
      }
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_OPERATIONS_QUERY_PAGINATION_NO_PAGE_SIZE = """{
  operations(
    page: %d
  ){
    entities{
      ouid
      opType
      entityType
      target
      timestamp
      args
      trx{
        name
        createdAt
        tuid
      }
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""

# API endpoint to obtain a context for executing queries
GRAPHQL_ENDPOINT = '/graphql/'


class TestQuery(SortingHatQuery, graphene.ObjectType):
    pass


class TestQueryPagination(django.test.TestCase):

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        api.add_organization('Example')

        api.add_identity('scm', email='jsmith@example')
        api.update_profile(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                           name='J. Smith', email='jsmith@example',
                           gender='male', gender_acc=75)
        api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2017, 6, 1))

        # Create an additional transaction controlling input values
        self.timestamp = datetime_utcnow()  # This will be used as a filter
        self.trx = Transaction(name='test_trx',
                               tuid='012345abcdef',
                               created_at=datetime_utcnow())
        self.trx.save()

    def test_pagination(self):
        """Check if the expected page and number of results is returned"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (2, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        entities = executed['data']['operations']['entities']
        self.assertEqual(len(entities), 2)

        op1 = entities[0]
        self.assertEqual(op1['opType'], Operation.OpType.ADD.value)
        self.assertEqual(op1['entityType'], 'identity')
        self.assertEqual(op1['target'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        op2 = entities[1]
        self.assertEqual(op2['opType'], Operation.OpType.UPDATE.value)
        self.assertEqual(op2['entityType'], 'profile')
        self.assertEqual(op2['target'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        pag_data = executed['data']['operations']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 2)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 3)
        self.assertTrue(pag_data['hasNext'])
        self.assertTrue(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 3)
        self.assertEqual(pag_data['endIndex'], 4)
        self.assertEqual(pag_data['totalResults'], 5)

    def test_page_not_set(self):
        """Check if returns the first page when `page` is not set"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION_NO_PAGE % 2
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        entities = executed['data']['operations']['entities']
        self.assertEqual(len(entities), 2)

        pag_data = executed['data']['operations']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 3)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 5)

    def test_page_exceeded(self):
        """Check if it fails when `page` is greater than the number of pages"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (30, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, PAGINATION_NO_RESULTS_ERROR)

    def test_page_negative(self):
        """Check if it fails when `page` is a negative number"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (-1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, PAGINATION_PAGE_LESS_THAN_ONE_ERROR)

    def test_page_zero(self):
        """Check if it fails when `page` is set to `0`"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (0, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, PAGINATION_PAGE_LESS_THAN_ONE_ERROR)

    def test_page_size_not_set(self):
        """Check if it takes the default value from settings when `pageSize` is not set"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION_NO_PAGE_SIZE % 1
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        pag_data = executed['data']['operations']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], settings.DEFAULT_GRAPHQL_PAGE_SIZE)
        self.assertEqual(pag_data['totalResults'], 5)

    def test_page_size_exceeded(self):
        """Check if returns all the elements when `pageSize` is greater than number of results"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (1, 30)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        pag_data = executed['data']['operations']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 30)
        self.assertEqual(pag_data['numPages'], 1)
        self.assertFalse(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 5)
        self.assertEqual(pag_data['totalResults'], 5)

    def test_page_size_negative(self):
        """Check if it fails when `pageSize` is a negative number"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (1, -2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, PAGINATION_PAGE_SIZE_NEGATIVE_ERROR)

    def test_page_size_zero(self):
        """Check if it fails when `pageSize` is set to `0`"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (1, 0)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, PAGINATION_PAGE_SIZE_ZERO_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        test_query = SH_OPERATIONS_QUERY_PAGINATION % (2, 2)
        executed = client.execute(test_query,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestMutations(SortingHatMutation):
    pass


schema = graphene.Schema(query=TestQuery,
                         mutation=TestMutations)


class TestQueryOrganizations(django.test.TestCase):
    """Unit tests for organization queries"""

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

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
        executed = client.execute(SH_ORGS_QUERY,
                                  context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
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
        executed = client.execute(SH_ORGS_QUERY,
                                  context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
        self.assertListEqual(orgs, [])

    def test_filter_registry(self):
        """Check whether it returns the organization searched when using name filter"""

        org1 = Organization.objects.create(name='Example')
        org2 = Organization.objects.create(name='Bitergia')
        org3 = Organization.objects.create(name='LibreSoft')

        client = graphene.test.Client(schema)
        test_query = SH_ORGS_QUERY_FILTER % 'Bitergia'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
        self.assertEqual(len(orgs), 1)

        # As organizations are sorted by name, the first one will be org2
        org = orgs[0]
        self.assertEqual(org['name'], org2.name)

    def test_filter_non_exist_registry(self):
        """Check whether it returns an empty list when searched with a non existing organization"""

        org1 = Organization.objects.create(name='Example')
        org2 = Organization.objects.create(name='Bitergia')
        org3 = Organization.objects.create(name='LibreSoft')

        client = graphene.test.Client(schema)
        test_query = SH_ORGS_QUERY_FILTER % 'Test'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
        self.assertListEqual(orgs, [])

    def test_pagination(self):
        """Check whether it returns the organizations searched when using pagination"""

        org1 = Organization.objects.create(name='Example')
        org2 = Organization.objects.create(name='Bitergia')
        org3 = Organization.objects.create(name='LibreSoft')

        client = graphene.test.Client(schema)
        test_query = SH_ORGS_QUERY_PAGINATION % (1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
        self.assertEqual(len(orgs), 2)

        # As organizations are sorted by name, the first two will be org2 and org1
        org = orgs[0]
        self.assertEqual(org['name'], org2.name)

        org = orgs[1]
        self.assertEqual(org['name'], org1.name)

        pag_data = executed['data']['organizations']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 2)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 3)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_ORGS_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestUniqueIdentities(django.test.TestCase):
    """Unit tests for unique identities queries"""

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

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
        executed = client.execute(SH_UIDS_QUERY,
                                  context_value=self.context_value)

        uidentities = executed['data']['uidentities']['entities']
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
        executed = client.execute(SH_UIDS_QUERY,
                                  context_value=self.context_value)

        uids = executed['data']['uidentities']['entities']
        self.assertListEqual(uids, [])

    def test_filter_registry(self):
        """Check whether it returns the uuid searched when using uuid filter"""

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
        executed = client.execute(SH_UIDS_UUID_FILTER,
                                  context_value=self.context_value)

        uidentities = executed['data']['uidentities']['entities']
        self.assertEqual(len(uidentities), 1)

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

    def test_filter_non_exist_registry(self):
        """Check whether it returns an empty list when searched with a non existing uuid"""

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

        client = graphene.test.Client(schema)
        executed = client.execute(SH_UIDS_UUID_FILTER,
                                  context_value=self.context_value)

        uids = executed['data']['uidentities']['entities']
        self.assertListEqual(uids, [])

    def test_pagination(self):
        """Check whether it returns the unique identities searched when using pagination"""

        uid1 = UniqueIdentity.objects.create(uuid='185c4b709e5446d250b4fde0e34b78a2b4fde0e3')
        uid2 = UniqueIdentity.objects.create(uuid='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        uid3 = UniqueIdentity.objects.create(uuid='c6d2504fde0e34b78a185c4b709e5442d045451c')

        client = graphene.test.Client(schema)
        test_query = SH_UIDS_UUID_PAGINATION % (1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        uids = executed['data']['uidentities']['entities']
        self.assertEqual(len(uids), 2)

        uid = uids[0]
        self.assertEqual(uid['uuid'], uid1.uuid)

        uid = uids[1]
        self.assertEqual(uid['uuid'], uid2.uuid)

        pag_data = executed['data']['uidentities']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 2)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 3)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_UIDS_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestQueryTransactions(django.test.TestCase):
    """Unit tests for transaction queries"""

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        api.add_organization('Example')

        api.add_identity('scm', email='jsmith@example')
        api.update_profile(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                           name='J. Smith', email='jsmith@example',
                           gender='male', gender_acc=75)
        api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2017, 6, 1))

        # Create an additional transaction controlling input values
        self.timestamp = datetime_utcnow()  # This will be used as a filter
        self.trx = Transaction(name='test_trx',
                               tuid='012345abcdef',
                               created_at=datetime_utcnow())
        self.trx.save()

    def test_transaction(self):
        """Check if it returns the registry of transactions"""

        timestamp = datetime_utcnow()
        client = graphene.test.Client(schema)
        executed = client.execute(SH_TRANSACTIONS_QUERY,
                                  context_value=self.context_value)

        transactions = executed['data']['transactions']['entities']
        self.assertEqual(len(transactions), 5)

        trx = transactions[0]
        self.assertEqual(trx['name'], 'add_organization')
        self.assertLess(str_to_datetime(trx['createdAt']), timestamp)
        self.assertIsInstance(trx['tuid'], str)
        self.assertLess(str_to_datetime(trx['closedAt']), timestamp)
        self.assertTrue(trx['isClosed'])

        trx = transactions[1]
        self.assertEqual(trx['name'], 'add_identity')
        self.assertLess(str_to_datetime(trx['createdAt']), timestamp)
        self.assertIsInstance(trx['tuid'], str)
        self.assertLess(str_to_datetime(trx['closedAt']), timestamp)
        self.assertTrue(trx['isClosed'])

        trx = transactions[2]
        self.assertEqual(trx['name'], 'update_profile')
        self.assertLess(str_to_datetime(trx['createdAt']), timestamp)
        self.assertIsInstance(trx['tuid'], str)
        self.assertLess(str_to_datetime(trx['closedAt']), timestamp)
        self.assertTrue(trx['isClosed'])

        trx = transactions[3]
        self.assertEqual(trx['name'], 'enroll')
        self.assertLess(str_to_datetime(trx['createdAt']), timestamp)
        self.assertIsInstance(trx['tuid'], str)
        self.assertLess(str_to_datetime(trx['closedAt']), timestamp)
        self.assertTrue(trx['isClosed'])

        trx = transactions[4]
        self.assertEqual(trx['name'], self.trx.name)
        self.assertEqual(str_to_datetime(trx['createdAt']), self.trx.created_at)
        self.assertEqual(trx['tuid'], self.trx.tuid)
        self.assertIsNone(trx['closedAt'])
        self.assertFalse(trx['isClosed'])

    def test_filter_registry(self):
        """Check whether it returns the transaction searched when using filters"""

        client = graphene.test.Client(schema)
        test_query = SH_TRANSACTIONS_QUERY_FILTER % ('012345abcdef', 'test_trx',
                                                     self.timestamp.isoformat())
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        transactions = executed['data']['transactions']['entities']
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertEqual(trx['name'], self.trx.name)
        self.assertEqual(str_to_datetime(trx['createdAt']), self.trx.created_at)
        self.assertEqual(trx['tuid'], self.trx.tuid)
        self.assertIsNone(trx['closedAt'])
        self.assertFalse(trx['isClosed'])

    def test_filter_non_existing_registry(self):
        """Check whether it returns an empty list when searched with a non existing transaction"""

        client = graphene.test.Client(schema)
        test_query = SH_TRANSACTIONS_QUERY_FILTER % ('012345abcdefg', 'test_trx',
                                                     self.timestamp.isoformat())
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        transactions = executed['data']['transactions']['entities']
        self.assertListEqual(transactions, [])

    def test_pagination(self):
        """Check whether it returns the transactions searched when using pagination"""

        timestamp = datetime_utcnow()

        client = graphene.test.Client(schema)
        test_query = SH_TRANSACTIONS_QUERY_PAGINATION % (1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        transactions = executed['data']['transactions']['entities']
        self.assertEqual(len(transactions), 2)

        trx = transactions[0]
        self.assertEqual(trx['name'], 'add_organization')
        self.assertLess(str_to_datetime(trx['createdAt']), timestamp)
        self.assertIsInstance(trx['tuid'], str)
        self.assertLess(str_to_datetime(trx['closedAt']), timestamp)
        self.assertTrue(trx['isClosed'])

        trx = transactions[1]
        self.assertEqual(trx['name'], 'add_identity')
        self.assertLess(str_to_datetime(trx['createdAt']), timestamp)
        self.assertIsInstance(trx['tuid'], str)
        self.assertLess(str_to_datetime(trx['closedAt']), timestamp)
        self.assertTrue(trx['isClosed'])

        pag_data = executed['data']['transactions']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 3)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 5)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        # Delete Transactions created in `setUp` method
        Transaction.objects.all().delete()
        transactions = Transaction.objects.all()

        self.assertEqual(len(transactions), 0)

        # Test query
        client = graphene.test.Client(schema)
        executed = client.execute(SH_TRANSACTIONS_QUERY,
                                  context_value=self.context_value)

        q_transactions = executed['data']['transactions']['entities']
        self.assertListEqual(q_transactions, [])

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_TRANSACTIONS_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestQueryOperations(django.test.TestCase):
    """Unit tests for operation queries"""

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        api.add_organization('Example')

        # Create an additional operation controlling input values
        trx = Transaction(name='test_trx',
                          tuid='012345abcdef',
                          created_at=datetime_utcnow())
        trx.save()

        self.trxl = TransactionsLog(trx)
        self.timestamp = datetime_utcnow()  # This will be used as a filter
        self.trxl.log_operation(op_type=Operation.OpType.UPDATE,
                                entity_type='test_entity',
                                timestamp=datetime_utcnow(),
                                args={'test_arg': 'test_value'},
                                target='test_target')
        self.trxl.close()

    def test_operation(self):
        """Check if it returns the registry of operations"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_OPERATIONS_QUERY,
                                  context_value=self.context_value)

        operations = executed['data']['operations']['entities']
        self.assertEqual(len(operations), 2)

        op1 = operations[0]
        self.assertEqual(op1['opType'], Operation.OpType.ADD.value)
        self.assertEqual(op1['entityType'], 'organization')
        self.assertLess(str_to_datetime(op1['timestamp']), self.timestamp)
        self.assertEqual(op1['args'], {'name': 'Example'})

        # Check if the query returns the associated transaction
        trx1 = op1['trx']
        self.assertEqual(trx1['name'], 'add_organization')
        self.assertIsInstance(trx1['tuid'], str)
        self.assertLess(str_to_datetime(trx1['createdAt']), self.timestamp)

        op2 = operations[1]
        self.assertEqual(op2['opType'], Operation.OpType.UPDATE.value)
        self.assertEqual(op2['entityType'], 'test_entity')
        self.assertGreater(str_to_datetime(op2['timestamp']), self.timestamp)
        self.assertEqual(op2['args'], {'test_arg': 'test_value'})

        # Check if the query returns the associated transaction
        trx2 = op2['trx']
        self.assertEqual(trx2['name'], self.trxl.trx.name)
        self.assertEqual(trx2['tuid'], self.trxl.trx.tuid)
        self.assertEqual(str_to_datetime(trx2['createdAt']), self.trxl.trx.created_at)

    def test_filter_registry(self):
        """Check whether it returns the operation searched when using filters"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_FILTER % ('UPDATE', 'test_entity',
                                                   self.timestamp.isoformat())
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        operations = executed['data']['operations']['entities']
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertEqual(op1['opType'], Operation.OpType.UPDATE.value)
        self.assertEqual(op1['entityType'], 'test_entity')
        self.assertGreater(str_to_datetime(op1['timestamp']), self.timestamp)
        self.assertEqual(op1['args'], {'test_arg': 'test_value'})

        # Check if the query returns the associated transaction
        trx1 = op1['trx']
        self.assertEqual(trx1['name'], self.trxl.trx.name)
        self.assertEqual(trx1['tuid'], self.trxl.trx.tuid)
        self.assertEqual(str_to_datetime(trx1['createdAt']), self.trxl.trx.created_at)

    def test_filter_non_existing_registry(self):
        """Check whether it returns an empty list when searched with a non existing operation"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_FILTER % ('DELETE', 'test_entity',
                                                   self.timestamp.isoformat())
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        operations = executed['data']['operations']['entities']
        self.assertListEqual(operations, [])

    def test_pagination(self):
        """Check whether it returns the operations searched when using pagination"""

        # Add an additional operation by calling an API method
        api.add_domain(organization='Example', domain_name='example.com')

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        operations = executed['data']['operations']['entities']
        self.assertEqual(len(operations), 2)

        op1 = operations[0]
        self.assertEqual(op1['opType'], Operation.OpType.ADD.value)
        self.assertEqual(op1['entityType'], 'organization')
        self.assertEqual(op1['target'], 'Example')
        self.assertLess(str_to_datetime(op1['timestamp']), self.timestamp)
        self.assertEqual(op1['args'], {'name': 'Example'})

        op2 = operations[1]
        self.assertEqual(op2['opType'], Operation.OpType.UPDATE.value)
        self.assertEqual(op2['entityType'], 'test_entity')
        self.assertGreater(str_to_datetime(op2['timestamp']), self.timestamp)
        self.assertEqual(op2['args'], {'test_arg': 'test_value'})

        pag_data = executed['data']['operations']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 2)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 3)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        # Delete Operations created in `setUp` method
        Operation.objects.all().delete()
        operations = Operation.objects.all()

        self.assertEqual(len(operations), 0)

        # Test query
        client = graphene.test.Client(schema)
        executed = client.execute(SH_OPERATIONS_QUERY,
                                  context_value=self.context_value)

        q_operations = executed['data']['operations']['entities']
        self.assertListEqual(q_operations, [])

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_OPERATIONS_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestAddOrganizationMutation(django.test.TestCase):
    """Unit tests for mutation to add organizations"""

    SH_ADD_ORG = """
      mutation addOrg {
        addOrganization(name: "Example") {
          organization {
            name
            domains {
              domain
              isTopDomain
            }
          }
        }
      }
    """

    SH_ADD_ORG_NAME_EMPTY = """
      mutation addOrg {
        addOrganization(name: "") {
          organization {
            name
            domains {
              domain
              isTopDomain
            }
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_add_organization(self):
        """Check if a new organization is added"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG,
                                  context_value=self.context_value)

        # Check result
        org = executed['data']['addOrganization']['organization']
        self.assertEqual(org['name'], 'Example')
        self.assertListEqual(org['domains'], [])

        # Check database
        org = Organization.objects.get(name='Example')
        self.assertEqual(org.name, 'Example')

    def test_name_empty(self):
        """Check whether organizations with empty names cannot be added"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG_NAME_EMPTY,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, NAME_EMPTY_ERROR)

        # Check database
        orgs = Organization.objects.all()
        self.assertEqual(len(orgs), 0)

    def test_integrity_error(self):
        """Check whether organizations with the same name cannot be inserted"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG,
                                  context_value=self.context_value)

        # Check database
        org = Organization.objects.get(name='Example')
        self.assertEqual(org.name, 'Example')

        # Try to insert it twice
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_ORG_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_ADD_ORG,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestDeleteOrganizationMutation(django.test.TestCase):
    """Unit tests for mutation to delete organizations"""

    SH_DELETE_ORG = """
      mutation delOrg {
        deleteOrganization(name: "Example") {
          organization {
            name
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_delete_organization(self):
        """Check whether it deletes an organization"""

        org_ex = Organization.objects.create(name='Example')
        Domain.objects.create(domain='example.org',
                              organization=org_ex)
        org_bit = Organization.objects.create(name='Bitergia')

        jsmith = UniqueIdentity.objects.create(uuid='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               uidentity=jsmith)
        Enrollment.objects.create(uidentity=jsmith, organization=org_ex)

        jdoe = UniqueIdentity.objects.create(uuid='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               uidentity=jdoe)
        Enrollment.objects.create(uidentity=jdoe, organization=org_ex)
        Enrollment.objects.create(uidentity=jdoe, organization=org_bit)

        # Delete organization
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_ORG,
                                  context_value=self.context_value)

        # Check result
        org = executed['data']['deleteOrganization']['organization']
        self.assertEqual(org['name'], 'Example')

        # Tests
        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            Organization.objects.get(name='Example')

        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            Domain.objects.get(domain='example.org')

        enrollments = Enrollment.objects.filter(organization__name='Example')
        self.assertEqual(len(enrollments), 0)

        enrollments = Enrollment.objects.filter(organization__name='Bitergia')
        self.assertEqual(len(enrollments), 1)

    def test_not_found_organization(self):
        """Check if it returns an error when an organization does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_ORG,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_EXAMPLE_DOES_NOT_EXIST_ERROR)

        # It should not remove anything
        Organization.objects.create(name='Bitergia')

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_EXAMPLE_DOES_NOT_EXIST_ERROR)

        orgs = Organization.objects.all()
        self.assertEqual(len(orgs), 1)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_DELETE_ORG,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestAddDomainMutation(django.test.TestCase):
    """Unit tests for mutation to add domains"""

    SH_ADD_DOMAIN = """
      mutation addDom {
        addDomain(organization: "Example",
                  domain: "example.net"
                  isTopDomain: true)
        {
          domain {
            domain
            isTopDomain
            organization {
              name
            }
          }
        }
      }
    """

    SH_ADD_DOMAIN_EMPTY = """
      mutation addDom {
        addDomain(organization: "Example",
                  domain: ""
                  isTopDomain: true)
        {
          domain {
            domain
            isTopDomain
            organization {
              name
            }
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_add_domain(self):
        """Check if a new domain is added"""

        Organization.objects.create(name='Example')

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_DOMAIN,
                                  context_value=self.context_value)

        # Check result
        dom = executed['data']['addDomain']['domain']
        self.assertEqual(dom['domain'], 'example.net')
        self.assertEqual(dom['isTopDomain'], True)
        self.assertEqual(dom['organization']['name'], 'Example')

        # Check database
        org = Organization.objects.get(name='Example')
        domains = org.domains.all()
        self.assertEqual(len(domains), 1)

        dom = domains[0]
        self.assertEqual(dom.domain, 'example.net')
        self.assertEqual(dom.is_top_domain, True)

    def test_domain_empty(self):
        """Check whether domains with empty names cannot be added"""

        Organization.objects.create(name='Example')

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_DOMAIN_EMPTY,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DOMAIN_NAME_EMPTY_ERROR)

        # Check database
        domains = Domain.objects.all()
        self.assertEqual(len(domains), 0)

    def test_integrity_error(self):
        """Check whether domains with the same domain name cannot be inserted"""

        Organization.objects.create(name='Example')

        client = graphene.test.Client(schema)
        client.execute(self.SH_ADD_DOMAIN, context_value=self.context_value)

        # Check database
        dom = Domain.objects.get(domain='example.net')
        self.assertEqual(dom.domain, 'example.net')

        # Try to insert it twice
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_DOMAIN,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_DOM_ERROR)

    def test_not_found_organization(self):
        """Check if it returns an error when an organization does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_DOMAIN,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_EXAMPLE_DOES_NOT_EXIST_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_ADD_DOMAIN,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestDeleteDomainMutation(django.test.TestCase):
    """Unit tests for mutation to delete domains"""

    SH_DELETE_DOMAIN = """
      mutation delDom {
        deleteDomain(domain: "example.net") {
          domain {
            domain
            isTopDomain
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_delete_domain(self):
        """Check whether it deletes a domain"""

        org = Organization.objects.create(name='Example')
        Domain.objects.create(domain='example.net', organization=org)
        Domain.objects.create(domain='example.com', organization=org)

        # Delete organization
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_DOMAIN,
                                  context_value=self.context_value)

        # Check result
        dom = executed['data']['deleteDomain']['domain']
        self.assertEqual(dom['domain'], 'example.net')

        # Tests
        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            Domain.objects.get(domain='example.net')

        domains = Domain.objects.all()
        self.assertEqual(len(domains), 1)

    def test_not_found_domain(self):
        """Check if it returns an error when a domain does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_DOMAIN,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DOMAIN_NOT_FOUND_ERROR)

        # It should not remove anything
        org = Organization.objects.create(name='Bitergia')
        Domain.objects.create(domain='example.com', organization=org)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DOMAIN_NOT_FOUND_ERROR)

        domains = Domain.objects.all()
        self.assertEqual(len(domains), 1)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_DELETE_DOMAIN,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestAddIdentityMutation(django.test.TestCase):
    """Unit tests for mutation to add identities"""

    SH_ADD_IDENTITY = """
      mutation addId(
        $source: String,
        $name: String,
        $email: String,
        $username: String
        $uuid: String) {
          addIdentity(
            source: $source
            name: $name
            email: $email
            username: $username
            uuid: $uuid) {
              uuid
              uidentity {
                uuid
                identities {
                  id
                  name
                  email
                  username
                  source
                }
              }
          }
        }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_add_new_identities(self):
        """Check if everything goes OK when adding new identities"""

        client = graphene.test.Client(schema)

        params = {
            'source': 'scm',
            'name': 'Jane Roe',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results
        uidentity = executed['data']['addIdentity']['uidentity']
        self.assertEqual(uidentity['uuid'], 'eda9f62ad321b1fbe5f283cc05e2484516203117')

        identities = uidentity['identities']
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity['id'], 'eda9f62ad321b1fbe5f283cc05e2484516203117')
        self.assertEqual(identity['source'], 'scm')
        self.assertEqual(identity['name'], 'Jane Roe')
        self.assertEqual(identity['email'], 'jroe@example.com')
        self.assertEqual(identity['username'], 'jrae')

        uuid = executed['data']['addIdentity']['uuid']
        self.assertEqual(uuid, 'eda9f62ad321b1fbe5f283cc05e2484516203117')

        # Check database
        uidentity = UniqueIdentity.objects.get(uuid='eda9f62ad321b1fbe5f283cc05e2484516203117')
        self.assertEqual(uidentity.uuid, identity['id'])

        identities = Identity.objects.filter(id=identity['id'])
        self.assertEqual(len(identities), 1)

        id0 = identities[0]
        self.assertEqual(id0.source, identity['source'])
        self.assertEqual(id0.name, identity['name'])
        self.assertEqual(id0.email, identity['email'])
        self.assertEqual(id0.username, identity['username'])

    def test_add_existing_uuid(self):
        """Check it it adds an identity to an existing unique identity"""

        uidentity = UniqueIdentity.objects.create(uuid='eda9f62ad321b1fbe5f283cc05e2484516203117')
        Identity.objects.create(id='eda9f62ad321b1fbe5f283cc05e2484516203117', source='scm',
                                name='Jane Roe', email='jroe@example.com', username='jrae',
                                uidentity=uidentity)

        client = graphene.test.Client(schema)

        params = {
            'source': 'mls',
            'name': 'Jane Roe',
            'email': 'jroe@example.com',
            'username': 'jrae',
            'uuid': 'eda9f62ad321b1fbe5f283cc05e2484516203117'
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results
        uidentity = executed['data']['addIdentity']['uidentity']
        self.assertEqual(uidentity['uuid'], 'eda9f62ad321b1fbe5f283cc05e2484516203117')

        identities = uidentity['identities']
        self.assertEqual(len(identities), 2)

        identity = identities[0]
        self.assertEqual(identity['id'], '55d88f85a41f3a9afa4dc9d4dfb6009c62f42fe3')
        self.assertEqual(identity['source'], 'mls')
        self.assertEqual(identity['name'], 'Jane Roe')
        self.assertEqual(identity['email'], 'jroe@example.com')
        self.assertEqual(identity['username'], 'jrae')

        uuid = executed['data']['addIdentity']['uuid']
        self.assertEqual(uuid, '55d88f85a41f3a9afa4dc9d4dfb6009c62f42fe3')

        # Check database
        identities = Identity.objects.filter(uidentity__uuid='eda9f62ad321b1fbe5f283cc05e2484516203117')
        self.assertEqual(len(identities), 2)

    def test_non_existing_uuid(self):
        """Check if it fails adding identities to unique identities that do not exist"""

        client = graphene.test.Client(schema)

        params = {
            'source': 'mls',
            'email': 'jroe@example.com',
            'uuid': 'FFFFFFFFFFFFFFF'
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UID_DOES_NOT_EXIST_ERROR)

    def test_integrity_error(self):
        """Check if it fails adding an identity that already exists"""

        uidentity = UniqueIdentity.objects.create(uuid='eda9f62ad321b1fbe5f283cc05e2484516203117')
        Identity.objects.create(id='eda9f62ad321b1fbe5f283cc05e2484516203117', source='scm',
                                name='Jane Roe', email='jroe@example.com', username='jrae',
                                uidentity=uidentity)

        client = graphene.test.Client(schema)

        # Tests
        params = {
            'source': 'scm',
            'name': 'Jane Roe',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_UNIQUE_IDENTITY)

        # Different case letters, but same identity
        params = {
            'source': 'scm',
            'name': 'jane roe',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_UNIQUE_IDENTITY)

        # Different accents, but same identity
        params = {
            'source': 'scm',
            'name': 'Jane Röe',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_UNIQUE_IDENTITY)

    def test_empty_source(self):
        """Check whether new identities cannot be added when giving an empty source"""

        client = graphene.test.Client(schema)

        params = {'source': ''}
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, SOURCE_EMPTY_ERROR)

    def test_none_or_empty_data(self):
        """Check whether new identities cannot be added when identity data is None or empty"""

        client = graphene.test.Client(schema)

        # Tests
        params = {
            'source': 'scm',
            'name': '',
            'email': None,
            'username': None,
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, IDENTITY_EMPTY_DATA_ERROR)

        params = {
            'source': 'scm',
            'name': '',
            'email': '',
            'username': '',
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, IDENTITY_EMPTY_DATA_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'source': 'scm',
            'name': 'Jane Roe',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestDeleteIdentityMutation(django.test.TestCase):
    """Unit tests for mutation to delete identities"""

    SH_DELETE_IDENTITY = """
      mutation delId($uuid: String) {
        deleteIdentity(uuid: $uuid) {
          uuid
          uidentity {
            uuid
            identities {
              id
              name
              email
              username
              source
            }
          }
        }
      }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        # Transaction
        self.trxl = TransactionsLog.open(name='delete_identity')

        # Organizations
        example_org = db.add_organization(self.trxl, 'Example')
        bitergia_org = db.add_organization(self.trxl, 'Bitergia')
        libresoft_org = db.add_organization(self.trxl, 'LibreSoft')

        # Identities
        jsmith = api.add_identity('scm', email='jsmith@example')
        api.add_identity('scm',
                         name='John Smith',
                         email='jsmith@example',
                         uuid=jsmith.id)
        Enrollment.objects.create(uidentity=jsmith.uidentity,
                                  organization=example_org)
        Enrollment.objects.create(uidentity=jsmith.uidentity,
                                  organization=bitergia_org)

        jdoe = api.add_identity('scm', email='jdoe@example')
        Enrollment.objects.create(uidentity=jdoe.uidentity,
                                  organization=example_org)

        jrae = api.add_identity('scm',
                                name='Jane Rae',
                                email='jrae@example')
        Enrollment.objects.create(uidentity=jrae.uidentity,
                                  organization=libresoft_org)

    def test_delete_identity(self):
        """Check if everything goes OK when deleting identities"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': '1387b129ab751a3657312c09759caa41dfd8d07d',
        }
        executed = client.execute(self.SH_DELETE_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, only one identity remains
        uidentity = executed['data']['deleteIdentity']['uidentity']
        self.assertEqual(uidentity['uuid'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(len(uidentity['identities']), 1)

        identity = uidentity['identities'][0]
        self.assertEqual(identity['source'], 'scm')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith@example')
        self.assertEqual(identity['username'], None)
        self.assertEqual(identity['id'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        uuid = executed['data']['deleteIdentity']['uuid']
        self.assertEqual(uuid, '1387b129ab751a3657312c09759caa41dfd8d07d')

        # Check database
        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            uidentity = UniqueIdentity.objects.get(uuid='eda9f62ad321b1fbe5f283cc05e2484516203117')
            self.assertEqual(uidentity.uuid, identity['id'])

        identities = Identity.objects.filter(id=identity['id'])
        self.assertEqual(len(identities), 1)

        id0 = identities[0]
        self.assertEqual(id0.source, identity['source'])
        self.assertEqual(id0.name, identity['name'])
        self.assertEqual(id0.email, identity['email'])
        self.assertEqual(id0.username, identity['username'])

    def test_delete_unique_identity(self):
        """Check if everything goes OK when deleting unique identities"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
        }
        executed = client.execute(self.SH_DELETE_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results
        uidentity = executed['data']['deleteIdentity']['uidentity']
        self.assertEqual(uidentity, None)

        uuid = executed['data']['deleteIdentity']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            UniqueIdentity.objects.get(uuid='eda9f62ad321b1fbe5f283cc05e2484516203117')

    def test_non_existing_uuid(self):
        """Check if it fails removing identities or unique identities that do not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'FFFFFFFFFFFFFFF'
        }
        executed = client.execute(self.SH_DELETE_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UID_DOES_NOT_EXIST_ERROR)

    def test_empty_uuid(self):
        """Check whether identities cannot be removed when giving an empty UUID"""

        client = graphene.test.Client(schema)

        params = {'uuid': ''}
        executed = client.execute(self.SH_DELETE_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_EMPTY_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'uuid': '1387b129ab751a3657312c09759caa41dfd8d07d',
        }
        executed = client.execute(self.SH_DELETE_IDENTITY,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestUpdateProfileMutation(django.test.TestCase):
    """Unit tests for mutation to update profiles"""

    SH_UPDATE_PROFILE = """
      mutation editProfile($uuid: String, $data: ProfileInputType) {
        updateProfile(uuid: $uuid, data: $data) {
          uuid
          uidentity {
            uuid
            profile {
              name
              email
              gender
              genderAcc
              isBot
              country {
                name
                code
              }
            }
          }
        }
      }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')
        jsmith = api.add_identity('scm', email='jsmith@example')
        api.update_profile(jsmith.id, name='Smith J,', email='jsmith@example.com')

    def test_update_profile(self):
        """Check if it updates a profile"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'data': {
                'name': 'John Smith',
                'email': 'jsmith@example.net',
                'isBot': True,
                'countryCode': 'US',
                'gender': 'male',
                'genderAcc': 89
            }
        }
        executed = client.execute(self.SH_UPDATE_PROFILE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, profile was updated
        profile = executed['data']['updateProfile']['uidentity']['profile']
        self.assertEqual(profile['name'], 'John Smith')
        self.assertEqual(profile['email'], 'jsmith@example.net')
        self.assertEqual(profile['isBot'], True)
        self.assertEqual(profile['gender'], 'male')
        self.assertEqual(profile['genderAcc'], 89)
        self.assertEqual(profile['country']['code'], 'US')
        self.assertEqual(profile['country']['name'], 'United States of America')

        uuid = executed['data']['updateProfile']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        uidentity = UniqueIdentity.objects.get(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        profile = uidentity.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@example.net')
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 89)
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.name, 'United States of America')

    def test_non_existing_uuid(self):
        """Check if it fails updating profiles of unique identities that do not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'FFFFFFFFFFFFFFF',
            'data': {
                'name': 'John Smith',
            }
        }
        executed = client.execute(self.SH_UPDATE_PROFILE,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UID_DOES_NOT_EXIST_ERROR)

    def test_name_email_empty(self):
        """Check if name and email are set to None when an empty string is given"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'data': {
                'name': '',
                'email': ''
            }
        }
        executed = client.execute(self.SH_UPDATE_PROFILE,
                                  context_value=self.context_value,
                                  variables=params)

        profile = executed['data']['updateProfile']['uidentity']['profile']
        self.assertEqual(profile['name'], None)
        self.assertEqual(profile['email'], None)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'data': {
                'name': 'John Smith',
                'email': 'jsmith@example.net',
                'isBot': True,
                'countryCode': 'US',
                'gender': 'male',
                'genderAcc': 89
            }
        }
        executed = client.execute(self.SH_UPDATE_PROFILE,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestMoveIdentityMutation(django.test.TestCase):
    """Unit tests for mutation to move identities"""

    SH_MOVE = """
      mutation moveId($fromID: String, $toUUID: String) {
        moveIdentity(fromId: $fromID, toUuid: $toUUID) {
          uuid
          uidentity {
            uuid
            identities {
              id
              name
              email
              username
              source
            }
          }
        }
      }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        jsmith = api.add_identity('scm', email='jsmith@example.com')
        api.add_identity('scm',
                         name='John Smith',
                         email='jsmith@example.com',
                         uuid=jsmith.id)
        api.add_identity('scm', email='jdoe@example.com')

    def test_move_identity(self):
        """Test whether an identity is moved to a unique identity"""

        client = graphene.test.Client(schema)

        params = {
            'fromID': '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331',
            'toUUID': '03877f31261a6d1a1b3971d240e628259364b8ac'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, identity was moved
        identities = executed['data']['moveIdentity']['uidentity']['identities']

        self.assertEqual(len(identities), 2)

        identity = identities[0]
        self.assertEqual(identity['id'], '03877f31261a6d1a1b3971d240e628259364b8ac')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jdoe@example.com')

        identity = identities[1]
        self.assertEqual(identity['id'], '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity['name'], 'John Smith')
        self.assertEqual(identity['email'], 'jsmith@example.com')

        uuid = executed['data']['moveIdentity']['uuid']
        self.assertEqual(uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')

        # Check database objects
        uidentity_db = UniqueIdentity.objects.get(uuid='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '334da68fcd3da4e799791f73dfada2afb22648c6')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jsmith@example.com')

        uidentity_db = UniqueIdentity.objects.get(uuid='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 2)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '03877f31261a6d1a1b3971d240e628259364b8ac')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jdoe@example.com')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.id, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity_db.name, 'John Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.com')

    def test_equal_related_unique_identity(self):
        """Check if identities are not moved when 'to_uuid' is the unique identity related to 'from_id'"""

        client = graphene.test.Client(schema)

        params = {
            'fromID': '03877f31261a6d1a1b3971d240e628259364b8ac',
            'toUUID': '03877f31261a6d1a1b3971d240e628259364b8ac'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, identity was not moved
        identities = executed['data']['moveIdentity']['uidentity']['identities']

        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity['id'], '03877f31261a6d1a1b3971d240e628259364b8ac')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jdoe@example.com')

        uuid = executed['data']['moveIdentity']['uuid']
        self.assertEqual(uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')

        # Check database objects
        uidentity_db = UniqueIdentity.objects.get(uuid='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 2)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '334da68fcd3da4e799791f73dfada2afb22648c6')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.id, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')

        uidentity_db = UniqueIdentity.objects.get(uuid='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '03877f31261a6d1a1b3971d240e628259364b8ac')

    def test_create_new_unique_identity(self):
        """Check if a new unique identity is created when 'from_id' has the same value of 'to_uuid'"""

        client = graphene.test.Client(schema)

        params = {
            'fromID': '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331',
            'toUUID': '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        # This will create a new unique identity,
        # moving the identity to this new unique identity
        identities = executed['data']['moveIdentity']['uidentity']['identities']

        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity['id'], '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity['name'], 'John Smith')
        self.assertEqual(identity['email'], 'jsmith@example.com')

        uuid = executed['data']['moveIdentity']['uuid']
        self.assertEqual(uuid, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')

        # Check database objects
        uidentity_db = UniqueIdentity.objects.get(uuid='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '334da68fcd3da4e799791f73dfada2afb22648c6')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jsmith@example.com')

        uidentity_db = UniqueIdentity.objects.get(uuid='880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity_db.name, 'John Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.com')

        uidentity_db = UniqueIdentity.objects.get(uuid='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = uidentity_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.id, '03877f31261a6d1a1b3971d240e628259364b8ac')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jdoe@example.com')

    def test_not_found_from_identity(self):
        """Test whether it fails when 'from_id' identity is not found"""

        client = graphene.test.Client(schema)

        params = {
            'fromID': 'FFFFFFFFFFFFFFF',
            'toUUID': '03877f31261a6d1a1b3971d240e628259364b8ac'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UID_DOES_NOT_EXIST_ERROR)

    def test_not_found_to_identity(self):
        """Test whether it fails when 'to_uuid' unique identity is not found"""

        client = graphene.test.Client(schema)

        params = {
            'fromID': '03877f31261a6d1a1b3971d240e628259364b8ac',
            'toUUID': 'FFFFFFFFFFFFFFF'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UID_DOES_NOT_EXIST_ERROR)

    def test_empty_from_id(self):
        """Check whether identities cannot be moved when giving an empty id"""

        client = graphene.test.Client(schema)

        params = {
            'fromID': '',
            'toUUID': '03877f31261a6d1a1b3971d240e628259364b8ac'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, FROM_ID_EMPTY_ERROR)

    def test_empty_to_uuid(self):
        """Check whether identities cannot be moved when giving an empty UUID"""

        client = graphene.test.Client(schema)

        params = {
            'fromID': '03877f31261a6d1a1b3971d240e628259364b8ac',
            'toUUID': ''
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, TO_UUID_EMPTY_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'fromID': '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331',
            'toUUID': '03877f31261a6d1a1b3971d240e628259364b8ac'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestEnrollMutation(django.test.TestCase):
    """Unit tests for mutation to enroll identities"""

    SH_ENROLL = """
      mutation enrollId($uuid: String, $organization: String,
                        $fromDate: DateTime, $toDate: DateTime) {
        enroll(uuid: $uuid, organization: $organization
               fromDate: $fromDate, toDate: $toDate) {
          uuid
          uidentity {
            uuid
            enrollments {
              organization {
                name
              }
            start
            end
            }
          }
        }
      }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        # Transaction
        self.trxl = TransactionsLog.open(name='enroll')

        jsmith = api.add_identity('scm', email='jsmith@example')
        db.add_organization(self.trxl, 'Example')

        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))
        api.enroll(jsmith.id, 'Example',
                   from_date=datetime.datetime(2004, 1, 1),
                   to_date=datetime.datetime(2006, 1, 1))

    def test_enroll(self):
        """Check if it enrolls a unique identity"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'organization': 'Example',
            'fromDate': '2008-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, profile was updated
        enrollments = executed['data']['enroll']['uidentity']['enrollments']

        self.assertEqual(len(enrollments), 3)

        enrollment = enrollments[0]
        self.assertEqual(enrollment['organization']['name'], 'Example')
        self.assertEqual(enrollment['start'], '1999-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2000-01-01T00:00:00+00:00')

        enrollment = enrollments[1]
        self.assertEqual(enrollment['organization']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2004-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2006-01-01T00:00:00+00:00')

        enrollment = enrollments[2]
        self.assertEqual(enrollment['organization']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2008-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2009-01-01T00:00:00+00:00')

        uuid = executed['data']['enroll']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        uidentity = UniqueIdentity.objects.get(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments_db = uidentity.enrollments.all()
        self.assertEqual(len(enrollments_db), 3)

    def test_merge_enrollments(self):
        """Check if enrollments are merged for overlapped new entries"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'organization': 'Example',
            'fromDate': '1998-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, profile was updated
        enrollments = executed['data']['enroll']['uidentity']['enrollments']

        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment['organization']['name'], 'Example')
        self.assertEqual(enrollment['start'], '1998-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2009-01-01T00:00:00+00:00')

        uuid = executed['data']['enroll']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        uidentity = UniqueIdentity.objects.get(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments_db = uidentity.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

    def test_non_existing_uuid(self):
        """Check if it fails when the unique identity does not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'FFFFFFFFFFFFFFF',
            'organization': 'Example',
            'fromDate': '1998-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UID_DOES_NOT_EXIST_ERROR)

    def test_non_existing_organization(self):
        """Check if it fails when the organization does not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'organization': 'Bitergia',
            'fromDate': '1998-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_BITERGIA_DOES_NOT_EXIST_ERROR)

    def test_integrity_error(self):
        """Check whether enrollments in an existing period cannot be inserted"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'organization': 'Example',
            'fromDate': '2005-01-01T00:00:00+0000',
            'toDate': '2005-06-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        err = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3-Example-2005-01-01 00:00:00+00:00-2005-06-01 00:00:00+00:00'
        err = DUPLICATED_ENROLLMENT_ERROR.format(err)
        self.assertEqual(msg, err)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'organization': 'Example',
            'fromDate': '2008-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestWithdrawMutation(django.test.TestCase):
    """Unit tests for mutation to withdraw identities"""

    SH_WITHDRAW = """
      mutation withdrawId($uuid: String, $organization: String,
                          $fromDate: DateTime, $toDate: DateTime) {
        withdraw(uuid: $uuid, organization: $organization
                 fromDate: $fromDate, toDate: $toDate) {
          uuid
          uidentity {
            uuid
            enrollments {
              organization {
                name
              }
            start
            end
            }
          }
        }
      }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        # Transaction
        self.trxl = TransactionsLog.open(name='withdraw')

        db.add_organization(self.trxl, 'Example')
        db.add_organization(self.trxl, 'LibreSoft')

        api.add_identity('scm', email='jsmith@example')
        api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2006, 1, 1),
                   to_date=datetime.datetime(2008, 1, 1))
        api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2009, 1, 1),
                   to_date=datetime.datetime(2011, 1, 1))
        api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))
        api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'LibreSoft',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

        api.add_identity('scm', email='jrae@example')
        api.enroll('3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

    def test_withdraw(self):
        """Check if it withdraws a unique identity from an organization"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'organization': 'Example',
            'fromDate': '2007-01-01T00:00:00+0000',
            'toDate': '2013-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, enrollments were updated
        enrollments = executed['data']['withdraw']['uidentity']['enrollments']

        self.assertEqual(len(enrollments), 3)

        enrollment = enrollments[0]
        self.assertEqual(enrollment['organization']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2006-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2007-01-01T00:00:00+00:00')

        enrollment = enrollments[1]
        self.assertEqual(enrollment['organization']['name'], 'LibreSoft')
        self.assertEqual(enrollment['start'], '2012-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2014-01-01T00:00:00+00:00')

        enrollment = enrollments[2]
        self.assertEqual(enrollment['organization']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2013-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2014-01-01T00:00:00+00:00')

        uuid = executed['data']['withdraw']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        uidentity = UniqueIdentity.objects.get(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments_db = uidentity.enrollments.all()
        self.assertEqual(len(enrollments_db), 3)

        # Other enrollments were not deleted
        uidentity_db = UniqueIdentity.objects.get(uuid='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        enrollments_db = uidentity_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

    def test_withdraw_default_ranges(self):
        """Check if it withdraws a unique identity using default ranges when they are not given"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'organization': 'Example'
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, enrollments were updated
        enrollments = executed['data']['withdraw']['uidentity']['enrollments']

        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]
        self.assertEqual(enrollment['organization']['name'], 'LibreSoft')
        self.assertEqual(enrollment['start'], '2012-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2014-01-01T00:00:00+00:00')

        uuid = executed['data']['withdraw']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        uidentity = UniqueIdentity.objects.get(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments_db = uidentity.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

    def test_non_existing_uuid(self):
        """Check if it fails when the unique identity does not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'FFFFFFFFFFFFFFF',
            'organization': 'Example',
            'fromDate': '1998-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UID_DOES_NOT_EXIST_ERROR)

    def test_non_existing_organization(self):
        """Check if it fails when the organization does not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'organization': 'Bitergia',
            'fromDate': '1998-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_BITERGIA_DOES_NOT_EXIST_ERROR)

    def test_non_existing_enrollments(self):
        """Check if it fails when the enrollments for a period do not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'organization': 'Example',
            'fromDate': '2050-01-01T00:00:00+0000',
            'toDate': '2060-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ENROLLMENT_DOES_NOT_EXIST_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'organization': 'Example',
            'fromDate': '2007-01-01T00:00:00+0000',
            'toDate': '2013-01-01T00:00:00+0000',
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestMergeIdentitiesMutation(django.test.TestCase):
    """Unit tests for mutation to merge unique identities"""

    SH_MERGE = """
          mutation mergeIds($fromUuids: [String], $toUuid: String) {
            mergeIdentities(fromUuids: $fromUuids, toUuid: $toUuid) {
              uuid
              uidentity {
                uuid
                identities {
                  id
                  name
                  email
                  username
                  source
                }
              }
            }
          }
        """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        # Transaction
        self.trxl = TransactionsLog.open(name='merge_identities')

        db.add_organization(self.trxl, 'Example')
        db.add_organization(self.trxl, 'Bitergia')

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')

        api.add_identity('scm', email='jsmith@example')
        api.add_identity('git', email='jsmith-git@example', uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        api.update_profile(uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', name='J. Smith',
                           email='jsmith@example', gender='male', gender_acc=75)
        api.enroll('e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2017, 6, 1))

        api.add_identity('scm', email='jsmith@bitergia')
        api.add_identity('phabricator', email='jsmith-phab@bitergia', uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        api.update_profile(uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed', name='John Smith',
                           email='jsmith@profile-email', is_bot=True, country_code='US')
        api.enroll('caa5ebfe833371e23f0a3566f2b7ef4a984c4fed', 'Bitergia',
                   from_date=datetime.datetime(2017, 6, 2),
                   to_date=datetime.datetime(2100, 1, 1))

        api.add_identity('scm', email='jsmith@libresoft')
        api.add_identity('phabricator', email='jsmith2@libresoft', uuid='1c13fec7a328201fc6a230fe43eb81df0e20626e')
        api.add_identity('phabricator', email='jsmith3@libresoft', uuid='1c13fec7a328201fc6a230fe43eb81df0e20626e')
        api.update_profile(uuid='1c13fec7a328201fc6a230fe43eb81df0e20626e', name='John Smith',
                           email='jsmith@profile-email', is_bot=False, country_code='US')

    def test_merge_identities(self):
        """Check whether it merges two unique identities, merging their ids, enrollments and profiles"""

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': ['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
            'toUuid': 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed'
        }

        executed = client.execute(self.SH_MERGE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, identities were merged
        identities = executed['data']['mergeIdentities']['uidentity']['identities']

        self.assertEqual(len(identities), 4)

        identity = identities[0]
        self.assertEqual(identity['id'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith-git@example')
        self.assertEqual(identity['source'], 'git')

        identity = identities[1]
        self.assertEqual(identity['id'], '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith-phab@bitergia')
        self.assertEqual(identity['source'], 'phabricator')

        identity = identities[2]
        self.assertEqual(identity['id'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith@bitergia')
        self.assertEqual(identity['source'], 'scm')

        identity = identities[3]
        self.assertEqual(identity['id'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith@example')
        self.assertEqual(identity['source'], 'scm')

        uuid = executed['data']['mergeIdentities']['uuid']
        self.assertEqual(uuid, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        # Check database objects
        uidentity_db = UniqueIdentity.objects.get(uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        self.assertIsInstance(uidentity_db, UniqueIdentity)
        self.assertEqual(uidentity_db.uuid, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = uidentity_db.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 75)
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.country_id, 'US')

        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.alpha3, 'USA')

        identities = uidentity_db.identities.all()
        self.assertEqual(len(identities), 4)

        id1 = identities[0]
        self.assertEqual(id1.id, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id1.email, 'jsmith-git@example')
        self.assertEqual(id1.source, 'git')

        id2 = identities[1]
        self.assertEqual(id2.id, '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(id2.email, 'jsmith-phab@bitergia')
        self.assertEqual(id2.source, 'phabricator')

        id3 = identities[2]
        self.assertEqual(id3.id, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(id3.email, 'jsmith@bitergia')
        self.assertEqual(id3.source, 'scm')

        id4 = identities[3]
        self.assertEqual(id4.id, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(id4.email, 'jsmith@example')
        self.assertEqual(id4.source, 'scm')

        enrollments = uidentity_db.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1.organization.name, 'Example')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.organization.name, 'Bitergia')
        self.assertEqual(rol2.start, datetime.datetime(2017, 6, 2, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_merge_multiple_identities(self):
        """Check whether it merges more than two unique identities, merging their ids, enrollments and profiles"""

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': ['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                          '1c13fec7a328201fc6a230fe43eb81df0e20626e'],
            'toUuid': 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed'
        }

        executed = client.execute(self.SH_MERGE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, identities were merged
        identities = executed['data']['mergeIdentities']['uidentity']['identities']

        self.assertEqual(len(identities), 7)

        identity = identities[0]
        self.assertEqual(identity['id'], '1c13fec7a328201fc6a230fe43eb81df0e20626e')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith@libresoft')
        self.assertEqual(identity['source'], 'scm')

        identity = identities[1]
        self.assertEqual(identity['id'], '31581d7c6b039318e9048c4d8571666c26a5622b')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith3@libresoft')
        self.assertEqual(identity['source'], 'phabricator')

        identity = identities[2]
        self.assertEqual(identity['id'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith-git@example')
        self.assertEqual(identity['source'], 'git')

        identity = identities[3]
        self.assertEqual(identity['id'], '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith-phab@bitergia')
        self.assertEqual(identity['source'], 'phabricator')

        identity = identities[4]
        self.assertEqual(identity['id'], 'c2f5aa44e920b4fbe3cd36894b18e80a2606deba')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith2@libresoft')
        self.assertEqual(identity['source'], 'phabricator')

        identity = identities[5]
        self.assertEqual(identity['id'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith@bitergia')
        self.assertEqual(identity['source'], 'scm')

        identity = identities[6]
        self.assertEqual(identity['id'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith@example')
        self.assertEqual(identity['source'], 'scm')

        uuid = executed['data']['mergeIdentities']['uuid']
        self.assertEqual(uuid, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        # Check database objects
        uidentity_db = UniqueIdentity.objects.get(uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        self.assertIsInstance(uidentity_db, UniqueIdentity)
        self.assertEqual(uidentity_db.uuid, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = uidentity_db.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 75)
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.country_id, 'US')

        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.alpha3, 'USA')

        identities = uidentity_db.identities.all()
        self.assertEqual(len(identities), 7)

        id1 = identities[0]
        self.assertEqual(id1.id, '1c13fec7a328201fc6a230fe43eb81df0e20626e')
        self.assertEqual(id1.email, 'jsmith@libresoft')
        self.assertEqual(id1.source, 'scm')

        id2 = identities[1]
        self.assertEqual(id2.id, '31581d7c6b039318e9048c4d8571666c26a5622b')
        self.assertEqual(id2.email, 'jsmith3@libresoft')
        self.assertEqual(id2.source, 'phabricator')

        id3 = identities[2]
        self.assertEqual(id3.id, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id3.email, 'jsmith-git@example')
        self.assertEqual(id3.source, 'git')

        id4 = identities[3]
        self.assertEqual(id4.id, '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(id4.email, 'jsmith-phab@bitergia')
        self.assertEqual(id4.source, 'phabricator')

        id5 = identities[4]
        self.assertEqual(id5.id, 'c2f5aa44e920b4fbe3cd36894b18e80a2606deba')
        self.assertEqual(id5.email, 'jsmith2@libresoft')
        self.assertEqual(id5.source, 'phabricator')

        id6 = identities[5]
        self.assertEqual(id6.id, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(id6.email, 'jsmith@bitergia')
        self.assertEqual(id6.source, 'scm')

        id7 = identities[6]
        self.assertEqual(id7.id, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(id7.email, 'jsmith@example')
        self.assertEqual(id7.source, 'scm')

        enrollments = uidentity_db.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1.organization.name, 'Example')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.organization.name, 'Bitergia')
        self.assertEqual(rol2.start, datetime.datetime(2017, 6, 2, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_non_existing_from_uuids(self):
        """Check if it fails merging unique identities when source uuids field is `None` or empty"""

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': [],
            'toUuid': 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed'
        }

        executed = client.execute(self.SH_MERGE,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']

        self.assertEqual(msg, FROM_UUIDS_EMPTY_ERROR)

    def test_non_existing_from_uuid(self):
        """Check if it fails merging two unique identities when source uuid is `None` or empty"""

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': [''],
            'toUuid': 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed'
        }

        executed = client.execute(self.SH_MERGE,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']

        self.assertEqual(msg, FROM_UUID_EMPTY_ERROR)

    def test_non_existing_to_uuid(self):
        """Check if it fails merging two unique identities when destination uuid is `None` or empty"""

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': ['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
            'toUuid': ''
        }

        executed = client.execute(self.SH_MERGE,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']

        self.assertEqual(msg, TO_UUID_EMPTY_ERROR)

    def test_from_uuid_to_uuid_equal(self):
        """Check if it fails merging two unique identities when they are equal"""

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': ['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
            'toUuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'
        }

        executed = client.execute(self.SH_MERGE,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']

        self.assertEqual(msg, FROM_UUID_TO_UUID_EQUAL_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': ['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
            'toUuid': 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed'
        }
        executed = client.execute(self.SH_MERGE,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)
