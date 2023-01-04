# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2021 Bitergia
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

import copy
import logging
import re

import django.core.exceptions
import django.db.utils

from django.db.models import Q

from grimoirelab_toolkit.datetime import datetime_utcnow, datetime_to_utc

from .errors import AlreadyExistsError, NotFoundError, LockedIdentityError

from .models import (MIN_PERIOD_DATE,
                     MAX_PERIOD_DATE,
                     Organization,
                     Team,
                     Group,
                     Domain,
                     Country,
                     Individual,
                     Identity,
                     Profile,
                     Enrollment,
                     Operation)
from .aux import validate_field


logger = logging.getLogger(__name__)


def _set_lock(individual, lock_flag):
    """Set a lock value for a given individual.

    Sets the `is_locked` field from a given `individual`
    object to the boolean value from `lock` variable.

    :param individual: individual which `is_locked` parameter will be set
    :param lock_flag: bool value to be set to `is_locked` parameter from the `individual`

    :returns: the individual entity with `is_locked` field updated
    """
    individual.is_locked = lock_flag
    individual.save()

    return individual


def find_individual(mk):
    """Find an individual entity.

    Find an individual by its main key (`mk`) in the database.
    When the individual does not exist the function will
    raise a `NotFoundError`.

    :param mk: main key or id of the individual to find

    :returns: an individual object

    :raises NotFoundError: when the individual with
        the given `mk` does not exists.
    """
    try:
        logger.debug(f"Finding individual {mk} by main key ...")
        individual = Individual.objects.get(mk=mk)
    except Individual.DoesNotExist:
        logger.debug(f"Individual with main key {mk} does not exist")
        raise NotFoundError(entity=mk)
    else:
        logger.debug(f"Individual with main key {mk} was found")
        return individual


def find_individual_by_uuid(uuid):
    """Find an individual by its identities UUIDs.

    Find an individual which identities have the parameter
    `uuid` as their identifier. When such individual does
    not exists the function will raise a `NotFoundError`.

    :param uuid: id to search the individual

    :returns: an individual object

    :raises NotFoundError: when the individual does
        not exist.
    """
    try:
        logger.debug(f"Finding individual {uuid} by UUID ...")
        individual = Individual.objects.filter(
            Q(mk=uuid) | Q(identities__uuid=uuid)
        )[0]
    except IndexError:
        logger.debug(f"Individual with UUID {uuid} does not exist")
        raise NotFoundError(entity=uuid)
    else:
        logger.debug(f"Individual with UUID {uuid} was found")
        return individual


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
        logger.debug(f"Finding identity UUID {uuid} ...")
        identity = Identity.objects.get(uuid=uuid)
    except Identity.DoesNotExist:
        logger.debug(f"Identity with UUID {uuid} does not exist")
        raise NotFoundError(entity=uuid)
    else:
        logger.debug(f"Identity with UUID {uuid} was found")
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
        logger.debug(f"Finding organization '{name}' ...")
        organization = Organization.objects.all_organizations().get(name=name)
    except Organization.DoesNotExist:
        logger.debug(f"Organization with name '{name}' does not exist")
        raise NotFoundError(entity=name)
    else:
        logger.debug(f"Organization with name '{name}' was found")
        return organization


def find_team(team_name, organization=None):
    """Find a team.

    Finds a team by its name in the registry.
    If organization is passed, it looks for a team in that organization.

    When the team does not exist, the function will raise a `NotFoundError`.

    :param organization: name of the organization to which team belongs to
    :param team_name: name of the team to find
    :returns: a team object

    :raises NotFoundError: when the team with the
        given `name` does not exist in the `organization` specified.
    """
    validate_field('team_name', team_name)

    try:
        logger.debug(f"Finding team '{team_name}'" + f"in '{organization.name}' ..." if organization else "...")
        team = Team.objects.all_teams().get(name=team_name, parent_org=organization)
    except Team.DoesNotExist:
        logger.debug(f"Team with name '{team_name}' does not exist")
        raise NotFoundError(entity=team_name)
    else:
        logger.debug(f"Found team with name '{team_name}'")
        return team


