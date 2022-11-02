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
from sortinghat.cli.cmds.show import show


SHOW_CMD_OP = """query {{
  individuals({}) {{
    pageInfo {{
      hasNext
    }}
    entities {{
      mk
      isLocked
      profile {{
        name
        email
        gender
        isBot
        country {{
          code
          name
        }}
      }}
      identities {{
        uuid
        email
        name
        username
        source
      }}
      enrollments {{
        start
        end
        group {{
          name
        }}
      }}
    }}
  }}
}}"""


SHOW_OUTPUT = """
individual 0000000000000000000000000000000000000000\t(locked)

Profile:
    * Name: -
    * E-Mail: -
    * Gender: -
    * Bot: Yes
    * Country: -

No identities

No enrollments


individual 17ab00ed3825ec2f50483e33c88df223264182ba

Profile:
    * Name: Jane Roe
    * E-Mail: jroe@example.com
    * Gender: female
    * Bot: No
    * Country: US - United States of America

Identities:
  17ab00ed3825ec2f50483e33c88df223264182ba\tJane Roe\tjroe@example.com\tjroe\tscm
  22d1b20763c6f5822bdda8508957486c547bb9de\t-\tjroe@bitergia.com\t-\tunknown
  322397ed782a798ffd9d0bc7e293df4292fe075d\t-\tjroe@example.com\t-\tscm

Enrollments:
  Bitergia\t1999-01-01 00:00:00\t2000-01-01 00:00:00
  Bitergia\t2006-01-01 00:00:00\t2008-01-01 00:00:00
  Example\t1900-01-01 00:00:00\t2100-01-01 00:00:00


individual a9b403e150dd4af8953a52a4bb841051e4b705d9

Profile:
    * Name: -
    * E-Mail: jsmith@example.com
    * Gender: male
    * Bot: Yes
    * Country: -

Identities:
  880b3dfcb3a08712e5831bddc3dfe81fc5d7b331\tJohn Smith\tjsmith@example.com\t-\tscm
  a9b403e150dd4af8953a52a4bb841051e4b705d9\tJohn Smith\tjsmith@example.com\tjsmith\tscm

Enrollments:
  Example\t1900-01-01 00:00:00\t2100-01-01 00:00:00

"""

SHOW_UUID_OUTPUT = """
individual 17ab00ed3825ec2f50483e33c88df223264182ba

Profile:
    * Name: Jane Roe
    * E-Mail: jroe@example.com
    * Gender: female
    * Bot: No
    * Country: US - United States of America

Identities:
  17ab00ed3825ec2f50483e33c88df223264182ba\tJane Roe\tjroe@example.com\tjroe\tscm
  22d1b20763c6f5822bdda8508957486c547bb9de\t-\tjroe@bitergia.com\t-\tunknown
  322397ed782a798ffd9d0bc7e293df4292fe075d\t-\tjroe@example.com\t-\tscm

Enrollments:
  Bitergia\t1999-01-01 00:00:00\t2000-01-01 00:00:00
  Bitergia\t2006-01-01 00:00:00\t2008-01-01 00:00:00
  Example\t1900-01-01 00:00:00\t2100-01-01 00:00:00

"""

SHOW_EMPTY_OUTPUT = """"""


SHOW_UKNOWN_ERROR = (
    "unknown error"
)


EMPTY_ID_PROFILE = {
    'name': None,
    'email': None,
    'gender': None,
    'isBot': True,
    'country': None
}

JANE_ROE_PROFILE = {
    'name': 'Jane Roe',
    'email': 'jroe@example.com',
    'gender': 'female',
    'isBot': False,
    'country': {
        'code': 'US',
        'name': 'United States of America'
    }
}
JANE_ROE_IDENTITIES = [
    {
        'uuid': '17ab00ed3825ec2f50483e33c88df223264182ba',
        'email': 'jroe@example.com',
        'name': 'Jane Roe',
        'username': 'jroe',
        'source': 'scm'
    },
    {
        'uuid': '22d1b20763c6f5822bdda8508957486c547bb9de',
        'email': 'jroe@bitergia.com',
        'name': None,
        'username': None,
        'source': 'unknown'
    },
    {
        'uuid': '322397ed782a798ffd9d0bc7e293df4292fe075d',
        'email': 'jroe@example.com',
        'name': None,
        'username': None,
        'source': 'scm'
    }
]
JANE_ROE_ENROLLMENTS = [
    {
        'start': '1999-01-01T00:00:00Z',
        'end': '2000-01-01T00:00:00Z',
        'group': {
            'name': 'Bitergia'
        }
    },
    {
        'start': '2006-01-01T00:00:00Z',
        'end': '2008-01-01T00:00:00Z',
        'group': {
            'name': 'Bitergia'
        }
    },
    {
        'start': '1900-01-01T00:00:00Z',
        'end': '2100-01-01T00:00:00Z',
        'group': {
            'name': 'Example'
        }
    }
]

