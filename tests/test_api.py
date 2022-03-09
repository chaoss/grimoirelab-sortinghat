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
import sys
import unittest

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.db.model import UniqueIdentity, Identity, Profile, \
    Organization, Domain, Country, Enrollment, MatchingBlacklist
from sortinghat.exceptions import AlreadyExistsError, NotFoundError
from sortinghat.matcher import create_identity_matcher

from tests.base import TestDatabaseCaseBase

UUID_NONE_OR_EMPTY_ERROR = "'uuid' cannot be"
ORG_NONE_OR_EMPTY_ERROR = "'name' cannot be"
DOMAIN_NONE_OR_EMPTY_ERROR = "'domain_name' cannot be"
TOP_DOMAIN_VALUE_ERROR = "'is_top_domain' must have a boolean value"
IS_BOT_VALUE_ERROR = "is_bot must have a boolean value"
SOURCE_NONE_OR_EMPTY_ERROR = "source cannot be"
IDENTITY_NONE_OR_EMPTY_ERROR = "identity data cannot be None or empty"
ENTITY_BLACKLIST_NONE_OR_EMPTY_ERROR = "'term' to blacklist cannot be"
COUNTRY_CODE_INVALID_ERROR = "country code must be a 2 length alpha string - %(code)s given"
ENROLLMENT_PERIOD_INVALID_ERROR = "cannot be greater than "
ENROLLMENT_PERIOD_OUT_OF_BOUNDS_ERROR = "'%(type)s' %(date)s is out of bounds"
NOT_FOUND_ERROR = "%(entity)s not found in the registry"
IS_BOT_VALUE_ERROR = "'is_bot' must have a boolean value"
COUNTRY_CODE_ERROR = "'country_code' \\(%(code)s\\) does not match with a valid code"
GENDER_ACC_INVALID_ERROR = "'gender_acc' can only be set when 'gender' is given"
GENDER_ACC_INVALID_TYPE_ERROR = "'gender_acc' must have an integer value"
GENDER_ACC_INVALID_RANGE_ERROR = "'gender_acc' \\(%(acc)s\\) is not in range \\(1,100\\)"


class TestAPICaseBase(TestDatabaseCaseBase):
    """Test case base class for API tests"""

    def load_test_dataset(self):
        pass


class TestAddUniqueIdentity(TestAPICaseBase):
    """Unit tests for add_unique_identity"""

    def test_add_unique_identities(self):
        """Check whether it adds a set of unique identities"""

        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')
        api.add_unique_identity(self.db, 'Jane Roe')

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()
            self.assertEqual(uid.uuid, 'John Smith')

            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Doe').first()
            self.assertEqual(uid.uuid, 'John Doe')

            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'Jane Roe').first()
            self.assertEqual(uid.uuid, 'Jane Roe')

    def test_existing_uuid(self):
        """Check if it fails adding an identity that already exists"""

        # Add a pair of identities first
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')

        # Insert the first identity again. It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_unique_identity(self.db, 'John Smith')

        self.assertEqual(context.exception.eid, 'John Smith')
        print(context.exception)

    def test_none_uuid(self):
        """Check whether None identities cannot be added to the registry"""

        self.assertRaisesRegex(ValueError, UUID_NONE_OR_EMPTY_ERROR,
                               api.add_unique_identity, self.db, None)

    def test_empty_uuid(self):
        """Check whether empty uuids cannot be added to the registry"""

        self.assertRaisesRegex(ValueError, UUID_NONE_OR_EMPTY_ERROR,
                               api.add_unique_identity, self.db, '')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        before_dt = datetime.datetime.utcnow()
        api.add_unique_identity(self.db, 'John Smith')
        after_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()

            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertGreaterEqual(after_dt, uid.last_modified)


class TestAddIdentity(TestAPICaseBase):
    """Unit tests for add_identity"""

    def test_add_new_identity(self):
        """Check if everything goes OK when adding a new identity"""

        unique_id = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                     'John Smith', 'jsmith')

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'a9b403e150dd4af8953a52a4bb841051e4b705d9').first()
            self.assertEqual(uid.uuid, unique_id)

            identities = session.query(Identity).\
                filter(Identity.uuid == uid.uuid).all()
            self.assertEqual(len(identities), 1)

            id1 = identities[0]
            self.assertEqual(id1.id, unique_id)
            self.assertEqual(id1.id, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
            self.assertEqual(id1.name, 'John Smith')
            self.assertEqual(id1.email, 'jsmith@example.com')
            self.assertEqual(id1.username, 'jsmith')
            self.assertEqual(id1.source, 'scm')

    def test_add_new_identities_to_uuid(self):
        """Check if everything goes OK when adding a new identities to an existing one"""

        # First, insert the identity that will create the unique identity
        jsmith_uuid = api.add_identity(self.db, 'scm',
                                       'jsmith@example.com', 'John Smith', 'jsmith')

        jdoe_uuid = api.add_identity(self.db, 'scm',
                                     'jdoe@example.com', 'John Doe', 'jdoe')

        # Create new identities and assign them to John Smith id
        unique_id1 = api.add_identity(self.db, 'mls',
                                      'jsmith@example.com', 'John Smith', 'jsmith',
                                      uuid=jsmith_uuid)

        unique_id2 = api.add_identity(self.db, 'mls',
                                      name='John Smith', username='jsmith',
                                      uuid=jsmith_uuid)

        # Create a new identity for John Doe
        unique_id3 = api.add_identity(self.db, 'mls',
                                      'jdoe@example.com',
                                      uuid=jdoe_uuid)

        # Check identities
        with self.db.connect() as session:
            # First, John Smith
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == jsmith_uuid).first()

            self.assertEqual(len(uid.identities), 3)

            id1 = uid.identities[0]
            self.assertEqual(id1.id, unique_id1)
            self.assertEqual(id1.name, 'John Smith')
            self.assertEqual(id1.email, 'jsmith@example.com')
            self.assertEqual(id1.username, 'jsmith')
            self.assertEqual(id1.source, 'mls')

            id2 = uid.identities[1]
            self.assertEqual(id2.id, unique_id2)
            self.assertEqual(id2.name, 'John Smith')
            self.assertEqual(id2.email, None)
            self.assertEqual(id2.username, 'jsmith')
            self.assertEqual(id2.source, 'mls')

            id3 = uid.identities[2]
            self.assertEqual(id3.id, jsmith_uuid)
            self.assertEqual(id3.name, 'John Smith')
            self.assertEqual(id3.email, 'jsmith@example.com')
            self.assertEqual(id3.username, 'jsmith')
            self.assertEqual(id3.source, 'scm')
            self.assertEqual(id3.uuid, jsmith_uuid)

            # Next, John Doe
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == jdoe_uuid).first()

            self.assertEqual(len(uid.identities), 2)

            id1 = uid.identities[0]
            self.assertEqual(id1.id, unique_id3)
            self.assertEqual(id1.name, None)
            self.assertEqual(id1.email, 'jdoe@example.com')
            self.assertEqual(id1.username, None)
            self.assertEqual(id1.source, 'mls')

            id2 = uid.identities[1]
            self.assertEqual(id2.id, jdoe_uuid)
            self.assertEqual(id2.name, 'John Doe')
            self.assertEqual(id2.email, 'jdoe@example.com')
            self.assertEqual(id2.username, 'jdoe')
            self.assertEqual(id2.source, 'scm')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        # First, insert the identity that will create the unique identity
        before_dt = datetime.datetime.utcnow()
        jsmith_uuid = api.add_identity(self.db, 'scm',
                                       'jsmith@example.com', 'John Smith', 'jsmith')
        after_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == jsmith_uuid).first()

            # Check date on the unique identity
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertGreaterEqual(after_dt, uid.last_modified)

            # Check date on the identity
            self.assertLessEqual(before_dt, uid.identities[0].last_modified)
            self.assertGreaterEqual(after_dt, uid.identities[0].last_modified)

        # Check if a new identity added to the existing unique identity
        # updates both modification dates
        before_new_dt = datetime.datetime.utcnow()
        api.add_identity(self.db, 'scm', 'jsmith@example.com', None, None,
                         uuid=jsmith_uuid)
        after_new_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == jsmith_uuid).first()

            # Check date on the unique identity; it was updated
            self.assertLessEqual(before_new_dt, uid.last_modified)
            self.assertGreaterEqual(after_new_dt, uid.last_modified)

            # Check date of the new identity
            self.assertLessEqual(before_dt, uid.identities[0].last_modified)
            self.assertLessEqual(after_dt, uid.identities[0].last_modified)
            self.assertLessEqual(before_new_dt, uid.identities[0].last_modified)
            self.assertGreaterEqual(after_new_dt, uid.identities[0].last_modified)

            # Check date of the oldest identity; it wasn't modified
            self.assertLessEqual(before_dt, uid.identities[1].last_modified)
            self.assertGreaterEqual(after_dt, uid.identities[1].last_modified)
            self.assertGreaterEqual(before_new_dt, uid.identities[1].last_modified)
            self.assertGreaterEqual(after_new_dt, uid.identities[1].last_modified)

    def test_similar_identities(self):
        """Check if it works when adding similar identities"""

        api.add_identity(self.db, 'scm', 'jsmith@example.com')

        # Although, this identities belongs to the same unique identity,
        # the api will create different unique identities for each one of
        # them
        uuid1 = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                 'John Smith')
        uuid2 = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                 'John Smith', 'jsmith')
        uuid3 = api.add_identity(self.db, 'mls', 'jsmith@example.com',
                                 'John Smith', 'jsmith')
        uuid4 = api.add_identity(self.db, 'mls', name='John Smith')
        uuid5 = api.add_identity(self.db, 'scm', name='John Smith')

        self.assertEqual(uuid1, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(uuid2, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(uuid3, '539acca35c2e8502951a97d2d5af8b0857440b50')
        self.assertEqual(uuid4, 'e7efdaf17ad2cbc0e239b9afd29f6fe054b3b0fe')
        self.assertEqual(uuid5, 'c7acd177d107a0aefa6718e2ff0dec6ceba71660')

    def test_duplicate_identities_with_truncated_values(self):
        """Check if the same identiy with truncated values is not inserted twice"""

        # Due database limitations, email will be truncated
        source = 'scm'
        email = 'averylongemailaddressthatexceedsthemaximumlengthsoitwillbetruncated' * 2
        name = 'John Smith'
        username = 'jsmith'

        api.add_identity(self.db, source, email, name, username)

        self.assertRaises(AlreadyExistsError, api.add_identity,
                          self.db, source,
                          email, name, username)

    def test_non_existing_uuid(self):
        """Check whether it fails adding identities to one uuid that does not exist"""

        # Add a pair of identities first
        api.add_identity(self.db, 'scm', 'jsmith@example.com')
        api.add_identity(self.db, 'scm', 'jdoe@example.com')

        self.assertRaises(NotFoundError, api.add_identity,
                          self.db, 'mls',
                          'jsmith@example.com', None, None,
                          'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

    def test_existing_identity(self):
        """Check if it fails adding an identity that already exists"""

        # Add a pair of identities first
        api.add_identity(self.db, 'scm', 'jsmith@example.com')
        api.add_identity(self.db, 'scm', 'jdoe@example.com')

        # Insert the first identity again. It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity(self.db, 'scm', 'jsmith@example.com')

        self.assertEqual(context.exception.eid,
                         '334da68fcd3da4e799791f73dfada2afb22648c6')

        # Insert the same identity with upper case letters.
        # It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity(self.db, 'scm', 'JSMITH@example.com')

        self.assertEqual(context.exception.eid,
                         '334da68fcd3da4e799791f73dfada2afb22648c6')

        # "None" tuples also raise an exception
        api.add_identity(self.db, 'scm', "None", None, None)

        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity(self.db, 'scm', None, "None", None)

        self.assertEqual(context.exception.eid,
                         'f0999c4eed908d33365fa3435d9686d3add2412d')

    def test_unaccent_identities(self):
        """Check if it fails adding an identity that already exists with accent values"""

        # Add a pair of identities first
        api.add_identity(self.db, 'scm', name='John Smith')
        api.add_identity(self.db, 'scm', name='Jöhn Doe')

        # Insert an accent identity again. It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity(self.db, 'scm', name='Jöhn Smith')

        self.assertEqual(context.exception.eid,
                         'c7acd177d107a0aefa6718e2ff0dec6ceba71660')

        # Insert an accent identity again. It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity(self.db, 'scm', name='John Döe')

        # Insert an unaccent identity again. It should raise AlreadyExistsError
        with self.assertRaises(AlreadyExistsError) as context:
            api.add_identity(self.db, 'scm', name='John Doe')

        self.assertEqual(context.exception.eid,
                         'a16659ea83d28c839ffae76ceebb3ca9fb8e8894')

    def test_utf8_4bytes_identities(self):
        """Check if it inserts identities with 4bytes UTF-8 characters"""

        # Emojis are 4bytes characters
        unique_id = api.add_identity(self.db, 'scm', name='😂',
                                     email='😂', username='😂')

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == '843fcc3383ddfd6179bef87996fa761d88a43915').first()
            self.assertEqual(uid.uuid, unique_id)

            identities = session.query(Identity).\
                filter(Identity.uuid == uid.uuid).all()
            self.assertEqual(len(identities), 1)

            id1 = identities[0]
            self.assertEqual(id1.id, unique_id)
            self.assertEqual(id1.id, '843fcc3383ddfd6179bef87996fa761d88a43915')
            self.assertEqual(id1.name, '😂')
            self.assertEqual(id1.email, '😂')
            self.assertEqual(id1.username, '😂')
            self.assertEqual(id1.source, 'scm')

    def test_charset(self):
        """Check if it adds two identities with different encoding"""

        # With an invalid encoding both names wouldn't be inserted;
        # In MySQL, chars 'ı' and 'i' are considered the same with a
        # collation distinct to <charset>_unicode_ci
        uuid1 = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                 'John Smıth', 'jsmith')
        uuid2 = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                 'John Smith', 'jsmith')

        self.assertEqual(uuid1, 'cf79edf008b7b2960a0be3972b256c65af449dc1')
        self.assertEqual(uuid2, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

    def test_none_source(self):
        """Check whether new identities cannot be added when giving a None source"""

        self.assertRaisesRegex(ValueError, SOURCE_NONE_OR_EMPTY_ERROR,
                               api.add_identity, self.db, None)

    def test_empty_source(self):
        """Check whether new identities cannot be added when giving an empty source"""

        self.assertRaisesRegex(ValueError, SOURCE_NONE_OR_EMPTY_ERROR,
                               api.add_identity, self.db, '')

    def test_none_or_empty_data(self):
        """Check whether new identities cannot be added when identity data is None or empty"""

        self.assertRaisesRegex(ValueError, IDENTITY_NONE_OR_EMPTY_ERROR,
                               api.add_identity, self.db, 'scm', None, '', None)
        self.assertRaisesRegex(ValueError, IDENTITY_NONE_OR_EMPTY_ERROR,
                               api.add_identity, self.db, 'scm', '', '', '')


class TestAddOrganization(TestAPICaseBase):
    """Unit tests for add_organization"""

    def test_add_organizations(self):
        """Check whether it adds a set of organizations"""

        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')
        api.add_organization(self.db, 'LibreSoft')

        with self.db.connect() as session:
            org = session.query(Organization).\
                filter(Organization.name == 'Example').first()
            self.assertEqual(org.name, 'Example')

            org = session.query(Organization).\
                filter(Organization.name == 'Bitergia').first()
            self.assertEqual(org.name, 'Bitergia')

            org = session.query(Organization).\
                filter(Organization.name == 'LibreSoft').first()
            self.assertEqual(org.name, 'LibreSoft')

    def test_existing_organization(self):
        """Check if it fails adding an organization that already exists"""

        # Add a pair of organizations first
        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')

        # Insert the first organization. It should raise AlreadyExistsError
        self.assertRaises(AlreadyExistsError, api.add_organization,
                          self.db, 'Example')

    def test_none_organization(self):
        """Check whether None organizations cannot be added to the registry"""

        self.assertRaisesRegex(ValueError, ORG_NONE_OR_EMPTY_ERROR,
                               api.add_organization, self.db, None)

    def test_empty_organization(self):
        """Check whether empty organizations cannot be added to the registry"""

        self.assertRaisesRegex(ValueError, ORG_NONE_OR_EMPTY_ERROR,
                               api.add_organization, self.db, '')


class TestAddDomain(TestAPICaseBase):
    """Unit tests for add_domain"""

    def test_add_domains(self):
        """Check whether it adds a set of domains to one organization"""

        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com')
        api.add_domain(self.db, 'Example', 'example.org', is_top_domain=True)
        api.add_domain(self.db, 'Example', 'example.net')

        with self.db.connect() as session:
            domains = session.query(Domain).join(Organization).\
                filter(Organization.name == 'Example').all()
            self.assertEqual(len(domains), 3)

            self.assertEqual(domains[0].domain, 'example.com')
            self.assertEqual(domains[0].is_top_domain, False)

            self.assertEqual(domains[1].domain, 'example.org')
            self.assertEqual(domains[1].is_top_domain, True)

            self.assertEqual(domains[2].domain, 'example.net')
            self.assertEqual(domains[2].is_top_domain, False)

    def test_add_domains_to_organization(self):
        """Check whether it adds several domains to set of organizations"""

        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')
        api.add_organization(self.db, 'LibreSoft')

        api.add_domain(self.db, 'Example', 'example.com')
        api.add_domain(self.db, 'LibreSoft', 'libresoft.es', is_top_domain=True)
        api.add_domain(self.db, 'Example', 'example.org')
        api.add_domain(self.db, 'Example', 'example.net')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')
        api.add_domain(self.db, 'LibreSoft', 'libresoft.org')

        with self.db.connect() as session:
            domains = session.query(Domain).join(Organization).\
                filter(Organization.name == 'Example').all()
            self.assertEqual(len(domains), 3)
            self.assertEqual(domains[0].domain, 'example.com')
            self.assertEqual(domains[1].domain, 'example.org')
            self.assertEqual(domains[2].domain, 'example.net')

            domains = session.query(Domain).join(Organization).\
                filter(Organization.name == 'Bitergia').all()
            self.assertEqual(len(domains), 1)
            self.assertEqual(domains[0].domain, 'bitergia.com')

            domains = session.query(Domain).join(Organization).\
                filter(Organization.name == 'LibreSoft').all()
            self.assertEqual(len(domains), 2)
            self.assertEqual(domains[0].domain, 'libresoft.es')
            self.assertEqual(domains[0].is_top_domain, True)

            self.assertEqual(domains[1].domain, 'libresoft.org')
            self.assertEqual(domains[1].is_top_domain, False)

    def test_non_existing_organization(self):
        """Check if it fails adding domains to not existing organizations"""

        self.assertRaises(NotFoundError, api.add_domain,
                          self.db, 'ErrorOrg', 'example.com')

    def test_existing_domain(self):
        """Check if it fails adding a domain that already exists"""

        # Add a pair of organizations and domains first
        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Example', 'example.com')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')

        # Add 'bitergia.com' to 'Example' org. It should raise an
        # AlreadyExistsError exception.
        self.assertRaises(AlreadyExistsError, api.add_domain,
                          self.db, 'Example', 'bitergia.com')

        # It should still falling when adding the same domain twice
        self.assertRaises(AlreadyExistsError, api.add_domain,
                          self.db, 'Example', 'example.com')
        self.assertRaises(AlreadyExistsError, api.add_domain,
                          self.db, 'Bitergia', 'bitergia.com')

        # And even if we try to update top_domain information
        self.assertRaises(AlreadyExistsError, api.add_domain,
                          self.db, 'Example', 'example.com',
                          is_top_domain=True)

    def test_overwrite_domain(self):
        """Check whether it overwrites domain information"""

        # Add a pair of organizations and domains first
        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Example', 'example.com')
        api.add_domain(self.db, 'Example', 'example.org')

        # Check that everything went well
        with self.db.connect() as session:
            domains = session.query(Domain).join(Organization).\
                filter(Organization.name == 'Example').all()
            self.assertEqual(len(domains), 2)
            self.assertEqual(domains[0].domain, 'example.com')
            self.assertEqual(domains[0].is_top_domain, False)

            self.assertEqual(domains[1].domain, 'example.org')

            domains = session.query(Domain).join(Organization).\
                filter(Organization.name == 'Bitergia').all()
            self.assertEqual(len(domains), 0)

        # Overwrite the relationship assigning the domain to a different
        # company
        api.add_domain(self.db, 'Bitergia', 'example.com',
                       is_top_domain=True, overwrite=True)

        # When overwrite is not set, it raises an AlreadyExistsError error
        self.assertRaises(AlreadyExistsError, api.add_domain,
                          self.db, 'Bitergia', 'example.org')

        # Finally, check that domain was overwritten
        with self.db.connect() as session:
            domains = session.query(Domain).join(Organization).\
                filter(Organization.name == 'Example').all()
            self.assertEqual(len(domains), 1)
            self.assertEqual(domains[0].domain, 'example.org')

            domains = session.query(Domain).join(Organization).\
                filter(Organization.name == 'Bitergia').all()
            self.assertEqual(len(domains), 1)
            self.assertEqual(domains[0].domain, 'example.com')
            self.assertEqual(domains[0].is_top_domain, True)

    def test_none_domain(self):
        """Check whether None domains cannot be added to the registry"""

        api.add_organization(self.db, 'Example')

        self.assertRaisesRegex(ValueError, DOMAIN_NONE_OR_EMPTY_ERROR,
                               api.add_domain, self.db, 'Example', None)

    def test_empty_domain(self):
        """Check whether empty domains cannot be added to the registry"""

        api.add_organization(self.db, 'Example')

        self.assertRaisesRegex(ValueError, DOMAIN_NONE_OR_EMPTY_ERROR,
                               api.add_domain, self.db, 'Example', '')

    def test_invalid_type_top_domain(self):
        """Check type values of top domain flag"""

        api.add_organization(self.db, 'Example')

        self.assertRaisesRegex(ValueError, TOP_DOMAIN_VALUE_ERROR,
                               api.add_domain, self.db, 'Example', 'example.com', 1)
        self.assertRaisesRegex(ValueError, TOP_DOMAIN_VALUE_ERROR,
                               api.add_domain, self.db, 'Example', 'example.com', 'False')


