# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2021 Bitergia
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

import os

import click

from django.core.wsgi import get_wsgi_application
from django.core import management


@click.option('--config', envvar='SORTINGHAT_CONFIG',
              help="Configuration module in Python path syntax, e.g. sortinghat.settings.")
@click.argument('queues', nargs=-1)
@click.command()
def sortinghatw(config, queues):
    """Starts a SortingHat worker.

    Workers can execute long running jobs such as recommendations
    or affiliations. Workers get jobs from the a list of queues,
    executing one job at a time. This list of queues are passed as
    a list of arguments to this command, and they need to be defined
    in the configuration file. If the list is not given, workers
    will listed for jobs on all the queues defined in the configuration.

    The configuration is defined by a configuration file module using
    Python path syntax (e.g. sortinghat.settings). Take into account
    the module should be accessible by your PYTHONPATH env variable.

    QUEUES: read jobs from this list; if empty, reads from all the
    defined queues in the configuration file.
    """
    env = os.environ

    if config:
        env['DJANGO_SETTINGS_MODULE'] = config
    else:
        raise click.ClickException(
            "Configuration file not given. "
            "Set it with '--config' option "
            "or 'SORTINGHAT_CONFIG' env variable."
        )

    _ = get_wsgi_application()

    try:
        management.call_command('rqworker', *queues, with_scheduler=True)
    except KeyError as e:
        raise click.ClickException(f"Queue '{e.args[0]}' not found")
