# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2021 Bitergia
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
#     Eva Millán <evamillan@bitergia.com>
#


import json
import httpretty

from django.contrib.auth import get_user_model
from django.test import TestCase

from sortinghat.core import api
from sortinghat.core.context import SortingHatContext
from sortinghat.core.recommendations.gender import recommend_gender
from sortinghat.core.recommendations.exclusion import add_recommender_exclusion_term

GENDERIZE_API_URL = "https://api.genderize.io/"


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
                           GENDERIZE_API_URL,
                           responses=[
                               httpretty.Response(body=request_callback)
                           ])

    return http_requests


class TestRecommendGender(TestCase):
    """Unit tests for recommend_gender"""

    def setUp(self):
        """Initialize database with a dataset"""

        self.user = get_user_model().objects.create(username='test')
        self.ctx = SortingHatContext(self.user)

        self.john_smith = api.add_identity(self.ctx,
                                           name='John Smith',
                                           source='scm')
        self.jane_doe = api.add_identity(self.ctx,
                                         name='Jane Doe',
                                         source='scm')
        self.john = api.add_identity(self.ctx,
                                     name='John',
                                     source='scm')
        self.no_name = api.add_identity(self.ctx,
                                        email='email@example.com',
                                        source='scm')
        self.double_space = api.add_identity(self.ctx,
                                             name='John  Smith',
                                             source='scm')
        self.initial = api.add_identity(self.ctx,
                                        name='J Smith',
                                        source='scm')

    @httpretty.activate
    def test_recommend_gender_strict(self):
        """Check if it returns a gender for strict valid names"""

        setup_genderize_server()

        uuids = [self.john_smith.uuid,
                 self.jane_doe.uuid,
                 self.double_space.uuid,
                 self.initial.uuid]
        recs = list(recommend_gender(uuids))

        self.assertEqual(len(recs), 3)

        rec = recs[0]
        self.assertEqual(rec[0], self.john_smith.uuid)
        gender, acc = rec[1]
        self.assertEqual(gender, 'male')
        self.assertEqual(acc, 92)

        rec = recs[1]
        self.assertEqual(rec[0], self.jane_doe.uuid)
        gender, acc = rec[1]
        self.assertEqual(gender, 'female')
        self.assertEqual(acc, 89)

        rec = recs[2]
        self.assertEqual(rec[0], self.double_space.uuid)
        gender, acc = rec[1]
        self.assertEqual(gender, 'male')
        self.assertEqual(acc, 92)

    @httpretty.activate
    def test_recommend_gender_exclude(self):
        """Check if it returns a gender for valid names
        activating exclude"""

        setup_genderize_server()

        # Add 'John Smith' to RecommenderExclusionTerm
        add_recommender_exclusion_term(self.ctx, "John Smith")

        uuids = [self.john_smith.uuid, self.jane_doe.uuid]
        recs = list(recommend_gender(uuids, exclude=True))

        self.assertEqual(len(recs), 1)

        rec = recs[0]
        self.assertEqual(rec[0], self.jane_doe.uuid)
        gender, acc = rec[1]
        self.assertEqual(gender, 'female')
        self.assertEqual(acc, 89)

    @httpretty.activate
    def test_recommend_gender_not_strict(self):
        """Check if it returns a gender for valid names"""

        setup_genderize_server()

        uuids = [self.john_smith.uuid,
                 self.jane_doe.uuid,
                 self.double_space.uuid,
                 self.john.uuid,
                 self.initial.uuid]
        recs = list(recommend_gender(uuids, no_strict_matching=True))

        self.assertEqual(len(recs), 4)

        rec = recs[0]
        self.assertEqual(rec[0], self.john_smith.uuid)
        gender, acc = rec[1]
        self.assertEqual(gender, 'male')
        self.assertEqual(acc, 92)

        rec = recs[1]
        self.assertEqual(rec[0], self.jane_doe.uuid)
        gender, acc = rec[1]
        self.assertEqual(gender, 'female')
        self.assertEqual(acc, 89)

        rec = recs[2]
        self.assertEqual(rec[0], self.double_space.uuid)
        gender, acc = rec[1]
        self.assertEqual(gender, 'male')
        self.assertEqual(acc, 92)

        rec = recs[3]
        self.assertEqual(rec[0], self.john.uuid)
        gender, acc = rec[1]
        self.assertEqual(gender, 'male')
        self.assertEqual(acc, 92)

    @httpretty.activate
    def test_invalid_name_strict(self):
        """Check if no recommendations are generated when an
            individual does not have a strict valid name"""

        setup_genderize_server()

        uuids = [self.john.uuid, self.no_name.uuid, self.initial.uuid]
        recs = list(recommend_gender(uuids))

        self.assertEqual(len(recs), 0)

    @httpretty.activate
    def test_invalid_name_not_strict(self):
        """Check if no recommendations are generated when an
            individual does not have a valid name"""

        setup_genderize_server()

        uuids = [self.no_name.uuid, self.initial.uuid]
        recs = list(recommend_gender(uuids, no_strict_matching=True))

        self.assertEqual(len(recs), 0)

    def test_not_found_individual(self):
        """Check if no recommendations are generated when an
        individual does not exist"""

        recs = list(recommend_gender(['FFFFFFFFFFFFFFFFFF']))

        self.assertEqual(len(recs), 0)

    @httpretty.activate
    def test_api_key(self):
        """Test if genderize API is called with apikey parameter"""

        setup_genderize_server()

        uuids = [self.john_smith.uuid]
        recs = list(recommend_gender(uuids))

        expected = {
            'name': ['john'],
            'apikey': ['fake-key']
        }

        request = httpretty.last_request()
        self.assertEqual(request.querystring, expected)

    @httpretty.activate
    def test_retry(self):
        """Test if the request is retried when an error is returned"""

        http_requests = setup_genderize_server()

        # This profile won't be updated due to connection errors
        # In this case, a 502 HTTP error
        self.error_name = api.add_identity(self.ctx,
                                           name='Error Name',
                                           source='scm')

        uuids = [self.error_name.uuid]
        recs = list(recommend_gender(uuids))

        # Should have retried 5 times
        self.assertEqual(len(http_requests), 6)

        self.assertEqual(len(recs), 0)