class TestAddEnrollment(TestAPICaseBase):
    """Unit tests for add_enrollment"""

    def test_add_enrollment(self):
        """Check whether it adds a set of enrollment to the same
        unique identity and organization"""

        api.add_organization(self.db, 'Example')
        api.add_unique_identity(self.db, 'John Smith')

        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2000, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(2005, 1, 1),
                           datetime.datetime(2006, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(2013, 1, 1),
                           datetime.datetime(2014, 1, 1))

        with self.db.connect() as session:
            enrollments = session.query(Enrollment).\
                join(UniqueIdentity, Organization).\
                filter(UniqueIdentity.uuid == 'John Smith',
                       Organization.name == 'Example').\
                order_by(Enrollment.start).all()
            self.assertEqual(len(enrollments), 3)

            enrollment = enrollments[0]
            self.assertEqual(enrollment.start, datetime.datetime(1999, 1, 1))
            self.assertEqual(enrollment.end, datetime.datetime(2000, 1, 1))

            enrollment = enrollments[1]
            self.assertEqual(enrollment.start, datetime.datetime(2005, 1, 1))
            self.assertEqual(enrollment.end, datetime.datetime(2006, 1, 1))

            enrollment = enrollments[2]
            self.assertEqual(enrollment.start, datetime.datetime(2013, 1, 1))
            self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1))

    def test_last_modified(self):
        """Check if last modification date is updated"""

        api.add_organization(self.db, 'Example')

        before_dt = datetime.datetime.utcnow()
        api.add_unique_identity(self.db, 'John Smith')
        after_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertGreaterEqual(after_dt, uid.last_modified)

        before_rol_dt = datetime.datetime.utcnow()
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2000, 1, 1))
        after_rol_dt = datetime.datetime.utcnow()

        # After inserting a new enrollment, the modification date was udpated
        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()

            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertLessEqual(after_dt, uid.last_modified)
            self.assertLessEqual(before_rol_dt, uid.last_modified)
            self.assertGreaterEqual(after_rol_dt, uid.last_modified)

    def test_period_ranges(self):
        """Check whether enrollments cannot be added giving invalid period ranges"""

        api.add_organization(self.db, 'Example')
        api.add_unique_identity(self.db, 'John Smith')

        self.assertRaisesRegex(ValueError, ENROLLMENT_PERIOD_INVALID_ERROR,
                               api.add_enrollment, self.db, 'John Smith', 'Example',
                               datetime.datetime(2001, 1, 1),
                               datetime.datetime(1999, 1, 1))

        exc = ENROLLMENT_PERIOD_OUT_OF_BOUNDS_ERROR % {'type': 'from_date',
                                                       'date': '1899-12-31 23:59:59'}
        self.assertRaisesRegex(ValueError, exc,
                               api.add_enrollment, self.db, 'John Smith', 'Example',
                               datetime.datetime(1899, 12, 31, 23, 59, 59))

        exc = ENROLLMENT_PERIOD_OUT_OF_BOUNDS_ERROR % {'type': 'from_date',
                                                       'date': '2100-01-01 00:00:01'}
        self.assertRaisesRegex(ValueError, exc,
                               api.add_enrollment, self.db, 'John Smith', 'Example',
                               datetime.datetime(2100, 1, 1, 0, 0, 1))

        exc = ENROLLMENT_PERIOD_OUT_OF_BOUNDS_ERROR % {'type': 'to_date',
                                                       'date': '2100-01-01 00:00:01'}
        self.assertRaisesRegex(ValueError, exc,
                               api.add_enrollment, self.db, 'John Smith', 'Example',
                               datetime.datetime(1900, 1, 1),
                               datetime.datetime(2100, 1, 1, 0, 0, 1))

        exc = ENROLLMENT_PERIOD_OUT_OF_BOUNDS_ERROR % {'type': 'to_date',
                                                       'date': '1899-12-31 23:59:59'}
        self.assertRaisesRegex(ValueError, exc,
                               api.add_enrollment, self.db, 'John Smith', 'Example',
                               datetime.datetime(1900, 1, 1),
                               datetime.datetime(1899, 12, 31, 23, 59, 59))

    def test_non_existing_uuid(self):
        """Check if it fails adding enrollments to not existing unique identities"""

        self.assertRaisesRegex(NotFoundError,
                               NOT_FOUND_ERROR % {'entity': 'John Smith'},
                               api.add_enrollment,
                               self.db, 'John Smith', 'Example')

    def test_non_existing_organization(self):
        """Check if it fails adding enrollments to not existing organizations"""

        # We need first to add a unique identity
        api.add_unique_identity(self.db, 'John Smith')

        self.assertRaisesRegex(NotFoundError,
                               NOT_FOUND_ERROR % {'entity': 'Example'},
                               api.add_enrollment,
                               self.db, 'John Smith', 'Example')

    def test_existing_enrollment(self):
        """Check if it fails adding enrollment data that already exists"""

        # Add unique identity, organization and enrollment first
        api.add_unique_identity(self.db, 'John Smith')
        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2000, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(2005, 1, 1),
                           datetime.datetime(2006, 1, 1))

        # Same dates should raise an AlreadyExistsError exception.
        self.assertRaises(AlreadyExistsError, api.add_enrollment,
                          self.db, 'John Smith', 'Example')
        self.assertRaises(AlreadyExistsError, api.add_enrollment,
                          self.db, 'John Smith', 'Example',
                          datetime.datetime(1999, 1, 1),
                          datetime.datetime(2000, 1, 1))


class TestAddToMatchingBlacklist(TestAPICaseBase):
    """Unit tests for add_to_matching_blacklist"""

    def test_add_entity(self):
        """Check whether it adds a set of entities"""

        api.add_to_matching_blacklist(self.db, 'root@example.com')
        api.add_to_matching_blacklist(self.db, 'Bitergia')
        api.add_to_matching_blacklist(self.db, 'John Doe')

        with self.db.connect() as session:
            mb = session.query(MatchingBlacklist).\
                filter(MatchingBlacklist.excluded == 'root@example.com').first()
            self.assertEqual(mb.excluded, 'root@example.com')

            mb = session.query(MatchingBlacklist).\
                filter(MatchingBlacklist.excluded == 'Bitergia').first()
            self.assertEqual(mb.excluded, 'Bitergia')

            mb = session.query(MatchingBlacklist).\
                filter(MatchingBlacklist.excluded == 'John Doe').first()
            self.assertEqual(mb.excluded, 'John Doe')

    def test_existing_excluded_entity(self):
        """Check if it fails adding an entity that already exists"""

        # Add a pair of entities first
        api.add_to_matching_blacklist(self.db, 'root@example.com')
        api.add_to_matching_blacklist(self.db, 'John Doe')

        # Insert the first entity. It should raise AlreadyExistsError
        self.assertRaises(AlreadyExistsError, api.add_to_matching_blacklist,
                          self.db, 'root@example.com')

    def test_none_entity(self):
        """Check whether None entities cannot be added to the registry"""

        self.assertRaisesRegex(ValueError,
                               ENTITY_BLACKLIST_NONE_OR_EMPTY_ERROR,
                               api.add_to_matching_blacklist, self.db, None)

    def test_empty_entity(self):
        """Check whether empty entities cannot be added to the registry"""

        self.assertRaisesRegex(ValueError,
                               ENTITY_BLACKLIST_NONE_OR_EMPTY_ERROR,
                               api.add_to_matching_blacklist, self.db, '')


