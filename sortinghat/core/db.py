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
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#

import re

import django.core.exceptions
import django.db.utils

from grimoirelab_toolkit.datetime import datetime_utcnow, datetime_to_utc

from .errors import AlreadyExistsError, NotFoundError
from .models import (MIN_PERIOD_DATE,
                     MAX_PERIOD_DATE,
                     Organization,
                     Domain,
                     Country,
                     UniqueIdentity,
                     Identity,
                     Profile,
                     Enrollment)
from .utils import validate_field


def find_unique_identity(uuid):
    """Find a unique identity.

    Find a unique identity by its UUID in the database.
    When the unique identity does not exist the function will
    raise a `NotFoundError`.

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


def find_identity(uuid):
    """Find an identity.

    Find an identity by its UUID in the database. When the
    identity does not exist the function will raise
    a `NotFoundError`.

    :param uuid: id of the identity to find

    :returns: an identity object

    :raises NotFoundError: when the identity with the
        given `uuid` does not exists.
    """
    try:
        identity = Identity.objects.get(id=uuid)
    except Identity.DoesNotExist:
        raise NotFoundError(entity=uuid)
    else:
        return identity


def find_organization(name):
    """Find an organization.

    Find an organization by its name in the database. When the
    organization does not exist the function will raise
    a `NotFoundError`.

    :param name: name of the organization to find

    :returns: an organization object

    :raises NotFoundError: when the organization with the
        given `name` does not exists.
    """
    validate_field('name', name)

    try:
        organization = Organization.objects.get(name=name)
    except Organization.DoesNotExist:
        raise NotFoundError(entity=name)
    else:
        return organization


def find_domain(domain_name):
    """Find a domain.

    Find a domain by its name in the database. When the
    domain does not exist the function will raise
    a `NotFoundError`.

    :param domain_name: name of the domain to find

    :returns: a domain object

    :raises NotFoundError: when the domain with the
        given `name` does not exists.
    """
    validate_field('domain_name', domain_name)

    try:
        domain = Domain.objects.get(domain=domain_name)
    except Domain.DoesNotExist:
        raise NotFoundError(entity=domain_name)
    else:
        return domain


def search_enrollments_in_period(uuid, org_name,
                                 from_date=MIN_PERIOD_DATE,
                                 to_date=MIN_PERIOD_DATE):
    """Look for enrollments in a given period.

    Returns the enrollments of a unique identity for a given
    organization during period of time.

    An empty list will be returned when no enrollments could be
    found, due to the unique identity or the organization do not
    exist, or there are not enrollments assigned on that period.

    :param uuid: id of the unique identity
    :param org_name: name of the organization
    :param from_date: starting date for the period
    :param to_date: ending date for the period

    :returns: a list of enrollment objects
    """
    return Enrollment.objects.filter(uidentity__uuid=uuid,
                                     organization__name=org_name,
                                     start__lte=to_date, end__gte=from_date).order_by('start')


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
    validate_field('name', name)

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
    validate_field('domain_name', domain_name)
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
    validate_field('uuid', uuid)

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


def delete_unique_identity(uidentity):
    """Remove a unique identity from the database.

    Function that removes from the database the unique identity
    given in `uidentity`. Data related to this identity will be
    also removed.

    :param uidentity: unique identity to remove
    """
    uidentity.delete()


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
    validate_field('identity_id', identity_id)
    validate_field('source', source)
    validate_field('name', name, allow_none=True)
    validate_field('email', email, allow_none=True)
    validate_field('username', username, allow_none=True)

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


def delete_identity(identity):
    """Remove an identity from the database.

    This function removes from the database the identity given
    in `identity`. Take into account this function does not
    remove unique identities in the case they get empty.

    :param identity: identity to remove
    """
    identity.delete()
    identity.uidentity.save()


def update_profile(uidentity, **kwargs):
    """Update unique identity profile.

    This function allows to edit or update the profile information
    of the given unique identity. The values to update are given
    as keyword arguments. The allowed keys are listed below
    (other keywords will be ignored):

       - `name`: name of the unique identity
       - `email`: email address of the unique identity
       - `gender`: gender of the unique identity
       - `gender_acc`: gender accuracy (range of 1 to 100; by default, set to 100)
       - `is_bot`: boolean value to determine whether a unique identity is
             a bot or not. By default, this value is initialized to
             `False`.
       - `country_code`: ISO-3166 country code

    As a result, it will return the `UniqueIdentity` object with
    the updated data.

    :param uidentity: unique identity whose profile will be updated
    :param kwargs: parameters to edit the profile

    :returns: uidentity object with the updated profile

    :raises ValueError: raised either when `is_bot` does not have a boolean value;
        `gender_acc` is not an `int` or is not in range.
    """
    def to_none_if_empty(x):
        return None if not x else x

    profile = uidentity.profile

    if 'name' in kwargs:
        profile.name = to_none_if_empty(kwargs['name'])
    if 'email' in kwargs:
        profile.email = to_none_if_empty(kwargs['email'])

    if 'is_bot' in kwargs:
        is_bot = kwargs['is_bot']

        if not isinstance(is_bot, bool):
            raise ValueError("'is_bot' must have a boolean value")

        profile.is_bot = is_bot

    if 'country_code' in kwargs:
        code = to_none_if_empty(kwargs['country_code'])

        if code:
            try:
                country = Country.objects.get(code=code)
            except django.core.exceptions.ObjectDoesNotExist:
                msg = "'country_code' ({}) does not match with a valid code"
                raise ValueError(msg.format(str(code)))

            profile.country = country
        else:
            profile.country = None

    if 'gender' in kwargs:
        gender = to_none_if_empty(kwargs['gender'])
        gender_acc = None

        if gender:
            gender_acc = kwargs.get('gender_acc', 100)

            if not isinstance(gender_acc, int):
                raise ValueError("'gender_acc' must have an integer value")
            elif not 1 <= gender_acc <= 100:
                raise ValueError("'gender_acc' (%d) is not in range (1,100)"
                                 % gender_acc)

        profile.gender = gender
        profile.gender_acc = gender_acc
    elif 'gender_acc' in kwargs:
        raise ValueError("'gender_acc' can only be set when 'gender' is given")

    profile.save()
    uidentity.save()

    return uidentity


def add_enrollment(uidentity, organization,
                   start=MIN_PERIOD_DATE, end=MAX_PERIOD_DATE):
    """Enroll a unique identity to an organization in the database.

    The function adds a new relationship between the unique
    identity in `uidentity` and the given `organization` to
    the database.

    The period of the enrollment can be given with the parameters
    `from_date` and `to_date`, where `from_date <= to_date`.
    Default values for these dates are `MIN_PERIOD_DATE` and
    `MAX_PERIOD_DATE`. These dates cannot be `None`.

    This function returns as result a new `Enrollment` object.

    :param uidentity: unique identity to enroll
    :param organization: organization where the unique identity is enrolled
    :param start: date when the enrollment starts
    :param end: date when the enrollment ends

    :returns: a new enrollment

    :raises ValueError: when either `start` or `end` are `None`;
        when `start < MIN_PERIOD_DATE`; or `end > MAX_PERIOD_DATE`
        or `start > end`.
    """
    if not start:
        raise ValueError("'start' date cannot be None")
    if not end:
        raise ValueError("'end' date cannot be None")

    start = datetime_to_utc(start)
    end = datetime_to_utc(end)

    if start < MIN_PERIOD_DATE or start > MAX_PERIOD_DATE:
        raise ValueError("'start' date {} is out of bounds".format(start))
    if end < MIN_PERIOD_DATE or end > MAX_PERIOD_DATE:
        raise ValueError("'end' date {} is out of bounds".format(end))
    if start > end:
        raise ValueError("'start' date {} cannot be greater than {}".format(start, end))

    try:
        enrollment = Enrollment(uidentity=uidentity,
                                organization=organization,
                                start=start, end=end)
        enrollment.save()
        uidentity.save()
    except django.db.utils.IntegrityError as exc:
        _handle_integrity_error(Identity, exc)

    return enrollment


def delete_enrollment(enrollment):
    """Remove an enrollment from the database.

    This function removes from the database the enrollment given
    in `enrollment`.

    :param enrollment: enrollment object to remove
    """
    enrollment.delete()
    enrollment.uidentity.save()


def move_identity(identity, uidentity):
    """Move an identity to a unique identity.

    Shifts `identity` to the unique identity given in `uidentity`.
    As a result, it will return `uidentity` object with list of
    identities updated.

    When `identity` is already assigned to `uidentity`, the function
    will raise an `ValueError` exception.

    :param identity: identity to be moved
    :param uidentity: unique identity where `identity` will be moved

    :returns: the unique identity with related identities updated

    :raises ValueError: when `identity` is already part of `uidentity`
    """
    if identity.uidentity == uidentity:
        msg = "identity '{}' is already assigned to '{}'".format(identity.id, uidentity.uuid)
        raise ValueError(msg)

    old_uidentity = identity.uidentity
    identity.uidentity = uidentity

    identity.save()
    old_uidentity.save()
    uidentity.save()

    return uidentity


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
