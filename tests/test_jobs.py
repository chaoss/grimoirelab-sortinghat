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
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#

import datetime
import unittest.mock
import json

import httpretty

from dateutil.tz import UTC

from django.contrib.auth import get_user_model
from django.test import TestCase

from django_rq import enqueue

from grimoirelab_toolkit.datetime import datetime_utcnow

from sortinghat.core import api
from sortinghat.core.context import SortingHatContext
from sortinghat.core.errors import DuplicateRangeError, NotFoundError
from sortinghat.core.importer.backend import IdentitiesImporter
from sortinghat.core.jobs import (find_job,
                                  affiliate,
                                  unify,
                                  recommend_affiliations,
                                  recommend_matches,
                                  recommend_gender,
                                  genderize,
                                  import_identities)
from sortinghat.core.models import (Individual,
                                    Transaction,
                                    AffiliationRecommendation,
                                    MergeRecommendation,
                                    GenderRecommendation)
from sortinghat.core.recommendations import RecommendationEngine

JOB_NOT_FOUND_ERROR = "DEF not found in the registry"


def job_echo(s):
    """Function to test job queuing"""
    return s


class TestFindJob(TestCase):
    """Unit tests for find_job"""

    def test_find_job(self):
        """Check if it finds a job in the registry"""

        job = enqueue(job_echo, 'ABC')
        qjob = find_job(job.id, 'default')
        self.assertEqual(qjob, job)

    def test_not_found_job(self):
        """Check if it raises an exception when the job is not found"""

        enqueue(job_echo, 'ABC')

        with self.assertRaisesRegex(NotFoundError,
                                    JOB_NOT_FOUND_ERROR):
            find_job('DEF', 'default')


