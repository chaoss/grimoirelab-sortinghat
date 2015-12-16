# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Bitergia
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

import argparse
import os.path

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from ..command import Command, CMD_SUCCESS


class Config(Command):
    """Get and set configuration parameters.

    This command gets or sets parameter values from the user configuration
    file. On Linux systems, configuration will be stored in the file '~/.sortinghat'.

    Configuration parameters selected to get/set must follow the schema
    <section>.<option>. Available, configuration parameters can be found in
    CONFIG_OPTIONS dictionary.
    """

    CONFIG_OPTIONS = {
                      'db' : ['user', 'password', 'database', 'host', 'port'],
                      }

    def __init__(self, **kwargs):
        super(Config, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Actions sub-parser
        subparsers = self.parser.add_subparsers(dest='action')

        # Get action parser
        parser_get = subparsers.add_parser('get',
                                           help="Get a configuration parameter")
        parser_get.add_argument('parameter',
                                help="Parameter to get")

        # Set action parser
        parser_set = subparsers.add_parser('set',
                                           help="Set a configuration parameter")
        parser_set.add_argument('parameter',
                                help="Parameter to set")
        parser_set.add_argument('value',
                                help="Value to set")

    @property
    def description(self):
        return """Get and set configuration parameters."""

    @property
    def usage(self):
        return "%(prog)s config get <parameter>\n   or: %(prog)s config set <parameter> <value>"

    def run(self, *args):
        """Get and set configuration parameters.

        This command gets or sets parameter values from the user configuration
        file. On Linux systems, configuration will be stored in the file
        '~/.sortinghat'.
        """
        params = self.parser.parse_args(args)

        config_file = os.path.expanduser('~/.sortinghat')

        if params.action == 'get':
            code = self.get(params.parameter, config_file)
        elif params.action == 'set':
            code = self.set(params.parameter, params.value, config_file)
        else:
            raise RuntimeError("Not get or set action given")

        return code

    def get(self, key, filepath):
        """Get configuration parameter.

        Reads 'key' configuration parameter from the configuration file given
        in 'filepath'. Configuration parameter in 'key' must follow the schema
        <section>.<option> .

        :param key: key to get
        :param filepath: configuration file
        """
        if not filepath:
            raise RuntimeError("Configuration file not given")

        if not self.__check_config_key(key):
            raise RuntimeError("%s parameter does not exists" % key)

        if not os.path.isfile(filepath):
            raise RuntimeError("%s config file does not exist" % filepath)

        section, option = key.split('.')

        config = configparser.SafeConfigParser()
        config.read(filepath)

        try:
            option = config.get(section, option)
            self.display('config.tmpl', key=key, option=option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass

        return CMD_SUCCESS

    def set(self, key, value, filepath):
        """Set configuration parameter.

        Writes 'value' on 'key' to the configuration file given in
        'filepath'. Configuration parameter in 'key' must follow the schema
        <section>.<option> .

        :param key: key to set
        :param value: value to set
        :param filepath: configuration file
        """
        if not filepath:
            raise RuntimeError("Configuration file not given")

        if not self.__check_config_key(key):
            raise RuntimeError("%s parameter does not exists or cannot be set" % key)

        config = configparser.SafeConfigParser()

        if os.path.isfile(filepath):
            config.read(filepath)

        section, option = key.split('.')

        if not section in config.sections():
            config.add_section(section)

        try:
            config.set(section, option, value)
        except TypeError as e:
            raise RuntimeError(str(e))

        try:
            with open(filepath, 'w') as f:
                config.write(f)
        except IOError as e:
            raise RuntimeError(str(e))

        return CMD_SUCCESS

    def __check_config_key(self, key):
        """Check whether the key is valid.

        A valid key has the schema <section>.<option>. Keys supported
        are listed in CONFIG_OPTIONS dict.

        :param key: <section>.<option> key
        """
        try:
            section, option = key.split('.')
        except (AttributeError, ValueError):
            return False

        if not section or not option:
            return False

        return section in Config.CONFIG_OPTIONS and\
            option in Config.CONFIG_OPTIONS[section]
