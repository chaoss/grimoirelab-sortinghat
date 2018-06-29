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
import logging

from .model import (MAX_PERIOD_DATE,
                    MIN_PERIOD_DATE,
                    UniqueIdentity,
                    Identity,
                    Profile,
                    Organization,
                    Domain,
                    Enrollment,
                    Country,
                    MatchingBlacklist)


logger = logging.getLogger(__name__)


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


def find_country(session, code):
    """Find a country.

    Find a country by its ISO-3166 `code` (i.e ES for Spain,
    US for United States of America) using the given `session.
    When the country does not exist the function will return
    `None`.

    :param session: database session
    :param code: ISO-3166 code of the country to find

    :return: a country object; `None` when the country
        does not exist
    """
    country = session.query(Country).\
        filter(Country.code == code).first()

    return country


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


def delete_unique_identity(session, uidentity):
    """Remove a unique identity from the session.

    Function that removes from the session the unique identity
    given in `uidentity`. Data related to this identity will be
    also removed.

    :param session: database session
    :param uidentity: unique identity to remove
    """
    session.delete(uidentity)
    session.flush()


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


def delete_identity(session, identity):
    """Remove an identity from the session.

    This function removes from the session the identity given
    in `identity`. Take into account this function does not
    remove unique identities in the case they get empty.

    :param session: database session
    :param identity: identity to remove
    """
    uidentity = identity.uidentity
    uidentity.last_modified = datetime.datetime.utcnow()

    session.delete(identity)
    session.flush()


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


def delete_organization(session, organization):
    """Remove an organization from the session.

    Function that removes from the session the organization
    given in `organization`. Data related such as domains
    or enrollments are also removed.

    :param session: database session
    :param organization: organization to remove
    """
    last_modified = datetime.datetime.utcnow()

    for enrollment in organization.enrollments:
        enrollment.uidentity.last_modified = last_modified

    session.delete(organization)
    session.flush()


def add_domain(session, organization, domain_name, is_top_domain=False):
    """Add a domain to the session.

    This function adds a new domain to the session using
    `domain_name` as its identifier. The new domain will
    also be linked to the organization object of `organization`.

    Values assigned to `domain_name` cannot be `None` or empty.
    The parameter `is_top_domain` only accepts `bool` values.

    As a result, the function returns a new `Domain` object.

    :param session: database session
    :param organization: links the new domain to this organization object
    :param domain_name: name of the domain
    :param is_top_domain: set this domain as a top domain

    :return: a new domain

    :raises ValueError: raised when `domain_name` is `None` or an empty;
        when `is_top_domain` does not have a `bool` value.
    """
    if domain_name is None:
        raise ValueError("'domain_name' cannot be None")
    if domain_name == '':
        raise ValueError("'domain_name' cannot be an empty string")
    if not isinstance(is_top_domain, bool):
        raise ValueError("'is_top_domain' must have a boolean value")

    dom = Domain(domain=domain_name, is_top_domain=is_top_domain)
    dom.organization = organization

    session.add(dom)

    return dom


def delete_domain(session, domain):
    """Remove a domain from the session.

    Deletes from the session the domain given in `domain`.

    :param session: database session
    :param domain: domain to remove
    """
    session.delete(domain)
    session.flush()


def enroll(session, uidentity, organization,
           from_date=MIN_PERIOD_DATE, to_date=MAX_PERIOD_DATE):
    """Enroll a unique identity to an organization.

    The function adds a new relationship between the unique
    identity in `uidentity` and the given `organization` for
    the current session.

    The period of the enrollment can be given with the parameters
    `from_date` and `to_date`, where `from_date <= to_date`.
    Default values for these dates are `MIN_PERIOD_DATE` and
    `MAX_PERIOD_DATE`. These dates cannot be `None`.

    This function returns as result a new `Enrollment` object.

    :param session: database session
    :param uidentity: unique identity to enroll
    :param organization: organization where the unique identity is enrolled
    :param from_date: date when the enrollment starts
    :param to_date: date when the enrollment ends

    :return: a new enrollment

    :raises ValeError: when either `from_date` or `to_date` are `None`;
        when `from_date < MIN_PERIOD_DATE`; or `to_date > MAX_PERIOD_DATE`
        or `from_date > to_date`.
    """
    if not from_date:
        raise ValueError("'from_date' cannot be None")
    if not to_date:
        raise ValueError("'to_date' cannot be None")

    if from_date < MIN_PERIOD_DATE or from_date > MAX_PERIOD_DATE:
        raise ValueError("'from_date' %s is out of bounds" % str(from_date))
    if to_date < MIN_PERIOD_DATE or to_date > MAX_PERIOD_DATE:
        raise ValueError("'to_date' %s is out of bounds" % str(to_date))
    if from_date > to_date:
        raise ValueError("'from_date' %s cannot be greater than %s"
                         % (from_date, to_date))

    enrollment = Enrollment(uidentity=uidentity,
                            organization=organization,
                            start=from_date, end=to_date)
    uidentity.last_modified = datetime.datetime.utcnow()

    session.add(enrollment)

    return enrollment


