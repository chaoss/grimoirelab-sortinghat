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
import json

from dateutil.tz import UTC

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from grimoirelab_toolkit.datetime import datetime_utcnow, datetime_to_utc

from sortinghat.core import db
from sortinghat.core.errors import AlreadyExistsError, NotFoundError
from sortinghat.core.log import TransactionsLog
from sortinghat.core.models import (MIN_PERIOD_DATE,
                                    MAX_PERIOD_DATE,
                                    Organization,
                                    Domain,
                                    Country,
                                    UniqueIdentity,
                                    Identity,
                                    Profile,
                                    Enrollment,
                                    Transaction,
                                    Operation)


DUPLICATED_ORG_ERROR = "Organization 'Example' already exists in the registry"
DUPLICATED_DOM_ERROR = "Domain 'example.org' already exists in the registry"
DUPLICATED_UID_ERROR = "UniqueIdentity '1234567890ABCDFE' already exists in the registry"
DUPLICATED_ID_ERROR = "Identity '1234567890ABCDFE' already exists in the registry"
DUPLICATED_ID_DATA_ERROR = "Identity 'John Smith-jsmith@example.org-jsmith-scm' already exists in the registry"
NAME_NONE_ERROR = "'name' cannot be None"
NAME_EMPTY_ERROR = "'name' cannot be an empty string"
NAME_WHITESPACES_ERROR = "'name' cannot be composed by whitespaces only"
DOMAIN_NAME_NONE_ERROR = "'domain_name' cannot be None"
DOMAIN_NAME_EMPTY_ERROR = "'domain_name' cannot be an empty string"
DOMAIN_NAME_WHITESPACES_ERROR = "'domain_name' cannot be composed by whitespaces only"
DOMAIN_VALUE_ERROR = "field value must be a string; int given"
TOP_DOMAIN_VALUE_ERROR = "'is_top_domain' must have a boolean value"
UUID_NONE_ERROR = "'uuid' cannot be None"
UUID_EMPTY_ERROR = "'uuid' cannot be an empty string"
UUID_WHITESPACES_ERROR = "'uuid' cannot be composed by whitespaces only"
IDENTITY_ID_NONE_ERROR = "'identity_id' cannot be None"
IDENTITY_ID_EMPTY_ERROR = "'identity_id' cannot be an empty string"
IDENTITY_ID_WHITESPACES_ERROR = "'identity_id' cannot be composed by whitespaces only"
SOURCE_NONE_ERROR = "'source' cannot be None"
SOURCE_EMPTY_ERROR = "'source' cannot be an empty string"
SOURCE_WHITESPACES_ERROR = "'source' cannot be composed by whitespaces only"
IDENTITY_DATA_NONE_OR_EMPTY_ERROR = "identity data cannot be None or empty"
IDENTITY_DATA_EMPTY_ERROR = "'{name}' cannot be an empty string"
IDENTITY_DATA_NONE_ERROR = "'{name}' cannot be None"
IDENTITY_DATA_WHITESPACES_ERROR = "'{name}' cannot be composed by whitespaces only"
UNIQUE_IDENTITY_NOT_FOUND_ERROR = "zyxwuv not found in the registry"
IDENTITY_NOT_FOUND_ERROR = "zyxwuv not found in the registry"
ORGANIZATION_NOT_FOUND_ERROR = "Bitergia not found in the registry"
DOMAIN_NOT_FOUND_ERROR = "example.net not found in the registry"
IS_BOT_VALUE_ERROR = "'is_bot' must have a boolean value"
COUNTRY_CODE_ERROR = r"'country_code' \({code}\) does not match with a valid code"
GENDER_ACC_INVALID_ERROR = "'gender_acc' can only be set when 'gender' is given"
GENDER_ACC_INVALID_TYPE_ERROR = "'gender_acc' must have an integer value"
GENDER_ACC_INVALID_RANGE_ERROR = r"'gender_acc' \({acc}\) is not in range \(1,100\)"
START_DATE_NONE_ERROR = "'start' date cannot be None"
END_DATE_NONE_ERROR = "'end' date cannot be None"
PERIOD_INVALID_ERROR = "'start' date {start} cannot be greater than {end}"
PERIOD_OUT_OF_BOUNDS_ERROR = "'{type}' date {date} is out of bounds"
MOVE_ERROR = "identity '0001' is already assigned to 'AAAA'"


class TestFindUniqueIdentity(TestCase):
    """Unit tests for find_unique_identity"""

    def test_find_unique_identity(self):
        """Test if a unique identity is found by its UUID"""

        uuid = 'abcdefghijklmnopqrstuvwxyz'
        UniqueIdentity.objects.create(uuid=uuid)

        uidentity = db.find_unique_identity(uuid)
        self.assertIsInstance(uidentity, UniqueIdentity)
        self.assertEqual(uidentity.uuid, uuid)

    def test_unique_identity_not_found(self):
        """Test whether it raises an exception when the unique identity is not found"""

        uuid = 'abcdefghijklmnopqrstuvwxyz'
        UniqueIdentity.objects.create(uuid=uuid)

        with self.assertRaisesRegex(NotFoundError, UNIQUE_IDENTITY_NOT_FOUND_ERROR):
            db.find_unique_identity('zyxwuv')


class TestFindIdentity(TestCase):
    """Unit tests for find_identity"""

    def test_find_identity(self):
        """Test if an identity is found by its UUID"""

        uuid = 'abcdefghijklmnopqrstuvwxyz'
        uidentity = UniqueIdentity.objects.create(uuid=uuid)
        Identity.objects.create(id=uuid, source='scm', uidentity=uidentity)

        identity = db.find_identity(uuid)
        self.assertIsInstance(identity, Identity)
        self.assertEqual(identity.id, uuid)

    def test_identity_not_found(self):
        """Test whether it raises an exception when the identity is not found"""

        uuid = 'abcdefghijklmnopqrstuvwxyz'
        uidentity = UniqueIdentity.objects.create(uuid=uuid)
        Identity.objects.create(id=uuid, source='scm', uidentity=uidentity)

        with self.assertRaisesRegex(NotFoundError, IDENTITY_NOT_FOUND_ERROR):
            db.find_identity('zyxwuv')


class TestFindOrganization(TestCase):
    """Unit tests for find_organization"""

    def test_find_organization(self):
        """Test if an organization is found by its name"""

        name = 'Example'
        Organization.objects.create(name=name)

        organization = db.find_organization(name)
        self.assertIsInstance(organization, Organization)
        self.assertEqual(organization.name, name)

    def test_organization_not_found(self):
        """Test whether it raises an exception when the organization is not found"""

        name = 'Example'
        Organization.objects.create(name=name)

        with self.assertRaisesRegex(NotFoundError, ORGANIZATION_NOT_FOUND_ERROR):
            db.find_organization('Bitergia')