def find_group(name, parent_org=None):
    """Find a group.

    Find an group by its name in the database. If a parent organization
    is passed, it looks for a team in that organization.

    When the group does not exist the function will raise
    a `NotFoundError`.

    :param name: name of the group to find
    :param parent_org: name of the group's parent organization

    :returns: a group object

    :raises NotFoundError: when the group with the
        given `name` does not exists.
    """
    validate_field('name', name)

    try:
        logger.debug(f"Finding group '{name}'" + f"in '{parent_org}' ..." if parent_org else "...")
        group = Group.objects.get(name=name, parent_org__name=parent_org)
    except Group.DoesNotExist:
        logger.debug(f"Group with name '{name}' does not exist")
        raise NotFoundError(entity=name)
    else:
        logger.debug(f"Group with name '{name}' was found")
        return group


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
        logger.debug(f"Finding domain '{domain_name}' ...")
        domain = Domain.objects.get(domain=domain_name)
    except Domain.DoesNotExist:
        logger.debug(f"Domain with name '{domain_name}' does not exist")
        raise NotFoundError(entity=domain_name)
    else:
        logger.debug(f"Domain with name '{domain_name}' was found")
        return domain


def search_enrollments_in_period(mk, group_name,
                                 parent_org=None,
                                 from_date=MIN_PERIOD_DATE,
                                 to_date=MIN_PERIOD_DATE):
    """Look for enrollments in a given period.

    Returns the enrollments of an individual for a given
    organization during period of time.

    An empty list will be returned when no enrollments could be
    found, due to the individual or the organization do not
    exist, or there are not enrollments assigned for that period.

    :param mk: main key of the individual
    :param group_name: name of the group
    :param parent_org: name of the group's parent organization
    :param from_date: starting date for the period
    :param to_date: ending date for the period

    :returns: a list of enrollment objects
    """
    logger.debug(
        f"Run enrollments search; "
        f"individual='{mk}' group='{group_name}'"
        f"from='{from_date}' to='{to_date}'"
    )
    return Enrollment.objects.filter(individual__mk=mk,
                                     group__name=group_name,
                                     group__parent_org__name=parent_org,
                                     start__lte=to_date, end__gte=from_date).order_by('start')


def add_organization(trxl, name):
    """Add an organization to the database.

    This function adds a new organization to the database,
    using the given `name` as an identifier. Name cannot be
    empty or `None`.

    It returns a new `Organization` object.

    :param trxl: TransactionsLog object from the method calling this one
    :param name: name of the organization

    :returns: a new organization

    :raises ValueError: when `name` is `None` or empty.
    :raises AlreadyExistsError: when an instance with the same name
        already exists in the database.
    """
    # Setting operation arguments before they are modified
    op_args = {
        'name': name
    }

    validate_field('name', name)

    # Check if there is an organization with the same name.
    # Groups have a unique together constraint for the 'name' and 'parent_org'
    # fields, but the latter is always null for organizations and MySQL doesn't
    # treat null values as equal
    if Organization.objects.all_organizations().filter(name=name).exists():
        raise AlreadyExistsError(entity=Organization.__name__, eid=name)

    organization = Organization(name=name)

    try:
        Group.add_root(instance=organization)
    except django.db.utils.IntegrityError as exc:
        _handle_integrity_error(Organization, exc)

    trxl.log_operation(op_type=Operation.OpType.ADD, entity_type='organization',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['name'])

    return organization


def delete_organization(trxl, organization):
    """Remove an organization from the database.

    Function that removes from the database the organization
    given in `organization`. Data related such as domains
    or enrollments are also removed.

    :param trxl: TransactionsLog object from the method calling this one
    :param organization: organization to remove
    """
    # Setting operation arguments before they are modified
    op_args = {
        'organization': organization.name
    }

    last_modified = datetime_utcnow()
    Individual.objects.filter(enrollments__group=organization).\
        update(last_modified=last_modified)

    organization.delete()

    trxl.log_operation(op_type=Operation.OpType.DELETE, entity_type='organization',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['organization'])


def add_team(trxl, team_name, organization=None, parent=None):
    """Add a team to the database.

    This function adds a new team to the database using `team_name` as its identifier.
    The new team will be created as a subteam of a parent, if parent is provided.
    The new team will also be linked to the organization object in `organization`.

    Values assigned to `team_name` cannot be `None` or empty.

    As a result, the function returns a new `Team` object.

    :param trxl: TransactionsLog object from the method calling this one
    :param team_name: name of the team
    :param organization: links the new team to this organization object
    :param parent: parent team of the new team

    :returns: a new team

    :raises ValueError: raised when `team_name` is `None` or an empty string;
    """
    # Setting operation arguments before they are modified
    op_args = {
        'organization': None if not organization else organization.name,
        'team_name': team_name,
        'parent': None if not parent else parent.name
    }

    validate_field('team_name', team_name)

    if not organization:
        if Team.objects.all_teams().filter(name=team_name, parent_org=organization).exists():
            raise AlreadyExistsError(entity=Team.__name__, eid=team_name)

    team = Team(name=team_name, parent_org=organization)

    try:
        if parent:
            team = parent.add_child(instance=team)
        elif organization:
            team = organization.add_child(instance=team)
        else:
            team = Team.add_root(instance=team)
    except django.db.utils.IntegrityError as exc:
        _handle_integrity_error(Team, exc)

    trxl.log_operation(op_type=Operation.OpType.ADD, entity_type='team',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['team_name'])
    return team


