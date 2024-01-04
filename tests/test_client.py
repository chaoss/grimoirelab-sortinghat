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

import logging
import json
import unittest

import httpretty
import sgqlc.endpoint.requests

from sgqlc.operation import Operation

from sortinghat.cli.client import (SortingHatClient,
                                   SortingHatClientError,
                                   SortingHatSchema)


# Some 'sgqlc' errors are shown because a bad configuration in
# logging. This allows to ignore these errors while running
# the tests.
logging.disable(logging.CRITICAL)


SORTINGHAT_SERVER_URL = "http://localhost:9314/"

# Errors
AUTHENTICATION_ERROR = r"Authentication error"
CONNECTION_ERROR = r"Connection error"
NOT_CONNECTED_CLIENT_ERROR = r"Client not connected with " + SORTINGHAT_SERVER_URL


class MockSortingHatServer:
    """Class to mock calls to a SortingHat server"""

    # GraphQL queries
    MUTATION_AUTH_TOKEN = """mutation {\ntokenAuth(username: "admin", password: "admin") {\ntoken\n}\n}"""
    MUTATION_AUTH_TOKEN_INVALID = """mutation {\ntokenAuth(username: "admin", password: "1234") {\ntoken\n}\n}"""

    def __init__(self, base_url):
        self.base_url = base_url

        httpretty.enable()

        httpretty.register_uri(httpretty.POST,
                               self.base_url,
                               body=self.graphql_callback)

    def graphql_callback(self, request, uri, response_headers):
        query = json.loads(request.body)['query']

        if query == self.MUTATION_AUTH_TOKEN:
            response = {'data': {'tokenAuth': {'token': '12345678'}}}
            body = json.dumps(response)
        elif query == self.MUTATION_AUTH_TOKEN_INVALID:
            response = {
                'errors': [
                    {
                        'message': "Invalid credentials.",
                        'locations': [{'line': 1, 'column': 1}],
                        'path': ['tokenAuth', 'token']
                    }
                ]
            }
            body = json.dumps(response)

        return [200, response_headers, body]