class TestFindDomain(TestCase):
    """Unit tests for find_domain"""

    def setUp(self):
        """Load initial dataset"""

        org = Organization.objects.create(name='Example')
        Domain.objects.create(domain='example.com',
                              organization=org,
                              is_top_domain=True)

    def test_find_domain(self):
        """Test if a domain is found by its name"""

        domain = db.find_domain('example.com')

        # Tests
        self.assertIsInstance(domain, Domain)
        self.assertEqual(domain.organization.name, 'Example')
        self.assertEqual(domain.domain, 'example.com')
        self.assertEqual(domain.is_top_domain, True)

    def test_domain_not_found(self):
        """Test whether it raises an exception when the domain is not found"""

        with self.assertRaisesRegex(NotFoundError, DOMAIN_NOT_FOUND_ERROR):
            db.find_domain('example.net')

    def test_domain_name_none(self):
        """Check if it fails when domain name is `None`"""

        with self.assertRaisesRegex(ValueError, DOMAIN_NAME_NONE_ERROR):
            db.find_domain(None)

    def test_domain_name_empty(self):
        """Check if it fails when domain name is empty"""

        with self.assertRaisesRegex(ValueError, DOMAIN_NAME_EMPTY_ERROR):
            db.find_domain('')

    def test_domain_name_whitespaces(self):
        """Check if it fails when domain name is composed by whitespaces"""

        with self.assertRaisesRegex(ValueError, DOMAIN_NAME_WHITESPACES_ERROR):
            db.find_domain('    ')

        with self.assertRaisesRegex(ValueError, DOMAIN_NAME_WHITESPACES_ERROR):
            db.find_domain('\t')

        with self.assertRaisesRegex(ValueError, DOMAIN_NAME_WHITESPACES_ERROR):
            db.find_domain('  \t  ')

    def test_domain_name_int(self):
        """Check if it fails when domain name is an integer"""

        with self.assertRaisesRegex(TypeError, DOMAIN_VALUE_ERROR):
            db.find_domain(12345)


class TestSearchEnrollmentsInPeriod(TestCase):
    """Unit tests for search_enrollments_in_period"""

    def test_search_enrollments(self):
        """Test if a set of enrollments is returned"""

        uidentity_a = UniqueIdentity.objects.create(uuid='AAAA')
        uidentity_b = UniqueIdentity.objects.create(uuid='BBBB')

        example_org = Organization.objects.create(name='Example')
        bitergia_org = Organization.objects.create(name='Bitergia')

        # Example enrollments
        Enrollment.objects.create(uidentity=uidentity_a, organization=example_org,
                                  start=datetime.datetime(1999, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2002, 1, 1, tzinfo=UTC))
        Enrollment.objects.create(uidentity=uidentity_a, organization=example_org,
                                  start=datetime.datetime(2003, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2005, 1, 1, tzinfo=UTC))
        Enrollment.objects.create(uidentity=uidentity_a, organization=example_org,
                                  start=datetime.datetime(2008, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2010, 1, 1, tzinfo=UTC))

        Enrollment.objects.create(uidentity=uidentity_b, organization=example_org,
                                  start=datetime.datetime(2000, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2015, 1, 1, tzinfo=UTC))

        # Bitergia enrollments
        Enrollment.objects.create(uidentity=uidentity_a, organization=bitergia_org,
                                  start=datetime.datetime(2001, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2010, 1, 1, tzinfo=UTC))

        # Tests
        enrollments = db.search_enrollments_in_period('AAAA', 'Example',
                                                      from_date=datetime.datetime(2004, 1, 1, tzinfo=UTC),
                                                      to_date=datetime.datetime(2009, 1, 1, tzinfo=UTC))

        # Only Example enrollments for this identity are returned,
        # though there are others in the same range
        self.assertEqual(len(enrollments), 2)

        rol = enrollments[0]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.uidentity, uidentity_a)
        self.assertEqual(rol.organization, example_org)
        self.assertEqual(rol.start, datetime.datetime(2003, 1, 1, tzinfo=UTC))
        self.assertEqual(rol.end, datetime.datetime(2005, 1, 1, tzinfo=UTC))

        rol = enrollments[1]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.uidentity, uidentity_a)
        self.assertEqual(rol.organization, example_org)
        self.assertEqual(rol.start, datetime.datetime(2008, 1, 1, tzinfo=UTC))
        self.assertEqual(rol.end, datetime.datetime(2010, 1, 1, tzinfo=UTC))

    def test_no_enrollments_in_period(self):
        """Test if an empty set is returned when there are not enrollments for a given period"""

        uidentity_a = UniqueIdentity.objects.create(uuid='AAAA')
        example_org = Organization.objects.create(name='Example')

        Enrollment.objects.create(uidentity=uidentity_a, organization=example_org,
                                  start=datetime.datetime(1999, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2000, 1, 1, tzinfo=UTC))

        # Tests
        enrollments = db.search_enrollments_in_period('AAAA', 'Example',
                                                      from_date=datetime.datetime(2000, 2, 1, tzinfo=UTC),
                                                      to_date=datetime.datetime(2009, 1, 1, tzinfo=UTC))
        self.assertEqual(len(enrollments), 0)

    def test_no_identity(self):
        """Test if an empty set is returned when there identity does not exist"""

        uidentity_a = UniqueIdentity.objects.create(uuid='AAAA')
        example_org = Organization.objects.create(name='Example')

        Enrollment.objects.create(uidentity=uidentity_a, organization=example_org,
                                  start=datetime.datetime(1999, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2000, 1, 1, tzinfo=UTC))

        # Tests
        enrollments = db.search_enrollments_in_period('BBBB', 'Example',
                                                      from_date=datetime.datetime(1999, 1, 1, tzinfo=UTC),
                                                      to_date=datetime.datetime(2000, 1, 1, tzinfo=UTC))
        self.assertEqual(len(enrollments), 0)

    def test_no_organization(self):
        """Test if an empty set is returned when there organization does not exist"""

        uidentity_a = UniqueIdentity.objects.create(uuid='AAAA')
        example_org = Organization.objects.create(name='Example')

        Enrollment.objects.create(uidentity=uidentity_a, organization=example_org,
                                  start=datetime.datetime(1999, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2000, 1, 1, tzinfo=UTC))

        # Tests
        enrollments = db.search_enrollments_in_period('AAAA', 'Bitergia',
                                                      from_date=datetime.datetime(1999, 1, 1, tzinfo=UTC),
                                                      to_date=datetime.datetime(2000, 1, 1, tzinfo=UTC))
        self.assertEqual(len(enrollments), 0)


class TestAddOrganization(TestCase):
    """Unit tests for add_organization"""

    def setUp(self):
        """Load initial dataset"""

        self.trxl = TransactionsLog.open(name='add_organization')

    def test_add_organization(self):
        """Check if a new organization is added"""

        name = 'Example'

        org = db.add_organization(self.trxl, name)
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, name)

        org = Organization.objects.get(name=name)
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, name)

    def test_name_none(self):
        """Check whether organizations with None as name cannot be added"""

        with self.assertRaisesRegex(ValueError, NAME_NONE_ERROR):
            db.add_organization(self.trxl, None)

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_name_empty(self):
        """Check whether organizations with empty names cannot be added"""

        with self.assertRaisesRegex(ValueError, NAME_EMPTY_ERROR):
            db.add_organization(self.trxl, '')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_name_whitespaces(self):
        """Check whether organizations composed by whitespaces cannot be added"""

        with self.assertRaisesRegex(ValueError, NAME_WHITESPACES_ERROR):
            db.add_organization(self.trxl, '  ')

        with self.assertRaisesRegex(ValueError, NAME_WHITESPACES_ERROR):
            db.add_organization(self.trxl, '\t')

        with self.assertRaisesRegex(ValueError, NAME_WHITESPACES_ERROR):
            db.add_organization(self.trxl, ' \t  ')

        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_integrity_error(self):
        """Check whether organizations with the same name cannot be inserted"""

        name = 'Example'

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_ORG_ERROR):
            db.add_organization(self.trxl, name)
            db.add_organization(self.trxl, name)

    def test_operations(self):
        """Check if the right operations are created when adding an organization"""

        timestamp = datetime_utcnow()

        db.add_organization(self.trxl, 'Example')

        transactions = Transaction.objects.all()
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'organization')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, 'Example')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['name'], 'Example')