def add_domain(trxl, organization, domain_name, is_top_domain=True):
    """Add a domain to the database.

    This function adds a new domain to the database using
    `domain_name` as its identifier. The new domain will
    also be linked to the organization object in `organization`.

    Values assigned to `domain_name` cannot be `None` or empty.
    The parameter `is_top_domain` only accepts `bool` values.

    As a result, the function returns a new `Domain` object.

    :param trxl: TransactionsLog object from the method calling this one
    :param organization: links the new domain to this organization object
    :param domain_name: name of the domain
    :param is_top_domain: set this domain as a top domain

    :returns: a new domain

    :raises ValueError: raised when `domain_name` is `None` or an empty string;
        when `is_top_domain` does not have a `bool` value.
    """
    # Setting operation arguments before they are modified
    op_args = {
        'organization': organization.name,
        'domain_name': domain_name,
        'is_top_domain': is_top_domain
    }

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

    trxl.log_operation(op_type=Operation.OpType.ADD, entity_type='domain',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['organization'])

    return domain


def delete_domain(trxl, domain):
    """Remove a domain from the database.

    Deletes from the database the domain given in `domain`.

    :param trxl: TransactionsLog object from the method calling this one
    :param domain: domain to remove
    """
    # Setting operation arguments before they are modified
    op_args = {
        'domain': domain.domain
    }

    domain.delete()

    trxl.log_operation(op_type=Operation.OpType.DELETE, entity_type='domain',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['domain'])


def delete_team(trxl, team):
    """Remove a team and all its subteams from the database.

    Deletes from the database the team given in `team` as well as all teams with parent=`team`

    :param trxl: TransactionsLog object from the method calling this one
    :param team: team to remove
    """
    # Setting operation arguments before they are modified
    op_args = {
        'team': team.name
    }

    team.delete()

    trxl.log_operation(op_type=Operation.OpType.DELETE, entity_type='team',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['team'])


def add_individual(trxl, mk):
    """Add an individual to the database.

    This function adds an individual to the database with
    `mk` string as its main key (i.e main identifier). This
    identifier cannot be empty or `None`.

    When the individual is added, a new empty profile for
    this object is created too.

    As a result, the function returns a new `Individual`
    object.

    :param trxl: TransactionsLog object from the method calling this one
    :param mk: main key for the individual

    :returns: a new individual

    :raises ValueError: when `mk` is `None` or an empty string
    """
    # Setting operation arguments before they are modified
    op_args = {
        'mk': mk
    }

    validate_field('mk', mk)

    individual = Individual(mk=mk)

    try:
        individual.save(force_insert=True)
    except django.db.utils.IntegrityError as exc:
        _handle_integrity_error(Individual, exc)

    trxl.log_operation(op_type=Operation.OpType.ADD, entity_type='individual',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['mk'])

    profile = Profile(individual=individual)

    try:
        profile.save()
    except django.db.utils.IntegrityError as exc:
        _handle_integrity_error(Profile, exc)

    individual.refresh_from_db()

    return individual


def delete_individual(trxl, individual):
    """Remove an individual from the database.

    Function that removes from the database the individual
    given in `individual`. Data related to it will be also
    removed.

    :param trxl: TransactionsLog object from the method calling this one
    :param individual: individual to remove
    """
    # Setting operation arguments before they are modified
    op_args = {
        'individual': individual.mk
    }

    if individual.is_locked:
        raise LockedIdentityError(uuid=individual.mk)

    individual.delete()

    trxl.log_operation(op_type=Operation.OpType.DELETE, entity_type='individual',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['individual'])


