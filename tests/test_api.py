#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Bitergia
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

import datetime
import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.db.database import Database
from sortinghat.db.model import UniqueIdentity, Identity, Organization, Domain, Enrollment
from sortinghat.exceptions import AlreadyExistsError, NotFoundError

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


UUID_NONE_OR_EMPTY_ERROR = "uuid cannot be"
ORG_NONE_OR_EMPTY_ERROR = "organization cannot be"
DOMAIN_NONE_OR_EMPTY_ERROR = "domain cannot be"
SOURCE_NONE_OR_EMPTY_ERROR = "source cannot be"
IDENTITY_NONE_OR_EMPTY_ERROR = "identity data cannot be None or empty"
ENROLLMENT_PERIOD_INVALID_ERROR = "cannot be greater than "
NOT_FOUND_ERROR =  "%(entity)s not found in the registry"


class TestBaseCase(unittest.TestCase):
    """Defines common setup and teardown methods on api unit tests"""

    @classmethod
    def setUpClass(cls):
        cls.db = Database(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

    def setUp(self):
        self.db.clear()

    def tearDown(self):
        self.db.clear()


class TestAddUniqueIdentity(TestBaseCase):
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
        self.assertRaises(AlreadyExistsError, api.add_unique_identity,
                          self.db, 'John Smith')

    def test_none_uuid(self):
        """Check whether None identities cannot be added to the registry"""

        self.assertRaisesRegexp(ValueError, UUID_NONE_OR_EMPTY_ERROR,
                                api.add_unique_identity, self.db, None)

    def test_empty_uuid(self):
        """Check whether empty uuids cannot be added to the registry"""

        self.assertRaisesRegexp(ValueError, UUID_NONE_OR_EMPTY_ERROR,
                                api.add_unique_identity, self.db, '')


class TestAddIdentity(TestBaseCase):
    """Unit tests for add_identity"""

    def test_add_new_identity(self):
        """Check if everything goes OK when adding a new identity"""

        unique_id = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                     'John Smith', 'jsmith')

        with self.db.connect() as session:
            uid = session.query(UniqueIdentity).\
                    filter(UniqueIdentity.uuid == '03e12d00e37fd45593c49a5a5a1652deca4cf302').first()
            self.assertEqual(uid.uuid, unique_id)

            identities = session.query(Identity).\
                            filter(Identity.uuid == uid.uuid).all()
            self.assertEqual(len(identities), 1)

            id1 = identities[0]
            self.assertEqual(id1.id, unique_id)
            self.assertEqual(id1.id, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
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
            self.assertEqual(id1.id, jsmith_uuid)
            self.assertEqual(id1.name, 'John Smith')
            self.assertEqual(id1.email, 'jsmith@example.com')
            self.assertEqual(id1.username, 'jsmith')
            self.assertEqual(id1.source, 'scm')
            self.assertEqual(id1.uuid, jsmith_uuid)

            id2 = uid.identities[1]
            self.assertEqual(id2.id, unique_id1)
            self.assertEqual(id2.name, 'John Smith')
            self.assertEqual(id2.email, 'jsmith@example.com')
            self.assertEqual(id2.username, 'jsmith')
            self.assertEqual(id2.source, 'mls')

            id3 = uid.identities[2]
            self.assertEqual(id3.id, unique_id2)
            self.assertEqual(id3.name, 'John Smith')
            self.assertEqual(id3.email, None)
            self.assertEqual(id3.username, 'jsmith')
            self.assertEqual(id3.source, 'mls')

            # Next, John Doe
            uid = session.query(UniqueIdentity).\
                    filter(UniqueIdentity.uuid == jdoe_uuid).first()

            self.assertEqual(len(uid.identities), 2)

            id1 = uid.identities[0]
            self.assertEqual(id1.id, jdoe_uuid)
            self.assertEqual(id1.name, 'John Doe')
            self.assertEqual(id1.email, 'jdoe@example.com')
            self.assertEqual(id1.username, 'jdoe')
            self.assertEqual(id1.source, 'scm')

            id2 = uid.identities[1]
            self.assertEqual(id2.id, unique_id3)
            self.assertEqual(id2.name, None)
            self.assertEqual(id2.email, 'jdoe@example.com')
            self.assertEqual(id2.username, None)
            self.assertEqual(id2.source, 'mls')

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

        self.assertEqual(uuid1, '75d95d6c8492fd36d24a18bd45d62161e05fbc97')
        self.assertEqual(uuid2, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(uuid3, '764deab5c5f065025cd5518581f45ffd18d1f3bd')
        self.assertEqual(uuid4, 'a2e6bd8f997635d02837c86a6fea98fa835baf2a')
        self.assertEqual(uuid5, 'd32f8895d998f2e8f83375d544e40a30737f09e5')

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
        self.assertRaises(AlreadyExistsError, api.add_identity,
                          self.db, 'scm', 'jsmith@example.com')

    def test_none_source(self):
        """Check whether new identities cannot be added when giving a None source"""

        self.assertRaisesRegexp(ValueError, SOURCE_NONE_OR_EMPTY_ERROR,
                                api.add_identity, self.db, None)

    def test_empty_source(self):
        """Check whether new identities cannot be added when giving an empty source"""

        self.assertRaisesRegexp(ValueError, SOURCE_NONE_OR_EMPTY_ERROR,
                                api.add_identity, self.db, '')

    def test_none_or_empty_data(self):
        """Check whether new identities cannot be added when identity data is None or empty"""

        self.assertRaisesRegexp(ValueError, IDENTITY_NONE_OR_EMPTY_ERROR,
                                api.add_identity, self.db, 'scm', None, '', None)
        self.assertRaisesRegexp(ValueError, IDENTITY_NONE_OR_EMPTY_ERROR,
                                api.add_identity, self.db, 'scm', '', '', '')


class TestAddOrganization(TestBaseCase):
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

        self.assertRaisesRegexp(ValueError, ORG_NONE_OR_EMPTY_ERROR,
                                api.add_organization, self.db, None)

    def test_empty_organization(self):
        """Check whether empty organizations cannot be added to the registry"""

        self.assertRaisesRegexp(ValueError, ORG_NONE_OR_EMPTY_ERROR,
                                api.add_organization, self.db, '')


class TestAddDomain(TestBaseCase):
    """Unit tests for add_domain"""

    def test_add_domains(self):
        """Check whether it adds a set of domains to one organization"""

        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com')
        api.add_domain(self.db, 'Example', 'example.org')
        api.add_domain(self.db, 'Example', 'example.net')

        with self.db.connect() as session:
            domains = session.query(Domain).join(Organization).\
                filter(Organization.name == 'Example').all()
            self.assertEqual(len(domains), 3)
            self.assertEqual(domains[0].domain, 'example.com')
            self.assertEqual(domains[1].domain, 'example.org')
            self.assertEqual(domains[2].domain, 'example.net')

    def test_add_domains_to_organization(self):
        """Check whether it adds several domains to set of organizations"""

        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')
        api.add_organization(self.db, 'LibreSoft')

        api.add_domain(self.db, 'Example', 'example.com')
        api.add_domain(self.db, 'LibreSoft', 'libresoft.es')
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
            self.assertEqual(domains[1].domain, 'libresoft.org')

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

    def test_overwrite_domain(self):
        """Check whether it overwrites the old organization-domain relationship"""

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
            self.assertEqual(domains[1].domain, 'example.org')

            domains = session.query(Domain).join(Organization).\
                filter(Organization.name == 'Bitergia').all()
            self.assertEqual(len(domains), 0)

        # Overwrite the relationship assigning the domain to a different
        # company
        api.add_domain(self.db, 'Bitergia', 'example.com', overwrite=True)

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

    def test_none_domain(self):
        """Check whether None domains cannot be added to the registry"""

        self.assertRaisesRegexp(ValueError, DOMAIN_NONE_OR_EMPTY_ERROR,
                                api.add_domain, self.db, 'Example', None)

    def test_empty_domain(self):
        """Check whether empty domains cannot be added to the registry"""

        self.assertRaisesRegexp(ValueError, DOMAIN_NONE_OR_EMPTY_ERROR,
                                api.add_domain, self.db, 'Example', '')


class TestAddEnrollment(TestBaseCase):
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
                       Organization.name == 'Example').all()
            self.assertEqual(len(enrollments), 3)

            enrollment = enrollments[0]
            self.assertEqual(enrollment.init, datetime.datetime(1999, 1, 1))
            self.assertEqual(enrollment.end, datetime.datetime(2000, 1, 1))

            enrollment = enrollments[1]
            self.assertEqual(enrollment.init, datetime.datetime(2005, 1, 1))
            self.assertEqual(enrollment.end, datetime.datetime(2006, 1, 1))

            enrollment = enrollments[2]
            self.assertEqual(enrollment.init, datetime.datetime(2013, 1, 1))
            self.assertEqual(enrollment.end, datetime.datetime(2014, 1, 1))

    def test_period_ranges(self):
        """Check whether enrollments cannot be added giving invalid period ranges"""

        self.assertRaisesRegexp(ValueError, ENROLLMENT_PERIOD_INVALID_ERROR,
                                api.add_enrollment, self.db, 'John Smith', 'Example',
                                datetime.datetime(2001, 1, 1),
                                datetime.datetime(1999, 1, 1))

    def test_non_existing_uuid(self):
        """Check if it fails adding enrollments to not existing unique identities"""

        self.assertRaisesRegexp(NotFoundError,
                                NOT_FOUND_ERROR % {'entity' : 'John Smith'},
                                api.add_enrollment,
                                self.db, 'John Smith', 'Example')

    def test_non_existing_organization(self):
        """Check if it fails adding enrollments to not existing organizations"""

        # We need first to add a unique identity
        api.add_unique_identity(self.db, 'John Smith')

        self.assertRaisesRegexp(NotFoundError,
                                NOT_FOUND_ERROR % {'entity' : 'Example'},
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

class TestDeleteUniqueIdentity(TestBaseCase):
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

            # Check if there only remains one unique identity and one
            # enrollment
            identities = session.query(UniqueIdentity).all()
            self.assertEqual(len(identities), 1)
            self.assertEqual(identities[0].uuid, 'John Doe')

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


class TestDeteleIdentity(TestBaseCase):
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

            # Check if there only remains three unique identity and
            # two identities (one from John Smith and another one
            # from John Doe)
            uidentities = session.query(UniqueIdentity).all()
            self.assertEqual(len(uidentities), 3)
            self.assertEqual(uidentities[0].uuid, jdoe_uuid)
            self.assertEqual(uidentities[1].uuid, jrae_uuid)
            self.assertEqual(uidentities[2].uuid, jsmith_uuid)

            identities = session.query(Identity).all()
            self.assertEqual(len(identities), 2)
            self.assertEqual(identities[0].id, jdoe_uuid)
            self.assertEqual(identities[1].id, jsmith_uuid)

            enrollments = session.query(Enrollment).all()
            self.assertEqual(len(enrollments), 4)

            orgs = session.query(Organization).all()
            self.assertEqual(len(orgs), 3)

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


class TestDeleteOrganization(TestBaseCase):
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


class TestDeleteDomain(TestBaseCase):
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


class TestDeleteEnrollment(TestBaseCase):
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
                    filter(Organization.name == 'Example').all()
            self.assertEqual(len(enrollments), 2)

            self.assertEqual(enrollments[0].init, datetime.datetime(1900, 1, 1))
            self.assertEqual(enrollments[0].end, datetime.datetime(2100, 1, 1))

            self.assertEqual(enrollments[1].init, datetime.datetime(1999, 1, 1))
            self.assertEqual(enrollments[1].end, datetime.datetime(2010, 1, 1))

    def test_period_ranges(self):
        """Check whether enrollments cannot be removed giving invalid period ranges"""

        self.assertRaisesRegexp(ValueError, ENROLLMENT_PERIOD_INVALID_ERROR,
                                api.delete_enrollment, self.db, 'John Smith', 'Example',
                                datetime.datetime(2001, 1, 1),
                                datetime.datetime(1999, 1, 1))

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


class TestMergeEnrollments(TestBaseCase):
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
            self.assertEqual(rol0.init, datetime.datetime(2008, 1, 1))
            self.assertEqual(rol0.end, datetime.datetime(2010, 1, 1))

            # Enrollments on Bitergia were not modified
            enrollments = session.query(Enrollment).\
                join(UniqueIdentity, Organization).\
                filter(UniqueIdentity.uuid == 'John Smith',
                       Organization.name == 'Bitergia').all()
            self.assertEqual(len(enrollments), 2)

            rol0 = enrollments[0]
            self.assertEqual(rol0.init, datetime.datetime(1900, 1, 1))
            self.assertEqual(rol0.end, datetime.datetime(2010, 1, 1))

            rol1 = enrollments[1]
            self.assertEqual(rol1.init, datetime.datetime(2008, 1, 1))
            self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1))

        # Test Jonh Doe enrollments
        api.merge_enrollments(self.db, 'John Doe', 'Example')

        with self.db.connect() as session:
            enrollments = session.query(Enrollment).\
                join(UniqueIdentity, Organization).\
                filter(UniqueIdentity.uuid == 'John Doe',
                       Organization.name == 'Example').all()
            self.assertEqual(len(enrollments), 2)

            rol0 = enrollments[0]
            self.assertEqual(rol0.init, datetime.datetime(2008, 1, 1))
            self.assertEqual(rol0.end, datetime.datetime(2010, 1, 1))

            rol1 = enrollments[1]
            self.assertEqual(rol1.init, datetime.datetime(2010, 1, 2))
            self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1))

        # Test Jane Rae enrollments
        api.merge_enrollments(self.db, 'Jane Rae', 'Bitergia')

        with self.db.connect() as session:
            enrollments = session.query(Enrollment).\
                join(UniqueIdentity, Organization).\
                filter(UniqueIdentity.uuid == 'Jane Rae',
                       Organization.name == 'Bitergia').all()
            self.assertEqual(len(enrollments), 2)

            rol0 = enrollments[0]
            self.assertEqual(rol0.init, datetime.datetime(1900, 1, 1))
            self.assertEqual(rol0.end, datetime.datetime(2010, 1, 1))

            rol1 = enrollments[1]
            self.assertEqual(rol1.init, datetime.datetime(2010, 1, 2))
            self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1))

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