class TestEditProfile(TestAPICaseBase):
    """Unit tests for edit_profile"""

    def test_edit_new_profile(self):
        """Check if it creates an new profile"""

        api.add_unique_identity(self.db, 'John Smith')

        with self.db.connect() as session:
            # Add a country
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)

            # The profile is empty for the given uuid
            prf = session.query(Profile).\
                filter(Profile.uuid == 'John Smith').first()
            self.assertIsInstance(prf, Profile)
            self.assertEqual(prf.name, None)
            self.assertEqual(prf.email, None)

        # Add the new profile
        before_dt = datetime.datetime.utcnow()
        api.edit_profile(self.db, 'John Smith', name='Smith, J.', email='',
                         gender='male', is_bot=True, country_code='US')
        after_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()

            prf = uid.profile

            self.assertEqual(prf.uuid, 'John Smith')
            self.assertEqual(prf.name, 'Smith, J.')
            # This should be converted to None
            self.assertEqual(prf.email, None)
            self.assertEqual(prf.gender, 'male')
            self.assertEqual(prf.gender_acc, 100)
            self.assertEqual(prf.is_bot, True)
            self.assertEqual(prf.country_code, 'US')
            self.assertEqual(prf.country.code, 'US')
            self.assertEqual(prf.country.name, 'United States of America')

            # Modification time was updated
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertGreaterEqual(after_dt, uid.last_modified)

    def test_update_profile(self):
        """Check if it updates an existing profile"""

        with self.db.connect() as session:
            # Add a country
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)

        # Add a unique identity with a profile
        api.add_unique_identity(self.db, 'John Smith')
        api.edit_profile(self.db, 'John Smith', name='Smith, J.',
                         gender='', is_bot=True)

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()

            prf = uid.profile

            self.assertEqual(prf.uuid, 'John Smith')
            self.assertEqual(prf.name, 'Smith, J.')
            self.assertEqual(prf.email, None)
            self.assertEqual(prf.gender, None)
            self.assertEqual(prf.gender_acc, None)
            self.assertEqual(prf.is_bot, True)
            self.assertEqual(prf.country_code, None)
            self.assertEqual(prf.country, None)

        # Update some fields
        before_dt = datetime.datetime.utcnow()
        api.edit_profile(self.db, 'John Smith', name='', email='jsmith@example.com',
                         gender='male', gender_acc=89, is_bot=False, country_code='US')
        after_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()

            prf = uid.profile

            self.assertEqual(prf.uuid, 'John Smith')
            self.assertEqual(prf.name, None)
            self.assertEqual(prf.email, 'jsmith@example.com')
            self.assertEqual(prf.gender, 'male')
            self.assertEqual(prf.gender_acc, 89)
            self.assertEqual(prf.is_bot, False)
            self.assertEqual(prf.country_code, 'US')
            self.assertEqual(prf.country.code, 'US')
            self.assertEqual(prf.country.name, 'United States of America')

            # Modification time was updated
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertGreaterEqual(after_dt, uid.last_modified)

        # Unset country data
        api.edit_profile(self.db, 'John Smith', country_code=None)

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()

            prf = uid.profile
            self.assertEqual(prf.uuid, 'John Smith')
            self.assertEqual(prf.country_code, None)
            self.assertEqual(prf.country, None)

    def test_not_found_uuid(self):
        """Check if it fails editing a profile of a unique identity that does not exists"""

        # It should raise an error when the registry is empty
        self.assertRaises(NotFoundError, api.edit_profile,
                          self.db, 'John Smith')

        # Add a pair of unique identities first
        api.add_unique_identity(self.db, 'Jonh Smith')
        api.add_unique_identity(self.db, 'John Doe')

        # The error should be the same
        self.assertRaises(NotFoundError, api.edit_profile,
                          self.db, 'Jane Rae')

    def test_not_found_country_code(self):
        """Check if it fails when the given country is not found"""

        api.add_unique_identity(self.db, 'John Smith')

        with self.db.connect() as session:
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)

        self.assertRaisesRegex(ValueError,
                               COUNTRY_CODE_ERROR % {'code': 'ES'},
                               api.edit_profile, self.db, 'John Smith',
                               **{'country_code': 'ES'})

    def test_invalid_type_is_bot(self):
        """Check type values of is_bot parameter"""

        api.add_unique_identity(self.db, 'John Smith')

        self.assertRaisesRegex(ValueError, IS_BOT_VALUE_ERROR,
                               api.edit_profile, self.db, 'John Smith',
                               **{'is_bot': 1})
        self.assertRaisesRegex(ValueError, IS_BOT_VALUE_ERROR,
                               api.edit_profile, self.db, 'John Smith',
                               **{'is_bot': 'True'})

    def test_not_given_gender(self):
        """Check if it fails when gender_acc is given but not the gender"""

        api.add_unique_identity(self.db, 'John Smith')

        self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_ERROR,
                               api.edit_profile, self.db, 'John Smith',
                               **{'gender_acc': 100})

    def test_invalid_type_gender_acc(self):
        """Check type values of gender_acc parameter"""

        api.add_unique_identity(self.db, 'John Smith')

        self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_TYPE_ERROR,
                               api.edit_profile, self.db, 'John Smith',
                               **{'gender': 'male', 'gender_acc': 10.0})

        self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_TYPE_ERROR,
                               api.edit_profile, self.db, 'John Smith',
                               **{'gender': 'male', 'gender_acc': '100'})

    def test_invalid_range_gender_acc(self):
        """Check if it fails when gender_acc is given but not the gender"""

        api.add_unique_identity(self.db, 'John Smith')

        self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_RANGE_ERROR % {'acc': '-1'},
                               api.edit_profile, self.db, 'John Smith',
                               **{'gender': 'male', 'gender_acc': -1})

        self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_RANGE_ERROR % {'acc': '0'},
                               api.edit_profile, self.db, 'John Smith',
                               **{'gender': 'male', 'gender_acc': 0})

        self.assertRaisesRegex(ValueError, GENDER_ACC_INVALID_RANGE_ERROR % {'acc': '101'},
                               api.edit_profile, self.db, 'John Smith',
                               **{'gender': 'male', 'gender_acc': 101})


class TestDeleteUniqueIdentity(TestAPICaseBase):
    """Unit tests for delete_unique_identity"""

    def test_delete_unique_identities(self):
        """Check whether it deletes a set of unique identities"""

        # First, add a set of unique identities, including some
        # identities, organizations and enrollments
        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example',
                         uuid='John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example', 'John Smith',
                         uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        api.edit_profile(self.db, 'John Doe', name='John Doe', is_bot=False)

        api.add_unique_identity(self.db, 'Jane Rae')

        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_enrollment(self.db, 'John Doe', 'Example')

        api.add_organization(self.db, 'Bitergia')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia')

        api.add_organization(self.db, 'LibreSoft')
        api.add_enrollment(self.db, 'Jane Rae', 'LibreSoft')

        # Delete the first identity
        api.delete_unique_identity(self.db, 'John Smith')

        with self.db.connect() as session:
            uid1 = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()
            self.assertEqual(uid1, None)

            identities = session.query(Identity).join(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').all()
            self.assertEqual(len(identities), 0)

            enrollments = session.query(Enrollment).join(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').all()
            self.assertEqual(len(enrollments), 0)

        # Delete the last identity
        api.delete_unique_identity(self.db, 'Jane Rae')

        with self.db.connect() as session:
            uid2 = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'Jane Rae').first()
            self.assertEqual(uid2, None)

            # Check if there only remains one unique identity, one profile
            # and one enrollment
            identities = session.query(UniqueIdentity).all()
            self.assertEqual(len(identities), 1)
            self.assertEqual(identities[0].uuid, 'John Doe')

            profiles = session.query(Profile).all()
            self.assertEqual(len(profiles), 1)
            self.assertEqual(profiles[0].uuid, 'John Doe')

            enrollments = session.query(Enrollment).all()
            self.assertEqual(len(enrollments), 1)
            self.assertEqual(enrollments[0].uidentity.uuid, 'John Doe')
            self.assertEqual(enrollments[0].organization.name, 'Example')

            orgs = session.query(Organization).all()
            self.assertEqual(len(orgs), 3)

    def test_not_found_uuid(self):
        """Check if it fails removing a unique identity that does not exists"""

        # It should raise an error when the registry is empty
        self.assertRaises(NotFoundError, api.delete_unique_identity,
                          self.db, 'John Smith')

        # Add a pair of unique identities first
        api.add_unique_identity(self.db, 'Jonh Smith')
        api.add_unique_identity(self.db, 'John Doe')
        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Doe', 'Example')

        # The error should be the same
        self.assertRaises(NotFoundError, api.delete_unique_identity,
                          self.db, 'Jane Rae')

        # Nothing has been deleted from the registry
        with self.db.connect() as session:
            ids = session.query(UniqueIdentity).all()
            self.assertEqual(len(ids), 2)

            enrollments = session.query(Enrollment).all()
            self.assertEqual(len(enrollments), 1)


class TestDeleteIdentity(TestAPICaseBase):
    """Unit tests for delete_identity"""

    def test_delete_identities(self):
        """Check whether it deletes a set of identities"""

        # First, add a set of identities
        jsmith_uuid = api.add_identity(self.db, 'scm', 'jsmith@example')
        jsmith = api.add_identity(self.db, 'scm', 'jsmith@example', 'John Smith',
                                  uuid=jsmith_uuid)
        jdoe_uuid = api.add_identity(self.db, 'scm', 'jdoe@example')
        jrae_uuid = api.add_identity(self.db, 'scm', 'jrae@example', 'Jane Rae')

        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, jsmith_uuid, 'Example')
        api.add_enrollment(self.db, jdoe_uuid, 'Example')

        api.add_organization(self.db, 'Bitergia')
        api.add_enrollment(self.db, jsmith_uuid, 'Bitergia')

        api.add_organization(self.db, 'LibreSoft')
        api.add_enrollment(self.db, jrae_uuid, 'LibreSoft')

        # Delete the first identity
        api.delete_identity(self.db, jsmith)

        with self.db.connect() as session:
            uid1 = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == jsmith_uuid).first()
            self.assertEqual(uid1.uuid, jsmith_uuid)
            self.assertEqual(len(uid1.identities), 1)

            identities = session.query(Identity).\
                filter(Identity.id == jsmith).all()
            self.assertEqual(len(identities), 0)

            enrollments = session.query(Enrollment).join(UniqueIdentity).\
                filter(UniqueIdentity.uuid == jsmith_uuid).all()
            self.assertEqual(len(enrollments), 2)

        # Delete the last identity
        api.delete_identity(self.db, jrae_uuid)

        with self.db.connect() as session:
            uid2 = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == jrae_uuid).first()
            self.assertEqual(uid2.uuid, jrae_uuid)
            self.assertEqual(len(uid2.identities), 0)

            # Check if there only remains three unique identities and
            # two identities (one from John Smith and another one
            # from John Doe)
            uidentities = session.query(UniqueIdentity).\
                order_by(UniqueIdentity.uuid).all()
            self.assertEqual(len(uidentities), 3)
            self.assertEqual(uidentities[0].uuid, jdoe_uuid)
            self.assertEqual(uidentities[1].uuid, jrae_uuid)
            self.assertEqual(uidentities[2].uuid, jsmith_uuid)

            identities = session.query(Identity).\
                order_by(Identity.id).all()
            self.assertEqual(len(identities), 2)
            self.assertEqual(identities[0].id, jdoe_uuid)
            self.assertEqual(identities[1].id, jsmith_uuid)

            enrollments = session.query(Enrollment).all()
            self.assertEqual(len(enrollments), 4)

            orgs = session.query(Organization).all()
            self.assertEqual(len(orgs), 3)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        # First, add a set of identities
        before_dt = datetime.datetime.utcnow()
        jsmith_uuid = api.add_identity(self.db, 'scm', 'jsmith@example')
        jsmith = api.add_identity(self.db, 'scm', 'jsmith@example', 'John Smith',
                                  uuid=jsmith_uuid)
        after_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == jsmith_uuid).first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertGreaterEqual(after_dt, uid.last_modified)

        # Delete an identity
        before_del_dt = datetime.datetime.utcnow()
        api.delete_identity(self.db, jsmith)
        after_del_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == jsmith_uuid).first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertLessEqual(after_dt, uid.last_modified)
            self.assertLessEqual(before_del_dt, uid.last_modified)
            self.assertGreaterEqual(after_del_dt, uid.last_modified)

    def test_not_found_id(self):
        """Check if it fails removing an identity that does not exists"""

        # It should raise an error when the registry is empty
        self.assertRaises(NotFoundError, api.delete_identity,
                          self.db, 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

        # Add a pair of identities first
        id1 = api.add_identity(self.db, 'scm',
                               'jsmith@example.com', 'John Smith', 'jsmith')
        id2 = api.add_identity(self.db, 'scm',
                               'jdoe@example.com', 'John Doe', 'jdoe')

        # The error should be the same
        self.assertRaises(NotFoundError, api.delete_identity,
                          self.db, 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')

        # Nothing has been deleted from the registry
        with self.db.connect() as session:
            ids = session.query(UniqueIdentity).all()
            self.assertEqual(len(ids), 2)

            ids = session.query(Identity).all()
            self.assertEqual(len(ids), 2)
            self.assertEqual(ids[0].id, id1)
            self.assertEqual(ids[1].id, id2)


class TestDeleteOrganization(TestAPICaseBase):
    """Unit tests for delete_organization"""

    def test_delete_organizations(self):
        """Check whether it deletes a set of organizations"""

        # First, add a set of organizations, including some domains
        # and enrollments
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')
        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com')
        api.add_domain(self.db, 'Example', 'example.org')
        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_enrollment(self.db, 'John Doe', 'Example')
        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia')
        api.add_organization(self.db, 'LibreSoft')

        # Delete the first organization
        api.delete_organization(self.db, 'Example')

        with self.db.connect() as session:
            org1 = session.query(Organization).\
                filter(Organization.name == 'Example').first()
            self.assertEqual(org1, None)

            dom1 = session.query(Domain).\
                filter(Domain.domain == 'example.com').first()
            self.assertEqual(dom1, None)
            dom2 = session.query(Domain).\
                filter(Domain.domain == 'example.org').first()
            self.assertEqual(dom2, None)

            enr1 = session.query(Enrollment).join(Organization).\
                filter(Organization.name == 'Example').first()
            self.assertEqual(enr1, None)

        # Delete the last organization
        api.delete_organization(self.db, 'LibreSoft')

        with self.db.connect() as session:
            org2 = session.query(Organization).\
                filter(Organization.name == 'LibreSoft').first()
            self.assertEqual(org2, None)

            # Check if there only remains one organization and one domain
            orgs = session.query(Organization).all()
            self.assertEqual(len(orgs), 1)
            self.assertEqual(orgs[0].name, 'Bitergia')

            doms = session.query(Domain).all()
            self.assertEqual(len(doms), 1)
            self.assertEqual(doms[0].domain, 'bitergia.com')

            enrollments = session.query(Enrollment).all()
            self.assertEqual(len(enrollments), 1)
            self.assertEqual(enrollments[0].uidentity.uuid, 'John Smith')
            self.assertEqual(enrollments[0].organization.name, 'Bitergia')

    def test_not_found_organization(self):
        """Check if it fails removing an organization that does not exists"""

        # It should raise an error when the registry is empty
        self.assertRaises(NotFoundError, api.delete_organization,
                          self.db, 'Example')

        # Add a pair of organizations first
        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')

        # The error should be the same
        self.assertRaises(NotFoundError, api.delete_organization,
                          self.db, 'LibreSoft')

        # Nothing has been deleted from the registry
        with self.db.connect() as session:
            orgs = session.query(Organization).all()
            self.assertEqual(len(orgs), 2)

            doms = session.query(Domain).all()
            self.assertEqual(len(doms), 1)


class TestDeleteDomain(TestAPICaseBase):
    """Unit tests for delete_domain"""

    def test_delete_domains(self):
        """Check whether it deletes a set of domains"""

        # First, add a set of organizations, including some domains
        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com')
        api.add_domain(self.db, 'Example', 'example.org')
        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')
        api.add_organization(self.db, 'LibreSoft')

        # Delete some domains
        api.delete_domain(self.db, 'Example', 'example.org')
        api.delete_domain(self.db, 'Bitergia', 'bitergia.com')

        with self.db.connect() as session:
            doms1 = session.query(Domain).join(Organization).\
                filter(Organization.name == 'Example').all()
            self.assertEqual(len(doms1), 1)
            self.assertEqual(doms1[0].domain, 'example.com')

            doms2 = session.query(Domain).join(Organization).\
                filter(Organization.name == 'Bitergia').all()
            self.assertEqual(len(doms2), 0)

        # Delete the last domain
        api.delete_domain(self.db, 'Example', 'example.com')

        with self.db.connect() as session:
            doms3 = session.query(Domain).join(Organization).\
                filter(Organization.name == 'Example').all()
            self.assertEqual(len(doms3), 0)

            doms4 = session.query(Domain).all()
            self.assertEqual(len(doms4), 0)

    def test_not_found_organization(self):
        """Check if it fails removing a domain from an organization
           that does not exists"""

        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')

        self.assertRaises(NotFoundError, api.delete_domain,
                          self.db, 'LibreSoft', 'libresoft.es')

        # Nothing has been deleted from the registry
        with self.db.connect() as session:
            orgs = session.query(Organization).all()
            self.assertEqual(len(orgs), 2)

            doms = session.query(Domain).all()
            self.assertEqual(len(doms), 1)

    def test_not_found_domain(self):
        """Check if it fails removing a domain that does not exists"""

        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')

        self.assertRaises(NotFoundError, api.delete_domain,
                          self.db, 'Example', 'example.com')

        # It should not fail because the domain is assigned
        # to other company
        self.assertRaises(NotFoundError, api.delete_domain,
                          self.db, 'Example', 'bitergia.com')

        # Nothing has been deleted from the registry
        with self.db.connect() as session:
            orgs = session.query(Organization).all()
            self.assertEqual(len(orgs), 2)

            doms = session.query(Domain).all()
            self.assertEqual(len(doms), 1)


class TestDeleteEnrollment(TestAPICaseBase):
    """Unit tests for delete_enrollment"""

    def test_delete_enrollments(self):
        """Check whether it deletes a set of enrollments"""

        # First, add a set of uuids, organizations and enrollments
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')
        api.add_unique_identity(self.db, 'Jane Rae')

        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_enrollment(self.db, 'John Doe', 'Example')
        api.add_organization(self.db, 'Bitergia')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2000, 1, 1))
        api.add_organization(self.db, 'LibreSoft')
        api.add_enrollment(self.db, 'John Doe', 'LibreSoft')
        api.add_enrollment(self.db, 'Jane Rae', 'LibreSoft')

        # Delete some enrollments
        api.delete_enrollment(self.db, 'John Doe', 'LibreSoft')
        api.delete_enrollment(self.db, 'John Doe', 'Example')

        with self.db.connect() as session:
            enrollments = session.query(Enrollment).join(Organization).\
                filter(Organization.name == 'LibreSoft').all()
            self.assertEqual(len(enrollments), 1)
            self.assertEqual(enrollments[0].uidentity.uuid, 'Jane Rae')

            enrollments = session.query(Enrollment).join(Organization).\
                filter(Organization.name == 'Example').all()
            self.assertEqual(len(enrollments), 1)
            self.assertEqual(enrollments[0].uidentity.uuid, 'John Smith')

        # Delete enrollments from Bitergia
        api.delete_enrollment(self.db, 'John Smith', 'Bitergia')

        with self.db.connect() as session:
            enrollments = session.query(Enrollment).join(Organization).\
                filter(Organization.name == 'Bitergia').all()
            self.assertEqual(len(enrollments), 0)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'LibreSoft')

        before_dt = datetime.datetime.utcnow()
        api.add_unique_identity(self.db, 'John Doe')
        api.add_enrollment(self.db, 'John Doe', 'Example')
        api.add_enrollment(self.db, 'John Doe', 'LibreSoft')
        after_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Doe').first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertGreaterEqual(after_dt, uid.last_modified)

        # Delete some enrollments
        before_del_dt = datetime.datetime.utcnow()
        api.delete_enrollment(self.db, 'John Doe', 'LibreSoft')
        api.delete_enrollment(self.db, 'John Doe', 'Example')
        after_del_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Doe').first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertLessEqual(after_dt, uid.last_modified)
            self.assertLessEqual(before_del_dt, uid.last_modified)
            self.assertGreaterEqual(after_del_dt, uid.last_modified)

    def test_delete_with_period_ranges(self):
        """Check whether it deletes a set of enrollments using some periods"""

        # First, add a set of uuids, organizations and enrollments
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')

        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2010, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1981, 1, 1),
                           datetime.datetime(1990, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1991, 1, 1),
                           datetime.datetime(1993, 1, 1))

        # This should delete two enrolmments: 1981-1990 and 1991-1993
        # but not the one from 1999-2010 nor 1900-21000
        api.delete_enrollment(self.db, 'John Smith', 'Example',
                              datetime.datetime(1970, 1, 1),
                              datetime.datetime(1995, 1, 1))

        with self.db.connect() as session:
            enrollments = session.query(Enrollment).join(Organization).\
                filter(Organization.name == 'Example').\
                order_by(Enrollment.start).all()
            self.assertEqual(len(enrollments), 2)

            self.assertEqual(enrollments[0].start, datetime.datetime(1900, 1, 1))
            self.assertEqual(enrollments[0].end, datetime.datetime(2100, 1, 1))

            self.assertEqual(enrollments[1].start, datetime.datetime(1999, 1, 1))
            self.assertEqual(enrollments[1].end, datetime.datetime(2010, 1, 1))

    def test_period_ranges(self):
        """Check whether enrollments cannot be removed giving invalid period ranges"""

        api.add_unique_identity(self.db, 'John Smith')
        api.add_organization(self.db, 'Example')

        self.assertRaisesRegex(ValueError, ENROLLMENT_PERIOD_INVALID_ERROR,
                               api.delete_enrollment, self.db, 'John Smith', 'Example',
                               datetime.datetime(2001, 1, 1),
                               datetime.datetime(1999, 1, 1))

        exc = ENROLLMENT_PERIOD_OUT_OF_BOUNDS_ERROR % {'type': 'from_date',
                                                       'date': '1899-12-31 23:59:59'}
        self.assertRaisesRegex(ValueError, exc,
                               api.delete_enrollment, self.db, 'John Smith', 'Example',
                               datetime.datetime(1899, 12, 31, 23, 59, 59))

        exc = ENROLLMENT_PERIOD_OUT_OF_BOUNDS_ERROR % {'type': 'from_date',
                                                       'date': '2100-01-01 00:00:01'}
        self.assertRaisesRegex(ValueError, exc,
                               api.delete_enrollment, self.db, 'John Smith', 'Example',
                               datetime.datetime(2100, 1, 1, 0, 0, 1))

        exc = ENROLLMENT_PERIOD_OUT_OF_BOUNDS_ERROR % {'type': 'to_date',
                                                       'date': '2100-01-01 00:00:01'}
        self.assertRaisesRegex(ValueError, exc,
                               api.delete_enrollment, self.db, 'John Smith', 'Example',
                               datetime.datetime(1900, 1, 1),
                               datetime.datetime(2100, 1, 1, 0, 0, 1))

        exc = ENROLLMENT_PERIOD_OUT_OF_BOUNDS_ERROR % {'type': 'to_date',
                                                       'date': '1899-12-31 23:59:59'}
        self.assertRaisesRegex(ValueError, exc,
                               api.delete_enrollment, self.db, 'John Smith', 'Example',
                               datetime.datetime(1900, 1, 1),
                               datetime.datetime(1899, 12, 31, 23, 59, 59))

    def test_not_found_uuid(self):
        """Check if it fails removing enrollments from a unique identity
           that does not exists"""

        api.add_unique_identity(self.db, 'John Smith')
        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_organization(self.db, 'Bitergia')

        self.assertRaises(NotFoundError, api.delete_enrollment,
                          self.db, 'John Doe', 'Example')

        # Nothing has been deleted from the registry
        with self.db.connect() as session:
            uids = session.query(UniqueIdentity).all()
            self.assertEqual(len(uids), 1)

            orgs = session.query(Organization).all()
            self.assertEqual(len(orgs), 2)

            enrollments = session.query(Enrollment).all()
            self.assertEqual(len(enrollments), 1)

    def test_not_found_organization(self):
        """Check if it fails removing enrollments from an organization
           that does not exists"""

        api.add_unique_identity(self.db, 'John Smith')
        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_organization(self.db, 'Bitergia')

        self.assertRaises(NotFoundError, api.delete_enrollment,
                          self.db, 'John Smith', 'LibreSoft')

        # Nothing has been deleted from the registry
        with self.db.connect() as session:
            uids = session.query(UniqueIdentity).all()
            self.assertEqual(len(uids), 1)

            orgs = session.query(Organization).all()
            self.assertEqual(len(orgs), 2)

            enrollments = session.query(Enrollment).all()
            self.assertEqual(len(enrollments), 1)


