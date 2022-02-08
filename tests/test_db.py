#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2021 Bitergia
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

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from grimoirelab_toolkit.datetime import datetime_utcnow, datetime_to_utc

from sortinghat.core import db
from sortinghat.core.context import SortingHatContext
from sortinghat.core.errors import AlreadyExistsError, NotFoundError, LockedIdentityError
from sortinghat.core.log import TransactionsLog
from sortinghat.core.models import (MIN_PERIOD_DATE,
                                    MAX_PERIOD_DATE,
                                    Organization,
                                    Team,
                                    Group,
                                    Domain,
                                    Country,
                                    Individual,
                                    Identity,
                                    Profile,
                                    Enrollment,
                                    Transaction,
                                    Operation)


DUPLICATED_ORG_ERROR = "Organization 'Example' already exists in the registry"
DUPLICATED_DOM_ERROR = "Domain 'example.org' already exists in the registry"
DUPLICATED_TEAM_ERROR = "Team 'error_team' already exists in the registry"
DUPLICATED_INDIVIDUAL_ERROR = "Individual '1234567890ABCDFE' already exists in the registry"
DUPLICATED_ID_ERROR = "Identity '1234567890ABCDFE' already exists in the registry"
DUPLICATED_ID_DATA_ERROR = "Identity 'John Smith-jsmith@example.org-jsmith-scm' already exists in the registry"
DUPLICATED_ENROLLMENT_ERROR = r"Identity '1234567890ABCDFE-.+' already exists in the registry"
NAME_NONE_ERROR = "'name' cannot be None"
NAME_EMPTY_ERROR = "'name' cannot be an empty string"
NAME_WHITESPACES_ERROR = "'name' cannot be composed by whitespaces only"
DOMAIN_NAME_NONE_ERROR = "'domain_name' cannot be None"
DOMAIN_NAME_EMPTY_ERROR = "'domain_name' cannot be an empty string"
DOMAIN_NAME_WHITESPACES_ERROR = "'domain_name' cannot be composed by whitespaces only"
DOMAIN_VALUE_ERROR = "field value must be a string; int given"
TOP_DOMAIN_VALUE_ERROR = "'is_top_domain' must have a boolean value"
MK_NONE_ERROR = "'mk' cannot be None"
MK_EMPTY_ERROR = "'mk' cannot be an empty string"
MK_WHITESPACES_ERROR = "'mk' cannot be composed by whitespaces only"
UUID_NONE_ERROR = "'uuid' cannot be None"
UUID_EMPTY_ERROR = "'uuid' cannot be an empty string"
UUID_WHITESPACES_ERROR = "'uuid' cannot be composed by whitespaces only"
SOURCE_NONE_ERROR = "'source' cannot be None"
SOURCE_EMPTY_ERROR = "'source' cannot be an empty string"
SOURCE_WHITESPACES_ERROR = "'source' cannot be composed by whitespaces only"
IDENTITY_DATA_NONE_OR_EMPTY_ERROR = "identity data cannot be None or empty"
IDENTITY_DATA_EMPTY_ERROR = "'{name}' cannot be an empty string"
IDENTITY_DATA_NONE_ERROR = "'{name}' cannot be None"
IDENTITY_DATA_WHITESPACES_ERROR = "'{name}' cannot be composed by whitespaces only"
INDIVIDUAL_NOT_FOUND_ERROR = "zyxwuv not found in the registry"
IDENTITY_NOT_FOUND_ERROR = "zyxwuv not found in the registry"
ORGANIZATION_NOT_FOUND_ERROR = "Bitergia not found in the registry"
GROUP_NOT_FOUND_ERROR = "Bitergia not found in the registry"
DOMAIN_NOT_FOUND_ERROR = "example.net not found in the registry"
TEAM_NOT_FOUND_ERROR = "subTeam not found in the registry"
TEAM_NAME_NONE_ERROR = "'team_name' cannot be None"
TEAM_NAME_EMPTY_ERROR = "'{var}' cannot be an empty string"
TEAM_NAME_WHITESPACE_ERROR = "'team_name' cannot be composed by whitespaces only"
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
INDIVIDUAL_LOCKED_ERROR = "Individual {mk} is locked"


class TestFindIndividual(TestCase):
    """Unit tests for find_individual"""

    def test_find_individual(self):
        """Test if an individual is found by its main key"""

        mk = 'abcdefghijklmnopqrstuvwxyz'
        Individual.objects.create(mk=mk)

        individual = db.find_individual(mk)
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, mk)

    def test_individual_not_found(self):
        """Test whether it raises an exception when the individual is not found"""

        mk = 'abcdefghijklmnopqrstuvwxyz'
        Individual.objects.create(mk=mk)

        with self.assertRaisesRegex(NotFoundError, INDIVIDUAL_NOT_FOUND_ERROR):
            db.find_individual('zyxwuv')


class TestFindIndividualbyUUID(TestCase):
    """Unit tests for find_individual_by_uuid"""

    def test_find_individual_with_mk(self):
        """Test if it finds an individual giving its mk"""

        mk = 'abcdefghijklmnopqrstuvwxyz'
        Individual.objects.create(mk=mk)

        individual = db.find_individual_by_uuid(mk)
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, mk)

    def test_find_individual_with_uuid(self):
        """Test if it finds an individual giving the uuid of one of its identities"""

        mk = 'abcdefghijklmnopqrstuvwxyz'
        uuid = '1234567890'
        individual = Individual.objects.create(mk=mk)
        Identity.objects.create(uuid=mk, source='scm', individual=individual)
        Identity.objects.create(uuid=uuid, source='mls', individual=individual)

        individual = db.find_individual_by_uuid(uuid)
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, mk)

    def test_individual_not_found(self):
        """Test whether it raises an exception when the individual is not found"""

        mk = 'abcdefghijklmnopqrstuvwxyz'
        uuid = '1234567890'
        individual = Individual.objects.create(mk=mk)
        Identity.objects.create(uuid=mk, source='scm', individual=individual)
        Identity.objects.create(uuid=uuid, source='mls', individual=individual)

        with self.assertRaisesRegex(NotFoundError, INDIVIDUAL_NOT_FOUND_ERROR):
            db.find_individual_by_uuid('zyxwuv')


class TestFindIdentity(TestCase):
    """Unit tests for find_identity"""

    def test_find_identity(self):
        """Test if an identity is found by its UUID"""

        mk = 'abcdefghijklmnopqrstuvwxyz'
        individual = Individual.objects.create(mk=mk)
        Identity.objects.create(uuid=mk, source='scm', individual=individual)

        identity = db.find_identity(mk)
        self.assertIsInstance(identity, Identity)
        self.assertEqual(identity.uuid, mk)

    def test_identity_not_found(self):
        """Test whether it raises an exception when the identity is not found"""

        mk = 'abcdefghijklmnopqrstuvwxyz'
        individual = Individual.objects.create(mk=mk)
        Identity.objects.create(uuid=mk, source='scm', individual=individual)

        with self.assertRaisesRegex(NotFoundError, IDENTITY_NOT_FOUND_ERROR):
            db.find_identity('zyxwuv')


class TestFindOrganization(TestCase):
    """Unit tests for find_organization"""

    def test_find_organization(self):
        """Test if an organization is found by its name"""

        name = 'Example'
        Organization.add_root(name=name)

        organization = db.find_organization(name)
        self.assertIsInstance(organization, Organization)
        self.assertEqual(organization.name, name)

    def test_organization_not_found(self):
        """Test whether it raises an exception when the organization is not found"""

        name = 'Example'
        Organization.add_root(name=name)

        with self.assertRaisesRegex(NotFoundError, ORGANIZATION_NOT_FOUND_ERROR):
            db.find_organization('Bitergia')


class TestFindTeam(TestCase):
    """Unit tests for find_team"""

    def setUp(self) -> None:
        self.org = Organization.add_root(name='Example')

    def test_find_team(self):
        """Check if a team is found by its name and organization"""

        Group.add_root(name='Example Subteam', parent_org=self.org, type='team')
        team = db.find_team(team_name='Example Subteam', organization=self.org)

        self.assertIsInstance(team, Team)
        self.assertEqual(team.parent_org.name, 'Example')
        self.assertEqual(team.name, 'Example Subteam')
        self.assertEqual(team.get_parent(), None)

    def test_team_not_found(self):
        """Check if an error is raise if team is not found"""

        with self.assertRaisesRegex(NotFoundError, TEAM_NOT_FOUND_ERROR):
            db.find_team('subTeam', self.org)

    def test_team_name_none(self):
        """Check if finding team fails when team name is `None`"""

        with self.assertRaisesRegex(ValueError, TEAM_NAME_NONE_ERROR):
            db.find_team(None, self.org)

    def test_team_name_empty(self):
        """Check if finding team fails when team name is empty"""

        with self.assertRaisesRegex(ValueError, TEAM_NAME_EMPTY_ERROR.format(var="team_name")):
            db.find_team('', self.org)

    def test_team_name_whitespaces(self):
        """Check if finding team fails when team name is composed by whitespaces"""

        with self.assertRaisesRegex(ValueError, TEAM_NAME_WHITESPACE_ERROR):
            db.find_team('    ', self.org)

        with self.assertRaisesRegex(ValueError, TEAM_NAME_WHITESPACE_ERROR):
            db.find_team('\t', self.org)

        with self.assertRaisesRegex(ValueError, TEAM_NAME_WHITESPACE_ERROR):
            db.find_team('  \t  ', self.org)


