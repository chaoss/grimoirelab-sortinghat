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
import unittest

from sortinghat.db import api
from sortinghat.db.model import (UniqueIdentity,
                                 Identity,
                                 Profile,
                                 Organization,
                                 Domain)

from tests.base import TestDatabaseCaseBase


UUID_NONE_ERROR = "'uuid' cannot be None"
UUID_EMPTY_ERROR = "'uuid' cannot be an empty string"
IDENTITY_ID_NONE_ERROR = "'identity_id' cannot be None"
IDENTITY_ID_EMPTY_ERROR = "'identity_id' cannot be an empty string"
SOURCE_NONE_ERROR = "'source' cannot be None"
SOURCE_EMPTY_ERROR = "'source' cannot be an empty string"
IDENTITY_DATA_NONE_OR_EMPTY_ERROR = "identity data cannot be None or empty"


class TestDBAPICaseBase(TestDatabaseCaseBase):
    """Test case base class for database API tests"""

    def load_test_dataset(self):
        pass


class TestFindUniqueIdentity(TestDBAPICaseBase):
    """Unit tests for find_unique_identity"""

    def test_find_unique_identity(self):
        """Test if a unique identity is found by its UUID"""

        with self.db.connect() as session:
            uuid = 'abcdefghijklmnopqrstuvwxyz'
            uidentity = UniqueIdentity(uuid=uuid)
            session.add(uidentity)

        with self.db.connect() as session:
            uidentity = api.find_unique_identity(session, uuid)
            self.assertIsInstance(uidentity, UniqueIdentity)
            self.assertEqual(uidentity.uuid, uuid)

    def test_unique_identity_not_found(self):
        """Test whether the function returns None when the unique identity is not found"""

        with self.db.connect() as session:
            uuid = 'abcdefghijklmnopqrstuvwxyz'
            uidentity = UniqueIdentity(uuid=uuid)
            session.add(uidentity)

        with self.db.connect() as session:
            uidentity = api.find_unique_identity(session, 'zyxwuv')
            self.assertEqual(uidentity, None)


class TestFindIdentity(TestDBAPICaseBase):
    """Unit tests for find_identity"""

    def test_find_identity(self):
        """Test if an identity is found by its ID"""

        with self.db.connect() as session:
            id_ = 'abcdefghijklmnopqrstuvwxyz'
            identity = Identity(id=id_, name='John Smith', source='unknown')
            session.add(identity)

        with self.db.connect() as session:
            identity = api.find_identity(session, id_)
            self.assertIsInstance(identity, Identity)
            self.assertEqual(identity.id, id_)

    def test_identity_not_found(self):
        """Test whether the function returns None when the identity is not found"""

        with self.db.connect() as session:
            id_ = 'abcdefghijklmnopqrstuvwxyz'
            identity = Identity(id=id_, name='Jonh Smith', source='unknown')
            session.add(identity)

        with self.db.connect() as session:
            identity = api.find_identity(session, 'zyxwuv')
            self.assertEqual(identity, None)


class TestFindOrganization(TestDBAPICaseBase):
    """Unit tests for find_organization"""

    def test_find_organization(self):
        """Test if an organization is found by its name"""

        with self.db.connect() as session:
            name = 'Example'
            organization = Organization(name=name)
            session.add(organization)

        with self.db.connect() as session:
            organization = api.find_organization(session, name)
            self.assertIsInstance(organization, Organization)
            self.assertEqual(organization.name, name)

    def test_organization_not_found(self):
        """Test whether the function returns None when the organization is not found"""

        with self.db.connect() as session:
            name = 'Example'
            organization = Organization(name=name)
            session.add(organization)

        with self.db.connect() as session:
            organization = api.find_organization(session, 'Bitergia')
            self.assertEqual(organization, None)


class TestFindDomain(TestDBAPICaseBase):
    """Unit tests for find_domain"""

    def test_find_domain(self):
        """Test if an domain is found by its name"""

        with self.db.connect() as session:
            orgname = 'Example'
            organization = Organization(name=orgname)
            session.add(organization)

            domname = 'example.org'
            domain = Domain(domain=domname, organization=organization)
            session.add(domain)

        with self.db.connect() as session:
            domain = api.find_domain(session, domname)
            self.assertIsInstance(domain, Domain)
            self.assertEqual(domain.domain, domname)

    def test_domain_not_found(self):
        """Test whether the function returns None when the domain is not found"""

        with self.db.connect() as session:
            orgname = 'Example'
            organization = Organization(name=orgname)
            session.add(organization)

            domname = 'example.org'
            domain = Domain(domain=domname, organization=organization)
            session.add(domain)

        with self.db.connect() as session:
            domain = api.find_domain(session, 'example.net')
            self.assertEqual(domain, None)


