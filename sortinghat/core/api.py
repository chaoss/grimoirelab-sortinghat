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
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#

import hashlib

import django.db.transaction

from grimoirelab_toolkit.datetime import datetime_to_utc

from .db import (find_unique_identity,
                 find_identity,
                 find_organization,
                 find_domain,
                 search_enrollments_in_period,
                 add_unique_identity as add_unique_identity_db,
                 add_identity as add_identity_db,
                 add_organization as add_organization_db,
                 add_domain as add_domain_db,
                 delete_unique_identity as delete_unique_identity_db,
                 delete_identity as delete_identity_db,
                 delete_organization as delete_organization_db,
                 delete_domain as delete_domain_db,
                 update_profile as update_profile_db,
                 move_identity as move_identity_db,
                 lock as lock_db,
                 unlock as unlock_db,
                 add_enrollment,
                 delete_enrollment)
from .errors import InvalidValueError, AlreadyExistsError, NotFoundError
from .log import TransactionsLog
from .models import Identity, MIN_PERIOD_DATE, MAX_PERIOD_DATE
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
def add_identity(ctx, source, name=None, email=None, username=None, uuid=None):
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

    :param ctx: context from where this method is called
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
    trxl = TransactionsLog.open('add_identity', ctx)
    try:
        id_ = generate_uuid(source, email=email,
                            name=name, username=username)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    if not uuid:
        uidentity = add_unique_identity_db(trxl, id_)
        uidentity = update_profile_db(trxl, uidentity,
                                      name=name, email=email)
    else:
        uidentity = find_unique_identity(uuid)

    args = {
        'trxl': trxl,
        'uidentity': uidentity,
        'identity_id': id_,
        'source': source,
        'name': name,
        'email': email,
        'username': username
    }

    try:
        identity = add_identity_db(**args)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    trxl.close()

    return identity


@django.db.transaction.atomic
def delete_identity(ctx, uuid):
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

    :param ctx: context from where this method is called
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

    trxl = TransactionsLog.open('delete_identity', ctx)

    identity = find_identity(uuid)
    uidentity = identity.uidentity

    if uidentity.uuid == uuid:
        delete_unique_identity_db(trxl, identity.uidentity)
        uidentity = None
    else:
        delete_identity_db(trxl, identity)
        uidentity.refresh_from_db()

    trxl.close()

    return uidentity


@django.db.transaction.atomic
def update_profile(ctx, uuid, **kwargs):
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

    :param ctx: context from where this method is called
    :param uuid: identifier of the unique identity which its project
        will be updated
    :param kwargs: keyword arguments with data to update the profile

    :returns: a unique identity with its profile updated

    :raises NotFoundError: raised when either the unique identity
        or the country code do not exist in the registry.
    :raises InvalidValueError: raised when any of the keyword arguments
        has an invalid value.
    """
    trxl = TransactionsLog.open('update_profile', ctx)

    uidentity = find_unique_identity(uuid)

    try:
        uidentity = update_profile_db(trxl, uidentity, **kwargs)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    trxl.close()

    return uidentity


@django.db.transaction.atomic
def move_identity(ctx, from_id, to_uuid):
    """Move an identity to a unique identity.

    This function shifts the identity identified by `from_id` to
    the unique identity identified by `to_uuid`.

    When `to_uuid` is the unique identity that is currently related
    to `from_id`, the action does not have any effect.

    In the case of `from_id` and `to_uuid` have equal values and the
    unique identity does not exist, a new unique identity will be
    created and the identity will be moved to it.

    When `from_id` exists as a unique identity too, the function raises
    an `InvalidValueError`, as this identity cannot be moved.

    The function raises a `NotFoundError` exception when either `from_id`
    or `to_uuid` do not exist in the registry and both identifiers are
    not the same.

    The unique identity object with updated identities data is returned
    as the result of calling this function.

    :param ctx: context from where this method is called
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

    trxl = TransactionsLog.open('move_identity', ctx)

    identity = find_identity(from_id)

    if identity.id == identity.uidentity.uuid:
        msg = "'from_id' is a unique identity and it cannot be moved; use 'merge' instead"
        raise InvalidValueError(msg=msg)

    try:
        to_uid = find_unique_identity(to_uuid)
    except NotFoundError as exc:
        # Move identity to a new one
        if identity.id == to_uuid:
            to_uid = add_unique_identity_db(trxl, identity.id)
            to_uid = update_profile_db(trxl, to_uid,
                                       name=identity.name,
                                       email=identity.email)
        else:
            raise exc

    try:
        uidentity = move_identity_db(trxl, identity, to_uid)
    except ValueError:
        # Case when the identity is already assigned to the unique identity
        uidentity = to_uid

    trxl.close()

    return uidentity


