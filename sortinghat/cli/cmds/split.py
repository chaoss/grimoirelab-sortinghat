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
@click.argument('uuid', nargs=-1, required=True)
@sh_client
def split(ctx, uuid, **extra):
    """Separate one or more identities from their corresponding individuals.

    This command separates a list of identities, creating a unique
    identity for each one.

    A profile for each new individual will be created using
    the 'name' and 'email' fields of the parent individual.

    Nor the enrollments or the profile from any parent unique
    identity of the input identities are modified.

    When a given identity <uuid> is equal to the <uuid> of its
    parent individual, there will be no effect. Also,
    take into account all identities must exist before splitting
    them. Otherwise, the command will abort the operation.

    UUID: identities to split
    """
    with connect(ctx.obj) as conn:
        uuids = sorted(list(set(uuid)))
        result = _unmerge_identities(conn, uuids=uuids)
        display('split.tmpl', nl=False, uuids=result)


def _unmerge_identities(conn, **kwargs):
    """Run a server operation to unmerge identities."""

    args = {k: v for k, v in kwargs.items() if v is not None}

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.unmerge_identities(**args)
    op.unmerge_identities.uuids()

    result = conn.execute(op)

    return result['data']['unmergeIdentities']['uuids']
