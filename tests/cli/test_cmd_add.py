#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2022 Bitergia
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
from sortinghat.cli.cmds.add import add


ADD_CMD_OP = """mutation {{
  addIdentity(
      source: "{}"
      email: "{}"
      name: "{}"
      username: "{}"
    ) {{
    uuid
  }}
}}"""
ADD_PARTIAL_CMD_OP = """mutation {{
  addIdentity(source: "{}", email: "{}") {{
    uuid
  }}
}}"""
ADD_UUID_CMD_OP = """mutation {{
  addIdentity(source: "{}", email: "{}", uuid: "{}") {{
    uuid
  }}
}}"""

ADD_OUTPUT = (
    "New identity eda9f62ad321b1fbe5f283cc05e2484516203117 "
    "added to eda9f62ad321b1fbe5f283cc05e2484516203117\n"
)
ADD_PARTIAL_OUTPUT = (
    "New identity 322397ed782a798ffd9d0bc7e293df4292fe075d "
    "added to 322397ed782a798ffd9d0bc7e293df4292fe075d\n"
)
ADD_UUID_OUTPUT = (
    "New identity ffefc2e3f2a255e9450ac9e2d36f37c28f51bd73 "
    "added to a9b403e150dd4af8953a52a4bb841051e4b705d9\n"
)
ADD_UTF8_OUTPUT = (
    "New identity 843fcc3383ddfd6179bef87996fa761d88a43915 "
    "added to 843fcc3383ddfd6179bef87996fa761d88a43915\n"
)
ADD_NOT_FOUND_ERROR = (
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


class TestAddCommand(unittest.TestCase):
    """Add command unit tests"""

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_add(self, mock_client):
        """Check if it adds a new identity"""

        responses = [
            {'data': {'addIdentity': {'uuid': 'eda9f62ad321b1fbe5f283cc05e2484516203117'}}},
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        # Create a new identity
        params = [
            '--source', 'scm',
            '--email', 'jroe@example.com',
            '--name', 'Jane Roe',
            '--username', 'jrae'
        ]
        result = runner.invoke(add, params)

        expected = ADD_CMD_OP.format('scm', 'jroe@example.com', 'Jane Roe', 'jrae')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        self.assertEqual(result.stdout, ADD_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_add_partial_data(self, mock_client):
        """Check if it adds a new identity giving partial data"""

        responses = [
            {'data': {'addIdentity': {'uuid': '322397ed782a798ffd9d0bc7e293df4292fe075d'}}},
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        # Create a new identity setting partial data
        params = [
            '--source', 'scm',
            '--email', 'jroe@example.com'
        ]
        result = runner.invoke(add, params)

        expected = ADD_PARTIAL_CMD_OP.format('scm', 'jroe@example.com')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        self.assertEqual(result.stdout, ADD_PARTIAL_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_add_with_uuid(self, mock_client):
        """Check if it adds a new identity to an existing one"""

        responses = [
            {'data': {'addIdentity': {'uuid': 'ffefc2e3f2a255e9450ac9e2d36f37c28f51bd73'}}}
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        # Assign to John Smith - a9b403e150dd4af8953a52a4bb841051e4b705d9
        # individual
        params = [
            '--source', 'mls',
            '--email', 'jsmith@example.com',
            '--uuid', 'a9b403e150dd4af8953a52a4bb841051e4b705d9'
        ]
        result = runner.invoke(add, params)

        expected = ADD_UUID_CMD_OP.format('mls', 'jsmith@example.com',
                                          'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        self.assertEqual(result.stdout, ADD_UUID_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_add_with_utf8_4bytes(self, mock_client):
        """Check if it adds a new identity with utf-8 of 4 bytes"""

        responses = [
            {'data': {'addIdentity': {'uuid': '843fcc3383ddfd6179bef87996fa761d88a43915'}}}
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        params = [
            '--source', 'scm',
            '--name', '😂',
            '--email', '😂',
            '--username', '😂'
        ]
        result = runner.invoke(add, params)

        expected = ADD_CMD_OP.format('scm', '😂', '😂', '😂',
                                     '843fcc3383ddfd6179bef87996fa761d88a43915')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        self.assertEqual(result.stdout, ADD_UTF8_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_error(self, mock_client):
        """"Check if it fails when an error is sent by the server"""

        error = {
            'message': ADD_NOT_FOUND_ERROR,
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
            '--source', 'scm',
            '--email', 'jroe@example.com',
            '--uuid', 'FFFFFFFFFFFFFFF'
        ]
        result = runner.invoke(add, params, obj=mock_client)

        expected = ADD_UUID_CMD_OP.format('scm', 'jroe@example.com',
                                          'FFFFFFFFFFFFFFF')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        expected_err = "Error: " + ADD_NOT_FOUND_ERROR + '\n'
        self.assertEqual(result.stderr, expected_err)
        self.assertEqual(result.exit_code, 9)


if __name__ == '__main__':
    unittest.main()
