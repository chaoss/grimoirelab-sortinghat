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

from sortinghat.db.model import ModelBase, Organization, Domain
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


class TestOrganization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = MockDatabase(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

    def setUp(self):
        self.session = self.db.session()

    def tearDown(self):
        self.session.rollback()
        self.session.close()

    def test_unique_organizations(self):
        """Check whether organizations are unique"""

        with self.assertRaises(IntegrityError):
            org1 = Organization(name='Example')
            org2 = Organization(name='Example')

            self.session.add(org1)
            self.session.add(org2)
            self.session.commit()


class TestDomain(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = MockDatabase(DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT)

    def setUp(self):
        self.session = self.db.session()

    def tearDown(self):
        self.session.rollback()
        self.session.close()

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


if __name__ == "__main__":
    unittest.main()
