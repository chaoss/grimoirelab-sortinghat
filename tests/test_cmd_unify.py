#!/usr/bin/env python
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

import json
import os
import shutil
import sys
import tempfile
import unittest
import unittest.mock

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat import api
from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.unify import Unify
from sortinghat.exceptions import CODE_MATCHER_NOT_SUPPORTED_ERROR

from tests.base import TestCommandCaseBase


UNIFY_DEFAULT_OUTPUT_RECOVERY = """Loading matches from recovery file:.*
Unique identity 880b3dfcb3a08712e5831bddc3dfe81fc5d7b331 merged on 178315df7941fc76a6ffb06fd5b00f6932ad9c41
Total unique identities processed: 6
Total matches: 1
Total unique identities after merging: 5"""
UNIFY_DEFAULT_OUTPUT = """Unique identity 880b3dfcb3a08712e5831bddc3dfe81fc5d7b331 merged on 178315df7941fc76a6ffb06fd5b00f6932ad9c41
Total unique identities processed: 6
Total matches: 1
Total unique identities after merging: 5"""
UNIFY_SOURCES_OUTPUT = """Unique identity f30dc6a71730e37f03c7e27379febb219f7918de merged on 9cb28b6fb034393bbe4749081e0da6cc5a715b85
Total unique identities processed: 6
Total matches: 1
Total unique identities after merging: 5"""
UNIFY_NO_STRICT_OUTPUT = """Unique identity 9cb28b6fb034393bbe4749081e0da6cc5a715b85 merged on 54806f99212ac5de67684dabda6db139fc6507ee
Unique identity f30dc6a71730e37f03c7e27379febb219f7918de merged on 54806f99212ac5de67684dabda6db139fc6507ee
Unique identity 400fdfaab5918d1b7e0e0efba4797abdc378bd7d merged on 178315df7941fc76a6ffb06fd5b00f6932ad9c41
Unique identity 880b3dfcb3a08712e5831bddc3dfe81fc5d7b331 merged on 178315df7941fc76a6ffb06fd5b00f6932ad9c41
Total unique identities processed: 6
Total matches: 4
Total unique identities after merging: 2"""
UNIFY_EMAIL_NAME_OUTPUT = """Unique identity 400fdfaab5918d1b7e0e0efba4797abdc378bd7d merged on 178315df7941fc76a6ffb06fd5b00f6932ad9c41
Unique identity 880b3dfcb3a08712e5831bddc3dfe81fc5d7b331 merged on 178315df7941fc76a6ffb06fd5b00f6932ad9c41
Unique identity f30dc6a71730e37f03c7e27379febb219f7918de merged on 9cb28b6fb034393bbe4749081e0da6cc5a715b85
Total unique identities processed: 6
Total matches: 3
Total unique identities after merging: 3"""
UNIFY_EMPTY_OUTPUT = """Total unique identities processed: 0
Total matches: 0
Total unique identities after merging: 0"""


UNIFY_MATCHING_ERROR = "Error: mock identity matcher is not supported"


class TestUnifyCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on unify unit tests"""

    cmd_klass = Unify

    def load_test_dataset(self):
        # Add some unique identities

        uuid = api.add_identity(self.db, source='scm', email='jsmith@example.com', name='John Smith')
        api.add_identity(self.db, source='scm', name='John Smith', uuid=uuid)
        api.add_identity(self.db, source='scm', username='jsmith', uuid=uuid)

        uuid = api.add_identity(self.db, source='alt', name='J. Smith', username='john_smith')
        api.add_identity(self.db, source='alt', name='John Smith', username='jsmith', uuid=uuid)
        api.add_identity(self.db, source='alt', email='jsmith', uuid=uuid)

        uuid = api.add_identity(self.db, source='scm', name='Jane Rae')
        api.add_identity(self.db, source='mls', email='jane.rae@example.net', name='Jane Rae Doe', uuid=uuid)

        uuid = api.add_identity(self.db, source='scm', name='J. Smith', username='john_smith')
        api.add_identity(self.db, source='scm', username='john_smith', uuid=uuid)
        api.add_identity(self.db, source='mls', username='Smith. J', uuid=uuid)
        api.add_identity(self.db, source='mls', email='JSmith@example.com', name='Smith. J', uuid=uuid)

        uuid = api.add_identity(self.db, source='mls', email='jrae@example.net', name='Jane Rae Doe')
        api.add_identity(self.db, source='mls', name='jrae', uuid=uuid)

        uuid = api.add_identity(self.db, source='scm', name='jrae')


class TestUnifyCommand(TestUnifyCaseBase):
    """Unify command unit tests"""

    def setUp(self):
        super().setUp()
        self.recovery_path = os.path.join('/tmp', next(tempfile._get_candidate_names()))

    def tearDown(self):
        if os.path.exists(self.recovery_path):
            os.remove(self.recovery_path)

    def test_unify(self):
        """Test command"""

        code = self.cmd.run()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_DEFAULT_OUTPUT)

    def test_unify_fast_matching(self):
        """Test command with fast matching"""

        code = self.cmd.run('--fast-matching')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_DEFAULT_OUTPUT)

    def test_unify_no_strict(self):
        """Test command with no strict mode active"""

        code = self.cmd.run('--no-strict-matching', '--matching', 'email-name')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_NO_STRICT_OUTPUT)

    def test_unify_sources_list(self):
        """Test command with a sources list"""

        code = self.cmd.run('--matching', 'email-name',
                            '--sources', 'mls', 'alt')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        # Only jrae identities are merged
        self.assertEqual(output, UNIFY_SOURCES_OUTPUT)

    def test_unify_email_name_matcher(self):
        """Test command using the email-name matcher"""

        code = self.cmd.run('--matching', 'email-name')
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_EMAIL_NAME_OUTPUT)

    def test_unify_load_matches_from_recovery_file(self):
        """Test command when loading matches from the recovery file"""

        original_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/unify_matches.log')
        shutil.copyfile(original_log, self.recovery_path)

        with unittest.mock.patch('sortinghat.cmd.unify.RecoveryFile.location') as mock_location:
            mock_location.return_value = self.recovery_path

            self.assertTrue(os.path.exists(self.recovery_path))
            code = self.cmd.run('--recovery')
            self.assertEqual(code, CMD_SUCCESS)
            output = sys.stdout.getvalue().strip()
            self.assertRegex(output, UNIFY_DEFAULT_OUTPUT_RECOVERY)
            self.assertFalse(os.path.exists(self.recovery_path))

    def test_unify_disabled_recovery(self):
        """Test command when the recovery file exists but the recovery mode is not active"""

        original_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/unify_matches.log')
        shutil.copyfile(original_log, self.recovery_path)

        with unittest.mock.patch('sortinghat.cmd.unify.RecoveryFile.location') as mock_location:
            mock_location.return_value = self.recovery_path

            self.assertTrue(os.path.exists(self.recovery_path))
            code = self.cmd.run()
            self.assertEqual(code, CMD_SUCCESS)
            output = sys.stdout.getvalue().strip()
            self.assertEqual(output, UNIFY_DEFAULT_OUTPUT)
            self.assertTrue(os.path.exists(self.recovery_path))

    def test_unify_success_no_recovery_file(self):
        """Test command when the recovery file does not exist, the recovery mode is active and the execution is ok"""

        with unittest.mock.patch('sortinghat.cmd.unify.RecoveryFile.location') as mock_location:
            mock_location.return_value = self.recovery_path
            self.assertFalse(os.path.exists(self.recovery_path))

            self.assertFalse(os.path.exists(self.recovery_path))
            self.cmd.run('--recovery')
            self.assertFalse(os.path.exists(self.recovery_path))

    @unittest.mock.patch('sortinghat.api.merge_unique_identities')
    def test_unify_no_success_no_recovery_file(self, mock_merge_unique_identities):
        """Test command when the recovery file does not exist, the recovery mode is active and the execution isn't ok"""

        mock_merge_unique_identities.side_effect = Exception

        with unittest.mock.patch('sortinghat.cmd.unify.RecoveryFile.location') as mock_location:
            mock_location.return_value = self.recovery_path

            self.assertFalse(os.path.exists(self.recovery_path))
            with self.assertRaises(Exception):
                self.cmd.run('--recovery')
            self.assertTrue(os.path.exists(self.recovery_path))

            with open(self.recovery_path, 'r') as f:
                count_objs = 0
                for line in f.readlines():
                    matches_obj = json.loads(line.strip("\n"))
                    self.assertTrue(all([isinstance(m, str) for m in matches_obj['identities']]))
                    self.assertFalse(matches_obj['processed'])
                    count_objs += 1

                self.assertEqual(count_objs, 1)

    @unittest.mock.patch('sortinghat.api.merge_unique_identities')
    def test_unify_no_success_no_recovery(self, mock_merge_unique_identities):
        """Test command when the the recovery mode is not active and the execution isn't ok"""

        mock_merge_unique_identities.side_effect = Exception

        with unittest.mock.patch('sortinghat.cmd.unify.RecoveryFile.location') as mock_location:
            mock_location.return_value = self.recovery_path

            self.assertFalse(os.path.exists(self.recovery_path))
            with self.assertRaises(Exception):
                self.cmd.run()
            self.assertFalse(os.path.exists(self.recovery_path))

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Delete the contents of the database
        self.db.clear()

        code = self.cmd.run()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_EMPTY_OUTPUT)


