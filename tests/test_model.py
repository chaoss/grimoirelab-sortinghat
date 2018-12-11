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

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TransactionTestCase

from grimoirelab_toolkit.datetime import datetime_utcnow

from sortinghat.core.models import (Organization,
                                    Domain,
                                    Country,
                                    UniqueIdentity,
                                    Identity,
                                    Profile,
                                    Enrollment,
                                    MatchingBlacklist)

# Test check errors messages
DUPLICATE_CHECK_ERROR = "Duplicate entry .+"
NULL_VALUE_CHECK_ERROR = "Column .+ cannot be null"
INVALID_BOOLEAN_CHECK_ERROR = "'true' value must be either True or False."


class TestOrganization(TransactionTestCase):
    """Unit tests for Organization class"""

    def test_unique_organizations(self):
        """Check whether organizations name are unique"""

        with self.assertRaises(IntegrityError):
            Organization.objects.create(name="Example")
            Organization.objects.create(name="Example")

    def test_charset(self):
        """Check encoding charset"""

        # With an invalid encoding both names wouldn't be inserted;
        # In MySQL, chars 'ı' and 'i' are considered the same with a
        # collation distinct to <charset>_unicode_ci
        Organization.objects.create(name='ıCompany')
        Organization.objects.create(name='iCompany')

        org1 = Organization.objects.get(name='ıCompany')
        org2 = Organization.objects.get(name='iCompany')

        self.assertEqual(org1.name, 'ıCompany')
        self.assertEqual(org2.name, 'iCompany')

    def test_created_at(self):
        """Check creation date is only set when the object is created"""

        before_dt = datetime_utcnow()
        org = Organization.objects.create(name='ıCompany')
        after_dt = datetime_utcnow()

        self.assertGreaterEqual(org.created_at, before_dt)
        self.assertLessEqual(org.created_at, after_dt)

        org.save()

        self.assertGreaterEqual(org.created_at, before_dt)
        self.assertLessEqual(org.created_at, after_dt)

    def test_last_modified(self):
        """Check last modification date is set when the object is updated"""

        before_dt = datetime_utcnow()
        org = Organization.objects.create(name='ıCompany')
        after_dt = datetime_utcnow()

        self.assertGreaterEqual(org.last_modified, before_dt)
        self.assertLessEqual(org.last_modified, after_dt)

        before_modified_dt = datetime_utcnow()
        org.save()
        after_modified_dt = datetime_utcnow()

        self.assertGreaterEqual(org.last_modified, before_modified_dt)
        self.assertLessEqual(org.last_modified, after_modified_dt)


class TestDomain(TransactionTestCase):
    """Unit tests for Domain class"""

    def test_unique_domains(self):
        """Check whether domains are unique"""

        with self.assertRaisesRegex(IntegrityError, DUPLICATE_CHECK_ERROR):
            org = Organization.objects.create(name='Example')
            Domain.objects.create(domain='example.com', organization=org)
            Domain.objects.create(domain='example.com', organization=org)

    def test_not_null_organizations(self):
        """Check whether every domain is assigned to an organization"""

        with self.assertRaisesRegex(IntegrityError, NULL_VALUE_CHECK_ERROR):
            Domain.objects.create(domain='example.com')

    def test_is_top_domain_invalid_type(self):
        """Check invalid values on is_top_domain bool column"""

        with self.assertRaisesRegex(ValidationError, INVALID_BOOLEAN_CHECK_ERROR):
            org = Organization.objects.create(name='Example')
            Domain.objects.create(domain='example.com', is_top_domain='true',
                                  organization=org)

    def test_created_at(self):
        """Check creation date is only set when the object is created"""

        before_dt = datetime_utcnow()
        org = Organization.objects.create(name='Example')
        dom = Domain.objects.create(domain='example.com', is_top_domain=True,
                                    organization=org)
        after_dt = datetime_utcnow()

        self.assertEqual(dom.is_top_domain, True)
        self.assertGreaterEqual(dom.created_at, before_dt)
        self.assertLessEqual(dom.created_at, after_dt)

        dom.is_top_domain = False
        dom.save()

        self.assertEqual(dom.is_top_domain, False)
        self.assertGreaterEqual(dom.created_at, before_dt)
        self.assertLessEqual(dom.created_at, after_dt)

    def test_last_modified(self):
        """Check last modification date is set when the object is updated"""

        before_dt = datetime_utcnow()
        org = Organization.objects.create(name='Example')
        dom = Domain.objects.create(domain='example.com', is_top_domain=True,
                                    organization=org)
        after_dt = datetime_utcnow()

        self.assertEqual(dom.is_top_domain, True)
        self.assertGreaterEqual(dom.last_modified, before_dt)
        self.assertLessEqual(dom.last_modified, after_dt)

        before_modified_dt = datetime_utcnow()
        dom.is_top_domain = False
        dom.save()
        after_modified_dt = datetime_utcnow()

        self.assertEqual(dom.is_top_domain, False)
        self.assertGreaterEqual(dom.last_modified, before_modified_dt)
        self.assertLessEqual(dom.last_modified, after_modified_dt)


