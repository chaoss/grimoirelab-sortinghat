#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2016 Bitergia
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.move import Move
from sortinghat.exceptions import CODE_NOT_FOUND_ERROR

from tests.base import TestCommandCaseBase


MOVE_FROM_ID_NOT_FOUND_ERROR = "Error: FFFFFFFFFFF not found in the registry"
MOVE_TO_UUID_NOT_FOUND_ERROR = "Error: Jane Rae not found in the registry"

MOVE_OUTPUT = """Identity b4c250eaaf873a04093319f26ca13b02a9248251 moved to unique identity John Smith"""
MOVE_NEW_UID_OUTPUT = """New unique identity b4c250eaaf873a04093319f26ca13b02a9248251 created. Identity moved"""
MOVE_EMPTY_OUTPUT = ""


class TestMoveCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on move unit tests"""

    cmd_klass = Move

    def load_test_dataset(self):
        api.add_unique_identity(self.db, 'John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com',
                         uuid='John Smith')
        api.add_identity(self.db, 'scm', 'jsmith@example.com', 'John Smith',
                         uuid='John Smith')

        api.add_unique_identity(self.db, 'John Doe')
        api.add_identity(self.db, 'scm', 'jdoe@example.com',
                         uuid='John Doe')


class TestMoveCommand(TestMoveCaseBase):
    """Move command unit tests"""

    def test_move(self):
        """Check how it works when moving an identity"""

        # Move an identity
        code = self.cmd.run('b4c250eaaf873a04093319f26ca13b02a9248251', 'John Smith')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, MOVE_OUTPUT)


class TestMove(TestMoveCaseBase):
    """Unit tests for move"""

    def test_move(self):
        """Check behaviour moving an identity"""

        code = self.cmd.move('b4c250eaaf873a04093319f26ca13b02a9248251', 'John Smith')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, MOVE_OUTPUT)

    def test_not_found_from_id_identity(self):
        """Check if it fails moving an identity that does not exist"""

        code = self.cmd.move('FFFFFFFFFFF', 'John Smith')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, MOVE_FROM_ID_NOT_FOUND_ERROR)

    def test_not_found_to_uuid_unique_identity(self):
        """Check if it fails moving an identity to a unique identity that does not exist"""

        code = self.cmd.move('b4c250eaaf873a04093319f26ca13b02a9248251', 'Jane Rae')
        self.assertEqual(code, CODE_NOT_FOUND_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, MOVE_TO_UUID_NOT_FOUND_ERROR)

    def test_create_new_unique_identity(self):
        """Check if a new unique identity is created when both uuids are equal"""

        code = self.cmd.move('b4c250eaaf873a04093319f26ca13b02a9248251', 'b4c250eaaf873a04093319f26ca13b02a9248251')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, MOVE_NEW_UID_OUTPUT)

    def test_none_ids(self):
        """Check behavior moving None ids"""

        code = self.cmd.move(None, 'John Smith')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.move('b4c250eaaf873a04093319f26ca13b02a9248251', None)
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, MOVE_EMPTY_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, MOVE_EMPTY_OUTPUT)

    def test_empty_ids(self):
        """Check behavior moving empty ids"""

        code = self.cmd.move('', 'John Smith')
        self.assertEqual(code, CMD_SUCCESS)

        code = self.cmd.move('b4c250eaaf873a04093319f26ca13b02a9248251', '')
        self.assertEqual(code, CMD_SUCCESS)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, MOVE_EMPTY_OUTPUT)

        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, MOVE_EMPTY_OUTPUT)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
