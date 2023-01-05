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


from .cmds.add import add
from .cmds.config import (config,
                          CONFIG_OPTIONS,
                          SORTINGHAT_CFG_FILE_NAME,
                          SORTINGHAT_CFG_DIR_NAME)
from .cmds.countries import countries
from .cmds.enroll import enroll
from .cmds.lock import lock
from .cmds.merge import merge
from .cmds.mv import mv
from .cmds.orgs import orgs
from .cmds.profile import profile
from .cmds.rm import rm
from .cmds.split import split
from .cmds.show import show
from .cmds.withdraw import withdraw


@click.group()
@click.option('-c', '--config', 'config_file', type=click.Path(),
              help="Use this configuration file.")
@click.pass_context
def sortinghat(ctx, config_file):
    """A tool to manage identities."""

    if not config_file:
        config_file = os.path.expanduser(SORTINGHAT_CFG_DIR_NAME)
        config_file = os.path.join(config_file, SORTINGHAT_CFG_FILE_NAME)
        if not os.path.isfile(config_file):
            config_file = None

    if config_file:
        try:
            ctx.obj = _read_config_file(config_file)
        except Exception as e:
            raise click.ClickException(str(e))
    else:
        ctx.obj = {}


# Add commands to the root command
sortinghat.add_command(config)
sortinghat.add_command(add)
sortinghat.add_command(rm)
sortinghat.add_command(profile)
sortinghat.add_command(mv)
sortinghat.add_command(enroll)
sortinghat.add_command(withdraw)
sortinghat.add_command(merge)
sortinghat.add_command(split)
sortinghat.add_command(lock)
sortinghat.add_command(show)
sortinghat.add_command(orgs)
sortinghat.add_command(countries)


def _read_config_file(filepath):
    """Read SortingHat configuration file."""

    cfg = configparser.ConfigParser()
    cfg.read_dict(CONFIG_OPTIONS)
    cfg.read(filepath)

    opts = {}

    for key in CONFIG_OPTIONS.keys():
        # Set group defaults
        opts = {**opts, **CONFIG_OPTIONS[key]}

        # Set config file parameters
        if key in cfg.sections():
            opts = {**opts, **dict(cfg.items(key))}

    return opts