class TestMergeUniqueIdentities(TestBaseCase):
    """Unit tests for merge_unique_identities"""

    def test_merge_identitites(self):
        """Test behavior merging unique identities"""

        # Add some unique identities, identities and
        # enrollments first
        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com', 'John Smith',
                         uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         uuid='John Doe')
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
            uidentities = session.query(UniqueIdentity).all()
            self.assertEqual(len(uidentities), 2)

            uid1 = uidentities[0]
            self.assertEqual(uid1.uuid, 'Jane Rae')
            self.assertEqual(len(uid1.identities), 0)
            self.assertEqual(len(uid1.enrollments), 1)

            uid2 = uidentities[1]
            self.assertEqual(uid2.uuid, 'John Doe')
            self.assertEqual(len(uid2.identities), 3)

            id1 = uid2.identities[0]
            self.assertEqual(id1.name, 'John Smith')
            self.assertEqual(id1.email, 'jsmith@example.com')
            self.assertEqual(id1.source, 'scm')

            id2 = uid2.identities[1]
            self.assertEqual(id2.name, None)
            self.assertEqual(id2.email, 'jsmith@example.com')
            self.assertEqual(id2.source, 'scm')

            id3 = uid2.identities[2]
            self.assertEqual(id3.name, None)
            self.assertEqual(id3.email, 'jdoe@example.com')
            self.assertEqual(id3.source, 'scm')

            # Duplicate enrollments should had been removed
            self.assertEqual(len(uid2.enrollments), 3)

            rol1 = uid2.enrollments[0]
            self.assertEqual(rol1.organization.name, 'Example')
            self.assertEqual(rol1.init, datetime.datetime(1900, 1, 1))
            self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1))

            rol2 = uid2.enrollments[1]
            self.assertEqual(rol2.organization.name, 'Bitergia')
            self.assertEqual(rol2.init, datetime.datetime(1900, 1, 1))
            self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1))

            rol3 = uid2.enrollments[2]
            self.assertEqual(rol3.organization.name, 'Bitergia')
            self.assertEqual(rol3.init, datetime.datetime(1999, 1, 1))
            self.assertEqual(rol3.end, datetime.datetime(2000, 1, 1))

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
            uidentities = session.query(UniqueIdentity).all()
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
        self.assertRaisesRegexp(NotFoundError,
                                NOT_FOUND_ERROR % {'entity' : 'Jane Roe'},
                                api.merge_unique_identities,
                                self.db, 'Jane Roe', 'John Smith')

        # Check 'to_uuid' parameter
        self.assertRaisesRegexp(NotFoundError,
                                NOT_FOUND_ERROR % {'entity' : 'Jane Roe'},
                                api.merge_unique_identities,
                                self.db, 'John Smith', 'Jane Roe')

        # Even if the identities are the same and do not exist, it still
        # raises the exception
        self.assertRaisesRegexp(NotFoundError,
                                NOT_FOUND_ERROR % {'entity' : 'Jane Roe'},
                                api.merge_unique_identities,
                                self.db, 'Jane Roe', 'Jane Roe')


