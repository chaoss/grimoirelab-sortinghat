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

from grimoirelab_toolkit.datetime import datetime_to_utc

from .db import (find_unique_identity,
                 find_identity,
                 find_organization,
                 search_enrollments_in_period,
                 add_unique_identity as add_unique_identity_db,
                 add_identity as add_identity_db,
                 delete_unique_identity as delete_unique_identity_db,
                 delete_identity as delete_identity_db,
                 update_profile as update_profile_db,
                 move_identity as move_identity_db,
                 add_enrollment,
                 delete_enrollment)
from .errors import InvalidValueError, AlreadyExistsError, NotFoundError
from .models import MIN_PERIOD_DATE, MAX_PERIOD_DATE
from .utils import unaccent_string, merge_datetime_ranges


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


@django.db.transaction.atomic
def move_identity(from_id, to_uuid):
    """Move an identity to a unique identity.

    This function shifts the identity identified by `from_id` to
    the unique identity identified by `to_uuid`.

    When `to_uuid` is the unique identity that is currently related
    to `from_id`, the action does not have any effect.

    In the case of `from_id` and `to_uuid` have equal values and the
    unique identity does not exist, a new unique identity will be
    created and the identity will be moved to it.

    The function raises a `NotFoundError` exception when either `from_id`
    or `to_uuid` do not exist in the registry and both identifiers are
    not the same.

    The unique identity object with updated identities data is returned
    as the result of calling this function.

    :param from_id: identifier of the identity set to be moved
    :param to_uuid: identifier of the unique identity where 'from_id'
        will be moved

    :returns: a unique identity with identities data updated

    :raises NotFoundError: raised when either `from_uuid` or `to_uuid`
        do not exist in the registry.
    :raises InvalidValueError: raised when either `from_id' or `to_uuid`
        are `None` or empty strings,
    """
    if from_id is None:
        raise InvalidValueError(msg="'from_id' cannot be None")
    if from_id == '':
        raise InvalidValueError(msg="'from_id' cannot be an empty string")
    if to_uuid is None:
        raise InvalidValueError(msg="'to_uuid' cannot be None")
    if to_uuid == '':
        raise InvalidValueError(msg="'to_uuid' cannot be an empty string")

    identity = find_identity(from_id)

    try:
        to_uid = find_unique_identity(to_uuid)
    except NotFoundError as exc:
        # Move identity to a new one
        if identity.id == to_uuid:
            to_uid = add_unique_identity_db(identity.id)
        else:
            raise exc

    try:
        uidentity = move_identity_db(identity, to_uid)
    except ValueError:
        # Case when the identity is already assigned to the unique identity
        uidentity = to_uid

    return uidentity


@django.db.transaction.atomic
def enroll(uuid, organization, from_date=None, to_date=None):
    """Enroll a unique identity in an organization.

    The function enrolls a unique identity, identified by `uuid`,
    in the given `organization`. Both identity and organization must
    exist before adding this enrollment to the registry. Otherwise,
    a `NotFoundError` exception will be raised.

    The period of the enrollment can be given with the parameters
    `from_date` and `to_date`, where `from_date <= to_date`. Default
    values for these dates are `1900-01-01` and `2100-01-01`.

    Existing enrollments for the same unique identity and organization
    which overlap with the new period will be merged into a single
    enrollment.

    If the given period for that enrollment is enclosed by one already
    stored, the function will raise an `AlreadyExistsError` exception.

    The unique identity object with updated enrollment data is returned
    as the result of calling this function.

    :param uuid: unique identifier
    :param organization: name of the organization
    :param from_date: date when the enrollment starts
    :param to_date: date when the enrollment ends

    :returns: a unique identity with enrollment data updated

    :raises NotFoundError: when either `uuid` or `organization` are not
        found in the registry.
    :raises InvalidValueError: raised in three cases, when either identity or
        organization are None or empty strings; when "from_date" < 1900-01-01 or
        "to_date" > 2100-01-01; when "from_date > to_date".
    :raises AlreadyExistsError: raised when the given period for that enrollment
        already exists in the registry.
    """
    if uuid is None:
        raise InvalidValueError(msg="uuid cannot be None")
    if uuid == '':
        raise InvalidValueError(msg="uuid cannot be an empty string")
    if organization is None:
        raise InvalidValueError(msg="organization cannot be None")
    if organization == '':
        raise InvalidValueError(msg="organization cannot be an empty string")

    from_date = datetime_to_utc(from_date) if from_date else MIN_PERIOD_DATE
    to_date = datetime_to_utc(to_date) if to_date else MAX_PERIOD_DATE

    if from_date > to_date:
        msg = "'start' date {} cannot be greater than {}".format(from_date, to_date)
        raise InvalidValueError(msg=msg)

    # Find and check entities
    uidentity = find_unique_identity(uuid)
    org = find_organization(organization)

    # Get the list of current ranges
    # Check whether the new one already exist
    enrollments_db = search_enrollments_in_period(uuid, organization,
                                                  from_date=from_date,
                                                  to_date=to_date)

    periods = [[enr_db.start, enr_db.end] for enr_db in enrollments_db]

    for period in periods:
        if from_date >= period[0] and to_date <= period[1]:
            eid = '{}-{}-{}-{}'.format(uuid, organization, from_date, to_date)
            raise AlreadyExistsError(entity='Enrollment', eid=eid)
        if to_date < period[0]:
            break

    periods.append([from_date, to_date])

    # Remove old enrollments and add new ones based in the new ranges
    for enrollment_db in enrollments_db:
        delete_enrollment(enrollment_db)

    try:
        for start_dt, end_dt in merge_datetime_ranges(periods):
            add_enrollment(uidentity, org, start=start_dt, end=end_dt)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    uidentity.refresh_from_db()

    return uidentity


