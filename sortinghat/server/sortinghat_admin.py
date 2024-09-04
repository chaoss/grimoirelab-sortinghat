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

import getpass
import logging
import os
import sys

import click

import importlib_resources

from django.contrib.auth import get_user_model
from django.core.wsgi import get_wsgi_application
from django.core import management, exceptions
from django.db import IntegrityError
from django.conf import settings


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
    _setup(no_interactive=no_interactive, only_ui=only_ui)


@click.command()
@click.argument('username')
@click.argument('header')
@click.argument('tenant')
def set_user_tenant(username, header, tenant):
    """Assign a user and header to a specific tenant"""

    from sortinghat.core.models import Tenant

    try:
        user = get_user_model().objects.get(username=username)
    except exceptions.ObjectDoesNotExist:
        raise click.ClickException(f"User '{username}' does not exist.")

    Tenant.objects.update_or_create(user=user, header=header,
                                    defaults={'database': tenant})
    click.echo(f"User '{username}' at '{header}' assigned to '{tenant}'")


def _setup(no_interactive, only_ui):
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

    for database in settings.DATABASES:
        _create_database(database=database)
        _setup_database(database=database)
        if database == 'default':
            _setup_database_superuser(no_interactive, database=database)
            _setup_group_permissions(database=database)

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
        for database in settings.DATABASES:
            _setup_database(database=database)

    _install_static_files()
    _setup_group_permissions(database='default')
    _migrate_users_permissions()

    click.secho("SortingHat upgrade completed", fg='bright_cyan')


@click.command()
@click.option('--no-interactive', is_flag=True, default=False,
              help="Run the command in no interactive mode.")
def migrate_old_database(no_interactive):
    """Migrate SortingHat 0.7 database schema to 0.8 and all the data"""

    import MySQLdb
    from .utils.create_sh_0_7_fixture import create_sh_fixture

    def _database_table_exists(db_params, table):
        try:
            MySQLdb.connect(
                user=db_params['USER'],
                password=db_params['PASSWORD'],
                host=db_params['HOST'],
                port=int(db_params['PORT']),
                database=db_params['NAME']
            ).cursor().execute(
                f"SELECT * FROM {table} LIMIT 0;"
            )
            return True
        except MySQLdb.DatabaseError as exc:
            click.echo(exc)
            return False

    def _backup_tables(db_params, from_db, to_db):
        try:
            cursor = MySQLdb.connect(
                user=db_params['USER'],
                password=db_params['PASSWORD'],
                host=db_params['HOST'],
                port=int(db_params['PORT'])
            ).cursor()

            cursor.execute(f"SHOW TABLES FROM {from_db};")
            for (table,) in cursor:
                click.echo(f'Backup table {table}')
                cursor.execute(
                    f"RENAME TABLE {from_db}.{table} TO {to_db}.{table};"
                )
        except MySQLdb.DatabaseError as exc:
            msg = f"Error in backup database '{from_db}': {exc}."
            raise click.ClickException(msg)

    for database in settings.DATABASES:
        db_params = settings.DATABASES[database]

        if not _database_table_exists(db_params, 'matching_blacklist'):
            click.echo("SortingHat database schema is >= 0.8. Done.")
            return

        click.secho("Migrate 0.7.X SortingHat database schema ...", fg='bright_cyan')

        backup_db_name = f"{db_params['NAME']}_backup"

        with open('/tmp/sortinghat_0_7_fixture.json', 'w') as output_fh:
            create_sh_fixture(db_host=db_params['HOST'],
                              db_port=int(db_params['PORT']),
                              db_user=db_params['USER'],
                              db_password=db_params['PASSWORD'],
                              database=db_params['NAME'],
                              output_fh=output_fh)

        _create_database(database=database, db_name=backup_db_name)
        _backup_tables(db_params, db_params['NAME'], backup_db_name)
        _setup(no_interactive, False)
        management.call_command('loaddata', '/tmp/sortinghat_0_7_fixture.json', database=database)

    click.echo("Migration completed!")


@click.command()
@click.option('--username', help="Specifies the login for the user.")
@click.option('--is-admin', is_flag=True, default=False,
              help="Specifies if the user is superuser.")
@click.option('--no-interactive', is_flag=True, default=False,
              help="Run the command in no interactive mode.")
