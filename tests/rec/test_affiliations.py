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

from django.contrib.auth import get_user_model
from django.test import TestCase

from sortinghat.core import api
from sortinghat.core.context import SortingHatContext
from sortinghat.core.recommendations.affiliation import recommend_affiliations


class TestRecommendAffiliations(TestCase):
    """Unit tests for recommend_affiliations"""

    def setUp(self):
        """Initialize database with a set of organizations and domains"""

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

    def test_recommendations(self):
        """Test if a set of recommendations is produced"""

        # Add some cases
        ctx = SortingHatContext(self.user)

        # John Smith identity
        jsmith = api.add_identity(ctx,
                                  source='scm',
                                  email='jsmith@us.example.com',
                                  name='John Smith',
                                  username='jsmith')
        api.add_identity(ctx,
                         source='scm',
                         email='jsmith@example.net',
                         name='John Smith',
                         uuid=jsmith.uuid)
        api.add_identity(ctx,
                         source='scm',
                         email='jsmith@bitergia.com',
                         name='John Smith',
                         username='jsmith',
                         uuid=jsmith.uuid)
        api.enroll(ctx, jsmith.uuid, 'Bitergia')

        # Jane Roe identity
        jroe = api.add_identity(ctx,
                                source='scm',
                                email='jroe@example.com',
                                name='Jane Roe',
                                username='jroe')
        api.add_identity(ctx,
                         source='scm',
                         email='jroe@example.com',
                         uuid=jroe.uuid)
        api.add_identity(ctx,
                         source='unknown',
                         email='jroe@bitergia.com',
                         uuid=jroe.uuid)

        # Test
        uuids = [jsmith.uuid, jroe.uuid]
        recs = list(recommend_affiliations(uuids))

        self.assertEqual(len(recs), 2)

        rec = recs[0]
        self.assertEqual(rec[0], jsmith.uuid)
        self.assertListEqual(rec[1], ['Example'])

        rec = recs[1]
        self.assertEqual(rec[0], jroe.uuid)
        self.assertListEqual(rec[1], ['Bitergia', 'Example'])

    def test_already_enrolled(self):
        """Check if an organization is not included in the recommendation
        when the individual is already enrolled to it"""

        ctx = SortingHatContext(self.user)

        jsmith = api.add_identity(ctx,
                                  source='scm',
                                  email='jsmith@example.com',
                                  name='John Smith')
        api.add_identity(ctx,
                         source='scm',
                         email='jsmith@bitergia.com',
                         name='John Smith',
                         username='jsmith',
                         uuid=jsmith.uuid)
        api.enroll(ctx, jsmith.uuid, 'Bitergia')

        # Test
        recs = list(recommend_affiliations([jsmith.uuid]))

        self.assertEqual(len(recs), 1)

        rec = recs[0]
        self.assertEqual(rec[0], jsmith.uuid)
        # Bitergia is not included
        self.assertListEqual(rec[1], ['Example'])

    def test_multiple_top_domains(self):
        """Check if it chooses the right domain when multiple top
        domains are available"""

        ctx = SortingHatContext(self.user)

        jdoe = api.add_identity(ctx, source='scm',
                                email='janedoe@it.u.example.com')

        # Test
        recs = list(recommend_affiliations([jdoe.uuid]))

        self.assertEqual(len(recs), 1)

        rec = recs[0]
        self.assertEqual(rec[0], jdoe.uuid)
        self.assertListEqual(rec[1], ['Example Int.'])

    def test_no_match(self):
        """Check if empty recommendations are returned when there is
        not match for a domain"""

        ctx = SortingHatContext(self.user)

        jsmith = api.add_identity(ctx,
                                  source='scm',
                                  email='jsmith@example.org',
                                  name='John Smith',
                                  username='jsmith')

        # Test
        recs = list(recommend_affiliations([jsmith.uuid]))

        self.assertEqual(len(recs), 1)

        rec = recs[0]
        self.assertEqual(rec[0], jsmith.uuid)
        self.assertListEqual(rec[1], [])

    def test_invalid_identity_email(self):
        """Check if empty recommendations are returned for invalid emails"""

        ctx = SortingHatContext(self.user)

        noemail = api.add_identity(ctx,
                                   source='unknown',
                                   email='novalidemail@')

        # Test
        recs = list(recommend_affiliations([noemail.uuid]))

        self.assertEqual(len(recs), 1)

        rec = recs[0]
        self.assertEqual(rec[0], noemail.uuid)
        self.assertListEqual(rec[1], [])

    def test_empty_email(self):
        """Check if empty recommendations are returned for empty
        email addresses"""

        ctx = SortingHatContext(self.user)

        jdoe = api.add_identity(ctx,
                                source='unknown',
                                name='John Doe',
                                username='jdoe')

        # Test
        recs = list(recommend_affiliations([jdoe.uuid]))

        self.assertEqual(len(recs), 1)

        rec = recs[0]
        self.assertEqual(rec[0], jdoe.uuid)
        self.assertListEqual(rec[1], [])

    def test_not_found_individual(self):
        """Check if no recommendations are generated when an
        individual does not exist"""

        # Test
        recs = list(recommend_affiliations('FFFFFFFFFFFFFFFFFF'))

        self.assertListEqual(recs, [])