class TestDeleteFromMatchingBlacklist(TestAPICaseBase):
    """Unit tests for delete_from_matching_blacklist"""

    def test_delete_blacklisted_entity(self):
        """Check whether it deletes a set of blacklisted entities"""

        # First, add a set of blacklisted entities
        api.add_to_matching_blacklist(self.db, 'root@example.com')
        api.add_to_matching_blacklist(self.db, 'Bitergia')
        api.add_to_matching_blacklist(self.db, 'John Doe')

        # Delete the first entity
        api.delete_from_matching_blacklist(self.db, 'root@example.com')

        with self.db.connect() as session:
            mb1 = session.query(MatchingBlacklist).\
                filter(MatchingBlacklist.excluded == 'root@example.net').first()
            self.assertEqual(mb1, None)

        # Delete the last entity
        api.delete_from_matching_blacklist(self.db, 'John Doe')

        with self.db.connect() as session:
            mb2 = session.query(MatchingBlacklist).\
                filter(MatchingBlacklist.excluded == 'John Doe').first()
            self.assertEqual(mb2, None)

            # Check if there only remains one entity
            mbs = session.query(MatchingBlacklist).all()
            self.assertEqual(len(mbs), 1)
            self.assertEqual(mbs[0].excluded, 'Bitergia')

    def test_not_found_blacklisted_entity(self):
        """Check if it fails removing an entity that does not exists"""

        # It should raise an error when the registry is empty
        self.assertRaises(NotFoundError, api.delete_from_matching_blacklist,
                          self.db, 'root@example.com')

        # Add a pair of entities first
        api.add_to_matching_blacklist(self.db, 'root@example.com')
        api.add_to_matching_blacklist(self.db, 'John Doe')

        # The error should be the same
        self.assertRaises(NotFoundError, api.delete_from_matching_blacklist,
                          self.db, 'John Smith')

        # Nothing has been deleted from the registry
        with self.db.connect() as session:
            mbs = session.query(MatchingBlacklist).all()
            self.assertEqual(len(mbs), 2)


class TestMergeEnrollments(TestAPICaseBase):
    """Unite tests for merge_enrollments"""

    def test_merge_enrollments(self):
        """Check if it merges a set of enrollments"""

        api.add_unique_identity(self.db, 'John Smith')
        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1900, 1, 1),
                           datetime.datetime(2010, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(2008, 1, 1),
                           datetime.datetime(2100, 1, 1))

        api.add_unique_identity(self.db, 'John Doe')
        api.add_enrollment(self.db, 'John Doe', 'Example',
                           datetime.datetime(2010, 1, 2),
                           datetime.datetime(2100, 1, 1))
        api.add_enrollment(self.db, 'John Doe', 'Example',
                           datetime.datetime(2008, 1, 1),
                           datetime.datetime(2010, 1, 1))
        api.add_enrollment(self.db, 'John Doe', 'Example',
                           datetime.datetime(1900, 1, 1),
                           datetime.datetime(2010, 1, 1))

        api.add_unique_identity(self.db, 'Jane Rae')
        api.add_organization(self.db, 'Bitergia')
        api.add_enrollment(self.db, 'Jane Rae', 'Bitergia',
                           datetime.datetime(2010, 1, 2),
                           datetime.datetime(2100, 1, 1))
        api.add_enrollment(self.db, 'Jane Rae', 'Bitergia',
                           datetime.datetime(1900, 1, 1),
                           datetime.datetime(2010, 1, 1))

        # This enrollments will not be merged
        api.add_enrollment(self.db, 'John Smith', 'Bitergia',
                           datetime.datetime(1900, 1, 1),
                           datetime.datetime(2010, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Bitergia',
                           datetime.datetime(2008, 1, 1),
                           datetime.datetime(2100, 1, 1))

        # Tests John Smith enrollments
        api.merge_enrollments(self.db, 'John Smith', 'Example')

        with self.db.connect() as session:
            enrollments = session.query(Enrollment).\
                join(UniqueIdentity, Organization).\
                filter(UniqueIdentity.uuid == 'John Smith',
                       Organization.name == 'Example').all()
            self.assertEqual(len(enrollments), 1)

            rol0 = enrollments[0]
            self.assertEqual(rol0.start, datetime.datetime(2008, 1, 1))
            self.assertEqual(rol0.end, datetime.datetime(2010, 1, 1))

            # Enrollments on Bitergia were not modified
            enrollments = session.query(Enrollment).\
                join(UniqueIdentity, Organization).\
                filter(UniqueIdentity.uuid == 'John Smith',
                       Organization.name == 'Bitergia').\
                order_by(Enrollment.start).all()
            self.assertEqual(len(enrollments), 2)

            rol0 = enrollments[0]
            self.assertEqual(rol0.start, datetime.datetime(1900, 1, 1))
            self.assertEqual(rol0.end, datetime.datetime(2010, 1, 1))

            rol1 = enrollments[1]
            self.assertEqual(rol1.start, datetime.datetime(2008, 1, 1))
            self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1))

        # Test Jonh Doe enrollments
        api.merge_enrollments(self.db, 'John Doe', 'Example')

        with self.db.connect() as session:
            enrollments = session.query(Enrollment).\
                join(UniqueIdentity, Organization).\
                filter(UniqueIdentity.uuid == 'John Doe',
                       Organization.name == 'Example').\
                order_by(Enrollment.start).all()
            self.assertEqual(len(enrollments), 2)

            rol0 = enrollments[0]
            self.assertEqual(rol0.start, datetime.datetime(2008, 1, 1))
            self.assertEqual(rol0.end, datetime.datetime(2010, 1, 1))

            rol1 = enrollments[1]
            self.assertEqual(rol1.start, datetime.datetime(2010, 1, 2))
            self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1))

        # Test Jane Rae enrollments
        api.merge_enrollments(self.db, 'Jane Rae', 'Bitergia')

        with self.db.connect() as session:
            enrollments = session.query(Enrollment).\
                join(UniqueIdentity, Organization).\
                filter(UniqueIdentity.uuid == 'Jane Rae',
                       Organization.name == 'Bitergia').\
                order_by(Enrollment.start).all()
            self.assertEqual(len(enrollments), 2)

            rol0 = enrollments[0]
            self.assertEqual(rol0.start, datetime.datetime(1900, 1, 1))
            self.assertEqual(rol0.end, datetime.datetime(2010, 1, 1))

            rol1 = enrollments[1]
            self.assertEqual(rol1.start, datetime.datetime(2010, 1, 2))
            self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1))

    def test_last_modified(self):
        """Check if last modification date is updated"""

        api.add_organization(self.db, 'Example')

        before_dt = datetime.datetime.utcnow()
        api.add_unique_identity(self.db, 'John Smith')
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1900, 1, 1),
                           datetime.datetime(2010, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(2008, 1, 1),
                           datetime.datetime(2100, 1, 1))
        after_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertGreaterEqual(after_dt, uid.last_modified)

        # Merge enrollments
        before_merge_dt = datetime.datetime.utcnow()
        api.merge_enrollments(self.db, 'John Smith', 'Example')
        after_merge_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertLessEqual(after_dt, uid.last_modified)
            self.assertLessEqual(before_merge_dt, uid.last_modified)
            self.assertGreaterEqual(after_merge_dt, uid.last_modified)

    def test_not_found_uuid(self):
        """Check if it fails merging enrollments from a unique identity
           that does not exists"""

        # Add some data first
        api.add_unique_identity(self.db, 'John Smith')
        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1900, 1, 1),
                           datetime.datetime(2010, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(2008, 1, 1),
                           datetime.datetime(2100, 1, 1))
        api.add_organization(self.db, 'Bitergia')

        # Test
        self.assertRaises(NotFoundError, api.merge_enrollments,
                          self.db, 'John Doe', 'Example')

        # Nothing has been merged on the registry
        with self.db.connect() as session:
            enrollments = session.query(Enrollment).all()
            self.assertEqual(len(enrollments), 2)

    def test_not_found_organization(self):
        """Check if it fails merging enrollments from an organization
           that does not exists"""

        # Add some data first
        api.add_unique_identity(self.db, 'John Smith')
        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1900, 1, 1),
                           datetime.datetime(2010, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(2008, 1, 1),
                           datetime.datetime(2100, 1, 1))
        api.add_organization(self.db, 'Bitergia')

        # Test
        self.assertRaises(NotFoundError, api.merge_enrollments,
                          self.db, 'John Smith', 'LibreSoft')

        # Nothing has been merged on the registry
        with self.db.connect() as session:
            enrollments = session.query(Enrollment).all()
            self.assertEqual(len(enrollments), 2)

    def test_not_found_enrollments(self):
        """Check if it fails merging enrollments that do not exist"""

        # Add some data first
        api.add_unique_identity(self.db, 'John Smith')
        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1900, 1, 1),
                           datetime.datetime(2010, 1, 1))
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(2008, 1, 1),
                           datetime.datetime(2100, 1, 1))
        api.add_organization(self.db, 'Bitergia')

        # Test
        self.assertRaises(NotFoundError, api.merge_enrollments,
                          self.db, 'John Smith', 'Bitergia')

        # Nothing has been merged on the registry
        with self.db.connect() as session:
            enrollments = session.query(Enrollment).all()
            self.assertEqual(len(enrollments), 2)


