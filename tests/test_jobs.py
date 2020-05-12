# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2020 Bitergia
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
import unittest.mock

from dateutil.tz import UTC

from django.contrib.auth import get_user_model
from django.test import TestCase

from grimoirelab_toolkit.datetime import datetime_utcnow

from sortinghat.core import api
from sortinghat.core.context import SortingHatContext
from sortinghat.core.errors import DuplicateRangeError, NotFoundError
from sortinghat.core.jobs import affiliate
from sortinghat.core.models import Individual, Transaction


class TestAffiliateIndividuals(TestCase):
    """Unit tests for affiliate"""

    def setUp(self):
        """Initialize database with a dataset"""

        self.user = get_user_model().objects.create(username='test')
        ctx = SortingHatContext(self.user)

        # Organizations and domains
        api.add_organization(ctx, 'Example')
        api.add_domain(ctx, 'Example', 'example.com', is_top_domain=True)

        api.add_organization(ctx, 'Example Int.')
        api.add_domain(ctx, 'Example Int.', 'u.example.com',
                       is_top_domain=True)
        api.add_domain(ctx, 'Example Int.', 'es.u.example.com')
        api.add_domain(ctx, 'Example Int.', 'en.u.example.com')

        api.add_organization(ctx, 'Bitergia')
        api.add_domain(ctx, 'Bitergia', 'bitergia.com')
        api.add_domain(ctx, 'Bitergia', 'bitergia.org')

        api.add_organization(ctx, 'LibreSoft')

        # John Smith identity
        self.jsmith = api.add_identity(ctx,
                                       source='scm',
                                       email='jsmith@us.example.com',
                                       name='John Smith',
                                       username='jsmith')
        api.add_identity(ctx,
                         source='scm',
                         email='jsmith@example.net',
                         name='John Smith',
                         uuid=self.jsmith.uuid)

        # Add John Doe identity
        self.jdoe = api.add_identity(ctx,
                                     source='unknown',
                                     email=None,
                                     name='John Doe',
                                     username='jdoe')

        # Jane Roe identity
        self.jroe = api.add_identity(ctx,
                                     source='scm',
                                     email='jroe@example.com',
                                     name='Jane Roe',
                                     username='jroe')
        api.add_identity(ctx,
                         source='scm',
                         email='jroe@example.com',
                         uuid=self.jroe.uuid)
        api.add_identity(ctx,
                         source='unknown',
                         email='jroe@bitergia.com',
                         uuid=self.jroe.uuid)

    def test_affiliate(self):
        """Check if all the individuals stored in the registry are affiliated"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                '0c1e1701bc819495acf77ef731023b7d789a9c71': [],
                '17ab00ed3825ec2f50483e33c88df223264182ba': ['Bitergia', 'Example'],
                'dc31d2afbee88a6d1dbc1ef05ec827b878067744': ['Example']
            },
            'errors': []
        }

        job = affiliate.delay(ctx)
        result = job.result

        self.assertDictEqual(result, expected)

        # Check database objects
        individual_db = Individual.objects.get(mk=self.jroe.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 2)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.organization.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[1]
        self.assertEqual(enrollment_db.organization.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        individual_db = Individual.objects.get(mk=self.jsmith.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.organization.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        # John Doe was not affiliated
        individual_db = Individual.objects.get(mk=self.jdoe.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 0)

    def test_affiliate_uuid(self):
        """Check if only the given individuals are affiliated"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                'dc31d2afbee88a6d1dbc1ef05ec827b878067744': ['Example']
            },
            'errors': []
        }

        uuids = ['dc31d2afbee88a6d1dbc1ef05ec827b878067744']
        job = affiliate.delay(ctx, uuids=uuids)

        result = job.result

        self.assertDictEqual(result, expected)

        # Check database objects

        # Only John Smith was affiliated
        individual_db = Individual.objects.get(mk=self.jsmith.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.organization.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        # Jane Roe and John Doe were not affiliated
        individual_db = Individual.objects.get(mk=self.jroe.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 0)

        individual_db = Individual.objects.get(mk=self.jdoe.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 0)

    @unittest.mock.patch('sortinghat.core.api.find_individual_by_uuid')
    def test_not_found_uuid_error(self, mock_find_indv):
        """Check if the affiliation process logs the error when an individual is not found"""

        exc = NotFoundError(entity='dc31d2afbee88a6d1dbc1ef05ec827b878067744')
        mock_find_indv.side_effect = exc

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                'dc31d2afbee88a6d1dbc1ef05ec827b878067744': []
            },
            'errors': [
                "dc31d2afbee88a6d1dbc1ef05ec827b878067744 not found in the registry"
            ]
        }

        uuids = ['dc31d2afbee88a6d1dbc1ef05ec827b878067744']
        job = affiliate.delay(ctx, uuids=uuids)
        result = job.result

        self.assertDictEqual(result, expected)

    @unittest.mock.patch('sortinghat.core.api.add_enrollment')
    def test_enrollment_errors(self, mock_enroll):
        """Check if the affiliation process logs the errors there are errors
        adding enrollments"""

        exc = DuplicateRangeError(start='1900-01-01',
                                  end='2100-01-01',
                                  org='Example')
        mock_enroll.side_effect = exc

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                'dc31d2afbee88a6d1dbc1ef05ec827b878067744': []
            },
            'errors': [
                "range date '1900-01-01'-'2100-01-01' is part of an existing range for Example"
            ]
        }

        uuids = ['dc31d2afbee88a6d1dbc1ef05ec827b878067744']
        job = affiliate.delay(ctx, uuids=uuids)
        result = job.result

        self.assertDictEqual(result, expected)

    def test_transactions(self):
        """Check if the right transactions were created"""

        timestamp = datetime_utcnow()

        ctx = SortingHatContext(self.user)

        affiliate.delay(ctx, job_id='1234-5678-90AB-CDEF')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 4)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'affiliate-1234-5678-90AB-CDEF')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, ctx.user.username)

        for trx in transactions[1:]:
            self.assertIsInstance(trx, Transaction)
            self.assertEqual(trx.name, 'enroll-1234-5678-90AB-CDEF')
            self.assertGreater(trx.created_at, timestamp)
            self.assertEqual(trx.authored_by, ctx.user.username)