class TestDeleteOrganization(TestCase):
    """Unit tests for delete_organization"""

    def setUp(self):
        """Load initial dataset"""

        self.trxl = TransactionsLog.open(name='delete_organization')

    def test_delete_organization(self):
        """Check whether it deletes an organization and its related data"""

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

        # Check data and remove organization
        org_ex.refresh_from_db()
        self.assertEqual(len(org_ex.domains.all()), 1)
        self.assertEqual(len(org_ex.enrollments.all()), 2)

        org_bit.refresh_from_db()
        self.assertEqual(len(org_bit.enrollments.all()), 1)

        db.delete_organization(self.trxl, org_ex)

        # Tests
        with self.assertRaises(ObjectDoesNotExist):
            Organization.objects.get(name='Example')

        with self.assertRaises(ObjectDoesNotExist):
            Domain.objects.get(domain='example.org')

        enrollments = Enrollment.objects.filter(organization__name='Example')
        self.assertEqual(len(enrollments), 0)

        enrollments = Enrollment.objects.filter(organization__name='Bitergia')
        self.assertEqual(len(enrollments), 1)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        org_ex = Organization.objects.create(name='Example')
        org_bit = Organization.objects.create(name='Bitergia')

        jsmith = UniqueIdentity.objects.create(uuid='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               uidentity=jsmith)
        Enrollment.objects.create(uidentity=jsmith,
                                  organization=org_ex)

        jdoe = UniqueIdentity.objects.create(uuid='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               uidentity=jdoe)
        Enrollment.objects.create(uidentity=jdoe,
                                  organization=org_ex)
        Enrollment.objects.create(uidentity=jdoe,
                                  organization=org_bit)

        # Tests
        before_dt = datetime_utcnow()
        db.delete_organization(self.trxl, org_ex)
        after_dt = datetime_utcnow()

        jsmith = UniqueIdentity.objects.get(uuid='AAAA')
        self.assertLessEqual(before_dt, jsmith.last_modified)
        self.assertGreaterEqual(after_dt, jsmith.last_modified)

        jdoe = UniqueIdentity.objects.get(uuid='BBBB')
        self.assertLessEqual(before_dt, jdoe.last_modified)
        self.assertGreaterEqual(after_dt, jdoe.last_modified)

        # Both unique identities were modified at the same time
        self.assertEqual(jsmith.last_modified, jdoe.last_modified)

    def test_operations(self):
        """Check if the right operations are created when deleting an organization"""

        timestamp = datetime_utcnow()
        org_ex = Organization.objects.create(name='Example')

        transactions = Transaction.objects.filter(name='delete_organization')
        trx = transactions[0]

        db.delete_organization(self.trxl, org_ex)

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'organization')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, 'Example')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['organization'], 'Example')


class TestAddDomain(TestCase):
    """"Unit tests for add_domain"""

    def setUp(self):
        """Load initial dataset"""

        self.trxl = TransactionsLog.open(name='add_domain')

    def test_add_domain(self):
        """Check if a new domain is added"""

        name = 'Example'
        domain_name = 'example.net'

        org = Organization.objects.create(name=name)
        dom = db.add_domain(self.trxl, org, domain_name,
                            is_top_domain=True)
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, domain_name)
        self.assertEqual(dom.organization, org)

        org = Organization.objects.get(name='Example')
        domains = org.domains.all()
        self.assertEqual(len(domains), 1)

        dom = domains[0]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, domain_name)
        self.assertEqual(dom.is_top_domain, True)

    def test_add_multiple_domains(self):
        """Check if multiple domains can be added"""

        org = Organization.objects.create(name='Example')
        db.add_domain(self.trxl, org, 'example.com')
        db.add_domain(self.trxl, org, 'my.example.net',
                      is_top_domain=False)

        org = Organization.objects.get(name='Example')
        domains = org.domains.all()
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Example')

        self.assertEqual(len(domains), 2)

        dom = domains[0]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'example.com')
        self.assertEqual(dom.is_top_domain, True)

        dom = domains[1]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'my.example.net')
        self.assertEqual(dom.is_top_domain, False)

    def test_domain_none(self):
        """Check whether domains with None name cannot be added"""

        org = Organization.objects.create(name='Example')

        with self.assertRaisesRegex(ValueError, DOMAIN_NAME_NONE_ERROR):
            db.add_domain(self.trxl, org, None)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_domain_empty(self):
        """Check whether domains with empty names cannot be added"""

        org = Organization.objects.create(name='Example')

        with self.assertRaisesRegex(ValueError, DOMAIN_NAME_EMPTY_ERROR):
            db.add_domain(self.trxl, org, '')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_domain_whitespaces(self):
        """Check whether domains with names composed by whitespaces cannot be added"""

        org = Organization.objects.create(name='Example')

        with self.assertRaisesRegex(ValueError, DOMAIN_NAME_WHITESPACES_ERROR):
            db.add_domain(self.trxl, org, ' ')

        with self.assertRaisesRegex(ValueError, DOMAIN_NAME_WHITESPACES_ERROR):
            db.add_domain(self.trxl, org, '\t')

        with self.assertRaisesRegex(ValueError, DOMAIN_NAME_WHITESPACES_ERROR):
            db.add_domain(self.trxl, org, ' \t ')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_top_domain_invalid_type(self):
        """Check type values of top domain flag"""

        org = Organization.objects.create(name='Example')

        with self.assertRaisesRegex(ValueError, TOP_DOMAIN_VALUE_ERROR):
            db.add_domain(self.trxl, org, 'example.net', is_top_domain=1)

        with self.assertRaisesRegex(ValueError, TOP_DOMAIN_VALUE_ERROR):
            db.add_domain(self.trxl, org, 'example.net', is_top_domain='False')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_integrity_error(self):
        """Check whether domains with the same domain name cannot be inserted"""

        org = Organization.objects.create(name='Example')
        domain_name = 'example.org'

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_DOM_ERROR):
            db.add_domain(self.trxl, org, domain_name)
            db.add_domain(self.trxl, org, domain_name)

    def test_operations(self):
        """Check if the right operations are created when adding a domain"""

        timestamp = datetime_utcnow()
        org = Organization.objects.create(name='Example')

        dom = db.add_domain(self.trxl, org, 'example.net',
                            is_top_domain=True)

        transactions = Transaction.objects.filter(name='add_domain')
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'domain')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, 'Example')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 3)
        self.assertEqual(op1_args['organization'], 'Example')
        self.assertEqual(op1_args['domain_name'], 'example.net')
        self.assertEqual(op1_args['is_top_domain'], True)


class TestDeleteDomain(TestCase):
    """Unit tests for delete_domain"""

    def setUp(self):
        """Load initial dataset"""

        self.trxl = TransactionsLog.open(name='delete_domain')

    def test_delete_domain(self):
        """Check whether it deletes a domain"""

        org = Organization.objects.create(name='Example')
        dom = Domain.objects.create(domain='example.org', organization=org)
        Domain.objects.create(domain='example.com', organization=org)

        # Check data and remove domain
        org.refresh_from_db()
        self.assertEqual(len(org.domains.all()), 2)

        dom.refresh_from_db()
        db.delete_domain(self.trxl, dom)

        # Tests
        with self.assertRaises(ObjectDoesNotExist):
            Domain.objects.get(domain='example.org')

        org.refresh_from_db()
        self.assertEqual(len(org.domains.all()), 1)

    def test_operations(self):
        """Check if the right operations are created when deleting a domain"""

        timestamp = datetime_utcnow()
        org = Organization.objects.create(name='Example')
        dom = Domain.objects.create(domain='example.org', organization=org)

        db.delete_domain(self.trxl, dom)

        transactions = Transaction.objects.filter(name='delete_domain')
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'domain')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, 'example.org')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['domain'], 'example.org')


