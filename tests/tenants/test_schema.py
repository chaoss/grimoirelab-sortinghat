# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Bitergia
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
#     Jose Javier Merchante <jjmerchante@bitergia.com>
#

import django.test
import graphene.test
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from grimoirelab_toolkit.datetime import datetime_utcnow
from sortinghat.app.schema import schema
from sortinghat.core import tenant
from sortinghat.core.models import Organization, Domain, Transaction

# API endpoint to obtain a context for executing queries
GRAPHQL_ENDPOINT = '/graphql/'

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


class TestTenantSchema(django.test.TestCase):
    """Unit tests for queries with multi-tenant"""
    databases = {'default', 'tenant_1', 'tenant_2'}

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test', is_superuser=True)
        self.context_value = django.test.RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_add_org_tenant(self):
        """Check if it adds an organizations in a tenant"""

        # Tests
        tenant.set_db_tenant("tenant_1")
        client = graphene.test.Client(schema)
        executed = client.execute(SH_ADD_ORG,
                                  context_value=self.context_value)
        tenant.unset_db_tenant()

        # Check result
        org = executed['data']['addOrganization']['organization']
        self.assertEqual(org['name'], 'Example')
        self.assertListEqual(org['domains'], [])

        # Check database
        org = Organization.objects.using('tenant_1').get(name='Example')
        self.assertEqual(org.name, 'Example')

        with self.assertRaises(ObjectDoesNotExist):
            org = Organization.objects.using('tenant_2').get(name='Example')

    def test_get_organization(self):
        """Check if it retrieves an organization from a tenant"""

        tenant.set_db_tenant("tenant_1")
        org = Organization.add_root(name='Example')
        Domain.objects.create(domain='example.com', organization=org)
        Domain.objects.create(domain='example.org', organization=org)
        org = Organization.add_root(name='Bitergia')
        Domain.objects.create(domain='bitergia.com', organization=org)
        _ = Organization.add_root(name='LibreSoft')

        client = graphene.test.Client(schema)
        executed = client.execute(SH_ORGS_QUERY,
                                  context_value=self.context_value)
        tenant.unset_db_tenant()

        # Check result
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

    def test_get_organization_empty_tenant(self):
        """Check if it does not retrieve an organization from different tenant"""

        tenant.set_db_tenant("tenant_1")
        org = Organization.add_root(name='Example')
        Domain.objects.create(domain='example.com', organization=org)
        Domain.objects.create(domain='example.org', organization=org)

        tenant.set_db_tenant("tenant_2")
        client = graphene.test.Client(schema)
        executed = client.execute(SH_ORGS_QUERY,
                                  context_value=self.context_value)
        tenant.unset_db_tenant()

        # Check result
        orgs = executed['data']['organizations']['entities']
        self.assertEqual(len(orgs), 0)

        # Check that organization is available for tenant_1
        tenant.set_db_tenant("tenant_1")
        client = graphene.test.Client(schema)
        executed = client.execute(SH_ORGS_QUERY,
                                  context_value=self.context_value)
        tenant.unset_db_tenant()

        orgs = executed['data']['organizations']['entities']
        self.assertEqual(len(orgs), 1)

    def test_transaction(self):
        """Check if a transaction is created with the right tenant"""

        timestamp = datetime_utcnow()

        tenant.set_db_tenant("tenant_1")
        client = graphene.test.Client(schema)
        executed = client.execute(SH_ADD_ORG,
                                  context_value=self.context_value)

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'add_organization')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, self.user.username)
        self.assertEqual(trx.tenant, 'tenant_1')
        tenant.unset_db_tenant()