def add_identity(trxl, individual, uuid, source,
                 name=None, email=None, username=None):
    """Add an identity to the database.

    This function adds a new identity to the database using
    `uuid` as its identifier. The new identity will
    also be linked to the individual object of `individual`.

    Neither the values given to `uuid` nor to `source` can
    be `None` or empty. Moreover, `name`, `email` or `username`
    parameters need a non empty value.

    As a result, the function returns a new `Identity` object.

    :param trxl: TransactionsLog object from the method calling this one
    :param individual: links the new identity to this individual object
    :param uuid: identifier for the new identity
    :param source: data source where this identity was found
    :param name: full name of the identity
    :param email: email of the identity
    :param username: user name used by the identity

    :returns: a new identity

    :raises ValueError: when `uuid` and `source` are `None` or empty;
        when all of the data parameters are `None` or empty.
    """
    # Setting operation arguments before they are modified
    op_args = {
        'individual': individual.mk,
        'uuid': uuid,
        'source': source,
        'name': name,
        'email': email,
        'username': username
    }

    if individual.is_locked:
        raise LockedIdentityError(uuid=individual.mk)

    validate_field('uuid', uuid)
    validate_field('source', source)
    validate_field('name', name, allow_none=True)
    validate_field('email', email, allow_none=True)
    validate_field('username', username, allow_none=True)

    if not (name or email or username):
        raise ValueError("identity data cannot be None or empty")

    try:
        identity = Identity(uuid=uuid, name=name, email=email,
                            username=username, source=source,
                            individual=individual)
        identity.save(force_insert=True)
        individual.save()
    except django.db.utils.IntegrityError as exc:
        _handle_integrity_error(Identity, exc)

    trxl.log_operation(op_type=Operation.OpType.ADD, entity_type='identity',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['individual'])

    return identity


def delete_identity(trxl, identity):
    """Remove an identity from the database.

    This function removes from the database the identity given
    in `identity`. Take into account this function does not
    remove individual in the case they get empty.

    :param trxl: TransactionsLog object from the method calling this one
    :param identity: identity to remove
    """
    # Setting operation arguments before they are modified
    op_args = {
        'identity': identity.uuid
    }

    if identity.individual.is_locked:
        raise LockedIdentityError(uuid=identity.individual.mk)

    identity.delete()
    identity.individual.save()

    trxl.log_operation(op_type=Operation.OpType.DELETE, entity_type='identity',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['identity'])


def update_profile(trxl, individual, **kwargs):
    """Update individual profile.

    This function allows to edit or update the profile information
    of the given individual. The values to update are given
    as keyword arguments. The allowed keys are listed below
    (other keywords will be ignored):

       - `name`: name of the individual
       - `email`: email address of the individual
       - `gender`: gender of the individual
       - `gender_acc`: gender accuracy (range of 1 to 100; by default, set to 100)
       - `is_bot`: boolean value to determine whether an individual is
             a bot or not. By default, this value is initialized to
             `False`.
       - `country_code`: ISO-3166 country code

    As a result, it will return the `Individual` object with
    the updated data.

    :param trxl: TransactionsLog object from the method calling this one
    :param individual: individual whose profile will be updated
    :param kwargs: parameters to edit the profile

    :returns: individual object with the updated profile

    :raises ValueError: raised either when `is_bot` does not have a boolean value;
        `gender_acc` is not an `int` or is not in range.
    """

    def to_none_if_empty(x):
        return None if not x else x

    # Setting operation arguments before they are modified
    op_args = copy.deepcopy(kwargs)
    op_args.update({'individual': individual.mk})

    if individual.is_locked:
        raise LockedIdentityError(uuid=individual.mk)

    profile = individual.profile

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
    individual.save()

    trxl.log_operation(op_type=Operation.OpType.UPDATE, entity_type='profile',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['individual'])

    return individual


def add_enrollment(trxl, individual, group,
                   start=MIN_PERIOD_DATE, end=MAX_PERIOD_DATE):
    """Enroll an individual to an organization in the database.

    The function adds a new relationship between the individual
    in `individual` and the given `organization` to the database.

    The period of the enrollment can be given with the parameters
    `from_date` and `to_date`, where `from_date <= to_date`.
    Default values for these dates are `MIN_PERIOD_DATE` and
    `MAX_PERIOD_DATE`. These dates cannot be `None`.

    This function returns as result a new `Enrollment` object.

    :param trxl: TransactionsLog object from the method calling this one
    :param individual: individual to enroll
    :param group: group where the individual is enrolled
    :param start: date when the enrollment starts
    :param end: date when the enrollment ends

    :returns: a new enrollment

    :raises ValueError: when either `start` or `end` are `None`;
        when `start < MIN_PERIOD_DATE`; or `end > MAX_PERIOD_DATE`
        or `start > end`.
    """
    # Setting operation arguments before they are modified
    op_args = {
        'individual': individual.mk,
        'group': group.name,
        'start': copy.deepcopy(str(start)),
        'end': copy.deepcopy(str(end))
    }

    if individual.is_locked:
        raise LockedIdentityError(uuid=individual.mk)

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
        enrollment = Enrollment(individual=individual,
                                group=group,
                                start=start, end=end)
        enrollment.save()
        individual.save()
    except django.db.utils.IntegrityError as exc:
        _handle_integrity_error(Identity, exc)

    trxl.log_operation(op_type=Operation.OpType.ADD, entity_type='enrollment',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['individual'])

    return enrollment


