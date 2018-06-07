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

import datetime

from .model import (UniqueIdentity,
                    Identity,
                    Profile,
                    Organization,
                    Domain)


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


def find_organization(session, name):
    """Find an organization.

    Find an organization by its `name` using the given `session`.
    When the organization does not exist the function will
    return `None`.

    :param session: database session
    :param name: name of the organization to find

    :returns: an organization object; `None` when the organization
        does not exist
    """
    organization = session.query(Organization). \
        filter(Organization.name == name).first()

    return organization


def find_domain(session, name):
    """Find a domain.

    Find a domain by its domain name using the given `session`.
    When the domain does not exist the function will
    return `None`.

    :param session: database session
    :param name: name of the domain to find

    :returns: a domain object; `None` when the domain
        does not exist
    """
    domain = session.query(Domain). \
        filter(Domain.domain == name).first()

    return domain


def add_unique_identity(session, uuid):
    """Add a unique identity to the session.

    This function adds a unique identity to the session with
    `uuid` string as unique identifier. This identifier cannot
    be empty or `None`.

    When the unique identity is added, a new empty profile for
    this object is created too.

    As a result, the function returns a new `UniqueIdentity`
    object.

    :param session: database session
    :param uuid: unique identifier for the unique identity

    :return: a new unique identity

    :raises ValueError: when `uuid` is `None` or an empty string
    """
    if uuid is None:
        raise ValueError("'uuid' cannot be None")
    if uuid == '':
        raise ValueError("'uuid' cannot be an empty string")

    uidentity = UniqueIdentity(uuid=uuid)
    uidentity.profile = Profile()
    uidentity.last_modified = datetime.datetime.utcnow()

    session.add(uidentity)

    return uidentity
