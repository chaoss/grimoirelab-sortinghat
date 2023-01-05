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


@click.option('--config', envvar='SORTINGHAT_CONFIG',
              help="Configuration module in Python path syntax, e.g. sortinghat.settings.")
@click.option('--dev', 'devel', is_flag=True, default=False,
              help="Run the service in developer mode.")
@click.option('--no-auth', 'no_auth', is_flag=True, default=False,
              help="Run the service without authentication.")
@click.command()
def sortinghatd(config, devel, no_auth):
    """Starts the SortingHat server.

    SortingHat allows to manage the multiple identities that individuals
    can have across software development data sources. The server provides
    an API to perform all the operations.

    To run the server, you will need to pass a configuration file module
    using Python path syntax (e.g. sortinghat.settings). Take into account
    the module should be accessible by your PYTHON_PATH.

    By default, the server runs a WSGI app because in production it should
    be run with a reverse proxy. If you activate the '--dev' flag, a HTTP
    server will be run instead.
    """
    env = os.environ

    if config:
        env['UWSGI_ENV'] = f"DJANGO_SETTINGS_MODULE={config}"
    else:
        raise click.ClickException(
            "Configuration file not given. "
            "Set it with '--config' option "
            "or 'SORTINGHAT_CONFIG' env variable."
        )

    if devel:
        env['SORTINGHAT_DEBUG'] = 'true'

        from django.conf import settings

        env['DJANGO_SETTINGS_MODULE'] = config
        env['UWSGI_HTTP'] = env.get('SORTINGHAT_HTTP_DEV', "127.0.0.1:8000")
        env['UWSGI_STATIC_MAP'] = settings.STATIC_URL + "=" + settings.STATIC_ROOT
    else:
        env['UWSGI_HTTP'] = ''

    env['UWSGI_MODULE'] = "sortinghat.app.wsgi:application"
    env['UWSGI_SOCKET'] = "0.0.0.0:9314"

    # These options shouldn't be modified
    env['UWSGI_MASTER'] = "true"
    env['UWSGI_ENABLE_THREADS'] = "true"
    env['UWSGI_LAZY_APPS'] = "true"
    env['UWSGI_SINGLE_INTERPRETER'] = "true"

    os.execvp("uwsgi", ("uwsgi",))


if __name__ == "__main__":
    sortinghatd()
