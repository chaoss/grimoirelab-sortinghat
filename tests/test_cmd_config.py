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

import os.path
import sys
import unittest

import configparser

if '..' not in sys.path:
    sys.path.insert(0, '..')

from sortinghat.command import CMD_SUCCESS
from sortinghat.cmd.config import Config

from tests.base import TestCommandCaseBase, datadir


MOCK_CONFIG_FILE = datadir('mock_config_file.cfg')

INVALID_CONFIG_FILE = "Configuration file not given"
SET_KEY_CONFIG_ERROR = "%(param)s parameter does not exists or cannot be set"
GET_KEY_CONFIG_ERROR = "%(param)s parameter does not exists"
NOT_FOUND_FILE_ERROR = "./data/invalid_config_file.cfg config file does not exist"


class TestConfigCaseBase(TestCommandCaseBase):
    """Defines common setup and teardown methods on config unit tests"""

    cmd_klass = Config

    def load_test_dataset(self):
        pass


class TestSetConfig(TestConfigCaseBase):
    """Set method unit tests"""

    def test_none_param_values(self):
        """Check it if raises exceptions when passing None params"""

        self.assertRaisesRegex(RuntimeError,
                               SET_KEY_CONFIG_ERROR % {'param': 'None'},
                               self.cmd.set, None, 'value',
                               MOCK_CONFIG_FILE)

        self.assertRaisesRegex(RuntimeError,
                               INVALID_CONFIG_FILE,
                               self.cmd.set, 'db.user', 'value',
                               None)

    def test_unsupported_keys(self):
        """Check if it raises an error when passing unsupported keys"""

        # Test not available keys
        self.assertRaisesRegex(RuntimeError,
                               SET_KEY_CONFIG_ERROR % {'param': 'section.option'},
                               self.cmd.set, 'section.option', 'value',
                               MOCK_CONFIG_FILE)

        # Test keys that do not follow '<section>.<option>' schema
        self.assertRaisesRegex(RuntimeError,
                               SET_KEY_CONFIG_ERROR % {'param': '1'},
                               self.cmd.set, 1, 'value',
                               MOCK_CONFIG_FILE)
        self.assertRaisesRegex(RuntimeError,
                               SET_KEY_CONFIG_ERROR % {'param': ''},
                               self.cmd.set, '.', 'value',
                               MOCK_CONFIG_FILE)
        self.assertRaisesRegex(RuntimeError,
                               SET_KEY_CONFIG_ERROR % {'param': '.'},
                               self.cmd.set, '.', 'value',
                               MOCK_CONFIG_FILE)
        self.assertRaisesRegex(RuntimeError,
                               SET_KEY_CONFIG_ERROR % {'param': 'section.'},
                               self.cmd.set, 'section.', 'value',
                               MOCK_CONFIG_FILE)
        self.assertRaisesRegex(RuntimeError,
                               SET_KEY_CONFIG_ERROR % {'param': '.option'},
                               self.cmd.set, '.option', 'value',
                               MOCK_CONFIG_FILE)
        self.assertRaisesRegex(RuntimeError,
                               SET_KEY_CONFIG_ERROR % {'param': 'section.option.suboption'},
                               self.cmd.set, 'section.option.suboption', 'value',
                               MOCK_CONFIG_FILE)

    def test_invalid_config_files(self):
        """Check whether it raises and error reading invalid configuration files"""

        # Test directory
        dirpath = os.path.expanduser('~')

        self.assertRaises(RuntimeError, self.cmd.set,
                          'db.user', 'value', dirpath)

    def test_set_value(self):
        """Check set method"""

        import shutil
        import tempfile

        # Copy the reference config file to a temporary directory
        testpath = tempfile.mkdtemp(prefix='sortinghat_')
        shutil.copy(MOCK_CONFIG_FILE, testpath)
        filepath = os.path.join(testpath, 'mock_config_file.cfg')

        # First read initial values
        config = configparser.SafeConfigParser()
        config.read(filepath)

        self.assertEqual(config.get('db', 'user'), 'root')
        self.assertEqual(config.get('db', 'database'), 'testdb')

        # Set the new values
        retcode = self.cmd.set('db.user', 'jsmith', filepath)
        self.assertEqual(retcode, CMD_SUCCESS)

        retcode = self.cmd.set('db.database', 'mydb', filepath)
        self.assertEqual(retcode, CMD_SUCCESS)

        # Check the new values
        config.read(filepath)
        self.assertEqual(config.get('db', 'user'), 'jsmith')
        self.assertEqual(config.get('db', 'password'), '****')
        self.assertEqual(config.get('db', 'database'), 'mydb')

        shutil.rmtree(testpath)