class TestAddUniqueIdentity(TestDBAPICaseBase):
    """Unit tests for add_unique_identity"""

    def test_add_unique_identity(self):
        """Check whether it adds a unique identity"""

        uuid = '1234567890ABCDFE'

        with self.db.connect() as session:
            uidentity = api.add_unique_identity(session, uuid)
            self.assertIsInstance(uidentity, UniqueIdentity)
            self.assertEqual(uidentity.uuid, uuid)

        with self.db.connect() as session:
            uidentity = api.find_unique_identity(session, uuid)
            self.assertIsInstance(uidentity, UniqueIdentity)
            self.assertEqual(uidentity.uuid, uuid)

            self.assertIsInstance(uidentity.profile, Profile)
            self.assertEqual(uidentity.profile.name, None)
            self.assertEqual(uidentity.profile.email, None)
            self.assertEqual(uidentity.profile.uuid, uuid)

    def test_add_unique_identities(self):
        """Check whether it adds a set of unique identities"""

        uuids = ['AAAA', 'BBBB', 'CCCC']

        with self.db.connect() as session:
            for uuid in uuids:
                api.add_unique_identity(session, uuid)

        with self.db.connect() as session:
            for uuid in uuids:
                uidentity = api.find_unique_identity(session, uuid)
                self.assertIsInstance(uidentity, UniqueIdentity)
                self.assertEqual(uidentity.uuid, uuid)

                self.assertIsInstance(uidentity.profile, Profile)
                self.assertEqual(uidentity.profile.name, None)
                self.assertEqual(uidentity.profile.email, None)
                self.assertEqual(uidentity.profile.uuid, uuid)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        uuid = '1234567890ABCDFE'

        before_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            api.add_unique_identity(session, uuid)

        after_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uidentity = api.find_unique_identity(session, uuid)
            self.assertIsInstance(uidentity.last_modified, datetime.datetime)
            self.assertLessEqual(before_dt, uidentity.last_modified)
            self.assertGreaterEqual(after_dt, uidentity.last_modified)

    def test_uuid_none(self):
        """Check whether a unique identity with None as UUID cannot be added"""

        with self.db.connect() as session:
            with self.assertRaisesRegex(ValueError, UUID_NONE_ERROR):
                api.add_unique_identity(session, None)

    def test_uuid_empty(self):
        """Check whether a unique identity with empty UUID cannot be added"""

        with self.db.connect() as session:
            with self.assertRaisesRegex(ValueError, UUID_EMPTY_ERROR):
                api.add_unique_identity(session, '')


