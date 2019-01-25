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

import hashlib

import django.db.transaction

from .db import (find_unique_identity,
                 find_identity,
                 add_unique_identity as add_unique_identity_db,
                 add_identity as add_identity_db,
                 delete_unique_identity as delete_unique_identity_db,
                 delete_identity as delete_identity_db,
                 update_profile as update_profile_db)
from .errors import InvalidValueError
from .utils import unaccent_string


def generate_uuid(source, email=None, name=None, username=None):
    """Generate a UUID related to identity data.

    Based on the input data, the function will return the UUID
    associated to an identity. On this version, the UUID will
    be the SHA1 of `source:email:name:username` string.

    This string is case insensitive, which means same values
    for the input parameters in upper or lower case will produce
    the same UUID.

    The value of `name` will converted to its unaccent form which
    means same values with accent or unaccent chars (i.e 'ö and o')
    will generate the same UUID.

    For instance, these combinations will produce the same UUID:
        ('scm', 'jsmith@example.com', 'John Smith', 'jsmith'),
        ('scm', 'jsmith@example,com', 'Jöhn Smith', 'jsmith'),
        ('scm', 'jsmith@example.com', 'John Smith', 'JSMITH'),
        ('scm', 'jsmith@example.com', 'john Smith', 'jsmith')

    :param source: data source
    :param email: email of the identity
    :param name: full name of the identity
    :param username: user name used by the identity

    :returns: a universal unique identifier for Sorting Hat

    :raises ValueError: when source is `None` or empty; each one
        of the parameters is `None`; or the parameters are empty.
    """
    def to_str(value, unaccent=False):
        s = str(value)
        if unaccent:
            return unaccent_string(s)
        else:
            return s

    if source is None:
        raise ValueError("'source' cannot be None")
    if source == '':
        raise ValueError("'source' cannot be an empty string")
    if not (email or name or username):
        raise ValueError("identity data cannot be empty")

    s = ':'.join((to_str(source),
                  to_str(email),
                  to_str(name, unaccent=True),
                  to_str(username))).lower()
    s = s.encode('UTF-8', errors="surrogateescape")

    sha1 = hashlib.sha1(s)
    uuid = sha1.hexdigest()

    return uuid


@django.db.transaction.atomic
def add_identity(source, name=None, email=None, username=None, uuid=None):
    """Add an identity to the registry.

    This function adds a new identity to the registry. By default,
    a new unique identity will be also added and associated to
    the new identity.

    When `uuid` parameter is set, it creates a new identity that
    will be associated to the unique identity defined by this
    identifier. This identifier must exist on the registry.
    If it does not exist, the function will raise a `NotFoundError`
    exception.

    When no `uuid` is given, both new unique identity and identity
    will have the same identifier.

    The registry considers that two identities are distinct when
    any value of the tuple (source, email, name, username) is
    different. Thus, the identities:

        `id1:('scm', 'jsmith@example.com', 'John Smith', 'jsmith')`
        `id2:('mls', 'jsmith@example.com', 'John Smith', 'jsmith')`

    will be registered as different identities. An `AlreadyExistError`
    exception will be raised when the function tries to insert a
    tuple that exists in the registry.

    The function returns the new identity associated to the new
    registered identity.

    :param source: data source
    :param name: full name of the identity
    :param email: email of the identity
    :param username: user name used by the identity
    :param uuid: associates the new identity to the unique identity
        identified by this id

    :returns: a universal unique identifier

    :raises InvalidValueError: when `source` is `None` or empty;
        when all the identity parameters are `None` or empty.
    :raises AlreadyExistsError: raised when the identity already
        exists in the registry.
    :raises NotFoundError: raised when the unique identity
        associated to the given `uuid` is not in the registry.
    """
    try:
        id_ = generate_uuid(source, email=email,
                            name=name, username=username)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    if not uuid:
        uidentity = add_unique_identity_db(id_)
    else:
        uidentity = find_unique_identity(uuid)

    try:
        identity = add_identity_db(uidentity, id_, source,
                                   name=name, email=email, username=username)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    return identity


@django.db.transaction.atomic
def delete_identity(uuid):
    """Remove an identity from the registry.

    This function removes from the registry the identity which
    its identifier matches with `uuid`. When the `uuid` also
    belongs to a unique identity, this entry and those identities
    linked to it will be removed too. The value of this identifier
    cannot be empty.

    If the identifier is not found in the registry a 'NotFoundError'
    exception is raised.

    As a result, the function will return an updated version of the
    unique identity with the identity removed. If the deleted entry
    was a unique identity, the returned value will be `None` because
    this object was wiped out.

    :param uuid: identifier assigned to the identity or unique
        identity that will be removed

    :returns: a unique identity with the identity removed; `None` when
        the unique identity was also removed.

    :raises InvalidValueError: when `uuid` is `None` or empty.
    :raises NotFoundError: when the identity does not exist in the
        registry.
    """
    if uuid is None:
        raise InvalidValueError(msg="'uuid' cannot be None")
    if uuid == '':
        raise InvalidValueError(msg="'uuid' cannot be an empty string")

    identity = find_identity(uuid)
    uidentity = identity.uidentity

    if uidentity.uuid == uuid:
        delete_unique_identity_db(identity.uidentity)
        uidentity = None
    else:
        delete_identity_db(identity)
        uidentity.refresh_from_db()

    return uidentity


@django.db.transaction.atomic
def update_profile(uuid, **kwargs):
    """Update unique identity profile.

    This function allows to edit or update the profile information
    of the unique identity identified by `uuid`.

    The values to update are given as keyword arguments. The allowed
    keys are listed below (other keywords will be ignored):

       - 'name' : name of the unique identity
       - 'email' : email address of the unique identity
       - 'gender' : gender of the unique identity
       - 'gender_acc' : gender accuracy (range of 1 to 100; by default,
             set to 100)
       - 'is_bot' : boolean value to determine whether a unique identity is
             a bot or not. By default, this value is initialized to
             `False`.
       - 'country_code' : ISO-3166 country code

    The result of calling this function will be the `UniqueIdentity`
    object with an updated profile.

    :param uuid: identifier of the unique identity which its project
        will be updated
    :param kwargs: keyword arguments with data to update the profile

    :returns: a unique identity with its profile updated

    :raises NotFoundError: raised when either the unique identity
        or the country code do not exist in the registry.
    :raises InvalidValueError: raised when any of the keyword arguments
        has an invalid value.
    """
    uidentity = find_unique_identity(uuid)

    try:
        uidentity = update_profile_db(uidentity, **kwargs)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    return uidentity