class TestMergeUniqueIdentities(TestAPICaseBase):
    """Unit tests for merge_unique_identities"""

    def test_merge_identitites(self):
        """Test behavior merging unique identities"""

        # Add some countries, unique identities, identities and
        # enrollments first
        with self.db.connect() as session:
            # Add a country
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)

        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com', 'John Smith',
                         uuid='John Smith')
        api.edit_profile(self.db, 'John Smith', name='John Smith',
                         gender='male', gender_acc=75,
                         is_bot=True, country_code='US')

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         uuid='John Doe')
        api.edit_profile(self.db, 'John Doe', email='jdoe@example.com', is_bot=False)

        api.add_unique_identity(self.db, 'Jane Rae')

        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_enrollment(self.db, 'John Doe', 'Example')

        api.add_organization(self.db, 'Bitergia')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia')
        api.add_enrollment(self.db, 'John Doe', 'Bitergia',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2000, 1, 1))

        api.add_organization(self.db, 'LibreSoft')
        api.add_enrollment(self.db, 'Jane Rae', 'LibreSoft')

        # Merge John Smith and John Doe unique identities
        api.merge_unique_identities(self.db, 'John Smith', 'John Doe')

        with self.db.connect() as session:
            uidentities = session.query(UniqueIdentity).\
                order_by(UniqueIdentity.uuid).all()
            self.assertEqual(len(uidentities), 2)

            uid1 = uidentities[0]
            self.assertEqual(uid1.uuid, 'Jane Rae')
            self.assertEqual(len(uid1.identities), 0)
            self.assertEqual(len(uid1.enrollments), 1)

            uid2 = uidentities[1]
            self.assertEqual(uid2.uuid, 'John Doe')

            self.assertEqual(uid2.profile.uuid, 'John Doe')
            self.assertEqual(uid2.profile.name, 'John Smith')
            self.assertEqual(uid2.profile.email, 'jdoe@example.com')
            self.assertEqual(uid2.profile.gender, 'male')
            self.assertEqual(uid2.profile.gender_acc, 75)
            self.assertEqual(uid2.profile.is_bot, True)
            self.assertEqual(uid2.profile.country_code, 'US')
            self.assertEqual(uid2.profile.country.code, 'US')
            self.assertEqual(uid2.profile.country.name, 'United States of America')

            self.assertEqual(len(uid2.identities), 3)

            identities = uid2.identities
            identities.sort(key=lambda x: x.id)

            id1 = identities[0]
            self.assertEqual(id1.name, None)
            self.assertEqual(id1.email, 'jdoe@example.com')
            self.assertEqual(id1.source, 'scm')

            id2 = identities[1]
            self.assertEqual(id2.name, None)
            self.assertEqual(id2.email, 'jsmith@example.com')
            self.assertEqual(id2.source, 'scm')

            id3 = identities[2]
            self.assertEqual(id3.name, 'John Smith')
            self.assertEqual(id3.email, 'jsmith@example.com')
            self.assertEqual(id3.source, 'scm')

            # Duplicate enrollments should had been removed
            # and overlaped enrollments shoud had been merged
            enrollments = uid2.enrollments
            enrollments.sort(key=lambda x: x.start)
            self.assertEqual(len(enrollments), 2)

            rol1 = enrollments[0]
            self.assertEqual(rol1.organization.name, 'Example')
            self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1))
            self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1))

            rol2 = enrollments[1]
            self.assertEqual(rol2.organization.name, 'Bitergia')
            self.assertEqual(rol2.start, datetime.datetime(1999, 1, 1))
            self.assertEqual(rol2.end, datetime.datetime(2000, 1, 1))

    def test_moved_enrollments(self):
        """Test if enrollments are moved from one identity to another"""

        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         uuid='John Doe')

        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example')

        api.add_organization(self.db, 'Bitergia')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia')

        api.merge_unique_identities(self.db, 'John Smith', 'John Doe')

        with self.db.connect() as session:
            uidentities = session.query(UniqueIdentity).\
                order_by(UniqueIdentity.uuid).all()
            self.assertEqual(len(uidentities), 1)
            self.assertEqual(len(uidentities[0].enrollments), 2)

    def test_last_modified(self):
        """Check if last modification date is updated"""

        before_dt = datetime.datetime.utcnow()
        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com', 'John Smith',
                         uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         uuid='John Doe')
        after_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertGreaterEqual(after_dt, uid.last_modified)

            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Doe').first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertGreaterEqual(after_dt, uid.last_modified)

        # Merge identities
        before_merge_dt = datetime.datetime.utcnow()
        api.merge_unique_identities(self.db, 'John Smith', 'John Doe')
        after_merge_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Doe').first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertLessEqual(after_dt, uid.last_modified)
            self.assertLessEqual(before_merge_dt, uid.last_modified)
            self.assertGreaterEqual(after_merge_dt, uid.last_modified)

            # Not merged identity were not modified
            self.assertLessEqual(before_dt, uid.identities[0].last_modified)
            self.assertGreaterEqual(after_dt, uid.identities[0].last_modified)
            self.assertGreaterEqual(before_merge_dt, uid.identities[0].last_modified)
            self.assertGreaterEqual(after_merge_dt, uid.identities[0].last_modified)

    def test_merge_identities_and_swap_profile(self):
        """Test swap of profiles when a unique identity does not have one"""

        # Add some countries, unique identities, identities and
        # enrollments first
        with self.db.connect() as session:
            # Add a country
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)

        api.add_unique_identity(self.db, 'John Smith')
        api.edit_profile(self.db, 'John Smith', name='John Smith', is_bot=True,
                         country_code='US')

        api.add_unique_identity(self.db, 'Jane Rae')

        # Merge John Smith and Jane Rae unique identities
        # John Smith profile should be swapped to Jane Rae
        api.merge_unique_identities(self.db, 'John Smith', 'Jane Rae')

        with self.db.connect() as session:
            uidentities = session.query(UniqueIdentity).all()
            self.assertEqual(len(uidentities), 1)

            uid1 = uidentities[0]
            self.assertEqual(uid1.uuid, 'Jane Rae')

            self.assertEqual(uid1.profile.uuid, 'Jane Rae')
            self.assertEqual(uid1.profile.name, 'John Smith')
            self.assertEqual(uid1.profile.email, None)
            self.assertEqual(uid1.profile.gender, None)
            self.assertEqual(uid1.profile.gender_acc, None)
            self.assertEqual(uid1.profile.is_bot, True)
            self.assertEqual(uid1.profile.country_code, 'US')
            self.assertEqual(uid1.profile.country.code, 'US')
            self.assertEqual(uid1.profile.country.name, 'United States of America')

    def test_equal_unique_identities(self):
        """Test that all remains the same when 'from' and 'to' identities are the same"""

        # Add some unique identities and identities
        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com', 'John Smith',
                         uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         uuid='John Doe')

        # Merge the same identity
        api.merge_unique_identities(self.db, 'John Smith', 'John Smith')

        # Nothing has happened
        with self.db.connect() as session:
            uidentities = session.query(UniqueIdentity).\
                order_by(UniqueIdentity.uuid).all()
            self.assertEqual(len(uidentities), 2)

            uid2 = uidentities[1]
            self.assertEqual(uid2.uuid, 'John Smith')
            self.assertEqual(len(uid2.identities), 2)

    def test_not_found_unique_identities(self):
        """Test whether it fails when one of the unique identities is not found"""

        # Add some unique identities first
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')

        # Check 'from_uuid' parameter
        self.assertRaisesRegex(NotFoundError,
                               NOT_FOUND_ERROR % {'entity': 'Jane Roe'},
                               api.merge_unique_identities,
                               self.db, 'Jane Roe', 'John Smith')

        # Check 'to_uuid' parameter
        self.assertRaisesRegex(NotFoundError,
                               NOT_FOUND_ERROR % {'entity': 'Jane Roe'},
                               api.merge_unique_identities,
                               self.db, 'John Smith', 'Jane Roe')

        # Even if the identities are the same and do not exist, it still
        # raises the exception
        self.assertRaisesRegex(NotFoundError,
                               NOT_FOUND_ERROR % {'entity': 'Jane Roe'},
                               api.merge_unique_identities,
                               self.db, 'Jane Roe', 'Jane Roe')


class TestMoveIdentity(TestAPICaseBase):
    """Unit tests for move_identity"""

    def test_move_identity(self):
        """Test when an identity is moved to a unique identity"""

        # Add some unique identities and identities first
        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com', 'John Smith',
                         uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        from_id = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                   uuid='John Doe')

        api.move_identity(self.db, from_id, 'John Smith')

        with self.db.connect() as session:
            uidentities = session.query(UniqueIdentity).\
                order_by(UniqueIdentity.uuid).all()
            self.assertEqual(len(uidentities), 2)

            uid1 = uidentities[0]
            self.assertEqual(uid1.uuid, 'John Doe')
            self.assertEqual(len(uid1.identities), 0)

            uid2 = uidentities[1]
            self.assertEqual(uid2.uuid, 'John Smith')
            self.assertEqual(len(uid2.identities), 3)

            identities = uid2.identities
            identities.sort(key=lambda x: x.id)

            id1 = identities[0]
            self.assertEqual(id1.id, from_id)
            self.assertEqual(id1.name, None)
            self.assertEqual(id1.email, 'jdoe@example.com')
            self.assertEqual(id1.source, 'scm')

            id2 = identities[1]
            self.assertEqual(id2.name, None)
            self.assertEqual(id2.email, 'jsmith@example.com')
            self.assertEqual(id2.source, 'scm')

            id3 = identities[2]
            self.assertEqual(id3.name, 'John Smith')
            self.assertEqual(id3.email, 'jsmith@example.com')
            self.assertEqual(id3.source, 'scm')

    def test_last_modified(self):
        """Check if last modification date is updated"""

        before_dt = datetime.datetime.utcnow()
        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        from_id = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                   uuid='John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com', 'Jon Doe',
                         uuid='John Doe')
        after_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertGreaterEqual(after_dt, uid.last_modified)

            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Doe').first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertGreaterEqual(after_dt, uid.last_modified)

        # Move identities
        before_move_dt = datetime.datetime.utcnow()
        api.move_identity(self.db, from_id, 'John Smith')
        after_move_dt = datetime.datetime.utcnow()

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Smith').first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertLessEqual(after_dt, uid.last_modified)
            self.assertLessEqual(before_move_dt, uid.last_modified)
            self.assertGreaterEqual(after_move_dt, uid.last_modified)

            # Moved identity have the date updated
            self.assertEqual(uid.identities[0].last_modified, uid.last_modified)

            # Identity not moved were not modified
            self.assertLessEqual(before_dt, uid.identities[1].last_modified)
            self.assertGreaterEqual(after_dt, uid.identities[1].last_modified)
            self.assertGreaterEqual(before_move_dt, uid.identities[1].last_modified)
            self.assertGreaterEqual(after_move_dt, uid.identities[1].last_modified)

            # The origin of the moved identity was also updated
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == 'John Doe').first()
            self.assertLessEqual(before_dt, uid.last_modified)
            self.assertLessEqual(after_dt, uid.last_modified)
            self.assertLessEqual(before_move_dt, uid.last_modified)
            self.assertGreaterEqual(after_move_dt, uid.last_modified)

    def test_equal_related_unique_identity(self):
        """Test that all remains the same when to_uuid is the unique identity related to 'from_id'"""

        # Add some unique identities and identities first
        api.add_unique_identity(self.db, 'John Smith')
        from_id = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                   uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         uuid='John Doe')
        new_uuid = api.add_identity(self.db, 'scm', 'john.doe@example.com',
                                    uuid='John Doe')

        # Move the identity to the same unique identity
        api.move_identity(self.db, from_id, 'John Smith')

        # Nothing has happened
        with self.db.connect() as session:
            uidentities = session.query(UniqueIdentity).all()
            self.assertEqual(len(uidentities), 2)

            uid = uidentities[0]
            self.assertEqual(uid.uuid, 'John Doe')
            self.assertEqual(len(uid.identities), 2)

            uid = uidentities[1]
            self.assertEqual(uid.uuid, 'John Smith')
            self.assertEqual(len(uid.identities), 1)

            id1 = uid.identities[0]
            self.assertEqual(id1.id, from_id)

        # This will create a new unique identity,
        # moving the identity to this new unique identity
        api.move_identity(self.db, new_uuid, new_uuid)

        with self.db.connect() as session:
            uidentities = session.query(UniqueIdentity).\
                order_by(UniqueIdentity.uuid).all()
            self.assertEqual(len(uidentities), 3)

            uid = uidentities[0]
            self.assertEqual(uid.uuid, new_uuid)
            self.assertEqual(len(uid.identities), 1)

            id1 = uid.identities[0]
            self.assertEqual(id1.id, new_uuid)

            uid = uidentities[1]
            self.assertEqual(uid.uuid, 'John Doe')
            self.assertEqual(len(uid.identities), 1)

    def test_not_found_identities(self):
        """Test whether it fails when one of identities is not found"""

        # Add some unique identities first
        api.add_unique_identity(self.db, 'John Smith')
        from_id = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                   uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         uuid='John Doe')

        # Check 'from_id' parameter
        self.assertRaisesRegex(NotFoundError,
                               NOT_FOUND_ERROR % {'entity': 'FFFFFFFFFFF'},
                               api.move_identity,
                               self.db, 'FFFFFFFFFFF', 'John Smith')

        # Check 'to_uuid' parameter
        self.assertRaisesRegex(NotFoundError,
                               NOT_FOUND_ERROR % {'entity': 'Jane Roe'},
                               api.move_identity,
                               self.db, from_id, 'Jane Roe')