class TestMoveIdentity(TestBaseCase):
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
            uidentities = session.query(UniqueIdentity).all()
            self.assertEqual(len(uidentities), 2)

            uid1 = uidentities[0]
            self.assertEqual(uid1.uuid, 'John Doe')
            self.assertEqual(len(uid1.identities), 0)

            uid2 = uidentities[1]
            self.assertEqual(uid2.uuid, 'John Smith')
            self.assertEqual(len(uid2.identities), 3)

            id1 = uid2.identities[0]
            self.assertEqual(id1.name, 'John Smith')
            self.assertEqual(id1.email, 'jsmith@example.com')
            self.assertEqual(id1.source, 'scm')

            id2 = uid2.identities[1]
            self.assertEqual(id2.name, None)
            self.assertEqual(id2.email, 'jsmith@example.com')
            self.assertEqual(id2.source, 'scm')

            id3 = uid2.identities[2]
            self.assertEqual(id3.id, from_id)
            self.assertEqual(id3.name, None)
            self.assertEqual(id3.email, 'jdoe@example.com')
            self.assertEqual(id3.source, 'scm')

    def test_equal_related_unique_identity(self):
        """Test that all remains the same when to_uuid is the unique identity related to 'from_id'"""

        # Add some unique identities and identities first
        api.add_unique_identity(self.db, 'John Smith')
        from_id = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                   uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         uuid='John Doe')

        # Move the identity to the same unique identity
        api.move_identity(self.db, from_id, 'John Smith')

        # Nothing has happened
        with self.db.connect() as session:
            uidentities = session.query(UniqueIdentity).all()
            self.assertEqual(len(uidentities), 2)

            uid2 = uidentities[1]
            self.assertEqual(uid2.uuid, 'John Smith')
            self.assertEqual(len(uid2.identities), 1)

            id1 = uid2.identities[0]
            self.assertEqual(id1.id, from_id)

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
        self.assertRaisesRegexp(NotFoundError,
                                NOT_FOUND_ERROR % {'entity' : 'FFFFFFFFFFF'},
                                api.move_identity,
                                self.db, 'FFFFFFFFFFF', 'John Smith')

        # Check 'to_uuid' parameter
        self.assertRaisesRegexp(NotFoundError,
                                NOT_FOUND_ERROR % {'entity' : 'Jane Roe'},
                                api.move_identity,
                                self.db, from_id, 'Jane Roe')


