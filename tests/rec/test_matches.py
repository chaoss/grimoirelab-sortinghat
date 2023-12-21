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

from django.contrib.auth import get_user_model
from django.test import TestCase

from grimoirelab_toolkit.datetime import datetime_utcnow

from sortinghat.core import api
from sortinghat.core.context import SortingHatContext
from sortinghat.core.recommendations.matching import recommend_matches
from sortinghat.core.recommendations.exclusion import add_recommender_exclusion_term


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

    def test_recommend_matches(self):
        """Check if recommendations are obtained for the specified individuals"""

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

        # Identities which don't have the fields in `criteria` won't be returned
        recs = list(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria))

        self.assertEqual(len(recs), 3)

        rec = recs[0]
        self.assertEqual(rec[0], self.john_smith.uuid)
        self.assertEqual(rec[1], self.john_smith.individual.mk)
        self.assertEqual(rec[2], sorted([self.jsmith.individual.mk]))

        rec = recs[1]
        self.assertEqual(rec[0], self.jrae_no_name.uuid)
        self.assertEqual(rec[1], self.jrae_no_name.individual.mk)
        self.assertEqual(rec[2], [])

        rec = recs[2]
        self.assertEqual(rec[0], self.jr2.uuid)
        self.assertEqual(rec[1], self.jr2.individual.mk)
        self.assertEqual(rec[2], sorted([self.jrae.individual.mk]))

    def test_recommend_matches_no_strict(self):
        """Check if recommendations are obtained for the specified individuals when
        'strict' is disabled"""

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

        recs = list(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria,
                                      strict=False))

        self.assertEqual(len(recs), 3)

        rec = recs[0]
        self.assertEqual(rec[0], self.john_smith.uuid)
        self.assertEqual(rec[1], self.john_smith.individual.mk)
        self.assertEqual(rec[2], sorted([self.jsmith.individual.mk,
                                         self.jsmith_no_email.individual.mk]))

        rec = recs[1]
        self.assertEqual(rec[0], self.jrae_no_name.uuid)
        self.assertEqual(rec[1], self.jrae_no_name.individual.mk)
        self.assertEqual(rec[2], sorted([self.jrae2.individual.mk]))

        rec = recs[2]
        self.assertEqual(rec[0], self.jr2.uuid)
        self.assertEqual(rec[1], self.jr2.individual.mk)
        self.assertEqual(rec[2], sorted([self.jrae.individual.mk]))

    def test_recommend_matches_exclude(self):
        """Check if recommendations are obtained for the specified individuals
        activating exclude"""

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

        # Add 'jsmith@example.com' and 'jsmith' to RecommenderExclusionTerm
        add_recommender_exclusion_term(self.ctx, "jsmith@example.com")
        add_recommender_exclusion_term(self.ctx, "jsmith")

        # Identities which don't have the fields in `criteria` won't be returned
        recs = list(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria,
                                      exclude=True))

        self.assertEqual(len(recs), 3)

        rec = recs[0]
        self.assertEqual(rec[0], self.john_smith.uuid)
        self.assertEqual(rec[1], self.john_smith.individual.mk)
        self.assertEqual(rec[2], [])

        rec = recs[1]
        self.assertEqual(rec[0], self.jrae_no_name.uuid)
        self.assertEqual(rec[1], self.jrae_no_name.individual.mk)
        self.assertEqual(rec[2], [])

        rec = recs[2]
        self.assertEqual(rec[0], self.jr2.uuid)
        self.assertEqual(rec[1], self.jr2.individual.mk)
        self.assertEqual(rec[2], [self.jrae.individual.mk])

    def test_recommend_matches_last_modified(self):
        """Check if recommendations are obtained for individuals modified after a date"""

        timestamp = datetime_utcnow()

        api.add_identity(self.ctx,
                         username='john_smith',
                         source='mls',
                         uuid=self.js_alt.uuid)

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` won't be returned
        recs = list(recommend_matches(None,
                                      None,
                                      criteria,
                                      last_modified=timestamp))

        self.assertEqual(len(recs), 1)

        rec = recs[0]
        self.assertEqual(rec[0], self.js_alt.uuid)
        self.assertEqual(rec[1], self.js_alt.individual.mk)
        self.assertEqual(rec[2], [self.jsmith.individual.mk])

    def test_recommend_matches_verbose(self):
        """Check if recommendations are obtained for the specified individuals, at identity level"""

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

        # Identities which don't have the fields in `criteria` won't be returned
        recs = list(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria,
                                      verbose=True))

        self.assertEqual(len(recs), 3)

        rec = recs[0]
        self.assertEqual(rec[0], self.john_smith.uuid)
        self.assertEqual(rec[1], self.john_smith.individual.mk)
        self.assertEqual(rec[2], sorted([self.jsm2.uuid,
                                         self.jsm3.uuid,
                                         self.js2.uuid]))

        rec = recs[1]
        self.assertEqual(rec[0], self.jrae_no_name.uuid)
        self.assertEqual(rec[1], self.jrae_no_name.individual.mk)
        self.assertEqual(rec[2], [])

        rec = recs[2]
        self.assertEqual(rec[0], self.jr2.uuid)
        self.assertEqual(rec[1], self.jr2.individual.mk)
        self.assertEqual(rec[2], [self.jrae.uuid])

    def test_recommend_matches_verbose_no_strict(self):
        """Check if recommendations are obtained for the specified individuals,
        at identity level, when 'strict' is disabled"""

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

        # Identities which don't have the fields in `criteria` won't be returned
        recs = list(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria,
                                      verbose=True,
                                      strict=False))

        self.assertEqual(len(recs), 3)

        rec = recs[0]
        self.assertEqual(rec[0], self.john_smith.uuid)
        self.assertEqual(rec[1], self.john_smith.individual.mk)
        self.assertEqual(rec[2], sorted([self.jsm2.uuid,
                                         self.jsm3.uuid,
                                         self.js2.uuid]))

        rec = recs[1]
        self.assertEqual(rec[0], self.jrae_no_name.uuid)
        self.assertEqual(rec[1], self.jrae_no_name.individual.mk)
        self.assertEqual(rec[2], [self.jrae2.uuid])

        rec = recs[2]
        self.assertEqual(rec[0], self.jr2.uuid)
        self.assertEqual(rec[1], self.jr2.individual.mk)
        self.assertEqual(rec[2], [self.jrae.uuid])

    def test_recommend_source_not_mk(self):
        """Check if recommendations work when the provided uuid is not an Individual's main key"""

        source_uuids = [self.js3.uuid]
        target_uuids = [self.jsm3.uuid]
        criteria = ['email', 'name', 'username']

        recs = list(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria))

        self.assertEqual(len(recs), 1)

        rec = recs[0]
        self.assertEqual(rec[0], self.js3.uuid)
        self.assertEqual(rec[1], self.js3.individual.mk)
        self.assertEqual(rec[2], [self.jsmith.individual.mk])

    def test_no_matches_found(self):
        """Check whether it returns an empty result when there is no matches for the input identity"""

        source_uuids = [self.john_smith.uuid]
        target_uuids = [self.jrae.uuid]
        criteria = ['email', 'name']

        recs = list(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria))

        self.assertEqual(len(recs), 1)

        rec = recs[0]
        self.assertEqual(rec[0], self.john_smith.uuid)
        self.assertEqual(rec[1], self.john_smith.individual.mk)
        self.assertEqual(rec[2], [])

    def test_not_found_uuid_error(self):
        """Check if the recommendation process returns no results when an individual is not found"""

        source_uuids = ['1234567890abcdefg']
        target_uuids = [self.john_smith.uuid]
        criteria = ['email', 'name']

        recs = list(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria))

        self.assertEqual(len(recs), 1)

        rec = recs[0]
        self.assertEqual(rec[0], '1234567890abcdefg')
        self.assertEqual(rec[1], '1234567890abcdefg')
        self.assertEqual(rec[2], [])

    def test_recommend_match_source(self):
        """Test if recommendations are created between same identities with same source"""

        jr3 = api.add_identity(self.ctx,
                               name='J. Rae',
                               username='jane_rae',
                               source='github',
                               uuid=self.jane_rae.uuid)
        jrae_github = api.add_identity(self.ctx,
                                       name='Jane Rae',
                                       username='jane_rae',
                                       source='github')

        source_uuids = [self.john_smith.uuid, self.jrae_no_name.uuid, self.jr2.uuid]
        target_uuids = [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                        self.js4.uuid,
                        self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                        self.jane_rae.uuid, self.jr2.uuid,
                        self.js_alt.uuid, self.js_alt2.uuid,
                        self.js_alt3.uuid, self.js_alt4.uuid,
                        self.jrae.uuid, self.jrae2.uuid,
                        self.jrae_no_name.uuid, self.jsmith_no_email.uuid,
                        jrae_github]

        criteria = ['email', 'name', 'username']

        # Recommend identities which match the fields in `criteria` for the same `source`
        recs = list(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria,
                                      match_source=True))

        self.assertEqual(len(recs), 3)

        rec = recs[0]
        self.assertEqual(rec[0], self.john_smith.uuid)
        self.assertEqual(rec[1], self.john_smith.individual.mk)
        self.assertEqual(rec[2], [])

        rec = recs[1]
        self.assertEqual(rec[0], self.jrae_no_name.uuid)
        self.assertEqual(rec[1], self.jrae_no_name.individual.mk)
        self.assertEqual(rec[2], [])

        rec = recs[2]
        self.assertEqual(rec[0], self.jr2.uuid)
        self.assertEqual(rec[1], self.jr2.individual.mk)
        self.assertEqual(rec[2], sorted([jrae_github.individual.mk]))

    def test_recommend_same_source_not_trusted(self):
        """Matches are not created for ids with same source but not github or gitlab"""

        jr3 = api.add_identity(self.ctx,
                               name='J. Rae',
                               username='jane_rae',
                               source='git',
                               uuid=self.jane_rae.uuid)
        jrae_git = api.add_identity(self.ctx,
                                    name='Jane Rae',
                                    username='jane_rae',
                                    source='git')

        source_uuids = [self.john_smith.uuid, self.jrae_no_name.uuid, self.jr2.uuid]
        target_uuids = [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                        self.js4.uuid,
                        self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                        self.jane_rae.uuid, self.jr2.uuid,
                        self.js_alt.uuid, self.js_alt2.uuid,
                        self.js_alt3.uuid, self.js_alt4.uuid,
                        self.jrae.uuid, self.jrae2.uuid,
                        self.jrae_no_name.uuid, self.jsmith_no_email.uuid,
                        jrae_git]

        criteria = ['email', 'name', 'username']

        # Recommend identities which match the fields in `criteria` for the same `source`
        recs = list(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria,
                                      match_source=True))

        self.assertEqual(len(recs), 3)

        rec = recs[0]
        self.assertEqual(rec[0], self.john_smith.uuid)
        self.assertEqual(rec[1], self.john_smith.individual.mk)
        self.assertEqual(rec[2], [])

        rec = recs[1]
        self.assertEqual(rec[0], self.jrae_no_name.uuid)
        self.assertEqual(rec[1], self.jrae_no_name.individual.mk)
        self.assertEqual(rec[2], [])

        rec = recs[2]
        self.assertEqual(rec[0], self.jr2.uuid)
        self.assertEqual(rec[1], self.jr2.individual.mk)
        self.assertEqual(rec[2], [])