class TestFindGroup(TestCase):
    """Unit tests for find_group"""

    def setUp(self):
        """Load initial dataset"""

        self.org = Organization.add_root(name='Example Org')
        Team.add_root(name='Example Team', parent_org=self.org)
        Team.add_root(name='Example Group')

    def test_find_organization(self):
        """Test if an organization is found by its name"""

        name = 'Example Org'

        group = db.find_group(name)
        self.assertIsInstance(group, Group)
        self.assertEqual(group.type, 'organization')
        self.assertEqual(group.name, name)

    def test_find_team(self):
        """Test if a team is found by its name and parent organization"""

        name = 'Example Team'

        group = db.find_group(name, 'Example Org')
        self.assertIsInstance(group, Group)
        self.assertEqual(group.type, 'team')
        self.assertEqual(group.name, name)
        self.assertEqual(group.parent_org.name, self.org.name)

    def test_find_group(self):
        """Test if a team with no parent organization is found"""

        name = 'Example Group'

        group = db.find_group(name)
        self.assertIsInstance(group, Group)
        self.assertEqual(group.type, 'team')
        self.assertEqual(group.name, name)
        self.assertEqual(group.parent_org, None)

    def test_group_not_found(self):
        """Test whether it raises an exception when the group is not found"""

        with self.assertRaisesRegex(NotFoundError, GROUP_NOT_FOUND_ERROR):
            db.find_group('Bitergia')


class TestFindDomain(TestCase):
    """Unit tests for find_domain"""

    def setUp(self):
        """Load initial dataset"""

        org = Organization.add_root(name='Example')
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

        individual_a = Individual.objects.create(mk='AAAA')
        individual_b = Individual.objects.create(mk='BBBB')

        example_org = Organization.add_root(name='Example')
        bitergia_org = Organization.add_root(name='Bitergia')

        # Example enrollments
        Enrollment.objects.create(individual=individual_a, group=example_org,
                                  start=datetime.datetime(1999, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2002, 1, 1, tzinfo=UTC))
        Enrollment.objects.create(individual=individual_a, group=example_org,
                                  start=datetime.datetime(2003, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2005, 1, 1, tzinfo=UTC))
        Enrollment.objects.create(individual=individual_a, group=example_org,
                                  start=datetime.datetime(2008, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2010, 1, 1, tzinfo=UTC))

        Enrollment.objects.create(individual=individual_b, group=example_org,
                                  start=datetime.datetime(2000, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2015, 1, 1, tzinfo=UTC))

        # Bitergia enrollments
        Enrollment.objects.create(individual=individual_a, group=bitergia_org,
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
        self.assertEqual(rol.individual, individual_a)
        self.assertEqual(rol.group, example_org)
        self.assertEqual(rol.start, datetime.datetime(2003, 1, 1, tzinfo=UTC))
        self.assertEqual(rol.end, datetime.datetime(2005, 1, 1, tzinfo=UTC))

        rol = enrollments[1]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.individual, individual_a)
        self.assertEqual(rol.group, example_org)
        self.assertEqual(rol.start, datetime.datetime(2008, 1, 1, tzinfo=UTC))
        self.assertEqual(rol.end, datetime.datetime(2010, 1, 1, tzinfo=UTC))

    def test_no_enrollments_in_period(self):
        """Test if an empty set is returned when there are not enrollments for a given period"""

        individual_a = Individual.objects.create(mk='AAAA')
        example_org = Organization.add_root(name='Example')

        Enrollment.objects.create(individual=individual_a, group=example_org,
                                  start=datetime.datetime(1999, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2000, 1, 1, tzinfo=UTC))

        # Tests
        enrollments = db.search_enrollments_in_period('AAAA', 'Example',
                                                      from_date=datetime.datetime(2000, 2, 1, tzinfo=UTC),
                                                      to_date=datetime.datetime(2009, 1, 1, tzinfo=UTC))
        self.assertEqual(len(enrollments), 0)

    def test_no_identity(self):
        """Test if an empty set is returned when there identity does not exist"""

        individual_a = Individual.objects.create(mk='AAAA')
        example_org = Organization.add_root(name='Example')

        Enrollment.objects.create(individual=individual_a, group=example_org,
                                  start=datetime.datetime(1999, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2000, 1, 1, tzinfo=UTC))

        # Tests
        enrollments = db.search_enrollments_in_period('BBBB', 'Example',
                                                      from_date=datetime.datetime(1999, 1, 1, tzinfo=UTC),
                                                      to_date=datetime.datetime(2000, 1, 1, tzinfo=UTC))
        self.assertEqual(len(enrollments), 0)

    def test_no_organization(self):
        """Test if an empty set is returned when there organization does not exist"""

        individual_a = Individual.objects.create(mk='AAAA')
        example_org = Organization.add_root(name='Example')

        Enrollment.objects.create(individual=individual_a, group=example_org,
                                  start=datetime.datetime(1999, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2000, 1, 1, tzinfo=UTC))

        # Tests
        enrollments = db.search_enrollments_in_period('AAAA', 'Bitergia',
                                                      from_date=datetime.datetime(1999, 1, 1, tzinfo=UTC),
                                                      to_date=datetime.datetime(2000, 1, 1, tzinfo=UTC))
        self.assertEqual(len(enrollments), 0)

    def test_search_enrollments_in_team(self):
        individual_a = Individual.objects.create(mk='AAAA')
        example_org = Organization.add_root(name='Example')
        team1 = Team.add_root(name='Team 1', parent_org=example_org)
        team2 = Team.add_root(name='Team 2', parent_org=example_org)

        Enrollment.objects.create(individual=individual_a, group=team1,
                                  start=datetime.datetime(1999, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2000, 1, 1, tzinfo=UTC))
        Enrollment.objects.create(individual=individual_a, group=team1,
                                  start=datetime.datetime(2002, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2004, 1, 1, tzinfo=UTC))
        Enrollment.objects.create(individual=individual_a, group=team1,
                                  start=datetime.datetime(2006, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2008, 1, 1, tzinfo=UTC))

        Enrollment.objects.create(individual=individual_a, group=team2,
                                  start=datetime.datetime(2001, 1, 1, tzinfo=UTC),
                                  end=datetime.datetime(2006, 1, 1, tzinfo=UTC))

        # Tests
        enrollments = db.search_enrollments_in_period('AAAA', 'Team 1',
                                                      parent_org='Example',
                                                      from_date=datetime.datetime(2003, 1, 1, tzinfo=UTC),
                                                      to_date=datetime.datetime(2009, 1, 1, tzinfo=UTC))

        self.assertEqual(len(enrollments), 2)

        rol = enrollments[0]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.individual, individual_a)
        self.assertEqual(rol.group, team1)
        self.assertEqual(rol.start, datetime.datetime(2002, 1, 1, tzinfo=UTC))
        self.assertEqual(rol.end, datetime.datetime(2004, 1, 1, tzinfo=UTC))

        rol = enrollments[1]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.individual, individual_a)
        self.assertEqual(rol.group, team1)
        self.assertEqual(rol.start, datetime.datetime(2006, 1, 1, tzinfo=UTC))
        self.assertEqual(rol.end, datetime.datetime(2008, 1, 1, tzinfo=UTC))