def create_user(username, is_admin, no_interactive):
    """Create a new user given a username and password"""

    try:
        if no_interactive:
            # Use password from environment variable, if provided.
            password = os.environ.get('SORTINGHAT_USER_PASSWORD')
            if not password or not password.strip():
                raise click.ClickException("Password cannot be empty.")
            # Use username from environment variable, if not provided in options.
            if username is None:
                username = os.environ.get('SORTINGHAT_USER_USERNAME')
            error = _validate_username(username)
            if error:
                click.ClickException(error)
        else:
            # Get username
            if username is None:
                username = input("Username: ")
            error = _validate_username(username)
            if error:
                click.ClickException(error)
            # Prompt for a password
            password = getpass.getpass()
            password2 = getpass.getpass('Password (again): ')
            if password != password2:
                raise click.ClickException("Error: Your passwords didn't match.")
            if password.strip() == '':
                raise click.ClickException("Error: Blank passwords aren't allowed.")

        extra_fields = {}
        if is_admin:
            extra_fields['is_staff'] = True
            extra_fields['is_superuser'] = True

        get_user_model().objects.create_user(username=username,
                                             password=password,
                                             **extra_fields)

        click.echo("User created successfully.")
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled.")
        sys.exit(1)
    except IntegrityError:
        click.echo(f"User '{username}' already exists.")
        sys.exit(1)


@click.command()
@click.argument('username')
@click.argument('permission_group')
@click.option('--tenant', default='default')
def set_user_permissions(username, permission_group, tenant):
    """Assign a user to a specific permission group"""

    try:
        management.call_command('set_permissions', username, permission_group, database=tenant)
    except management.CommandError as exc:
        click.echo(exc)
        sys.exit(1)

    click.echo(f"User '{username}' assigned to '{permission_group}'.")


def _create_database(database='default', db_name=None):
    """Create an empty database."""

    import MySQLdb

    db_params = settings.DATABASES[database]
    db_name = db_name if db_name else db_params['NAME']

    click.secho("## SortingHat database creation\n", fg='bright_cyan')

    try:
        cursor = MySQLdb.connect(
            user=db_params['USER'],
            password=db_params['PASSWORD'],
            host=db_params['HOST'],
            port=int(db_params['PORT'])
        ).cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {db_name} "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_520_ci;"
        )
    except MySQLdb.DatabaseError as exc:
        msg = f"Error creating database '{db_name}' for '{database}': {exc}."
        raise click.ClickException(msg)

    click.echo(f"SortingHat database '{db_name}' for '{database}' created.\n")


def _setup_database(database='default'):
    """Apply migrations and fixtures to the database."""

    click.secho(f"## SortingHat database setup for {database}\n", fg='bright_cyan')

    management.call_command('migrate', database=database)

    with importlib_resources.path('sortinghat.core.fixtures', 'countries.json') as p:
        fixture_countries_path = p

    management.call_command('loaddata', fixture_countries_path, database=database)

    click.echo()


def _setup_database_superuser(no_interactive=False, database='default'):
    """Create database superuser."""

    click.secho(f"## SortingHat superuser configuration for {database}\n", fg='bright_cyan')

    env = os.environ
    kwargs = {}

    if no_interactive:
        env['DJANGO_SUPERUSER_USERNAME'] = env['SORTINGHAT_SUPERUSER_USERNAME']
        env['DJANGO_SUPERUSER_PASSWORD'] = env['SORTINGHAT_SUPERUSER_PASSWORD']
        env['DJANGO_SUPERUSER_EMAIL'] = 'noreply@localhost'
        kwargs['interactive'] = False

    kwargs['database'] = database
    management.call_command('createsuperuser', **kwargs)


def _setup_group_permissions(database='default'):
    """Create permission groups."""

    click.secho(f"## SortingHat groups creation for {database}\n", fg='bright_cyan')

    management.call_command('create_groups', database=database)

    click.echo("SortingHat groups created.\n")


def _migrate_users_permissions():
    """Migrate permissions for users from the previous version"""

    from sortinghat.core.models import Tenant
    from django.contrib.auth.models import Group

    users = get_user_model().objects.all()

    if settings.MULTI_TENANT:
        for user in users:
            group = user.groups.first()
            if not group:
                continue
            Tenant.objects.filter(user=user).update(perm_group=group.name)
            click.echo(f"Permissions for '{user}' updated to '{group.name}'.")
            user.groups.clear()
    else:
        for user in users:
            group = user.groups.first()
            if group:
                continue
            if user.is_superuser:
                group = Group.objects.get(name='admin')
            else:
                group = Group.objects.get(name='user')
            click.echo(f"Permissions for '{user}' updated to '{group.name}'.")
            user.groups.set([group.id])


def _install_static_files():
    """Collect static files and installed them."""

    click.secho('## SortingHat static files installation\n',
                fg='bright_cyan')

    management.call_command('collectstatic', clear=True,
                            interactive=False)

    click.echo()


def _validate_username(username):
    """Check if the username is valid and return the error"""

    if not username:
        return "Username cannot be empty."
    username_field = get_user_model()._meta.get_field(get_user_model().USERNAME_FIELD)
    try:
        username_field.clean(username, None)
    except exceptions.ValidationError as e:
        return '; '.join(e.messages)


sortinghat_admin.add_command(setup)
sortinghat_admin.add_command(upgrade)
sortinghat_admin.add_command(migrate_old_database)
sortinghat_admin.add_command(create_user)
sortinghat_admin.add_command(set_user_tenant)
sortinghat_admin.add_command(set_user_permissions)
