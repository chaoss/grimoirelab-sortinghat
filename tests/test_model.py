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

import configparser
import datetime
import sys
import unittest

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import IntegrityError, InternalError, StatementError
from sqlalchemy.orm import sessionmaker

from sortinghat.db.model import ModelBase, Organization, Domain, Country,\
    UniqueIdentity, Identity, Profile, Enrollment, MatchingBlacklist

from tests.base import Database, CONFIG_FILE

DUP_CHECK_ERROR = 'Duplicate entry'
NULL_CHECK_ERROR = 'cannot be null'
INVALID_DATATYPE_ERROR = 'TypeError'


class MockDatabase(object):

    def __init__(self, user, password, database, host, port):
        driver = 'mysql+pymysql'

        self.url = URL(driver, user, password, host, port, database)

        # Hack to establish SSL connection (see #231)
        try:
            self._engine = create_engine(self.url, echo=True,
                                         connect_args={'ssl': {'activate': True}})
            self._engine.connect().close()
        except InternalError:
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
        config = configparser.ConfigParser()
        config.read(config.read(CONFIG_FILE))
        cls.db_kwargs = {'user': config['Database']['user'],
                         'password': config['Database']['password'],
                         'database': config['Database']['name'],
                         'host': config['Database']['host'],
                         'port': config['Database']['port']}
        if 'create' in config['Database']:
            cls.create = config['Database'].getboolean('create')
        else:
            cls.create = False
        if cls.create:
            Database.create(**cls.db_kwargs)
        cls.db = MockDatabase(**cls.db_kwargs)

    @classmethod
    def tearDownClass(cls):
        if cls.create:
            Database.drop(**cls.db_kwargs)

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

        with self.assertRaisesRegex(IntegrityError, NULL_CHECK_ERROR):
            org1 = Organization()

            self.session.add(org1)
            self.session.commit()

    def test_charset(self):
        """Check encoding charset"""

        # With an invalid encoding both names wouldn't be inserted;
        # In MySQL, chars 'ı' and 'i' are considered the same with a
        # collation distinct to <charset>_unicode_ci
        org1 = Organization(name='ıCompany'.encode('utf-8'))
        org2 = Organization(name='iCompany')

        self.session.add(org1)
        self.session.add(org2)
        self.session.commit()

    def test_to_dict(self):
        """Test output of to_dict() method"""

        org = Organization(name='Example')
        self.session.add(org)

        dom1 = Domain(domain='example.com',
                      is_top_domain=True,
                      organization=org)
        dom2 = Domain(domain='us.example.net',
                      is_top_domain=False,
                      organization=org)
        self.session.add(dom1)
        self.session.add(dom2)
        self.session.commit()

        # Tests
        d = org.to_dict()

        self.assertIsInstance(d, dict)
        self.assertEqual(d['name'], 'Example')

        doms = d['domains']
        self.assertEqual(len(doms), 2)

        d0 = doms[0]
        self.assertEqual(d0['domain'], 'example.com')
        self.assertEqual(d0['top_domain'], True)
        self.assertEqual(d0['organization'], 'Example')

        d1 = doms[1]
        self.assertEqual(d1['domain'], 'us.example.net')
        self.assertEqual(d1['top_domain'], False)
        self.assertEqual(d1['organization'], 'Example')


class TestDomain(TestCaseBase):
    """Unit tests for Domain class"""

    def test_unique_domains(self):
        """Check whether domains are unique"""

        with self.assertRaisesRegex(IntegrityError, DUP_CHECK_ERROR):
            org1 = Organization(name='Example')
            self.session.add(org1)

            dom1 = Domain(domain='example.com')
            dom1.organization = org1
            dom2 = Domain(domain='example.com')
            dom2.organization = org1

            self.session.add(dom1)
            self.session.add(dom2)
            self.session.commit()

    def test_not_null_organizations(self):
        """Check whether every domain is assigned to an organization"""

        with self.assertRaisesRegex(IntegrityError, NULL_CHECK_ERROR):
            dom1 = Domain(domain='example.com')
            self.session.add(dom1)
            self.session.commit()

    def test_none_name_domains(self):
        """Check whether domains without name can be stored"""

        with self.assertRaisesRegex(IntegrityError, NULL_CHECK_ERROR):
            org1 = Organization(name='Example')
            self.session.add(org1)

            dom1 = Domain()
            dom1.organization = org1

            self.session.add(dom1)
            self.session.commit()

    def test_is_top_domain_invalid_type(self):
        """Check invalid values on top_domain bool column"""

        with self.assertRaisesRegex(StatementError, INVALID_DATATYPE_ERROR):
            org1 = Organization(name='Example')
            self.session.add(org1)

            dom1 = Domain(domain='example.com', is_top_domain='True')
            dom1.organization = org1

            self.session.add(dom1)
            self.session.commit()

    def test_to_dict(self):
        """Test output of to_dict() method"""

        org = Organization(name='Example')
        self.session.add(org)

        dom = Domain(domain='example.com',
                     is_top_domain=True,
                     organization=org)
        self.session.add(dom)
        self.session.commit()

        # Tests
        d = dom.to_dict()

        self.assertIsInstance(d, dict)
        self.assertEqual(d['domain'], 'example.com')
        self.assertEqual(d['top_domain'], True)
        self.assertEqual(d['organization'], 'Example')