class TestMatchIdentities(TestAPICaseBase):
    """Unit tests for match_identities"""

    def test_default_matcher(self):
        """Test default identity matcher"""

        # Add some unique identities first
        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')
        api.add_identity(self.db, 'scm', name='John Smith', uuid='John Smith')
        api.add_identity(self.db, 'scm', username='jsmith', uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'mls', 'johndoe@example.com', uuid='John Doe')
        api.add_identity(self.db, 'mls', 'johndoe@example.net', uuid='John Doe')

        api.add_unique_identity(self.db, 'Smith J.')
        api.add_identity(self.db, 'mls', 'JSmith@example.com',
                         uuid='Smith J.')

        api.add_unique_identity(self.db, 'Jane Rae')
        api.add_identity(self.db, 'scm', 'janerae@example.com', 'Jane Rae', uuid='Jane Rae')

        api.add_unique_identity(self.db, 'JRae')
        api.add_identity(self.db, 'mls', name='Jane Rae', username='jrae', uuid='JRae')
        api.add_identity(self.db, 'scm', username='jrae', uuid='JRae')
        api.add_identity(self.db, 'scm', 'janerae@example.com', uuid='JRae')

        api.add_unique_identity(self.db, 'Jane')
        api.add_identity(self.db, 'unknown', 'jane@example.com', 'Jane', uuid='Jane')
        api.add_identity(self.db, 'unknown', 'jane@example.net', 'Jane', uuid='Jane')
        api.add_identity(self.db, 'unknown', 'jane@example.org', 'Jane', uuid='Jane')
        api.add_identity(self.db, 'unknown', 'jrae@example.org', 'Jane', uuid='Jane')
        api.add_identity(self.db, 'unknown', 'jrae@example.com', 'Jane', uuid='Jane')
        api.add_identity(self.db, 'unknown', 'janerae@example.com', 'Jane', uuid='Jane')

        # Tests
        get_uuids = lambda l: [u.uuid for u in l]

        matcher = create_identity_matcher('default')

        # John Smith
        m1 = api.match_identities(self.db, 'John Smith', matcher)
        uids = get_uuids(m1)

        self.assertListEqual(uids, ['Smith J.'])

        # Smith J.
        m1 = api.match_identities(self.db, 'Smith J.', matcher)
        uids = get_uuids(m1)

        self.assertListEqual(uids, ['John Smith'])

        # John Doe
        m2 = api.match_identities(self.db, 'John Doe', matcher)
        uids = get_uuids(m2)

        self.assertListEqual(uids, [])

        # Jane Rae
        m3 = api.match_identities(self.db, 'Jane Rae', matcher)
        uids = get_uuids(m3)

        self.assertListEqual(uids, ['Jane', 'JRae'])

        # JRae
        m3 = api.match_identities(self.db, 'JRae', matcher)
        uids = get_uuids(m3)

        self.assertListEqual(uids, ['Jane', 'Jane Rae'])

        # Jane
        m3 = api.match_identities(self.db, 'Jane', matcher)
        uids = get_uuids(m3)

        self.assertListEqual(uids, ['Jane Rae', 'JRae'])

    def test_empty_registry(self):
        """Test whether it fails when the registry is empty"""

        matcher = create_identity_matcher('default')

        # This test must raise a NotFoundError
        self.assertRaisesRegex(NotFoundError,
                               NOT_FOUND_ERROR % {'entity': 'Jane Roe'},
                               api.match_identities,
                               self.db, 'Jane Roe', matcher)

    def test_not_found_identities(self):
        """Test whether it fails when uuid is not found"""

        # Add some unique identities first
        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')
        api.add_unique_identity(self.db, 'Smith J.')
        api.add_identity(self.db, 'mls', 'jsmith@example.com',
                         uuid='Smith J.')

        matcher = create_identity_matcher('default')

        self.assertRaisesRegex(NotFoundError,
                               NOT_FOUND_ERROR % {'entity': 'Jane Roe'},
                               api.match_identities,
                               self.db, 'Jane Roe', matcher)


class TestUniqueIdentities(TestAPICaseBase):
    """Unit tests for unique_identities"""

    def test_unique_identities(self):
        """Check if it returns the registry of unique identities"""

        # Add a country
        with self.db.connect() as session:
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)

        # Add some identities
        jsmith_uuid = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                       'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@bitergia.com', uuid=jsmith_uuid)
        api.add_identity(self.db, 'mls', 'jsmith@bitergia.com', uuid=jsmith_uuid)
        api.edit_profile(self.db, jsmith_uuid, email='jsmith@example.com',
                         is_bot=True, country_code='US')

        jdoe_uuid = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                     'John Doe', 'jdoe')
        api.add_identity(self.db, 'scm', 'jdoe@libresoft.es', uuid=jdoe_uuid)

        # Tests
        uidentities = api.unique_identities(self.db)
        self.assertEqual(len(uidentities), 2)

        # Test John Smith unique identity
        uid = uidentities[0]
        self.assertEqual(uid.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        self.assertEqual(uid.profile.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(uid.profile.name, None)
        self.assertEqual(uid.profile.email, 'jsmith@example.com')
        self.assertEqual(uid.profile.is_bot, True)
        self.assertEqual(uid.profile.country_code, 'US')
        self.assertEqual(uid.profile.country.code, 'US')
        self.assertEqual(uid.profile.country.name, 'United States of America')

        self.assertEqual(len(uid.identities), 3)

        identities = uid.identities
        identities.sort(key=lambda x: x.id)

        id1 = identities[0]
        self.assertEqual(id1.email, 'jsmith@example.com')

        id2 = identities[1]
        self.assertEqual(id2.email, 'jsmith@bitergia.com')
        self.assertEqual(id2.source, 'mls')

        id3 = identities[2]
        self.assertEqual(id3.email, 'jsmith@bitergia.com')
        self.assertEqual(id3.source, 'scm')

        # Test John Doe unique identity
        uid = uidentities[1]
        self.assertEqual(uid.uuid, 'c6d2504fde0e34b78a185c4b709e5442d045451c')
        self.assertEqual(uid.profile.name, None)
        self.assertEqual(uid.profile.email, None)

        self.assertEqual(len(uid.identities), 2)

        identities = uid.identities
        identities.sort(key=lambda x: x.id)

        id1 = identities[0]
        self.assertEqual(id1.email, 'jdoe@libresoft.es')

        id2 = identities[1]
        self.assertEqual(id2.email, 'jdoe@example.com')

    def test_unique_identities_source(self):
        """Check if it returns the registry of unique identities assigned to a source"""

        # Add some identities
        jsmith_uuid = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                       'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@bitergia.com', uuid=jsmith_uuid)
        api.add_identity(self.db, 'mls', 'jsmith@bitergia.com', uuid=jsmith_uuid)

        jdoe_uuid = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                     'John Doe', 'jdoe')
        api.add_identity(self.db, 'scm', 'jdoe@libresoft.es', uuid=jdoe_uuid)

        # Test unique identities with source 'mls'
        uidentities = api.unique_identities(self.db, source='mls')
        self.assertEqual(len(uidentities), 1)

        uid = uidentities[0]
        self.assertEqual(uid.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        # No unique identities for 'its' source
        uidentities = api.unique_identities(self.db, source='its')
        self.assertEqual(len(uidentities), 0)

    def test_unique_identity_uuid(self):
        """Check if it returns the given unique identitie"""

        # Add some identities
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         'John Doe', 'jdoe')

        # Tests
        uidentities = api.unique_identities(self.db, uuid='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(len(uidentities), 1)

        uid = uidentities[0]
        self.assertEqual(uid.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(len(uid.identities), 1)

        id1 = uid.identities[0]
        self.assertEqual(id1.email, 'jsmith@example.com')

        # Using the source parameter should return the same result
        uidentities = api.unique_identities(self.db,
                                            uuid='a9b403e150dd4af8953a52a4bb841051e4b705d9',
                                            source='scm')
        self.assertEqual(len(uidentities), 1)

        uid = uidentities[0]
        self.assertEqual(uid.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        identities = api.unique_identities(self.db)
        self.assertListEqual(identities, [])

    def test_not_found_uuid(self):
        """Check whether it raises an error when the uuid is not available"""

        # It should raise an error when the registry is empty
        self.assertRaises(NotFoundError, api.unique_identities,
                          self.db, 'John Smith')

        # It should do the same when there are some identities available
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')

        self.assertRaises(NotFoundError, api.unique_identities,
                          self.db, 'Jane Rae')

        # Or even using a valid uuid but an invalid source parameter
        self.assertRaises(NotFoundError, api.unique_identities,
                          self.db, 'John Smith', 'scm')


class TestSearchUniqueIdentities(TestAPICaseBase):
    """Unit tests for search_unique_identities"""

    def test_search_unique_identities(self):
        """Check if it returns the unique identities that match with the criteria"""

        # Add a country
        with self.db.connect() as session:
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)

        # Add some identities
        jsmith_uuid = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                       'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@bitergia.com', uuid=jsmith_uuid)
        api.add_identity(self.db, 'mls', 'jsmith@bitergia.com', uuid=jsmith_uuid)
        api.edit_profile(self.db, jsmith_uuid, email='jsmith@example.com',
                         is_bot=True, country_code='US')

        jdoe_uuid = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                     'John Doe', 'jdoe')
        api.add_identity(self.db, 'scm', 'jdoe@libresoft.es',
                         'jdoe', 'jdoe', uuid=jdoe_uuid)

        # Tests
        uids = api.search_unique_identities(self.db, 'jsmith')
        self.assertEqual(len(uids), 1)
        self.assertEqual(uids[0].uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(len(uids[0].identities), 3)

        uids = api.search_unique_identities(self.db, 'john')
        self.assertEqual(len(uids), 2)
        self.assertEqual(uids[0].uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(len(uids[0].identities), 3)
        self.assertEqual(uids[1].uuid, 'c6d2504fde0e34b78a185c4b709e5442d045451c')
        self.assertEqual(len(uids[1].identities), 2)

        # None values can also be used
        uids = api.search_unique_identities(self.db, None)
        self.assertEqual(len(uids), 1)
        self.assertEqual(uids[0].uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(len(uids[0].identities), 3)

    def test_search_4bytes_utf8_identities(self):
        """Check if it returns the unique identities which have 4 bytes UTF8-characters"""

        # Add some identities
        jsmith_uuid = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                       'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@bitergia.com', uuid=jsmith_uuid)
        api.add_identity(self.db, 'mls', 'jsmith@bitergia.com', uuid=jsmith_uuid)

        jdoe_uuid = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                     'John Doe', 'jdoe')
        api.add_identity(self.db, 'scm', 'jdoe@libresoft.es',
                         'jdoe', 'jdoe', uuid=jdoe_uuid)

        emoji_uuid = api.add_identity(self.db, 'scm', name='😂',
                                      email='😂', username='😂')

        # An emoji is 4 bytes UTF-8 character
        uids = api.search_unique_identities(self.db, '😂')
        self.assertEqual(len(uids), 1)
        self.assertEqual(uids[0].uuid, '843fcc3383ddfd6179bef87996fa761d88a43915')
        self.assertEqual(len(uids[0].identities), 1)

    def test_filter_source(self):
        """Check if it returns a set of identities linked to the given source"""

        # Add some identities
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         'John Smith', 'jsmith')
        api.add_identity(self.db, 'mls', 'jsmith@bitergia.com')

        # Tests
        uids = api.search_unique_identities(self.db, 'jsmith')
        self.assertEqual(len(uids), 2)

        uids = api.search_unique_identities(self.db, 'jsmith', source='scm')
        self.assertEqual(len(uids), 1)
        self.assertEqual(uids[0].uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(len(uids[0].identities), 1)

    def test_empty_registry(self):
        """Check whether it returns an exception when the registry is empty"""

        self.assertRaises(NotFoundError, api.search_unique_identities,
                          self.db, None)

    def test_term_not_found(self):
        """Check whether it raises an error when the term is not found"""

        # It should raise an error when the registry is empty
        self.assertRaises(NotFoundError, api.search_unique_identities,
                          self.db, 'John Smith')

        # It should do the same when there are some identities available
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         'John Doe', 'jdoe')

        self.assertRaises(NotFoundError, api.search_unique_identities,
                          self.db, 'Jane Rae')


class TestSearchUniqueIdentitiesSlice(TestAPICaseBase):
    """Unit tests for search_unique_identitie_slice"""

    def test_search_unique_identities_slice(self):
        """Check if it returns a slice of unique identities that match with the criteria"""

        # Add a country
        with self.db.connect() as session:
            us = Country(code='US', name='United States of America', alpha3='USA')
            session.add(us)

        # Add some identities
        jsmith_uuid = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                       'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@bitergia.com', uuid=jsmith_uuid)
        api.add_identity(self.db, 'mls', 'jsmith@bitergia.com', uuid=jsmith_uuid)
        api.edit_profile(self.db, jsmith_uuid, email='jsmith@example.com',
                         is_bot=True, country_code='US')

        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         'John Doe', 'jdoe')
        api.add_identity(self.db, 'scm', 'jdoe@libresoft.es',
                         'John', 'jdoe')

        # Tests
        uids, ntotal = api.search_unique_identities_slice(self.db, 'jsmith', 0, 100)
        self.assertEqual(len(uids), 1)
        self.assertEqual(ntotal, 1)
        self.assertEqual(uids[0].uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        uids, ntotal = api.search_unique_identities_slice(self.db, 'john', 0, 100)
        self.assertEqual(len(uids), 3)
        self.assertEqual(ntotal, 3)
        self.assertEqual(uids[0].uuid, '56de4d86c1bed9979cd89d98bd2ea4a898f30cc6')
        self.assertEqual(uids[1].uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(uids[2].uuid, 'c6d2504fde0e34b78a185c4b709e5442d045451c')

        # None values can also be used
        uids, ntotal = api.search_unique_identities_slice(self.db, None, 0, 100)
        self.assertEqual(len(uids), 3)
        self.assertEqual(ntotal, 3)
        self.assertEqual(uids[0].uuid, '56de4d86c1bed9979cd89d98bd2ea4a898f30cc6')
        self.assertEqual(uids[1].uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(uids[2].uuid, 'c6d2504fde0e34b78a185c4b709e5442d045451c')

    def test_filter_by_slice(self):
        """Check if it returns a set of identities filtered by slice"""

        # Add some identities
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@bitergia.com')
        api.add_identity(self.db, 'mls', 'jsmith@bitergia.com')
        api.add_identity(self.db, 'scm', 'jdoe@example.com', 'John Doe', 'jdoe')

        # Tests
        uids, ntotal = api.search_unique_identities_slice(self.db, 'jsmith', 0, 2)
        self.assertEqual(len(uids), 2)
        self.assertEqual(ntotal, 3)
        self.assertEqual(uids[0].uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(uids[1].uuid, 'acced28b86278f00a21080d695ecb34b81a1828f')

        uids, ntotal = api.search_unique_identities_slice(self.db, 'jsmith', 2, 2)
        self.assertEqual(len(uids), 1)
        self.assertEqual(ntotal, 3)
        self.assertEqual(uids[0].uuid, 'ebcda394c978d50847d60015892f9ca0f0ccde65')

        # No more results
        uids, ntotal = api.search_unique_identities_slice(self.db, 'jsmith', 3, 2)
        self.assertListEqual(uids, [])
        self.assertEqual(ntotal, 3)

    def test_search_4bytes_utf8_identities_by_slice(self):
        """Check if it returns a slice of unique identities which have 4 bytes UTF8-characters filtered by slice"""

        emoji_name = api.add_identity(self.db, 'scm', name='😂')
        emoji_email = api.add_identity(self.db, 'scm', email='😂')
        emoji_username = api.add_identity(self.db, 'scm', username='😂')
        emoji = api.add_identity(self.db, 'scm', name='😂', email='😂', username='😂')

        # Tests
        uids, ntotal = api.search_unique_identities_slice(self.db, '😂', 0, 2)
        self.assertEqual(len(uids), 2)
        self.assertEqual(ntotal, 4)
        self.assertEqual(uids[0].uuid, emoji_email)
        self.assertEqual(len(uids[0].identities), 1)
        self.assertEqual(uids[1].uuid, emoji)
        self.assertEqual(len(uids[0].identities), 1)

        uids, ntotal = api.search_unique_identities_slice(self.db, '😂', 2, 2)
        self.assertEqual(len(uids), 2)
        self.assertEqual(ntotal, 4)
        self.assertEqual(uids[0].uuid, emoji_name)
        self.assertEqual(len(uids[0].identities), 1)
        self.assertEqual(uids[1].uuid, emoji_username)
        self.assertEqual(len(uids[0].identities), 1)

        # No more results
        uids, ntotal = api.search_unique_identities_slice(self.db, '😂', 4, 2)
        self.assertListEqual(uids, [])
        self.assertEqual(ntotal, 4)

    def test_unique_identities_slice(self):
        """Test if a given number of unique identities is returned"""

        uuid = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@bitergia.com', uuid=uuid)
        api.add_identity(self.db, 'scm', None, None, 'jsmith', uuid=uuid)

        uuid = api.add_identity(self.db, 'scm', 'jdoe@example.com', 'John Doe', 'jdoe')
        api.add_identity(self.db, 'scm', None, 'John Doe', 'jdoe', uuid=uuid)

        # This call should return 2 unique identities at most
        # Even when all the identities match with the request
        uids, ntotal = api.search_unique_identities_slice(self.db, None, 0, 2)
        self.assertEqual(len(uids), 2)
        self.assertEqual(ntotal, 2)
        self.assertEqual(uids[0].uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(uids[1].uuid, 'c6d2504fde0e34b78a185c4b709e5442d045451c')

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        uids, ntotal = api.search_unique_identities_slice(self.db, None, 0, 100)
        self.assertListEqual(uids, [])
        self.assertEqual(ntotal, 0)

    def test_term_not_found(self):
        """Check whether it returns an empty list when the term is not found"""

        # Empty registry
        uids, ntotal = api.search_unique_identities_slice(self.db, 'Jane Rae', 0, 100)
        self.assertListEqual(uids, [])
        self.assertEqual(ntotal, 0)

        # It should do the same when there are some identities available
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         'John Doe', 'jdoe')

        uids, ntotal = api.search_unique_identities_slice(self.db, 'Jane Rae', 0, 100)
        self.assertListEqual(uids, [])
        self.assertEqual(ntotal, 0)

    def test_invalid_offset(self):
        """Check whether it raises an exception when offset value is invalid"""

        self.assertRaises(ValueError, api.search_unique_identities_slice,
                          self.db, None, -1, 100)

    def test_invalid_limit(self):
        """Check whether it raises an exception when limit value is invalid"""

        self.assertRaises(ValueError, api.search_unique_identities_slice,
                          self.db, None, 1, -1)


class TestSearchLastModifiedIdentities(TestAPICaseBase):
    """Unit tests for last_modified_identities"""

    def test_search_last_modified_identities(self):
        """Check if it returns the uuids of the modified identities"""

        # Add identities
        before_dt = datetime.datetime.utcnow()
        api.add_unique_identity(self.db, 'John Smith')
        jsmith_id = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                     uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        jdoe_id = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                   uuid='John Doe')
        jdoe_alt_id = api.add_identity(self.db, 'scm', 'jdoe@example.com', 'Jon Doe',
                                       uuid='John Doe')

        # Check if all uuids are returned
        ids = api.search_last_modified_identities(self.db, before_dt)
        self.assertListEqual(ids, [jdoe_id, jsmith_id, jdoe_alt_id])

        # Update identities
        before_move_dt = datetime.datetime.utcnow()
        api.move_identity(self.db, jdoe_id, 'John Smith')

        # Check if only modified uuids are returned
        ids = api.search_last_modified_identities(self.db, before_move_dt)
        self.assertListEqual(ids, [jdoe_id])

    def test_search_last_modified_unique_identities(self):
        """Check if it returns the uuids of the modified unique identities"""

        # Add identities
        before_dt = datetime.datetime.utcnow()
        api.add_unique_identity(self.db, 'John Smith')
        jsmith_id = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                     uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        jdoe_id = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                   uuid='John Doe')
        jdoe_alt_id = api.add_identity(self.db, 'scm', 'jdoe@example.com', 'Jon Doe',
                                       uuid='John Doe')

        # Check if all uuids are returned
        uuids = api.search_last_modified_unique_identities(self.db, before_dt)
        self.assertListEqual(uuids, ['John Doe', 'John Smith'])

        # Update identities
        before_move_dt = datetime.datetime.utcnow()
        api.move_identity(self.db, jdoe_id, 'John Smith')

        # Check if only modified uuids are returned
        uuids = api.search_last_modified_unique_identities(self.db, before_move_dt)
        self.assertListEqual(uuids, ['John Doe', 'John Smith'])

    def test_empty_search_modified_identities(self):
        """Check if the result is empty when identities are not modified"""

        # Add identities
        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         uuid='John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com', 'Jon Doe',
                         uuid='John Doe')

        after_dt = datetime.datetime.utcnow()

        # Check if all uuids are returned
        ids = api.search_last_modified_identities(self.db, after_dt)
        self.assertListEqual(ids, [])

    def test_empty_search_modified_unique_identities(self):
        """Check if the result is empty when unique identities are not modified"""

        # Add identities
        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         uuid='John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com', 'Jon Doe',
                         uuid='John Doe')

        after_dt = datetime.datetime.utcnow()

        # Check if all uuids are returned
        uuids = api.search_last_modified_unique_identities(self.db, after_dt)
        self.assertListEqual(uuids, [])


