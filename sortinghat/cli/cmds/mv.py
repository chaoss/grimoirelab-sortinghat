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
@click.argument('from_uuid')
@click.argument('to_uuid')
@sh_client
def mv(ctx, from_uuid, to_uuid, **extra):
    """Move an identity to an individual.

    This command shifts the identity identified by <from_uuid> to
    the individual identified by <to_uuid>.

    When <to_uuid> is already related to <from_uuid>, the command does
    not have any effect.

    In the case of <from_uuid> and <to_uuid> have equal values and the
    individual does not exist, a new individual will be
    created and the identity will be moved to it.

    When <from_uuid> exists also as an individual, this command will
    fail as this identity cannot be moved.

    FROM_UUID: identifier of the identity to move

    TO_UUID: identifier of the individual where <from_uuid> will be moved
    """
    with connect(ctx.obj) as conn:
        _move_identity(conn, from_uuid=from_uuid,
                       to_uuid=to_uuid)

        display('mv.tmpl', from_uuid=from_uuid, to_uuid=to_uuid)


def _move_identity(conn, **kwargs):
    """Run a server operation to move an identity."""

    args = {k: v for k, v in kwargs.items() if v is not None}

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.move_identity(**args)
    op.move_identity.uuid()

    result = conn.execute(op)

    return result['data']['moveIdentity']['uuid']