class TestCountry(TestCaseBase):
    """Unit tests for Country class"""

    def test_unique_countries(self):
        """Check whether countries are unique"""

        with self.assertRaisesRegex(IntegrityError, DUP_CHECK_ERROR):
            c1 = Country(code='ES', name='Spain', alpha3='ESP')
            self.session.add(c1)

            c2 = Country(code='ES', name='España', alpha3='E')
            self.session.add(c2)

            self.session.commit()

    def test_unique_alpha3(self):
        """Check whether alpha3 codes are unique"""

        with self.assertRaisesRegex(IntegrityError, DUP_CHECK_ERROR):
            c1 = Country(code='ES', name='Spain', alpha3='ESP')
            self.session.add(c1)

            c2 = Country(code='E', name='Spain', alpha3='ESP')
            self.session.add(c2)

            self.session.commit()

    def test_none_name_country(self):
        """Check whether countries without name can be stored"""

        with self.assertRaisesRegex(IntegrityError, NULL_CHECK_ERROR):
            c = Country(code='ES', alpha3='ESP')
            self.session.add(c)

            self.session.commit()

    def test_none_alpha3_country(self):
        """Check whether countries without alpha3 code can be stored"""

        with self.assertRaisesRegex(IntegrityError, NULL_CHECK_ERROR):
            c = Country(code='ES', name='Spain')
            self.session.add(c)

            self.session.commit()

    def test_to_dict(self):
        """Test output of to_dict() method"""

        c = Country(code='ES', name='Spain', alpha3='ESP')
        self.session.add(c)

        # Tests
        d = c.to_dict()

        self.assertIsInstance(d, dict)
        self.assertEqual(d['code'], 'ES')
        self.assertEqual(d['name'], 'Spain')
        self.assertEqual(d['alpha3'], 'ESP')


class TestUniqueIdentity(TestCaseBase):
    """Unit tests for UniqueIdentity class"""

    def test_unique_uuid(self):
        """Check whether the uuid is in fact unique"""

        with self.assertRaisesRegex(IntegrityError, DUP_CHECK_ERROR):
            uid1 = UniqueIdentity(uuid='John Smith')
            uid2 = UniqueIdentity(uuid='John Smith')

            self.session.add(uid1)
            self.session.add(uid2)
            self.session.commit()

    def test_to_dict(self):
        """Test output of to_dict() method"""

        c = Country(code='US', name='United States of America', alpha3='USA')
        self.session.add(c)

        uid = UniqueIdentity(uuid='John Smith')
        self.session.add(uid)

        id1 = Identity(id='A', name='John Smith', email='jsmith@example.com',
                       username='jsmith', source='scm', uuid='John Smith')
        id2 = Identity(id='B', name=None, email='jsmith@example.net',
                       username=None, source='scm', uuid='John Smith')

        self.session.add(id1)
        self.session.add(id2)
        self.session.commit()

        # Tests
        d = uid.to_dict()

        self.assertIsInstance(d, dict)
        self.assertEqual(d['uuid'], 'John Smith')

        self.assertEqual(d['profile'], None)

        identities = d['identities']
        self.assertEqual(len(identities), 2)

        d0 = d['identities'][0]
        self.assertEqual(d0['id'], 'A')
        self.assertEqual(d0['name'], 'John Smith')
        self.assertEqual(d0['email'], 'jsmith@example.com')
        self.assertEqual(d0['username'], 'jsmith')
        self.assertEqual(d0['source'], 'scm')
        self.assertEqual(d0['uuid'], 'John Smith')

        d1 = d['identities'][1]
        self.assertEqual(d1['id'], 'B')
        self.assertEqual(d1['name'], None)
        self.assertEqual(d1['email'], 'jsmith@example.net')
        self.assertEqual(d1['username'], None)
        self.assertEqual(d1['source'], 'scm')
        self.assertEqual(d1['uuid'], 'John Smith')

        prf = Profile(uuid='John Smith', name='Smith, J.',
                      email='jsmith@example.com', is_bot=True,
                      country_code='US')

        # Add profile information
        self.session.add(prf)
        self.session.commit()

        d = uid.to_dict()

        dp = d['profile']
        self.assertEqual(dp['uuid'], 'John Smith')
        self.assertEqual(dp['name'], 'Smith, J.')
        self.assertEqual(dp['email'], 'jsmith@example.com')
        self.assertEqual(dp['is_bot'], True)
        self.assertEqual(dp['country']['code'], 'US')
        self.assertEqual(dp['country']['name'], 'United States of America')


