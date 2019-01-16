# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2019 Bitergia
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

import re

import django.db.utils

from grimoirelab_toolkit.datetime import datetime_utcnow

from .errors import AlreadyExistsError, NotFoundError
from .models import (Organization,
                     Domain,
                     UniqueIdentity,
                     Identity,
                     Profile)


def find_unique_identity(uuid):
    """Find a unique identity.

    Find a unique identity by its UUID in the database.
    When the unique identity does not exist the function will
    raise a `NotFoundException`.

    :param uuid: id of the unique identity to find

    :returns: a unique identity object

    :raises NotFoundError: when the unique identity with
        the given `uuid` does not exists.
    """
    try:
        uidentity = UniqueIdentity.objects.get(uuid=uuid)
    except UniqueIdentity.DoesNotExist:
        raise NotFoundError(entity=uuid)
    else:
        return uidentity


def add_organization(name):
    """Add an organization to the database.

    This function adds a new organization to the database,
    using the given `name` as an identifier. Name cannot be
    empty or `None`.

    It returns a new `Organization` object.

    :param name: name of the organization

    :returns: a new organization

    :raises ValueError: when `name` is `None` or empty.
    :raises AlreadyExistsError: when an instance with the same name
        already exists in the database.
    """
    if name is None:
        raise ValueError("'name' cannot be None")
    if name == '':
        raise ValueError("'name' cannot be an empty string")

    organization = Organization(name=name)

    try:
        organization.save()
    except django.db.utils.IntegrityError as exc:
        _handle_integrity_error(Organization, exc)

    return organization


def delete_organization(organization):
    """Remove an organization from the database.

    Function that removes from the database the organization
    given in `organization`. Data related such as domains
    or enrollments are also removed.

    :param organization: organization to remove
    """
    last_modified = datetime_utcnow()
    UniqueIdentity.objects.filter(enrollments__organization=organization).\
        update(last_modified=last_modified)

    organization.delete()


def add_domain(organization, domain_name, is_top_domain=False):
    """Add a domain to the database.

    This function adds a new domain to the database using
    `domain_name` as its identifier. The new domain will
    also be linked to the organization object in `organization`.

    Values assigned to `domain_name` cannot be `None` or empty.
    The parameter `is_top_domain` only accepts `bool` values.

    As a result, the function returns a new `Domain` object.

    :param organization: links the new domain to this organization object
    :param domain_name: name of the domain
    :param is_top_domain: set this domain as a top domain

    :returns: a new domain

    :raises ValueError: raised when `domain_name` is `None` or an empty string;
        when `is_top_domain` does not have a `bool` value.
    """
    if domain_name is None:
        raise ValueError("'domain_name' cannot be None")
    if domain_name == '':
        raise ValueError("'domain_name' cannot be an empty string")
    if not isinstance(is_top_domain, bool):
        raise ValueError("'is_top_domain' must have a boolean value")

    domain = Domain(domain=domain_name,
                    is_top_domain=is_top_domain,
                    organization=organization)

    try:
        domain.save()
    except django.db.utils.IntegrityError as exc:
        _handle_integrity_error(Domain, exc)

    return domain


def delete_domain(domain):
    """Remove a domain from the database.

    Deletes from the database the domain given in `domain`.

    :param domain: domain to remove
    """
    domain.delete()


def add_unique_identity(uuid):
    """Add a unique identity to the database.

    This function adds a unique identity to the database with
    `uuid` string as unique identifier. This identifier cannot
    be empty or `None`.

    When the unique identity is added, a new empty profile for
    this object is created too.

    As a result, the function returns a new `UniqueIdentity`
    object.

    :param uuid: unique identifier for the unique identity

    :returns: a new unique identity

    :raises ValueError: when `uuid` is `None` or an empty string
    """
    if uuid is None:
        raise ValueError("'uuid' cannot be None")
    if uuid == '':
        raise ValueError("'uuid' cannot be an empty string")

    uidentity = UniqueIdentity(uuid=uuid)

    try:
        uidentity.save(force_insert=True)
    except django.db.utils.IntegrityError as exc:
        _handle_integrity_error(UniqueIdentity, exc)

    profile = Profile(uidentity=uidentity)

    try:
        profile.save()
    except django.db.utils.IntegrityError as exc:
        _handle_integrity_error(Profile, exc)

    uidentity.refresh_from_db()

    return uidentity


def add_identity(uidentity, identity_id, source,
                 name=None, email=None, username=None):
    """Add an identity to the database.

    This function adds a new identity to the database using
    `identity_id` as its identifier. The new identity will
    also be linked to the unique identity object of `uidentity`.

    Neither the values given to `identity_id` nor to `source` can
    be `None` or empty. Moreover, `name`, `email` or `username`
    parameters need a non empty value.

    As a result, the function returns a new `Identity` object.

    :param uidentity: links the new identity to this unique identity object
    :param identity_id: identifier for the new identity
    :param source: data source where this identity was found
    :param name: full name of the identity
    :param email: email of the identity
    :param username: user name used by the identity

    :returns: a new identity

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

    try:
        identity = Identity(id=identity_id, name=name, email=email,
                            username=username, source=source,
                            uidentity=uidentity)
        identity.save(force_insert=True)
        uidentity.save()
    except django.db.utils.IntegrityError as exc:
        _handle_integrity_error(Identity, exc)

    return identity


_MYSQL_DUPLICATE_ENTRY_ERROR_REGEX = re.compile(r"Duplicate entry '(?P<value>.+)' for key")


def _handle_integrity_error(model, exc):
    """Handle integrity error exceptions."""

    m = re.match(_MYSQL_DUPLICATE_ENTRY_ERROR_REGEX,
                 exc.__cause__.args[1])
    if not m:
        raise exc

    entity = model.__name__
    eid = m.group('value')

    raise AlreadyExistsError(entity=entity, eid=eid)
