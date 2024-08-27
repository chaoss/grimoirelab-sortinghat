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

import os.path
import shutil
import unittest
import unittest.mock

import configparser

import click.testing

from sortinghat.cli.cmds.config import (init,
                                        get,
                                        set,
                                        SORTINGHAT_CFG_FILE_NAME)


MOCK_CONFIG_FILE = 'config_file.cfg'
MOCK_CONFIG_FILEPATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                    MOCK_CONFIG_FILE)


CONFIG_FILE_EXISTS_ERROR = "Error: Configuration file {} already exists. Use '--overwrite' to replace it.\n"
INVALID_CONFIG_FILE = "Error: Could not open file '{}': [Errno 21] Is a directory: '{}'\n"
SET_KEY_CONFIG_ERROR = "Error: {} config parameter is not supported\n"
GET_KEY_CONFIG_ERROR = "Error: {} config parameter is not supported\n"
NOT_FOUND_FILE_ERROR = "Error: Could not open file '{}': file does not exist\n"


class TestInitConfig(unittest.TestCase):
    """Init command unit tests"""

    def test_init(self):
        """Check if it initializes a configuration file."""

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            filepath = os.path.join(fs, MOCK_CONFIG_FILE)

            params = [
                '--filepath', filepath
            ]
            result = runner.invoke(init, params)

            self.assertEqual(result.exit_code, 0)

            # Check the new values
            cfg = configparser.ConfigParser()
            cfg.read(filepath)
            self.assertEqual(cfg.get('endpoint', 'user'), '')
            self.assertEqual(cfg.get('endpoint', 'password'), '')
            self.assertEqual(cfg.get('endpoint', 'host'), 'localhost')
            self.assertEqual(cfg.get('endpoint', 'port'), '9314')
            self.assertEqual(cfg.get('endpoint', 'path'), '/')
            self.assertEqual(cfg.get('endpoint', 'ssl'), 'true')

    @unittest.mock.patch('os.path.expanduser')
    def test_default_filename(self, mock_basepath):
        """Check if it uses the default filename when filepath is not given"""

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            dirpath = os.path.join(fs, '.sortinghat')
            mock_basepath.return_value = dirpath
            default_filepath = os.path.join(dirpath, SORTINGHAT_CFG_FILE_NAME)

            params = []
            result = runner.invoke(init, params)

            self.assertEqual(result.exit_code, 0)

            # Check the new values
            cfg = configparser.ConfigParser()
            cfg.read(default_filepath)
            self.assertEqual(cfg.get('endpoint', 'user'), '')
            self.assertEqual(cfg.get('endpoint', 'password'), '')
            self.assertEqual(cfg.get('endpoint', 'host'), 'localhost')
            self.assertEqual(cfg.get('endpoint', 'port'), '9314')
            self.assertEqual(cfg.get('endpoint', 'path'), '/')
            self.assertEqual(cfg.get('endpoint', 'ssl'), 'true')

    def test_config_is_not_overwritten(self):
        """Check whether an existing config file is not replaced"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            shutil.copy(MOCK_CONFIG_FILEPATH, fs)
            filepath = os.path.join(fs, MOCK_CONFIG_FILE)

            # Check initial values first
            cfg = configparser.ConfigParser()
            cfg.read(filepath)
            self.assertEqual(cfg.get('endpoint', 'user'), 'root')
            self.assertEqual(cfg.get('endpoint', 'host'), 'localhost')

            params = [
                '--filepath', filepath
            ]
            result = runner.invoke(init, params)

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(result.stderr, CONFIG_FILE_EXISTS_ERROR.format(filepath))

            # Values did not change
            cfg.read(filepath)
            self.assertEqual(cfg.get('endpoint', 'user'), 'root')
            self.assertEqual(cfg.get('endpoint', 'host'), 'localhost')

    def test_overwrite_config(self):
        """Check whether an existing config file is overwritten"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            shutil.copy(MOCK_CONFIG_FILEPATH, fs)
            filepath = os.path.join(fs, MOCK_CONFIG_FILE)

            # Check initial values first
            cfg = configparser.ConfigParser()
            cfg.read(filepath)
            self.assertEqual(cfg.get('endpoint', 'user'), 'root')
            self.assertEqual(cfg.get('endpoint', 'host'), 'localhost')

            params = [
                '--filepath', filepath,
                '--overwrite'
            ]
            result = runner.invoke(init, params)

            self.assertEqual(result.exit_code, 0)

            # New values are written
            cfg.read(filepath)
            self.assertEqual(cfg.get('endpoint', 'user'), '')
            self.assertEqual(cfg.get('endpoint', 'password'), '')
            self.assertEqual(cfg.get('endpoint', 'host'), 'localhost')
            self.assertEqual(cfg.get('endpoint', 'port'), '9314')
            self.assertEqual(cfg.get('endpoint', 'path'), '/')
            self.assertEqual(cfg.get('endpoint', 'ssl'), 'true')


