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

from dateutil.tz import UTC

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from grimoirelab_toolkit.datetime import datetime_utcnow

from sortinghat.core import db
from sortinghat.core.errors import AlreadyExistsError, NotFoundError
from sortinghat.core.models import (MIN_PERIOD_DATE,
                                    MAX_PERIOD_DATE,
                                    Organization,
                                    Domain,
                                    Country,
                                    UniqueIdentity,
                                    Identity,
                                    Profile,
                                    Enrollment)


DUPLICATED_ORG_ERROR = "Organization 'Example' already exists in the registry"
DUPLICATED_DOM_ERROR = "Domain 'example.org' already exists in the registry"
DUPLICATED_UID_ERROR = "UniqueIdentity '1234567890ABCDFE' already exists in the registry"
DUPLICATED_ID_ERROR = "Identity '1234567890ABCDFE' already exists in the registry"
DUPLICATED_ID_DATA_ERROR = "Identity 'John Smith-jsmith@example.org-jsmith-scm' already exists in the registry"
NAME_NONE_ERROR = "'name' cannot be None"
NAME_EMPTY_ERROR = "'name' cannot be an empty string"
DOMAIN_NAME_NONE_ERROR = "'domain_name' cannot be None"
DOMAIN_NAME_EMPTY_ERROR = "'domain_name' cannot be an empty string"
TOP_DOMAIN_VALUE_ERROR = "'is_top_domain' must have a boolean value"
UUID_NONE_ERROR = "'uuid' cannot be None"
UUID_EMPTY_ERROR = "'uuid' cannot be an empty string"
IDENTITY_ID_NONE_ERROR = "'identity_id' cannot be None"
IDENTITY_ID_EMPTY_ERROR = "'identity_id' cannot be an empty string"
SOURCE_NONE_ERROR = "'source' cannot be None"
SOURCE_EMPTY_ERROR = "'source' cannot be an empty string"
IDENTITY_DATA_NONE_OR_EMPTY_ERROR = "identity data cannot be None or empty"
UNIQUE_IDENTITY_NOT_FOUND_ERROR = "zyxwuv not found in the registry"
IDENTITY_NOT_FOUND_ERROR = "zyxwuv not found in the registry"
IS_BOT_VALUE_ERROR = "'is_bot' must have a boolean value"
COUNTRY_CODE_ERROR = r"'country_code' \({code}\) does not match with a valid code"
GENDER_ACC_INVALID_ERROR = "'gender_acc' can only be set when 'gender' is given"
GENDER_ACC_INVALID_TYPE_ERROR = "'gender_acc' must have an integer value"
GENDER_ACC_INVALID_RANGE_ERROR = r"'gender_acc' \({acc}\) is not in range \(1,100\)"
START_DATE_NONE_ERROR = "'start' date cannot be None"
END_DATE_NONE_ERROR = "'end' date cannot be None"
PERIOD_INVALID_ERROR = "'start' date {start} cannot be greater than {end}"
PERIOD_OUT_OF_BOUNDS_ERROR = "'{type}' date {date} is out of bounds"


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


class TestAddDomain(TestCase):
    """"Unit tests for add_domain"""

    def test_add_domain(self):
        """Check if a new domain is added"""

        name = 'Example'
        domain_name = 'example.net'

        org = Organization.objects.create(name=name)
        dom = db.add_domain(org, domain_name,
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
        db.add_domain(org, 'example.com',
                      is_top_domain=True)
        db.add_domain(org, 'my.example.net')

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
            db.add_domain(org, None)

    def test_domain_empty(self):
        """Check whether domains with empty names cannot be added"""

        org = Organization.objects.create(name='Example')

        with self.assertRaisesRegex(ValueError, DOMAIN_NAME_EMPTY_ERROR):
            db.add_domain(org, '')

    def test_top_domain_invalid_type(self):
        """Check type values of top domain flag"""

        org = Organization.objects.create(name='Example')

        with self.assertRaisesRegex(ValueError, TOP_DOMAIN_VALUE_ERROR):
            db.add_domain(org, 'example.net', is_top_domain=1)

        with self.assertRaisesRegex(ValueError, TOP_DOMAIN_VALUE_ERROR):
            db.add_domain(org, 'example.net', is_top_domain='False')

    def test_integrity_error(self):
        """Check whether domains with the same domain name cannot be inserted"""

        org = Organization.objects.create(name='Example')
        domain_name = 'example.org'

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_DOM_ERROR):
            db.add_domain(org, domain_name)
            db.add_domain(org, domain_name)


