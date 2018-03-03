#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2017 Bitergia
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

from __future__ import absolute_import
from __future__ import unicode_literals

import json
import sys
import unittest

import httpretty

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.autogender import AutoGender, genderize

from tests.base import TestCommandCaseBase


GENDERIZE_API_URL = "https://api.genderize.io/"

PROFILE_AUTOGENDER = """unique identity 2a9ec221b8dd5d5a85ae0e3276b8b2c3618ee15e (Jane) gender profile updated to female (acc: 100)
unique identity 539acca35c2e8502951a97d2d5af8b0857440b50 (John Smith) gender profile updated to male (acc: 99)
unique identity a39ac334be9f17bfc7f9f21bbb25f389388f8e18 (John D) gender profile updated to male (acc: 99)"""

PROFILE_AUTOGENDER_ALL = """unique identity 2a9ec221b8dd5d5a85ae0e3276b8b2c3618ee15e (Jane) gender profile updated to female (acc: 100)
unique identity 3e1eccdb1e52ea56225f419d3e532fe9133c7821 (Jane R) gender profile updated to female (acc: 100)
unique identity 539acca35c2e8502951a97d2d5af8b0857440b50 (John Smith) gender profile updated to male (acc: 99)
unique identity a39ac334be9f17bfc7f9f21bbb25f389388f8e18 (John D) gender profile updated to male (acc: 99)"""


