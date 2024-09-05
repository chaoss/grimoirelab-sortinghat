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

import logging

from grimoirelab_toolkit.datetime import datetime_to_utc, datetime_utcnow

from .db import (find_individual_by_uuid,
                 find_identity,
                 find_organization,
                 find_domain,
                 find_team,
                 find_group,
                 find_scheduled_task,
                 find_alias,
                 search_enrollments_in_period,
                 add_individual as add_individual_db,
                 add_identity as add_identity_db,
                 add_organization as add_organization_db,
                 add_scheduled_task as add_scheduled_task_db,
                 add_team as add_team_db,
                 add_domain as add_domain_db,
                 add_alias as add_alias_db,
                 delete_individual as delete_individual_db,
                 delete_identity as delete_identity_db,
                 delete_organization as delete_organization_db,
                 delete_team as delete_team_db,
                 delete_scheduled_task as delete_scheduled_task_db,
                 delete_domain as delete_domain_db,
                 delete_alias as delete_alias_db,
                 delete_merge_recommendations as delete_merge_recommendations_db,
                 update_profile as update_profile_db,
                 update_scheduled_task as update_scheduled_task_db,
                 move_identity as move_identity_db,
                 lock as lock_db,
                 unlock as unlock_db,
                 add_enrollment,
                 delete_enrollment,
                 move_domain,
                 move_team,
                 move_alias,
                 review as review_db)
from .errors import (InvalidValueError,
                     AlreadyExistsError,
                     NotFoundError,
                     DuplicateRangeError,
                     EqualIndividualError)
from .log import TransactionsLog
from .models import Identity, MergeRecommendation, MIN_PERIOD_DATE, MAX_PERIOD_DATE
from .aux import merge_datetime_ranges
from .decorators import atomic_using_tenant
from ..utils import generate_uuid


logger = logging.getLogger(__name__)