class TestAddOrganization(TestCase):
    """Unit tests for add_organization"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('add_organization', self.ctx)

    def test_add_organization(self):
        """Check if a new organization is added"""

        name = 'Example'

        org = db.add_organization(self.trxl, name)
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.type, 'organization')
        self.assertEqual(org.name, name)

        org = Organization.objects.get(name=name)
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, name)

    def test_add_multiple_organizations(self):
        """Check if more than one organization is added"""

        name = 'Organization 1'
        org = db.add_organization(self.trxl, name)
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.type, 'organization')
        self.assertEqual(org.name, name)

        name = 'Organization 2'
        org = db.add_organization(self.trxl, name)
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.type, 'organization')
        self.assertEqual(org.name, name)

        name = 'Organization 3'
        org = db.add_organization(self.trxl, name)
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.type, 'organization')
        self.assertEqual(org.name, name)

        orgs = Organization.objects.all_organizations()
        self.assertEqual(len(orgs), 3)

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

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('delete_organization', self.ctx)

    def test_delete_organization(self):
        """Check whether it deletes an organization and its related data"""

        org_ex = Organization.add_root(name='Example')
        Domain.objects.create(domain='example.org',
                              organization=org_ex)
        org_bit = Organization.add_root(name='Bitergia')

        jsmith = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               individual=jsmith)
        Enrollment.objects.create(individual=jsmith, group=org_ex)

        jdoe = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               individual=jdoe)
        Enrollment.objects.create(individual=jdoe, group=org_ex)
        Enrollment.objects.create(individual=jdoe, group=org_bit)

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

        enrollments = Enrollment.objects.filter(group__name='Example')
        self.assertEqual(len(enrollments), 0)

        enrollments = Enrollment.objects.filter(group__name='Bitergia')
        self.assertEqual(len(enrollments), 1)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        org_ex = Organization.add_root(name='Example')
        org_bit = Organization.add_root(name='Bitergia')

        jsmith = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               individual=jsmith)
        Enrollment.objects.create(individual=jsmith,
                                  group=org_ex)

        jdoe = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               individual=jdoe)
        Enrollment.objects.create(individual=jdoe,
                                  group=org_ex)
        Enrollment.objects.create(individual=jdoe,
                                  group=org_bit)

        # Tests
        before_dt = datetime_utcnow()
        db.delete_organization(self.trxl, org_ex)
        after_dt = datetime_utcnow()

        jsmith = Individual.objects.get(mk='AAAA')
        self.assertLessEqual(before_dt, jsmith.last_modified)
        self.assertGreaterEqual(after_dt, jsmith.last_modified)

        jdoe = Individual.objects.get(mk='BBBB')
        self.assertLessEqual(before_dt, jdoe.last_modified)
        self.assertGreaterEqual(after_dt, jdoe.last_modified)

        # Both individuals were modified at the same time
        self.assertEqual(jsmith.last_modified, jdoe.last_modified)

    def test_operations(self):
        """Check if the right operations are created when deleting an organization"""

        timestamp = datetime_utcnow()
        org_ex = Organization.add_root(name='Example')

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


class TestAddTeam(TestCase):
    """"Unit tests for add_team"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('add_team', self.ctx)
        self.orgname = "Example"
        self.org = Organization.add_root(name=self.orgname)

    def test_add_team(self):
        """Check if a new team is added"""

        team_name = 'subteam'

        team = db.add_team(self.trxl, team_name, self.org, None)
        self.assertIsInstance(team, Team)
        self.assertEqual(team.name, team_name)
        self.assertEqual(team.parent_org, self.org)

    def test_add_subteam(self):
        """Check if a new subteam is added for specified team"""

        team_name = 'subteam'
        team = db.add_team(self.trxl, team_name, self.org, None)
        subteam = db.add_team(self.trxl, 'childteam', self.org, team)

        self.assertIsInstance(subteam, Team)
        self.assertEqual(subteam.get_parent(), team)
        self.assertEqual(subteam.name, 'childteam')
        self.assertEqual(subteam.parent_org, self.org)

    def test_add_multiple_teams(self):
        """Check if multiple teams can be added"""

        parent = db.add_team(self.trxl, 'parent_team', self.org, None)
        db.add_team(self.trxl, 'child_team', self.org, parent)
        db.add_team(self.trxl, 'team2', self.org, None)
        db.add_team(self.trxl, 'team3', self.org, None)
        db.add_team(self.trxl, 'team4', self.org, None)

        teams = Team.objects.all().filter(parent_org=self.org)
        self.assertEqual(len(teams), 5)
        for team in teams:
            self.assertIsInstance(team, Team)

    def test_team_none(self):
        """Check whether teams with None name cannot be added"""

        with self.assertRaisesRegex(ValueError, TEAM_NAME_NONE_ERROR):
            db.add_team(self.trxl, None, self.org, None)
        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_team_empty(self):
        """Check whether teams with empty names cannot be added"""

        with self.assertRaisesRegex(ValueError, TEAM_NAME_EMPTY_ERROR.format(var="team_name")):
            db.add_team(self.trxl, '', self.org, None)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_team_whitespaces(self):
        """Check whether teams with names composed by whitespaces cannot be added"""

        with self.assertRaisesRegex(ValueError, TEAM_NAME_WHITESPACE_ERROR):
            db.add_team(self.trxl, '    ', self.org, None)

        with self.assertRaisesRegex(ValueError, TEAM_NAME_WHITESPACE_ERROR):
            db.add_team(self.trxl, '\t', self.org, None)

        with self.assertRaisesRegex(ValueError, TEAM_NAME_WHITESPACE_ERROR):
            db.add_team(self.trxl, '  \t  ', self.org, None)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_integrity_error(self):
        """Check whether teams with the same team name cannot be inserted"""

        team_name = 'error_team'

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_TEAM_ERROR):
            db.add_team(self.trxl, team_name, self.org, None)
            db.add_team(self.trxl, team_name, self.org, None)

    def test_integrity(self):
        """Check whether team with the same team name can be inserted in two diff organizations"""

        org1 = Organization.add_root(name='Example1')
        org2 = Organization.add_root(name='Example2')
        team_name = 'subteam'

        team1 = db.add_team(self.trxl, team_name, org1, None)
        team2 = db.add_team(self.trxl, team_name, org2, None)

        self.assertIsInstance(team1, Team)
        self.assertEqual(team1.parent_org, org1)

        self.assertIsInstance(team2, Team)
        self.assertEqual(team2.parent_org, org2)

    def test_integrity_error_no_org_teams(self):
        """Check whether teams with the same team name cannot be inserted when organization is None"""

        team_name = 'error_team'

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_TEAM_ERROR):
            db.add_team(self.trxl, team_name, None, None)
            db.add_team(self.trxl, team_name, None, None)

        teams = Team.objects.all_teams()
        self.assertEqual(len(teams), 1)

    def test_integrity_no_org_teams(self):
        """Check whether teams with different team names linked to no organization can be inserted"""

        team1 = db.add_team(self.trxl, "team1", self.org, None)
        team2 = db.add_team(self.trxl, "team2", self.org, None)

        teams = Team.objects.all_teams()

        self.assertIsInstance(team1, Team)
        self.assertIsInstance(team2, Team)
        self.assertEqual(len(teams), 2)

    def test_operations(self):
        """Check if the right operations are created when adding a team"""

        timestamp = datetime_utcnow()
        db.add_team(self.trxl, 'subteam', self.org, None)

        transactions = Transaction.objects.filter(name='add_team')
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'team')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, 'subteam')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 3)
        self.assertEqual(op1_args['organization'], self.orgname)
        self.assertEqual(op1_args['team_name'], 'subteam')
        self.assertEqual(op1_args['parent'], None)


class TestDeleteTeam(TestCase):
    """Unit tests for delete_team"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('delete_team', self.ctx)
        self.org = Organization.add_root(name='Example')

    def test_delete_team(self):
        """Check whether it deletes a team"""

        team = Team.add_root(name='subTeam1', parent_org=self.org)
        team.add_child(name='subTeam12', parent_org=self.org)

        team.refresh_from_db()
        db.delete_team(self.trxl, team)

        with self.assertRaises(ObjectDoesNotExist):
            Team.objects.get(name='subTeam1')

        with self.assertRaises(ObjectDoesNotExist):
            Team.objects.get(name='subTeam12')

    def test_operations(self):
        """Check if the right operations are created when deleting a team"""

        timestamp = datetime_utcnow()
        team = Team.add_root(name='subTeam1', parent_org=self.org)

        db.delete_team(self.trxl, team)

        transactions = Transaction.objects.filter(name='delete_team')
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'team')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, 'subTeam1')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['team'], 'subTeam1')


class TestAddDomain(TestCase):
    """"Unit tests for add_domain"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('add_domain', self.ctx)

    def test_add_domain(self):
        """Check if a new domain is added"""

        name = 'Example'
        domain_name = 'example.net'

        org = Organization.add_root(name=name)
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

        org = Organization.add_root(name='Example')
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

        org = Organization.add_root(name='Example')

        with self.assertRaisesRegex(ValueError, DOMAIN_NAME_NONE_ERROR):
            db.add_domain(self.trxl, org, None)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_domain_empty(self):
        """Check whether domains with empty names cannot be added"""

        org = Organization.add_root(name='Example')

        with self.assertRaisesRegex(ValueError, DOMAIN_NAME_EMPTY_ERROR):
            db.add_domain(self.trxl, org, '')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_domain_whitespaces(self):
        """Check whether domains with names composed by whitespaces cannot be added"""

        org = Organization.add_root(name='Example')

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

        org = Organization.add_root(name='Example')

        with self.assertRaisesRegex(ValueError, TOP_DOMAIN_VALUE_ERROR):
            db.add_domain(self.trxl, org, 'example.net', is_top_domain=1)

        with self.assertRaisesRegex(ValueError, TOP_DOMAIN_VALUE_ERROR):
            db.add_domain(self.trxl, org, 'example.net', is_top_domain='False')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_integrity_error(self):
        """Check whether domains with the same domain name cannot be inserted"""

        org = Organization.add_root(name='Example')
        domain_name = 'example.org'

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_DOM_ERROR):
            db.add_domain(self.trxl, org, domain_name)
            db.add_domain(self.trxl, org, domain_name)

    def test_operations(self):
        """Check if the right operations are created when adding a domain"""

        timestamp = datetime_utcnow()
        org = Organization.add_root(name='Example')

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

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('delete_domain', self.ctx)

    def test_delete_domain(self):
        """Check whether it deletes a domain"""

        org = Organization.add_root(name='Example')
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
        org = Organization.add_root(name='Example')
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


