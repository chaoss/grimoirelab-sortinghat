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

    def test_recommend_matches(self):
        """Check if recommendations are obtained for the specified individuals"""

        # Test
        expected = {
            self.john_smith.uuid: sorted([self.jsmith.uuid]),
            self.jrae3.uuid: sorted([self.jrae.uuid,
                                     self.jane_rae.uuid]),
            self.jr2.uuid: sorted([self.jrae.uuid,
                                   self.jane_rae.uuid])
        }

        source_uuids = [self.john_smith.uuid, self.jrae3.uuid, self.jr2.uuid]
        target_uuids = [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                        self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                        self.jane_rae.uuid, self.jr2.uuid,
                        self.js_alt.uuid, self.js_alt2.uuid,
                        self.js_alt3.uuid, self.js_alt4.uuid,
                        self.jrae.uuid, self.jrae2.uuid, self.jrae3.uuid]

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` won't be returned
        recs = dict(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria))

        # Preserve results order for the comparison against the expected results
        result = {}
        for key in recs:
            result[key] = sorted(recs[key])

        self.assertEqual(len(result), 3)
        self.assertDictEqual(result, expected)

    def test_recommend_matches_exclude(self):
        """Check if recommendations are obtained for the specified individuals
        activating exclude"""

        # Test
        expected = {
            self.john_smith.uuid: [],
            self.jrae3.uuid: sorted([self.jrae.uuid,
                                     self.jane_rae.uuid]),
            self.jr2.uuid: sorted([self.jrae.uuid,
                                   self.jane_rae.uuid])
        }

        source_uuids = [self.john_smith.uuid, self.jrae3.uuid, self.jr2.uuid]
        target_uuids = [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                        self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                        self.jane_rae.uuid, self.jr2.uuid,
                        self.js_alt.uuid, self.js_alt2.uuid,
                        self.js_alt3.uuid, self.js_alt4.uuid,
                        self.jrae.uuid, self.jrae2.uuid, self.jrae3.uuid]

        criteria = ['email', 'name', 'username']

        # Add 'jsmith@example.com' and 'jsmith' to RecommenderExclusionTerm
        add_recommender_exclusion_term(self.ctx, "jsmith@example.com")
        add_recommender_exclusion_term(self.ctx, "jsmith")

        # Identities which don't have the fields in `criteria` won't be returned
        recs = dict(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria,
                                      exclude=True))

        # Preserve results order for the comparison against the expected results
        result = {}
        for key in recs:
            result[key] = sorted(recs[key])

        self.assertEqual(len(result), 3)
        self.assertDictEqual(result, expected)

    def test_recommend_matches_verbose(self):
        """Check if recommendations are obtained for the specified individuals, at identity level"""

        # Test
        expected = {
            self.john_smith.uuid: sorted([self.jsm2.uuid,
                                          self.jsm3.uuid,
                                          self.js2.uuid,
                                          self.js3.uuid]),
            self.jrae3.uuid: sorted([self.jrae2.uuid]),
            self.jr2.uuid: sorted([self.jrae.uuid])
        }

        source_uuids = [self.john_smith.uuid, self.jrae3.uuid, self.jr2.uuid]
        target_uuids = [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                        self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                        self.jane_rae.uuid, self.jr2.uuid,
                        self.js_alt.uuid, self.js_alt2.uuid, self.js_alt3.uuid, self.js_alt4.uuid,
                        self.jrae.uuid, self.jrae2.uuid, self.jrae3.uuid]

        criteria = ['email', 'name', 'username']

        # Identities which don't have the fields in `criteria` won't be returned
        recs = dict(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria,
                                      verbose=True))
        # Preserve results order for the comparison against the expected results
        result = {}
        for key in recs:
            result[key] = sorted(recs[key])

        self.assertEqual(len(result), 3)
        self.assertDictEqual(result, expected)

    def test_recommend_source_not_mk(self):
        """Check if recommendations work when the provided uuid is not an Individual's main key"""

        # Test
        expected = {
            self.js3.uuid: [self.jsmith.uuid]
        }

        source_uuids = [self.js3.uuid]
        target_uuids = [self.jsm3.uuid]
        criteria = ['email', 'name', 'username']

        recs = dict(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria))

        # Preserve same format as in other tests.
        # 1-element result is returned as {key: {result}} instead of {key: [result]}
        result = {}
        for key in recs:
            result[key] = list(recs[key])

        self.assertEqual(len(recs), 1)
        self.assertDictEqual(result, expected)

    def test_no_matches_found(self):
        """Check whether it returns an empty result when there is no matches for the input identity"""

        # Test
        expected = {'880b3dfcb3a08712e5831bddc3dfe81fc5d7b331': []}

        source_uuids = [self.john_smith.uuid]
        target_uuids = [self.jrae.uuid]
        criteria = ['email', 'name']

        recs = dict(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria))

        self.assertDictEqual(recs, expected)

    def test_not_found_uuid_error(self):
        """Check if the recommendation process returns no results when an individual is not found"""

        # Test
        expected = {'1234567890abcdefg': []}

        source_uuids = ['1234567890abcdefg']
        target_uuids = [self.john_smith.uuid]
        criteria = ['email', 'name']

        recs = dict(recommend_matches(source_uuids,
                                      target_uuids,
                                      criteria))

        self.assertDictEqual(recs, expected)
