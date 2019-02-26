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

import dateutil

import django.core.exceptions
import django.test
import graphene
import graphene.test

from sortinghat.core import api
from sortinghat.core import db
from sortinghat.core.models import (Organization,
                                    Domain,
                                    Country,
                                    UniqueIdentity,
                                    Identity,
                                    Profile,
                                    Enrollment)
from sortinghat.core.schema import SortingHatQuery, SortingHatMutation


DUPLICATED_ORG_ERROR = "Organization 'Example' already exists in the registry"
DUPLICATED_DOM_ERROR = "Domain 'example.net' already exists in the registry"
DUPLICATED_UNIQUE_IDENTITY = "UniqueIdentity 'eda9f62ad321b1fbe5f283cc05e2484516203117' already exists in the registry"
DUPLICATED_ENROLLMENT_ERROR = "Enrollment '{}' already exists in the registry"
NAME_EMPTY_ERROR = "'name' cannot be an empty string"
DOMAIN_NAME_EMPTY_ERROR = "'domain_name' cannot be an empty string"
SOURCE_EMPTY_ERROR = "'source' cannot be an empty string"
IDENTITY_EMPTY_DATA_ERROR = 'identity data cannot be empty'
UUID_EMPTY_ERROR = "'uuid' cannot be an empty string"
ORG_DOES_NOT_EXIST_ERROR = "Organization matching query does not exist."
DOMAIN_DOES_NOT_EXIST_ERROR = "Domain matching query does not exist."
UID_DOES_NOT_EXIST_ERROR = "FFFFFFFFFFFFFFF not found in the registry"
ORGANIZATION_DOES_NOT_EXIST_ERROR = "Bitergia not found in the registry"
ENROLLMENT_DOES_NOT_EXIST_ERROR = "'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3-Example-2050-01-01 00:00:00+00:00-2060-01-01 00:00:00+00:00' not found in the registry"


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
SH_UIDS_UUID_FILTER = """{
  uidentities(filters: {uuid: "a9b403e150dd4af8953a52a4bb841051e4b705d9"}) {
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


class TestMutations(SortingHatMutation):
    pass


schema = graphene.Schema(query=TestQuery,
                         mutation=TestMutations)


class TestQueryOrganizations(django.test.TestCase):
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
        executed = client.execute(SH_UIDS_UUID_FILTER)

        uidentities = executed['data']['uidentities']
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
        executed = client.execute(SH_UIDS_UUID_FILTER)

        uids = executed['data']['uidentities']
        self.assertListEqual(uids, [])


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

    def test_add_organization(self):
        """Check if a new organization is added"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG)

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
        executed = client.execute(self.SH_ADD_ORG_NAME_EMPTY)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, NAME_EMPTY_ERROR)

        # Check database
        orgs = Organization.objects.all()
        self.assertEqual(len(orgs), 0)

    def test_integrity_error(self):
        """Check whether organizations with the same name cannot be inserted"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG)

        # Check database
        org = Organization.objects.get(name='Example')
        self.assertEqual(org.name, 'Example')

        # Try to insert it twice
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_ORG_ERROR)


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
        executed = client.execute(self.SH_DELETE_ORG)

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
        executed = client.execute(self.SH_DELETE_ORG)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORG_DOES_NOT_EXIST_ERROR)

        # It should not remove anything
        Organization.objects.create(name='Bitergia')

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORG_DOES_NOT_EXIST_ERROR)

        orgs = Organization.objects.all()
        self.assertEqual(len(orgs), 1)


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

    def test_add_domain(self):
        """Check if a new domain is added"""

        Organization.objects.create(name='Example')

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_DOMAIN)

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
        executed = client.execute(self.SH_ADD_DOMAIN_EMPTY)

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
        client.execute(self.SH_ADD_DOMAIN)

        # Check database
        dom = Domain.objects.get(domain='example.net')
        self.assertEqual(dom.domain, 'example.net')

        # Try to insert it twice
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_DOMAIN)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_DOM_ERROR)

    def test_not_found_organization(self):
        """Check if it returns an error when an organization does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_DOMAIN)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORG_DOES_NOT_EXIST_ERROR)


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

    def test_delete_domain(self):
        """Check whether it deletes a domain"""

        org = Organization.objects.create(name='Example')
        Domain.objects.create(domain='example.net', organization=org)
        Domain.objects.create(domain='example.com', organization=org)

        # Delete organization
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_DOMAIN)

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
        executed = client.execute(self.SH_DELETE_DOMAIN)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DOMAIN_DOES_NOT_EXIST_ERROR)

        # It should not remove anything
        org = Organization.objects.create(name='Bitergia')
        Domain.objects.create(domain='example.com', organization=org)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DOMAIN_DOES_NOT_EXIST_ERROR)

        domains = Domain.objects.all()
        self.assertEqual(len(domains), 1)


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

    def test_add_new_identities(self):
        """Check if everything goes OK when adding new identities"""

        client = graphene.test.Client(schema)

        params = {
            'source': 'scm',
            'name': 'Jane Roe',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY, variables=params)

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
        executed = client.execute(self.SH_ADD_IDENTITY, variables=params)

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
        executed = client.execute(self.SH_ADD_IDENTITY, variables=params)

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
        executed = client.execute(self.SH_ADD_IDENTITY, variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_UNIQUE_IDENTITY)

        # Different case letters, but same identity
        params = {
            'source': 'scm',
            'name': 'jane roe',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY, variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_UNIQUE_IDENTITY)

        # Different accents, but same identity
        params = {
            'source': 'scm',
            'name': 'Jane Röe',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY, variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_UNIQUE_IDENTITY)

    def test_empty_source(self):
        """Check whether new identities cannot be added when giving an empty source"""

        client = graphene.test.Client(schema)

        params = {'source': ''}
        executed = client.execute(self.SH_ADD_IDENTITY, variables=params)
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
        executed = client.execute(self.SH_ADD_IDENTITY, variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, IDENTITY_EMPTY_DATA_ERROR)

        params = {
            'source': 'scm',
            'name': '',
            'email': '',
            'username': '',
        }
        executed = client.execute(self.SH_ADD_IDENTITY, variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, IDENTITY_EMPTY_DATA_ERROR)


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
        """Load initial dataset"""

        # Organizations
        example_org = db.add_organization('Example')
        bitergia_org = db.add_organization('Bitergia')
        libresoft_org = db.add_organization('LibreSoft')

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
        executed = client.execute(self.SH_DELETE_IDENTITY, variables=params)

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
        executed = client.execute(self.SH_DELETE_IDENTITY, variables=params)

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
        executed = client.execute(self.SH_DELETE_IDENTITY, variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UID_DOES_NOT_EXIST_ERROR)

    def test_empty_uuid(self):
        """Check whether identities cannot be removed when giving an empty UUID"""

        client = graphene.test.Client(schema)

        params = {'uuid': ''}
        executed = client.execute(self.SH_DELETE_IDENTITY, variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_EMPTY_ERROR)


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
        """Load initial dataset"""

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
        executed = client.execute(self.SH_UPDATE_PROFILE, variables=params)

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
        executed = client.execute(self.SH_UPDATE_PROFILE, variables=params)

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
        executed = client.execute(self.SH_UPDATE_PROFILE, variables=params)

        profile = executed['data']['updateProfile']['uidentity']['profile']
        self.assertEqual(profile['name'], None)
        self.assertEqual(profile['email'], None)


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
        """Load initial dataset"""

        jsmith = api.add_identity('scm', email='jsmith@example')
        db.add_organization('Example')

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
        executed = client.execute(self.SH_ENROLL, variables=params)

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
        executed = client.execute(self.SH_ENROLL, variables=params)

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
        executed = client.execute(self.SH_ENROLL, variables=params)

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
        executed = client.execute(self.SH_ENROLL, variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_DOES_NOT_EXIST_ERROR)

    def test_integrity_error(self):
        """Check whether enrollments in an existing period cannot be inserted"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'organization': 'Example',
            'fromDate': '2005-01-01T00:00:00+0000',
            'toDate': '2005-06-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL, variables=params)

        msg = executed['errors'][0]['message']
        err = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3-Example-2005-01-01 00:00:00+00:00-2005-06-01 00:00:00+00:00'
        err = DUPLICATED_ENROLLMENT_ERROR.format(err)
        self.assertEqual(msg, err)


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
        """Load initial dataset"""

        db.add_organization('Example')
        db.add_organization('LibreSoft')

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
        executed = client.execute(self.SH_WITHDRAW, variables=params)

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
        executed = client.execute(self.SH_WITHDRAW, variables=params)

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
        executed = client.execute(self.SH_WITHDRAW, variables=params)

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
        executed = client.execute(self.SH_WITHDRAW, variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_DOES_NOT_EXIST_ERROR)

    def test_non_existing_enrollments(self):
        """Check if it fails when the enrollments for a period do not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'organization': 'Example',
            'fromDate': '2050-01-01T00:00:00+0000',
            'toDate': '2060-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_WITHDRAW, variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ENROLLMENT_DOES_NOT_EXIST_ERROR)