class TestCountry(TransactionTestCase):
    """Unit tests for Country class"""

    def test_unique_countries(self):
        """Check whether countries are unique"""

        with self.assertRaisesRegex(IntegrityError, DUPLICATE_CHECK_ERROR):
            Country.objects.create(code='ES', name='Spain', alpha3='ESP')
            Country.objects.create(code='ES', name='España', alpha3='E')

    def test_unique_alpha3(self):
        """Check whether alpha3 codes are unique"""

        with self.assertRaisesRegex(IntegrityError, DUPLICATE_CHECK_ERROR):
            Country.objects.create(code='ES', name='Spain', alpha3='ESP')
            Country.objects.create(code='E', name='Spain', alpha3='ESP')

    def test_created_at(self):
        """Check creation date is only set when the object is created"""

        before_dt = datetime_utcnow()
        country = Country.objects.create(code='ES', name='Spain', alpha3='ESP')
        after_dt = datetime_utcnow()

        self.assertEqual(country.name, 'Spain')
        self.assertGreaterEqual(country.created_at, before_dt)
        self.assertLessEqual(country.created_at, after_dt)

        country.name = 'España'
        country.save()

        self.assertEqual(country.name, 'España')
        self.assertGreaterEqual(country.created_at, before_dt)
        self.assertLessEqual(country.created_at, after_dt)

    def test_last_modified(self):
        """Check last modification date is set when the object is updated"""

        before_dt = datetime_utcnow()
        country = Country.objects.create(code='ES', name='Spain', alpha3='ESP')
        after_dt = datetime_utcnow()

        self.assertEqual(country.name, 'Spain')
        self.assertGreaterEqual(country.last_modified, before_dt)
        self.assertLessEqual(country.last_modified, after_dt)

        before_modified_dt = datetime_utcnow()
        country.name = 'España'
        country.save()
        after_modified_dt = datetime_utcnow()

        self.assertEqual(country.name, 'España')
        self.assertGreaterEqual(country.last_modified, before_modified_dt)
        self.assertLessEqual(country.last_modified, after_modified_dt)


class TestUniqueIdentity(TransactionTestCase):
    """Unit tests for UniqueIdentity class"""

    def test_unique_uuid(self):
        """Check whether the uuid is in fact unique"""

        with self.assertRaisesRegex(IntegrityError, DUPLICATE_CHECK_ERROR):
            UniqueIdentity.objects.create(uuid='AAAA')
            UniqueIdentity.objects.create(uuid='AAAA')

    def test_created_at(self):
        """Check creation date is only set when the object is created"""

        before_dt = datetime_utcnow()
        uid = UniqueIdentity.objects.create(uuid='AAAA')
        after_dt = datetime_utcnow()

        self.assertGreaterEqual(uid.created_at, before_dt)
        self.assertLessEqual(uid.created_at, after_dt)

        uid.save()

        self.assertGreaterEqual(uid.created_at, before_dt)
        self.assertLessEqual(uid.created_at, after_dt)

    def test_last_modified(self):
        """Check last modification date is set when the object is updated"""

        before_dt = datetime_utcnow()
        uid = UniqueIdentity.objects.create(uuid='AAAA')
        after_dt = datetime_utcnow()

        self.assertGreaterEqual(uid.last_modified, before_dt)
        self.assertLessEqual(uid.last_modified, after_dt)

        before_modified_dt = datetime_utcnow()
        uid.save()
        after_modified_dt = datetime_utcnow()

        self.assertGreaterEqual(uid.last_modified, before_modified_dt)
        self.assertLessEqual(uid.last_modified, after_modified_dt)


