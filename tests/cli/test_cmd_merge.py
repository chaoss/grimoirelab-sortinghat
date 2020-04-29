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
from sortinghat.cli.cmds.merge import merge


MERGE_CMD_OP = """mutation {{
  merge(fromUuids: [{}], toUuid: "{}") {{
    uuid
  }}
}}"""

MERGE_NOT_FOUND_ERROR = (
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


class TestMergeCommand(unittest.TestCase):
    """Merge command unit tests"""

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_merge(self, mock_client):
        """Check if it merges a set of individuals"""

        responses = [
            {'data': {'merge': {'uuid': 'eda9f62ad321b1fbe5f283cc05e2484516203117'}}}
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        # Merge individuals
        params = [
            'eda9f62ad321b1fbe5f283cc05e2484516203117',
            '322397ed782a798ffd9d0bc7e293df4292fe075d',
            'a9b403e150dd4af8953a52a4bb841051e4b705d9',
            'ffefc2e3f2a255e9450ac9e2d36f37c28f51bd73'
        ]
        result = runner.invoke(merge, params)

        uuids = '"{}", "{}", "{}"'.format(*params[1:])

        expected = MERGE_CMD_OP.format(uuids,
                                       params[0])
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_error(self, mock_client):
        """"Check if it fails when an error is sent by the server"""

        error = {
            'message': MERGE_NOT_FOUND_ERROR,
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
        result = runner.invoke(merge, params)

        expected = MERGE_CMD_OP.format('"FFFFFFFFFFFFFFF"',
                                       '322397ed782a798ffd9d0bc7e293df4292fe075d')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        expected_err = "Error: " + MERGE_NOT_FOUND_ERROR + '\n'
        self.assertEqual(result.stderr, expected_err)
        self.assertEqual(result.exit_code, 9)


if __name__ == '__main__':
    unittest.main()