class TestSetConfig(unittest.TestCase):
    """Set command unit tests"""

    def test_set_value(self):
        """Check set method"""

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            shutil.copy(MOCK_CONFIG_FILEPATH, fs)
            filepath = os.path.join(fs, MOCK_CONFIG_FILE)

            # First read initial values
            cfg = configparser.ConfigParser()
            cfg.read(filepath)

            self.assertEqual(cfg.get('endpoint', 'user'), 'root')
            self.assertEqual(cfg.get('endpoint', 'host'), 'localhost')

            # Set the new values
            params = [
                'endpoint.user',
                'jsmith',
                '--filepath', filepath
            ]
            result = runner.invoke(set, params)

            self.assertEqual(result.exit_code, 0)

            params = [
                'endpoint.host',
                'example.com',
                '--filepath', filepath
            ]
            result = runner.invoke(set, params)

            self.assertEqual(result.exit_code, 0)

            # Check the new values
            cfg.read(filepath)
            self.assertEqual(cfg.get('endpoint', 'user'), 'jsmith')
            self.assertEqual(cfg.get('endpoint', 'password'), '****')
            self.assertEqual(cfg.get('endpoint', 'host'), 'example.com')

    @unittest.mock.patch('os.path.expanduser')
    def test_default_filename(self, mock_basepath):
        """Check if it uses the default filename when filepath is not given"""

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            dirpath = os.path.join(fs, '.sortinghat')
            mock_basepath.return_value = dirpath
            default_filepath = os.path.join(dirpath, SORTINGHAT_CFG_FILE_NAME)

            params = [
                'endpoint.user',
                'jsmith'
            ]
            result = runner.invoke(set, params)
            self.assertEqual(result.exit_code, 0)

            params = [
                'endpoint.host',
                'example.com'
            ]
            result = runner.invoke(set, params)
            self.assertEqual(result.exit_code, 0)

            # Check the new values
            cfg = configparser.ConfigParser()
            cfg.read(default_filepath)
            self.assertEqual(cfg.get('endpoint', 'user'), 'jsmith')
            self.assertEqual(cfg.get('endpoint', 'host'), 'example.com')

    def test_not_available_keys(self):
        """Check if it raises an error when the key is not available"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            shutil.copy(MOCK_CONFIG_FILEPATH, fs)
            filepath = os.path.join(fs, MOCK_CONFIG_FILE)

            params = [
                'section.option',
                'value',
                '--filepath', filepath
            ]
            result = runner.invoke(set, params)
            self.assertEqual(result.exit_code, 1)

            expected = SET_KEY_CONFIG_ERROR.format('section.option')
            self.assertEqual(result.stderr, expected)

    def test_invalid_keys(self):
        """Check if it raises an error when the key is invalid"""

        runner = click.testing.CliRunner(mix_stderr=False)

        # Test keys that do not follow '<section>.<option>' schema
        with runner.isolated_filesystem() as fs:
            shutil.copy(MOCK_CONFIG_FILEPATH, fs)
            filepath = os.path.join(fs, MOCK_CONFIG_FILE)

            params = [
                '1',
                'value',
                '--filepath', filepath
            ]
            result = runner.invoke(set, params)
            self.assertEqual(result.exit_code, 1)
            expected = SET_KEY_CONFIG_ERROR.format('1')
            self.assertEqual(result.stderr, expected)

            params = [
                '.',
                'value',
                '--filepath', filepath
            ]
            result = runner.invoke(set, params)
            self.assertEqual(result.exit_code, 1)
            expected = SET_KEY_CONFIG_ERROR.format('.')
            self.assertEqual(result.stderr, expected)

            params = [
                'section.',
                'value',
                '--filepath', filepath
            ]
            result = runner.invoke(set, params)
            self.assertEqual(result.exit_code, 1)
            expected = SET_KEY_CONFIG_ERROR.format('section.')
            self.assertEqual(result.stderr, expected)

            params = [
                '.option',
                'value',
                '--filepath', filepath
            ]
            result = runner.invoke(set, params)
            self.assertEqual(result.exit_code, 1)

            expected = SET_KEY_CONFIG_ERROR.format('.option')
            self.assertEqual(result.stderr, expected)

            params = [
                'section.option.suboption',
                'value',
                '--filepath', filepath
            ]
            result = runner.invoke(set, params)
            self.assertEqual(result.exit_code, 1)
            expected = SET_KEY_CONFIG_ERROR.format('section.option.suboption')
            self.assertEqual(result.stderr, expected)

    def test_invalid_config_files(self):
        """Check whether it raises and error reading invalid configuration files"""

        runner = click.testing.CliRunner(mix_stderr=False)

        # Test keys that do not follow '<section>.<option>' schema
        with runner.isolated_filesystem() as fs:
            params = [
                'endpoint.host',
                'example.com',
                '--filepath', fs
            ]
            result = runner.invoke(set, params)
            self.assertEqual(result.exit_code, 1)
            expected = INVALID_CONFIG_FILE.format(fs, fs)
            self.assertEqual(result.stderr, expected)


class TestGetConfig(unittest.TestCase):
    """Get command unit tests"""

    def test_get_value(self):
        """Test get method"""

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            shutil.copy(MOCK_CONFIG_FILEPATH, fs)
            filepath = os.path.join(fs, MOCK_CONFIG_FILE)

            params = [
                'endpoint.user',
                '--filepath', filepath
            ]
            result = runner.invoke(get, params)
            self.assertEqual(result.exit_code, 0)
            output = result.stdout.strip().split('\n')[0]
            self.assertEqual(output, 'endpoint.user root')

            params = [
                'endpoint.password',
                '--filepath', filepath
            ]
            result = runner.invoke(get, params)
            self.assertEqual(result.exit_code, 0)
            output = result.stdout.strip().split('\n')[0]
            self.assertEqual(output, 'endpoint.password ****')

            params = [
                'endpoint.host',
                '--filepath', filepath
            ]
            result = runner.invoke(get, params)
            self.assertEqual(result.exit_code, 0)
            output = result.stdout.strip().split('\n')[0]
            self.assertEqual(output, 'endpoint.host localhost')

    @unittest.mock.patch('os.path.expanduser')
    def test_default_filename(self, mock_basepath):
        """Check if it uses the default filename when filepath is not given"""

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            mock_basepath.return_value = fs
            default_filepath = os.path.join(fs, SORTINGHAT_CFG_FILE_NAME)
            shutil.copy(MOCK_CONFIG_FILEPATH, default_filepath)

            params = [
                'endpoint.user'
            ]
            result = runner.invoke(get, params)
            self.assertEqual(result.exit_code, 0)
            output = result.stdout.strip().split('\n')[0]
            self.assertEqual(output, 'endpoint.user root')

            params = [
                'endpoint.host'
            ]
            result = runner.invoke(get, params)
            self.assertEqual(result.exit_code, 0)
            output = result.stdout.strip().split('\n')[0]
            self.assertEqual(output, 'endpoint.host localhost')

    def test_not_available_keys(self):
        """Check if it raises an error when the key is not available"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            shutil.copy(MOCK_CONFIG_FILEPATH, fs)
            filepath = os.path.join(fs, MOCK_CONFIG_FILE)

            params = [
                'section.option',
                '--filepath', filepath
            ]
            result = runner.invoke(get, params)
            self.assertEqual(result.exit_code, 1)

            expected = GET_KEY_CONFIG_ERROR.format('section.option')
            self.assertEqual(result.stderr, expected)

    def test_invalid_keys(self):
        """Check if it raises an error when the key is invalid"""

        runner = click.testing.CliRunner(mix_stderr=False)

        # Test keys that do not follow '<section>.<option>' schema
        with runner.isolated_filesystem() as fs:
            shutil.copy(MOCK_CONFIG_FILEPATH, fs)
            filepath = os.path.join(fs, MOCK_CONFIG_FILE)

            params = [
                '1',
                '--filepath', filepath
            ]
            result = runner.invoke(get, params)
            self.assertEqual(result.exit_code, 1)
            expected = GET_KEY_CONFIG_ERROR.format('1')
            self.assertEqual(result.stderr, expected)

            params = [
                '.',
                '--filepath', filepath
            ]
            result = runner.invoke(get, params)
            self.assertEqual(result.exit_code, 1)
            expected = GET_KEY_CONFIG_ERROR.format('.')
            self.assertEqual(result.stderr, expected)

            params = [
                'section.',
                '--filepath', filepath
            ]
            result = runner.invoke(get, params)
            self.assertEqual(result.exit_code, 1)
            expected = GET_KEY_CONFIG_ERROR.format('section.')
            self.assertEqual(result.stderr, expected)

            params = [
                '.option',
                '--filepath', filepath
            ]
            result = runner.invoke(get, params)
            self.assertEqual(result.exit_code, 1)

            expected = GET_KEY_CONFIG_ERROR.format('.option')
            self.assertEqual(result.stderr, expected)

            params = [
                'section.option.suboption',
                '--filepath', filepath
            ]
            result = runner.invoke(get, params)
            self.assertEqual(result.exit_code, 1)
            expected = GET_KEY_CONFIG_ERROR.format('section.option.suboption')
            self.assertEqual(result.stderr, expected)

    def test_invalid_config_files(self):
        """Check whether it raises and error reading invalid configuration files"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            filepath = os.path.join(fs, 'unknown_file.cfg')

            params = [
                'endpoint.host',
                '--filepath', filepath
            ]
            result = runner.invoke(get, params)
            self.assertEqual(result.exit_code, 1)
            expected = NOT_FOUND_FILE_ERROR.format(filepath)
            self.assertEqual(result.stderr, expected)


if __name__ == "__main__":
    unittest.main()
