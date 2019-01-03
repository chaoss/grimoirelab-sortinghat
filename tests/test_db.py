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

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from grimoirelab_toolkit.datetime import datetime_utcnow

from sortinghat.core import db
from sortinghat.core.errors import AlreadyExistsError
from sortinghat.core.models import (Organization,
                                    Domain,
                                    UniqueIdentity,
                                    Profile,
                                    Enrollment)


NAME_NONE_ERROR = "'name' cannot be None"
NAME_EMPTY_ERROR = "'name' cannot be an empty string"
DUPLICATED_ORG_ERROR = "Organization 'Example' already exists in the registry"


class TestAddOrganization(TestCase):
    """Unit tests for add_organization"""

    def test_add_organization(self):
        """Check if a new organization is added"""

        name = 'Example'

        org = db.add_organization(name)
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, name)

        org = Organization.objects.get(name=name)
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, name)

    def test_name_none(self):
        """Check whether organizations with None as name cannot be added"""

        with self.assertRaisesRegex(ValueError, NAME_NONE_ERROR):
            db.add_organization(None)

    def test_name_empty(self):
        """Check whether organizations with empty names cannot be added"""

        with self.assertRaisesRegex(ValueError, NAME_EMPTY_ERROR):
            db.add_organization('')

    def test_integrity_error(self):
        """Check whether organizations with the same name cannot be inserted"""

        name = 'Example'

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_ORG_ERROR):
            db.add_organization(name)
            db.add_organization(name)


class TestDeleteOrganization(TestCase):
    """Unit tests for delete_organization"""

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

        db.delete_organization(org_ex)

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
        db.delete_organization(org_ex)
        after_dt = datetime_utcnow()

        jsmith = UniqueIdentity.objects.get(uuid='AAAA')
        self.assertLessEqual(before_dt, jsmith.last_modified)
        self.assertGreaterEqual(after_dt, jsmith.last_modified)

        jdoe = UniqueIdentity.objects.get(uuid='BBBB')
        self.assertLessEqual(before_dt, jdoe.last_modified)
        self.assertGreaterEqual(after_dt, jdoe.last_modified)

        # Both unique identities were modified at the same time
        self.assertEqual(jsmith.last_modified, jdoe.last_modified)