class TestRecommendAffiliations(TestCase):
    """Unit tests for recommend_affiliations"""

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

    def test_recommend_affiliations(self):
        """Check if recommendations are obtained for all the individuals stored in the registry"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                '17ab00ed3825ec2f50483e33c88df223264182ba': ['Bitergia', 'Example'],
                'dc31d2afbee88a6d1dbc1ef05ec827b878067744': ['Example']
            }
        }

        job = recommend_affiliations.delay(ctx)
        result = job.result

        self.assertDictEqual(result, expected)

    def test_recommend_affiliations_uuid(self):
        """Check if recommendations are obtained only for the given individuals"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                'dc31d2afbee88a6d1dbc1ef05ec827b878067744': ['Example']
            }
        }

        uuids = ['dc31d2afbee88a6d1dbc1ef05ec827b878067744']
        job = recommend_affiliations.delay(ctx, uuids=uuids)

        result = job.result

        self.assertDictEqual(result, expected)

        recommendation = AffiliationRecommendation.objects.first()
        self.assertEqual(recommendation.individual.mk, uuids[0])
        self.assertEqual(recommendation.organization.name, 'Example')
        self.assertEqual(recommendation.applied, None)

    def test_recommend_affiliations_new_identity(self):
        """Check if new recommendations are included when adding new identities"""
        ctx = SortingHatContext(self.user)

        # Test
        expected_1 = {
            'results': {
                'dc31d2afbee88a6d1dbc1ef05ec827b878067744': ['Example']
            }
        }
        expected_2 = {
            'results': {
                'dc31d2afbee88a6d1dbc1ef05ec827b878067744': ['Bitergia', 'Example']
            }
        }

        uuids = ['dc31d2afbee88a6d1dbc1ef05ec827b878067744']
        job = recommend_affiliations.delay(ctx, uuids=uuids)
        result = job.result

        self.assertDictEqual(result, expected_1)

        recommendation = AffiliationRecommendation.objects.get(individual__mk=uuids[0])
        self.assertEqual(recommendation.individual.mk, uuids[0])
        self.assertEqual(recommendation.organization.name, 'Example')
        self.assertEqual(recommendation.applied, None)

        api.add_identity(ctx,
                         source='unknown',
                         email='jsmith@bitergia.com',
                         uuid=self.jsmith.uuid)

        job = recommend_affiliations.delay(ctx, uuids=uuids)
        result = job.result

        self.assertDictEqual(result, expected_2)

        recommendations = AffiliationRecommendation.objects.filter(individual__mk=uuids[0])
        self.assertEqual(len(recommendations), 2)
        for rec in recommendations:
            self.assertEqual(rec.individual.mk, uuids[0])
            self.assertIn(rec.organization.name, ['Bitergia', 'Example'])

    def test_recommend_affiliations_last_modified(self):
        """Check if recommendations are obtained only for individuals modified after a date"""
        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                'dc31d2afbee88a6d1dbc1ef05ec827b878067744': ['Bitergia', 'Example']
            }
        }

        timestamp = datetime_utcnow()

        api.add_identity(ctx,
                         source='unknown',
                         email='jsmith@bitergia.com',
                         uuid=self.jsmith.uuid)

        job = recommend_affiliations.delay(ctx, uuids=None, last_modified=timestamp)
        result = job.result

        self.assertDictEqual(result, expected)

        recommendations = AffiliationRecommendation.objects.filter(individual__mk=self.jsmith.uuid)
        self.assertEqual(len(recommendations), 2)
        for rec in recommendations:
            self.assertEqual(rec.individual.mk, self.jsmith.uuid)
            self.assertIn(rec.organization.name, ['Bitergia', 'Example'])

    @unittest.mock.patch('sortinghat.core.api.find_individual_by_uuid')
    def test_not_found_uuid_error(self, mock_find_indv):
        """Check if the recommendation process returns no results when an individual is not found"""

        exc = NotFoundError(entity='1234567890abcdefg')
        mock_find_indv.side_effect = exc

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {}
        }

        uuids = ['1234567890abcdefg']
        job = recommend_affiliations.delay(ctx, uuids=uuids)
        result = job.result

        self.assertDictEqual(result, expected)

        total_recommend = AffiliationRecommendation.objects.count()
        self.assertEqual(total_recommend, 0)

    def test_transactions(self):
        """Check if the right transactions were created"""

        timestamp = datetime_utcnow()

        ctx = SortingHatContext(self.user)

        recommend_affiliations.delay(ctx, job_id='1234-5678-90AB-CDEF')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'recommend_affiliations-1234-5678-90AB-CDEF')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, ctx.user.username)


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
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[1]
        self.assertEqual(enrollment_db.group.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        individual_db = Individual.objects.get(mk=self.jsmith.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        # John Doe was not affiliated
        individual_db = Individual.objects.get(mk=self.jdoe.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 0)

    def test_affiliate_last_modified(self):
        """Check if only the individuals modified after a date are affiliated"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                'dc31d2afbee88a6d1dbc1ef05ec827b878067744': ['Bitergia', 'Example']
            },
            'errors': []
        }

        timestamp = datetime_utcnow()

        api.add_identity(ctx,
                         source='unknown',
                         email='jsmith@bitergia.com',
                         uuid=self.jsmith.uuid)

        job = affiliate.delay(ctx, uuids=None, last_modified=timestamp)
        result = job.result

        self.assertDictEqual(result, expected)

        # Check database objects

        # Only John Smith was affiliated
        individual_db = Individual.objects.get(mk=self.jsmith.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 2)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[1]
        self.assertEqual(enrollment_db.group.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        # Jane Roe and John Doe were not affiliated
        individual_db = Individual.objects.get(mk=self.jdoe.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 0)

        individual_db = Individual.objects.get(mk=self.jroe.uuid)
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
        self.assertEqual(enrollment_db.group.name, 'Example')
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
            'results': {},
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
                                  group='Example')
        mock_enroll.side_effect = exc

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {},
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


class TestRecommendMatches(TestCase):
    """Unit tests for recommend_matches"""

    def setUp(self):
        """Initialize database with a dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        # Individual 1
        self.john_smith = api.add_identity(self.ctx,
                                           email='jsmith@example.com',
                                           name='John Smith',
                                           source='scm')
        self.js2 = api.add_identity(self.ctx,
                                    name='John Smith',
                                    source='scm',
                                    uuid=self.john_smith.uuid)
        self.js3 = api.add_identity(self.ctx,
                                    username='jsmith',
                                    source='scm',
                                    uuid=self.john_smith.uuid)
        self.js4 = api.add_identity(self.ctx,
                                    email='jsmith',
                                    source='scm',
                                    uuid=self.john_smith.uuid)

        # Individual 2
        self.jsmith = api.add_identity(self.ctx,
                                       name='J. Smith',
                                       username='john_smith',
                                       source='alt')
        self.jsm2 = api.add_identity(self.ctx,
                                     name='John Smith',
                                     username='jsmith',
                                     source='alt',
                                     uuid=self.jsmith.uuid)
        self.jsm3 = api.add_identity(self.ctx,
                                     email='jsmith@example.com',
                                     source='alt',
                                     uuid=self.jsmith.uuid)

        # Individual 3
        self.jane_rae = api.add_identity(self.ctx,
                                         name='Janer Rae',
                                         source='mls')
        self.jr2 = api.add_identity(self.ctx,
                                    email='jane.rae@example.net',
                                    name='Jane Rae Doe',
                                    source='mls',
                                    uuid=self.jane_rae.uuid)

        # Individual 4
        self.js_alt = api.add_identity(self.ctx,
                                       name='J. Smith',
                                       username='john_smith',
                                       source='scm')
        self.js_alt2 = api.add_identity(self.ctx,
                                        email='JSmith@example.com',
                                        username='john_smith',
                                        source='mls',
                                        uuid=self.js_alt.uuid)
        self.js_alt3 = api.add_identity(self.ctx,
                                        username='Smith. J',
                                        source='mls',
                                        uuid=self.js_alt.uuid)
        self.js_alt4 = api.add_identity(self.ctx,
                                        email='JSmith@example.com',
                                        name='Smith. J',
                                        source='mls',
                                        uuid=self.js_alt.uuid)

        # Individual 5
        self.jrae = api.add_identity(self.ctx,
                                     email='jrae@example.net',
                                     name='Jane Rae Doe',
                                     source='mls')
        self.jrae2 = api.add_identity(self.ctx,
                                      name='jrae',
                                      source='mls',
                                      uuid=self.jrae.uuid)

        # Individual 6
        self.jrae_no_name = api.add_identity(self.ctx,
                                             name='jrae',
                                             source='scm')

        # Individual 7
        self.jsmith_no_email = api.add_identity(self.ctx,
                                                email='jsmith',
                                                source='mls')

    def test_recommend_matches_all_individuals(self):
        """Check if recommendations are obtained for all individuals"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                self.js_alt.individual.mk: sorted([self.jsmith.individual.mk]),
                self.jsmith.individual.mk: sorted([self.john_smith.individual.mk, self.js_alt.individual.mk]),
                self.jrae_no_name.individual.mk: [],
                self.jsmith_no_email.individual.mk: [],
                self.john_smith.individual.mk: sorted([self.jsmith.individual.mk]),
                self.jrae.individual.mk: sorted([self.jane_rae.individual.mk]),
                self.jane_rae.individual.mk: sorted([self.jrae.individual.mk]),
            }
        }

        recommendations_expected = [
            sorted([self.js_alt.individual.mk, self.jsmith.individual.mk]),
            sorted([self.jsmith.individual.mk, self.john_smith.individual.mk]),
            sorted([self.jrae.individual.mk, self.jane_rae.individual.mk]),
        ]

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        job = recommend_matches.delay(ctx,
                                      None,
                                      None,
                                      criteria)
        # Preserve job results order for the comparison against the expected results
        result = job.result
        for key in result['results']:
            result['results'][key] = sorted(result['results'][key])

        self.assertDictEqual(result, expected)

        self.assertEqual(MergeRecommendation.objects.count(), 3)

        for rec in recommendations_expected:
            self.assertTrue(
                MergeRecommendation.objects.filter(individual1=rec[0],
                                                   individual2=rec[1]).exists())

        # Should have the same result as passing all the uuids
        all_source_uuids = [self.john_smith.uuid, self.jsmith.uuid,
                            self.jane_rae.uuid, self.js_alt.uuid, self.jrae.uuid,
                            self.jrae_no_name.uuid, self.jsmith_no_email.uuid]

        job_uuids = recommend_matches.delay(ctx,
                                            all_source_uuids,
                                            None,
                                            criteria)
        result_all_uuids = job_uuids.result
        for key in result_all_uuids['results']:
            result_all_uuids['results'][key] = sorted(result_all_uuids['results'][key])

        self.assertDictEqual(result, result_all_uuids)

    def test_recommend_matches_all_individuals_no_strict(self):
        """Check if recommendations are obtained for all individuals with strict mode disabled"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                self.js_alt.individual.mk: sorted([self.jsmith.individual.mk]),
                self.jsmith.individual.mk: sorted([self.john_smith.individual.mk,
                                                   self.js_alt.individual.mk]),
                self.jrae_no_name.individual.mk: sorted([self.jrae.individual.mk]),
                self.jsmith_no_email.individual.mk: sorted([self.john_smith.individual.mk]),
                self.john_smith.individual.mk: sorted([self.jsmith.individual.mk,
                                                       self.jsmith_no_email.individual.mk]),
                self.jrae.individual.mk: sorted([self.jane_rae.individual.mk,
                                                 self.jrae_no_name.individual.mk]),
                self.jane_rae.individual.mk: sorted([self.jrae.individual.mk]),
            }
        }

        recommendations_expected = [
            sorted([self.js_alt.individual.mk, self.jsmith.individual.mk]),
            sorted([self.jsmith.individual.mk, self.john_smith.individual.mk]),
            sorted([self.jrae_no_name.individual.mk, self.jrae.individual.mk]),
            sorted([self.jsmith_no_email.individual.mk, self.john_smith.individual.mk]),
            sorted([self.jrae.individual.mk, self.jane_rae.individual.mk]),
        ]

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        job = recommend_matches.delay(ctx,
                                      None,
                                      None,
                                      criteria,
                                      strict=False)
        # Preserve job results order for the comparison against the expected results
        result = job.result
        for key in result['results']:
            result['results'][key] = sorted(result['results'][key])

        self.assertDictEqual(result, expected)

        self.assertEqual(MergeRecommendation.objects.count(), 5)

        for rec in recommendations_expected:
            self.assertTrue(
                MergeRecommendation.objects.filter(individual1=rec[0],
                                                   individual2=rec[1]).exists())

        # Should have the same result as passing all the uuids
        all_source_uuids = [self.john_smith.uuid, self.jsmith.uuid,
                            self.jane_rae.uuid, self.js_alt.uuid, self.jrae.uuid,
                            self.jrae_no_name.uuid, self.jsmith_no_email.uuid]

        job_uuids = recommend_matches.delay(ctx,
                                            all_source_uuids,
                                            None,
                                            criteria,
                                            strict=False)
        result_all_uuids = job_uuids.result
        for key in result_all_uuids['results']:
            result_all_uuids['results'][key] = sorted(result_all_uuids['results'][key])

        self.assertDictEqual(result, result_all_uuids)

    def test_recommend_matches(self):
        """Check if recommendations are obtained for the specified individuals"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                self.john_smith.uuid: sorted([self.jsmith.individual.mk]),
                self.jrae_no_name.uuid: [],
                self.jr2.uuid: sorted([self.jrae.individual.mk])
            }
        }

        recommendations_expected = [
            sorted([self.john_smith.individual.mk, self.jsmith.individual.mk]),
            sorted([self.jr2.individual.mk, self.jrae.individual.mk]),
        ]

        source_uuids = [self.john_smith.uuid, self.jrae_no_name.uuid, self.jr2.uuid]
        target_uuids = [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                        self.js4.uuid,
                        self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                        self.jane_rae.uuid, self.jr2.uuid,
                        self.js_alt.uuid, self.js_alt2.uuid,
                        self.js_alt3.uuid, self.js_alt4.uuid,
                        self.jrae.uuid, self.jrae2.uuid,
                        self.jrae_no_name.uuid, self.jsmith_no_email.uuid]

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        job = recommend_matches.delay(ctx,
                                      source_uuids,
                                      target_uuids,
                                      criteria)
        # Preserve job results order for the comparison against the expected results
        result = job.result
        for key in result['results']:
            result['results'][key] = sorted(result['results'][key])

        self.assertDictEqual(result, expected)

        self.assertEqual(MergeRecommendation.objects.count(), 2)

        for rec in recommendations_expected:
            self.assertTrue(
                MergeRecommendation.objects.filter(individual1=rec[0],
                                                   individual2=rec[1]).exists())

    def test_recommend_matches_no_strict(self):
        """Check if recommendations are obtained for the specified individuals without strict mode"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                self.john_smith.uuid: sorted([self.jsmith.individual.mk]),
                self.jrae_no_name.uuid: sorted([self.jrae.individual.mk]),
                self.jr2.uuid: sorted([self.jrae.individual.mk])
            }
        }

        recommendations_expected = [
            sorted([self.john_smith.individual.mk, self.jsmith.individual.mk]),
            sorted([self.jrae_no_name.individual.mk, self.jrae.individual.mk]),
            sorted([self.jr2.individual.mk, self.jrae.individual.mk])
        ]

        source_uuids = [self.john_smith.uuid, self.jrae_no_name.uuid, self.jr2.uuid]
        target_uuids = [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                        self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                        self.jane_rae.uuid, self.jr2.uuid,
                        self.js_alt.uuid, self.js_alt2.uuid,
                        self.js_alt3.uuid, self.js_alt4.uuid,
                        self.jrae.uuid, self.jrae2.uuid, self.jrae_no_name.uuid]

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        job = recommend_matches.delay(ctx,
                                      source_uuids,
                                      target_uuids,
                                      criteria,
                                      strict=False)
        # Preserve job results order for the comparison against the expected results
        result = job.result
        for key in result['results']:
            result['results'][key] = sorted(result['results'][key])

        self.assertDictEqual(result, expected)

        self.assertEqual(MergeRecommendation.objects.count(), 3)

        for rec in recommendations_expected:
            self.assertTrue(
                MergeRecommendation.objects.filter(individual1=rec[0],
                                                   individual2=rec[1]).exists())

    def test_recommend_matches_verbose(self):
        """Check if recommendations are obtained for the specified individuals, at identity level"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                self.john_smith.uuid: sorted([self.jsm2.uuid,
                                              self.jsm3.uuid,
                                              self.js2.uuid]),
                self.jrae_no_name.uuid: [],
                self.jr2.uuid: sorted([self.jrae.uuid])
            }
        }
        recommendations_expected = [
            sorted([self.john_smith.individual.mk, self.jsm2.individual.mk]),
            sorted([self.jr2.individual.mk, self.jrae.individual.mk])
        ]

        source_uuids = [self.john_smith.uuid, self.jrae_no_name.uuid, self.jr2.uuid]
        target_uuids = [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                        self.js4.uuid,
                        self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                        self.jane_rae.uuid, self.jr2.uuid,
                        self.js_alt.uuid, self.js_alt2.uuid,
                        self.js_alt3.uuid, self.js_alt4.uuid,
                        self.jrae.uuid, self.jrae2.uuid,
                        self.jrae_no_name.uuid, self.jsmith_no_email.uuid]

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        job = recommend_matches.delay(ctx,
                                      source_uuids,
                                      target_uuids,
                                      criteria,
                                      verbose=True)
        # Preserve job results order for the comparison against the expected results
        result = job.result
        for key in result['results']:
            result['results'][key] = sorted(result['results'][key])

        self.assertDictEqual(result, expected)

        self.assertEqual(MergeRecommendation.objects.count(), 2)

        for rec in recommendations_expected:
            self.assertTrue(
                MergeRecommendation.objects.filter(individual1=rec[0],
                                                   individual2=rec[1]).exists())

    def test_recommend_matches_verbose_no_strict(self):
        """Check if recommendations are obtained for the specified individuals, at identity level,
        with strict mode disabled"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                self.john_smith.uuid: sorted([self.jsm2.uuid,
                                              self.jsm3.uuid,
                                              self.js2.uuid]),
                self.jrae_no_name.uuid: sorted([self.jrae2.uuid]),
                self.jr2.uuid: sorted([self.jrae.uuid])
            }
        }

        recommendations_expected = [
            sorted([self.john_smith.individual.mk, self.jsm2.individual.mk]),
            sorted([self.jrae_no_name.individual.mk, self.jrae.individual.mk]),
            sorted([self.jr2.individual.mk, self.jrae.individual.mk])
        ]

        source_uuids = [self.john_smith.uuid, self.jrae_no_name.uuid, self.jr2.uuid]
        target_uuids = [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                        self.js4.uuid,
                        self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                        self.jane_rae.uuid, self.jr2.uuid,
                        self.js_alt.uuid, self.js_alt2.uuid,
                        self.js_alt3.uuid, self.js_alt4.uuid,
                        self.jrae.uuid, self.jrae2.uuid,
                        self.jrae_no_name.uuid, self.jsmith_no_email.uuid]

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        job = recommend_matches.delay(ctx,
                                      source_uuids,
                                      target_uuids,
                                      criteria,
                                      verbose=True,
                                      strict=False)
        # Preserve job results order for the comparison against the expected results
        result = job.result
        for key in result['results']:
            result['results'][key] = sorted(result['results'][key])

        self.assertDictEqual(result, expected)

        self.assertEqual(MergeRecommendation.objects.count(), 3)

        for rec in recommendations_expected:
            self.assertTrue(
                MergeRecommendation.objects.filter(individual1=rec[0],
                                                   individual2=rec[1]).exists())

    def test_recommend_matches_match_source(self):
        """Check if recommendations are obtained when the identities share the source"""

        ctx = SortingHatContext(self.user)

        jr3 = api.add_identity(self.ctx,
                               name='J. Rae',
                               username='jane_rae',
                               source='github',
                               uuid=self.jane_rae.uuid)
        jrae_github = api.add_identity(self.ctx,
                                       name='Jane Rae',
                                       username='jane_rae',
                                       source='github')

        # Test
        expected = {
            'results': {
                self.john_smith.uuid: sorted([self.jsm3.individual.mk]),
                self.jrae_no_name.uuid: sorted([self.jrae2.individual.mk]),
                self.jr2.uuid: sorted([jrae_github.individual.mk, self.jrae.individual.mk])
            }
        }

        recommendations_expected = [
            sorted([self.john_smith.individual.mk, self.jsm3.individual.mk]),
            sorted([self.jrae_no_name.individual.mk, self.jrae2.individual.mk]),
            sorted([self.jr2.individual.mk, jrae_github.individual.mk]),
            sorted([self.jr2.individual.mk, self.jrae.individual.mk])
        ]

        source_uuids = [self.john_smith.uuid, self.jrae_no_name.uuid, self.jr2.uuid]
        target_uuids = [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                        self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                        self.jane_rae.uuid, self.jr2.uuid,
                        self.js_alt.uuid, self.js_alt2.uuid,
                        self.js_alt3.uuid, self.js_alt4.uuid,
                        self.jrae.uuid, self.jrae2.uuid, self.jrae_no_name.uuid,
                        jrae_github]

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        job = recommend_matches.delay(ctx,
                                      source_uuids,
                                      target_uuids,
                                      criteria,
                                      strict=False,
                                      match_source=True)
        # Preserve job results order for the comparison against the expected results
        result = job.result
        for key in result['results']:
            result['results'][key] = sorted(result['results'][key])

        self.assertDictEqual(result, expected)

        self.assertEqual(MergeRecommendation.objects.count(), 4)

        for rec in recommendations_expected:
            self.assertTrue(
                MergeRecommendation.objects.filter(individual1=rec[0],
                                                   individual2=rec[1]).exists())

    def test_recommend_matches_github_email(self):
        """Check if recommendations are obtained when a GitHub email matches a username"""

        ctx = SortingHatContext(self.user)

        jr_github = api.add_identity(self.ctx,
                                     name='Jane Rae',
                                     username='jane_rae',
                                     source='github')
        jr1 = api.add_identity(self.ctx,
                               email='32474881+jane_rae@users.noreply.github.com',
                               source='mls')
        jr2 = api.add_identity(self.ctx,
                               email='jane_rae@users.noreply.github.com',
                               source='scm')
        api.add_identity(self.ctx,
                         email='jsmith@users.noreply.github.com',
                         source='scm')
        api.add_identity(self.ctx,
                         email='2474881@users.noreply.github.com',
                         source='mls')
        api.add_identity(self.ctx,
                         email='@users.noreply.github.com',
                         source='scm')

        # Test
        expected = {
            'results': {
                jr_github.uuid: sorted([jr1.uuid, jr2.uuid])
            }
        }

        recommendations_expected = [
            sorted([jr_github.individual.mk, jr1.individual.mk]),
            sorted([jr_github.individual.mk, jr2.individual.mk]),
        ]

        source_uuids = [jr_github.uuid]

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        job = recommend_matches.delay(ctx,
                                      source_uuids,
                                      None,
                                      criteria,
                                      strict=False,
                                      guess_github_user=True)
        # Preserve job results order for the comparison against the expected results
        result = job.result
        for key in result['results']:
            result['results'][key] = sorted(result['results'][key])

        self.assertDictEqual(result, expected)

        self.assertEqual(MergeRecommendation.objects.count(), 2)

        for rec in recommendations_expected:
            self.assertTrue(
                MergeRecommendation.objects.filter(individual1=rec[0],
                                                   individual2=rec[1]).exists())

    def test_recommend_source_not_mk(self):
        """Check if recommendations work when the provided uuid is not an Individual's main key"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                self.js_alt3.uuid: [self.jsm3.individual.mk]
            }
        }
        recommendations_expected = [
            sorted([self.js_alt3.individual.mk, self.jsmith.individual.mk])
        ]

        source_uuids = [self.js_alt3.uuid]
        target_uuids = [self.jsm3.uuid]
        criteria = ['email', 'name', 'username']

        job = recommend_matches.delay(ctx,
                                      source_uuids,
                                      target_uuids,
                                      criteria)
        result = job.result

        self.assertDictEqual(result, expected)

        self.assertEqual(MergeRecommendation.objects.count(), 1)

        for rec in recommendations_expected:
            self.assertTrue(
                MergeRecommendation.objects.filter(individual1=rec[0],
                                                   individual2=rec[1]).exists())

    def test_recommend_matches_empty_target(self):
        """Check if recommendations are obtained for the given individuals against the whole registry"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {
                self.john_smith.uuid: [self.jsmith.individual.mk]
            }
        }
        recommendations_expected = [
            sorted([self.john_smith.individual.mk, self.jsmith.individual.mk])
        ]

        source_uuids = [self.john_smith.uuid]
        target_uuids = None
        criteria = ['email', 'name']

        job = recommend_matches.delay(ctx,
                                      source_uuids,
                                      target_uuids,
                                      criteria)

        # Preserve job results order for the comparison against the expected results
        result = job.result
        for key in result['results']:
            result['results'][key] = sorted(result['results'][key])

        self.assertDictEqual(result, expected)

        self.assertEqual(MergeRecommendation.objects.count(), 1)

        for rec in recommendations_expected:
            self.assertTrue(MergeRecommendation.objects.filter(individual1=rec[0], individual2=rec[1]).exists())

    def test_no_matches_found(self):
        """Check whether it returns no results when there is no matches for the input identity"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {'880b3dfcb3a08712e5831bddc3dfe81fc5d7b331': []}
        }

        source_uuids = [self.john_smith.uuid]
        target_uuids = [self.jrae.uuid]
        criteria = ['email', 'name']

        job = recommend_matches.delay(ctx,
                                      source_uuids,
                                      target_uuids,
                                      criteria)

        result = job.result

        self.assertDictEqual(result, expected)

        total_recommendations = MergeRecommendation.objects.count()
        self.assertEqual(total_recommendations, 0)

    @unittest.mock.patch('sortinghat.core.api.find_individual_by_uuid')
    def test_not_found_uuid_error(self, mock_find_indv):
        """Check if the recommendation process returns no results when an individual is not found"""

        exc = NotFoundError(entity='1234567890abcdefg')
        mock_find_indv.side_effect = exc

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': {'1234567890abcdefg': []}
        }

        source_uuids = ['1234567890abcdefg']
        target_uuids = [self.john_smith.uuid]
        criteria = ['email', 'name']

        job = recommend_matches.delay(ctx,
                                      source_uuids,
                                      target_uuids,
                                      criteria)
        result = job.result

        self.assertDictEqual(result, expected)

    @unittest.mock.patch('sortinghat.core.jobs.RecommendationEngine')
    def test_recommend_matches_with_concurrent_removal(self, mock_recommendation_engine):
        """Check if recommendations are obtained when an identity is removed while the job is running"""

        ctx = SortingHatContext(self.user)

        # Mock RecommendationEngine class to return a non-existing key and an existing one
        def mock_recommend_matches(*args, **kwargs):
            yield (self.john_smith.individual.mk,
                   self.john_smith.individual.mk,
                   ['non_existing_mk', self.jsmith.individual.mk])

        class MockRecommendationEngine(RecommendationEngine):
            RECOMMENDATION_TYPES = {
                'matches': mock_recommend_matches,
            }

        mock_recommendation_engine.return_value = MockRecommendationEngine()

        # Test
        expected = {
            'results': {
                self.john_smith.uuid: sorted(['non_existing_mk', self.jsm3.individual.mk])
            }
        }
        recommendations_expected = [
            sorted([self.jsmith.individual.mk, self.john_smith.individual.mk])
        ]

        source_uuids = [self.john_smith.uuid]
        target_uuids = [self.john_smith.uuid,
                        self.jsmith.uuid]

        criteria = ['email', 'name', 'username']

        job = recommend_matches.delay(ctx,
                                      source_uuids,
                                      target_uuids,
                                      criteria)
        result = job.result

        # Preserve job results order for the comparison against the expected results
        for key in result['results']:
            result['results'][key] = sorted(result['results'][key])

        self.assertDictEqual(result, expected)

        self.assertEqual(MergeRecommendation.objects.count(), 1)

        for rec in recommendations_expected:
            self.assertTrue(
                MergeRecommendation.objects.filter(individual1=rec[0],
                                                   individual2=rec[1]).exists())

    def test_transactions(self):
        """Check if the right transactions were created"""

        timestamp = datetime_utcnow()

        ctx = SortingHatContext(self.user)

        source_uuids = [self.john_smith]
        target_uuids = [self.jsmith]
        criteria = ['email', 'name']

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        recommend_matches.delay(ctx,
                                source_uuids,
                                target_uuids,
                                criteria,
                                job_id='ABCD-EF12-3456-7890')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'recommend_matches-ABCD-EF12-3456-7890')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, ctx.user.username)


class TestUnify(TestCase):
    """Unit tests for unify"""

    def setUp(self):
        """Initialize database with a dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        # Individual 1
        self.john_smith = api.add_identity(self.ctx,
                                           email='jsmith@example.com',
                                           name='John Smith',
                                           source='scm')
        self.js2 = api.add_identity(self.ctx,
                                    name='John Smith',
                                    source='scm',
                                    uuid=self.john_smith.uuid)
        self.js3 = api.add_identity(self.ctx,
                                    username='jsmith',
                                    source='scm',
                                    uuid=self.john_smith.uuid)

        # Individual 2
        self.jsmith = api.add_identity(self.ctx,
                                       name='J. Smith',
                                       username='john_smith',
                                       source='alt')
        self.jsm2 = api.add_identity(self.ctx,
                                     name='John Smith',
                                     username='jsmith',
                                     source='alt',
                                     uuid=self.jsmith.uuid)
        self.jsm3 = api.add_identity(self.ctx,
                                     email='jsmith@example.com',
                                     source='alt',
                                     uuid=self.jsmith.uuid)

        # Individual 3
        self.jane_rae = api.add_identity(self.ctx,
                                         name='Janer Rae',
                                         source='mls')
        self.jr2 = api.add_identity(self.ctx,
                                    email='jane.rae@example.net',
                                    name='Jane Rae Doe',
                                    source='mls',
                                    uuid=self.jane_rae.uuid)

        # Individual 4
        self.js_alt = api.add_identity(self.ctx,
                                       name='J. Smith',
                                       username='john_smith',
                                       source='scm')
        self.js_alt2 = api.add_identity(self.ctx,
                                        email='JSmith@example.com',
                                        username='john_smith',
                                        source='mls',
                                        uuid=self.js_alt.uuid)
        self.js_alt3 = api.add_identity(self.ctx,
                                        username='Smith. J',
                                        source='mls',
                                        uuid=self.js_alt.uuid)
        self.js_alt4 = api.add_identity(self.ctx,
                                        email='JSmith@example.com',
                                        name='Smith. J',
                                        source='mls',
                                        uuid=self.js_alt.uuid)

        # Individual 5
        self.jrae = api.add_identity(self.ctx,
                                     email='jrae@example.net',
                                     name='Jane Rae Doe',
                                     source='mls')
        self.jrae2 = api.add_identity(self.ctx,
                                      name='jrae',
                                      source='mls',
                                      uuid=self.jrae.uuid)
        self.jrae3 = api.add_identity(self.ctx,
                                      name='jrae',
                                      source='scm',
                                      uuid=self.jrae.uuid)

    def test_unify(self):
        """Check if unify is applied for the specified individuals"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': [self.jsmith.uuid,
                        self.jrae.uuid],
            'errors': []
        }

        source_uuids = [self.john_smith.uuid, self.jrae3.uuid, self.jr2.uuid]
        target_uuids = [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                        self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                        self.jane_rae.uuid, self.jr2.uuid,
                        self.js_alt.uuid, self.js_alt2.uuid,
                        self.js_alt3.uuid, self.js_alt4.uuid,
                        self.jrae.uuid, self.jrae2.uuid, self.jrae3.uuid]

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        job = unify.delay(ctx,
                          criteria,
                          source_uuids,
                          target_uuids)

        result = job.result

        self.assertDictEqual(result, expected)

        # Checking if the identities have been merged
        # Individual 1
        individual_1 = Individual.objects.get(mk=self.jsmith.uuid)
        identities = individual_1.identities.all()
        self.assertEqual(len(identities), 6)

        id1 = identities[0]
        self.assertEqual(id1, self.jsm2)

        id2 = identities[1]
        self.assertEqual(id2, self.jsmith)

        id3 = identities[2]
        self.assertEqual(id3, self.jsm3)

        id4 = identities[3]
        self.assertEqual(id4, self.john_smith)

        id5 = identities[4]
        self.assertEqual(id5, self.js2)

        id6 = identities[5]
        self.assertEqual(id6, self.js3)

        # Individual 2
        individual_2 = Individual.objects.get(mk=self.jrae.uuid)
        identities = individual_2.identities.all()
        self.assertEqual(len(identities), 5)

        id1 = identities[0]
        self.assertEqual(id1, self.jrae2)

        id2 = identities[1]
        self.assertEqual(id2, self.jrae3)

        id3 = identities[2]
        self.assertEqual(id3, self.jrae)

        id4 = identities[3]
        self.assertEqual(id4, self.jane_rae)

        id5 = identities[4]
        self.assertEqual(id5, self.jr2)

    def test_unify_all_individuals(self):
        """Check if unify is applied for all individuals when no uuids are provided"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': [self.js_alt.uuid,
                        self.jrae.uuid],
            'errors': []
        }

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        job = unify.delay(ctx,
                          criteria,
                          None,
                          None)

        result = job.result
        self.assertDictEqual(result, expected)

        # Checking if the identities have been merged
        individual_1 = Individual.objects.get(mk=self.js_alt.uuid)
        identities = individual_1.identities.all()
        self.assertEqual(len(identities), 10)

        individual_2 = Individual.objects.get(mk=self.jrae.uuid)
        identities = individual_2.identities.all()
        self.assertEqual(len(identities), 5)

    def test_unify_match_source(self):
        """Check if unify is applied when the identities share the source"""

        jr3 = api.add_identity(self.ctx,
                               name='J. Rae',
                               username='jane_rae',
                               source='github',
                               uuid=self.jane_rae.uuid)
        jrae_github = api.add_identity(self.ctx,
                                       name='Jane Rae',
                                       username='jane_rae',
                                       source='github')

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': [jrae_github.uuid, self.jsmith.uuid],
            'errors': []
        }

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        job = unify.delay(ctx,
                          criteria,
                          None,
                          None,
                          match_source=True)

        result = job.result
        self.assertDictEqual(result, expected)

        # Checking if the identities have been merged

        individual = Individual.objects.get(mk=jrae_github.uuid)
        identities = individual.identities.all()
        self.assertEqual(len(identities), 7)

        individual = Individual.objects.get(mk=self.jsmith.uuid)
        identities = individual.identities.all()
        self.assertEqual(len(identities), 6)

    def test_unify_github_email(self):
        """Check if unify is applied when a GitHub email matches a username"""

        jr_github = api.add_identity(self.ctx,
                                     name='Jane Rae',
                                     username='jane_rae',
                                     source='github')
        jr1 = api.add_identity(self.ctx,
                               email='32474881+jane_rae@users.noreply.github.com',
                               source='mls')
        jr2 = api.add_identity(self.ctx,
                               email='jane_rae@users.noreply.github.com',
                               source='scm')
        api.add_identity(self.ctx,
                         email='jsmith@users.noreply.github.com',
                         source='scm')
        api.add_identity(self.ctx,
                         email='2474881+jsmith@users.noreply.github.com',
                         source='mls')
        api.add_identity(self.ctx,
                         email='2474881@users.noreply.github.com',
                         source='mls')
        api.add_identity(self.ctx,
                         email='@users.noreply.github.com',
                         source='scm')

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': [jr_github.uuid],
            'errors': []
        }

        source_uuids = [jr_github.uuid]

        criteria = ['email', 'name', 'username']

        job = unify.delay(ctx,
                          criteria,
                          source_uuids,
                          None,
                          guess_github_user=True)

        result = job.result
        self.assertDictEqual(result, expected)

        # Checking if the identities have been merged

        individual = Individual.objects.get(mk=jr_github.uuid)
        identities = individual.identities.all()
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1, jr_github)

        id2 = identities[1]
        self.assertEqual(id2, jr2)

        id3 = identities[2]
        self.assertEqual(id3, jr1)

    def test_unify_github_email_match_source(self):
        """Check if unify is applied when a GitHub email matches a username with source matching enabled"""

        jr_github = api.add_identity(self.ctx,
                                     name='Jane Rae',
                                     username='jane_rae',
                                     source='github')
        jr1 = api.add_identity(self.ctx,
                               email='32474881+jane_rae@users.noreply.github.com',
                               source='mls')
        jr2 = api.add_identity(self.ctx,
                               email='jane_rae@users.noreply.github.com',
                               source='scm')

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': [jr_github.uuid],
            'errors': []
        }

        source_uuids = [jr_github.uuid]

        criteria = ['email', 'name', 'username']

        job = unify.delay(ctx,
                          criteria,
                          source_uuids,
                          None,
                          match_source=True,
                          guess_github_user=True)

        result = job.result
        self.assertDictEqual(result, expected)

        # Checking if the identities have been merged

        individual = Individual.objects.get(mk=jr_github.uuid)
        identities = individual.identities.all()
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1, jr_github)

        id2 = identities[1]
        self.assertEqual(id2, jr2)

        id3 = identities[2]
        self.assertEqual(id3, jr1)

    def test_unify_last_modified(self):
        """Check if unify is applied only for individuals updated after a given date"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': [self.js_alt.uuid],
            'errors': []
        }

        criteria = ['email', 'name', 'username']

        timestamp = datetime_utcnow()

        api.add_identity(self.ctx,
                         username='john_smith',
                         source='mls',
                         uuid=self.js_alt.uuid)

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        job = unify.delay(ctx,
                          criteria,
                          None,
                          None,
                          exclude=False,
                          last_modified=timestamp)

        result = job.result
        self.assertDictEqual(result, expected)

        # Checking if the identities have been merged
        individual_1 = Individual.objects.get(mk=self.js_alt.uuid)
        identities = individual_1.identities.all()
        self.assertEqual(len(identities), 8)

    def test_unify_source_not_mk(self):
        """Check if unify works when the provided uuid is not an Individual's main key"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': [
                self.js_alt.uuid
            ],
            'errors': []
        }

        source_uuids = [self.js_alt3.uuid]
        target_uuids = [self.jsmith.uuid]
        criteria = ['email', 'name', 'username']

        job = unify.delay(ctx,
                          criteria,
                          source_uuids,
                          target_uuids)
        result = job.result

        self.assertDictEqual(result, expected)

        # Checking if the identities have been merged
        individual = Individual.objects.get(mk=self.js_alt.uuid)
        identities = individual.identities.all()
        self.assertEqual(len(identities), 7)

        id1 = identities[0]
        self.assertEqual(id1, self.jsm2)

        id2 = identities[1]
        self.assertEqual(id2, self.js_alt)

        id3 = identities[2]
        self.assertEqual(id3, self.js_alt4)

        id4 = identities[3]
        self.assertEqual(id4, self.js_alt3)

        id5 = identities[4]
        self.assertEqual(id5, self.jsmith)

        id6 = identities[5]
        self.assertEqual(id6, self.jsm3)

        id7 = identities[6]
        self.assertEqual(id7, self.js_alt2)

    def test_unify_empty_target(self):
        """Check if unify is applied for the given individuals against the whole registry"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': [
                self.jsmith.uuid
            ],
            'errors': []
        }

        source_uuids = [self.john_smith.uuid]
        target_uuids = None
        criteria = ['email', 'name']

        job = unify.delay(ctx,
                          criteria,
                          source_uuids,
                          target_uuids,)

        result = job.result

        self.assertDictEqual(result, expected)

        # Checking if the identities have been merged
        individual = Individual.objects.get(mk=self.jsmith.uuid)
        identities = individual.identities.all()
        self.assertEqual(len(identities), 6)

        id1 = identities[0]
        self.assertEqual(id1, self.jsm2)

        id2 = identities[1]
        self.assertEqual(id2, self.jsmith)

        id3 = identities[2]
        self.assertEqual(id3, self.jsm3)

        id4 = identities[3]
        self.assertEqual(id4, self.john_smith)

        id5 = identities[4]
        self.assertEqual(id5, self.js2)

        id6 = identities[5]
        self.assertEqual(id6, self.js3)

    def test_no_matches_found(self):
        """Check whether it returns no results when there is no matches for the input identity"""

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': [],
            'errors': []
        }

        source_uuids = [self.john_smith.uuid]
        target_uuids = [self.jrae.uuid]
        criteria = ['email', 'name']

        job = unify.delay(ctx,
                          criteria,
                          source_uuids,
                          target_uuids)

        result = job.result

        self.assertDictEqual(result, expected)

    @unittest.mock.patch('sortinghat.core.api.find_individual_by_uuid')
    def test_not_found_uuid_error(self, mock_find_indv):
        """Check if the unify process returns no results when an individual is not found"""

        exc = NotFoundError(entity='1234567890abcdefg')
        mock_find_indv.side_effect = exc

        ctx = SortingHatContext(self.user)

        # Test
        expected = {
            'results': [],
            'errors': []
        }

        source_uuids = ['1234567890abcdefg']
        target_uuids = [self.john_smith.uuid]
        criteria = ['email', 'name']

        job = unify.delay(ctx,
                          criteria,
                          source_uuids,
                          target_uuids)
        result = job.result

        self.assertDictEqual(result, expected)

    def test_transactions(self):
        """Check if the right transactions were created"""

        timestamp = datetime_utcnow()

        ctx = SortingHatContext(self.user)

        source_uuids = [self.john_smith.uuid]
        target_uuids = [self.jsmith.uuid]
        criteria = ['email', 'name']

        # Identities which don't have the fields in `criteria` or no matches won't be returned
        unify.delay(ctx,
                    criteria,
                    source_uuids,
                    target_uuids,
                    job_id='ABCD-EF12-3456-7890')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 2)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'unify-ABCD-EF12-3456-7890')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, ctx.user.username)

        trx = transactions[1]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'merge-ABCD-EF12-3456-7890')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, ctx.user.username)


def setup_genderize_server():
    """Setup a mock HTTP server for genderize.io"""

    http_requests = []

    def request_callback(method, uri, headers):
        last_request = httpretty.last_request()
        http_requests.append(last_request)

        params = last_request.querystring
        name = params['name'][0].lower()

        if name == 'error':
            return 502, headers, 'Bad Gateway'

        if name == 'john':
            data = {
                'gender': 'male',
                'probability': 0.92
            }
        elif name == 'jane':
            data = {
                'gender': 'female',
                'probability': 0.89
            }
        else:
            data = {
                'gender': None,
                'probability': None
            }

        body = json.dumps(data)

        return (200, headers, body)

    httpretty.register_uri(httpretty.GET,
                           "https://api.genderize.io/",
                           responses=[
                               httpretty.Response(body=request_callback)
                           ])

    return http_requests


class TestRecommendGender(TestCase):
    """Unit tests for recommend_gender"""

    def setUp(self):
        """Initialize database with a dataset"""

        self.user = get_user_model().objects.create(username='test')
        ctx = SortingHatContext(self.user)

        self.jsmith = api.add_identity(ctx,
                                       source='scm',
                                       name='John Smith')

        self.jdoe = api.add_identity(ctx,
                                     source='scm',
                                     name='Jane Doe')

    @httpretty.activate
    def test_recommend_gender(self):
        """Check if recommendations are obtained for the specified individuals"""

        ctx = SortingHatContext(self.user)

        expected = {
            'results': {
                self.jsmith.uuid: {
                    'gender': 'male',
                    'accuracy': 92
                },
                self.jdoe.uuid: {
                    'gender': 'female',
                    'accuracy': 89
                }
            }
        }

        setup_genderize_server()

        uuids = [self.jsmith.uuid, self.jdoe.uuid]
        job = recommend_gender.delay(ctx, uuids)
        # Preserve job results order for the comparison against the expected results
        result = job.result

        self.assertDictEqual(result, expected)

        recommendations = GenderRecommendation.objects.all()
        for recommendation in recommendations:
            self.assertEqual(recommendation.gender, expected['results'][recommendation.individual.mk]['gender'])
            self.assertEqual(recommendation.accuracy, expected['results'][recommendation.individual.mk]['accuracy'])

    @httpretty.activate
    def test_transactions(self):
        """Check if the right transactions were created"""

        timestamp = datetime_utcnow()

        ctx = SortingHatContext(self.user)

        setup_genderize_server()

        uuids = [self.jsmith.uuid, self.jdoe.uuid]
        recommend_gender.delay(ctx,
                               uuids,
                               job_id='ABCD-EF12-3456-7890')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'recommend_gender-ABCD-EF12-3456-7890')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, ctx.user.username)


class TestGenderize(TestCase):
    """Unit tests for genderize"""

    def setUp(self):
        """Initialize database with a dataset"""

        self.user = get_user_model().objects.create(username='test')
        ctx = SortingHatContext(self.user)

        self.jsmith = api.add_identity(ctx,
                                       source='scm',
                                       name='John Smith')

        self.jdoe = api.add_identity(ctx,
                                     source='scm',
                                     name='Jane Doe')

    @httpretty.activate
    def test_genderize(self):
        """Check if genderize is applied for the specified individuals"""

        ctx = SortingHatContext(self.user)

        expected = {
            'results': {
                self.jsmith.uuid: ('male', 92)
            },
            'errors': []
        }

        setup_genderize_server()

        uuids = [self.jsmith.uuid]
        job = genderize.delay(ctx, uuids)
        # Preserve job results order for the comparison against the expected results
        result = job.result

        self.assertDictEqual(result, expected)

        individual = Individual.objects.get(mk=self.jsmith.uuid)
        gender = individual.profile.gender
        accuracy = individual.profile.gender_acc
        self.assertEqual(gender, 'male')
        self.assertEqual(accuracy, 92)

    @httpretty.activate
    def test_genderize_all(self):
        """Check if genderize is applied for all individuals in the registry"""

        ctx = SortingHatContext(self.user)

        expected = {
            'results': {
                self.jsmith.uuid: ('male', 92),
                self.jdoe.uuid: ('female', 89)
            },
            'errors': []
        }

        setup_genderize_server()

        job = genderize.delay(ctx)
        result = job.result

        self.assertDictEqual(result, expected)

        individual_1 = Individual.objects.get(mk=self.jsmith.uuid)
        gender_1 = individual_1.profile.gender
        self.assertEqual(gender_1, 'male')

        individual_2 = Individual.objects.get(mk=self.jdoe.uuid)
        gender_2 = individual_2.profile.gender
        self.assertEqual(gender_2, 'female')


class MockTestImporter(IdentitiesImporter):
    NAME = 'test_backend'

    def __init__(self, ctx, url, token=None):
        super().__init__(ctx, url)
        self.token = token

    def get_individuals(self):
        from sortinghat.core.importer.models import Individual, Identity
        indiv = Individual()
        indiv.identities.append(Identity(source='test_backend', username='test_user'))
        return [indiv]


class TestImportIdentities(TestCase):
    """Unit tests for import_identities"""

    def setUp(self):
        """Initialize database"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

    @unittest.mock.patch('sortinghat.core.importer.backend.find_backends')
    def test_import_identities(self, mock_find_backends):
        """Check if the importer is executed correctly"""

        mock_find_backends.return_value = {'test_backend': MockTestImporter}

        # Test
        ctx = SortingHatContext(self.user)

        job = import_identities.delay(ctx, 'test_backend', 'my_url')
        result = job.result

        self.assertEqual(result, 1)

        # Check individual and identity are inserted
        indiv = Individual.objects.first()
        identity = indiv.identities.first()
        self.assertEqual(identity.source, 'test_backend')
        self.assertEqual(identity.username, 'test_user')

    @unittest.mock.patch('sortinghat.core.importer.backend.find_backends')
    def test_backend_not_found(self, mock_find_backends):
        """Check if the importer is executed correctly"""

        mock_find_backends.return_value = {}

        # Test
        ctx = SortingHatContext(self.user)

        job = import_identities.delay(ctx, 'test_backend', 'my_url')
        self.assertEqual(job.is_failed, True)

    @unittest.mock.patch('sortinghat.core.importer.backend.find_backends')
    def test_transactions(self, mock_find_backends):
        """Check if the right transactions were created"""

        mock_find_backends.return_value = {'test_backend': MockTestImporter}

        timestamp = datetime_utcnow()

        ctx = SortingHatContext(self.user)

        import_identities.delay(ctx, 'test_backend', 'my_url',
                                job_id='ABCD-EF12-3456-7890')

        transactions = Transaction.objects.filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 2)

        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'import_identities-ABCD-EF12-3456-7890')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, ctx.user.username)
        trx = transactions[1]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'add_identity-ABCD-EF12-3456-7890')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, ctx.user.username)
