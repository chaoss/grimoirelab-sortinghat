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
@click.option('--source', default='unknown',
              help="source where the identity comes from")
@click.option('--email',
              help="email address of the identity")
@click.option('--name',
              help="name of the identity")
@click.option('--username',
              help="user name of the identity")
@click.option('--uuid',
              help="associates the new identity to this individual")
@sh_client
def add(ctx, source, email, name, username, uuid, **extra):
    """Add an identity to the registry.

    This command adds a new identity to the registry. By default,
    a new individual will also be created and linked to the
    new identity.

    The registry considers that two identities are distinct when
    any value of the tuple (<source>, <email>, <name>, <username>)
    is different. For example, the identities:

    \b
      * ('scm', 'jsmith@example.com', 'John Smith', 'jsmith')
      * ('mls', 'jsmith@example.com', 'John Smith', 'jsmith')

    will be registered as different identities.

    When <uuid> parameter is set, it creates a new identity that
    will be linked to the individual defined by <uuid>.
    Take into account <uuid> must exist before adding the new
    identity.

    To add a new identity, at least one of <email>, <name>, or
    <username> must be provided. The default value for <source>
    is "unknown".
    """
    with connect(ctx.obj) as conn:
        id_ = _add_identity(conn,
                            source=source, email=email,
                            name=name, username=username,
                            uuid=uuid)

        uuid = uuid or id_
        display('add.tmpl', id_=id_, uuid=uuid)


def _add_identity(conn, **kwargs):
    """Run a server operation to add an identity to the registry."""

    args = {k: v for k, v in kwargs.items() if v is not None}

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.add_identity(**args)
    op.add_identity.uuid()

    result = conn.execute(op)

    return result['data']['addIdentity']['uuid']