class TestIdentity(TransactionTestCase):
    """Unit tests for Identity class"""

    def test_not_null_source(self):
        """Check whether every identity has a source"""

        with self.assertRaisesRegex(IntegrityError, NULL_VALUE_CHECK_ERROR):
            uid = UniqueIdentity.objects.create(uuid='AAAA')
            Identity.objects.create(uidentity=uid, source=None)

    def test_identities_are_unique(self):
        """Check if there is only one tuple with the same values"""

        uid = UniqueIdentity.objects.create(uuid='AAAA')
        id1 = Identity.objects.create(id='A',
                                      name='John Smith',
                                      email='jsmith@example.com',
                                      username='jsmith',
                                      source='scm',
                                      uidentity=uid)

        with self.assertRaisesRegex(IntegrityError, DUPLICATE_CHECK_ERROR):
            Identity.objects.create(id='B',
                                    name='John Smith',
                                    email='jsmith@example.com',
                                    username='jsmith',
                                    source='scm',
                                    uidentity=uid)

        # Changing an property should not raise any error
        id2 = Identity.objects.create(id='B',
                                      name='John Smith',
                                      email='jsmith@example.com',
                                      username='jsmith',
                                      source='mls',
                                      uidentity=uid)

        self.assertNotEqual(id1.id, id2.id)

    def test_charset(self):
        """Check encoding charset"""

        # With an invalid encoding both names wouldn't be inserted;
        # In MySQL, chars 'ı' and 'i' are considered the same with a
        # collation distinct to <charset>_unicode_ci
        uid = UniqueIdentity.objects.create(uuid='AAAA')
        Identity.objects.create(id='A',
                                name='John Smıth',
                                email='jsmith@example.com',
                                username='jsmith',
                                source='scm',
                                uidentity=uid)
        Identity.objects.create(id='B',
                                name='John Smith',
                                email='jsmith@example.com',
                                username='jsmith',
                                source='scm',
                                uidentity=uid)

        id1 = Identity.objects.get(name='John Smıth')
        id2 = Identity.objects.get(name='John Smith')

        self.assertEqual(id1.name, 'John Smıth')
        self.assertEqual(id2.name, 'John Smith')

    def test_created_at(self):
        """Check creation date is only set when the object is created"""

        before_dt = datetime_utcnow()
        uid = UniqueIdentity.objects.create(uuid='AAAA')
        id1 = Identity.objects.create(id='A',
                                      name='John Smith',
                                      email='jsmith@example.com',
                                      username='jsmith',
                                      source='scm',
                                      uidentity=uid)
        after_dt = datetime_utcnow()

        self.assertEqual(id1.source, 'scm')
        self.assertGreaterEqual(id1.created_at, before_dt)
        self.assertLessEqual(id1.created_at, after_dt)

        id1.source = 'mls'
        id1.save()

        self.assertEqual(id1.source, 'mls')
        self.assertGreaterEqual(id1.created_at, before_dt)
        self.assertLessEqual(id1.created_at, after_dt)

    def test_last_modified(self):
        """Check last modification date is set when the object is updated"""

        before_dt = datetime_utcnow()
        uid = UniqueIdentity.objects.create(uuid='AAAA')
        id1 = Identity.objects.create(id='A',
                                      name='John Smith',
                                      email='jsmith@example.com',
                                      username='jsmith',
                                      source='scm',
                                      uidentity=uid)
        after_dt = datetime_utcnow()

        self.assertEqual(id1.source, 'scm')
        self.assertGreaterEqual(id1.last_modified, before_dt)
        self.assertLessEqual(id1.last_modified, after_dt)

        before_modified_dt = datetime_utcnow()
        id1.source = 'mls'
        id1.save()
        after_modified_dt = datetime_utcnow()

        self.assertEqual(id1.source, 'mls')
        self.assertGreaterEqual(id1.last_modified, before_modified_dt)
        self.assertLessEqual(id1.last_modified, after_modified_dt)


