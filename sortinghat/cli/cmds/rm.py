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
@click.argument('uuid')
@sh_client
def rm(ctx, uuid, **extra):
    """Remove an identity from the registry.

    This command removes from the registry the identity whose
    identifier matches with <uuid>.

    When the <uuid> also belongs to an individual, this entry
    and those identities linked to it will be removed too.

    UUID: identifier of the identity to remove
    """
    with connect(ctx.obj) as conn:
        rm_id = _remove_identity(conn, uuid=uuid)
        display('rm.tmpl', uuid=uuid, is_id_removed=rm_id)


def _remove_identity(conn, **kwargs):
    """Run a server operation to remove an identity from the registry."""

    args = {k: v for k, v in kwargs.items() if v is not None}

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.delete_identity(**args)
    op.delete_identity.individual().mk()

    result = conn.execute(op)

    individual = result['data']['deleteIdentity']['individual']

    return individual is not None