class TestAddUniqueIdentity(TestCase):
    """Unit tests for add_unique_identity"""

    def setUp(self):
        """Load initial dataset"""

        self.trxl = TransactionsLog.open(name='add_unique_identity')

    def test_add_unique_identity(self):
        """Check whether it adds a unique identity"""

        uuid = '1234567890ABCDFE'

        uidentity = db.add_unique_identity(self.trxl, uuid)
        self.assertIsInstance(uidentity, UniqueIdentity)
        self.assertEqual(uidentity.uuid, uuid)

        uidentity = UniqueIdentity.objects.get(uuid=uuid)
        self.assertIsInstance(uidentity, UniqueIdentity)
        self.assertEqual(uidentity.uuid, uuid)

        self.assertIsInstance(uidentity.profile, Profile)
        self.assertEqual(uidentity.profile.name, None)
        self.assertEqual(uidentity.profile.email, None)

    def test_add_unique_identities(self):
        """Check whether it adds a set of unique identities"""

        uuids = ['AAAA', 'BBBB', 'CCCC']

        for uuid in uuids:
            db.add_unique_identity(self.trxl, uuid)

        for uuid in uuids:
            uidentity = UniqueIdentity.objects.get(uuid=uuid)
            self.assertIsInstance(uidentity, UniqueIdentity)
            self.assertEqual(uidentity.uuid, uuid)

            self.assertIsInstance(uidentity.profile, Profile)
            self.assertEqual(uidentity.profile.name, None)
            self.assertEqual(uidentity.profile.email, None)

    def test_uuid_none(self):
        """Check whether a unique identity with None as UUID cannot be added"""

        with self.assertRaisesRegex(ValueError, UUID_NONE_ERROR):
            db.add_unique_identity(self.trxl, None)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_uuid_empty(self):
        """Check whether a unique identity with empty UUID cannot be added"""

        with self.assertRaisesRegex(ValueError, UUID_EMPTY_ERROR):
            db.add_unique_identity(self.trxl, '')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_uuid_whitespaces(self):
        """Check whether a unique identity with UUID composed by whitespaces cannot be added"""

        with self.assertRaisesRegex(ValueError, UUID_WHITESPACES_ERROR):
            db.add_unique_identity(self.trxl, '   ')

        with self.assertRaisesRegex(ValueError, UUID_WHITESPACES_ERROR):
            db.add_unique_identity(self.trxl, '\t')

        with self.assertRaisesRegex(ValueError, UUID_WHITESPACES_ERROR):
            db.add_unique_identity(self.trxl, ' \t  ')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_integrity_error(self):
        """Check whether unique identities with the same UUID cannot be inserted"""

        uuid = '1234567890ABCDFE'

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_UID_ERROR):
            db.add_unique_identity(self.trxl, uuid)
            db.add_unique_identity(self.trxl, uuid)

    def test_operations(self):
        """Check if the right operations are created when adding a new identity"""

        timestamp = datetime_utcnow()
        uuid = '1234567890ABCDFE'

        uidentity = db.add_unique_identity(self.trxl, uuid)

        transactions = Transaction.objects.all()
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'unique_identity')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, '1234567890ABCDFE')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['uuid'], uidentity.uuid)


class TestDeleteUniqueIdentity(TestCase):
    """Unit tests for delete_unique_identity"""

    def setUp(self):
        """Load initial dataset"""

        self.trxl = TransactionsLog.open(name='delete_identity')

    def test_delete_unique_identity(self):
        """Check if it deletes a unique identity"""

        org_ex = Organization.objects.create(name='Example')
        org_bit = Organization.objects.create(name='Bitergia')

        jsmith = UniqueIdentity.objects.create(uuid='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               uidentity=jsmith)
        Identity.objects.create(id='0001', name='John Smith',
                                uidentity=jsmith)
        Identity.objects.create(id='0002', email='jsmith@example.net',
                                uidentity=jsmith)
        Identity.objects.create(id='0003', email='jsmith@example.org',
                                uidentity=jsmith)
        Enrollment.objects.create(uidentity=jsmith, organization=org_ex)

        jdoe = UniqueIdentity.objects.create(uuid='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               uidentity=jdoe)
        Identity.objects.create(id='0004', name='John Doe',
                                email='jdoe@bitergia.com',
                                uidentity=jdoe)
        Enrollment.objects.create(uidentity=jdoe, organization=org_ex)
        Enrollment.objects.create(uidentity=jdoe, organization=org_bit)

        # Check data and remove unique identity
        jsmith.refresh_from_db()
        self.assertEqual(len(jsmith.identities.all()), 3)
        self.assertEqual(len(jsmith.enrollments.all()), 1)

        jdoe.refresh_from_db()
        self.assertEqual(len(jdoe.identities.all()), 1)
        self.assertEqual(len(jdoe.enrollments.all()), 2)

        db.delete_unique_identity(self.trxl, jsmith)

        # Tests
        with self.assertRaises(ObjectDoesNotExist):
            UniqueIdentity.objects.get(uuid='AAAA')

        self.assertEqual(len(Identity.objects.all()), 1)
        self.assertEqual(len(Enrollment.objects.all()), 2)

        jdoe.refresh_from_db()
        self.assertEqual(len(jdoe.identities.all()), 1)
        self.assertEqual(len(jdoe.enrollments.all()), 2)

    def test_delete_unique_identities(self):
        """Check if it deletes a set of unique identities"""

        uuids = ['AAAA', 'BBBB', 'CCCC']

        for uuid in uuids:
            UniqueIdentity.objects.create(uuid=uuid)

        self.assertEqual(len(UniqueIdentity.objects.all()), len(uuids))

        for uuid in uuids:
            uidentity = UniqueIdentity.objects.get(uuid=uuid)

            db.delete_unique_identity(self.trxl, uidentity)

            with self.assertRaises(ObjectDoesNotExist):
                UniqueIdentity.objects.get(uuid=uuid)

        self.assertEqual(len(UniqueIdentity.objects.all()), 0)

    def test_operations(self):
        """Check if the right operations are created when deleting an identity"""

        timestamp = datetime_utcnow()
        jsmith = UniqueIdentity.objects.create(uuid='AAAA')

        db.delete_unique_identity(self.trxl, jsmith)

        transactions = Transaction.objects.filter(name='delete_identity')
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'unique_identity')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, 'AAAA')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['uidentity'], 'AAAA')