@django.db.transaction.atomic
def lock(ctx, uuid):
    """Lock a unique identity so it cannot be modified.

    This function locks the unique identity identified by `uuid`
    so this object and its related objects such as identities,
    enrollments or the profile cannot be modified.

    :param ctx: context from where this method is called
    :param uuid: identifier of the unique identity which will be locked

    :returns: a unique identity with its locked value updated

    :raises InvalidValueError: raised when `uuid` is `None` or an empty string
    :raises NotFoundError: when the identity with the
        given `uuid` does not exists.
    """
    if uuid is None:
        raise InvalidValueError(msg="'uuid' cannot be None")
    if uuid == '':
        raise InvalidValueError(msg="'uuid' cannot be an empty string")

    trxl = TransactionsLog.open('lock', ctx)

    uidentity = find_unique_identity(uuid)
    uidentity = lock_db(trxl, uidentity)

    trxl.close()

    return uidentity


@django.db.transaction.atomic
def unlock(ctx, uuid):
    """Unlock a unique identity so it can be modified.

    This function unlocks the unique identity identified by `uuid`
    so this object and its related objects such as identities,
    enrollments or the profile can be modified.

    :param ctx: context from where this method is called
    :param uuid: identifier of the unique identity which will be unlocked

    :returns: a unique identity with its locked value updated

    :raises InvalidValueError: raised when `uuid` is `None` or an empty string
    :raises NotFoundError: when the identity with the
        given `uuid` does not exists.
    """
    if uuid is None:
        raise InvalidValueError(msg="'uuid' cannot be None")
    if uuid == '':
        raise InvalidValueError(msg="'uuid' cannot be an empty string")

    trxl = TransactionsLog.open('unlock', ctx)

    uidentity = find_unique_identity(uuid)
    uidentity = unlock_db(trxl, uidentity)

    trxl.close()

    return uidentity


@django.db.transaction.atomic
def add_organization(ctx, name):
    """Add an organization to the registry.

    This function adds an organization to the registry.
    It checks first whether the organization is already on the registry.
    When it is not found, the new organization is added. Otherwise,
    it raises a 'AlreadyExistsError' exception to notify that the organization
    already exists.

    :param ctx: context from where this method is called
    :param name: name of the organization

    :raises InvalidValueError: raised when organization is None or an empty string
    :raises AlreadyExistsError: raised when the organization already exists
        in the registry
    """
    if name is None:
        raise InvalidValueError(msg="'name' cannot be None")
    if name == '':
        raise InvalidValueError(msg="'name' cannot be an empty string")

    trxl = TransactionsLog.open('add_organization', ctx)
    try:
        org = add_organization_db(trxl, name=name)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))
    except AlreadyExistsError as exc:
        raise exc

    trxl.close()

    return org