class TestSortingHatClient(unittest.TestCase):
    """Unit tests for SortingHatClient class"""

    def setUp(self):
        self.server = MockSortingHatServer(SORTINGHAT_SERVER_URL)

    def test_client_initialization(self):
        """Test if a client instance is correctly initialized"""

        # Check with default values
        client = SortingHatClient('localhost')

        self.assertEqual(client.url, "https://localhost:9314/")
        self.assertEqual(client.user, None)
        self.assertEqual(client.password, None)
        self.assertEqual(client.gqlc, None)

        # Check with defined parameters
        client = SortingHatClient('localhost', port=1111, path='graphql',
                                  user='admin', password='admin', ssl=False)
        self.assertEqual(client.url, "http://localhost:1111/graphql/")
        self.assertEqual(client.user, 'admin')
        self.assertEqual(client.password, 'admin')

        client = SortingHatClient('localhost', path='/graphql')
        self.assertEqual(client.url, "https://localhost:9314/graphql/")

    @httpretty.activate
    def test_connect(self):
        """Test whether the client establishes a connection with a SortingHat server"""

        MockSortingHatServer(SORTINGHAT_SERVER_URL)

        client = SortingHatClient('localhost', ssl=False)
        client.connect()

        self.assertIsInstance(client.gqlc, sgqlc.endpoint.requests.RequestsEndpoint)

        # Connection was established
        expected = {
            'Referer': 'http://localhost:9314/',
            'Host': 'localhost:9314'
        }
        self.assertDictEqual(client.gqlc.base_headers, expected)

    @httpretty.activate
    def test_disconnect(self):
        """Test whether the client disconnects from the server"""

        MockSortingHatServer(SORTINGHAT_SERVER_URL)

        client = SortingHatClient('localhost', ssl=False)
        client.connect()
        client.disconnect()

    @httpretty.activate
    def test_authentication(self):
        """Test whether the client authenticates on a SortingHat server"""

        MockSortingHatServer(SORTINGHAT_SERVER_URL)

        client = SortingHatClient('localhost', user='admin', password='admin', ssl=False)
        client.connect()

        self.assertIsInstance(client.gqlc, sgqlc.endpoint.requests.RequestsEndpoint)

        latest_requests = httpretty.latest_requests()
        self.assertEqual(len(latest_requests), 2)

        request = latest_requests[0]
        self.assertEqual(request.method, 'POST')
        self.assertEqual(dict(request.headers)['Host'], 'localhost:9314')

        request = latest_requests[1]
        self.assertEqual(request.method, 'POST')
        self.assertEqual(dict(request.headers)['Host'], 'localhost:9314')

        # Connection was established and authorization was completed
        expected = {
            'Authorization': 'JWT 12345678',
            'Referer': 'http://localhost:9314/',
            'Host': 'localhost:9314'
        }
        self.assertDictEqual(client.gqlc.base_headers, expected)

    @httpretty.activate
    def test_authentication_error(self):
        """Test whether it raises an error when the credentials are wrong"""

        MockSortingHatServer(SORTINGHAT_SERVER_URL)
        client = SortingHatClient('localhost', user='admin', password='1234',
                                  ssl=False)

        with self.assertRaisesRegex(SortingHatClientError, AUTHENTICATION_ERROR):
            client.connect()

    @httpretty.activate
    def test_execute(self):
        """Test if GraphQL operations are executed by the client"""

        MockSortingHatServer(SORTINGHAT_SERVER_URL)

        client = SortingHatClient('localhost', ssl=False)
        client.connect()

        op = Operation(SortingHatSchema.SortingHatMutation)
        op.token_auth(username='admin', password='admin').token()
        result = client.execute(op)

        # Check output
        expected = {
            'data': {
                'tokenAuth': {
                    'token': '12345678'
                }
            }
        }
        self.assertDictEqual(result, expected)

        # Check query
        expected_body = (
            b'{"query": "mutation {\\ntokenAuth(username: \\"admin\\", password: \\"admin\\") {\\ntoken\\n}\\n}", '
            b'"variables": null, '
            b'"operationName": null}'
        )

        request = httpretty.latest_requests()[-1]
        self.assertEqual(request.method, 'POST')
        self.assertEqual(dict(request.headers)['Host'], 'localhost:9314')
        self.assertEqual(request.body, expected_body)

    @httpretty.activate
    def test_execute_error(self):
        """Test if it raises an exception when an error is found"""

        MockSortingHatServer(SORTINGHAT_SERVER_URL)
        client = SortingHatClient('localhost', user='admin', password='admin',
                                  ssl=False)
        client.connect()

        with self.assertRaises(SortingHatClientError) as exc:
            op = Operation(SortingHatSchema.SortingHatMutation)
            op.token_auth(username='admin', password='1234').token()
            client.execute(op)

        expected = [
            {
                'message': "Invalid credentials.",
                'locations': [{'line': 1, 'column': 1}],
                'path': ['tokenAuth', 'token']
            }
        ]

        error = exc.exception
        self.assertEqual(error.msg, "GraphQL operation error; 1 errors found")
        self.assertListEqual(error.errors, expected)

    @httpretty.activate
    def test_execute_not_connected(self):
        """Test if execute fails when the client is not connected"""

        MockSortingHatServer(SORTINGHAT_SERVER_URL)
        client = SortingHatClient('localhost', ssl=False)

        with self.assertRaisesRegex(SortingHatClientError, NOT_CONNECTED_CLIENT_ERROR):
            op = Operation(SortingHatSchema.SortingHatMutation)
            op.token_auth(username='admin', password='1234').token()
            client.execute(op)

    def test_client_tenant(self):
        """Test if the tenant is included in the client connection"""

        client = SortingHatClient('localhost', tenant='tenant_1')

        self.assertEqual(client.tenant, 'tenant_1')

    def test_connect_tenant(self):
        """Test if the tenant is included in the client connection to the server"""

        MockSortingHatServer(SORTINGHAT_SERVER_URL)

        client = SortingHatClient('localhost', tenant='tenant_1')
        client.connect()

        self.assertEqual(client.tenant, 'tenant_1')

        self.assertIsInstance(client.gqlc, sgqlc.endpoint.requests.RequestsEndpoint)

        # Connection was established and tokens set
        expected = {
            'Referer': 'https://localhost:9314/',
            'Host': 'localhost:9314',
            'sortinghat-tenant': 'tenant_1'
        }
        self.assertDictEqual(client.gqlc.base_headers, expected)


if __name__ == "__main__":
    unittest.main(warnings='ignore')
