#!/usr/bin/env python3
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

import unittest
import unittest.mock

import click.testing

from sortinghat.cli.client import SortingHatClientError
from sortinghat.cli.cmds.countries import countries


COUNTRIES_CMD_OP = """query {{
  countries({}) {{
    pageInfo {{
      hasNext
    }}
    entities {{
      code
      name
    }}
  }}
}}"""

COUNTRIES_OUTPUT = """ES\tSpain
GB\tUnited Kingdom
US\tUnited States of America
"""

COUNTRIES_CODE_OUTPUT = """ES\tSpain\n"""

COUNTRIES_TERM_OUTPUT = """GB\tUnited Kingdom
US\tUnited States of America
"""

COUNTRIES_EMPTY_OUTPUT = """"""

COUNTRIES_UKNOWN_ERROR = (
    "unknown error"
)

COUNTRIES_CODE_ERROR = (
    "Error: Invalid value for '--code': "
    "country code must be a 2 alpha characters long"
)
COUNTRIES_TERM_ERROR = (
    "Error: Invalid value for '--term': "
    "term must be at least 3 characters long"
)


class MockClient:
    """Mock client"""

    def __init__(self, responses):
        self.responses = responses
        self.ops = []

    def connect(self):
        pass

    def disconnect(self):
        pass

    def execute(self, operation):
        self.ops.append(operation)
        response = self.responses.pop(0)

        if isinstance(response, SortingHatClientError):
            raise response
        else:
            return response


class TestCountriesCommand(unittest.TestCase):
    """Countries command unit tests"""

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_countries(self, mock_client):
        """Check if it displays information of countries"""

        # Split entities into pages
        responses = [
            {
                'data': {
                    'countries': {
                        'pageInfo': {'hasNext': True},
                        'entities': [
                            {
                                'code': 'ES',
                                'name': 'Spain'
                            },
                            {
                                'code': 'GB',
                                'name': 'United Kingdom'
                            }
                        ]
                    }
                }
            },
            {
                'data': {
                    'countries': {
                        'pageInfo': {'hasNext': False},
                        'entities': [
                            {
                                'code': 'US',
                                'name': 'United States of America'
                            }
                        ]
                    }
                }
            }
        ]

        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()
        result = runner.invoke(countries)

        self.assertEqual(len(client.ops), 2)
        expected = COUNTRIES_CMD_OP.format('page: 1')
        op = str(client.ops[0])
        self.assertEqual(op, expected)

        expected = COUNTRIES_CMD_OP.format('page: 2')
        op = str(client.ops[1])
        self.assertEqual(op, expected)

        self.assertEqual(result.stdout, COUNTRIES_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_countries_code(self, mock_client):
        """Check if it displays information of countries when code is set"""

        # Split entities into pages
        responses = [
            {
                'data': {
                    'countries': {
                        'pageInfo': {'hasNext': False},
                        'entities': [
                            {
                                'code': 'ES',
                                'name': 'Spain'
                            }
                        ]
                    }
                }
            }
        ]

        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        params = ['--code', 'ES']
        result = runner.invoke(countries, params)

        self.assertEqual(len(client.ops), 1)

        filters = 'page: {}, filters: {{code: "{}"}}'
        filters = filters.format('1', 'ES')
        expected = COUNTRIES_CMD_OP.format(filters)
        op = str(client.ops[0])
        self.assertEqual(op, expected)

        self.assertEqual(result.stdout, COUNTRIES_CODE_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    def test_countries_invalid_code(self):
        """Check if it fails when code is invalid"""

        runner = click.testing.CliRunner(mix_stderr=False)

        params = ['--code', 'E']
        result = runner.invoke(countries, params)

        self.assertEqual(result.stderr.split('\n')[-2],
                         COUNTRIES_CODE_ERROR)
        self.assertEqual(result.exit_code, 2)

        params = ['--code', '']
        result = runner.invoke(countries, params)

        self.assertEqual(result.stderr.split('\n')[-2],
                         COUNTRIES_CODE_ERROR)
        self.assertEqual(result.exit_code, 2)

        params = ['--code', 'AAA']
        result = runner.invoke(countries, params)

        self.assertEqual(result.stderr.split('\n')[-2],
                         COUNTRIES_CODE_ERROR)
        self.assertEqual(result.exit_code, 2)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_countries_term(self, mock_client):
        """Check if it displays information of countries when term is set"""

        # Split entities into pages
        responses = [
            {
                'data': {
                    'countries': {
                        'pageInfo': {'hasNext': False},
                        'entities': [
                            {
                                'code': 'GB',
                                'name': 'United Kingdom'
                            },
                            {
                                'code': 'US',
                                'name': 'United States of America'
                            }
                        ]
                    }
                }
            }
        ]

        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        params = ['--term', 'unit']
        result = runner.invoke(countries, params)

        self.assertEqual(len(client.ops), 1)

        filters = 'page: {}, filters: {{term: "{}"}}'
        filters = filters.format('1', 'unit')
        expected = COUNTRIES_CMD_OP.format(filters)
        op = str(client.ops[0])
        self.assertEqual(op, expected)

        self.assertEqual(result.stdout, COUNTRIES_TERM_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    def test_countries_invalid_term(self):
        """Check if it fails when term is invalid"""

        runner = click.testing.CliRunner(mix_stderr=False)

        params = ['--term', 'E']
        result = runner.invoke(countries, params)

        self.assertEqual(result.stderr.split('\n')[-2],
                         COUNTRIES_TERM_ERROR)
        self.assertEqual(result.exit_code, 2)

        params = ['--term', '']
        result = runner.invoke(countries, params)

        self.assertEqual(result.stderr.split('\n')[-2],
                         COUNTRIES_TERM_ERROR)
        self.assertEqual(result.exit_code, 2)

        params = ['--term', 'AA']
        result = runner.invoke(countries, params)

        self.assertEqual(result.stderr.split('\n')[-2],
                         COUNTRIES_TERM_ERROR)
        self.assertEqual(result.exit_code, 2)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_countries_empty(self, mock_client):
        """Check if it displays an empty list of countries"""

        responses = [
            {
                'data': {
                    'countries': {
                        'pageInfo': {'hasNext': False},
                        'entities': []
                    }
                }
            }
        ]

        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        result = runner.invoke(countries)

        self.assertEqual(len(client.ops), 1)

        expected = COUNTRIES_CMD_OP.format('page: 1')
        op = str(client.ops[0])
        self.assertEqual(op, expected)

        self.assertEqual(result.stdout, COUNTRIES_EMPTY_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_error(self, mock_client):
        """"Check if it fails when an error is sent by the server"""

        error = {
            'message': COUNTRIES_UKNOWN_ERROR,
            'extensions': {
                'code': 128
            }
        }

        responses = [
            SortingHatClientError(error['message'], errors=[error])
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner(mix_stderr=False)

        result = runner.invoke(countries)

        expected = COUNTRIES_CMD_OP.format('page: 1')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        expected_err = "Error: " + COUNTRIES_UKNOWN_ERROR + '\n'
        self.assertEqual(result.stderr, expected_err)
        self.assertEqual(result.exit_code, 128)


if __name__ == '__main__':
    unittest.main()