def delete_enrollment(trxl, enrollment):
    """Remove an enrollment from the database.

    This function removes from the database the enrollment given
    in `enrollment`.

    :param trxl: TransactionsLog object from the method calling this one
    :param enrollment: enrollment object to remove
    """
    # Setting operation arguments before they are modified
    op_args = {
        'mk': enrollment.individual.mk,
        'group': enrollment.group.name,
        'start': str(enrollment.start),
        'end': str(enrollment.end)
    }

    if enrollment.individual.is_locked:
        raise LockedIdentityError(uuid=enrollment.individual.mk)

    enrollment.delete()
    enrollment.individual.save()

    trxl.log_operation(op_type=Operation.OpType.DELETE, entity_type='enrollment',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['mk'])


def move_identity(trxl, identity, individual):
    """Move an identity to an individual.

    Shifts `identity` to the individual given in `individual`.
    As a result, it will return `individual` object with list of
    identities updated.

    When `identity` is already assigned to `individual`, the function
    will raise an `ValueError` exception.

    :param trxl: TransactionsLog object from the method calling this one
    :param identity: identity to be moved
    :param individual: individual where `identity` will be moved

    :returns: the individual with related identities updated

    :raises ValueError: when `identity` is already part of `individual`
    """
    # Setting operation arguments before they are modified
    op_args = {
        'identity': identity.uuid,
        'individual': individual.mk
    }

    if identity.individual.is_locked:
        raise LockedIdentityError(uuid=identity.individual.mk)
    if individual.is_locked:
        raise LockedIdentityError(uuid=individual.mk)
    if identity.individual == individual:
        msg = "identity '{}' is already assigned to '{}'".format(identity.uuid, individual.mk)
        raise ValueError(msg)

    old_individual = identity.individual
    identity.individual = individual

    identity.save()
    old_individual.save()
    individual.save()

    trxl.log_operation(op_type=Operation.OpType.UPDATE, entity_type='identity',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['identity'])

    return individual


def lock(trxl, individual):
    """Lock a given individual.

    Locks a given `individual` object so this object and its related objects
    such as identities, enrollments or its profile cannot be modified.

    :param trxl: TransactionsLog object from the method calling this one
    :param individual: individual which will be locked

    :returns: the individual with lock parameter updated
    """
    op_args = {
        'mk': individual.mk,
        'is_locked': True
    }

    _set_lock(individual, True)

    trxl.log_operation(op_type=Operation.OpType.UPDATE, entity_type='individual',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['mk'])

    return individual


def unlock(trxl, individual):
    """Unlock a given individual.

    Unlocks a given `individual` object so this object and its related objects
    such as identities, enrollments or its profile can be modified.

    :param trxl: TransactionsLog object from the method calling this one
    :param individual: individual which will be unlocked

    :returns: the individual with lock parameter updated
    """
    op_args = {
        'mk': individual.mk,
        'is_locked': False
    }

    _set_lock(individual, False)

    trxl.log_operation(op_type=Operation.OpType.UPDATE, entity_type='individual',
                       timestamp=datetime_utcnow(), args=op_args,
                       target=op_args['mk'])

    return individual


_MYSQL_DUPLICATE_ENTRY_ERROR_REGEX = re.compile(r"Duplicate entry '(?P<value>.+)' for key")


def _handle_integrity_error(model, exc):
    """Handle integrity error exceptions."""

    logger.debug("Database operation aborted; integrity error;",
                 exc_info=True)
    m = re.match(_MYSQL_DUPLICATE_ENTRY_ERROR_REGEX,
                 exc.__cause__.args[1])
    if not m:
        raise exc

    entity = model.__name__
    eid = m.group('value')

    if model == Team:
        eid = m.group('value').split('-')[0]

    raise AlreadyExistsError(entity=entity, eid=eid)