class TestAddIndividual(TestCase):
    """Unit tests for add_individual"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('add_individual', self.ctx)

    def test_add_individual(self):
        """Check whether it adds an individual"""

        mk = '1234567890ABCDFE'

        individual = db.add_individual(self.trxl, mk)
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, mk)
        self.assertEqual(individual.is_locked, False)

        individual = Individual.objects.get(mk=mk)
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual.mk, mk)
        self.assertEqual(individual.is_locked, False)

        self.assertIsInstance(individual.profile, Profile)
        self.assertEqual(individual.profile.name, None)
        self.assertEqual(individual.profile.email, None)

    def test_add_individuals(self):
        """Check whether it adds a set of individuals"""

        mks = ['AAAA', 'BBBB', 'CCCC']

        for mk in mks:
            db.add_individual(self.trxl, mk)

        for mk in mks:
            individual = Individual.objects.get(mk=mk)
            self.assertIsInstance(individual, Individual)
            self.assertEqual(individual.mk, mk)
            self.assertEqual(individual.is_locked, False)

            self.assertIsInstance(individual.profile, Profile)
            self.assertEqual(individual.profile.name, None)
            self.assertEqual(individual.profile.email, None)

    def test_uuid_none(self):
        """Check whether an individual with None as UUID cannot be added"""

        with self.assertRaisesRegex(ValueError, MK_NONE_ERROR):
            db.add_individual(self.trxl, None)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_mk_empty(self):
        """Check whether an individual with empty MK cannot be added"""

        with self.assertRaisesRegex(ValueError, MK_EMPTY_ERROR):
            db.add_individual(self.trxl, '')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_mk_whitespaces(self):
        """Check whether an individual with MK composed by whitespaces cannot be added"""

        with self.assertRaisesRegex(ValueError, MK_WHITESPACES_ERROR):
            db.add_individual(self.trxl, '   ')

        with self.assertRaisesRegex(ValueError, MK_WHITESPACES_ERROR):
            db.add_individual(self.trxl, '\t')

        with self.assertRaisesRegex(ValueError, MK_WHITESPACES_ERROR):
            db.add_individual(self.trxl, ' \t  ')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_integrity_error(self):
        """Check whether individuals with the same MK cannot be inserted"""

        mk = '1234567890ABCDFE'

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_INDIVIDUAL_ERROR):
            db.add_individual(self.trxl, mk)
            db.add_individual(self.trxl, mk)

    def test_operations(self):
        """Check if the right operations are created when adding a new identity"""

        timestamp = datetime_utcnow()
        mk = '1234567890ABCDFE'

        individual = db.add_individual(self.trxl, mk)

        transactions = Transaction.objects.all()
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.ADD.value)
        self.assertEqual(op1.entity_type, 'individual')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, '1234567890ABCDFE')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['mk'], individual.mk)


class TestDeleteIndividual(TestCase):
    """Unit tests for delete_individual"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('delete_identity', self.ctx)

    def test_delete_individual(self):
        """Check if it deletes an individual"""

        org_ex = Organization.add_root(name='Example')
        org_bit = Organization.add_root(name='Bitergia')

        jsmith = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               individual=jsmith)
        Identity.objects.create(uuid='0001', name='John Smith',
                                individual=jsmith)
        Identity.objects.create(uuid='0002', email='jsmith@example.net',
                                individual=jsmith)
        Identity.objects.create(uuid='0003', email='jsmith@example.org',
                                individual=jsmith)
        Enrollment.objects.create(individual=jsmith, group=org_ex)

        jdoe = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               individual=jdoe)
        Identity.objects.create(uuid='0004', name='John Doe',
                                email='jdoe@bitergia.com',
                                individual=jdoe)
        Enrollment.objects.create(individual=jdoe, group=org_ex)
        Enrollment.objects.create(individual=jdoe, group=org_bit)

        # Check data and remove individual
        jsmith.refresh_from_db()
        self.assertEqual(len(jsmith.identities.all()), 3)
        self.assertEqual(len(jsmith.enrollments.all()), 1)

        jdoe.refresh_from_db()
        self.assertEqual(len(jdoe.identities.all()), 1)
        self.assertEqual(len(jdoe.enrollments.all()), 2)

        db.delete_individual(self.trxl, jsmith)

        # Tests
        with self.assertRaises(ObjectDoesNotExist):
            Individual.objects.get(mk='AAAA')

        self.assertEqual(len(Identity.objects.all()), 1)
        self.assertEqual(len(Enrollment.objects.all()), 2)

        jdoe.refresh_from_db()
        self.assertEqual(len(jdoe.identities.all()), 1)
        self.assertEqual(len(jdoe.enrollments.all()), 2)

    def test_delete_individuals(self):
        """Check if it deletes a set of individuals"""

        mks = ['AAAA', 'BBBB', 'CCCC']

        for mk in mks:
            Individual.objects.create(mk=mk)

        self.assertEqual(len(Individual.objects.all()), len(mks))

        for mk in mks:
            individual = Individual.objects.get(mk=mk)

            db.delete_individual(self.trxl, individual)

            with self.assertRaises(ObjectDoesNotExist):
                Individual.objects.get(mk=mk)

        self.assertEqual(len(Individual.objects.all()), 0)

    def test_locked_individual(self):
        """Check if if fails when the individual is locked"""

        jsmith = Individual.objects.create(mk='AAAA', is_locked=True)

        msg = INDIVIDUAL_LOCKED_ERROR.format(mk='AAAA')
        with self.assertRaisesRegex(LockedIdentityError, msg):
            db.delete_individual(self.trxl, jsmith)

    def test_operations(self):
        """Check if the right operations are created when deleting an individual"""

        timestamp = datetime_utcnow()
        jsmith = Individual.objects.create(mk='AAAA')

        db.delete_individual(self.trxl, jsmith)

        transactions = Transaction.objects.filter(name='delete_identity')
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.DELETE.value)
        self.assertEqual(op1.entity_type, 'individual')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, 'AAAA')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 1)
        self.assertEqual(op1_args['individual'], 'AAAA')


