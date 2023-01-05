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
from sortinghat.cli.cmds.mv import mv


MV_CMD_OP = """mutation {{
  moveIdentity(fromUuid: "{}", toUuid: "{}") {{
    uuid
  }}
}}"""

MV_OUTPUT = (
    "Identity 322397ed782a798ffd9d0bc7e293df4292fe075d moved to "
    "individual eda9f62ad321b1fbe5f283cc05e2484516203117\n"
)
MV_NEW_UID_OUTPUT = (
    "New individual 322397ed782a798ffd9d0bc7e293df4292fe075d created; "
    "identity moved\n"
)


MV_NOT_FOUND_ERROR = (
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


class TestMvCommand(unittest.TestCase):
    """Mv command unit tests"""

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_mv(self, mock_client):
        """Check if it moves a new identity"""

        responses = [
            {'data': {'moveIdentity': {'uuid': 'eda9f62ad321b1fbe5f283cc05e2484516203117'}}}
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        # Create a new identity
        params = [
            '322397ed782a798ffd9d0bc7e293df4292fe075d',
            'eda9f62ad321b1fbe5f283cc05e2484516203117'
        ]
        result = runner.invoke(mv, params)

        expected = MV_CMD_OP.format('322397ed782a798ffd9d0bc7e293df4292fe075d',
                                    'eda9f62ad321b1fbe5f283cc05e2484516203117')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        self.assertEqual(result.stdout, MV_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_mv_to_new_uid(self, mock_client):
        """Check if it creates a new individual when moving"""

        responses = [
            {'data': {'moveIdentity': {'uuid': 'eda9f62ad321b1fbe5f283cc05e2484516203117'}}}
        ]
        client = MockClient(responses)
        mock_client.return_value = client

        runner = click.testing.CliRunner()

        # Create a new identity
        params = [
            '322397ed782a798ffd9d0bc7e293df4292fe075d',
            '322397ed782a798ffd9d0bc7e293df4292fe075d'
        ]
        result = runner.invoke(mv, params)

        expected = MV_CMD_OP.format('322397ed782a798ffd9d0bc7e293df4292fe075d',
                                    '322397ed782a798ffd9d0bc7e293df4292fe075d')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        self.assertEqual(result.stdout, MV_NEW_UID_OUTPUT)
        self.assertEqual(result.exit_code, 0)

    @unittest.mock.patch('sortinghat.cli.utils.SortingHatClient')
    def test_error(self, mock_client):
        """"Check if it fails when an error is sent by the server"""

        error = {
            'message': MV_NOT_FOUND_ERROR,
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
        result = runner.invoke(mv, params)

        expected = MV_CMD_OP.format('322397ed782a798ffd9d0bc7e293df4292fe075d',
                                    'FFFFFFFFFFFFFFF')
        self.assertEqual(len(client.ops), 1)
        self.assertEqual(str(client.ops[0]), expected)

        expected_err = "Error: " + MV_NOT_FOUND_ERROR + '\n'
        self.assertEqual(result.stderr, expected_err)
        self.assertEqual(result.exit_code, 9)


if __name__ == '__main__':
    unittest.main()