@django.db.transaction.atomic
def add_domain(ctx, organization, domain_name, is_top_domain=True):
    """Add a domain to the registry.

    This function adds a new domain to a given organization.
    The organization must exist on the registry prior to insert the new
    domain. Otherwise, it will raise a `NotFoundError` exception. Moreover,
    if the given domain is already in the registry an `AlreadyExistsError`
    exception will be raised.

    The new domain is set as a top domain by default. That is useful to avoid
    the insertion of sub-domains that belong to the same organization (i.e
    eu.example.com, us.example.com).

    Remember that a domain can only be assigned to one (and only one)
    organization.

    :param ctx: context from where this method is called
    :param organization: name of the organization
    :param domain_name: domain to add to the registry
    :param is_top_domain: set this domain as a top domain

    :returns the new domain object

    :raises InvalidValueError: raised when domain is None or an empty string or
        is_top_domain does not have a boolean value
    :raises NotFoundError: raised when the given organization is not found
        in the registry
    :raises AlreadyExistsError: raised when the domain already exists
        in the registry
    """
    if organization is None:
        raise InvalidValueError(msg="'org_name' cannot be None")
    if organization == '':
        raise InvalidValueError(msg="'org_name' cannot be an empty string")
    if domain_name is None:
        raise InvalidValueError(msg="'domain_name' cannot be None")
    if domain_name == '':
        raise InvalidValueError(msg="'domain_name' cannot be an empty string")

    trxl = TransactionsLog.open('add_domain', ctx)

    try:
        organization = find_organization(organization)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))
    except NotFoundError as exc:
        raise exc

    try:
        domain = add_domain_db(trxl, organization=organization,
                               domain_name=domain_name,
                               is_top_domain=is_top_domain)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))
    except AlreadyExistsError as exc:
        raise exc

    trxl.close()

    return domain


@django.db.transaction.atomic
def delete_organization(ctx, name):
    """Remove an organization from the registry.

    This function removes the given organization from the registry.
    Related information such as domains or enrollments are also removed.
    It checks first whether the organization is already on the registry.
    When it is found, the organization is removed. Otherwise,
    it will raise a 'NotFoundError'.

    :param ctx: context from where this method is called
    :param name: name of the organization to remove

    :raises InvalidValueError: raised when organization is None or an empty string
    :raises NotFoundError: raised when the organization does not exist
        in the registry
    """
    if name is None:
        raise InvalidValueError(msg="'name' cannot be None")
    if name == '':
        raise InvalidValueError(msg="'name' cannot be an empty string")

    trxl = TransactionsLog.open('delete_organization', ctx)

    try:
        org = find_organization(name)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))
    except NotFoundError as exc:
        raise exc

    delete_organization_db(trxl, organization=org)

    trxl.close()

    return org


@django.db.transaction.atomic
def delete_domain(ctx, domain_name):
    """Remove a domain from the registry.

    This function removes the given domain from the registry.
    Domain must exist in the registry. Otherwise, it will raise
    a `NotFoundError` exception.

    :param ctx: context from where this method is called
    :param domain_name: name of the domain to remove

    :returns the removed domain object

    :raises NotFoundError: raised when the domain
        does not exist in the registry.
    """
    if domain_name is None:
        raise InvalidValueError(msg="'domain_name' cannot be None")
    if domain_name == '':
        raise InvalidValueError(msg="'domain_name' cannot be an empty string")

    trxl = TransactionsLog.open('delete_domain', ctx)

    try:
        domain = find_domain(domain_name)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))
    except NotFoundError as exc:
        raise exc

    delete_domain_db(trxl, domain)

    trxl.close()

    return domain


@django.db.transaction.atomic
def enroll(ctx, uuid, organization, from_date=None, to_date=None):
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

    :param ctx: context from where this method is called
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

    trxl = TransactionsLog.open('enroll', ctx)

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
        delete_enrollment(trxl, enrollment_db)

    try:
        for start_dt, end_dt in merge_datetime_ranges(periods):
            add_enrollment(trxl, uidentity, org, start=start_dt, end=end_dt)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    uidentity.refresh_from_db()

    trxl.close()

    return uidentity


@django.db.transaction.atomic
def withdraw(ctx, uuid, organization, from_date=None, to_date=None):
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

    :param ctx: context from where this method is called
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

    trxl = TransactionsLog.open('withdraw', ctx)

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
        delete_enrollment(trxl, enrollment_db)

    min_range = min(mins)
    max_range = max(maxs)

    try:
        if min_range < from_date:
            add_enrollment(trxl, uidentity, org, start=min_range, end=from_date)
        if max_range > to_date:
            add_enrollment(trxl, uidentity, org, start=to_date, end=max_range)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    uidentity.refresh_from_db()

    trxl.close()

    return uidentity


