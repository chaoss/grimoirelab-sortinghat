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
@click.argument('uuid', nargs=1, required=False)
@sh_client
def show(ctx, uuid, **extra):
    """Show information about unique identities.

    This command displays, by default, information about all
    the unique identities stored in the registry. The information
    shown includes identities and enrollments.

    When <uuid> is given, it will show information about the unique
    identity related to <uuid>.

    UUID: unique identity to show
    """
    with connect(ctx.obj) as conn:
        for uidentities in _fetch_unique_identities(conn, uuid=uuid):
            display('show.tmpl', nl=False,
                    uidentities=uidentities)


def _fetch_unique_identities(client, uuid=None):
    """Run a server operation to get the list of unique identities."""

    page = 1
    paginate = True

    while paginate:
        op = _generate_uidentities_operation(page, uuid)

        result = client.execute(op)

        data = op + result
        paginate = data.uidentities.page_info.has_next
        page += 1
        yield data.uidentities.entities


def _generate_uidentities_operation(page, uuid):
    """Define an operation to get the list of organizations."""

    args = {
        'page': page
    }
    if uuid:
        args['filters'] = {'uuid': uuid}

    op = Operation(SortingHatSchema.Query)
    op.uidentities(**args)

    # Select page information
    op.uidentities().page_info.has_next()

    # Select identities information
    uidentity = op.uidentities().entities()

    uidentity.uuid()
    uidentity.is_locked()
    uidentity.profile().__fields__('name', 'email',
                                   'gender', 'is_bot')
    uidentity.profile().country().__fields__('code', 'name')

    uidentity.identities().__fields__('id', 'email', 'name', 'username', 'source')
    uidentity.enrollments().__fields__('start', 'end')
    uidentity.enrollments().organization().name()

    return op