class TestSearchProfiles(TestAPICaseBase):
    """Unit tests for search_profiles"""

    def test_search_profiles(self):
        """Check if it returns a list of profiles"""

        # Add some identities
        jsmith_uuid = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                       'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@bitergia.com', uuid=jsmith_uuid)
        api.add_identity(self.db, 'mls', 'jsmith@bitergia.com', uuid=jsmith_uuid)
        api.edit_profile(self.db, jsmith_uuid, email='jsmith@example.com',
                         is_bot=True, gender="male")

        jdoe_uuid = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                     'John Doe', 'jdoe')
        api.add_identity(self.db, 'scm', 'jdoe@libresoft.es',
                         'jdoe', 'jdoe', uuid=jdoe_uuid)
        api.edit_profile(self.db, jdoe_uuid, email='jsmith@example.com',
                         is_bot=False)

        # Tests
        profiles = api.search_profiles(self.db)
        self.assertEqual(len(profiles), 2)

        prf = profiles[0]
        self.assertIsInstance(prf, Profile)
        self.assertEqual(prf.uuid, 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        prf = profiles[1]
        self.assertIsInstance(prf, Profile)
        self.assertEqual(prf.uuid, 'c6d2504fde0e34b78a185c4b709e5442d045451c')

    def test_filter_no_gender(self):
        """Check if it returns a set of profiles which do not have gender"""

        # Add some identities
        jsmith_uuid = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                       'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@bitergia.com', uuid=jsmith_uuid)
        api.add_identity(self.db, 'mls', 'jsmith@bitergia.com', uuid=jsmith_uuid)
        api.edit_profile(self.db, jsmith_uuid, email='jsmith@example.com',
                         is_bot=True, gender="male")

        jdoe_uuid = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                     'John Doe', 'jdoe')
        api.add_identity(self.db, 'scm', 'jdoe@libresoft.es',
                         'jdoe', 'jdoe', uuid=jdoe_uuid)
        api.edit_profile(self.db, jdoe_uuid, email='jsmith@example.com',
                         is_bot=False)

        # Tests
        profiles = api.search_profiles(self.db, no_gender=True)
        self.assertEqual(len(profiles), 1)

        prf = profiles[0]
        self.assertIsInstance(prf, Profile)
        self.assertEqual(prf.uuid, 'c6d2504fde0e34b78a185c4b709e5442d045451c')


class TestRegistry(TestAPICaseBase):
    """Unit tests for registry"""

    def test_get_registry(self):
        """Check if it returns the registry of organizations"""

        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com')
        api.add_domain(self.db, 'Example', 'example.org')
        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')
        api.add_organization(self.db, 'LibreSoft')

        orgs = api.registry(self.db)
        self.assertEqual(len(orgs), 3)

        org1 = orgs[0]
        self.assertIsInstance(org1, Organization)
        self.assertEqual(org1.name, 'Bitergia')
        self.assertEqual(len(org1.domains), 1)

        org2 = orgs[1]
        self.assertIsInstance(org2, Organization)
        self.assertEqual(org2.name, 'Example')
        self.assertEqual(len(org2.domains), 2)

        org3 = orgs[2]
        self.assertIsInstance(org3, Organization)
        self.assertEqual(org3.name, 'LibreSoft')
        self.assertEqual(len(org3.domains), 0)

    def test_get_registry_term(self):
        """Check if it returns the info about orgs using a search term"""

        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com')
        api.add_domain(self.db, 'Example', 'example.org')
        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')
        api.add_organization(self.db, 'My Example')
        api.add_domain(self.db, 'My Example', 'myexample.com')

        # This query have to return two organizations
        orgs = api.registry(self.db, 'Example')
        self.assertEqual(len(orgs), 2)

        # Example organization
        org = orgs[0]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'Example')
        self.assertEqual(len(org.domains), 2)

        domains = org.domains
        domains.sort(key=lambda x: x.domain)

        dom = domains[0]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'example.com')

        dom = domains[1]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'example.org')

        # My Example organization
        org = orgs[1]
        self.assertIsInstance(org, Organization)
        self.assertEqual(org.name, 'My Example')
        self.assertEqual(len(org.domains), 1)

        dom = org.domains[0]
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.domain, 'myexample.com')

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        orgs = api.registry(self.db)
        self.assertListEqual(orgs, [])

    def test_not_found_term(self):
        """Check whether it raises an error when the organization is not available"""

        # It should raise an error when the registry is empty
        self.assertRaises(NotFoundError, api.registry, self.db, 'Example')

        # It should do the same when there are some orgs available
        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')

        self.assertRaises(NotFoundError, api.registry, self.db, 'LibreSoft')


class TestDomains(TestAPICaseBase):
    """Unit tests for domains"""

    def test_get_domains(self):
        """Check if it returns the registry of domains"""

        # Add some domains
        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com', is_top_domain=True)
        api.add_domain(self.db, 'Example', 'u.example.com', is_top_domain=True)
        api.add_domain(self.db, 'Example', 'es.u.example.com')
        api.add_domain(self.db, 'Example', 'en.u.example.com')

        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')
        api.add_domain(self.db, 'Bitergia', 'bitergia.org')

        api.add_organization(self.db, 'LibreSoft')

        doms = api.domains(self.db)
        self.assertEqual(len(doms), 6)

        dom0 = doms[0]
        self.assertIsInstance(dom0, Domain)
        self.assertEqual(dom0.domain, 'bitergia.com')
        self.assertEqual(dom0.organization.name, 'Bitergia')

        dom1 = doms[1]
        self.assertIsInstance(dom1, Domain)
        self.assertEqual(dom1.domain, 'bitergia.org')
        self.assertEqual(dom1.organization.name, 'Bitergia')

        dom2 = doms[2]
        self.assertIsInstance(dom2, Domain)
        self.assertEqual(dom2.domain, 'en.u.example.com')
        self.assertEqual(dom2.organization.name, 'Example')

        dom3 = doms[3]
        self.assertIsInstance(dom3, Domain)
        self.assertEqual(dom3.domain, 'es.u.example.com')
        self.assertEqual(dom3.organization.name, 'Example')

        dom4 = doms[4]
        self.assertIsInstance(dom4, Domain)
        self.assertEqual(dom4.domain, 'example.com')
        self.assertEqual(dom4.organization.name, 'Example')

        dom5 = doms[5]
        self.assertIsInstance(dom5, Domain)
        self.assertEqual(dom5.domain, 'u.example.com')
        self.assertEqual(dom5.organization.name, 'Example')

    def test_domain(self):
        """Check if it returns the info about an existing domain"""

        # Add some domains
        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com', is_top_domain=True)
        api.add_domain(self.db, 'Example', 'u.example.com', is_top_domain=True)
        api.add_domain(self.db, 'Example', 'es.u.example.com')
        api.add_domain(self.db, 'Example', 'en.u.example.com')

        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')
        api.add_domain(self.db, 'Bitergia', 'bitergia.org')

        api.add_organization(self.db, 'LibreSoft')

        # Find the given domain
        doms = api.domains(self.db, 'example.com')
        self.assertEqual(len(doms), 1)

        dom0 = doms[0]
        self.assertEqual(dom0.domain, 'example.com')
        self.assertEqual(dom0.organization.name, 'Example')

        # Find the given domain
        doms = api.domains(self.db, 'es.u.example.com')
        self.assertEqual(len(doms), 1)

        dom0 = doms[0]
        self.assertEqual(dom0.domain, 'es.u.example.com')
        self.assertEqual(dom0.organization.name, 'Example')

    def test_top_domains(self):
        """Check top domains option"""

        # Add some domains
        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com', is_top_domain=True)
        api.add_domain(self.db, 'Example', 'u.example.com', is_top_domain=True)
        api.add_domain(self.db, 'Example', 'es.u.example.com')
        api.add_domain(self.db, 'Example', 'en.u.example.com')

        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')
        api.add_domain(self.db, 'Bitergia', 'bitergia.org')

        api.add_organization(self.db, 'LibreSoft')

        # Look only for top domains
        doms = api.domains(self.db, top=True)
        self.assertEqual(len(doms), 2)

        dom0 = doms[0]
        self.assertIsInstance(dom0, Domain)
        self.assertEqual(dom0.domain, 'example.com')
        self.assertEqual(dom0.organization.name, 'Example')

        dom1 = doms[1]
        self.assertIsInstance(dom1, Domain)
        self.assertEqual(dom1.domain, 'u.example.com')
        self.assertEqual(dom1.organization.name, 'Example')

        # Look top domains of the given domain
        doms = api.domains(self.db, 'us.u.example.com', top=True)
        self.assertEqual(len(doms), 2)

        dom0 = doms[0]
        self.assertEqual(dom0.domain, 'example.com')
        self.assertEqual(dom0.organization.name, 'Example')

        dom1 = doms[1]
        self.assertEqual(dom1.domain, 'u.example.com')
        self.assertEqual(dom1.organization.name, 'Example')

        # Look for a top domain
        doms = api.domains(self.db, 'u.example.com', top=True)
        self.assertEqual(len(doms), 1)

        dom0 = doms[0]
        self.assertEqual(dom0.domain, 'u.example.com')
        self.assertEqual(dom0.organization.name, 'Example')

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        doms = api.domains(self.db)
        self.assertListEqual(doms, [])

    def test_not_found_domain(self):
        """Check whether it raises an error when the domain is not available"""

        # It should raise an error when the registry is empty
        self.assertRaises(NotFoundError, api.domains, self.db, 'Example')
        self.assertRaises(NotFoundError, api.domains, self.db, 'Example', True)

        # Add some domains
        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com', is_top_domain=True)
        api.add_domain(self.db, 'Example', 'es.example.com')
        api.add_domain(self.db, 'Example', 'en.example.com')

        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')

        # It should fail when there are some domains available
        self.assertRaises(NotFoundError, api.domains, self.db, 'libresoft.es')
        self.assertRaises(NotFoundError, api.domains, self.db, 'us.example.com')

        # Or even when looks for top domains
        self.assertRaises(NotFoundError, api.domains, self.db, 'libresoft.es', True)
        self.assertRaises(NotFoundError, api.domains, self.db, 'myexample.com', True)
        self.assertRaises(NotFoundError, api.domains, self.db, '.myexample.com', True)