class TestUnify(TestUnifyCaseBase):
    """Unit tests for unify"""

    def setUp(self):
        super().setUp()
        self.recovery_path = os.path.join('/tmp', next(tempfile._get_candidate_names()))

    def tearDown(self):
        if os.path.exists(self.recovery_path):
            os.remove(self.recovery_path)

    def test_unify(self):
        """Test unify method using a default matcher"""

        before = api.unique_identities(self.db)
        self.assertEqual(len(before), 6)

        code = self.cmd.unify(matching='default')
        self.assertEqual(code, CMD_SUCCESS)

        after = api.unique_identities(self.db)
        self.assertEqual(len(after), 5)

        # jsmith identities with same email address
        jsmith = after[0]
        self.assertEqual(jsmith.uuid, '178315df7941fc76a6ffb06fd5b00f6932ad9c41')

        identities = jsmith.identities
        identities.sort(key=lambda x: x.id)

        self.assertEqual(len(identities), 7)

        id_ = identities[1]
        self.assertEqual(id_.email, 'JSmith@example.com')
        self.assertEqual(id_.source, 'mls')

        id_ = identities[3]
        self.assertEqual(id_.email, 'jsmith@example.com')
        self.assertEqual(id_.source, 'scm')

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_DEFAULT_OUTPUT)

    def test_unify_from_recovery_file(self):
        """Test unify method when reading matches from the recovery file"""

        original_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/unify_matches.log')
        shutil.copyfile(original_log, self.recovery_path)

        with unittest.mock.patch('sortinghat.cmd.unify.RecoveryFile.location') as mock_location:
            mock_location.return_value = self.recovery_path

            before = api.unique_identities(self.db)
            self.assertEqual(len(before), 6)

            self.assertTrue(os.path.exists(self.recovery_path))
            code = self.cmd.unify(matching='default', recovery=True)
            self.assertEqual(code, CMD_SUCCESS)

            after = api.unique_identities(self.db)
            self.assertEqual(len(after), 5)

            # jsmith identities with same email address
            jsmith = after[0]
            self.assertEqual(jsmith.uuid, '178315df7941fc76a6ffb06fd5b00f6932ad9c41')

            identities = jsmith.identities
            identities.sort(key=lambda x: x.id)

            self.assertEqual(len(identities), 7)

            id_ = identities[1]
            self.assertEqual(id_.email, 'JSmith@example.com')
            self.assertEqual(id_.source, 'mls')

            id_ = identities[3]
            self.assertEqual(id_.email, 'jsmith@example.com')
            self.assertEqual(id_.source, 'scm')

            output = sys.stdout.getvalue().strip()
            self.assertRegex(output, UNIFY_DEFAULT_OUTPUT_RECOVERY)
            self.assertFalse(os.path.exists(self.recovery_path))

    def test_unify_success_no_recovery_mode(self):
        """Test unify method when the recovery file exists but the recovery mode is not active"""

        original_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/unify_matches.log')
        shutil.copyfile(original_log, self.recovery_path)

        with unittest.mock.patch('sortinghat.cmd.unify.RecoveryFile.location') as mock_location:
            mock_location.return_value = self.recovery_path

            before = api.unique_identities(self.db)
            self.assertEqual(len(before), 6)

            self.assertTrue(os.path.exists(self.recovery_path))
            code = self.cmd.unify(matching='default')
            self.assertEqual(code, CMD_SUCCESS)

            after = api.unique_identities(self.db)
            self.assertEqual(len(after), 5)

            # jsmith identities with same email address
            jsmith = after[0]
            self.assertEqual(jsmith.uuid, '178315df7941fc76a6ffb06fd5b00f6932ad9c41')

            identities = jsmith.identities
            identities.sort(key=lambda x: x.id)

            self.assertEqual(len(identities), 7)

            id_ = identities[1]
            self.assertEqual(id_.email, 'JSmith@example.com')
            self.assertEqual(id_.source, 'mls')

            id_ = identities[3]
            self.assertEqual(id_.email, 'jsmith@example.com')
            self.assertEqual(id_.source, 'scm')

            output = sys.stdout.getvalue().strip()
            self.assertEqual(output, UNIFY_DEFAULT_OUTPUT)
            self.assertTrue(os.path.exists(self.recovery_path))

    @unittest.mock.patch('sortinghat.api.merge_unique_identities')
    def test_unify_no_success_no_recovery_file(self, mock_merge_unique_identities):
        """Test command when the recovery file does not exist, the recovery mode is active and the execution isn't ok"""

        mock_merge_unique_identities.side_effect = Exception

        with unittest.mock.patch('sortinghat.cmd.unify.RecoveryFile.location') as mock_location:
            mock_location.return_value = self.recovery_path

            self.assertFalse(os.path.exists(self.recovery_path))
            with self.assertRaises(Exception):
                self.cmd.unify(matching='default', recovery=True)
            self.assertTrue(os.path.exists(self.recovery_path))

            with open(self.recovery_path, 'r') as f:
                count_objs = 0
                for line in f.readlines():
                    matches_obj = json.loads(line.strip("\n"))
                    self.assertTrue(all([isinstance(m, str) for m in matches_obj['identities']]))
                    self.assertFalse(matches_obj['processed'])
                    count_objs += 1

                self.assertEqual(count_objs, 1)

    @unittest.mock.patch('sortinghat.api.merge_unique_identities')
    def test_unify_no_success_no_recovery_mode(self, mock_merge_unique_identities):
        """Test command when the the recovery mode is not active and the execution isn't ok"""

        mock_merge_unique_identities.side_effect = Exception

        with unittest.mock.patch('sortinghat.cmd.unify.RecoveryFile.location') as mock_location:
            mock_location.return_value = self.recovery_path

            self.assertFalse(os.path.exists(self.recovery_path))
            with self.assertRaises(Exception):
                self.cmd.unify(matching='default')
            self.assertFalse(os.path.exists(self.recovery_path))

    def test_unify_fast_matching(self):
        """Test unify method using a default matcher and fast matching mode"""

        before = api.unique_identities(self.db)
        self.assertEqual(len(before), 6)

        code = self.cmd.unify(matching='default', fast_matching=True)
        self.assertEqual(code, CMD_SUCCESS)

        after = api.unique_identities(self.db)
        self.assertEqual(len(after), 5)

        # jsmith identities with same email address
        jsmith = after[0]
        self.assertEqual(jsmith.uuid, '178315df7941fc76a6ffb06fd5b00f6932ad9c41')

        identities = jsmith.identities
        identities.sort(key=lambda x: x.id)

        self.assertEqual(len(identities), 7)

        id_ = identities[1]
        self.assertEqual(id_.email, 'JSmith@example.com')
        self.assertEqual(id_.source, 'mls')

        id_ = identities[3]
        self.assertEqual(id_.email, 'jsmith@example.com')
        self.assertEqual(id_.source, 'scm')

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_DEFAULT_OUTPUT)

    def test_unify_no_strict(self):
        """Test unify method with no strict mode set"""

        before = api.unique_identities(self.db)
        self.assertEqual(len(before), 6)

        code = self.cmd.unify(matching='email-name',
                              no_strict_matching=True)
        self.assertEqual(code, CMD_SUCCESS)

        after = api.unique_identities(self.db)
        self.assertEqual(len(after), 2)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_NO_STRICT_OUTPUT)

    def test_unify_with_blacklist(self):
        """Test unify method using a blacklist"""

        # Add some entries to the blacklist
        api.add_to_matching_blacklist(self.db, 'Jane Rae Doe')
        api.add_to_matching_blacklist(self.db, 'jsmith@example.com')

        before = api.unique_identities(self.db)
        self.assertEqual(len(before), 6)

        code = self.cmd.unify(matching='default')
        self.assertEqual(code, CMD_SUCCESS)

        # No match was found
        after = api.unique_identities(self.db)
        self.assertEqual(len(after), 6)

    def test_unify_with_sources_list(self):
        """Test unify method using a sources list"""

        sources = ['mls', 'alt']

        before = api.unique_identities(self.db)
        self.assertEqual(len(before), 6)

        code = self.cmd.unify(matching='email-name', sources=sources)
        self.assertEqual(code, CMD_SUCCESS)

        # Only jrae identities are merged
        after = api.unique_identities(self.db)
        self.assertEqual(len(after), 5)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_SOURCES_OUTPUT)

    def test_unify_email_name_matcher(self):
        """Test unify method using the email-name matcher"""

        before = api.unique_identities(self.db)
        self.assertEqual(len(before), 6)

        code = self.cmd.unify(matching='email-name')
        self.assertEqual(code, CMD_SUCCESS)

        after = api.unique_identities(self.db)
        self.assertEqual(len(after), 3)

        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_EMAIL_NAME_OUTPUT)

    def test_unify_email_name_matcher_with_blacklist(self):
        """Test unify method using a blacklist"""

        # Add some entries to the blacklist
        api.add_to_matching_blacklist(self.db, 'Jane Rae Doe')
        api.add_to_matching_blacklist(self.db, 'jsmith@example.com')

        before = api.unique_identities(self.db)
        self.assertEqual(len(before), 6)

        code = self.cmd.unify(matching='email-name')
        self.assertEqual(code, CMD_SUCCESS)

        after = api.unique_identities(self.db)
        self.assertEqual(len(after), 5)

        # Only two identities were merged due to the blacklist
        jsmith = after[0]
        self.assertEqual(jsmith.uuid, '178315df7941fc76a6ffb06fd5b00f6932ad9c41')
        self.assertEqual(len(jsmith.identities), 4)

        jsmith = after[1]
        self.assertEqual(jsmith.uuid, '400fdfaab5918d1b7e0e0efba4797abdc378bd7d')
        self.assertEqual(len(jsmith.identities), 6)

    def test_empty_registry(self):
        """Check output when the registry is empty"""

        # Delete the contents of the database
        self.db.clear()

        code = self.cmd.unify()
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip()
        self.assertEqual(output, UNIFY_EMPTY_OUTPUT)

    def test_invalid_matching_method(self):
        """Check if it fails when an invalid matching method is given"""

        code = self.cmd.unify(matching='mock')
        self.assertEqual(code, CODE_MATCHER_NOT_SUPPORTED_ERROR)
        output = sys.stderr.getvalue().strip()
        self.assertEqual(output, UNIFY_MATCHING_ERROR)


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