@django.db.transaction.atomic
def withdraw(uuid, organization, from_date=None, to_date=None):
    """Withdraw a unique identity from an organization.

    This function withdraws a unique identity identified by `uuid`
    from the given `organization` during the given period of time.

    For example, if the unique identity `A` was enrolled from `2010-01-01`
    to `2018-01-01` to the organization `Example`, the result of withdrawing
    that identity from `2014-01-01` to `2016-01-01` will be two enrollments
    for that identity: one for the period 2010-2014 and another one for
    the period 2016-2018. If the period of withdrawing encloses minimum
    and maximum dates, all the enrollments will be removed.

    Both `uuid` and `organization` must exists before being deleted.
    Moreover, an enrollment during the given period must exist.
    Otherwise, it will raise a `NotFoundError` exception.

    The period of the enrollment can be given with the parameters
    `from_date` and `to_date`, where `from_date <= to_date`. Default
    values for these dates are `1900-01-01` and `2100-01-01`.

    The unique identity object with updated enrollment data is returned
    as the result of calling this function.

    :param uuid: unique identifier
    :param organization: name of the organization
    :param from_date: date when the enrollment starts
    :param to_date: date when the enrollment ends

    :returns: a unique identity with enrollment data updated

    :raises NotFoundError: when either `uuid` or `organization` are not
        found in the registry or when the identity is not enrolled
        in that organization for the given period
    :raises InvalidValeError: raised in three cases, when either identity or
        organization are `None` or empty strings; when "from_date" < 1900-01-01 or
        "to_date" > 2100-01-01; when "from_date > to_date"
    """
    if uuid is None:
        raise InvalidValueError(msg="uuid cannot be None")
    if uuid == '':
        raise InvalidValueError(msg="uuid cannot be an empty string")
    if organization is None:
        raise InvalidValueError(msg="organization cannot be None")
    if organization == '':
        raise InvalidValueError(msg="organization cannot be an empty string")

    from_date = datetime_to_utc(from_date) if from_date else MIN_PERIOD_DATE
    to_date = datetime_to_utc(to_date) if to_date else MAX_PERIOD_DATE

    if from_date < MIN_PERIOD_DATE or from_date > MAX_PERIOD_DATE:
        raise InvalidValueError(msg="'from_date' date {} is out of bounds".format(from_date))
    if to_date < MIN_PERIOD_DATE or to_date > MAX_PERIOD_DATE:
        raise InvalidValueError(msg="'to_date' date {} is out of bounds".format(to_date))
    if from_date > to_date:
        msg = "'from_date' date {} cannot be greater than {}".format(from_date, to_date)
        raise InvalidValueError(msg=msg)

    # Find and check entities
    uidentity = find_unique_identity(uuid)
    org = find_organization(organization)

    # Get the list of current ranges
    # Check whether any enrollment for the given period exist
    enrollments_db = search_enrollments_in_period(uuid, organization,
                                                  from_date=from_date,
                                                  to_date=to_date)

    if not enrollments_db:
        eid = "'{}-{}-{}-{}'".format(uuid, organization, from_date, to_date)
        raise NotFoundError(entity=eid)

    # Remove enrollments and generate new periods
    mins = []
    maxs = []

    for enrollment_db in enrollments_db:
        mins.append(enrollment_db.start)
        maxs.append(enrollment_db.end)
        delete_enrollment(enrollment_db)

    min_range = min(mins)
    max_range = max(maxs)

    try:
        if min_range < from_date:
            add_enrollment(uidentity, org, start=min_range, end=from_date)
        if max_range > to_date:
            add_enrollment(uidentity, org, start=to_date, end=max_range)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    uidentity.refresh_from_db()

    return uidentity
