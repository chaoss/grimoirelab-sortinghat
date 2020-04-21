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

import click

from sgqlc.operation import Operation

from ..client import SortingHatSchema
from ..utils import (connect,
                     display,
                     sh_client_cmd_options,
                     sh_client)


@click.command()
@sh_client_cmd_options
@click.option('--name',
              help="Name of the individual.")
@click.option('--email',
              help="Email address of the individual.")
@click.option('--gender',
              help="Gender of the individual.")
@click.option('--country',
              help="ISO_3166-1 country code.")
@click.option('--bot/--no-bot', default=None,
              help="Set/unset the individual as a bot.")
@click.argument('uuid')
@sh_client
def profile(ctx, uuid, name, email, gender, country, bot, **extra):
    """Edit profile information.

    This command updates the profile information of the unique
    identity <uuid>. It is possible to edit, among other information,
    the name, the email, the country, or to define whether a unique
    identity is a bot or not.

    When only <uuid> is provided, the command will display the
    profile of that individual.

    UUID: identifier of the individual
    """
    with connect(ctx.obj) as conn:
        indv = _update_profile(conn, uuid, email=email,
                               name=name, gender=gender,
                               country_code=country,
                               is_bot=bot)
        display('profile.tmpl', indv=indv)


def _update_profile(conn, uuid, **kwargs):
    """Run a server operation to update the profile of an individual."""

    args = {k: v for k, v in kwargs.items() if v is not None}
    pd = SortingHatSchema.ProfileInputType(**args)

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.update_profile(uuid=uuid, data=pd)
    op.update_profile().individual().mk()
    op.update_profile().individual().profile().__fields__('name', 'email',
                                                          'gender', 'is_bot')
    op.update_profile().individual().profile().country().__fields__('code', 'name')

    result = conn.execute(op)

    data = op + result

    return data.update_profile.individual