class TestIdentity(TestCaseBase):
    """Unit tests for Identity class"""

    def test_not_null_source(self):
        """Check whether every identity has a source"""

        with self.assertRaisesRegex(IntegrityError, NULL_CHECK_ERROR):
            id1 = Identity(id='A')
            self.session.add(id1)
            self.session.commit()

    def test_unique_identities(self):
        """Check if there is only one tuple with the same values"""

        id1 = Identity(id='A', name='John Smith', email='jsmith@example.com',
                       username='jsmith', source='scm')
        id2 = Identity(id='B', name='John Smith', email='jsmith@example.com',
                       username='jsmith', source='scm')

        with self.assertRaisesRegex(IntegrityError, DUP_CHECK_ERROR):
            self.session.add(id1)
            self.session.add(id2)
            self.session.commit()

        self.session.rollback()

        # Changing an property should not raise any error
        id2.source = 'mls'
        self.session.add(id1)
        self.session.add(id2)
        self.session.commit()

        self.assertNotEqual(id1.id, id2.id)

    def test_charset(self):
        """Check encoding charset"""

        # With an invalid encoding both names wouldn't be inserted;
        # In MySQL, chars 'ı' and 'i' are considered the same with a
        # collation distinct to <charset>_unicode_ci
        id1 = Identity(id='A', name='John Smıth'.encode('utf-8'),
                       email='jsmith@example.com',
                       username='jsmith', source='scm')
        id2 = Identity(id='B', name='John Smith',
                       email='jsmith@example.com',
                       username='jsmith', source='scm')

        self.session.add(id1)
        self.session.add(id2)
        self.session.commit()

    def test_to_dict(self):
        """Test output of to_dict() method"""

        uid = UniqueIdentity(uuid='John Smith')
        self.session.add(uid)

        id1 = Identity(id='A', name='John Smith', email='jsmith@example.com',
                       username='jsmith', source='scm', uuid='John Smith')

        self.session.add(id1)
        self.session.commit()

        # Tests
        d = id1.to_dict()

        self.assertIsInstance(d, dict)
        self.assertEqual(d['id'], 'A')
        self.assertEqual(d['name'], 'John Smith')
        self.assertEqual(d['email'], 'jsmith@example.com')
        self.assertEqual(d['username'], 'jsmith')
        self.assertEqual(d['source'], 'scm')
        self.assertEqual(d['uuid'], 'John Smith')


class TestProfile(TestCaseBase):
    """Unit tests for Profile class"""

    def test_unique_profile(self):
        """Check if there is only one profile for each unique identity"""

        uid = UniqueIdentity(uuid='John Smith')
        self.session.add(uid)

        prf1 = Profile(uuid='John Smith', name='John Smith')
        prf2 = Profile(uuid='John Smith', name='Smith, J.')

        with self.assertRaisesRegex(IntegrityError, DUP_CHECK_ERROR):
            self.session.add(prf1)
            self.session.add(prf2)
            self.session.commit()

    def test_is_bot_invalid_type(self):
        """Check invalid values on is_bot bool column"""

        with self.assertRaisesRegex(StatementError, INVALID_DATATYPE_ERROR):
            uid = UniqueIdentity(uuid='John Smith')
            self.session.add(uid)

            prf = Profile(uuid='John Smith', name='John Smith', is_bot='True')

            self.session.add(prf)
            self.session.commit()

    def test_to_dict(self):
        """Test output of to_dict() method"""

        uid = UniqueIdentity(uuid='John Smith')
        self.session.add(uid)

        c = Country(code='US', name='United States of America', alpha3='USA')
        self.session.add(c)

        prf = Profile(uuid='John Smith', name='Smith, J.',
                      email='jsmith@example.com', is_bot=True,
                      country_code='US')

        self.session.add(prf)
        self.session.commit()

        # Tests
        d = prf.to_dict()

        self.assertIsInstance(d, dict)
        self.assertEqual(d['uuid'], 'John Smith')
        self.assertEqual(d['name'], 'Smith, J.')
        self.assertEqual(d['email'], 'jsmith@example.com')
        self.assertEqual(d['is_bot'], True)
        self.assertEqual(d['country']['code'], 'US')
        self.assertEqual(d['country']['name'], 'United States of America')

        # No country set
        prf = Profile(uuid='John Smith', name='Smith, J.',
                      email='jsmith@example.com', is_bot=True,
                      country_code=None)

        d = prf.to_dict()
        self.assertEqual(d['country'], None)


