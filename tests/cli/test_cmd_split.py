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
from sortinghat.cli.cmds.split import split


SPLIT_CMD_OP = """mutation {{
  unmergeIdentities(uuids: [{}]) {{
    uuids
  }}
}}"""


SPLIT_OUTPUT = """New individual 322397ed782a798ffd9d0bc7e293df4292fe075d split
New individual a9b403e150dd4af8953a52a4bb841051e4b705d9 split
New individual eda9f62ad321b1fbe5f283cc05e2484516203117 split
New individual ffefc2e3f2a255e9450ac9e2d36f37c28f51bd73 split
"""


SPLIT_NOT_FOUND_ERROR = (
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


class TestSplitCommand(unittest.TestCase):
    """Split command unit tests"""

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_split(self, mock_client):
        """Check if it splits a set of identities"""

        uuids = [
            '322397ed782a798ffd9d0bc7e293df4292fe075d',
            'a9b403e150dd4af8953a52a4bb841051e4b705d9',
            'eda9f62ad321b1fbe5f283cc05e2484516203117',
            'ffefc2e3f2a255e9450ac9e2d36f37c28f51bd73'
        ]

        responses = [
            {'data': {'unmergeIdentities': {'uuids': uuids}}}
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        # Split into individuals
        params = uuids
        result = runner.invoke(split, params)

        uuids_str = '"{}", "{}", "{}", "{}"'.format(*params)

        expected = SPLIT_CMD_OP.format(uuids_str)
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        self.assertEqual(result.stdout, SPLIT_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_split_dup(self, mock_client):
        """Check if it ignores dup uuids while splitting"""

        uuids = [
            '322397ed782a798ffd9d0bc7e293df4292fe075d',
            'a9b403e150dd4af8953a52a4bb841051e4b705d9',
            'eda9f62ad321b1fbe5f283cc05e2484516203117',
            'ffefc2e3f2a255e9450ac9e2d36f37c28f51bd73',
            'eda9f62ad321b1fbe5f283cc05e2484516203117'
        ]

        responses = [
            {'data': {'unmergeIdentities': {'uuids': uuids[:-1]}}}
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        # Split into individuals
        params = uuids
        result = runner.invoke(split, params)

        # Last uuid was filtered and not sent in the operation
        uuids_str = '"{}", "{}", "{}", "{}"'.format(*uuids[:-1])

        expected = SPLIT_CMD_OP.format(uuids_str)
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        self.assertEqual(result.stdout, SPLIT_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_error(self, mock_client):
        """"Check if it fails when an error is sent by the server"""

        error = {
            'message': SPLIT_NOT_FOUND_ERROR,
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
            '322397ed782a798ffd9d0bc7e293df4292fe075d',
            'FFFFFFFFFFFFFFF'
        ]
        result = runner.invoke(split, params)

        uuids_str = '"{}", "{}"'.format(*params)

        expected = SPLIT_CMD_OP.format(uuids_str)
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        expected_err = "Error: " + SPLIT_NOT_FOUND_ERROR + '\n'
        self.assertEqual(result.stderr, expected_err)
        self.assertEqual(result.exit_code, 9)


if __name__ == '__main__':
    unittest.main()
