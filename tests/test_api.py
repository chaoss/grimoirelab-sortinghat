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
from sortinghat.db.model import UniqueIdentity, Organization, Domain, Enrollment
from sortinghat.exceptions import AlreadyExistsError, NotFoundError

from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


UUID_NONE_OR_EMPTY_ERROR = "uuid cannot be"
ORG_NONE_OR_EMPTY_ERROR = "organization cannot be"
DOMAIN_NONE_OR_EMPTY_ERROR = "domain cannot be"
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
                    filter(UniqueIdentity.identifier == 'John Smith').first()
            self.assertEqual(uid.identifier, 'John Smith')

            uid = session.query(UniqueIdentity).\
                    filter(UniqueIdentity.identifier == 'John Doe').first()
            self.assertEqual(uid.identifier, 'John Doe')

            uid = session.query(UniqueIdentity).\
                    filter(UniqueIdentity.identifier == 'Jane Roe').first()
            self.assertEqual(uid.identifier, 'Jane Roe')

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
            domains = session.query(Domain).\
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

    def test_add_domains(self):
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
                filter(UniqueIdentity.identifier == 'John Smith',
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

        # First, add a set of identities, including some organizations
        # and enrollments
        api.add_unique_identity(self.db, 'John Smith')
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
                filter(UniqueIdentity.identifier == 'John Smith').first()
            self.assertEqual(uid1, None)

            enrollments = session.query(Enrollment).\
                filter(UniqueIdentity.identifier == 'John Smith').all()
            self.assertEqual(len(enrollments), 0)

        # Delete the last identity
        api.delete_unique_identity(self.db, 'Jane Rae')

        with self.db.connect() as session:
            uid2 = session.query(UniqueIdentity).\
                filter(UniqueIdentity.identifier == 'Jane Rae').first()
            self.assertEqual(uid2, None)

            # Check if there only remains one unique identity and one
            # enrollment
            identities = session.query(UniqueIdentity).all()
            self.assertEqual(len(identities), 1)
            self.assertEqual(identities[0].identifier, 'John Doe')

            enrollments = session.query(Enrollment).all()
            self.assertEqual(len(enrollments), 1)
            self.assertEqual(enrollments[0].identity.identifier, 'John Doe')
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

            enr1 = session.query(Enrollment).\
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
            self.assertEqual(enrollments[0].identity.identifier, 'John Smith')
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
            self.assertEqual(enrollments[0].identity.identifier, 'Jane Rae')

            enrollments = session.query(Enrollment).join(Organization).\
                    filter(Organization.name == 'Example').all()
            self.assertEqual(len(enrollments), 1)
            self.assertEqual(enrollments[0].identity.identifier, 'John Smith')

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
        """Check if it fails removing enrollments from an organization
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
        """Check if it fails removing enrollments from a unique identity
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


if __name__ == "__main__":
    unittest.main()
