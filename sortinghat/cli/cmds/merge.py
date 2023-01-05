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
                     sh_client_cmd_options,
                     sh_client)


@click.command()
@sh_client_cmd_options
@click.argument('to_uuid')
@click.argument('from_uuid', nargs=-1)
@sh_client
def merge(ctx, to_uuid, from_uuid, **extra):
    """Merge one or more individuals into another.

    This command merges a list of individuals into <to_uuid>.
    Identities and enrollments related to each <from_uuid> will be
    assigned to <to_uuid>.

    Duplicated enrollments will be also removed from the registry
    while overlapped enrollments will be merged.

    The profile in <to_uuid> will be updated if any of its fields
    is empty.

    Take into account all identities must exist before merging
    them. Also any identifier <from_uuid> must be different of
    <to_uuid>. The same individual cannot be merged with
    itself. Otherwise, the command will abort the operation.

    TO_UUID: individual where FROM_UUIDs will be merged

    FROM_UUID: individual to merge
    """
    with connect(ctx.obj) as conn:
        _merge_individuals(conn, from_uuids=list(from_uuid),
                           to_uuid=to_uuid)


def _merge_individuals(conn, **kwargs):
    """Run a server operation to merge individuals."""

    args = {k: v for k, v in kwargs.items() if v is not None}

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.merge(**args)
    op.merge.uuid()

    result = conn.execute(op)

    return result['data']['merge']['uuid']