JSMITH_PROFILE = {
    'name': None,
    'email': 'jsmith@example.com',
    'gender': 'male',
    'isBot': True,
    'country': None
}
JSMITH_IDENTITIES = [
    {
        'uuid': '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331',
        'email': 'jsmith@example.com',
        'name': 'John Smith',
        'username': None,
        'source': 'scm'
    },
    {
        'uuid': 'a9b403e150dd4af8953a52a4bb841051e4b705d9',
        'email': 'jsmith@example.com',
        'name': 'John Smith',
        'username': 'jsmith',
        'source': 'scm'
    }
]
JSMITH_ENROLLMENTS = [
    {
        'start': '1900-01-01T00:00:00Z',
        'end': '2100-01-01T00:00:00Z',
        'group': {
            'name': 'Example'
        }
    }
]

EMPTY_ID_DATA = {
    'mk': '0000000000000000000000000000000000000000',
    'isLocked': True,
    'profile': EMPTY_ID_PROFILE,
    'identities': [],
    'enrollments': []
}
JANE_ROE_ID_DATA = {
    'mk': '17ab00ed3825ec2f50483e33c88df223264182ba',
    'isLocked': False,
    'profile': JANE_ROE_PROFILE,
    'identities': JANE_ROE_IDENTITIES,
    'enrollments': JANE_ROE_ENROLLMENTS
}
JSMITH_ID_DATA = {
    'mk': 'a9b403e150dd4af8953a52a4bb841051e4b705d9',
    'isLocked': False,
    'profile': JSMITH_PROFILE,
    'identities': JSMITH_IDENTITIES,
    'enrollments': JSMITH_ENROLLMENTS
}


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


class TestShowCommand(unittest.TestCase):
    """Show command unit tests"""

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_show(self, mock_client):
        """Check if it displays information of individuals"""

        entities = [
            EMPTY_ID_DATA,
            JANE_ROE_ID_DATA,
            JSMITH_ID_DATA
        ]

        # Split entities into pages
        responses = [
            {
                'data': {
                    'individuals': {
                        'pageInfo': {'hasNext': True},
                        'entities': entities[0:2]
                    }
                }
            },
            {
                'data': {
                    'individuals': {
                        'pageInfo': {'hasNext': False},
                        'entities': entities[2:]
                    }
                }
            }
        ]

        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()
        result = runner.invoke(show)

        self.assertEqual(len(client.ops), 2)
        expected = SHOW_CMD_OP.format('page: 1')
        op = str(client.ops[0])
        self.assertEqual(op, expected)

        expected = SHOW_CMD_OP.format('page: 2')
        op = str(client.ops[1])
        self.assertEqual(op, expected)

        self.assertEqual(result.stdout, SHOW_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_show_uuid(self, mock_client):
        """Check if it displays information of the given individual"""

        entities = [
            JANE_ROE_ID_DATA
        ]

        # Split entities into pages
        responses = [
            {
                'data': {
                    'individuals': {
                        'pageInfo': {'hasNext': False},
                        'entities': entities
                    }
                }
            }
        ]

        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        params = ['17ab00ed3825ec2f50483e33c88df223264182ba']
        result = runner.invoke(show, params)

        self.assertEqual(len(client.ops), 1)

        filters = 'page: {}, filters: {{uuid: "{}"}}'
        filters = filters.format('1', '17ab00ed3825ec2f50483e33c88df223264182ba')
        expected = SHOW_CMD_OP.format(filters)
        op = str(client.ops[0])
        self.assertEqual(op, expected)

        self.assertEqual(result.stdout, SHOW_UUID_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_show_empty(self, mock_client):
        """Check if it shows an empty list of individuals"""

        responses = [
            {
                'data': {
                    'individuals': {
                        'pageInfo': {'hasNext': False},
                        'entities': []
                    }
                }
            }
        ]

        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        result = runner.invoke(show)

        self.assertEqual(len(client.ops), 1)

        expected = SHOW_CMD_OP.format('page: 1')
        op = str(client.ops[0])
        self.assertEqual(op, expected)

        self.assertEqual(result.stdout, SHOW_EMPTY_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_error(self, mock_client):
        """"Check if it fails when an error is sent by the server"""

        error = {
            'message': SHOW_UKNOWN_ERROR,
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

        result = runner.invoke(show)

        expected = SHOW_CMD_OP.format('page: 1')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        expected_err = "Error: " + SHOW_UKNOWN_ERROR + '\n'
        self.assertEqual(result.stderr, expected_err)
        self.assertEqual(result.exit_code, 128)


if __name__ == '__main__':
    unittest.main()
