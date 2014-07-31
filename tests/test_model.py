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

import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import sessionmaker

from sortinghat.db.model import ModelBase, Organization, Domain, UniqueIdentity, Enrollment
from tests.config import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT


DUP_CHECK_ERROR = 'Duplicate entry'
NULL_CHECK_ERROR = 'cannot be null'


class MockDatabase(object):

    def __init__(self, user, password, database, host, port):
        # Create an engine
        self.url = URL('mysql', user, password, host, port, database)
        self._engine = create_engine(self.url, echo=True)
        self._Session = sessionmaker(bind=self._engine)

        # Create the schema on the database.
        # It won't replace any existing schema
        ModelBase.metadata.create_all(self._engine)

    def session(self):
        return self._Session()


class TestCaseBase(unittest.TestCase):
    """Defines common setup and teardown methods on model unit tests"""

    @classmethod
    def setUpClass(cls):
        cls.db = MockDatabase(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

    def setUp(self):
        self.session = self.db.session()

    def tearDown(self):
        self.session.rollback()

        for table in reversed(ModelBase.metadata.sorted_tables):
            self.session.execute(table.delete())
            self.session.commit()

        self.session.close()


class TestOrganization(TestCaseBase):
    """Unit tests for Organization class"""

    def test_unique_organizations(self):
        """Check whether organizations are unique"""

        with self.assertRaises(IntegrityError):
            org1 = Organization(name='Example')
            org2 = Organization(name='Example')

            self.session.add(org1)
            self.session.add(org2)
            self.session.commit()

    def test_none_name_organizations(self):
        """Check whether organizations without name can be stored"""

        with self.assertRaisesRegexp(OperationalError, NULL_CHECK_ERROR):
            org1 = Organization()

            self.session.add(org1)
            self.session.commit()


class TestDomain(TestCaseBase):
    """Unit tests for Domain class"""

    def test_unique_domains(self):
        """Check whether domains are unique"""

        with self.assertRaisesRegexp(IntegrityError, DUP_CHECK_ERROR):
            org1 = Organization(name='Example')
            self.session.add(org1)

            dom1 = Domain(domain='example.com')
            dom1.company = org1
            dom2 = Domain(domain='example.com')
            dom2.company = org1

            self.session.add(dom1)
            self.session.add(dom2)
            self.session.commit()

    def test_not_null_organizations(self):
        """Check whether every domain is assigned to an organization"""

        with self.assertRaisesRegexp(OperationalError, NULL_CHECK_ERROR):
            dom1 = Domain(domain='example.com')
            self.session.add(dom1)
            self.session.commit()

    def test_none_name_domains(self):
        """Check whether domains without name can be stored"""

        with self.assertRaisesRegexp(OperationalError, NULL_CHECK_ERROR):
            org1 = Organization(name='Example')
            self.session.add(org1)

            dom1 = Domain()
            dom1.company = org1

            self.session.add(dom1)
            self.session.commit()


class TestUniqueIdentity(TestCaseBase):
    """Unit tests for UniqueIdentity class"""

    def test_not_null_identifiers(self):
        """Check whether every unique identity has an identifier"""

        with self.assertRaisesRegexp(OperationalError, NULL_CHECK_ERROR):
            uid = UniqueIdentity()
            self.session.add(uid)
            self.session.commit()


class TestEnrollment(TestCaseBase):
    """Unit tests for Enrollment class"""

    def test_not_null_relationships(self):
        """Check whether every enrollment is assigned organizations and unique identities"""

        with self.assertRaisesRegexp(OperationalError, NULL_CHECK_ERROR):
            rol1 = Enrollment()
            self.session.add(rol1)
            self.session.commit()

        self.session.rollback()

        with self.assertRaisesRegexp(OperationalError, NULL_CHECK_ERROR):
            uid = UniqueIdentity(identifier='John Smith')
            self.session.add(uid)

            rol2 = Enrollment(user=uid)
            self.session.add(rol2)
            self.session.commit()

        self.session.rollback()

        with self.assertRaisesRegexp(OperationalError, NULL_CHECK_ERROR):
            org = Organization(name='Example')
            self.session.add(org)

            rol3 = Enrollment(organization=org)
            self.session.add(rol3)
            self.session.commit()

        self.session.rollback()

    def test_unique_enrollments(self):
        """Check if there is only one tuple with the same values"""

        with self.assertRaisesRegexp(IntegrityError, DUP_CHECK_ERROR):
            uid = UniqueIdentity(identifier='John Smith')
            self.session.add(uid)

            org = Organization(name='Example')
            self.session.add(org)

            rol1 = Enrollment(user=uid, organization=org)
            rol2 = Enrollment(user=uid, organization=org)

            self.session.add(rol1)
            self.session.add(rol2)
            self.session.commit()

    def test_default_enrollment_period(self):
        """Check whether the default period is set when initializing the class"""

        import datetime

        uid = UniqueIdentity(identifier='John Smith')
        self.session.add(uid)

        org = Organization(name='Example')
        self.session.add(org)

        rol1 = Enrollment(user=uid, organization=org)
        self.session.add(rol1)
        self.session.commit()

        self.assertEqual(rol1.init, datetime.datetime(1900, 1, 1, 0, 0, 0))
        self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1, 0, 0, 0))

        # Setting init and end dates to None produce the same result
        rol2 = Enrollment(user=uid, organization=org,
                          init=None, end=datetime.datetime(2222, 1, 1, 0, 0, 0))
        self.session.add(rol2)
        self.session.commit()

        self.assertEqual(rol2.init, datetime.datetime(1900, 1, 1, 0, 0, 0))
        self.assertEqual(rol2.end, datetime.datetime(2222, 1, 1, 0, 0, 0))

        rol3 = Enrollment(user=uid, organization=org,
                          init=datetime.datetime(1999, 1, 1, 0, 0, 0), end=None)
        self.session.add(rol3)
        self.session.commit()

        self.assertEqual(rol3.init, datetime.datetime(1999, 1, 1, 0, 0, 0))
        self.assertEqual(rol3.end, datetime.datetime(2100, 1, 1, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