class TestAddIdentity(TestCase):
    """Unit tests for add_identity"""

    def setUp(self):
        """Load initial dataset"""

        self.trxl = TransactionsLog.open(name='add_identity')

    def test_add_identity(self):
        """Check if a new identity is added"""

        uuid = '1234567890ABCDFE'

        uidentity = UniqueIdentity.objects.create(uuid=uuid)
        identity = db.add_identity(self.trxl, uidentity, uuid, 'scm',
                                   name='John Smith',
                                   email='jsmith@example.org',
                                   username='jsmith')

        self.assertIsInstance(identity, Identity)
        self.assertEqual(identity.id, uuid)
        self.assertEqual(identity.uidentity, uidentity)

        uidentity = UniqueIdentity.objects.get(uuid=uuid)
        self.assertEqual(uidentity.uuid, uuid)

        identities = uidentity.identities.all()
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertIsInstance(identity, Identity)
        self.assertEqual(identity.id, uuid)
        self.assertEqual(identity.uidentity.uuid, uuid)
        self.assertEqual(identity.source, 'scm')
        self.assertEqual(identity.name, 'John Smith')
        self.assertEqual(identity.email, 'jsmith@example.org')
        self.assertEqual(identity.username, 'jsmith')

    def test_add_multiple_identities(self):
        """Check if multiple identities can be added"""

        uidentity = UniqueIdentity.objects.create(uuid='AAAA')
        db.add_identity(self.trxl, uidentity, 'AAAA', 'scm',
                        name='John Smith',
                        email=None,
                        username=None)
        db.add_identity(self.trxl, uidentity, 'BBBB', 'its',
                        name=None,
                        email='jsmith@example.org',
                        username=None)
        db.add_identity(self.trxl, uidentity, 'CCCC', 'mls',
                        name=None,
                        email=None,
                        username='jsmith')

        uidentity = UniqueIdentity.objects.get(uuid='AAAA')
        identities = uidentity.identities.all()
        self.assertEqual(len(identities), 3)

        identity = identities[0]
        self.assertIsInstance(identity, Identity)
        self.assertEqual(identity.id, 'AAAA')
        self.assertEqual(identity.uidentity.uuid, 'AAAA')
        self.assertEqual(identity.source, 'scm')
        self.assertEqual(identity.name, 'John Smith')
        self.assertEqual(identity.email, None)
        self.assertEqual(identity.username, None)

        identity = identities[1]
        self.assertIsInstance(identity, Identity)
        self.assertEqual(identity.id, 'BBBB')
        self.assertEqual(identity.uidentity.uuid, 'AAAA')
        self.assertEqual(identity.source, 'its')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.email, 'jsmith@example.org')
        self.assertEqual(identity.username, None)

        identity = identities[2]
        self.assertIsInstance(identity, Identity)
        self.assertEqual(identity.id, 'CCCC')
        self.assertEqual(identity.uidentity.uuid, 'AAAA')
        self.assertEqual(identity.source, 'mls')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.email, None)
        self.assertEqual(identity.username, 'jsmith')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        uuid = '1234567890ABCDFE'
        uidentity = UniqueIdentity.objects.create(uuid=uuid)

        before_dt = datetime_utcnow()
        db.add_identity(self.trxl, uidentity, uuid, 'scm',
                        name='John Smith',
                        email='jsmith@example.org',
                        username='jsmith')
        after_dt = datetime_utcnow()

        # Tests
        uidentity = UniqueIdentity.objects.get(uuid=uuid)
        identity = Identity.objects.get(id=uuid)

        self.assertLessEqual(before_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_dt, uidentity.last_modified)

        self.assertLessEqual(before_dt, identity.last_modified)
        self.assertGreaterEqual(after_dt, identity.last_modified)

    def test_identity_id_none(self):
        """Check whether an identity with None as ID cannot be added"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, IDENTITY_ID_NONE_ERROR):
            db.add_identity(self.trxl, uidentity, None, 'scm')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_identity_id_empty(self):
        """Check whether an identity with empty ID cannot be added"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, IDENTITY_ID_EMPTY_ERROR):
            db.add_identity(self.trxl, uidentity, '', 'scm')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_identity_id_whitespaces(self):
        """Check whether an identity with an ID composed by whitespaces cannot be added"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, IDENTITY_ID_WHITESPACES_ERROR):
            db.add_identity(self.trxl, uidentity, '    ', 'scm')

        with self.assertRaisesRegex(ValueError, IDENTITY_ID_WHITESPACES_ERROR):
            db.add_identity(self.trxl, uidentity, '\t', 'scm')

        with self.assertRaisesRegex(ValueError, IDENTITY_ID_WHITESPACES_ERROR):
            db.add_identity(self.trxl, uidentity, '  \t', 'scm')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_source_none(self):
        """Check whether an identity with None as source cannot be added"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, SOURCE_NONE_ERROR):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', None)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_source_empty(self):
        """Check whether an identity with empty source cannot be added"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, SOURCE_EMPTY_ERROR):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', '')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_source_whitespaces(self):
        """Check whether an identity with a source composed by whitespaces cannot be added"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, SOURCE_WHITESPACES_ERROR):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', '  ')

        with self.assertRaisesRegex(ValueError, SOURCE_WHITESPACES_ERROR):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', '\t')

        with self.assertRaisesRegex(ValueError, SOURCE_WHITESPACES_ERROR):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', ' \t ')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_data_none_or_empty(self):
        """
        Check whether new identities cannot be added when identity data is None, empty
        or composed by whitespaces
        """
        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, IDENTITY_DATA_NONE_OR_EMPTY_ERROR):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', 'git',
                            name=None, email=None, username=None)

        expected = IDENTITY_DATA_EMPTY_ERROR.format(name='name')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', 'git',
                            name='', email='', username='')

        expected = IDENTITY_DATA_EMPTY_ERROR.format(name='email')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', 'git',
                            name=None, email='', username=None)

        expected = IDENTITY_DATA_WHITESPACES_ERROR.format(name='username')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', 'git',
                            name=None, email=None, username='  ')

        expected = IDENTITY_DATA_WHITESPACES_ERROR.format(name='username')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', 'git',
                            name=None, email=None, username='\t')

        expected = IDENTITY_DATA_EMPTY_ERROR.format(name='name')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', 'git',
                            name='', email=None, username='    ')

        expected = IDENTITY_DATA_EMPTY_ERROR.format(name='name')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', 'git',
                            name='', email=None, username='\t')

        expected = IDENTITY_DATA_WHITESPACES_ERROR.format(name='name')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', 'git',
                            name='   ', email=None, username='')

        expected = IDENTITY_DATA_WHITESPACES_ERROR.format(name='name')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', 'git',
                            name='\t', email=None, username='')

        expected = IDENTITY_DATA_WHITESPACES_ERROR.format(name='name')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, uidentity, '1234567890ABCDFE', 'git',
                            name=' \t ', email=None, username='')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_integrity_error_id(self):
        """Check whether identities with the same id cannot be inserted"""

        uuid = '1234567890ABCDFE'
        uidentity = UniqueIdentity.objects.create(uuid=uuid)

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_ID_ERROR):
            db.add_identity(self.trxl, uidentity, uuid, 'scm',
                            name='John Smith',
                            email='jsmith@example.org',
                            username='jsmith')
            db.add_identity(self.trxl, uidentity, uuid, 'scm',
                            name='John Smith',
                            email='jsmith@example.net',
                            username='jonhsmith')

    def test_integrity_error_unique_data(self):
        """Check whether identities with the same data cannot be inserted"""

        uidentity = UniqueIdentity.objects.create(uuid='AAAA')

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_ID_DATA_ERROR):
            db.add_identity(self.trxl, uidentity, 'AAAA', 'scm',
                            name='John Smith',
                            email='jsmith@example.org',
                            username='jsmith')
            db.add_identity(self.trxl, uidentity, 'BBBB', 'scm',
                            name='John Smith',
                            email='jsmith@example.org',
                            username='jsmith')

    def test_operations(self):
        """Check if the right operations are created when adding a new identity"""

        timestamp = datetime_utcnow()
        uuid = '1234567890ABCDFE'

        uidentity = UniqueIdentity.objects.create(uuid=uuid)
        identity = db.add_identity(self.trxl, uidentity, uuid, 'scm',
                                   name='John Smith',
                                   email='jsmith@example.org',
                                   username='jsmith')

        transactions = Transaction.objects.all()
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'identity')
        self.assertGreater(op1.timestamp, timestamp)
        self.assertEqual(op1.target, '1234567890ABCDFE')
        self.assertEqual(op1.trx, trx)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 6)
        self.assertEqual(op1_args['uidentity'], identity.uidentity.uuid)
        self.assertEqual(op1_args['identity_id'], identity.id)
        self.assertEqual(op1_args['source'], identity.source)
        self.assertEqual(op1_args['name'], identity.name)
        self.assertEqual(op1_args['email'], identity.email)
        self.assertEqual(op1_args['username'], identity.username)


