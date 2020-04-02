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


@click.group()
@sh_client_cmd_options
@sh_client
def lock(ctx, user, password, host, port, server_path, disable_ssl):
    """Lock and unlock unique identities on the registry."""

    pass


@lock.command()
@click.argument('uuid')
@click.pass_obj
def add(client, uuid):
    """Add a lock to a unique identity so it cannot be modified.

    This command adds a lock to the unique identity identified
    by <uuid>. Therefore, this and its related entities such
    as identities, enrollments or the profile cannot be
    modified.

    UUID: identifier of the unique identity which will be locked
    """
    with connect(client) as conn:
        _lock_identity(conn, uuid=uuid)
        display('lock.tmpl', uuid=uuid, unlocked=False)


def _lock_identity(conn, **kwargs):
    """Run a server operation to lock a unique identity."""

    args = {k: v for k, v in kwargs.items() if v is not None}

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.lock_identity(**args)
    op.lock_identity.uuid()

    result = conn.execute(op)

    return result['data']['lockIdentity']['uuid']


@lock.command()
@click.argument('uuid')
@click.pass_obj
def rm(client, uuid):
    """Remove a lock from a unique identity so it can be modified.

    This command removes a lock from the unique identity
    identified by <uuid>. Therefore, this and its related
    entities such as identities, enrollments or the profile
    can be modified.

    UUID: identifier of the unique identity which will be unlocked
    """
    with connect(client) as conn:
        _unlock_identity(conn, uuid=uuid)
        display('lock.tmpl', uuid=uuid, unlocked=True)


def _unlock_identity(conn, **kwargs):
    """Run a server operation to unlock a unique identity."""

    args = {k: v for k, v in kwargs.items() if v is not None}

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.unlock_identity(**args)
    op.unlock_identity.uuid()

    result = conn.execute(op)

    return result['data']['unlockIdentity']['uuid']
