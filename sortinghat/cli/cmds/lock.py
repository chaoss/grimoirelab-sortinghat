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
def lock(ctx, **extra):
    """Lock and unlock individuals on the registry."""

    pass


@lock.command()
@click.argument('uuid')
@click.pass_obj
def add(client, uuid):
    """Add a lock to an individual so it cannot be modified.

    This command adds a lock to the individual identified
    by <uuid>. Therefore, this and its related entities such
    as identities, enrollments or the profile cannot be
    modified.

    UUID: identifier of the individual which will be locked
    """
    with connect(client) as conn:
        _lock_identity(conn, uuid=uuid)
        display('lock.tmpl', uuid=uuid, unlocked=False)


def _lock_identity(conn, **kwargs):
    """Run a server operation to lock an individual."""

    args = {k: v for k, v in kwargs.items() if v is not None}

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.lock(**args)
    op.lock.uuid()

    result = conn.execute(op)

    return result['data']['lock']['uuid']


@lock.command()
@click.argument('uuid')
@click.pass_obj
def rm(client, uuid):
    """Remove a lock from an individual so it can be modified.

    This command removes a lock from the individual
    identified by <uuid>. Therefore, this and its related
    entities such as identities, enrollments or the profile
    can be modified.

    UUID: identifier of the individual which will be unlocked
    """
    with connect(client) as conn:
        _unlock_individual(conn, uuid=uuid)
        display('lock.tmpl', uuid=uuid, unlocked=True)


def _unlock_individual(conn, **kwargs):
    """Run a server operation to unlock an individual."""

    args = {k: v for k, v in kwargs.items() if v is not None}

    op = Operation(SortingHatSchema.SortingHatMutation)
    op.unlock(**args)
    op.unlock.uuid()

    result = conn.execute(op)

    return result['data']['unlock']['uuid']