def setup_genderize_server():
    """Setup a mock HTTP server for genderize.io"""

    http_requests = []

    def request_callback(method, uri, headers):
        last_request = httpretty.last_request()
        http_requests.append(last_request)

        params = last_request.querystring
        name = params['name'][0].lower()

        if name == 'john':
            data = {
                'gender': 'male',
                'probability': 0.99
            }
        elif name == 'jane':
            data = {
                'gender': 'female',
                'probability': 1.0
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


class TestAutoGenderCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on autogender unit tests"""

    cmd_klass = AutoGender

    def load_test_dataset(self):
        # Add identities
        jroe_uuid = api.add_identity(self.db, 'scm', 'jroe@example.com',
                                     'Jane', 'jroe')
        api.edit_profile(self.db, jroe_uuid, name="Jane")

        jrae_uuid = api.add_identity(self.db, 'scm', 'jrae@example.com',
                                     'Jane', 'jrae')
        api.edit_profile(self.db, jrae_uuid, name="Jane R", gender="unknown")

        jsmith_uuid = api.add_identity(self.db, 'mls', 'jsmith@example.com',
                                       'John Smith', 'jsmith')
        api.edit_profile(self.db, jsmith_uuid, name="John Smith")

        jdoe_uuid = api.add_identity(self.db, 'scm', 'jdoe@example.com',
                                     'John D', 'jdoe')
        api.edit_profile(self.db, jdoe_uuid, name="John D")



class TestAutoGender(TestAutoGenderCaseBase):
    """Unit tests for autogender command"""

    @httpretty.activate
    def test_command(self):
        """Test autogender command"""

        setup_genderize_server()

        code = self.cmd.run()

        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, PROFILE_AUTOGENDER)

    @httpretty.activate
    def test_command_token(self):
        """Test if autogender is called with token parameter"""

        setup_genderize_server()

        code = self.cmd.run('--api-token', 'abcdefghi')

        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, PROFILE_AUTOGENDER)

        expected = {
            'name': ['John'],
            'apikey': ['abcdefghi']
        }

        req = httpretty.last_request()
        self.assertEqual(req.querystring, expected)

    @httpretty.activate
    def test_command_all(self):
        """Test if data about gender is overwritten for all the unique identities"""

        setup_genderize_server()

        code = self.cmd.run('--all')

        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, PROFILE_AUTOGENDER_ALL)

    @httpretty.activate
    def test_autogender(self):
        """Test autogender method"""

        http_requests = setup_genderize_server()

        self.cmd.autogender(api_token='abcdefghi')

        uids = api.unique_identities(self.db)

        prf = uids[0].profile
        self.assertEqual(prf.uuid, '2a9ec221b8dd5d5a85ae0e3276b8b2c3618ee15e')
        self.assertEqual(prf.gender, 'female')
        self.assertEqual(prf.gender_acc, 100)

        # Jane Rae gender is not updated because it was already set
        prf = uids[1].profile
        self.assertEqual(prf.uuid, '3e1eccdb1e52ea56225f419d3e532fe9133c7821')
        self.assertEqual(prf.gender, 'unknown')
        self.assertEqual(prf.gender_acc, 100)

        prf = uids[2].profile
        self.assertEqual(prf.uuid, '539acca35c2e8502951a97d2d5af8b0857440b50')
        self.assertEqual(prf.gender, 'male')
        self.assertEqual(prf.gender_acc, 99)

        prf = uids[3].profile
        self.assertEqual(prf.uuid, 'a39ac334be9f17bfc7f9f21bbb25f389388f8e18')
        self.assertEqual(prf.gender, 'male')
        self.assertEqual(prf.gender_acc, 99)

        # Check requests
        expected = [
            {
                'name': ['Jane'],
                'apikey': ['abcdefghi']
            },
            {
                'name': ['John'],
                'apikey': ['abcdefghi']
            },
        ]

        self.assertEqual(len(http_requests), len(expected))

        for i in range(len(expected)):
            self.assertDictEqual(http_requests[i].querystring, expected[i])

    @httpretty.activate
    def test_autogender_all(self):
        """Test whether all gener info is overwritten"""

        http_requests = setup_genderize_server()

        self.cmd.autogender(api_token='abcdefghi', genderize_all=True)

        uids = api.unique_identities(self.db)

        prf = uids[0].profile
        self.assertEqual(prf.uuid, '2a9ec221b8dd5d5a85ae0e3276b8b2c3618ee15e')
        self.assertEqual(prf.gender, 'female')
        self.assertEqual(prf.gender_acc, 100)

        prf = uids[1].profile
        self.assertEqual(prf.uuid, '3e1eccdb1e52ea56225f419d3e532fe9133c7821')
        self.assertEqual(prf.gender, 'female')
        self.assertEqual(prf.gender_acc, 100)

        prf = uids[2].profile
        self.assertEqual(prf.uuid, '539acca35c2e8502951a97d2d5af8b0857440b50')
        self.assertEqual(prf.gender, 'male')
        self.assertEqual(prf.gender_acc, 99)

        prf = uids[3].profile
        self.assertEqual(prf.uuid, 'a39ac334be9f17bfc7f9f21bbb25f389388f8e18')
        self.assertEqual(prf.gender, 'male')
        self.assertEqual(prf.gender_acc, 99)

        # Check requests
        expected = [
            {
                'name': ['Jane'],
                'apikey': ['abcdefghi']
            },
            {
                'name': ['John'],
                'apikey': ['abcdefghi']
            },
        ]

        self.assertEqual(len(http_requests), len(expected))

        for i in range(len(expected)):
            self.assertDictEqual(http_requests[i].querystring, expected[i])

    @httpretty.activate
    def test_autogender_name_not_found(self):
        """Test if no gender is set when a name is not found"""

        http_requests = setup_genderize_server()

        # This name won't be found
        uuid = api.add_identity(self.db, 'scm', 'random@example.com',
                                'Random Name')
        api.edit_profile(self.db, uuid, name="random")

        self.cmd.autogender(api_token='abcdefghi')

        uids = api.unique_identities(self.db)

        prf = uids[0].profile
        self.assertEqual(prf.uuid, '2a9ec221b8dd5d5a85ae0e3276b8b2c3618ee15e')
        self.assertEqual(prf.gender, 'female')
        self.assertEqual(prf.gender_acc, 100)

        # Jane Rae gender is not updated because it was already set
        prf = uids[1].profile
        self.assertEqual(prf.uuid, '3e1eccdb1e52ea56225f419d3e532fe9133c7821')
        self.assertEqual(prf.gender, 'unknown')
        self.assertEqual(prf.gender_acc, 100)

        prf = uids[2].profile
        self.assertEqual(prf.uuid, '539acca35c2e8502951a97d2d5af8b0857440b50')
        self.assertEqual(prf.gender, 'male')
        self.assertEqual(prf.gender_acc, 99)

        prf = uids[3].profile
        self.assertEqual(prf.uuid, 'a39ac334be9f17bfc7f9f21bbb25f389388f8e18')
        self.assertEqual(prf.gender, 'male')
        self.assertEqual(prf.gender_acc, 99)

        # This name was not found and the gender was not updated
        prf = uids[4].profile
        self.assertEqual(prf.uuid, 'cfa19ae04ce0c70902a31084fc75086b61ccfcf2')
        self.assertEqual(prf.gender, None)
        self.assertEqual(prf.gender_acc, None)

        # Check requests
        expected = [
            {
                'name': ['Jane'],
                'apikey': ['abcdefghi']
            },
            {
                'name': ['John'],
                'apikey': ['abcdefghi']
            },
            {
                'name': ['random'],
                'apikey': ['abcdefghi']
            },
        ]

        self.assertEqual(len(http_requests), len(expected))

        for i in range(len(expected)):
            self.assertDictEqual(http_requests[i].querystring, expected[i])


class TestGenderize(unittest.TestCase):
    """Genderize function tests"""

    @httpretty.activate
    def test_genderize(self):
        """Test if the gender of a name is obtained"""

        setup_genderize_server()

        gender, acc = genderize('John')
        self.assertEqual(gender, 'male')
        self.assertEqual(acc, 99)

        expected = {
            'name': ['John']
        }

        req = httpretty.last_request()
        self.assertEqual(req.method, 'GET')
        self.assertEqual(req.querystring, expected)

    @httpretty.activate
    def test_name_not_found(self):
        """Test if a null response is returned when the name is not found"""

        setup_genderize_server()

        gender, acc = genderize('Jack')
        self.assertEqual(gender, None)
        self.assertEqual(acc, None)

        expected = {
            'name': ['Jack']
        }

        req = httpretty.last_request()
        self.assertEqual(req.method, 'GET')
        self.assertEqual(req.querystring, expected)

    @httpretty.activate
    def test_api_token(self):
        """Test if the api token is set in the request"""

        setup_genderize_server()

        genderize('John', api_token='abcdefghi')

        expected = {
            'name': ['John'],
            'apikey': ['abcdefghi']
        }

        req = httpretty.last_request()
        self.assertEqual(req.method, 'GET')
        self.assertEqual(req.querystring, expected)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
