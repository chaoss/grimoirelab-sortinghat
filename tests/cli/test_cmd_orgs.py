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

import click.testing

from sortinghat.cli.client import SortingHatClientError
from sortinghat.cli.cmds.orgs import add, rm, show


ORGS_ADD_ORG_CMD_OP = """mutation {{
  addOrganization(name: "{}") {{
    organization {{
      name
    }}
  }}
}}"""

ORGS_ADD_DOM_CMD_OP = """mutation {{
  addDomain(organization: "{}", domain: "{}", isTopDomain: {}) {{
    domain {{
      domain
    }}
  }}
}}"""

ORGS_RM_ORG_CMD_OP = """mutation {{
  deleteOrganization(name: "{}") {{
    organization {{
      name
    }}
  }}
}}"""

ORGS_RM_DOM_CMD_OP = """mutation {{
  deleteDomain(domain: "{}") {{
    domain {{
      domain
    }}
  }}
}}"""

ORGS_SHOW_ORGS_CMD_OP = """query {{
  organizations(page: {}) {{
    pageInfo {{
      hasNext
    }}
    entities {{
      name
      domains {{
        domain
        isTopDomain
      }}
    }}
  }}
}}"""


ORG_ALREADY_EXISTS_ERROR = "Example already exists in the registry"
DOM_ALREADY_EXISTS_ERROR = "example.org already exists in the registry"
ORG_DOES_NOT_EXIST_ERROR = "Example not found in the registry"
DOM_DOES_NOT_EXIST_ERROR = "example.org not found in the registry"


SHOW_CMD_OUTPUT = """Bitergia\tbitergia.com *
Bitergia\tbitergia.net
Example\texample.com
Example\texample.net
Example\texample.org
LibreSoft
"""

SHOW_EMPTY_CMD_OUTPUT = """"""


class MockClient:
    """Mock client"""

    def __init__(self, responses):
        self.responses = responses
        self.ops = []

    def connect(self):
        pass

    def execute(self, operation):
        self.ops.append(operation)
        response = self.responses.pop(0)

        if isinstance(response, SortingHatClientError):
            raise response
        else:
            return response

    def disconnect(self):
        pass