def withdraw(session, uidentity, organization,
             from_date=MIN_PERIOD_DATE, to_date=MAX_PERIOD_DATE):
    """Withdraw a unique identity from an organization.

    Removes all the enrollments between the unique identity in
    `uidentity` and the given 'organization'.

    When a period of time is given using `from_date` and `to_date`
    parameters, the function will remove those periods on which
    `from_date` <= enrollment <= `to_date`. Default values for
    these dates are `MIN_PERIOD_DATE` and `MAX_PERIOD_DATE`.
    These dates cannot be `None`.

    :param session: database session
    :param uidentity: unique identity to withdraw
    :param organization: organization where the unique identity is withdrawn
    :param from_date: date when the enrollment starts
    :param to_date: date when the enrollment ends

    :return: number of removed enrollments

    :raises ValeError: when either `from_date` or `to_date` are `None`;
        when `from_date < MIN_PERIOD_DATE`; or `to_date > MAX_PERIOD_DATE`
        or `from_date > to_date`.
    """
    if not from_date:
        raise ValueError("'from_date' cannot be None")
    if not to_date:
        raise ValueError("'to_date' cannot be None")

    if from_date < MIN_PERIOD_DATE or from_date > MAX_PERIOD_DATE:
        raise ValueError("'from_date' %s is out of bounds" % str(from_date))
    if to_date < MIN_PERIOD_DATE or to_date > MAX_PERIOD_DATE:
        raise ValueError("'to_date' %s is out of bounds" % str(to_date))
    if from_date > to_date:
        raise ValueError("'from_date' %s cannot be greater than %s"
                         % (from_date, to_date))

    enrollments = session.query(Enrollment).\
        filter(Enrollment.uidentity == uidentity,
               Enrollment.organization == organization,
               from_date <= Enrollment.start,
               Enrollment.end <= to_date).all()

    ndeleted = 0

    for enrollment in enrollments:
        session.delete(enrollment)
        ndeleted += 1

    if ndeleted > 0:
        uidentity.last_modified = datetime.datetime.utcnow()
        session.flush()

    return ndeleted


def delete_enrollment(session, enrollment):
    """Remove an enrollment from the session.

    This function removes from the session the given enrollment.

    :param session: database session
    :param enrollment: enrollment to remove
    """
    uidentity = enrollment.uidentity
    uidentity.last_modified = datetime.datetime.utcnow()

    session.delete(enrollment)
    session.flush()


def edit_profile(session, uidentity, **kwargs):
    """Edit unique identity profile.

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

    As a result, it will return a `Profile` object with the updated data.

    :param session: database session
    :param uidentity: unique identity whose profile will be edited
    :param kwargs: parameters to edit the profile

    :return: the edited profile

    :raises ValueError: raised when `is_bot` does not have a boolean value;
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
        country_code = None

        if code:
            country = find_country(session, code)

            if not country:
                raise ValueError("'country_code' (%s) does not match with a valid code"
                                 % str(code))

            country_code = country.code

        profile.country_code = country_code

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

    uidentity.last_modified = datetime.datetime.utcnow()

    session.add(profile)

    return profile


def move_identity(session, identity, uidentity):
    """Move an identity to a unique identity.

    Shifts `identity` to the unique identity given in
    `uidentity`. The function returns whether the operation
    was executed successfully.

    When `uidentity` is the unique identity currently related
    to `identity`, this operation does not have any effect and
    `False` will be returned as result.

    :param session: database session
    :param identity: identity to be moved
    :param uidentity: unique identity where `identity` will be moved

    :return: `True` if the identity was moved; `False` in any other
        case
    """
    if identity.uuid == uidentity.uuid:
        return False

    old_uidentity = identity.uidentity
    identity.uidentity = uidentity

    last_modified = datetime.datetime.utcnow()

    old_uidentity.last_modified = last_modified
    uidentity.last_modified = last_modified
    identity.last_modified = last_modified

    session.add(uidentity)
    session.add(old_uidentity)

    return True


def move_enrollment(session, enrollment, uidentity):
    """Move an enrollment to a unique identity.

    Shifts `enrollment` to the unique identity given in
    `uidentity`. The function returns whether the operation
    was executed successfully.

    When `uidentity` is the unique identity currently related
    to `enrollment`, this operation does not have any effect and
    `False` will be returned as result.

    :param session: database session
    :param enrollment: enrollment to be moved
    :param uidentity: unique identity where `enrollment` will be moved

    :return: `True` if the enrollment was moved; `False` in any other
        case
    """
    if enrollment.uuid == uidentity.uuid:
        return False

    old_uidentity = enrollment.uidentity
    enrollment.uidentity = uidentity

    last_modified = datetime.datetime.utcnow()

    old_uidentity.last_modified = last_modified
    uidentity.last_modified = last_modified

    session.add(uidentity)
    session.add(old_uidentity)

    return True


def add_to_matching_blacklist(session, term):
    """Add term to the matching blacklist.

    This function adds a `term` to the matching blacklist.
    The term to add cannot have a `None` or empty value,
    on this case an `ValueError` will be raised.

    :param session: database session
    :param term: term, word or value to blacklist

    :return: a new entry in the blacklist

    :raises ValueError: raised when `term` is `None` or an empty string
    """
    if term is None:
        raise ValueError("'term' to blacklist cannot be None")
    if term == '':
        raise ValueError("'term' to blacklist cannot be an empty string")

    mb = MatchingBlacklist(excluded=term)
    session.add(mb)

    return mb


def delete_from_matching_blacklist(session, entry):
    """Remove a blacklisted entry from the registry.

    This function removes the given blacklisted term from
    the registry.

    :param session: database session
    :param entry: blacklisted entry to remove
    """
    session.delete(entry)
    session.flush()
