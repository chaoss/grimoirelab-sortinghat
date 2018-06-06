# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2018 Bitergia
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

from .model import UniqueIdentity, Identity, Organization


def find_unique_identity(session, uuid):
    """Find a unique identity.

    Find a unique identity by its UUID using the given `session`.
    When the unique identity does not exist the function will
    return `None`.

    :param session: database session
    :param uuid: id of the unique identity to find

    :returns: a unique identity object; `None` when the unique
        identity does not exist
    """
    uidentity = session.query(UniqueIdentity). \
        filter(UniqueIdentity.uuid == uuid).first()

    return uidentity


def find_identity(session, id_):
    """Find an identity.

    Find an identity by its ID using the given `session`.
    When the identity does not exist the function will
    return `None`.

    :param session: database session
    :param id_: id of the identity to find

    :returns: an identity object; `None` when the identity
        does not exist
    """
    identity = session.query(Identity). \
        filter(Identity.id == id_).first()

    return identity