@django.db.transaction.atomic
def merge_identities(ctx, from_uuids, to_uuid):
    """
    Merge one or more unique identities into another.

    Use this function to join a list of `from_uuid` unique identities into
    `to_uuid`. Identities and enrollments related to each `from_uuid` will be
    assigned to `to_uuid`. In addition, each `from_uuid` will be removed
    from the registry. Duplicated enrollments will be also removed from
    the registry while overlapped enrollments will be merged.

    This function also merges two or more profiles. When a field on `to_uuid`
    profile is `None` or empty, it will be updated with the value on the
    profile of each `from_uuid`. If any of the unique identities was set
    as a bot, the new profile will also be set as a bot.

    When any of the `from_uuid` and `to_uuid` are equal, or any of this two
    fields are `None` or empty, it raises an `InvalidValueError`.

    The function raises a `NotFoundError` exception when either any `from_uuid`
    or `to_uuid` do not exist in the registry.

    :param ctx: context from where this method is called
    :param from_uuids: List of identifiers of the unique identities set to merge
    :param to_uuid: identifier of the unique identity where `from_uuids`
        will be merged

    :returns: a UniqueIdentity object as the result of the merged identities

    :raises NotFoundError: raised when either one of the `from_uuids` or
        `to_uuid` do not exist in the registry
    """

    def _find_unique_identities(from_uuids, to_uuid):
        """Find the unique identities to be merged from their uuids"""

        unique_identities = []
        for from_uuid in from_uuids:
            # Check whether input values are valid
            if from_uuid is None:
                raise InvalidValueError(msg="'from_uuid' cannot be None")
            if from_uuid == '':
                raise InvalidValueError(msg="'from_uuid' cannot be an empty string")
            if from_uuid == to_uuid:
                raise InvalidValueError(msg="'from_uuid' and 'to_uuid' cannot be equal")

            try:
                from_uid = find_unique_identity(from_uuid)
                unique_identities.append(from_uid)
            except NotFoundError as exc:
                raise exc

        return unique_identities

    def _get_identities(from_uids):
        """Get all the sub-identities from all the unique identities to be merged"""

        identities = Identity.objects.none()  # Initialize empty QuerySet
        for from_uid in from_uids:
            try:
                identities = identities | from_uid.identities.all()
            except ValueError as e:
                raise InvalidValueError(msg=str(e))

        return identities

    def _move_identities(trxl, from_uids, to_uid):
        """Move individual sub-identities into the target unique identity"""

        identities = _get_identities(from_uids)
        for identity in identities:
            move_identity_db(trxl, identity, to_uid)

    def _merge_enrollments(trxl, from_uids, to_uid):
        """Merge enrollments from `UniqueIdentity` objects"""

        # Get current enrollments from all uidentities
        enrollments_db = to_uid.enrollments.all()
        for from_uid in from_uids:
            enrollments_db = enrollments_db | from_uid.enrollments.all()

        enrollments = {}
        for enrollment in enrollments_db:
            org = enrollment.organization
            dates = enrollments.setdefault(org, [])
            dates.append((enrollment.start, enrollment.end))
            enrollments[org] = dates

        # Remove old enrollments and add new ones based in the new ranges
        for enrollment_db in enrollments_db:
            delete_enrollment(trxl, enrollment_db)

        # Add new enrollments merging datetime ranges
        for org in enrollments.keys():
            periods = enrollments[org]
            try:
                for start_dt, end_dt in merge_datetime_ranges(periods, exclude_limits=True):
                    add_enrollment(trxl, to_uid, org, start=start_dt, end=end_dt)
            except ValueError as e:
                raise InvalidValueError(msg=str(e))

        return to_uid

    def _merge_profiles(from_uids, to_uid):
        """Merge the profiles from `UniqueIdentity` objects"""

        for from_uid in from_uids:
            if not to_uid.profile.is_bot and from_uid.profile.is_bot:
                to_uid.profile.is_bot = True
            if not to_uid.profile.name:
                to_uid.profile.name = from_uid.profile.name
            if not to_uid.profile.email:
                to_uid.profile.email = from_uid.profile.email
            if not to_uid.profile.gender:
                to_uid.profile.gender = from_uid.profile.gender
            if not to_uid.profile.gender_acc:
                to_uid.profile.gender_acc = from_uid.profile.gender_acc
            if not to_uid.profile.country:
                to_uid.profile.country = from_uid.profile.country

        return to_uid

    def _delete_unique_identities(trxl, uids):
        """Delete unique identities from the database"""

        for uid in uids:
            delete_unique_identity_db(trxl, uid)

    # Check input values
    if from_uuids is None:
        raise InvalidValueError(msg="'from_uuids' cannot be None")
    if from_uuids == []:
        raise InvalidValueError(msg="'from_uuids' cannot be an empty list")
    if to_uuid is None:
        raise InvalidValueError(msg="'to_uuid' cannot be None")
    if to_uuid == '':
        raise InvalidValueError(msg="'to_uuid' cannot be an empty string")

    trxl = TransactionsLog.open('merge_identities', ctx)

    try:
        to_uid = find_unique_identity(to_uuid)
        from_uids = _find_unique_identities(from_uuids, to_uuid)
    except NotFoundError as exc:
        # At least one unique identity was not found, so they cannot be merged
        raise exc

    _move_identities(trxl, from_uids, to_uid)

    to_uid = _merge_enrollments(trxl, from_uids, to_uid)
    to_uid.refresh_from_db()

    to_uid = _merge_profiles(from_uids, to_uid)
    update_profile_db(trxl, to_uid)

    _delete_unique_identities(trxl, from_uids)

    trxl.close()

    return to_uid