class TestDeleteDomain(TestCase):
    """Unit tests for delete_domain"""

    def test_delete_domain(self):
        """Check whether it deletes a domain"""

        org = Organization.objects.create(name='Example')
        dom = Domain.objects.create(domain='example.org', organization=org)
        Domain.objects.create(domain='example.com', organization=org)

        # Check data and remove domain
        org.refresh_from_db()
        self.assertEqual(len(org.domains.all()), 2)

        dom.refresh_from_db()
        db.delete_domain(dom)

        # Tests
        with self.assertRaises(ObjectDoesNotExist):
            Domain.objects.get(domain='example.org')

        org.refresh_from_db()
        self.assertEqual(len(org.domains.all()), 1)


class TestAddUniqueIdentity(TestCase):
    """Unit tests for add_unique_identity"""

    def test_add_unique_identity(self):
        """Check whether it adds a unique identity"""

        uuid = '1234567890ABCDFE'

        uidentity = db.add_unique_identity(uuid)
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
            db.add_unique_identity(uuid)

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
            db.add_unique_identity(None)

    def test_uuid_empty(self):
        """Check whether a unique identity with empty UUID cannot be added"""

        with self.assertRaisesRegex(ValueError, UUID_EMPTY_ERROR):
            db.add_unique_identity('')

    def test_integrity_error(self):
        """Check whether unique identities with the same UUID cannot be inserted"""

        uuid = '1234567890ABCDFE'

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_UID_ERROR):
            db.add_unique_identity(uuid)
            db.add_unique_identity(uuid)


class TestDeleteUniqueIdentity(TestCase):
    """Unit tests for delete_unique_identity"""

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

        db.delete_unique_identity(jsmith)

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

            db.delete_unique_identity(uidentity)

            with self.assertRaises(ObjectDoesNotExist):
                UniqueIdentity.objects.get(uuid=uuid)

        self.assertEqual(len(UniqueIdentity.objects.all()), 0)