class TestAddIdentity(TestCase):
    """Unit tests for add_identity"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('add_identity', self.ctx)

    def test_add_identity(self):
        """Check if a new identity is added"""

        mk = '1234567890ABCDFE'

        individual = Individual.objects.create(mk=mk)
        identity = db.add_identity(self.trxl, individual, mk, 'scm',
                                   name='John Smith',
                                   email='jsmith@example.org',
                                   username='jsmith')

        self.assertIsInstance(identity, Identity)
        self.assertEqual(identity.uuid, mk)
        self.assertEqual(identity.individual, individual)

        individual = Individual.objects.get(mk=mk)
        self.assertEqual(individual.mk, mk)

        identities = individual.identities.all()
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertIsInstance(identity, Identity)
        self.assertEqual(identity.uuid, mk)
        self.assertEqual(identity.individual.mk, mk)
        self.assertEqual(identity.source, 'scm')
        self.assertEqual(identity.name, 'John Smith')
        self.assertEqual(identity.email, 'jsmith@example.org')
        self.assertEqual(identity.username, 'jsmith')

    def test_add_multiple_identities(self):
        """Check if multiple identities can be added"""

        individual = Individual.objects.create(mk='AAAA')
        db.add_identity(self.trxl, individual, 'AAAA', 'scm',
                        name='John Smith',
                        email=None,
                        username=None)
        db.add_identity(self.trxl, individual, 'BBBB', 'its',
                        name=None,
                        email='jsmith@example.org',
                        username=None)
        db.add_identity(self.trxl, individual, 'CCCC', 'mls',
                        name=None,
                        email=None,
                        username='jsmith')

        individual = Individual.objects.get(mk='AAAA')
        identities = individual.identities.all()
        self.assertEqual(len(identities), 3)

        identity = identities[0]
        self.assertIsInstance(identity, Identity)
        self.assertEqual(identity.uuid, 'AAAA')
        self.assertEqual(identity.individual.mk, 'AAAA')
        self.assertEqual(identity.source, 'scm')
        self.assertEqual(identity.name, 'John Smith')
        self.assertEqual(identity.email, None)
        self.assertEqual(identity.username, None)

        identity = identities[1]
        self.assertIsInstance(identity, Identity)
        self.assertEqual(identity.uuid, 'BBBB')
        self.assertEqual(identity.individual.mk, 'AAAA')
        self.assertEqual(identity.source, 'its')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.email, 'jsmith@example.org')
        self.assertEqual(identity.username, None)

        identity = identities[2]
        self.assertIsInstance(identity, Identity)
        self.assertEqual(identity.uuid, 'CCCC')
        self.assertEqual(identity.individual.mk, 'AAAA')
        self.assertEqual(identity.source, 'mls')
        self.assertEqual(identity.name, None)
        self.assertEqual(identity.email, None)
        self.assertEqual(identity.username, 'jsmith')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        mk = '1234567890ABCDFE'
        individual = Individual.objects.create(mk=mk)

        before_dt = datetime_utcnow()
        db.add_identity(self.trxl, individual, mk, 'scm',
                        name='John Smith',
                        email='jsmith@example.org',
                        username='jsmith')
        after_dt = datetime_utcnow()

        # Tests
        individual = Individual.objects.get(mk=mk)
        identity = Identity.objects.get(uuid=mk)

        self.assertLessEqual(before_dt, individual.last_modified)
        self.assertGreaterEqual(after_dt, individual.last_modified)

        self.assertLessEqual(before_dt, identity.last_modified)
        self.assertGreaterEqual(after_dt, identity.last_modified)

    def test_identity_id_none(self):
        """Check whether an identity with None as ID cannot be added"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, UUID_NONE_ERROR):
            db.add_identity(self.trxl, individual, None, 'scm')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_identity_id_empty(self):
        """Check whether an identity with empty ID cannot be added"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, UUID_EMPTY_ERROR):
            db.add_identity(self.trxl, individual, '', 'scm')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_identity_id_whitespaces(self):
        """Check whether an identity with an ID composed by whitespaces cannot be added"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, UUID_WHITESPACES_ERROR):
            db.add_identity(self.trxl, individual, '    ', 'scm')

        with self.assertRaisesRegex(ValueError, UUID_WHITESPACES_ERROR):
            db.add_identity(self.trxl, individual, '\t', 'scm')

        with self.assertRaisesRegex(ValueError, UUID_WHITESPACES_ERROR):
            db.add_identity(self.trxl, individual, '  \t', 'scm')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_source_none(self):
        """Check whether an identity with None as source cannot be added"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, SOURCE_NONE_ERROR):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', None)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_source_empty(self):
        """Check whether an identity with empty source cannot be added"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, SOURCE_EMPTY_ERROR):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', '')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_source_whitespaces(self):
        """Check whether an identity with a source composed by whitespaces cannot be added"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, SOURCE_WHITESPACES_ERROR):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', '  ')

        with self.assertRaisesRegex(ValueError, SOURCE_WHITESPACES_ERROR):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', '\t')

        with self.assertRaisesRegex(ValueError, SOURCE_WHITESPACES_ERROR):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', ' \t ')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_data_none_or_empty(self):
        """
        Check whether new identities cannot be added when identity data is None, empty
        or composed by whitespaces
        """
        individual = Individual.objects.create(mk='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, IDENTITY_DATA_NONE_OR_EMPTY_ERROR):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', 'git',
                            name=None, email=None, username=None)

        expected = IDENTITY_DATA_EMPTY_ERROR.format(name='name')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', 'git',
                            name='', email='', username='')

        expected = IDENTITY_DATA_EMPTY_ERROR.format(name='email')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', 'git',
                            name=None, email='', username=None)

        expected = IDENTITY_DATA_WHITESPACES_ERROR.format(name='username')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', 'git',
                            name=None, email=None, username='  ')

        expected = IDENTITY_DATA_WHITESPACES_ERROR.format(name='username')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', 'git',
                            name=None, email=None, username='\t')

        expected = IDENTITY_DATA_EMPTY_ERROR.format(name='name')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', 'git',
                            name='', email=None, username='    ')

        expected = IDENTITY_DATA_EMPTY_ERROR.format(name='name')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', 'git',
                            name='', email=None, username='\t')

        expected = IDENTITY_DATA_WHITESPACES_ERROR.format(name='name')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', 'git',
                            name='   ', email=None, username='')

        expected = IDENTITY_DATA_WHITESPACES_ERROR.format(name='name')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', 'git',
                            name='\t', email=None, username='')

        expected = IDENTITY_DATA_WHITESPACES_ERROR.format(name='name')
        with self.assertRaisesRegex(ValueError, expected):
            db.add_identity(self.trxl, individual, '1234567890ABCDFE', 'git',
                            name=' \t ', email=None, username='')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_integrity_error_id(self):
        """Check whether identities with the same id cannot be inserted"""

        mk = '1234567890ABCDFE'
        individual = Individual.objects.create(mk=mk)

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_ID_ERROR):
            db.add_identity(self.trxl, individual, mk, 'scm',
                            name='John Smith',
                            email='jsmith@example.org',
                            username='jsmith')
            db.add_identity(self.trxl, individual, mk, 'scm',
                            name='John Smith',
                            email='jsmith@example.net',
                            username='jonhsmith')

    def test_integrity_error_unique_data(self):
        """Check whether identities with the same data cannot be inserted"""

        individual = Individual.objects.create(mk='AAAA')

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_ID_DATA_ERROR):
            db.add_identity(self.trxl, individual, 'AAAA', 'scm',
                            name='John Smith',
                            email='jsmith@example.org',
                            username='jsmith')
            db.add_identity(self.trxl, individual, 'BBBB', 'scm',
                            name='John Smith',
                            email='jsmith@example.org',
                            username='jsmith')

    def test_locked_individual(self):
        """Check if if fails when the individual is locked"""

        jsmith = Individual.objects.create(mk='AAAA', is_locked=True)

        msg = INDIVIDUAL_LOCKED_ERROR.format(mk='AAAA')
        with self.assertRaisesRegex(LockedIdentityError, msg):
            db.add_identity(self.trxl, jsmith, 'AAAA', 'scm',
                            name='John Smith',
                            email='jsmith@example.org',
                            username='jsmith')

    def test_operations(self):
        """Check if the right operations are created when adding a new identity"""

        timestamp = datetime_utcnow()
        mk = '1234567890ABCDFE'

        individual = Individual.objects.create(mk=mk)
        identity = db.add_identity(self.trxl, individual, mk, 'scm',
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
        self.assertEqual(op1_args['individual'], identity.individual.mk)
        self.assertEqual(op1_args['uuid'], identity.uuid)
        self.assertEqual(op1_args['source'], identity.source)
        self.assertEqual(op1_args['name'], identity.name)
        self.assertEqual(op1_args['email'], identity.email)
        self.assertEqual(op1_args['username'], identity.username)


class TestDeleteIdentity(TestCase):
    """Unit tests for delete_identity"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('delete_identity', self.ctx)

    def test_delete_identity(self):
        """Check whether it deletes an identity"""

        jsmith = Individual.objects.create(mk='AAAA')
        Identity.objects.create(uuid='0001', name='John Smith',
                                individual=jsmith)
        Identity.objects.create(uuid='0002', email='jsmith@example.net',
                                individual=jsmith)
        Identity.objects.create(uuid='0003', email='jsmith@example.org',
                                individual=jsmith)

        # Check data and remove identity
        jsmith.refresh_from_db()
        self.assertEqual(len(jsmith.identities.all()), 3)

        identity = Identity.objects.get(uuid='0002')
        db.delete_identity(self.trxl, identity)

        # Tests
        with self.assertRaises(ObjectDoesNotExist):
            Identity.objects.get(uuid='0002')

        jsmith.refresh_from_db()
        self.assertEqual(len(jsmith.identities.all()), 2)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        jsmith = Individual.objects.create(mk='AAAA')
        Identity.objects.create(uuid='0001', name='John Smith',
                                individual=jsmith)
        Identity.objects.create(uuid='0002', email='jsmith@example.net',
                                individual=jsmith)
        Identity.objects.create(uuid='0003', email='jsmith@example.org',
                                individual=jsmith)

        before_dt = datetime_utcnow()
        identity = Identity.objects.get(uuid='0001')
        db.delete_identity(self.trxl, identity)
        after_dt = datetime_utcnow()

        # Tests
        individual = Individual.objects.get(mk='AAAA')
        self.assertEqual(len(individual.identities.all()), 2)
        self.assertLessEqual(before_dt, individual.last_modified)
        self.assertGreaterEqual(after_dt, individual.last_modified)

        identity = Identity.objects.get(uuid='0002')
        self.assertLessEqual(identity.last_modified, before_dt)
        self.assertLessEqual(identity.last_modified, after_dt)

    def test_locked_individual(self):
        """Check if if fails when the individual is locked"""

        jsmith = Individual.objects.create(mk='AAAA', is_locked=True)

        msg = INDIVIDUAL_LOCKED_ERROR.format(mk='AAAA')
        with self.assertRaisesRegex(LockedIdentityError, msg):
            db.delete_individual(self.trxl, jsmith)

    def test_operations(self):
        """Check if the right operations are created when deleting an identity"""

        # Set the initial dataset
        timestamp = datetime_utcnow()
        jsmith = Individual.objects.create(mk='AAAA')
        Identity.objects.create(uuid='0001', name='John Smith',
                                individual=jsmith)
        Identity.objects.create(uuid='0002', email='jsmith@example.net',
                                individual=jsmith)
        Identity.objects.create(uuid='0003', email='jsmith@example.org',
                                individual=jsmith)
        jsmith.refresh_from_db()

        # Get the identity and delete it
        identity = Identity.objects.get(uuid='0002')
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

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('update_profile', self.ctx)

    def test_update_profile(self):
        """Check if it updates a profile"""

        mk = '1234567890ABCDFE'

        country = Country.objects.create(code='US',
                                         name='United States of America',
                                         alpha3='USA')
        jsmith = Individual.objects.create(mk=mk)
        Profile.objects.create(individual=jsmith)

        individual = db.update_profile(self.trxl, jsmith,
                                       name='Smith, J.', email='jsmith@example.net',
                                       is_bot=True, country_code='US',
                                       gender='male', gender_acc=98)

        # Tests
        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual, jsmith)

        profile = individual.profile
        self.assertEqual(profile.name, 'Smith, J.')
        self.assertEqual(profile.email, 'jsmith@example.net')
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.country, country)
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 98)

        # Check database object
        individual_db = Individual.objects.get(mk=mk)
        self.assertEqual(profile, individual_db.profile)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        mk = '1234567890ABCDFE'

        individual = Individual.objects.create(mk=mk)
        Profile.objects.create(individual=individual)

        before_dt = datetime_utcnow()
        db.update_profile(self.trxl, individual,
                          name='John Smith', email='jsmith@example.net')
        after_dt = datetime_utcnow()

        # Tests
        individual = Individual.objects.get(mk=mk)
        self.assertLessEqual(before_dt, individual.last_modified)
        self.assertGreaterEqual(after_dt, individual.last_modified)

    def test_name_email_empty(self):
        """Check if name and email are set to None when an empty string is given"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')
        Profile.objects.create(individual=individual)

        individual = db.update_profile(self.trxl, individual, name='', email='')
        profile = individual.profile
        self.assertEqual(profile.name, None)
        self.assertEqual(profile.email, None)

    def test_is_bot_invalid_type(self):
        """Check type values of is_bot parameter"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')
        Profile.objects.create(individual=individual)

        with self.assertRaisesRegex(ValueError, IS_BOT_VALUE_ERROR):
            db.update_profile(self.trxl, individual, is_bot=1)

        with self.assertRaisesRegex(ValueError, IS_BOT_VALUE_ERROR):
            db.update_profile(self.trxl, individual, is_bot='True')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_country_code_not_valid(self):
        """Check if it fails when the given country is not valid"""

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')

        individual = Individual.objects.create(mk='1234567890ABCDFE')
        Profile.objects.create(individual=individual)

        msg = COUNTRY_CODE_ERROR.format(code='JKL')

        with self.assertRaisesRegex(ValueError, msg):
            db.update_profile(self.trxl, individual, country_code='JKL')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_gender_not_given(self):
        """Check if it fails when gender_acc is given but not the gender"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')
        Profile.objects.create(individual=individual)

        with self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_ERROR):
            db.update_profile(self.trxl, individual, gender_acc=100)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_gender_acc_invalid_type(self):
        """Check type values of gender_acc parameter"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')
        Profile.objects.create(individual=individual)

        with self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_TYPE_ERROR):
            db.update_profile(self.trxl, individual,
                              gender='male', gender_acc=10.0)

        with self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_TYPE_ERROR):
            db.update_profile(self.trxl, individual,
                              gender='male', gender_acc='100')

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_gender_acc_invalid_range(self):
        """Check if it fails when gender_acc is given but not the gender"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')
        Profile.objects.create(individual=individual)

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='-1')

        with self.assertRaisesRegex(ValueError, msg):
            db.update_profile(self.trxl, individual,
                              gender='male', gender_acc=-1)

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='0')

        with self.assertRaisesRegex(ValueError, msg):
            db.update_profile(self.trxl, individual,
                              gender='male', gender_acc=0)

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='101')

        with self.assertRaisesRegex(ValueError, msg):
            db.update_profile(self.trxl, individual,
                              gender='male', gender_acc=101)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_locked_individual(self):
        """Check if if fails when the individual is locked"""

        jsmith = Individual.objects.create(mk='AAAA', is_locked=True)
        Profile.objects.create(individual=jsmith)

        msg = INDIVIDUAL_LOCKED_ERROR.format(mk='AAAA')
        with self.assertRaisesRegex(LockedIdentityError, msg):
            db.update_profile(self.trxl, jsmith,
                              name='Smith, J.', email='jsmith@example.net',
                              is_bot=True, country_code='US',
                              gender='male', gender_acc=98)

    def test_operations(self):
        """Check if the right operations are created when updating a profile"""

        timestamp = datetime_utcnow()

        # Load initial dataset
        mk = '1234567890ABCDFE'
        country = Country.objects.create(code='US',
                                         name='United States of America',
                                         alpha3='USA')
        jsmith = Individual.objects.create(mk=mk)
        Profile.objects.create(individual=jsmith)

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
        self.assertEqual(op1_args['individual'], mk)
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

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('enroll', self.ctx)

    def test_enroll(self):
        """Check if a new enrollment is added"""

        mk = '1234567890ABCDFE'

        individual = Individual.objects.create(mk=mk)
        org = Organization.add_root(name='Example')

        start = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        end = datetime.datetime(2000, 1, 1, tzinfo=UTC)

        enrollment = db.add_enrollment(self.trxl, individual, org, start=start, end=end)

        self.assertIsInstance(enrollment, Enrollment)
        self.assertEqual(enrollment.start, start)
        self.assertEqual(enrollment.end, end)
        self.assertEqual(enrollment.individual, individual)
        self.assertEqual(enrollment.group, org)

        individual = Individual.objects.get(mk=mk)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment_db = enrollments[0]
        self.assertEqual(enrollment, enrollment_db)

    def test_enroll_in_team(self):
        """Check if a new enrollment in a team is added"""

        mk = '1234567890ABCDFE'

        individual = Individual.objects.create(mk=mk)
        org = Organization.add_root(name='Bitergia')
        team = Team.add_root(name='Example', parent_org=org)

        start = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        end = datetime.datetime(2000, 1, 1, tzinfo=UTC)

        enrollment = db.add_enrollment(self.trxl, individual, team,
                                       start=start, end=end)

        self.assertIsInstance(enrollment, Enrollment)
        self.assertEqual(enrollment.start, start)
        self.assertEqual(enrollment.end, end)
        self.assertEqual(enrollment.individual, individual)
        self.assertEqual(enrollment.group, team)
        self.assertEqual(enrollment.group.parent_org, org)

        individual = Individual.objects.get(mk=mk)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 1)

        enrollment_db = enrollments[0]
        self.assertEqual(enrollment, enrollment_db)

    def test_add_multiple_enrollments(self):
        """Check if multiple enrollments can be added"""

        mk = '1234567890ABCDFE'
        name = 'Example'

        individual = Individual.objects.create(mk='1234567890ABCDFE')
        org = Organization.add_root(name='Example')

        db.add_enrollment(self.trxl, individual, org, start=datetime.datetime(1999, 1, 1, tzinfo=UTC))
        db.add_enrollment(self.trxl, individual, org, end=datetime.datetime(2005, 1, 1, tzinfo=UTC))
        db.add_enrollment(self.trxl, individual, org, start=datetime.datetime(2013, 1, 1, tzinfo=UTC),
                          end=datetime.datetime(2014, 1, 1, tzinfo=UTC))

        # Tests
        individual = Individual.objects.get(mk=mk)

        enrollments = individual.enrollments.all()
        self.assertEqual(len(enrollments), 3)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, MIN_PERIOD_DATE)
        self.assertEqual(enrollment.end, datetime.datetime(2005, 1, 1, tzinfo=UTC))
        self.assertIsInstance(enrollment.individual, Individual)
        self.assertEqual(enrollment.individual.mk, mk)
        self.assertIsInstance(enrollment.group, Group)
        self.assertEqual(enrollment.group.name, name)

        enrollment = enrollments[1]
        self.assertEqual(enrollment.start, datetime.datetime(1999, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, MAX_PERIOD_DATE)
        self.assertIsInstance(enrollment.individual, Individual)
        self.assertEqual(enrollment.individual.mk, mk)
        self.assertIsInstance(enrollment.group, Group)
        self.assertEqual(enrollment.group.name, name)

        enrollment = enrollments[2]
        self.assertEqual(enrollment.start, datetime.datetime(2013, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))
        self.assertIsInstance(enrollment.individual, Individual)
        self.assertEqual(enrollment.individual.mk, mk)
        self.assertIsInstance(enrollment.group, Group)
        self.assertEqual(enrollment.group.name, name)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')
        org = Organization.add_root(name='Example')

        before_dt = datetime_utcnow()
        db.add_enrollment(self.trxl, individual, org, start=MIN_PERIOD_DATE, end=MAX_PERIOD_DATE)
        after_dt = datetime_utcnow()

        # Tests
        individual = Individual.objects.get(mk='1234567890ABCDFE')
        self.assertLessEqual(before_dt, individual.last_modified)
        self.assertGreaterEqual(after_dt, individual.last_modified)

    def test_from_date_none(self):
        """Check if an enrollment cannot be added when from_date is None"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')
        org = Organization.add_root(name='Example')

        with self.assertRaisesRegex(ValueError, START_DATE_NONE_ERROR):
            db.add_enrollment(self.trxl, individual, org,
                              start=None, end=datetime.datetime(1999, 1, 1, tzinfo=UTC))

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_to_date_none(self):
        """Check if an enrollment cannot be added when to_date is None"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')
        org = Organization.add_root(name='Example')

        with self.assertRaisesRegex(ValueError, END_DATE_NONE_ERROR):
            db.add_enrollment(self.trxl, individual, org,
                              start=datetime.datetime(2001, 1, 1, tzinfo=UTC), end=None)

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_integrity_error_unique_data(self):
        """Check whether enrollments with the same data cannot be inserted"""

        mk = '1234567890ABCDFE'

        # Load initial dataset
        individual = Individual.objects.create(mk=mk)
        org = Organization.add_root(name='Example')

        start = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        end = datetime.datetime(2000, 1, 1, tzinfo=UTC)

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_ENROLLMENT_ERROR):
            db.add_enrollment(self.trxl, individual, org,
                              start=start, end=end)
            db.add_enrollment(self.trxl, individual, org,
                              start=start, end=end)

    def test_period_invalid(self):
        """Check whether enrollments cannot be added giving invalid period ranges"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')
        org = Organization.add_root(name='Example')

        data = {
            'start': r'2001-01-01 00:00:00\+00:00',
            'end': r'1999-01-01 00:00:00\+00:00'
        }
        msg = PERIOD_INVALID_ERROR.format(**data)

        with self.assertRaisesRegex(ValueError, msg):
            db.add_enrollment(self.trxl, individual, org,
                              start=datetime.datetime(2001, 1, 1, tzinfo=UTC),
                              end=datetime.datetime(1999, 1, 1, tzinfo=UTC))

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_period_out_of_bounds(self):
        """Check whether enrollments cannot be added giving a range out of bounds"""

        individual = Individual.objects.create(mk='1234567890ABCDFE')
        org = Organization.add_root(name='Example')

        data = {
            'type': 'start',
            'date': r'1899-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(ValueError, msg):
            db.add_enrollment(self.trxl, individual, org,
                              start=datetime.datetime(1899, 12, 31, 23, 59, 59, tzinfo=UTC))

        data = {
            'type': 'start',
            'date': r'2100-01-01 00:00:01\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(ValueError, msg):
            db.add_enrollment(self.trxl, individual, org,
                              start=datetime.datetime(2100, 1, 1, 0, 0, 1, tzinfo=UTC))

        data = {
            'type': 'end',
            'date': r'2100-01-01 00:00:01\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(ValueError, msg):
            db.add_enrollment(self.trxl, individual, org,
                              end=datetime.datetime(2100, 1, 1, 0, 0, 1, tzinfo=UTC))

        data = {
            'type': 'end',
            'date': r'1899-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(ValueError, msg):
            db.add_enrollment(self.trxl, individual, org,
                              end=datetime.datetime(1899, 12, 31, 23, 59, 59, tzinfo=UTC))

        # Check if operations have not been generated after the failure
        operations = Operation.objects.all()
        self.assertEqual(len(operations), 0)

    def test_locked_individual(self):
        """Check if if fails when the individual is locked"""

        jsmith = Individual.objects.create(mk='AAAA', is_locked=True)
        org = Organization.add_root(name='Example')
        start = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        end = datetime.datetime(2000, 1, 1, tzinfo=UTC)

        msg = INDIVIDUAL_LOCKED_ERROR.format(mk='AAAA')
        with self.assertRaisesRegex(LockedIdentityError, msg):
            db.add_enrollment(self.trxl, jsmith, org, start=start, end=end)

    def test_operations(self):
        """Check if the right operations are created when deleting a domain"""

        timestamp = datetime_utcnow()
        mk = '1234567890ABCDFE'

        # Load initial dataset
        individual = Individual.objects.create(mk=mk)
        org = Organization.add_root(name='Example')

        start = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        end = datetime.datetime(2000, 1, 1, tzinfo=UTC)

        # Add the enrollment
        db.add_enrollment(self.trxl, individual, org, start=start, end=end)

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
        self.assertEqual(op1_args['individual'], mk)
        self.assertEqual(op1_args['group'], org.name)
        self.assertEqual(op1_args['start'], str(datetime_to_utc(datetime.datetime(1999, 1, 1))))
        self.assertEqual(op1_args['end'], str(datetime_to_utc(datetime.datetime(2000, 1, 1))))


class TestDeleteEnrollment(TestCase):
    """Unit tests for delete_enrollment"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('withdraw', self.ctx)

    def test_delete_enrollment(self):
        """Check whether it deletes an enrollment"""

        from_date = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        first_period = datetime.datetime(2000, 1, 1, tzinfo=UTC)
        second_period = datetime.datetime(2010, 1, 1, tzinfo=UTC)
        to_date = datetime.datetime(2010, 1, 1, tzinfo=UTC)

        jsmith = Individual.objects.create(mk='AAAA')
        Identity.objects.create(uuid='0001', name='John Smith',
                                individual=jsmith)

        example_org = Organization.add_root(name='Example')
        Enrollment.objects.create(individual=jsmith, group=example_org,
                                  start=from_date, end=first_period)
        enrollment = Enrollment.objects.create(individual=jsmith, group=example_org,
                                               start=second_period, end=to_date)

        bitergia_org = Organization.add_root(name='Bitergia')
        Enrollment.objects.create(individual=jsmith, group=bitergia_org,
                                  start=first_period, end=second_period)

        # Check data and remove enrollment
        jsmith.refresh_from_db()
        self.assertEqual(len(jsmith.identities.all()), 1)
        self.assertEqual(len(jsmith.enrollments.all()), 3)

        db.delete_enrollment(self.trxl, enrollment)

        # Tests
        with self.assertRaises(ObjectDoesNotExist):
            Enrollment.objects.get(individual=jsmith,
                                   start=second_period,
                                   end=to_date)

        enrollments = Enrollment.objects.filter(group__name='Example')
        self.assertEqual(len(enrollments), 1)

        enrollments = Enrollment.objects.filter(group__name='Bitergia')
        self.assertEqual(len(enrollments), 1)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        from_date = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        to_date = datetime.datetime(2000, 1, 1, tzinfo=UTC)

        jsmith = Individual.objects.create(mk='AAAA')
        Identity.objects.create(uuid='0001', name='John Smith',
                                individual=jsmith)

        example_org = Organization.add_root(name='Example')
        enrollment = Enrollment.objects.create(individual=jsmith, group=example_org,
                                               start=from_date, end=to_date)

        # Tests
        before_dt = datetime_utcnow()
        db.delete_enrollment(self.trxl, enrollment)
        after_dt = datetime_utcnow()

        jsmith = Individual.objects.get(mk='AAAA')
        self.assertLessEqual(before_dt, jsmith.last_modified)
        self.assertGreaterEqual(after_dt, jsmith.last_modified)

    def test_locked_individual(self):
        """Check if if fails when the individual is locked"""

        jsmith = Individual.objects.create(mk='AAAA', is_locked=True)

        org = Organization.add_root(name='Example')
        start = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        end = datetime.datetime(2000, 1, 1, tzinfo=UTC)

        enrollment = Enrollment.objects.create(individual=jsmith,
                                               group=org,
                                               start=start,
                                               end=end)

        jsmith.refresh_from_db()

        msg = INDIVIDUAL_LOCKED_ERROR.format(mk='AAAA')
        with self.assertRaisesRegex(LockedIdentityError, msg):
            db.delete_enrollment(self.trxl, enrollment)

    def test_operations(self):
        """Check if the right operations are created when deleting an enrollment"""

        timestamp = datetime_utcnow()

        # Load intial dataset
        from_date = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        first_period = datetime.datetime(2000, 1, 1, tzinfo=UTC)
        second_period = datetime.datetime(2010, 1, 1, tzinfo=UTC)
        to_date = datetime.datetime(2010, 1, 1, tzinfo=UTC)

        jsmith = Individual.objects.create(mk='AAAA')
        Identity.objects.create(uuid='0001', name='John Smith',
                                individual=jsmith)

        example_org = Organization.add_root(name='Example')
        Enrollment.objects.create(individual=jsmith, group=example_org,
                                  start=from_date, end=first_period)
        enrollment = Enrollment.objects.create(individual=jsmith, group=example_org,
                                               start=second_period, end=to_date)

        bitergia_org = Organization.add_root(name='Bitergia')
        Enrollment.objects.create(individual=jsmith, group=bitergia_org,
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
        self.assertEqual(op1_args['mk'], 'AAAA')
        self.assertEqual(op1_args['group'], 'Example')
        self.assertEqual(op1_args['start'], str(datetime_to_utc(second_period)))
        self.assertEqual(op1_args['end'], str(datetime_to_utc(to_date)))


class TestMoveIdentity(TestCase):
    """Unit tests for move_identity"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('move_identity', self.ctx)

    def test_move_identity(self):
        """Test when an identity is moved to an individual"""

        from_indv = Individual.objects.create(mk='AAAA')
        to_indv = Individual.objects.create(mk='BBBB')

        identity = Identity.objects.create(uuid='0001', name='John Smith',
                                           individual=from_indv)

        # Move identity and check results
        individual = db.move_identity(self.trxl, identity, to_indv)

        self.assertIsInstance(individual, Individual)
        self.assertEqual(individual, to_indv)

        identities = individual.identities.all()
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity.uuid, '0001')
        self.assertEqual(identity.name, 'John Smith')

        # Check if the database stored those changes
        individual = Individual.objects.get(mk='AAAA')
        self.assertEqual(len(individual.identities.all()), 0)

        individual = Individual.objects.get(mk='BBBB')
        identities = individual.identities.all()
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity.uuid, '0001')
        self.assertEqual(identity.name, 'John Smith')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        from_indv = Individual.objects.create(mk='AAAA')
        to_indv = Individual.objects.create(mk='BBBB')

        identity = Identity.objects.create(uuid='0001', name='John Smith',
                                           individual=from_indv)

        # Move identity and check results
        before_dt = datetime_utcnow()
        db.move_identity(self.trxl, identity, to_indv)
        after_dt = datetime_utcnow()

        # Tests
        individual = Individual.objects.get(mk='AAAA')
        self.assertLessEqual(before_dt, individual.last_modified)
        self.assertGreaterEqual(after_dt, individual.last_modified)

        individual = Individual.objects.get(mk='BBBB')
        self.assertLessEqual(before_dt, individual.last_modified)
        self.assertGreaterEqual(after_dt, individual.last_modified)

        identity = Identity.objects.get(uuid='0001')
        self.assertLessEqual(before_dt, identity.last_modified)
        self.assertGreaterEqual(after_dt, identity.last_modified)

    def test_equal_related_individual(self):
        """Test that all remains the same when individual is the individual related to identity'"""

        from_indv = Individual.objects.create(mk='AAAA')
        identity = Identity.objects.create(uuid='0001', name='John Smith',
                                           individual=from_indv)
        # Move identity and check results
        with self.assertRaisesRegex(ValueError, MOVE_ERROR):
            db.move_identity(self.trxl, identity, from_indv)

        individual = Individual.objects.get(mk='AAAA')
        self.assertEqual(len(individual.identities.all()), 1)

    def test_locked_individual(self):
        """Check if if fails when the individual is locked"""

        indv1 = Individual.objects.create(mk='AAAA')
        indv2 = Individual.objects.create(mk='BBBB', is_locked=True)

        id1 = Identity.objects.create(uuid='0001', name='John Smith', individual=indv1)
        id2 = Identity.objects.create(uuid='0002', name='John Smith', individual=indv2)

        msg = INDIVIDUAL_LOCKED_ERROR.format(mk='BBBB')
        with self.assertRaisesRegex(LockedIdentityError, msg):
            db.move_identity(self.trxl, id1, indv2)

        with self.assertRaisesRegex(LockedIdentityError, msg):
            db.move_identity(self.trxl, id2, indv1)

    def test_operations(self):
        """Check if the right operations are created when moving an identity"""

        timestamp = datetime_utcnow()

        from_indv = Individual.objects.create(mk='AAAA')
        to_indv = Individual.objects.create(mk='BBBB')

        identity = Identity.objects.create(uuid='0001', name='John Smith',
                                           individual=from_indv)

        # Move identity
        db.move_identity(self.trxl, identity, to_indv)

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
        self.assertEqual(op1_args['individual'], 'BBBB')


class TestLock(TestCase):
    """Unit tests for lock"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('lock', self.ctx)

    def test_lock_identity(self):
        """Test if a given individual is locked"""

        jsmith = Individual.objects.create(mk='AAAA')

        # Check value before calling the method
        self.assertEqual(jsmith.is_locked, False)

        db.lock(self.trxl, jsmith)

        # Tests
        individual = Individual.objects.get(mk='AAAA')
        self.assertEqual(individual.is_locked, True)

    def test_operations(self):
        """Check if the right operations are created when locking an individual"""

        timestamp = datetime_utcnow()

        jsmith = Individual.objects.create(mk='AAAA')

        jsmith = db.lock(self.trxl, jsmith)

        transactions = Transaction.objects.all()
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'individual')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, 'AAAA')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 2)
        self.assertEqual(op1_args['mk'], jsmith.mk)
        self.assertEqual(op1_args['is_locked'], jsmith.is_locked)


class TestUnlock(TestCase):
    """Unit tests for unlock"""

    def setUp(self):
        """Load initial dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.trxl = TransactionsLog.open('lock', self.ctx)

    def test_unlock_identity(self):
        """Test if a given individual is unlocked"""

        jsmith = Individual.objects.create(mk='AAAA', is_locked=True)

        # Check value before calling the method
        self.assertEqual(jsmith.is_locked, True)

        # Calling method
        db.unlock(self.trxl, jsmith)

        # Tests
        individual = Individual.objects.get(mk='AAAA')
        self.assertEqual(individual.is_locked, False)

    def test_operations(self):
        """Check if the right operations are created when unlocking an individual"""

        timestamp = datetime_utcnow()

        jsmith = Individual.objects.create(mk='AAAA')

        jsmith = db.unlock(self.trxl, jsmith)

        transactions = Transaction.objects.all()
        trx = transactions[0]

        operations = Operation.objects.filter(trx=trx)
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertIsInstance(op1, Operation)
        self.assertEqual(op1.op_type, Operation.OpType.UPDATE.value)
        self.assertEqual(op1.entity_type, 'individual')
        self.assertEqual(op1.trx, trx)
        self.assertEqual(op1.target, 'AAAA')
        self.assertGreater(op1.timestamp, timestamp)

        op1_args = json.loads(op1.args)
        self.assertEqual(len(op1_args), 2)
        self.assertEqual(op1_args['mk'], jsmith.mk)
        self.assertEqual(op1_args['is_locked'], jsmith.is_locked)
