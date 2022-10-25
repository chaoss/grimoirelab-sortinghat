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

import logging
import os

import click

import importlib_resources

from django.core.wsgi import get_wsgi_application
from django.core import management


logger = logging.getLogger('main')


@click.group()
@click.option('--config', envvar='SORTINGHAT_CONFIG',
              help="Config module in Python path syntax, e.g. sortinghat.config.settings.")
def sortinghat_admin(config):
    """SortingHat server administration tool.

    This swiss army knife tool allows to run administrative tasks to
    configure, initialize, or update the service.

    To run the tool you will need to pass a configuration file module
    using Python path syntax (e.g. sortinghat.config.settings).
    Take into account the module should be accessible by your PYTHON_PATH.
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


@click.command()
@click.option('--no-interactive', is_flag=True, default=False,
              help="Run the command in no interactive mode.")
@click.option('--only-ui', is_flag=True, default=False,
              help="Configure only the UI.")
def setup(no_interactive, only_ui):
    """Run initialization tasks to configure the service.

    It will setup the uid, the database structure, and create a user
    with admin privileges for you.

    To cancel the interactive mode, use the env variables
    'SORTINGHAT_SUPERUSER_USERNAME' and 'SORTINGHAT_SUPERUSER_PASSWORD'.
    It the flag 'no-interactive' was given, these environment
    variables are mandatory.
    """
    env = os.environ
    env_vars = False

    if 'SORTINGHAT_SUPERUSER_USERNAME' in env:
        env_vars = True
    if 'SORTINGHAT_SUPERUSER_PASSWORD' in env:
        if not env_vars:
            msg = (
                "Set both SORTINGHAT_SUPERUSER_USERNAME "
                "and SORTINGHAT_SUPERUSER_PASSWORD env variables "
                "to run the no-interactive mode. "
                "Only one variable was set."
            )
            raise click.ClickException(msg)
        env_vars = True
        no_interactive = True

    # Env vars are mandatory in no interactive mode
    if no_interactive and not env_vars:
        msg = (
            "Set both SORTINGHAT_SUPERUSER_USERNAME "
            "and SORTINGHAT_SUPERUSER_PASSWORD env variables "
            "to run the mode no-interactive mode. "
        )
        raise click.ClickException(msg)

    click.secho("Configuring SortingHat service...\n", fg='bright_cyan')

    _install_static_files()

    if only_ui:
        click.secho("SortingHat UI deployed. Exiting.", fg='bright_cyan')
        return

    _create_database()
    _setup_database()
    _setup_database_superuser(no_interactive)
    _setup_group_permissions()

    click.secho("\nSortingHat configuration completed", fg='bright_cyan')


@click.command()
@click.option('--no-database', is_flag=True, default=False,
              help="Do not update the database.")
def upgrade(no_database):
    """Run pending configuration operations to keep the service up-to-date.

    It allows to run configuration operations in order to update
    the service to its last version. For example, it will run
    migrations or load pre-defined data.
    """
    click.secho("Upgrading SortingHat service...\n", fg='bright_cyan')

    update_database = not no_database

    if update_database:
        _setup_database()

    _install_static_files()

    click.secho("SortingHat upgrade completed", fg='bright_cyan')


def _create_database():
    """Create an empty database."""

    import MySQLdb
    from django.conf import settings

    db_params = settings.DATABASES['default']
    database = db_params['NAME']

    click.secho("## SortingHat database creation\n", fg='bright_cyan')

    try:
        cursor = MySQLdb.connect(
            user=db_params['USER'],
            password=db_params['PASSWORD'],
            host=db_params['HOST'],
            port=db_params['PORT']
        ).cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {database} "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci;"
        )
    except MySQLdb.DatabaseError as exc:
        msg = f"Error creating database '{database}': {exc}."
        raise click.ClickException(msg)

    click.echo(f"SortingHat database '{database}' created.\n")


def _setup_database():
    """Apply migrations and fixtures to the database."""

    click.secho("## SortingHat database setup\n", fg='bright_cyan')

    management.call_command('migrate')

    with importlib_resources.path('sortinghat.core.fixtures', 'countries.json') as p:
        fixture_countries_path = p

    management.call_command('loaddata', fixture_countries_path)

    click.echo()


def _setup_database_superuser(no_interactive=False):
    """Create database superuser."""

    click.secho("## SortingHat superuser configuration\n", fg='bright_cyan')

    env = os.environ
    kwargs = {}

    if no_interactive:
        env['DJANGO_SUPERUSER_USERNAME'] = env['SORTINGHAT_SUPERUSER_USERNAME']
        env['DJANGO_SUPERUSER_PASSWORD'] = env['SORTINGHAT_SUPERUSER_PASSWORD']
        env['DJANGO_SUPERUSER_EMAIL'] = 'noreply@localhost'
        kwargs['interactive'] = False

    management.call_command('createsuperuser', **kwargs)


def _setup_group_permissions():
    """Create permission groups."""

    click.secho("## SortingHat groups creation\n", fg='bright_cyan')

    management.call_command('create_groups')

    click.echo("SortingHat groups created.\n")


def _install_static_files():
    """Collect static files and installed them."""

    click.secho('## SortingHat static files installation\n',
                fg='bright_cyan')

    management.call_command('collectstatic', clear=True,
                            interactive=False)

    click.echo()


sortinghat_admin.add_command(setup)
sortinghat_admin.add_command(upgrade)