class TestAddIdentity(TestCase):
    """Unit tests for add_identity"""

    def test_add_identity(self):
        """Check if a new identity is added"""

        uuid = '1234567890ABCDFE'

        uidentity = UniqueIdentity.objects.create(uuid=uuid)
        identity = db.add_identity(uidentity, uuid, 'scm',
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
        db.add_identity(uidentity, 'AAAA', 'scm',
                        name='John Smith',
                        email=None,
                        username=None)
        db.add_identity(uidentity, 'BBBB', 'its',
                        name=None,
                        email='jsmith@example.org',
                        username=None)
        db.add_identity(uidentity, 'CCCC', 'mls',
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
        db.add_identity(uidentity, uuid, 'scm',
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
            db.add_identity(uidentity, None, 'scm')

    def test_identity_id_empty(self):
        """Check whether an identity with empty ID cannot be added"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, IDENTITY_ID_EMPTY_ERROR):
            db.add_identity(uidentity, '', 'scm')

    def test_source_none(self):
        """Check whether an identity with None as source cannot be added"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, SOURCE_NONE_ERROR):
            db.add_identity(uidentity, '1234567890ABCDFE', None)

    def test_source_empty(self):
        """Check whether an identity with empty source cannot be added"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, SOURCE_EMPTY_ERROR):
            db.add_identity(uidentity, '1234567890ABCDFE', '')

    def test_data_none_or_empty(self):
        """Check whether new identities cannot be added when identity data is None or empty"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')

        with self.assertRaisesRegex(ValueError, IDENTITY_DATA_NONE_OR_EMPTY_ERROR):
            db.add_identity(uidentity, '1234567890ABCDFE', 'git',
                            name=None, email=None, username=None)

        with self.assertRaisesRegex(ValueError, IDENTITY_DATA_NONE_OR_EMPTY_ERROR):
            db.add_identity(uidentity, '1234567890ABCDFE', 'git',
                            name='', email='', username='')

        with self.assertRaisesRegex(ValueError, IDENTITY_DATA_NONE_OR_EMPTY_ERROR):
            db.add_identity(uidentity, '1234567890ABCDFE', 'git',
                            name=None, email='', username=None)

    def test_integrity_error_id(self):
        """Check whether identities with the same id cannot be inserted"""

        uuid = '1234567890ABCDFE'
        uidentity = UniqueIdentity.objects.create(uuid=uuid)

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_ID_ERROR):
            db.add_identity(uidentity, uuid, 'scm',
                            name='John Smith',
                            email='jsmith@example.org',
                            username='jsmith')
            db.add_identity(uidentity, uuid, 'scm',
                            name='John Smith',
                            email='jsmith@example.net',
                            username='jonhsmith')

    def test_integrity_error_unique_data(self):
        """Check whether identities with the same data cannot be inserted"""

        uidentity = UniqueIdentity.objects.create(uuid='AAAA')

        with self.assertRaisesRegex(AlreadyExistsError, DUPLICATED_ID_DATA_ERROR):
            db.add_identity(uidentity, 'AAAA', 'scm',
                            name='John Smith',
                            email='jsmith@example.org',
                            username='jsmith')
            db.add_identity(uidentity, 'BBBB', 'scm',
                            name='John Smith',
                            email='jsmith@example.org',
                            username='jsmith')


class TestDeleteIdentity(TestCase):
    """Unit tests for delete_identity"""

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
        db.delete_identity(identity)

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
        db.delete_identity(identity)
        after_dt = datetime_utcnow()

        # Tests
        uidentity = UniqueIdentity.objects.get(uuid='AAAA')
        self.assertEqual(len(uidentity.identities.all()), 2)
        self.assertLessEqual(before_dt, uidentity.last_modified)
        self.assertGreaterEqual(after_dt, uidentity.last_modified)

        identity = Identity.objects.get(id='0002')
        self.assertLessEqual(identity.last_modified, before_dt)
        self.assertLessEqual(identity.last_modified, after_dt)


class TestUpdateProfile(TestCase):
    """Unit tests for update_profile"""

    def test_update_profile(self):
        """Check if it updates a profile"""

        uuid = '1234567890ABCDFE'

        country = Country.objects.create(code='US',
                                         name='United States of America',
                                         alpha3='USA')
        jsmith = UniqueIdentity.objects.create(uuid=uuid)
        Profile.objects.create(uidentity=jsmith)

        uidentity = db.update_profile(jsmith,
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
        db.update_profile(uidentity,
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

        uidentity = db.update_profile(uidentity, nme='', email='')
        profile = uidentity.profile
        self.assertEqual(profile.name, None)
        self.assertEqual(profile.email, None)

    def test_is_bot_invalid_type(self):
        """Check type values of is_bot parameter"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        Profile.objects.create(uidentity=uidentity)

        with self.assertRaisesRegex(ValueError, IS_BOT_VALUE_ERROR):
            db.update_profile(uidentity, is_bot=1)

        with self.assertRaisesRegex(ValueError, IS_BOT_VALUE_ERROR):
            db.update_profile(uidentity, is_bot='True')

    def test_country_code_not_valid(self):
        """Check if it fails when the given country is not valid"""

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        Profile.objects.create(uidentity=uidentity)

        msg = COUNTRY_CODE_ERROR.format(code='JKL')

        with self.assertRaisesRegex(ValueError, msg):
            db.update_profile(uidentity, country_code='JKL')

    def test_gender_not_given(self):
        """Check if it fails when gender_acc is given but not the gender"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        Profile.objects.create(uidentity=uidentity)

        with self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_ERROR):
            db.update_profile(uidentity, gender_acc=100)

    def test_gender_acc_invalid_type(self):
        """Check type values of gender_acc parameter"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        Profile.objects.create(uidentity=uidentity)

        with self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_TYPE_ERROR):
            db.update_profile(uidentity,
                              gender='male', gender_acc=10.0)

        with self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_TYPE_ERROR):
            db.update_profile(uidentity,
                              gender='male', gender_acc='100')

    def test_gender_acc_invalid_range(self):
        """Check if it fails when gender_acc is given but not the gender"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        Profile.objects.create(uidentity=uidentity)

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='-1')

        with self.assertRaisesRegex(ValueError, msg):
            db.update_profile(uidentity,
                              gender='male', gender_acc=-1)

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='0')

        with self.assertRaisesRegex(ValueError, msg):
            db.update_profile(uidentity,
                              gender='male', gender_acc=0)

        msg = GENDER_ACC_INVALID_RANGE_ERROR.format(acc='101')

        with self.assertRaisesRegex(ValueError, msg):
            db.update_profile(uidentity,
                              gender='male', gender_acc=101)


class TestAddEnrollment(TestCase):
    """Unit tests for add_enrollment"""

    def test_enroll(self):
        """Check if a new enrollment is added"""

        uuid = '1234567890ABCDFE'

        uidentity = UniqueIdentity.objects.create(uuid=uuid)
        org = Organization.objects.create(name='Example')

        start = datetime.datetime(1999, 1, 1, tzinfo=UTC)
        end = datetime.datetime(2000, 1, 1, tzinfo=UTC)

        enrollment = db.add_enrollment(uidentity, org, start=start, end=end)

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

        db.add_enrollment(uidentity, org, start=datetime.datetime(1999, 1, 1, tzinfo=UTC))
        db.add_enrollment(uidentity, org, end=datetime.datetime(2005, 1, 1, tzinfo=UTC))
        db.add_enrollment(uidentity, org, start=datetime.datetime(2013, 1, 1, tzinfo=UTC),
                          end=datetime.datetime(2014, 1, 1, tzinfo=UTC))

        # Tests
        uidentity = UniqueIdentity.objects.get(uuid=uuid)

        enrollments = uidentity.enrollments.all()
        self.assertEqual(len(enrollments), 3)

        enrollment = enrollments[0]
        self.assertEqual(enrollment.start, datetime.datetime(1999, 1, 1, tzinfo=dateutil.tz.tzutc()))
        self.assertEqual(enrollment.end, MAX_PERIOD_DATE)
        self.assertIsInstance(enrollment.uidentity, UniqueIdentity)
        self.assertEqual(enrollment.uidentity.uuid, uuid)
        self.assertIsInstance(enrollment.organization, Organization)
        self.assertEqual(enrollment.organization.name, name)

        enrollment = enrollments[1]
        self.assertEqual(enrollment.start, MIN_PERIOD_DATE)
        self.assertEqual(enrollment.end, datetime.datetime(2005, 1, 1, tzinfo=dateutil.tz.tzutc()))
        self.assertIsInstance(enrollment.uidentity, UniqueIdentity)
        self.assertEqual(enrollment.uidentity.uuid, uuid)
        self.assertIsInstance(enrollment.organization, Organization)
        self.assertEqual(enrollment.organization.name, name)

        enrollment = enrollments[2]
        self.assertEqual(enrollment.start, datetime.datetime(2013, 1, 1, tzinfo=dateutil.tz.tzutc()))
        self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1, tzinfo=dateutil.tz.tzutc()))
        self.assertIsInstance(enrollment.uidentity, UniqueIdentity)
        self.assertEqual(enrollment.uidentity.uuid, uuid)
        self.assertIsInstance(enrollment.organization, Organization)
        self.assertEqual(enrollment.organization.name, name)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        org = Organization.objects.create(name='Example')

        before_dt = datetime_utcnow()
        db.add_enrollment(uidentity, org, start=MIN_PERIOD_DATE, end=MAX_PERIOD_DATE)
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
            db.add_enrollment(uidentity, org,
                              start=None, end=datetime.datetime(1999, 1, 1, tzinfo=UTC))

    def test_to_date_none(self):
        """Check if an enrollment cannot be added when to_date is None"""

        uidentity = UniqueIdentity.objects.create(uuid='1234567890ABCDFE')
        org = Organization.objects.create(name='Example')

        with self.assertRaisesRegex(ValueError, END_DATE_NONE_ERROR):
            db.add_enrollment(uidentity, org,
                              start=datetime.datetime(2001, 1, 1, tzinfo=UTC), end=None)

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
            db.add_enrollment(uidentity, org,
                              start=datetime.datetime(2001, 1, 1, tzinfo=UTC),
                              end=datetime.datetime(1999, 1, 1, tzinfo=UTC))

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
            db.add_enrollment(uidentity, org,
                              start=datetime.datetime(1899, 12, 31, 23, 59, 59, tzinfo=UTC))

        data = {
            'type': 'start',
            'date': r'2100-01-01 00:00:01\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(ValueError, msg):
            db.add_enrollment(uidentity, org,
                              start=datetime.datetime(2100, 1, 1, 0, 0, 1, tzinfo=UTC))

        data = {
            'type': 'end',
            'date': r'2100-01-01 00:00:01\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(ValueError, msg):
            db.add_enrollment(uidentity, org,
                              end=datetime.datetime(2100, 1, 1, 0, 0, 1, tzinfo=UTC))

        data = {
            'type': 'end',
            'date': r'1899-12-31 23:59:59\+00:00'
        }
        msg = PERIOD_OUT_OF_BOUNDS_ERROR.format(**data)

        with self.assertRaisesRegex(ValueError, msg):
            db.add_enrollment(uidentity, org,
                              end=datetime.datetime(1899, 12, 31, 23, 59, 59, tzinfo=UTC))