@django.db.transaction.atomic
def unmerge_identities(ctx, uuids):
    """
    Unmerge one or more identities from their corresponding unique identities.

    Use this function to separate a list of `uuid` identities, creating a unique
    identity for each one. A profile for each new unique identity will be created using
    the `name` and `email` fields of the corresponding identity.
    Nor the enrollments or the profile from any parent unique identity of the input
    identities are modified.

    When a given identity `uuid` is equal to the `uuid` from its parent unique
    identity, there will be no effect.

    The function raises a `NotFoundError` exception when either any `uuid` from
    the list does not exist in the registry.

    The function raises an `InvalidValueError` exception when either any `uuid`
    from the list is `None` or an empty string.

    :param ctx: context from where this method is called
    :param uuids: list of identifiers of the identities set to be unmerged

    :returns: a list of UniqueIdentity objects as the result of the unmerged identities

    :raises NotFoundError: raised when either any `uuid` from the list
        does not exist in the registry
    :raises InvalidValueError: raised when either any `uuid` from the
        list is `None` or an empty string
    """
    def _find_identities(uuids):
        """Find the identities to be unmerged from their parent unique identities"""

        identities = []
        for uuid in uuids:
            # Check whether input values are valid
            if uuid is None:
                raise InvalidValueError(msg="'uuid' cannot be None")
            if uuid == '':
                raise InvalidValueError(msg="'uuid' cannot be an empty string")

            uid = find_identity(uuid)
            identities.append(uid)

        return identities

    def _set_destination_identity(trxl, identity):
        """Create the unique identity, if it does not exist, where the identity will be moved to."""

        if identity.id != identity.uidentity_id:
            uid = add_unique_identity_db(trxl, identity.id)
            uid = update_profile_db(trxl, uid,
                                    name=identity.name,
                                    email=identity.email)
        else:
            # Case when the identity to be unmerged is the main one
            uid = identity.uidentity

        return uid

    def _move_to_destination(trxl, identity, uid):
        """Move the identity from the old unique identity to the new one"""

        try:
            uidentity = move_identity_db(trxl, identity, uid)
        except ValueError:
            # Case when the identity is already assigned to the unique identity
            uidentity = uid

        return uidentity

    # Check input value
    if uuids is None:
        raise InvalidValueError(msg="'uuids' cannot be None")
    if uuids == []:
        raise InvalidValueError(msg="'uuids' cannot be an empty list")

    trxl = TransactionsLog.open('unmerge_identities', ctx)

    identities = _find_identities(uuids)

    new_uidentities = []
    for identity in identities:
        uid = _set_destination_identity(trxl, identity)
        uidentity = _move_to_destination(trxl, identity, uid)
        new_uidentities.append(uidentity)

    trxl.close()

    return new_uidentities