class TestGetConfig(TestConfigCaseBase):
    """Get method unit tests"""

    def test_none_param_values(self):
        """Check it if raises exceptions when passing None params"""

        self.assertRaisesRegex(RuntimeError,
                               GET_KEY_CONFIG_ERROR % {'param': 'None'},
                               self.cmd.get, None, MOCK_CONFIG_FILE)

        self.assertRaisesRegex(RuntimeError,
                               INVALID_CONFIG_FILE,
                               self.cmd.get, 'db.user', None)

    def test_unsupported_keys(self):
        """Check if it raises an error when passing unsupported keys"""

        # Test not available keys
        self.assertRaisesRegex(RuntimeError,
                               GET_KEY_CONFIG_ERROR % {'param': 'section.option'},
                               self.cmd.get, 'section.option',
                               MOCK_CONFIG_FILE)

        # Test keys that do not follow '<section>.<option>' schema
        self.assertRaisesRegex(RuntimeError,
                               GET_KEY_CONFIG_ERROR % {'param': '1'},
                               self.cmd.get, 1, MOCK_CONFIG_FILE)
        self.assertRaisesRegex(RuntimeError,
                               GET_KEY_CONFIG_ERROR % {'param': ''},
                               self.cmd.get, '.', MOCK_CONFIG_FILE)
        self.assertRaisesRegex(RuntimeError,
                               GET_KEY_CONFIG_ERROR % {'param': '.'},
                               self.cmd.get, '.', MOCK_CONFIG_FILE)
        self.assertRaisesRegex(RuntimeError,
                               GET_KEY_CONFIG_ERROR % {'param': 'section.'},
                               self.cmd.get, 'section.', MOCK_CONFIG_FILE)
        self.assertRaisesRegex(RuntimeError,
                               GET_KEY_CONFIG_ERROR % {'param': '.option'},
                               self.cmd.get, '.option', MOCK_CONFIG_FILE)
        self.assertRaisesRegex(RuntimeError,
                               GET_KEY_CONFIG_ERROR % {'param': 'section.option.suboption'},
                               self.cmd.get, 'section.option.suboption',
                               MOCK_CONFIG_FILE)

    def test_invalid_config_files(self):
        """Check whether it raises and error reading invalid configuration files"""

        # Test directory
        dirpath = os.path.expanduser('~')

        self.assertRaises(RuntimeError, self.cmd.get,
                          'db.user', dirpath)

        # Test non existing file
        self.assertRaisesRegex(RuntimeError, NOT_FOUND_FILE_ERROR,
                               self.cmd.get, 'db.user',
                               datadir('invalid_config_file.cfg'))

    def test_get_value(self):
        """Test get method"""

        code = self.cmd.get('db.user', MOCK_CONFIG_FILE)
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip().split('\n')[0]
        self.assertEqual(output, 'db.user root')

        code = self.cmd.get('db.password', MOCK_CONFIG_FILE)
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip().split('\n')[1]
        self.assertEqual(output, 'db.password ****')

        code = self.cmd.get('db.database', MOCK_CONFIG_FILE)
        self.assertEqual(code, CMD_SUCCESS)
        output = sys.stdout.getvalue().strip().split('\n')[2]
        self.assertEqual(output, 'db.database testdb')


if __name__ == "__main__":
    unittest.main(buffer=True, exit=False)
