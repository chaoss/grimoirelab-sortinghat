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


def add_identity(session, uidentity, identity_id, source,
                 name=None, email=None, username=None):
    """Add an identity to the session.

    This function adds a new identity to the session using
    `identity_id` as its identifier. The new identity will
    also be linked to the unique identity object of `uidentity`.

    Neither the values given to `identity_id` nor to `source` can
    be `None` or empty. Moreover, `name`, `email` or `username`
    parameters need a non empty value.

    As a result, the function returns a new `Identity` object.

    :param session: database session
    :param uidentity: links the new identity to this unique identity object
    :param identity_id: identifier for the new identity
    :param source: data source where this identity was found
    :param name: full name of the identity
    :param email: email of the identity
    :param username: user name used by the identity

    :return: a new identity

    :raises ValueError: when `identity_id` and `source` are `None` or empty;
        when all of the data parameters are `None` or empty.
    """
    if identity_id is None:
        raise ValueError("'identity_id' cannot be None")
    if identity_id == '':
        raise ValueError("'identity_id' cannot be an empty string")
    if source is None:
        raise ValueError("'source' cannot be None")
    if source == '':
        raise ValueError("'source' cannot be an empty string")
    if not (name or email or username):
        raise ValueError("identity data cannot be None or empty")

    identity = Identity(id=identity_id, name=name, email=email,
                        username=username, source=source)
    identity.last_modified = datetime.datetime.utcnow()
    identity.uidentity = uidentity
    identity.uidentity.last_modified = identity.last_modified

    session.add(identity)

    return identity


def add_organization(session, name):
    """Add an organization to the session.

    This function adds a new organization to the session,
    using the given `name` as an identifier. Name cannot be
    empty or `None`.

    It returns a new `Organization` object.

    :param session: database session
    :param name: name of the organization

    :return: a new organization

    :raises ValueError: when `name` is `None` or empty
    """
    if name is None:
        raise ValueError("'name' cannot be None")
    if name == '':
        raise ValueError("'name' cannot be an empty string")

    organization = Organization(name=name)

    session.add(organization)

    return organization
