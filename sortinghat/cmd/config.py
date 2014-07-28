# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Bitergia
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

import ConfigParser
import os.path

from sortinghat.command import Command


class Config(Command):
    """Set and get configuration parameters"""

    CONFIG_OPTIONS = {
                      'db' : ['user', 'password', 'database', 'host', 'port'],
                      }

    def __init__(self, **kwargs):
        super(Command, self).__init__(**kwargs)

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

        config = ConfigParser.SafeConfigParser()

        if os.path.isfile(filepath):
            config.read(filepath)

        section, option = key.split('.')

        if not section in config.sections():
            config.add_section(section)

        try:
            config.set(section, option, value)
        except TypeError, e:
            raise RuntimeError(str(e))

        try:
            with open(filepath, 'wb') as f:
                config.write(f)
        except IOError, e:
            raise RuntimeError(str(e))

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

        config = ConfigParser.SafeConfigParser()
        config.read(filepath)

        try:
            option = config.get(section, option)
            print key, option
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            pass

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