class TestUniqueIdentities(TestBaseCase):
    """Unit tests for unique_identities"""

    def test_unique_identities(self):
        """Check if it returns the registry of unique identities"""

        # Add some identities
        jsmith_uuid = api.add_identity(self.db, 'scm', 'jsmith@example.com',
                                       'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jsmith@bitergia.com', uuid=jsmith_uuid)
        api.add_identity(self.db, 'mls', 'jsmith@bitergia.com', uuid=jsmith_uuid)

        jdoe_uuid = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                     'John Doe', 'jdoe')
        api.add_identity(self.db, 'scm', 'jdoe@libresoft.es', uuid=jdoe_uuid)

        # Tests
        uidentities = api.unique_identities(self.db)
        self.assertEqual(len(uidentities), 2)

        # Test John Smith unique identity
        uid = uidentities[0]
        self.assertEqual(uid.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(len(uid.identities), 3)

        id1 = uid.identities[0]
        self.assertEqual(id1.email, 'jsmith@example.com')

        id2 = uid.identities[1]
        self.assertEqual(id2.email, 'jsmith@bitergia.com')
        self.assertEqual(id2.source, 'scm')

        id3 = uid.identities[2]
        self.assertEqual(id3.email, 'jsmith@bitergia.com')
        self.assertEqual(id3.source, 'mls')

        # Test John Doe unique identity
        uid = uidentities[1]
        self.assertEqual(uid.uuid, '8e9eac4c6449d2661d66dc62c1752529f935f0b1')
        self.assertEqual(len(uid.identities), 2)

        id1 = uid.identities[0]
        self.assertEqual(id1.email, 'jdoe@libresoft.es')

        id2 = uid.identities[1]
        self.assertEqual(id2.email, 'jdoe@example.com')

    def test_unique_identity_uuid(self):
        """Check if it returns the given unique identitie"""

        # Add some identities
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         'John Smith', 'jsmith')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         'John Doe', 'jdoe')

        # Tests
        uidentities = api.unique_identities(self.db, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(len(uidentities), 1)

        uid = uidentities[0]
        self.assertEqual(uid.uuid, '03e12d00e37fd45593c49a5a5a1652deca4cf302')
        self.assertEqual(len(uid.identities), 1)

        id1 = uid.identities[0]
        self.assertEqual(id1.email, 'jsmith@example.com')

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

        self.assertRaises(NotFoundError, api.registry, self.db, 'Jane Rae')


class TestRegistry(TestBaseCase):
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

    def test_get_registry_organization(self):
        """Check if it returns the info about an existing organization"""

        api.add_organization(self.db, 'Example')
        api.add_domain(self.db, 'Example', 'example.com')
        api.add_domain(self.db, 'Example', 'example.org')
        api.add_organization(self.db, 'Bitergia')
        api.add_domain(self.db, 'Bitergia', 'bitergia.com')

        orgs = api.registry(self.db, 'Example')
        self.assertEqual(len(orgs), 1)

        org1 = orgs[0]
        self.assertIsInstance(org1, Organization)
        self.assertEqual(org1.name, 'Example')
        self.assertEqual(len(org1.domains), 2)

        dom1 = org1.domains[0]
        self.assertIsInstance(dom1, Domain)
        self.assertEqual(dom1.domain, 'example.com')

        dom2 = org1.domains[1]
        self.assertIsInstance(dom2, Domain)
        self.assertEqual(dom2.domain, 'example.org')

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        orgs = api.registry(self.db)
        self.assertListEqual(orgs, [])

    def test_not_found_organization(self):
        """Check whether it raises an error when the organization is not available"""

        # It should raise an error when the registry is empty
        self.assertRaises(NotFoundError, api.registry, self.db, 'Example')

        # It should do the same when there are some orgs available
        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')

        self.assertRaises(NotFoundError, api.registry, self.db, 'LibreSoft')


class TestEnrollments(TestBaseCase):
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
        self.assertEqual(rol.init, datetime.datetime(1999, 1, 1))
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
        self.assertEqual(rol.init, datetime.datetime(1999, 1, 1))
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
        "Check cases when the result is empty"

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

        self.assertRaisesRegexp(ValueError, ENROLLMENT_PERIOD_INVALID_ERROR,
                                api.enrollments, self.db, 'John Smith', 'Example',
                                datetime.datetime(2001, 1, 1),
                                datetime.datetime(1999, 1, 1))

    def test_not_found_uuid(self):
        """Check whether it raises an error when the uiid is not available"""

        # It should raise an error when the registry is empty
        self.assertRaisesRegexp(NotFoundError,
                                NOT_FOUND_ERROR % {'entity' : 'John Smith'},
                                api.enrollments, self.db,
                                'John Smith', 'Example')

        # It should do the same when there are some identities available
        api.add_unique_identity(self.db, 'John Smith')
        api.add_unique_identity(self.db, 'John Doe')

        self.assertRaisesRegexp(NotFoundError,
                                NOT_FOUND_ERROR % {'entity' : 'Jane Rae'},
                                api.enrollments, self.db,
                                'Jane Rae', 'LibreSoft')

    def test_not_found_organization(self):
        """Check whether it raises an error when the organization is not available"""

        api.add_unique_identity(self.db, 'John Smith')

        # It should raise an error when the registry is empty
        self.assertRaisesRegexp(NotFoundError,
                                NOT_FOUND_ERROR % {'entity' : 'Example'},
                                api.enrollments, self.db,
                                'John Smith', 'Example')

        # It should do the same when there are some orgs available
        api.add_organization(self.db, 'Example')
        api.add_organization(self.db, 'Bitergia')

        self.assertRaisesRegexp(NotFoundError,
                                NOT_FOUND_ERROR % {'entity' : 'LibreSoft'},
                                api.enrollments, self.db,
                                'John Smith', 'LibreSoft')


if __name__ == "__main__":
    unittest.main()