class TestEnrollment(TestCaseBase):
    """Unit tests for Enrollment class"""

    def test_not_null_relationships(self):
        """Check whether every enrollment is assigned organizations and unique identities"""

        with self.assertRaisesRegex(IntegrityError, NULL_CHECK_ERROR):
            rol1 = Enrollment()
            self.session.add(rol1)
            self.session.commit()

        self.session.rollback()

        with self.assertRaisesRegex(IntegrityError, NULL_CHECK_ERROR):
            uid = UniqueIdentity(uuid='John Smith')
            self.session.add(uid)

            rol2 = Enrollment(uidentity=uid)
            self.session.add(rol2)
            self.session.commit()

        self.session.rollback()

        with self.assertRaisesRegex(IntegrityError, NULL_CHECK_ERROR):
            org = Organization(name='Example')
            self.session.add(org)

            rol3 = Enrollment(organization=org)
            self.session.add(rol3)
            self.session.commit()

        self.session.rollback()

    def test_unique_enrollments(self):
        """Check if there is only one tuple with the same values"""

        with self.assertRaisesRegex(IntegrityError, DUP_CHECK_ERROR):
            uid = UniqueIdentity(uuid='John Smith')
            self.session.add(uid)

            org = Organization(name='Example')
            self.session.add(org)

            rol1 = Enrollment(uidentity=uid, organization=org)
            rol2 = Enrollment(uidentity=uid, organization=org)

            self.session.add(rol1)
            self.session.add(rol2)
            self.session.commit()

    def test_default_enrollment_period(self):
        """Check whether the default period is set when initializing the class"""

        uid = UniqueIdentity(uuid='John Smith')
        self.session.add(uid)

        org = Organization(name='Example')
        self.session.add(org)

        rol1 = Enrollment(uidentity=uid, organization=org)
        self.session.add(rol1)
        self.session.commit()

        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, 0, 0, 0))
        self.assertEqual(rol1.end, datetime.datetime(2100, 1, 1, 0, 0, 0))

        # Setting start and end dates to None produce the same result
        rol2 = Enrollment(uidentity=uid, organization=org,
                          start=None, end=datetime.datetime(2222, 1, 1, 0, 0, 0))
        self.session.add(rol2)
        self.session.commit()

        self.assertEqual(rol2.start, datetime.datetime(1900, 1, 1, 0, 0, 0))
        self.assertEqual(rol2.end, datetime.datetime(2222, 1, 1, 0, 0, 0))

        rol3 = Enrollment(uidentity=uid, organization=org,
                          start=datetime.datetime(1999, 1, 1, 0, 0, 0), end=None)
        self.session.add(rol3)
        self.session.commit()

        self.assertEqual(rol3.start, datetime.datetime(1999, 1, 1, 0, 0, 0))
        self.assertEqual(rol3.end, datetime.datetime(2100, 1, 1, 0, 0, 0))

    def test_to_dict(self):
        """Test output of to_dict() method"""

        uid = UniqueIdentity(uuid='John Smith')
        self.session.add(uid)

        org = Organization(name='Example')
        self.session.add(org)

        rol = Enrollment(uidentity=uid, organization=org,
                         start=datetime.datetime(1999, 1, 1, 0, 0, 0),
                         end=datetime.datetime(2001, 1, 1, 0, 0, 0))

        self.session.add(rol)
        self.session.commit()

        # Tests
        d = rol.to_dict()

        self.assertIsInstance(d, dict)
        self.assertEqual(d['uuid'], 'John Smith')
        self.assertEqual(d['organization'], 'Example')
        self.assertEqual(d['start'], datetime.datetime(1999, 1, 1, 0, 0, 0))
        self.assertEqual(d['end'], datetime.datetime(2001, 1, 1, 0, 0, 0))


class TestMatchingBlacklist(TestCaseBase):
    """Unit tests for MatchingBlacklist class"""

    def test_unique_excluded(self):
        """Check whether the excluded term is in fact unique"""

        with self.assertRaisesRegex(IntegrityError, DUP_CHECK_ERROR):
            mb1 = MatchingBlacklist(excluded='John Smith')
            mb2 = MatchingBlacklist(excluded='John Smith')

            self.session.add(mb1)
            self.session.add(mb2)
            self.session.commit()


if __name__ == "__main__":
    unittest.main()