class TestOrgsAdd(unittest.TestCase):
    """Add organizations and domains command unit tests"""

    def test_add_organization(self):
        """Check if it runs a query to add an organization"""

        responses = [
            {'data': {'addOrganization': {'organization': {'name': 'Example'}}}}
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()

        params = ['Example']
        result = runner.invoke(add, params, obj=mock_client)

        expected = ORGS_ADD_ORG_CMD_OP.format('Example')
        self.assertEqual(len(mock_client.ops), 1)
        self.assertEqual(str(mock_client.ops[0]), expected)
        self.assertEqual(result.exit_code, 0)

    def test_add_domain(self):
        """Check if it runs a query to add a domain"""

        responses = [
            {'data': {'addDomain': {'domain': {'domain': 'example.org'}}}}
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()

        params = ['Example', 'example.org']
        result = runner.invoke(add, params, obj=mock_client)

        expected = ORGS_ADD_DOM_CMD_OP.format('Example', 'example.org', 'false')
        self.assertEqual(len(mock_client.ops), 1)
        self.assertEqual(str(mock_client.ops[0]), expected)
        self.assertEqual(result.exit_code, 0)

    def test_add_domain_top_domain(self):
        """Check if runs a query to add a top domain"""

        responses = [
            {'data': {'addDomain': {'domain': {'domain': 'example.org'}}}}
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()

        params = ['Example', 'example.org', '--top-domain']
        result = runner.invoke(add, params, obj=mock_client)

        expected = ORGS_ADD_DOM_CMD_OP.format('Example', 'example.org', 'true')
        self.assertEqual(len(mock_client.ops), 1)
        self.assertEqual(str(mock_client.ops[0]), expected)
        self.assertEqual(result.exit_code, 0)

    def test_org_already_exists_error(self):
        """Check if fails when an organization already exists"""

        error = {
            'message': ORG_ALREADY_EXISTS_ERROR,
            'extensions': {
                'code': 2
            }
        }

        responses = [
            SortingHatClientError(error['message'], errors=[error])
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()

        params = ['Example']
        result = runner.invoke(add, params, obj=mock_client)

        expected = ORGS_ADD_ORG_CMD_OP.format('Example')
        self.assertEqual(len(mock_client.ops), 1)
        self.assertEqual(str(mock_client.ops[0]), expected)
        self.assertEqual(result.exit_code, 2)

    def test_domain_already_exists_error(self):
        """Check if fails when a domain already exists"""

        error = {
            'message': DOM_ALREADY_EXISTS_ERROR,
            'extensions': {
                'code': 2
            }
        }

        responses = [
            SortingHatClientError(error['message'], errors=[error])
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()

        params = ['Example', 'example.org']
        result = runner.invoke(add, params, obj=mock_client)

        expected = ORGS_ADD_DOM_CMD_OP.format('Example', 'example.org', 'false')
        self.assertEqual(len(mock_client.ops), 1)
        self.assertEqual(str(mock_client.ops[0]), expected)
        self.assertEqual(result.exit_code, 2)


class TestOrgsRm(unittest.TestCase):
    """Rm organizations and domains command unit tests"""

    def test_remove_organization(self):
        """Check if it runs a query to remove an organization"""

        responses = [
            {'data': {'deleteOrganization': {'organization': {'name': 'Example'}}}}
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()

        params = ['Example']
        result = runner.invoke(rm, params, obj=mock_client)

        expected = ORGS_RM_ORG_CMD_OP.format('Example')
        self.assertEqual(len(mock_client.ops), 1)
        self.assertEqual(str(mock_client.ops[0]), expected)
        self.assertEqual(result.exit_code, 0)

    def test_remove_domain(self):
        """Check if it runs a query to remove a domain"""

        responses = [
            {
                'data': {
                    'organizations': {
                        'pageInfo': {'totalResults': 1},
                        'entities': [{'domains': [{'domain': 'example.org'}]}]
                    }
                }
            },
            {'data': {'deleteDomain': {'domain': {'domain': 'example.org'}}}}
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()

        params = ['Example', 'example.org']
        result = runner.invoke(rm, params, obj=mock_client)

        expected = ORGS_RM_DOM_CMD_OP.format('example.org')
        self.assertEqual(len(mock_client.ops), 2)
        self.assertEqual(str(mock_client.ops[1]), expected)
        self.assertEqual(result.exit_code, 0)

    def test_org_not_found_error(self):
        """Check if fails when an organization does not exist"""

        error = {
            'message': ORG_DOES_NOT_EXIST_ERROR,
            'extensions': {
                'code': 9
            }
        }

        responses = [
            SortingHatClientError(error['message'], errors=[error])
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()

        params = ['Example']
        result = runner.invoke(rm, params, obj=mock_client)

        expected = ORGS_RM_ORG_CMD_OP.format('Example')
        self.assertEqual(len(mock_client.ops), 1)
        self.assertEqual(str(mock_client.ops[0]), expected)
        self.assertEqual(result.exit_code, 9)

    def test_domain_not_found_error(self):
        """Check if fails when a domain does not exist"""

        responses = [
            {
                'data': {
                    'organizations': {
                        'pageInfo': {'totalResults': 1},
                        'entities': [{'domains': [{'domain': 'example.net'}]}]
                    }
                }
            }
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()

        params = ['Example', 'example.org']
        result = runner.invoke(rm, params, obj=mock_client)
        self.assertEqual(len(mock_client.ops), 1)
        self.assertEqual(result.exit_code, 9)

    def test_domain_not_found_after_find_it(self):
        """Check if it fails when the domain was found but removed by other during this command"""

        error = {
            'message': DOM_DOES_NOT_EXIST_ERROR,
            'extensions': {
                'code': 9
            }
        }

        responses = [
            {
                'data': {
                    'organizations': {
                        'pageInfo': {'totalResults': 1},
                        'entities': [{'domains': [{'domain': 'example.org'}]}]
                    }
                }
            },
            SortingHatClientError(error['message'], errors=[error])
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()

        params = ['Example', 'example.org']
        result = runner.invoke(rm, params, obj=mock_client)

        expected = ORGS_RM_DOM_CMD_OP.format('example.org')
        self.assertEqual(len(mock_client.ops), 2)
        self.assertEqual(str(mock_client.ops[1]), expected)
        self.assertEqual(result.exit_code, 9)

    def test_domain_not_found_organization(self):
        """Check if it fails when the organization"""

        responses = [
            {
                'data': {
                    'organizations': {
                        'pageInfo': {'totalResults': 0},
                        'entities': []
                    }
                }
            }
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()

        params = ['Example', 'example.org']
        result = runner.invoke(rm, params, obj=mock_client)
        self.assertEqual(len(mock_client.ops), 1)
        self.assertEqual(result.exit_code, 9)


class TestOrgsShow(unittest.TestCase):
    """Show command unit tests"""

    def test_show(self):
        """Check if it runs a query to show the list of organizations"""

        entities = [
            {
                'name': 'Bitergia',
                'domains': [
                    {'domain': 'bitergia.com', 'isTopDomain': True},
                    {'domain': 'bitergia.net', 'isTopDomain': False}
                ]
            },
            {
                'name': 'Example',
                'domains': [
                    {'domain': 'example.com', 'isTopDomain': False},
                    {'domain': 'example.net', 'isTopDomain': False},
                    {'domain': 'example.org', 'isTopDomain': False},
                ]
            },
            {
                'name': 'LibreSoft',
                'domains': []
            }
        ]

        # Split entities into pages
        responses = [
            {
                'data': {
                    'organizations': {
                        'pageInfo': {'hasNext': True},
                        'entities': entities[0:2]
                    }
                }
            },
            {
                'data': {
                    'organizations': {
                        'pageInfo': {'hasNext': False},
                        'entities': entities[2:]
                    }
                }
            }
        ]

        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()
        result = runner.invoke(show, obj=mock_client)

        self.assertEqual(len(mock_client.ops), 2)
        expected = ORGS_SHOW_ORGS_CMD_OP.format('1')
        op = str(mock_client.ops[0])
        self.assertEqual(op, expected)

        expected = ORGS_SHOW_ORGS_CMD_OP.format('2')
        op = str(mock_client.ops[1])
        self.assertEqual(op, expected)

        self.assertEqual(result.stdout, SHOW_CMD_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    def test_empty_show(self):
        """Check if it runs a query to show an empty list of organizations"""

        responses = [
            {
                'data': {
                    'organizations': {
                        'pageInfo': {'hasNext': False},
                        'entities': []
                    }
                }
            }
        ]

        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()
        result = runner.invoke(show, obj=mock_client)

        self.assertEqual(len(mock_client.ops), 1)

        expected = ORGS_SHOW_ORGS_CMD_OP.format('1')
        op = str(mock_client.ops[0])
        self.assertEqual(op, expected)

        self.assertEqual(result.stdout, SHOW_EMPTY_CMD_OUTPUT)
        self.assertEqual(result.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