@atomic_using_tenant
def add_identity(ctx, source, name=None, email=None, username=None, uuid=None):
    """Add an identity to the registry.

    This function adds a new identity to the registry. By default,
    a new individual will be also added and associated to
    the new identity.

    When `uuid` parameter is set, it creates a new identity that
    will be associated to the individual defined by this
    identifier. Consider that any UUID of the identities of the
    individual is a valid identifier. Also, this identifier must
    exist on the registry. If it does not exist, the function will
    raise a `NotFoundError` exception.

    When no `uuid` is given, both new individual and identity
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
    :param uuid: associates the new identity to the individual
        identified by this id

    :returns: a universal unique identifier

    :raises InvalidValueError: when `source` is `None` or empty;
        when all the identity parameters are `None` or empty.
    :raises AlreadyExistsError: raised when the identity already
        exists in the registry.
    :raises NotFoundError: raised when the individual
        associated to the given `uuid` is not in the registry.
    """
    trxl = TransactionsLog.open('add_identity', ctx)

    try:
        id_ = generate_uuid(source, email=email,
                            name=name, username=username)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    if not uuid:
        individual = add_individual_db(trxl, id_)
        # In case there is no name, set `username` as profile name
        profile_name = name if name else username
        individual = update_profile_db(trxl, individual,
                                       name=profile_name, email=email)
    else:
        individual = find_individual_by_uuid(uuid)

    args = {
        'trxl': trxl,
        'individual': individual,
        'uuid': id_,
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

    if not uuid:
        logger.info(f"Individual {individual.mk} created")

    logger.info(f"Identity {identity.uuid} created for individual {individual.mk}")

    return identity


@atomic_using_tenant
def delete_identity(ctx, uuid):
    """Remove an identity from the registry.

    This function removes from the registry the identity which
    its identifier matches with `uuid`. When the `uuid` also
    belongs to an individual, this entry and those identities
    linked to it will be removed too. The value of this identifier
    cannot be empty.

    If the identifier is not found in the registry a 'NotFoundError'
    exception is raised.

    As a result, the function will return an updated version of the
    individual with the identity removed. If the deleted entry
    was an individual, the returned value will be `None` because
    this object was wiped out.

    :param ctx: context from where this method is called
    :param uuid: identifier assigned to the identity or individual
        that will be removed

    :returns: an individual with the identity removed; `None` when
        the individual was also removed.

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
    individual = identity.individual

    if individual.mk == uuid:
        delete_individual_db(trxl, identity.individual)
        individual = None
    else:
        delete_identity_db(trxl, identity)
        individual.refresh_from_db()

    trxl.close()

    logger.info(f"Identity {uuid} deleted")

    if not individual:
        logger.info(f"Individual {uuid} deleted")

    return individual


@atomic_using_tenant
def update_profile(ctx, uuid, **kwargs):
    """Update individual profile.

    This function allows to edit or update the profile information
    of the individual identified by `uuid`. Take into account that
    any UUID of the identities of the individual is a valid identifier.

    The values to update are given as keyword arguments. The allowed
    keys are listed below (other keywords will be ignored):

       - 'name' : name of the individual
       - 'email' : email address of the individual
       - 'gender' : gender of the individual
       - 'gender_acc' : gender accuracy (range of 1 to 100; by default,
             set to 100)
       - 'is_bot' : boolean value to determine whether an individual is
             a bot or not. By default, this value is initialized to
             `False`.
       - 'country_code' : ISO-3166 country code

    The result of calling this function will be the `Individual`
    object with an updated profile.

    :param ctx: context from where this method is called
    :param uuid: identifier of the individual which its project
        will be updated
    :param kwargs: keyword arguments with data to update the profile

    :returns: an individual with its profile updated

    :raises NotFoundError: raised when either the individual
        or the country code do not exist in the registry.
    :raises InvalidValueError: raised when any of the keyword arguments
        has an invalid value.
    """
    trxl = TransactionsLog.open('update_profile', ctx)

    individual = find_individual_by_uuid(uuid)

    try:
        individual = update_profile_db(trxl, individual, **kwargs)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    trxl.close()

    logger.info(f"Identity {uuid} profile successfully updated")

    return individual


@atomic_using_tenant
def move_identity(ctx, from_uuid, to_uuid):
    """Move an identity to an individual.

    This function shifts the identity identified by `from_uuid` to
    the individual identified by `to_uuid`. Take into account that
    any UUID of the identities of the individual is a valid
    identifier.

    When `to_uuid` is an UUID of the individual that is currently
    related to `from_uuid`, the action does not have any effect.

    In the case of `from_uuid` and `to_uuid` have equal values and the
    individual does not exist, a new individual will be created
    and the identity will be moved to it.

    When `from_uuid` exists as an individual too, the function raises
    an `InvalidValueError`, as this identity cannot be moved.

    The function raises a `NotFoundError` exception when either `from_uuid`
    or `to_uuid` do not exist in the registry and both identifiers are
    not the same.

    The individual object with updated identities data is returned
    as the result of calling this function.

    :param ctx: context from where this method is called
    :param from_uuid: identifier of the identity set to be moved
    :param to_uuid: identifier of the individual where 'from_uuid'
        will be moved

    :returns: an individual with identities data updated

    :raises NotFoundError: raised when either `from_uuid` or `to_uuid`
        do not exist in the registry.
    :raises InvalidValueError: raised when either `from_uuid' or `to_uuid`
        are `None` or empty strings,
    """
    if from_uuid is None:
        raise InvalidValueError(msg="'from_uuid' cannot be None")
    if from_uuid == '':
        raise InvalidValueError(msg="'from_uuid' cannot be an empty string")
    if to_uuid is None:
        raise InvalidValueError(msg="'to_uuid' cannot be None")
    if to_uuid == '':
        raise InvalidValueError(msg="'to_uuid' cannot be an empty string")

    trxl = TransactionsLog.open('move_identity', ctx)

    identity = find_identity(from_uuid)

    if identity.uuid == identity.individual.mk:
        msg = "'from_uuid' is an individual and it cannot be moved; use 'merge' instead"
        raise InvalidValueError(msg=msg)
    elif identity.uuid == to_uuid:
        to_indv = add_individual_db(trxl, identity.uuid)
        to_indv = update_profile_db(trxl, to_indv,
                                    name=identity.name,
                                    email=identity.email)
    else:
        to_indv = find_individual_by_uuid(to_uuid)

    try:
        individual = move_identity_db(trxl, identity, to_indv)
    except ValueError:
        # Case when the identity is already assigned to the individual
        individual = to_indv

    trxl.close()

    logger.info(f"Identity {from_uuid} moved to {to_uuid}")

    return individual


@atomic_using_tenant
def lock(ctx, uuid):
    """Lock an individual so it cannot be modified.

    This function locks the individual identified by `uuid`
    so this object and its related objects such as identities,
    enrollments or the profile cannot be modified.

    :param ctx: context from where this method is called
    :param uuid: identifier of the individual which will be locked

    :returns: an individual with its locked value updated

    :raises InvalidValueError: raised when `uuid` is `None` or an empty string
    :raises NotFoundError: when the identity with the
        given `uuid` does not exists.
    """
    if uuid is None:
        raise InvalidValueError(msg="'uuid' cannot be None")
    if uuid == '':
        raise InvalidValueError(msg="'uuid' cannot be an empty string")

    trxl = TransactionsLog.open('lock', ctx)

    individual = find_individual_by_uuid(uuid)
    individual = lock_db(trxl, individual)

    trxl.close()

    logger.info(f"Individual {uuid} successfully locked")

    return individual


@atomic_using_tenant
def unlock(ctx, uuid):
    """Unlock an individual so it can be modified.

    This function unlocks the individual identified by `uuid`
    so this object and its related objects such as identities,
    enrollments or the profile can be modified.

    :param ctx: context from where this method is called
    :param uuid: identifier of the individual which will be unlocked

    :returns: an individual with its locked value updated

    :raises InvalidValueError: raised when `uuid` is `None` or an empty string
    :raises NotFoundError: when the identity with the
        given `uuid` does not exists.
    """
    if uuid is None:
        raise InvalidValueError(msg="'uuid' cannot be None")
    if uuid == '':
        raise InvalidValueError(msg="'uuid' cannot be an empty string")

    trxl = TransactionsLog.open('unlock', ctx)

    individual = find_individual_by_uuid(uuid)
    individual = unlock_db(trxl, individual)

    trxl.close()

    logger.info(f"Individual {uuid} successfully unlocked")

    return individual


@atomic_using_tenant
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

    logger.info(f"Organization {org.name} created")

    return org


@atomic_using_tenant
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

    logger.info(f"Domain {domain.domain} created for organization {organization.name}")

    return domain


@atomic_using_tenant
def add_alias(ctx, organization, name):
    """Add an alias to the registry.

    This function adds a new alias to a given organization.
    The organization must exist on the registry prior to insert the new
    alias. Otherwise, it will raise a `NotFoundError` exception. Moreover,
    if the given alias is already in the registry an `AlreadyExistsError`
    exception will be raised.

    :param ctx: context from where this method is called
    :param organization: name of the organization
    :param name: alias to add to the registry

    :returns the new alias object

    :raises InvalidValueError: raised when alias is None or an empty string or
        when it is the same as the organization name
    :raises NotFoundError: raised when the given organization is not found
        in the registry
    :raises AlreadyExistsError: raised when the alias already exists
        in the registry
    """
    if organization is None:
        raise InvalidValueError(msg="'organization' cannot be None")
    if organization == '':
        raise InvalidValueError(msg="'organization' cannot be an empty string")
    if name is None:
        raise InvalidValueError(msg="'name' cannot be None")
    if name == '':
        raise InvalidValueError(msg="'name' cannot be an empty string")
    if name == organization:
        raise InvalidValueError(msg="'name' cannot be the same as 'organization'")

    trxl = TransactionsLog.open('add_alias', ctx)

    try:
        organization = find_organization(organization)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))
    except NotFoundError as exc:
        raise exc

    try:
        alias = add_alias_db(trxl, organization=organization, name=name)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))
    except AlreadyExistsError as exc:
        raise exc

    trxl.close()

    logger.info(f"Alias {alias.alias} created for organization {organization.name}")

    return alias


@atomic_using_tenant
def add_team(ctx, team_name, organization=None, parent_name=None):
    """Add a team to the registry.

    This function creates a new team. If organization is given, the team is added to
    the organization. The organization must exist on the registry prior to insert the new
    team. Otherwise, it will raise a `NotFoundError` exception. Moreover,
    if the given team already exists in the organization, an `AlreadyExistsError`
    exception will be raised.

    If a `parent_name` is passed to the function, the team is created as a subteam of
    the parent in the organization.

    :param ctx: context from where this method is called
    :param team_name: new team to be created
    :param organization: name of the organization
    :param parent_name: parent under which new team needs to be created

    :returns the new team object

    :raises InvalidValueError: raised when organization is an empty string or team_name is None or
        an empty string
    :raises NotFoundError: raised when the given organization or parent is not found
        in the registry
    :raises AlreadyExistsError: raised when the team already exists
        in the registry
    """

    if organization == '':
        raise InvalidValueError(msg="'org_name' cannot be an empty string")
    if team_name is None:
        raise InvalidValueError(msg="'team_name' cannot be None")
    if team_name == '':
        raise InvalidValueError(msg="'team_name' cannot be an empty string")

    trxl = TransactionsLog.open('add_team', ctx)

    if organization:
        try:
            organization = find_organization(organization)
        except ValueError as e:
            raise InvalidValueError(msg=str(e))
        except NotFoundError as esc:
            raise esc

    parent = None
    if parent_name:
        try:
            parent = find_team(parent_name, organization)
        except ValueError as e:
            raise InvalidValueError(msg=str(e))
        except NotFoundError as esc:
            raise esc

    try:
        team = add_team_db(trxl, team_name=team_name, organization=organization,
                           parent=parent)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))
    except AlreadyExistsError as exc:
        raise exc

    trxl.close()
    logger.info(f"Team {team.name} created " + f"for {organization.name}" if organization else "")
    return team


@atomic_using_tenant
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

    logger.info(f"Organization {name} deleted")

    return org


@atomic_using_tenant
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

    logger.info(f"Domain {domain_name} deleted")

    return domain


@atomic_using_tenant
def delete_alias(ctx, name):
    """Remove an alias from the registry.

    This function removes the given alias from the registry.
    Alias must exist in the registry. Otherwise, it will raise
    a `NotFoundError` exception.

    :param ctx: context from where this method is called
    :param name: name to remove

    :returns the removed alias object

    :raises NotFoundError: raised when the alias
        does not exist in the registry.
    """
    if name is None:
        raise InvalidValueError(msg="'name' cannot be None")
    if name == '':
        raise InvalidValueError(msg="'name' cannot be an empty string")

    trxl = TransactionsLog.open('delete_alias', ctx)

    try:
        alias = find_alias(name)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))
    except NotFoundError as exc:
        raise exc

    delete_alias_db(trxl, alias)

    trxl.close()

    logger.info(f"Alias {name} deleted")

    return alias


@atomic_using_tenant
def delete_team(ctx, team_name, organization=None):
    """Remove a team from the registry.

    This function removes the given team from the registry.
    Deleting a team also deletes all its subteams from the registry.
    If the team belongs to an Organization, the organization name must
    be passed. Both Organization and Team must exist in the registry.
    Otherwise, function will raise a `NotFoundError` exception.

    :param ctx: context from where this method is called
    :param team_name: team to be deleted
    :param organization: name of the organization that team belongs to

    :returns the removed team object

    :raises NotFoundError: raised when the team does not
        exist in the registry.
    :raises InvalidValueError: raised when the team name
        is None or an empty string or when organization name
        is invalid.
    """
    if team_name is None:
        raise InvalidValueError(msg="'team_name' cannot be None")
    if team_name == '':
        raise InvalidValueError(msg="'team_name' cannot be an empty string")

    trxl = TransactionsLog.open('delete_team', ctx)

    if organization:
        try:
            organization = find_organization(organization)
        except ValueError as e:
            raise InvalidValueError(msg=str(e))
        except NotFoundError as exc:
            raise exc

    try:
        team = find_team(team_name, organization)
    except NotFoundError as exc:
        raise exc

    delete_team_db(trxl, team)

    trxl.close()
    logger.info(f"Team {team.name} deleted")
    return team


@atomic_using_tenant
def enroll(ctx, uuid, group, parent_org=None, from_date=None, to_date=None,
           force=False):
    """Enroll an individual in a group.

    The function enrolls an individual, identified by `uuid`,
    in the given `group`. Both identity and group must
    exist before adding this enrollment to the registry. Otherwise,
    a `NotFoundError` exception will be raised. As in other functions,
    any UUID of the identities of the individual is a valid identifier.

    The period of the enrollment can be given with the parameters
    `from_date` and `to_date`, where `from_date <= to_date`. Default
    values for these dates are `1900-01-01` and `2100-01-01`.

    Existing enrollments for the same individual and group
    which overlap with the new period will be merged into a single
    enrollment.

    If the given period for that enrollment is enclosed by one already
    stored, the function will raise an `DuplicateRangeError` exception.

    In case the option `force` is set to `True`, and there is an
    existing enrollment having a range composed by any of the default start
    or end dates, the range will be overwritten with the new `from_date` and
    `to_date` values.

    The individual object with updated enrollment data is returned
    as the result of calling this function.

    :param ctx: context from where this method is called
    :param uuid: unique identifier
    :param group: name of the group
    :param parent_org: name of the group's parent organization
    :param from_date: date when the enrollment starts
    :param to_date: date when the enrollment ends
    :param force: overwrite default dates in case a more specific date
        is provided

    :returns: an individual with enrollment data updated

    :raises NotFoundError: when either `uuid` or `organization` are not
        found in the registry.
    :raises InvalidValueError: raised in three cases, when either identity or
        group are None or empty strings; when "from_date" < 1900-01-01 or
        "to_date" > 2100-01-01; when "from_date > to_date".
    :raises DuplicateRangeError: raised when the given period for that enrollment
        already exists in the registry.
    """
    if uuid is None:
        raise InvalidValueError(msg="'uuid' cannot be None")
    if uuid == '':
        raise InvalidValueError(msg="'uuid' cannot be an empty string")
    if group is None:
        raise InvalidValueError(msg="'group' cannot be None")
    if group == '':
        raise InvalidValueError(msg="'group' cannot be an empty string")

    trxl = TransactionsLog.open('enroll', ctx)

    from_date = datetime_to_utc(from_date) if from_date else MIN_PERIOD_DATE
    to_date = datetime_to_utc(to_date) if to_date else MAX_PERIOD_DATE

    if from_date > to_date:
        msg = "'start' date {} cannot be greater than {}".format(from_date, to_date)
        raise InvalidValueError(msg=msg)

    # Find and check entities
    individual = find_individual_by_uuid(uuid)
    group = find_group(group, parent_org)

    # Get the list of current ranges
    # Check whether the new one already exist
    enrollments_db = search_enrollments_in_period(individual.mk, group.name,
                                                  parent_org=parent_org,
                                                  from_date=from_date,
                                                  to_date=to_date)

    periods = [[enr_db.start, enr_db.end] for enr_db in enrollments_db]

    for period in periods:
        if from_date >= period[0] and to_date <= period[1]:
            # If any of the dates are the default ones
            default_values = (period[0] == MIN_PERIOD_DATE) or (period[1] == MAX_PERIOD_DATE)
            if default_values and force:
                # Default values will be overwritten with input values
                continue
            raise DuplicateRangeError(start=from_date, end=to_date, group=group)
        if to_date < period[0]:
            break

    periods.append([from_date, to_date])

    # Remove old enrollments and add new ones based in the new ranges
    for enrollment_db in enrollments_db:
        delete_enrollment(trxl, enrollment_db)

    try:
        dt_ranges = merge_datetime_ranges(periods, exclude_limits=force)
        for start_dt, end_dt in dt_ranges:
            add_enrollment(trxl, individual, group, start=start_dt, end=end_dt)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    individual.refresh_from_db()

    trxl.close()

    logger.info(
        f"Individual {uuid} enrolled to {group}; "
        f"from='{from_date}' to='{to_date}'"
    )

    return individual


@atomic_using_tenant
def withdraw(ctx, uuid, group, parent_org=None, from_date=None, to_date=None):
    """Withdraw an individual from a group.

    This function withdraws an individual identified by `uuid`
    from the given `group` during the given period of time.
    As in other functions, any UUID of the identities of the individual
    is a valid identifier.

    For example, if the individual `A` was enrolled from `2010-01-01`
    to `2018-01-01` to the group `Example`, the result of withdrawing
    that identity from `2014-01-01` to `2016-01-01` will be two enrollments
    for that identity: one for the period 2010-2014 and another one for
    the period 2016-2018. If the period of withdrawing encloses minimum
    and maximum dates, all the enrollments will be removed.

    Both `uuid` and `group` must exist before being deleted.
    Moreover, an enrollment during the given period must exist.
    Otherwise, it will raise a `NotFoundError` exception.

    The period of the enrollment can be given with the parameters
    `from_date` and `to_date`, where `from_date <= to_date`. Default
    values for these dates are `1900-01-01` and `2100-01-01`.

    The individual object with updated enrollment data is returned
    as the result of calling this function.

    :param ctx: context from where this method is called
    :param uuid: unique identifier
    :param group: name of the group
    :param parent_org: name of the group's parent organization
    :param from_date: date when the enrollment starts
    :param to_date: date when the enrollment ends

    :returns: an individual with enrollment data updated

    :raises NotFoundError: when either `uuid` or `group` are not
        found in the registry or when the identity is not enrolled
        in that organization for the given period
    :raises InvalidValeError: raised in three cases, when either identity or
        organization are `None` or empty strings; when "from_date" < 1900-01-01 or
        "to_date" > 2100-01-01; when "from_date > to_date"
    """
    if uuid is None:
        raise InvalidValueError(msg="'uuid' cannot be None")
    if uuid == '':
        raise InvalidValueError(msg="'uuid' cannot be an empty string")
    if group is None:
        raise InvalidValueError(msg="'group' cannot be None")
    if group == '':
        raise InvalidValueError(msg="'group' cannot be an empty string")

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
    individual = find_individual_by_uuid(uuid)
    group = find_group(group, parent_org=parent_org)

    # Get the list of current ranges
    # Check whether any enrollment for the given period exist
    enrollments_db = search_enrollments_in_period(individual.mk, group.name,
                                                  parent_org=parent_org,
                                                  from_date=from_date,
                                                  to_date=to_date)

    if not enrollments_db:
        eid = "enrollment with range '{}'-'{}' for {}".format(from_date,
                                                              to_date,
                                                              group)
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
            add_enrollment(trxl, individual, group, start=min_range, end=from_date)
        if max_range > to_date:
            add_enrollment(trxl, individual, group, start=to_date, end=max_range)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    individual.refresh_from_db()

    trxl.close()

    logger.info(
        f"Individual {uuid} withdrawn from {group}; "
        f"from='{from_date}' to='{to_date}';"
    )

    return individual


@atomic_using_tenant
def update_enrollment(ctx, uuid, group, from_date, to_date, parent_org=None,
                      new_from_date=None, new_to_date=None, force=True):
    """Update one or more enrollments from an individual given a new date range.

    Use this method to update atomically an individual's enrollment or set
    of enrollments defined by the initial date range to a new date range.

    As in the enroll method wider date ranges get merged into the wider one,
    this method withdraws the enrollments from the old date range and
    set a new enrollment with the new date range. By default, the `force`
    parameter is set to `True`, as it overwrites default dates in case a more
    specific date is provided when the updated enrollment is added.

    In case any of the new dates are missing, the former value for that date
    will be preserved.

    :param ctx: context from where this method is called
    :param uuid: unique identifier
    :param group: name of the group
    :param parent_org: name of the group's parent organization
    :param from_date: date when the enrollment(s) to be updated starts
    :param to_date: date when the enrollment(s) to be updated ends
    :param new_from_date: date when the new enrollment starts
    :param new_to_date: date when the new enrollment ends
    :param force: overwrite default dates in case a more specific date
        is provided

    :returns: an individual with enrollment data updated

    :raises NotFoundError: when either `uuid` or `group` are not
        found in the registry or when the identity is not enrolled
        in that group for the given period
    :raises InvalidValeError: raised in three cases, when either identity or
        group are `None` or empty strings; when "from_date" < 1900-01-01 or
        "to_date" > 2100-01-01; when "from_date > to_date"
    """
    if uuid is None:
        raise InvalidValueError(msg="'uuid' cannot be None")
    if uuid == '':
        raise InvalidValueError(msg="'uuid' cannot be an empty string")
    if group is None:
        raise InvalidValueError(msg="'group' cannot be None")
    if group == '':
        raise InvalidValueError(msg="'group' cannot be an empty string")
    if from_date is None:
        raise InvalidValueError(msg="'from_date' cannot be None")
    if from_date == '':
        raise InvalidValueError(msg="'from_date' cannot be empty")
    if to_date is None:
        raise InvalidValueError(msg="'to_date' cannot be None")
    if to_date == '':
        raise InvalidValueError(msg="'to_date' cannot be empty")
    if (not new_from_date) and (not new_to_date):
        raise InvalidValueError(msg="'new_from_date' and 'to_from_date' cannot be None at the same time")
    if (new_from_date == '') and (new_to_date == ''):
        raise InvalidValueError(msg="'new_from_date' and 'to_from_date' cannot be empty at the same time")

    # If any of the new dates is not provided, its value will be set as the former date values
    new_from_date = new_from_date if new_from_date else from_date
    new_to_date = new_to_date if new_to_date else to_date

    if from_date > to_date:
        msg = "'from_date' date {} cannot be greater than {}".format(from_date, to_date)
        raise InvalidValueError(msg=msg)

    if new_from_date > new_to_date:
        msg = "'new_from_date' date {} cannot be greater than {}".format(new_from_date, new_to_date)
        raise InvalidValueError(msg=msg)

    trxl = TransactionsLog.open('update_enrollment', ctx)

    # Remove the enrollment(s) associated with the old dates
    withdraw(ctx, uuid, group, parent_org=parent_org, from_date=from_date, to_date=to_date)

    # Add the enrollment with the new dates
    indv = enroll(ctx, uuid, group, parent_org=parent_org,
                  from_date=new_from_date, to_date=new_to_date, force=force)

    trxl.close()

    logger.info(
        f"Individual {uuid} enrollments of {group} updated; "
        f"from='{from_date}' to='{to_date}'; new_from='{new_from_date}' new_to='{new_to_date}';"
    )

    return indv


@atomic_using_tenant
def merge(ctx, from_uuids, to_uuid):
    """
    Merge one or more individuals into another.

    Use this function to join a list of individuals, defined in `from_uuid`
    by any of their valid identities ids, into `to_uuid` individual.
    Identities and enrollments related to each `from_uuid` will be assigned
    to `to_uuid`. In addition, each `from_uuid` will be removed from the
    registry. Duplicated enrollments will be also removed from the registry
    while overlapped enrollments will be merged.

    Take into account that individuals are identified by any of the UUIDs
    assigned to their identities.

    This function also merges two or more profiles. When a field on `to_uuid`
    profile is `None` or empty, it will be updated with the value on the
    profile of each `from_uuid`. If any of the individuals was set as a bot,
    the new profile will also be set as a bot.

    When any of the `from_uuid` and `to_uuid` are equal, or any of this two
    fields are `None` or empty, it raises an `InvalidValueError`.

    The function raises a `NotFoundError` exception when either any `from_uuid`
    or `to_uuid` do not exist in the registry.

    :param ctx: context from where this method is called
    :param from_uuids: List of identifiers of the individuals set to merge
    :param to_uuid: identifier of the individual where `from_uuids`
        will be merged

    :returns: a Individual object as the result of the merged individuals

    :raises NotFoundError: raised when either one of the `from_uuids` or
        `to_uuid` do not exist in the registry
    :raises EqualIndividualError: raised when `to_uuid` is part of `from_uuids`
    """

    def _find_individuals(from_uuids, to_uuid):
        """Find the individuals to be merged from their uuids"""

        individuals = []
        for from_uuid in from_uuids:
            # Check whether input values are valid
            if from_uuid is None:
                raise InvalidValueError(msg="'from_uuid' cannot be None")
            if from_uuid == '':
                raise InvalidValueError(msg="'from_uuid' cannot be an empty string")
            if from_uuid == to_uuid:
                msg = "'to_uuid' {} cannot be part of 'from_uuids'".format(to_uuid)
                raise EqualIndividualError(msg=msg)

            try:
                from_indv = find_individual_by_uuid(from_uuid)
                individuals.append(from_indv)
            except NotFoundError as exc:
                raise exc

        return individuals

    def _get_identities(from_individuals):
        """Get all the sub-identities from all the individuals to be merged"""

        identities = Identity.objects.none()  # Initialize empty QuerySet
        for from_indv in from_individuals:
            try:
                identities = identities | from_indv.identities.all()
            except ValueError as e:
                raise InvalidValueError(msg=str(e))

        return identities

    def _move_identities(trxl, from_individuals, to_individual):
        """Move single identities into the target individual"""

        identities = _get_identities(from_individuals)
        for identity in identities:
            move_identity_db(trxl, identity, to_individual)

    def _merge_enrollments(trxl, from_individuals, to_individual):
        """Merge enrollments from `Individual` objects"""

        # Get current enrollments from all individuals
        enrollments_db = to_individual.enrollments.all()
        for from_indv in from_individuals:
            enrollments_db = enrollments_db | from_indv.enrollments.all()

        enrollments = {}
        for enrollment in enrollments_db:
            group = enrollment.group
            dates = enrollments.setdefault(group, [])
            dates.append((enrollment.start, enrollment.end))
            enrollments[group] = dates

        # Remove old enrollments and add new ones based in the new ranges
        for enrollment_db in enrollments_db:
            delete_enrollment(trxl, enrollment_db)

        # Add new enrollments merging datetime ranges
        for group in enrollments.keys():
            periods = enrollments[group]
            try:
                for start_dt, end_dt in merge_datetime_ranges(periods, exclude_limits=True):
                    add_enrollment(trxl, to_individual, group, start=start_dt, end=end_dt)
            except ValueError as e:
                raise InvalidValueError(msg=str(e))

        return to_individual

    def _merge_profiles(from_individuals, to_individual):
        """Merge the profiles from `Individual` objects"""

        for from_indv in from_individuals:
            if not to_individual.profile.is_bot and from_indv.profile.is_bot:
                to_individual.profile.is_bot = True
            if not to_individual.profile.name:
                to_individual.profile.name = from_indv.profile.name
            if not to_individual.profile.email:
                to_individual.profile.email = from_indv.profile.email
            if not to_individual.profile.gender:
                to_individual.profile.gender = from_indv.profile.gender
            if not to_individual.profile.gender_acc:
                to_individual.profile.gender_acc = from_indv.profile.gender_acc
            if not to_individual.profile.country:
                to_individual.profile.country = from_indv.profile.country

        return to_individual

    def _delete_individuals(trxl, individuals):
        """Delete individuals from the database"""

        for indv in individuals:
            delete_individual_db(trxl, indv)

    # Check input values
    if from_uuids is None:
        raise InvalidValueError(msg="'from_uuids' cannot be None")
    if from_uuids == []:
        raise InvalidValueError(msg="'from_uuids' cannot be an empty list")
    if to_uuid is None:
        raise InvalidValueError(msg="'to_uuid' cannot be None")
    if to_uuid == '':
        raise InvalidValueError(msg="'to_uuid' cannot be an empty string")

    trxl = TransactionsLog.open('merge', ctx)

    try:
        to_individual = find_individual_by_uuid(to_uuid)
        from_individuals = _find_individuals(from_uuids,
                                             to_individual.mk)
    except NotFoundError as exc:
        # At least one individual was not found, so they cannot be merged
        raise exc

    _move_identities(trxl, from_individuals, to_individual)

    to_individual = _merge_enrollments(trxl, from_individuals, to_individual)
    to_individual.refresh_from_db()

    to_individual = _merge_profiles(from_individuals, to_individual)
    update_profile_db(trxl, to_individual)

    _delete_individuals(trxl, from_individuals)

    trxl.close()

    to_individual.refresh_from_db()

    logger.info(f"Individuals {from_uuids} merged with {to_uuid}")

    return to_individual


@atomic_using_tenant
def unmerge_identities(ctx, uuids):
    """
    Unmerge one or more identities from their corresponding individual.

    Use this function to separate a list of `uuid` identities, creating
    an individual for each one. A profile for each new individual will
    be created using the `name` and `email` fields of the corresponding
    identity. Nor the enrollments or the profile from any parent individual
    of the input identities are modified.

    When a given identity `uuid` is equal to the `uuid` from its parent
    individual, there will be no effect.

    The function raises a `NotFoundError` exception when either any `uuid` from
    the list does not exist in the registry.

    The function raises an `InvalidValueError` exception when either any `uuid`
    from the list is `None` or an empty string.

    :param ctx: context from where this method is called
    :param uuids: list of identifiers of the identities set to
        be unmerged

    :returns: a list of `Individual` objects as the result of
        unmerging the identities

    :raises NotFoundError: raised when either any `uuid` from the list
        does not exist in the registry
    :raises InvalidValueError: raised when either any `uuid` from the
        list is `None` or an empty string
    """
    def _find_identities(uuids):
        """Find the identities to be unmerged from their parent individuals"""

        identities = []
        for uuid in uuids:
            # Check whether input values are valid
            if uuid is None:
                raise InvalidValueError(msg="'uuid' cannot be None")
            if uuid == '':
                raise InvalidValueError(msg="'uuid' cannot be an empty string")

            identity = find_identity(uuid)
            identities.append(identity)

        return identities

    def _set_destination_for_identity(trxl, identity):
        """Create the individual, if it does not exist, where the identity will be moved to."""

        if identity.uuid != identity.individual_id:
            individual = add_individual_db(trxl, identity.uuid)
            individual = update_profile_db(trxl, individual,
                                           name=identity.name,
                                           email=identity.email)
        else:
            # Case when the identity to be unmerged is the main one
            individual = identity.individual

        return individual

    def _move_to_destination(trxl, identity, individual):
        """Move the identity from the old individual to the new one"""

        try:
            indv = move_identity_db(trxl, identity, individual)
        except ValueError:
            # Case when the identity is already assigned to the individual
            indv = individual

        return indv

    # Check input value
    if uuids is None:
        raise InvalidValueError(msg="'uuids' cannot be None")
    if uuids == []:
        raise InvalidValueError(msg="'uuids' cannot be an empty list")

    trxl = TransactionsLog.open('unmerge_identities', ctx)

    identities = _find_identities(uuids)

    new_individuals = []
    for identity in identities:
        indv = _set_destination_for_identity(trxl, identity)
        individual = _move_to_destination(trxl, identity, indv)
        new_individuals.append(individual)

    trxl.close()

    logger.info(f"Identities {uuids} unmerged from their individuals")

    return new_individuals


@atomic_using_tenant
def merge_organizations(ctx, from_org, to_org):
    """Merge an organization into another.

    This function moves the domains, teams and affiliations from
    an origin organization identified by `from_org` to the target
    organization identified by `to_org`. The origin organization is
    then deleted and its name is added as an alias.

    The function raises a `NotFoundError` exception when either `from_org`
    or `to_org` do not exist in the registry and both identifiers are
    not the same. If both are the same, it raises an `InvalidValueError`.

    The target organization with updated data is returned as a result.

    :param ctx: context from where this method is called
    :param from_org: identifier of the origin organization
    :param to_org: identifier of the target organization where the origin
        organization will be merged

    :returns: an organization with the domains, teams and affiliation
        data updated

    :raises NotFoundError: raised when either `from_org` or `to_org`
        do not exist in the registry.
    :raises InvalidValueError: raised when either `from_org' or `to_org`
        are `None` or empty strings, or their values are the same.
    """
    def _move_domains(trxl, from_org, to_org):
        """Move the domains from the origin organization to the target"""

        domains = from_org.domains.all()
        for domain in domains:
            move_domain(trxl, domain, to_org)

    def _move_aliases(trxl, from_org, to_org):
        """Move the aliases from the origin organization to the target"""

        aliases = from_org.aliases.all()
        for alias in aliases:
            move_alias(trxl, alias, to_org)

    def _move_teams(trxl, from_org, to_org):
        """Move the teams from the origin organization to the target"""

        teams = from_org.teams.all()
        for team in teams:
            move_team(trxl, team, to_org)

    def _move_enrollments(trxl, from_org, to_org):
        """Enroll the members of the origin organization in the target"""

        enrollments = from_org.enrollments.all()
        for enrollment in enrollments:
            individual = enrollment.individual
            start = enrollment.start
            end = enrollment.end
            enrollment_db = search_enrollments_in_period(individual.mk,
                                                         to_org.name,
                                                         from_date=start,
                                                         to_date=end)
            if not enrollment_db:
                add_enrollment(trxl, individual, to_org, start=start, end=end)

        return to_org

    # Check input values
    if from_org is None:
        raise InvalidValueError(msg="'from_org' cannot be None")
    if from_org == '':
        raise InvalidValueError(msg="'from_org' cannot be an empty string")
    if to_org is None:
        raise InvalidValueError(msg="'to_org' cannot be None")
    if to_org == '':
        raise InvalidValueError(msg="'to_org' cannot be an empty string")
    if from_org == to_org:
        raise InvalidValueError(msg="'to_org' cannot be the same as 'from_org'")

    trxl = TransactionsLog.open('merge_organizations', ctx)

    try:
        target = find_organization(to_org)
        origin = find_organization(from_org)
    except NotFoundError as exc:
        # At least one organization was not found, so they cannot be merged
        raise exc

    _move_domains(trxl, origin, target)
    _move_teams(trxl, origin, target)
    _move_enrollments(trxl, origin, target)
    _move_aliases(trxl, origin, target)

    delete_organization_db(trxl, organization=origin)

    add_alias_db(trxl, organization=target, name=origin.name)

    trxl.close()

    logger.info(f"Organization {from_org} merged in {to_org}")

    return target


@atomic_using_tenant
def add_scheduled_task(ctx, job_type, interval=None, args=None, job_id=None):
    """Add an scheduled task to the registry.

    This function adds a new task to the registry.

    As a result, the function returns a new `ScheduledTask` object.

    :param ctx: context from where this method is called.
    :param job_type: name of the job to be scheduled
    :param interval: period of executions, in minutes. None to disable
    :param args: specific arguments for the job
    :param job_id: current job running the task

    :returns: a new ScheduledTask
    """
    if not job_type:
        raise InvalidValueError(msg="'job_type' cannot be None")

    trxl = TransactionsLog.open('add_scheduled_task', ctx)

    try:
        task = add_scheduled_task_db(trxl,
                                     job_type=job_type,
                                     interval=interval,
                                     args=args,
                                     job_id=job_id)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))
    except AlreadyExistsError as exc:
        raise exc

    trxl.close()

    logger.info(f"'{job_type}' task created")

    return task


@atomic_using_tenant
def update_scheduled_task(ctx, task_id, **kwargs):
    """Update an scheduled task.

    This function allows to edit or update the information of
    the scheduled task identified by the given id.

    The values to update are given as keyword arguments. The allowed
    keys are listed below (other keywords will be ignored):

       - `interval`: period of executions, in minutes. None to disable
       - `params`: specific parameters for the importer backend

    As a result, it will return the `ScheduledTask` object with
    the updated data.

    :param ctx: context from where this method is called.
    :param task_id: identifier of the task to update.
    :param kwargs: keyword arguments with data to update the task.

    :returns: task object with the updated information

    :raises NotFoundError: raised when either the task does not exist
        in the registry.
    :raises InvalidValueError: raised when any of the keyword arguments
        has an invalid value.
    """
    if not task_id:
        raise InvalidValueError(msg="'task_id' cannot be None")

    trxl = TransactionsLog.open('update_scheduled_task', ctx)

    try:
        task = find_scheduled_task(task_id)
    except NotFoundError as exc:
        raise exc

    try:
        task = update_scheduled_task_db(trxl, task, **kwargs)
    except ValueError as e:
        raise InvalidValueError(msg=str(e))

    trxl.close()

    logger.info(f"Task {task_id} successfully updated")

    return task


@atomic_using_tenant
def delete_scheduled_task(ctx, task_id):
    """Remove an scheduled task from the registry.

    This function removes the given task from the registry.
    When it is found, the task is removed. Otherwise, it will
    raise a 'NotFoundError'.

    :param ctx: context from where this method is called
    :param task_id: id of the task to remove
    :raises InvalidValueError: raised when task is None or an empty string
    :raises NotFoundError: raised when the task does not exist
        in the registry
    """
    if not task_id:
        raise InvalidValueError(msg="'task_id' cannot be empty or None")

    trxl = TransactionsLog.open('delete_scheduled_task', ctx)

    try:
        task = find_scheduled_task(task_id)
    except NotFoundError as exc:
        raise exc

    delete_scheduled_task_db(trxl, task=task)

    trxl.close()

    logger.info(f"Task {task_id} deleted")

    return task


@atomic_using_tenant
def delete_merge_recommendations(ctx):
    """Remove merge recommendations from the registry.

    This function removes all the merge recommendations that have not been
    processed from the registry.

    :param ctx: context from where this method is called
    """
    trxl = TransactionsLog.open('delete_merge_recommendations', ctx)

    recommendations = MergeRecommendation.objects.filter(applied__isnull=True)
    delete_merge_recommendations_db(trxl, recommendations=recommendations)

    trxl.close()

    logger.info("Merge recommendations deleted")

    return recommendations


@atomic_using_tenant
def review(ctx, uuid):
    """Mark an individual as reviewed.

    This function sets the individual identified by `uuid` as last
    reviewed on the current date.

    :param ctx: context from where this method is called
    :param uuid: identifier of the individual which will be reviewed

    :returns: an individual with its last review value updated

    :raises InvalidValueError: raised when `uuid` is `None` or an empty string
    :raises NotFoundError: when the identity with the
        given `uuid` does not exist.
    """
    if uuid is None:
        raise InvalidValueError(msg="'uuid' cannot be None")
    if uuid == '':
        raise InvalidValueError(msg="'uuid' cannot be an empty string")

    trxl = TransactionsLog.open('review', ctx)

    try:
        individual = find_individual_by_uuid(uuid)
    except NotFoundError as exc:
        raise exc

    review_date = datetime_utcnow()
    individual = review_db(trxl, individual, review_date)

    trxl.close()

    logger.info(f"Individual {uuid} successfully updated")

    return individual