class TestCountries(TestAPICaseBase):
    """Unit tests for countries"""

    def test_get_countries(self):
        """Check if it returns the list of countries"""

        with self.db.connect() as session:
            us = Country(code='US', name='United States of America', alpha3='USA')
            es = Country(code='ES', name='Spain', alpha3='ESP')
            gb = Country(code='GB', name='United Kingdom', alpha3='GBR')

            session.add(es)
            session.add(us)
            session.add(gb)

        cs = api.countries(self.db)
        self.assertEqual(len(cs), 3)

        c0 = cs[0]
        self.assertIsInstance(c0, Country)
        self.assertEqual(c0.code, 'ES')
        self.assertEqual(c0.name, 'Spain')
        self.assertEqual(c0.alpha3, 'ESP')

        c1 = cs[1]
        self.assertIsInstance(c1, Country)
        self.assertEqual(c1.code, 'GB')
        self.assertEqual(c1.name, 'United Kingdom')
        self.assertEqual(c1.alpha3, 'GBR')

        c2 = cs[2]
        self.assertIsInstance(c2, Country)
        self.assertEqual(c2.code, 'US')
        self.assertEqual(c2.name, 'United States of America')
        self.assertEqual(c2.alpha3, 'USA')

    def test_get_countries_using_search_params(self):
        """Check if it returns the info about countries using search parameters"""

        with self.db.connect() as session:
            us = Country(code='US', name='United States of America', alpha3='USA')
            es = Country(code='ES', name='Spain', alpha3='ESP')
            gb = Country(code='GB', name='United Kingdom', alpha3='GBR')

            session.add(es)
            session.add(us)
            session.add(gb)

        # Check code param
        cs = api.countries(self.db, code='ES')
        self.assertEqual(len(cs), 1)

        c0 = cs[0]
        self.assertIsInstance(c0, Country)
        self.assertEqual(c0.code, 'ES')
        self.assertEqual(c0.name, 'Spain')
        self.assertEqual(c0.alpha3, 'ESP')

        # Check term param
        cs = api.countries(self.db, term='ited')
        self.assertEqual(len(cs), 2)

        c0 = cs[0]
        self.assertIsInstance(c0, Country)
        self.assertEqual(c0.code, 'GB')
        self.assertEqual(c0.name, 'United Kingdom')
        self.assertEqual(c0.alpha3, 'GBR')

        c1 = cs[1]
        self.assertIsInstance(c1, Country)
        self.assertEqual(c1.code, 'US')
        self.assertEqual(c1.name, 'United States of America')
        self.assertEqual(c1.alpha3, 'USA')

        # Check if term is ignored when code is given
        cs = api.countries(self.db, code='ES', term='ited')
        self.assertEqual(len(cs), 1)

        c0 = cs[0]
        self.assertIsInstance(c0, Country)
        self.assertEqual(c0.code, 'ES')
        self.assertEqual(c0.name, 'Spain')
        self.assertEqual(c0.alpha3, 'ESP')

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        cs = api.countries(self.db)
        self.assertListEqual(cs, [])

    def test_not_found(self):
        """Check whether it raises an error when the country is not available"""

        # It should raise an error when the registry is empty
        self.assertRaises(NotFoundError, api.countries, self.db, 'ES')

        # It should do the same when there are some orgs available
        with self.db.connect() as session:
            us = Country(code='US', name='United States of America', alpha3='USA')
            es = Country(code='ES', name='Spain', alpha3='ESP')
            gb = Country(code='GB', name='United Kingdom', alpha3='GBR')

            session.add(es)
            session.add(us)
            session.add(gb)

        self.assertRaises(NotFoundError, api.countries, self.db, 'GR')
        self.assertRaises(NotFoundError, api.countries, self.db, None, 'Greece')
        self.assertRaises(NotFoundError, api.countries, self.db, 'GR', 'Greece')

    def test_invalid_country_code(self):
        """Check whether it raises an error when the country code is not valid"""

        exc = COUNTRY_CODE_INVALID_ERROR % {'code': ''}
        self.assertRaisesRegex(ValueError, exc,
                               api.countries, self.db, '')

        exc = COUNTRY_CODE_INVALID_ERROR % {'code': 'AAA'}
        self.assertRaisesRegex(ValueError, exc,
                               api.countries, self.db, 'AAA')

        exc = COUNTRY_CODE_INVALID_ERROR % {'code': '2A'}
        self.assertRaisesRegex(ValueError, exc,
                               api.countries, self.db, '2A')

        exc = COUNTRY_CODE_INVALID_ERROR % {'code': '8'}
        self.assertRaisesRegex(ValueError, exc,
                               api.countries, self.db, 8)


class TestEnrollments(TestAPICaseBase):
    """Unit tests for enrollments"""

    def test_get_enrollments(self):
        """Check if it returns the registry of enrollments"""

        # First, add a set of uuids, organizations and enrollments
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')
        api.add_unique_identity(self.db, 'Jane Rae')

        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_enrollment(self.db, 'John Doe', 'Example')

        api.add_organization(self.db, 'Bitergia')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2000, 1, 1))
        api.add_enrollment(self.db, 'Jane Rae', 'Bitergia',
                           datetime.datetime(1998, 1, 1),
                           datetime.datetime(2005, 1, 1))

        api.add_organization(self.db, 'LibreSoft')
        api.add_enrollment(self.db, 'John Doe', 'LibreSoft')
        api.add_enrollment(self.db, 'Jane Rae', 'LibreSoft')

        # Tests
        enrollments = api.enrollments(self.db)
        self.assertEqual(len(enrollments), 7)

        rol = enrollments[0]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.uidentity.uuid, 'Jane Rae')
        self.assertEqual(rol.organization.name, 'Bitergia')

        rol = enrollments[1]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.uidentity.uuid, 'Jane Rae')
        self.assertEqual(rol.organization.name, 'LibreSoft')

        rol = enrollments[2]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.uidentity.uuid, 'John Doe')
        self.assertEqual(rol.organization.name, 'Example')

        rol = enrollments[3]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.uidentity.uuid, 'John Doe')
        self.assertEqual(rol.organization.name, 'LibreSoft')

        rol = enrollments[4]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Bitergia')

        rol = enrollments[5]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Bitergia')
        self.assertEqual(rol.start, datetime.datetime(1999, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2000, 1, 1))

        rol = enrollments[6]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')

        # Test dates
        enrollments = api.enrollments(self.db,
                                      from_date=datetime.datetime(1998, 5, 1),
                                      to_date=datetime.datetime(2006, 1, 1))
        self.assertEqual(len(enrollments), 1)

        rol = enrollments[0]
        self.assertIsInstance(rol, Enrollment)
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Bitergia')
        self.assertEqual(rol.start, datetime.datetime(1999, 1, 1))
        self.assertEqual(rol.end, datetime.datetime(2000, 1, 1))

    def test_enrollments_uuid(self):
        """Check if it returns the registry of enrollments for a uuid"""

        # First, add a set of uuids, organizations and enrollments
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')

        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_enrollment(self.db, 'John Doe', 'Example',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2000, 1, 1))

        api.add_organization(self.db, 'Bitergia')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia')

        api.add_organization(self.db, 'LibreSoft')
        api.add_enrollment(self.db, 'John Doe', 'LibreSoft')

        # Tests
        enrollments = api.enrollments(self.db, uuid='John Smith')
        self.assertEqual(len(enrollments), 2)

        rol = enrollments[0]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Bitergia')

        rol = enrollments[1]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')

        # Test using uuid and organization
        enrollments = api.enrollments(self.db,
                                      uuid='John Doe', organization='LibreSoft')
        self.assertEqual(len(enrollments), 1)

        # Test using period ranges
        enrollments = api.enrollments(self.db, uuid='John Doe',
                                      from_date=datetime.datetime(1998, 1, 1),
                                      to_date=datetime.datetime(2005, 1, 1))
        self.assertEqual(len(enrollments), 1)

    def test_enrollments_organization(self):
        """Check if it returns the registry of enrollments for an organization"""

        # First, add a set of uuids, organizations and enrollments
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')

        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example')
        api.add_enrollment(self.db, 'John Doe', 'Example',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2000, 1, 1))

        api.add_organization(self.db, 'Bitergia')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia')

        api.add_organization(self.db, 'LibreSoft')
        api.add_enrollment(self.db, 'John Doe', 'LibreSoft')

        # Tests
        enrollments = api.enrollments(self.db, organization='Example')
        self.assertEqual(len(enrollments), 2)

        rol = enrollments[0]
        self.assertEqual(rol.uidentity.uuid, 'John Doe')
        self.assertEqual(rol.organization.name, 'Example')

        rol = enrollments[1]
        self.assertEqual(rol.uidentity.uuid, 'John Smith')
        self.assertEqual(rol.organization.name, 'Example')

        enrollments = api.enrollments(self.db, organization='Example')
        self.assertEqual(len(enrollments), 2)

        # Test using period ranges
        enrollments = api.enrollments(self.db, organization='Example',
                                      from_date=datetime.datetime(1998, 1, 1),
                                      to_date=datetime.datetime(2005, 1, 1))
        self.assertEqual(len(enrollments), 1)

    def test_empty_results(self):
        """Check cases when the result is empty"""

        # First, add a set of uuids, organizations and enrollments
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')
        api.add_unique_identity(self.db, 'Jane Rae')

        api.add_organization(self.db, 'Example')
        api.add_enrollment(self.db, 'John Smith', 'Example',
                           datetime.datetime(1999, 1, 1),
                           datetime.datetime(2005, 1, 1))
        api.add_enrollment(self.db, 'John Doe', 'Example')

        api.add_organization(self.db, 'Bitergia')
        api.add_enrollment(self.db, 'John Smith', 'Bitergia')

        api.add_organization(self.db, 'LibreSoft')
        api.add_enrollment(self.db, 'John Doe', 'LibreSoft')

        api.add_organization(self.db, 'GSyC')

        # Test when there are not enrollments for a uuid
        enrollments = api.enrollments(self.db,
                                      uuid='Jane Rae')
        self.assertEqual(len(enrollments), 0)

        # Test when there are not enrollments for an organization
        enrollments = api.enrollments(self.db,
                                      organization='GSyC')
        self.assertEqual(len(enrollments), 0)

        # Test when an enrollment does not exist
        enrollments = api.enrollments(self.db,
                                      uuid='John Doe', organization='Bitergia')
        self.assertEqual(len(enrollments), 0)

        # Test enrollments between two dates
        enrollments = api.enrollments(self.db,
                                      uuid='John Smith', organization='Example',
                                      from_date=datetime.datetime(1999, 1, 1),
                                      to_date=datetime.datetime(2000, 1, 1))
        self.assertEqual(len(enrollments), 0)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        enrollments = api.enrollments(self.db)
        self.assertListEqual(enrollments, [])

    def test_period_ranges(self):
        """Check whether enrollments cannot be listed giving invalid period ranges"""

        self.assertRaisesRegex(ValueError, ENROLLMENT_PERIOD_INVALID_ERROR,
                               api.enrollments, self.db, 'John Smith', 'Example',
                               datetime.datetime(2001, 1, 1),
                               datetime.datetime(1999, 1, 1))

        exc = ENROLLMENT_PERIOD_OUT_OF_BOUNDS_ERROR % {'type': 'from_date',
                                                       'date': '1899-12-31 23:59:59'}
        self.assertRaisesRegex(ValueError, exc,
                               api.enrollments, self.db, 'John Smith', 'Example',
                               datetime.datetime(1899, 12, 31, 23, 59, 59))

        exc = ENROLLMENT_PERIOD_OUT_OF_BOUNDS_ERROR % {'type': 'from_date',
                                                       'date': '2100-01-01 00:00:01'}
        self.assertRaisesRegex(ValueError, exc,
                               api.enrollments, self.db, 'John Smith', 'Example',
                               datetime.datetime(2100, 1, 1, 0, 0, 1))

        exc = ENROLLMENT_PERIOD_OUT_OF_BOUNDS_ERROR % {'type': 'to_date',
                                                       'date': '2100-01-01 00:00:01'}
        self.assertRaisesRegex(ValueError, exc,
                               api.enrollments, self.db, 'John Smith', 'Example',
                               datetime.datetime(1900, 1, 1),
                               datetime.datetime(2100, 1, 1, 0, 0, 1))

        exc = ENROLLMENT_PERIOD_OUT_OF_BOUNDS_ERROR % {'type': 'to_date',
                                                       'date': '1899-12-31 23:59:59'}
        self.assertRaisesRegex(ValueError, exc,
                               api.enrollments, self.db, 'John Smith', 'Example',
                               datetime.datetime(1900, 1, 1),
                               datetime.datetime(1899, 12, 31, 23, 59, 59))

    def test_not_found_uuid(self):
        """Check whether it raises an error when the uiid is not available"""

        # It should raise an error when the registry is empty
        self.assertRaisesRegex(NotFoundError,
                               NOT_FOUND_ERROR % {'entity': 'John Smith'},
                               api.enrollments, self.db,
                               'John Smith', 'Example')

        # It should do the same when there are some identities available
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')

        self.assertRaisesRegex(NotFoundError,
                               NOT_FOUND_ERROR % {'entity': 'Jane Rae'},
                               api.enrollments, self.db,
                               'Jane Rae', 'LibreSoft')

    def test_not_found_organization(self):
        """Check whether it raises an error when the organization is not available"""

        api.add_unique_identity(self.db, 'John Smith')

        # It should raise an error when the registry is empty
        self.assertRaisesRegex(NotFoundError,
                               NOT_FOUND_ERROR % {'entity': 'Example'},
                               api.enrollments, self.db,
                               'John Smith', 'Example')

        # It should do the same when there are some orgs available
        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')

        self.assertRaisesRegex(NotFoundError,
                               NOT_FOUND_ERROR % {'entity': 'LibreSoft'},
                               api.enrollments, self.db,
                               'John Smith', 'LibreSoft')


class TestBlacklist(TestAPICaseBase):
    """Unit tests for blacklist"""

    def test_get_blacklist(self):
        """Check if it returns the blacklist"""

        api.add_to_matching_blacklist(self.db, 'root@example.com')
        api.add_to_matching_blacklist(self.db, 'John Smith')
        api.add_to_matching_blacklist(self.db, 'Bitergia')
        api.add_to_matching_blacklist(self.db, 'John Doe')

        mbs = api.blacklist(self.db)
        self.assertEqual(len(mbs), 4)

        with self.db.connect() as session:
            mb = session.query(MatchingBlacklist).\
                filter(MatchingBlacklist.excluded == 'root@example.com').first()
            self.assertEqual(mb.excluded, 'root@example.com')

            mb = session.query(MatchingBlacklist).\
                filter(MatchingBlacklist.excluded == 'Bitergia').first()
            self.assertEqual(mb.excluded, 'Bitergia')

            mb = session.query(MatchingBlacklist).\
                filter(MatchingBlacklist.excluded == 'John Doe').first()
            self.assertEqual(mb.excluded, 'John Doe')

        mb = mbs[0]
        self.assertIsInstance(mb, MatchingBlacklist)
        self.assertEqual(mb.excluded, 'Bitergia')

        mb = mbs[1]
        self.assertIsInstance(mb, MatchingBlacklist)
        self.assertEqual(mb.excluded, 'John Doe')

        mb = mbs[2]
        self.assertIsInstance(mb, MatchingBlacklist)
        self.assertEqual(mb.excluded, 'John Smith')

        mb = mbs[3]
        self.assertIsInstance(mb, MatchingBlacklist)
        self.assertEqual(mb.excluded, 'root@example.com')

    def test_get_blacklist_term(self):
        """Check if it returns the info about blacklisted entities using a search term"""

        api.add_to_matching_blacklist(self.db, 'root@example.com')
        api.add_to_matching_blacklist(self.db, 'John Smith')
        api.add_to_matching_blacklist(self.db, 'Bitergia')
        api.add_to_matching_blacklist(self.db, 'John Doe')

        # This query have to return two entries
        mbs = api.blacklist(self.db, 'ohn')
        self.assertEqual(len(mbs), 2)

        # John Doe
        mb = mbs[0]
        self.assertIsInstance(mb, MatchingBlacklist)
        self.assertEqual(mb.excluded, 'John Doe')

        mb = mbs[1]
        self.assertIsInstance(mb, MatchingBlacklist)
        self.assertEqual(mb.excluded, 'John Smith')

    def test_empty_blacklist(self):
        """Check whether it returns an empty list when the blacklist is empty"""

        mbs = api.blacklist(self.db)
        self.assertListEqual(mbs, [])

    def test_not_found_term(self):
        """Check whether it raises an error when the term is not found"""

        # It should raise an error when the blacklist is empty
        self.assertRaises(NotFoundError, api.blacklist, self.db, 'jane')

        # It should do the same when there are some orgs available
        api.add_to_matching_blacklist(self.db, 'root@example.com')
        api.add_to_matching_blacklist(self.db, 'John Smith')

        self.assertRaises(NotFoundError, api.blacklist, self.db, 'jane')


if __name__ == "__main__":
    unittest.main()