class TestDeleteIdentity(TestCase):
    """Unit tests for delete_identity"""

    def setUp(self):
        """Load initial dataset"""

        self.trxl = TransactionsLog.open(name='delete_identity')

    def test_delete_identity(self):
        """Check whether it deletes an identity"""

        jsmith = UniqueIdentity.objects.create(uuid='AAAA')
        Identity.objects.create(id='0001', name='John Smith',
                                uidentity=jsmith)
        Identity.objects.create(id='0002', email='jsmith@example.net',
                                uidentity=jsmith)
        Identity.objects.create(id='0003', email='jsmith@example.org',
                                uidentity=jsmith)

        # Check data and remove identity
        jsmith.refresh_from_db()
        self.assertEqual(len(jsmith.identities.all()), 3)

        identity = Identity.objects.get(id='0002')
        db.delete_identity(self.trxl, identity)

        # Tests
        with self.assertRaises(ObjectDoesNotExist):
            Identity.objects.get(id='0002')

        jsmith.refresh_from_db()
        self.assertEqual(len(jsmith.identities.all()), 2)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        jsmith = UniqueIdentity.objects.create(uuid='AAAA')
        Identity.objects.create(id='0001', name='John Smith',
                                uidentity=jsmith)
        Identity.objects.create(id='0002', email='jsmith@example.net',
                                uidentity=jsmith)
        Identity.objects.create(id='0003', email='jsmith@example.org',
                                uidentity=jsmith)

        before_dt = datetime_utcnow()
        identity = Identity.objects.get(id='0001')
        db.delete_identity(self.trxl, identity)
        after_dt = datetime_utcnow()

        # Tests
        uidentity = UniqueIdentity.objects.get(uuid='AAAA')
        self.assertEqual(len(uidentity.identities.all()), 2)
        self.assertLessEqual(before_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_dt, uidentity.last_modified)

        identity = Identity.objects.get(id='0002')
        self.assertLessEqual(identity.last_modified, before_dt)
        self.assertLessEqual(identity.last_modified, after_dt)

    def test_operations(self):
        """Check if the right operations are created when deleting an identity"""

        # Set the initial dataset
        timestamp = datetime_utcnow()
        jsmith = UniqueIdentity.objects.create(uuid='AAAA')
        Identity.objects.create(id='0001', name='John Smith',
                                uidentity=jsmith)
        Identity.objects.create(id='0002', email='jsmith@example.net',
                                uidentity=jsmith)
        Identity.objects.create(id='0003', email='jsmith@example.org',
                                uidentity=jsmith)
        jsmith.refresh_from_db()

        # Get the identity and delete it
        identity = Identity.objects.get(id='0002')
        db.delete_identity(self.trxl, identity)

        transactions = Transaction.objects.filter(name='delete_identity')
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'identity')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, '0002')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['identity'], '0002')


