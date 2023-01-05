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
from sortinghat.cli.cmds.lock import add, rm


LOCK_ADD_CMD_OP = """mutation {{
  lock(uuid: "{}") {{
    uuid
  }}
}}"""

LOCK_RM_CMD_OP = """mutation {{
  unlock(uuid: "{}") {{
    uuid
  }}
}}"""


LOCK_ADD_OUTPUT = """Individual {} is locked\n"""

LOCK_RM_OUTPUT = """Individual {} is unlocked\n"""


LOCK_NOT_FOUND_ERROR = (
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


class TestLockAddCommand(unittest.TestCase):
    """Lock add command unit tests"""

    def test_lock_add(self):
        """Check if it adds a lock to an individual"""

        responses = [
            {'data': {'lock': {'uuid': '322397ed782a798ffd9d0bc7e293df4292fe075d'}}}
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()

        # Add lock
        params = [
            '322397ed782a798ffd9d0bc7e293df4292fe075d'
        ]
        result = runner.invoke(add, params, obj=mock_client)

        expected = LOCK_ADD_CMD_OP.format('322397ed782a798ffd9d0bc7e293df4292fe075d')
        self.assertEqual(len(mock_client.ops), 1)
        self.assertEqual(str(mock_client.ops[0]), expected)

        expected = LOCK_ADD_OUTPUT.format('322397ed782a798ffd9d0bc7e293df4292fe075d')
        self.assertEqual(result.stdout, expected)
        self.assertEqual(result.exit_code, 0)

    def test_error(self):
        """"Check if it fails when an error is sent by the server"""

        error = {
            'message': LOCK_NOT_FOUND_ERROR,
            'extensions': {
                'code': 9
            }
        }

        responses = [
            SortingHatClientError(error['message'], errors=[error])
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner(mix_stderr=False)

        params = [
            'FFFFFFFFFFFFFFF'
        ]
        result = runner.invoke(add, params, obj=mock_client)

        expected = LOCK_ADD_CMD_OP.format('FFFFFFFFFFFFFFF')
        self.assertEqual(len(mock_client.ops), 1)
        self.assertEqual(str(mock_client.ops[0]), expected)

        expected_err = "Error: " + LOCK_NOT_FOUND_ERROR + '\n'
        self.assertEqual(result.stderr, expected_err)
        self.assertEqual(result.exit_code, 9)


class TestLockRmCommand(unittest.TestCase):
    """Lock rm command unit tests"""

    def test_lock_rm(self):
        """Check if it removes a lock from an individual"""

        responses = [
            {'data': {'unlock': {'uuid': '322397ed782a798ffd9d0bc7e293df4292fe075d'}}}
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner()

        # Remove lock
        params = [
            '322397ed782a798ffd9d0bc7e293df4292fe075d'
        ]
        result = runner.invoke(rm, params, obj=mock_client)

        expected = LOCK_RM_CMD_OP.format('322397ed782a798ffd9d0bc7e293df4292fe075d')
        self.assertEqual(len(mock_client.ops), 1)
        self.assertEqual(str(mock_client.ops[0]), expected)

        expected = LOCK_RM_OUTPUT.format('322397ed782a798ffd9d0bc7e293df4292fe075d')
        self.assertEqual(result.stdout, expected)
        self.assertEqual(result.exit_code, 0)

    def test_error(self):
        """"Check if it fails when an error is sent by the server"""

        error = {
            'message': LOCK_NOT_FOUND_ERROR,
            'extensions': {
                'code': 9
            }
        }

        responses = [
            SortingHatClientError(error['message'], errors=[error])
        ]
        mock_client = MockClient(responses)

        runner = click.testing.CliRunner(mix_stderr=False)

        params = [
            'FFFFFFFFFFFFFFF'
        ]
        result = runner.invoke(rm, params, obj=mock_client)

        expected = LOCK_RM_CMD_OP.format('FFFFFFFFFFFFFFF')
        self.assertEqual(len(mock_client.ops), 1)
        self.assertEqual(str(mock_client.ops[0]), expected)

        expected_err = "Error: " + LOCK_NOT_FOUND_ERROR + '\n'
        self.assertEqual(result.stderr, expected_err)
        self.assertEqual(result.exit_code, 9)


if __name__ == '__main__':
    unittest.main()