class TestProfile(TransactionTestCase):
    """Unit tests for Profile class"""

    def test_unique_profile(self):
        """Check if there is only one profile for each unique identity"""

        uid = UniqueIdentity.objects.create(uuid='AAAA')

        with self.assertRaisesRegex(IntegrityError, DUPLICATE_CHECK_ERROR):
            Profile.objects.create(name='John Smith', uidentity=uid)
            Profile.objects.create(name='Smith, J.', uidentity=uid)

    def test_is_bot_invalid_type(self):
        """Check invalid values on is_bot bool column."""

        uid = UniqueIdentity.objects.create(uuid='AAAA')

        with self.assertRaisesRegex(ValidationError, INVALID_BOOLEAN_CHECK_ERROR):
            Profile.objects.create(is_bot='true', uidentity=uid)

    def test_created_at(self):
        """Check creation date is only set when the object is created"""

        before_dt = datetime_utcnow()
        uid = UniqueIdentity.objects.create(uuid='AAAA')
        prf = Profile.objects.create(name='John Smith', uidentity=uid)
        after_dt = datetime_utcnow()

        self.assertEqual(prf.name, 'John Smith')
        self.assertGreaterEqual(prf.created_at, before_dt)
        self.assertLessEqual(prf.created_at, after_dt)

        prf.name = 'J. Smith'
        prf.save()

        self.assertEqual(prf.name, 'J. Smith')
        self.assertGreaterEqual(prf.created_at, before_dt)
        self.assertLessEqual(prf.created_at, after_dt)

    def test_last_modified(self):
        """Check last modification date is set when the object is updated"""

        before_dt = datetime_utcnow()
        uid = UniqueIdentity.objects.create(uuid='AAAA')
        prf = Profile.objects.create(name='John Smith', uidentity=uid)
        after_dt = datetime_utcnow()

        self.assertEqual(prf.name, 'John Smith')
        self.assertGreaterEqual(prf.last_modified, before_dt)
        self.assertLessEqual(prf.last_modified, after_dt)

        before_modified_dt = datetime_utcnow()
        prf.name = 'J. Smith'
        prf.save()
        after_modified_dt = datetime_utcnow()

        self.assertEqual(prf.name, 'J. Smith')
        self.assertGreaterEqual(prf.last_modified, before_modified_dt)
        self.assertLessEqual(prf.last_modified, after_modified_dt)