class TestAddIdentity(TestDBAPICaseBase):
    """Unit tests for add_identity"""

    def test_add_identity(self):
        """Check if a new identity is added"""

        uuid = '1234567890ABCDFE'

        with self.db.connect() as session:
            uidentity = UniqueIdentity(uuid=uuid)
            session.add(uidentity)
            identity = api.add_identity(session, uidentity, uuid, 'scm',
                                        name='John Smith',
                                        email='jsmith@example.org',
                                        username='jsmith')

            self.assertIsInstance(identity, Identity)
            self.assertEqual(identity.id, uuid)
            self.assertEqual(identity.uidentity, uidentity)

        with self.db.connect() as session:
            uidentity = api.find_unique_identity(session, uuid)

            self.assertIsInstance(uidentity, UniqueIdentity)
            self.assertEqual(uidentity.uuid, uuid)
            self.assertEqual(len(uidentity.identities), 1)

            identity = uidentity.identities[0]
            self.assertIsInstance(identity, Identity)
            self.assertEqual(identity.id, uuid)
            self.assertEqual(identity.uuid, uuid)
            self.assertEqual(identity.source, 'scm')
            self.assertEqual(identity.name, 'John Smith')
            self.assertEqual(identity.email, 'jsmith@example.org')
            self.assertEqual(identity.username, 'jsmith')

    def test_add_multiple_identities(self):
        """Check if multiple identities can be added"""

        with self.db.connect() as session:
            uidentity = UniqueIdentity(uuid='AAAA')
            session.add(uidentity)
            api.add_identity(session, uidentity, 'AAAA', 'scm',
                             name='John Smith',
                             email=None,
                             username=None)
            api.add_identity(session, uidentity, 'BBBB', 'its',
                             name=None,
                             email='jsmith@example.org',
                             username=None)
            api.add_identity(session, uidentity, 'CCCC', 'mls',
                             name=None,
                             email=None,
                             username='jsmith')

        with self.db.connect() as session:
            uidentity = api.find_unique_identity(session, 'AAAA')

            self.assertIsInstance(uidentity, UniqueIdentity)
            self.assertEqual(uidentity.uuid, 'AAAA')
            self.assertEqual(len(uidentity.identities), 3)

            identity = uidentity.identities[0]
            self.assertIsInstance(identity, Identity)
            self.assertEqual(identity.id, 'AAAA')
            self.assertEqual(identity.uuid, 'AAAA')
            self.assertEqual(identity.source, 'scm')
            self.assertEqual(identity.name, 'John Smith')
            self.assertEqual(identity.email, None)
            self.assertEqual(identity.username, None)

            identity = uidentity.identities[1]
            self.assertIsInstance(identity, Identity)
            self.assertEqual(identity.id, 'BBBB')
            self.assertEqual(identity.uuid, 'AAAA')
            self.assertEqual(identity.source, 'its')
            self.assertEqual(identity.name, None)
            self.assertEqual(identity.email, 'jsmith@example.org')
            self.assertEqual(identity.username, None)

            identity = uidentity.identities[2]
            self.assertIsInstance(identity, Identity)
            self.assertEqual(identity.id, 'CCCC')
            self.assertEqual(identity.uuid, 'AAAA')
            self.assertEqual(identity.source, 'mls')
            self.assertEqual(identity.name, None)
            self.assertEqual(identity.email, None)
            self.assertEqual(identity.username, 'jsmith')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        uuid = '1234567890ABCDFE'

        with self.db.connect() as session:
            uidentity = UniqueIdentity(uuid=uuid)
            session.add(uidentity)

        before_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uidentity = api.find_unique_identity(session, uuid)
            api.add_identity(session, uidentity, uuid, 'scm',
                             name='John Smith',
                             email='jsmith@example.org',
                             username='jsmith')

        after_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            identity = api.find_identity(session, uuid)
            self.assertIsInstance(identity.last_modified, datetime.datetime)
            self.assertLessEqual(before_dt, identity.last_modified)
            self.assertGreaterEqual(after_dt, identity.last_modified)

            uidentity = identity.uidentity
            self.assertIsInstance(uidentity.last_modified, datetime.datetime)
            self.assertLessEqual(before_dt, uidentity.last_modified)
            self.assertGreaterEqual(after_dt, uidentity.last_modified)

    def test_identity_id_none(self):
        """Check whether an identity with None as ID cannot be added"""

        with self.db.connect() as session:
            uidentity = UniqueIdentity(uuid='1234567890ABCDFE')
            session.add(uidentity)

            with self.assertRaisesRegex(ValueError, IDENTITY_ID_NONE_ERROR):
                api.add_identity(session, uidentity, None, 'scm')

    def test_identity_id_empty(self):
        """Check whether an identity with empty ID cannot be added"""

        with self.db.connect() as session:
            uidentity = UniqueIdentity(uuid='1234567890ABCDFE')
            session.add(uidentity)

            with self.assertRaisesRegex(ValueError, IDENTITY_ID_EMPTY_ERROR):
                api.add_identity(session, uidentity, '', 'scm')

    def test_source_none(self):
        """Check whether an identity with None as source cannot be added"""

        with self.db.connect() as session:
            uidentity = UniqueIdentity(uuid='1234567890ABCDFE')
            session.add(uidentity)

            with self.assertRaisesRegex(ValueError, SOURCE_NONE_ERROR):
                api.add_identity(session, uidentity, '1234567890ABCDFE', None)

    def test_source_empty(self):
        """Check whether an identity with empty source cannot be added"""

        with self.db.connect() as session:
            uidentity = UniqueIdentity(uuid='1234567890ABCDFE')
            session.add(uidentity)

            with self.assertRaisesRegex(ValueError, SOURCE_EMPTY_ERROR):
                api.add_identity(session, uidentity, '1234567890ABCDFE', '')

    def test_data_none_or_empty(self):
        """Check whether new identities cannot be added when identity data is None or empty"""

        with self.db.connect() as session:
            uidentity = UniqueIdentity(uuid='1234567890ABCDFE')
            session.add(uidentity)

            with self.assertRaisesRegex(ValueError, IDENTITY_DATA_NONE_OR_EMPTY_ERROR):
                api.add_identity(session, uidentity, '1234567890ABCDFE', 'git',
                                 name=None, email=None, username=None)

            with self.assertRaisesRegex(ValueError, IDENTITY_DATA_NONE_OR_EMPTY_ERROR):
                api.add_identity(session, uidentity, '1234567890ABCDFE', 'git',
                                 name='', email='', username='')

            with self.assertRaisesRegex(ValueError, IDENTITY_DATA_NONE_OR_EMPTY_ERROR):
                api.add_identity(session, uidentity, '1234567890ABCDFE', 'git',
                                 name=None, email='', username=None)


if __name__ == "__main__":
    unittest.main()