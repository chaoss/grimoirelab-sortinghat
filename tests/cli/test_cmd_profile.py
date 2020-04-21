#!/usr/bin/env python3
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

import unittest
import unittest.mock

import click.testing

from sortinghat.cli.client import SortingHatClientError
from sortinghat.cli.cmds.profile import profile


PROFILE_CMD_OP = """mutation {{
  updateProfile(uuid: "{}", data: {{name: "{}", email: "{}", gender: "{}", countryCode: "{}"}}) {{
    individual {{
      mk
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
    }}
  }}
}}"""

PROFILE_UUID_CMD_OP = """mutation {{
  updateProfile(uuid: "{}", data: {{}}) {{
    individual {{
      mk
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
    }}
  }}
}}"""

PROFILE_BOT_CMD_OP = """mutation {{
  updateProfile(uuid: "{}", data: {{isBot: {}}}) {{
    individual {{
      mk
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
    }}
  }}
}}"""


PROFILE_OUTPUT = """individual 17ab00ed3825ec2f50483e33c88df223264182ba

Profile:
    * Name: Jane Roe
    * E-Mail: jroe@example.com
    * Gender: female
    * Bot: Yes
    * Country: US - United States of America
"""

PROFILE_EMPTY_OUTPUT = """individual 17ab00ed3825ec2f50483e33c88df223264182ba

Profile:
    * Name: -
    * E-Mail: -
    * Gender: -
    * Bot: No
    * Country: -
"""

PROFILE_NOT_FOUND_ERROR = (
    "FFFFFFFFFFFFFFF not found in the registry"
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


class TestProfileCommand(unittest.TestCase):
    """Profile command unit tests"""

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_update_profile(self, mock_client):
        """Check if it updates the profile"""

        data = {
            'mk': '17ab00ed3825ec2f50483e33c88df223264182ba',
            'profile': {
                'name': 'Jane Roe',
                'email': 'jroe@example.com',
                'gender': 'female',
                'isBot': True,
                'country': {
                    'code': 'US',
                    'name': 'United States of America'
                }
            }
        }
        responses = [
            {'data': {'updateProfile': {'individual': data}}}
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        # Update the profile
        params = [
            '--name', 'Jane Roe',
            '--email', 'jroe@example.com',
            '--gender', 'female',
            '--country', 'US',
            '17ab00ed3825ec2f50483e33c88df223264182ba'
        ]
        result = runner.invoke(profile, params)

        expected = PROFILE_CMD_OP.format('17ab00ed3825ec2f50483e33c88df223264182ba',
                                         'Jane Roe', 'jroe@example.com',
                                         'female', 'US')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        self.assertEqual(result.stdout, PROFILE_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_bot_profile(self, mock_client):
        """Check if it bot argument is set or unset"""

        data = {
            'mk': '17ab00ed3825ec2f50483e33c88df223264182ba',
            'profile': {
                'name': 'Jane Roe',
                'email': 'jroe@example.com',
                'gender': 'female',
                'isBot': True,
                'country': {
                    'code': 'US',
                    'name': 'United States of America'
                }
            }
        }
        responses = [
            {'data': {'updateProfile': {'individual': data}}}
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        # Update the profile
        params = [
            '--bot',
            '17ab00ed3825ec2f50483e33c88df223264182ba'
        ]
        result = runner.invoke(profile, params)

        expected = PROFILE_BOT_CMD_OP.format('17ab00ed3825ec2f50483e33c88df223264182ba',
                                             'true')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        self.assertEqual(result.stdout, PROFILE_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_display_profile(self, mock_client):
        """Check if it only displays a profile"""

        data = {
            'mk': '17ab00ed3825ec2f50483e33c88df223264182ba',
            'profile': {
                'name': 'Jane Roe',
                'email': 'jroe@example.com',
                'gender': 'female',
                'isBot': True,
                'country': {
                    'code': 'US',
                    'name': 'United States of America'
                }
            }
        }
        responses = [
            {'data': {'updateProfile': {'individual': data}}}
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        # Show the profile
        params = [
            '17ab00ed3825ec2f50483e33c88df223264182ba'
        ]
        result = runner.invoke(profile, params)

        expected = PROFILE_UUID_CMD_OP.format('17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        self.assertEqual(result.stdout, PROFILE_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_display_empty_profile(self, mock_client):
        """Check if it displays an empty profile"""

        data = {
            'mk': '17ab00ed3825ec2f50483e33c88df223264182ba',
            'profile': {
                'name': None,
                'email': None,
                'gender': None,
                'isBot': False,
                'country': None,
            }
        }

        responses = [
            {'data': {'updateProfile': {'individual': data}}}
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        # Show the profile
        params = [
            '17ab00ed3825ec2f50483e33c88df223264182ba'
        ]
        result = runner.invoke(profile, params)

        expected = PROFILE_UUID_CMD_OP.format('17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        self.assertEqual(result.stdout, PROFILE_EMPTY_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_error(self, mock_client):
        """"Check if it fails when an error is sent by the server"""

        error = {
            'message': PROFILE_NOT_FOUND_ERROR,
            'extensions': {
                'code': 9
            }
        }

        responses = [
            SortingHatClientError(error['message'], errors=[error])
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner(mix_stderr=False)

        params = [
            'FFFFFFFFFFFFFFF'
        ]
        result = runner.invoke(profile, params, obj=mock_client)

        expected = PROFILE_UUID_CMD_OP.format('FFFFFFFFFFFFFFF')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        expected_err = "Error: " + PROFILE_NOT_FOUND_ERROR + '\n'
        self.assertEqual(result.stderr, expected_err)
        self.assertEqual(result.exit_code, 9)


if __name__ == '__main__':
    unittest.main()