class TestEnrollment(TransactionTestCase):
    """Unit tests for Enrollment class"""

    def test_not_null_relationships(self):
        """Check whether every enrollment is assigned organizations and unique identities"""

        with self.assertRaisesRegex(IntegrityError, NULL_VALUE_CHECK_ERROR):
            Enrollment.objects.create()

        with self.assertRaisesRegex(IntegrityError, NULL_VALUE_CHECK_ERROR):
            uid = UniqueIdentity.objects.create(uuid='AAAA')
            Enrollment.objects.create(uidentity=uid)

        with self.assertRaisesRegex(IntegrityError, NULL_VALUE_CHECK_ERROR):
            org = Organization.objects.create(name='Example')
            Enrollment.objects.create(organization=org)

    def test_unique_enrollments(self):
        """Check if there is only one tuple with the same values"""

        with self.assertRaisesRegex(IntegrityError, DUPLICATE_CHECK_ERROR):
            uid = UniqueIdentity.objects.create(uuid='AAAA')
            org = Organization.objects.create(name='Example')

            Enrollment.objects.create(uidentity=uid, organization=org)
            Enrollment.objects.create(uidentity=uid, organization=org)

    def test_default_enrollment_period(self):
        """Check whether the default period is set when initializing the class"""

        uid = UniqueIdentity.objects.create(uuid='AAAA')
        org = Organization.objects.create(name='Example')

        rol1 = Enrollment.objects.create(uidentity=uid, organization=org)
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, 0, 0, 0,
                                                       tzinfo=dateutil.tz.tzutc()))
        self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1, 0, 0, 0,
                                                     tzinfo=dateutil.tz.tzutc()))

        rol2 = Enrollment.objects.create(uidentity=uid, organization=org,
                                         end=datetime.datetime(2222, 1, 1, 0, 0, 0,
                                                               tzinfo=dateutil.tz.tzutc()))
        self.assertEqual(rol2.start, datetime.datetime(1900, 1, 1, 0, 0, 0,
                                                       tzinfo=dateutil.tz.tzutc()))
        self.assertEqual(rol2.end, datetime.datetime(2222, 1, 1, 0, 0, 0,
                                                     tzinfo=dateutil.tz.tzutc()))

        rol3 = Enrollment.objects.create(uidentity=uid, organization=org,
                                         start=datetime.datetime(1999, 1, 1, 0, 0, 0,
                                                                 tzinfo=dateutil.tz.tzutc()))
        self.assertEqual(rol3.start, datetime.datetime(1999, 1, 1, 0, 0, 0,
                                                       tzinfo=dateutil.tz.tzutc()))
        self.assertEqual(rol3.end, datetime.datetime(2100, 1, 1, 0, 0, 0,
                                                     tzinfo=dateutil.tz.tzutc()))

    def test_created_at(self):
        """Check creation date is only set when the object is created"""

        before_dt = datetime_utcnow()
        uid = UniqueIdentity.objects.create(uuid='AAAA')
        org = Organization.objects.create(name='Example')
        rol = Enrollment.objects.create(uidentity=uid, organization=org)
        after_dt = datetime_utcnow()

        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1, 0, 0, 0,
                                                      tzinfo=dateutil.tz.tzutc()))
        self.assertGreaterEqual(rol.created_at, before_dt)
        self.assertLessEqual(rol.created_at, after_dt)

        rol.start = datetime.datetime(2001, 1, 1, 0, 0, 0,
                                      tzinfo=dateutil.tz.tzutc())
        rol.save()

        self.assertEqual(rol.start, datetime.datetime(2001, 1, 1, 0, 0, 0,
                                                      tzinfo=dateutil.tz.tzutc()))
        self.assertGreaterEqual(rol.created_at, before_dt)
        self.assertLessEqual(rol.created_at, after_dt)

    def test_last_modified(self):
        """Check last modification date is set when the object is updated"""

        before_dt = datetime_utcnow()
        uid = UniqueIdentity.objects.create(uuid='AAAA')
        org = Organization.objects.create(name='Example')
        rol = Enrollment.objects.create(uidentity=uid, organization=org)
        after_dt = datetime_utcnow()

        self.assertEqual(rol.start, datetime.datetime(1900, 1, 1, 0, 0, 0,
                                                      tzinfo=dateutil.tz.tzutc()))
        self.assertGreaterEqual(rol.last_modified, before_dt)
        self.assertLessEqual(rol.last_modified, after_dt)

        before_modified_dt = datetime_utcnow()
        rol.start = datetime.datetime(2001, 1, 1, 0, 0, 0,
                                      tzinfo=dateutil.tz.tzutc())
        rol.save()
        after_modified_dt = datetime_utcnow()

        self.assertEqual(rol.start, datetime.datetime(2001, 1, 1, 0, 0, 0,
                                                      tzinfo=dateutil.tz.tzutc()))
        self.assertGreaterEqual(rol.last_modified, before_modified_dt)
        self.assertLessEqual(rol.last_modified, after_modified_dt)


class TestMatchingBlacklist(TransactionTestCase):
    """Unit tests for MatchingBlacklist class"""

    def test_unique_excluded(self):
        """Check whether the excluded term is in fact unique"""

        with self.assertRaisesRegex(IntegrityError, DUPLICATE_CHECK_ERROR):
            MatchingBlacklist.objects.create(excluded='John Smith')
            MatchingBlacklist.objects.create(excluded='John Smith')

    def test_created_at(self):
        """Check creation date is only set when the object is created."""

        before_dt = datetime_utcnow()
        mb = MatchingBlacklist.objects.create(excluded='John Smith')
        after_dt = datetime_utcnow()

        self.assertEqual(mb.excluded, 'John Smith')
        self.assertGreaterEqual(mb.created_at, before_dt)
        self.assertLessEqual(mb.created_at, after_dt)

        mb.excluded = 'J. Smith'
        mb.save()

        self.assertEqual(mb.excluded, 'J. Smith')
        self.assertGreaterEqual(mb.created_at, before_dt)
        self.assertLessEqual(mb.created_at, after_dt)

    def test_last_modified(self):
        """Check last modification date is set when the object is updated"""

        before_dt = datetime_utcnow()
        mb = MatchingBlacklist.objects.create(excluded='John Smith')
        after_dt = datetime_utcnow()

        self.assertEqual(mb.excluded, 'John Smith')
        self.assertGreaterEqual(mb.last_modified, before_dt)
        self.assertLessEqual(mb.last_modified, after_dt)

        before_modified_dt = datetime_utcnow()
        mb.excluded = 'J. Smith'
        mb.save()
        after_modified_dt = datetime_utcnow()

        self.assertEqual(mb.excluded, 'J. Smith')
        self.assertGreaterEqual(mb.last_modified, before_modified_dt)
        self.assertLessEqual(mb.last_modified, after_modified_dt)