class TestUpdateProfile(TestCase):
    """Unit tests for update_profile"""

    def setUp(self):
        """Load initial dataset"""

        self.trxl = TransactionsLog.open(name='update_profile')

    def test_update_profile(self):
        """Check if it updates a profile"""

        uuid = '1234567890ABCDFE'

        country = Country.objects.create(code='US',
                                         name='United States of America',
                                         alpha3='USA')
        jsmith = UniqueIdentity.objects.create(uuid=uuid)
        Profile.objects.create(uidentity=jsmith)

        uidentity = db.update_profile(self.trxl, jsmith,
                                      name='Smith, J.', email='jsmith@example.net',
                                      is_bot=True, country_code='US',
                                      gender='male', gender_acc=98)

        # Tests
        self.assertIsInstance(uidentity, UniqueIdentity)
        self.assertEqual(uidentity, jsmith)

        profile = uidentity.profile
        self.assertEqual(profile.name, 'Smith, J.')
        self.assertEqual(profile.email, 'jsmith@example.net')
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.country, country)
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 98)

        # Check database object
        uidentity_db = UniqueIdentity.objects.get(uuid=uuid)
        self.assertEqual(profile, uidentity_db.profile)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        uuid = '1234567890ABCDFE'

        uidentity = UniqueIdentity.objects.create(uuid=uuid)
        Profile.objects.create(uidentity=uidentity)

        before_dt = datetime_utcnow()
        db.update_profile(self.trxl, uidentity,
                          name='John Smith', email='jsmith@example.net')
        after_dt = datetime_utcnow()

        # Tests
        uidentity = UniqueIdentity.objects.get(uuid=uuid)
        self.assertLessEqual(before_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_dt, uidentity.last_modified)

    def test_name_email_empty(self):
        """Check if name and email are set to None when an empty string is given"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        Profile.objects.create(uidentity=uidentity)

        uidentity = db.update_profile(self.trxl, uidentity, name='', email='')
        profile = uidentity.profile
        self.assertEqual(profile.name, None)
        self.assertEqual(profile.email, None)

    def test_is_bot_invalid_type(self):
        """Check type values of is_bot parameter"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        Profile.objects.create(uidentity=uidentity)

        with self.assertRaisesRegex(ValueError, IS_BOT_VALUE_ERROR):
            db.update_profile(self.trxl, uidentity, is_bot=1)

        with self.assertRaisesRegex(ValueError, IS_BOT_VALUE_ERROR):
            db.update_profile(self.trxl, uidentity, is_bot='True')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_country_code_not_valid(self):
        """Check if it fails when the given country is not valid"""

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        Profile.objects.create(uidentity=uidentity)

        msg = COUNTRY_CODE_ERROR.format(code='JKL')

        with self.assertRaisesRegex(ValueError, msg):
            db.update_profile(self.trxl, uidentity, country_code='JKL')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_gender_not_given(self):
        """Check if it fails when gender_acc is given but not the gender"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        Profile.objects.create(uidentity=uidentity)

        with self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_ERROR):
            db.update_profile(self.trxl, uidentity, gender_acc=100)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_gender_acc_invalid_type(self):
        """Check type values of gender_acc parameter"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        Profile.objects.create(uidentity=uidentity)

        with self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_TYPE_ERROR):
            db.update_profile(self.trxl, uidentity,
                              gender='male', gender_acc=10.0)

        with self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_TYPE_ERROR):
            db.update_profile(self.trxl, uidentity,
                              gender='male', gender_acc='100')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_gender_acc_invalid_range(self):
        """Check if it fails when gender_acc is given but not the gender"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        Profile.objects.create(uidentity=uidentity)

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='-1')

        with self.assertRaisesRegex(ValueError, msg):
            db.update_profile(self.trxl, uidentity,
                              gender='male', gender_acc=-1)

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='0')

        with self.assertRaisesRegex(ValueError, msg):
            db.update_profile(self.trxl, uidentity,
                              gender='male', gender_acc=0)

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='101')

        with self.assertRaisesRegex(ValueError, msg):
            db.update_profile(self.trxl, uidentity,
                              gender='male', gender_acc=101)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_operations(self):
        """Check if the right operations are created when updating a profile"""

        timestamp = datetime_utcnow()

        # Load initial dataset
        uuid = '1234567890ABCDFE'
        country = Country.objects.create(code='US',
                                         name='United States of America',
                                         alpha3='USA')
        jsmith = UniqueIdentity.objects.create(uuid=uuid)
        Profile.objects.create(uidentity=jsmith)

        # Update the profile
        db.update_profile(self.trxl, jsmith,
                          name='Smith, J.', email='jsmith@example.net',
                          is_bot=True, country_code='US',
                          gender='male', gender_acc=98)

        transactions = Transaction.objects.filter(name='update_profile')
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'profile')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, '1234567890ABCDFE')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 7)
        self.assertEqual(op1_args['uidentity'], uuid)
        self.assertEqual(op1_args['name'], 'Smith, J.')
        self.assertEqual(op1_args['email'], 'jsmith@example.net')
        self.assertEqual(op1_args['is_bot'], True)
        self.assertEqual(op1_args['country_code'], 'US')
        self.assertEqual(op1_args['gender'], 'male')
        self.assertEqual(op1_args['gender_acc'], 98)


class TestAddEnrollment(TestCase):
    """Unit tests for add_enrollment"""

    def setUp(self):
        """Load initial dataset"""

        self.trxl = TransactionsLog.open(name='enroll')

    def test_enroll(self):
        """Check if a new enrollment is added"""

        uuid = '1234567890ABCDFE'

        uidentity = UniqueIdentity.objects.create(uuid=uuid)
        org = Organization.objects.create(name='Example')

        start = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        end = datetime.datetime(2000, 1, 1, tzinfo=UTC)

        enrollment = db.add_enrollment(self.trxl, uidentity, org, start=start, end=end)

        self.assertIsInstance(enrollment, Enrollment)
        self.assertEqual(enrollment.start, start)
        self.assertEqual(enrollment.end, end)
        self.assertEqual(enrollment.uidentity, uidentity)
        self.assertEqual(enrollment.organization, org)

        uidentity = UniqueIdentity.objects.get(uuid=uuid)

        enrollments = uidentity.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment_db = enrollments[0]
        self.assertEqual(enrollment, enrollment_db)

    def test_add_multiple_enrollments(self):
        """Check if multiple enrollments can be added"""

        uuid = '1234567890ABCDFE'
        name = 'Example'

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        org = Organization.objects.create(name='Example')

        db.add_enrollment(self.trxl, uidentity, org, start=datetime.datetime(1999, 1, 1, tzinfo=UTC))
        db.add_enrollment(self.trxl, uidentity, org, end=datetime.datetime(2005, 1, 1, tzinfo=UTC))
        db.add_enrollment(self.trxl, uidentity, org, start=datetime.datetime(2013, 1, 1, tzinfo=UTC),
                          end=datetime.datetime(2014, 1, 1, tzinfo=UTC))

        # Tests
        uidentity = UniqueIdentity.objects.get(uuid=uuid)

        enrollments = uidentity.enrollments.all()
        self.assertEqual(len(enrollments), 3)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, MIN_PERIOD_DATE)
        self.assertEqual(enrollment.end, datetime.datetime(2005, 1, 1, tzinfo=UTC))
        self.assertIsInstance(enrollment.uidentity, UniqueIdentity)
        self.assertEqual(enrollment.uidentity.uuid, uuid)
        self.assertIsInstance(enrollment.organization, Organization)
        self.assertEqual(enrollment.organization.name, name)

        enrollment = enrollments[1]
        self.assertEqual(enrollment.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, MAX_PERIOD_DATE)
        self.assertIsInstance(enrollment.uidentity, UniqueIdentity)
        self.assertEqual(enrollment.uidentity.uuid, uuid)
        self.assertIsInstance(enrollment.organization, Organization)
        self.assertEqual(enrollment.organization.name, name)

        enrollment = enrollments[2]
        self.assertEqual(enrollment.start, datetime.datetime(2013, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))
        self.assertIsInstance(enrollment.uidentity, UniqueIdentity)
        self.assertEqual(enrollment.uidentity.uuid, uuid)
        self.assertIsInstance(enrollment.organization, Organization)
        self.assertEqual(enrollment.organization.name, name)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        org = Organization.objects.create(name='Example')

        before_dt = datetime_utcnow()
        db.add_enrollment(self.trxl, uidentity, org, start=MIN_PERIOD_DATE, end=MAX_PERIOD_DATE)
        after_dt = datetime_utcnow()

        # Tests
        uidentity = UniqueIdentity.objects.get(uuid='1234567890ABCDFE')
        self.assertLessEqual(before_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_dt, uidentity.last_modified)

    def test_from_date_none(self):
        """Check if an enrollment cannot be added when from_date is None"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        org = Organization.objects.create(name='Example')

        with self.assertRaisesRegex(ValueError, START_DATE_NONE_ERROR):
            db.add_enrollment(self.trxl, uidentity, org,
                              start=None, end=datetime.datetime(1999, 1, 1, tzinfo=UTC))

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_to_date_none(self):
        """Check if an enrollment cannot be added when to_date is None"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        org = Organization.objects.create(name='Example')

        with self.assertRaisesRegex(ValueError, END_DATE_NONE_ERROR):
            db.add_enrollment(self.trxl, uidentity, org,
                              start=datetime.datetime(2001, 1, 1, tzinfo=UTC), end=None)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_period_invalid(self):
        """Check whether enrollments cannot be added giving invalid period ranges"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        org = Organization.objects.create(name='Example')

        data = {
            'start': r'2001-01-01 00:00:00\+00:00',
            'end': r'1999-01-01 00:00:00\+00:00'
        }
        msg = PERIOD_INVALID_ERROR.format(**data)

        with self.assertRaisesRegex(ValueError, msg):
            db.add_enrollment(self.trxl, uidentity, org,
                              start=datetime.datetime(2001, 1, 1, tzinfo=UTC),
                              end=datetime.datetime(1999, 1, 1, tzinfo=UTC))

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_period_out_of_bounds(self):
        """Check whether enrollments cannot be added giving a range out of bounds"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        org = Organization.objects.create(name='Example')

        data = {
            'type': 'start',
            'date': r'1899-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(ValueError, msg):
            db.add_enrollment(self.trxl, uidentity, org,
                              start=datetime.datetime(1899, 12, 31, 23, 59, 59, tzinfo=UTC))

        data = {
            'type': 'start',
            'date': r'2100-01-01 00:00:01\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(ValueError, msg):
            db.add_enrollment(self.trxl, uidentity, org,
                              start=datetime.datetime(2100, 1, 1, 0, 0, 1, tzinfo=UTC))

        data = {
            'type': 'end',
            'date': r'2100-01-01 00:00:01\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(ValueError, msg):
            db.add_enrollment(self.trxl, uidentity, org,
                              end=datetime.datetime(2100, 1, 1, 0, 0, 1, tzinfo=UTC))

        data = {
            'type': 'end',
            'date': r'1899-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(ValueError, msg):
            db.add_enrollment(self.trxl, uidentity, org,
                              end=datetime.datetime(1899, 12, 31, 23, 59, 59, tzinfo=UTC))

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_operations(self):
        """Check if the right operations are created when deleting a domain"""

        timestamp = datetime_utcnow()
        uuid = '1234567890ABCDFE'

        # Load initial dataset
        uidentity = UniqueIdentity.objects.create(uuid=uuid)
        org = Organization.objects.create(name='Example')

        start = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        end = datetime.datetime(2000, 1, 1, tzinfo=UTC)

        # Add the enrollment
        db.add_enrollment(self.trxl, uidentity, org, start=start, end=end)

        transactions = Transaction.objects.filter(name='enroll')
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'enrollment')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, '1234567890ABCDFE')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 4)
        self.assertEqual(op1_args['uidentity'], uuid)
        self.assertEqual(op1_args['organization'], org.name)
        self.assertEqual(op1_args['start'], str(datetime_to_utc(datetime.datetime(1999, 1, 1))))
        self.assertEqual(op1_args['end'], str(datetime_to_utc(datetime.datetime(2000, 1, 1))))


class TestDeleteEnrollment(TestCase):
    """Unit tests for delete_enrollment"""

    def setUp(self):
        """Load initial dataset"""

        self.trxl = TransactionsLog.open(name='withdraw')

    def test_delete_enrollment(self):
        """Check whether it deletes an enrollment"""

        from_date = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        first_period = datetime.datetime(2000, 1, 1, tzinfo=UTC)
        second_period = datetime.datetime(2010, 1, 1, tzinfo=UTC)
        to_date = datetime.datetime(2010, 1, 1, tzinfo=UTC)

        jsmith = UniqueIdentity.objects.create(uuid='AAAA')
        Identity.objects.create(id='0001', name='John Smith',
                                uidentity=jsmith)

        example_org = Organization.objects.create(name='Example')
        Enrollment.objects.create(uidentity=jsmith, organization=example_org,
                                  start=from_date, end=first_period)
        enrollment = Enrollment.objects.create(uidentity=jsmith, organization=example_org,
                                               start=second_period, end=to_date)

        bitergia_org = Organization.objects.create(name='Bitergia')
        Enrollment.objects.create(uidentity=jsmith, organization=bitergia_org,
                                  start=first_period, end=second_period)

        # Check data and remove enrollment
        jsmith.refresh_from_db()
        self.assertEqual(len(jsmith.identities.all()), 1)
        self.assertEqual(len(jsmith.enrollments.all()), 3)

        db.delete_enrollment(self.trxl, enrollment)

        # Tests
        with self.assertRaises(ObjectDoesNotExist):
            Enrollment.objects.get(uidentity=jsmith,
                                   start=second_period,
                                   end=to_date)

        enrollments = Enrollment.objects.filter(organization__name='Example')
        self.assertEqual(len(enrollments), 1)

        enrollments = Enrollment.objects.filter(organization__name='Bitergia')
        self.assertEqual(len(enrollments), 1)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        from_date = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        to_date = datetime.datetime(2000, 1, 1, tzinfo=UTC)

        jsmith = UniqueIdentity.objects.create(uuid='AAAA')
        Identity.objects.create(id='0001', name='John Smith',
                                uidentity=jsmith)

        example_org = Organization.objects.create(name='Example')
        enrollment = Enrollment.objects.create(uidentity=jsmith, organization=example_org,
                                               start=from_date, end=to_date)

        # Tests
        before_dt = datetime_utcnow()
        db.delete_enrollment(self.trxl, enrollment)
        after_dt = datetime_utcnow()

        jsmith = UniqueIdentity.objects.get(uuid='AAAA')
        self.assertLessEqual(before_dt, jsmith.last_modified)
        self.assertGreaterEqual(after_dt, jsmith.last_modified)

    def test_operations(self):
        """Check if the right operations are created when deleting an enrollment"""

        timestamp = datetime_utcnow()

        # Load intial dataset
        from_date = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        first_period = datetime.datetime(2000, 1, 1, tzinfo=UTC)
        second_period = datetime.datetime(2010, 1, 1, tzinfo=UTC)
        to_date = datetime.datetime(2010, 1, 1, tzinfo=UTC)

        jsmith = UniqueIdentity.objects.create(uuid='AAAA')
        Identity.objects.create(id='0001', name='John Smith',
                                uidentity=jsmith)

        example_org = Organization.objects.create(name='Example')
        Enrollment.objects.create(uidentity=jsmith, organization=example_org,
                                  start=from_date, end=first_period)
        enrollment = Enrollment.objects.create(uidentity=jsmith, organization=example_org,
                                               start=second_period, end=to_date)

        bitergia_org = Organization.objects.create(name='Bitergia')
        Enrollment.objects.create(uidentity=jsmith, organization=bitergia_org,
                                  start=first_period, end=second_period)
        jsmith.refresh_from_db()

        # Remove enrollment
        db.delete_enrollment(self.trxl, enrollment)

        transactions = Transaction.objects.filter(name='withdraw')
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'enrollment')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, 'AAAA')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 4)
        self.assertEqual(op1_args['uuid'], 'AAAA')
        self.assertEqual(op1_args['organization'], 'Example')
        self.assertEqual(op1_args['start'], str(datetime_to_utc(second_period)))
        self.assertEqual(op1_args['end'], str(datetime_to_utc(to_date)))


class TestMoveIdentity(TestCase):
    """Unit tests for move_identity"""

    def setUp(self):
        """Load initial dataset"""

        self.trxl = TransactionsLog.open(name='move_identity')

    def test_move_identity(self):
        """Test when an identity is moved to a unique identity"""

        from_uid = UniqueIdentity.objects.create(uuid='AAAA')
        to_uid = UniqueIdentity.objects.create(uuid='BBBB')

        identity = Identity.objects.create(id='0001', name='John Smith',
                                           uidentity=from_uid)

        # Move identity and check results
        uidentity = db.move_identity(self.trxl, identity, to_uid)

        self.assertIsInstance(uidentity, UniqueIdentity)
        self.assertEqual(uidentity, to_uid)

        identities = uidentity.identities.all()
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity.id, '0001')
        self.assertEqual(identity.name, 'John Smith')

        # Check if the database stored those changes
        uidentity = UniqueIdentity.objects.get(uuid='AAAA')
        self.assertEqual(len(uidentity.identities.all()), 0)

        uidentity = UniqueIdentity.objects.get(uuid='BBBB')
        identities = uidentity.identities.all()
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity.id, '0001')
        self.assertEqual(identity.name, 'John Smith')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        from_uid = UniqueIdentity.objects.create(uuid='AAAA')
        to_uid = UniqueIdentity.objects.create(uuid='BBBB')

        identity = Identity.objects.create(id='0001', name='John Smith',
                                           uidentity=from_uid)

        # Move identity and check results
        before_dt = datetime_utcnow()
        db.move_identity(self.trxl, identity, to_uid)
        after_dt = datetime_utcnow()

        # Tests
        uidentity = UniqueIdentity.objects.get(uuid='AAAA')
        self.assertLessEqual(before_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_dt, uidentity.last_modified)

        uidentity = UniqueIdentity.objects.get(uuid='BBBB')
        self.assertLessEqual(before_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_dt, uidentity.last_modified)

        identity = Identity.objects.get(id='0001')
        self.assertLessEqual(before_dt, identity.last_modified)
        self.assertGreaterEqual(after_dt, identity.last_modified)

    def test_equal_related_unique_identity(self):
        """Test that all remains the same when uidentity is the unique identity related to identity'"""

        from_uid = UniqueIdentity.objects.create(uuid='AAAA')
        identity = Identity.objects.create(id='0001', name='John Smith',
                                           uidentity=from_uid)
        # Move identity and check results
        with self.assertRaisesRegex(ValueError, MOVE_ERROR):
            db.move_identity(self.trxl, identity, from_uid)

        uidentity = UniqueIdentity.objects.get(uuid='AAAA')
        self.assertEqual(len(uidentity.identities.all()), 1)

    def test_operations(self):
        """Check if the right operations are created when moving an identity"""

        timestamp = datetime_utcnow()

        from_uid = UniqueIdentity.objects.create(uuid='AAAA')
        to_uid = UniqueIdentity.objects.create(uuid='BBBB')

        identity = Identity.objects.create(id='0001', name='John Smith',
                                           uidentity=from_uid)

        # Move identity
        db.move_identity(self.trxl, identity, to_uid)

        transactions = Transaction.objects.filter(name='move_identity')
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'identity')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, '0001')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 2)
        self.assertEqual(op1_args['identity'], '0001')
        self.assertEqual(op1_args['uidentity'], 'BBBB')
