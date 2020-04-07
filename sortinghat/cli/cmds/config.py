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

import configparser
import os.path

import click

from ..utils import display


CONFIG_OPTIONS = {
    'endpoint': {
        'user': '',
        'password': '',
        'host': 'localhost',
        'port': '9314',
        'path': '/',
        'ssl': 'true',
    }
}

SORTINGHAT_CFG_DIR_NAME = '~/.sortinghat'
SORTINGHAT_CFG_FILE_NAME = 'sortinghat.cfg'


@click.group()
def config():
    """Configure SortingHat client.

    This command gets or sets parameters from/to the client
    configuration file.

    On Unix systems, configuration will be stored by default
    under the file '~/.sortinghat/sortinghat.cfg'.

    Configuration parameters selected to get/set must follow
    the schema "<section>.<option>" (e.g 'endpoint.host').
    """
    pass


@config.command()
@click.option('--filepath',
              help="Path to the configuration file.")
@click.option('--overwrite', is_flag=True,
              help="Force to replace an existing configuration file.")
def init(filepath, overwrite):
    """Create a configuration file with default parameters.

    This command will create a configuration file under <filepath>
    using default configuration parameters. When <filepath> is not
    given the default location for the configuration file will be
    used instead.

    The configuration file must not exist. Otherwise the command
    will return with an error. Use the option '--overwrite' to force
    to replace the existing file.
    """
    if not filepath:
        dirpath = os.path.expanduser(SORTINGHAT_CFG_DIR_NAME)
        os.makedirs(dirpath, exist_ok=True)
        config_file = os.path.join(dirpath, SORTINGHAT_CFG_FILE_NAME)
    else:
        config_file = filepath

    if os.path.isfile(config_file) and not overwrite:
        msg = ("Configuration file {} already exists. "
               "Use '--overwrite' to replace it.").format(config_file)
        raise click.ClickException(msg)

    cfg = configparser.ConfigParser()
    cfg.read_dict(CONFIG_OPTIONS)

    try:
        with open(config_file, 'w') as f:
            cfg.write(f)
    except IOError as e:
        raise click.FileError(config_file, hint=str(e))


@config.command()
@click.argument('key')
@click.option('--filepath',
              help="Path to the configuration file.")
def get(key, filepath):
    """Get configuration parameters.

    This command reads <key> configuration parameter from the
    configuration file given in <filepath>. When <filepath>
    is not given, the command will use the default configuration
    file.

    Configuration parameter in <key> must follow the pattern
    "<section>.<option>" (e.g 'endpoint.host').

    KEY: configuration parameter
    """
    if not filepath:
        dirpath = os.path.expanduser(SORTINGHAT_CFG_DIR_NAME)
        config_file = os.path.join(dirpath, SORTINGHAT_CFG_FILE_NAME)
    else:
        config_file = filepath

    if not _check_config_key(key):
        msg = "{} config parameter is not supported".format(key)
        raise click.ClickException(msg)

    if not os.path.isfile(config_file):
        raise click.FileError(config_file, hint="file does not exist")

    section, option = key.split('.')

    cfg = configparser.ConfigParser()
    cfg.read(config_file)

    try:
        option = cfg.get(section, option)
        display('config.tmpl', key=key, option=option)
    except (configparser.NoSectionError, configparser.NoOptionError):
        pass


@config.command()
@click.argument('key')
@click.argument('value')
@click.option('--filepath',
              help="Path to the configuration file.")
def set(key, value, filepath):
    """Set configuration parameter.

    This command writes <value> on <key> parameter in the
    configuration file given in <filepath>. When <filepath>
    is not given, the command will use the default configuration
    file.

    Configuration parameter in <key> must follow the pattern
    "<section>.<option>" (e.g 'endpoint.host').

    KEY: configuration parameter

    VALUE: value for the configuration parameter
    """
    if not filepath:
        dirpath = os.path.expanduser(SORTINGHAT_CFG_DIR_NAME)
        os.makedirs(dirpath, exist_ok=True)
        config_file = os.path.join(dirpath, SORTINGHAT_CFG_FILE_NAME)
    else:
        config_file = filepath

    if not _check_config_key(key):
        msg = "{} config parameter is not supported".format(key)
        raise click.ClickException(msg)

    cfg = configparser.ConfigParser()

    if os.path.isfile(config_file):
        cfg.read(config_file)

    section, option = key.split('.')

    if section not in cfg.sections():
        cfg.add_section(section)

    try:
        cfg.set(section, option, value)
    except TypeError as e:
        raise click.ClickException(str(e))

    try:
        with open(config_file, 'w') as f:
            cfg.write(f)
    except IOError as e:
        raise click.FileError(config_file, hint=str(e))


def _check_config_key(key):
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

    return section in CONFIG_OPTIONS and\
        option in CONFIG_OPTIONS[section]
