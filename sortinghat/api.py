# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Bitergia
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

from sortinghat.db.model import DEFAULT_START_DATE, DEFAULT_END_DATE,\
    UniqueIdentity, Organization, Domain, Enrollment
from sortinghat.exceptions import AlreadyExistsError, NotFoundError


def add_unique_identity(db, uuid):
    """Add a unique identity to the registry.

    This function adds a unique identity to the registry.
    First, it checks if the unique identifier (uuid) used to create the
    identity is already on the registry. When it is not found, a new unique
    identity is created. Otherwise, it raises a 'AlreadyExistError' exception.

    :param db: database manager
    :param uuid: unique identifier for the identity
    :raises ValueError: when uuid is None or an empty string
    :raises AlreadyExistsError: when the identifier already exists
        in the registry.
    """
    if uuid is None:
        raise ValueError('uuid cannot be None')
    if uuid == '':
        raise ValueError('uuid cannot be an empty string')

    with db.connect() as session:
        identity = session.query(UniqueIdentity).\
            filter(UniqueIdentity.identifier == uuid).first()

        if identity:
            raise AlreadyExistsError(entity=uuid)

        identity = UniqueIdentity(identifier=uuid)
        session.add(identity)


def add_organization(db, organization):
    """Add an organization to the registry.

    This function adds an organization to the registry.
    It checks first whether the organization is already on the registry.
    When it is not found, the new organization is added. Otherwise,
    it raises a 'AlreadyExistsError' exception to notify that the organization
    already exists.

    :param db: database manager
    :param organization: name of the organization
    :raises ValueError: raised when organization is None or an empty string
    :raises AlreadyExistsError: raised when the organization already exists
        in the registry.
    """
    if organization is None:
        raise ValueError('organization cannot be None')
    if organization == '':
        raise ValueError('organization cannot be an empty string')

    with db.connect() as session:
        org = session.query(Organization).\
            filter(Organization.name == organization).first()

        if org:
            raise AlreadyExistsError(entity=organization)

        org = Organization(name=organization)
        session.add(org)


def add_domain(db, organization, domain, overwrite=False):
    """Add a domain to the registry.

    This function adds a new domain to the given organization.
    The organization must exists on the registry prior to insert the new
    domain. Otherwise, it will raise a 'NotFoundError' exception. Moreover,
    if the given domain is already in the registry an 'AlreadyExistsError'
    exception will be raised.
    Remember that a domain can only be assigned to one (and only one)
    organization. When the given domain is already assigned to a distinct
    organization, you can use 'overwrite' parameter to shift the domain
    from the old organization to the new one.

    :param db: database manager
    :param organization: name of the organization
    :param domain: domain to add to the registry
    :param overwrite: force to reassign the domain to the given company

    :raises ValueError: raised when domain is None or an empty string
    :raises NotFoundError: raised when the given organization is not found
        in the registry
    :raises AlreadyExistsError: raised when the domain already exists
        in the registry
    """
    if domain is None:
        raise ValueError('domain cannot be None')
    if domain == '':
        raise ValueError('domain cannot be an empty string')

    with db.connect() as session:
        org = session.query(Organization).\
            filter(Organization.name == organization).first()

        if not org:
            raise NotFoundError(entity=organization)

        dom = session.query(Domain).\
            filter(Domain.domain == domain).first()

        if dom and not overwrite:
            raise AlreadyExistsError(entity=domain)
        elif not dom:
            dom = Domain(domain=domain)

        dom.company = org
        session.add(dom)


def add_enrollment(db, uuid, organization, from_date=None, to_date=None):
    """Enroll a unique identity to an organization.

    The function adds a new relationship between the unique identity
    identified by 'uuid' and the given 'organization'. The given
    identity and organization must exist prior to add this enrollment
    in the registry. Otherwise, a 'NotFoundError' exception will be raised.

    The period of the enrollment can be given with the parameters 'from_date'
    and 'to_date', where "from_date <= to_date". Default values for these
    dates are '1900-01-01' and '2100-01-01'.

    If the given enrollment data is already in the registry, the function
    will raise a 'AlreadyExistsError' exception.

    :param db: database manager
    :param uuid: unique identifier
    :param organization: name of the organization
    :param from_date: date when the enrollment starts
    :param to_date: date when the enrollment ends

    :raises NotFoundError: when either 'uuid' or 'organization' are not
        found in the registry.
    :raises ValeError: raised in two cases, when either identity or
        organization are None or empty strings; when "from_date > to_date".
    :raises AlreadyExistsError: raised when given enrollment already exists
        in the registry.
    """
    if uuid is None:
        raise ValueError('uuid cannot be None')
    if uuid == '':
        raise ValueError('uuid cannot be an empty string')
    if organization is None:
        raise ValueError('organization cannot be None')
    if organization == '':
        raise ValueError('organization cannot be an empty string')

    if from_date and to_date and from_date > to_date:
        raise ValueError('start date %s cannot be greater than %s'
                         % (from_date, to_date))

    if not from_date:
        from_date = DEFAULT_START_DATE
    if not to_date:
        to_date = DEFAULT_END_DATE

    with db.connect() as session:
        identity = session.query(UniqueIdentity).\
            filter(UniqueIdentity.identifier == uuid).first()

        if not identity:
            raise NotFoundError(entity=uuid)

        org = session.query(Organization).\
            filter(Organization.name == organization).first()

        if not org:
            raise NotFoundError(entity=organization)

        enrollment = session.query(Enrollment).\
            filter(Enrollment.identity == identity,
                   Enrollment.organization == org,
                   Enrollment.init == from_date,
                   Enrollment.end == to_date).first()

        if enrollment:
            entity = '-'.join((uuid, organization,
                              str(enrollment.init), str(enrollment.end)))
            raise AlreadyExistsError(entity=entity)

        enrollment = Enrollment(identity=identity, organization=org,
                                init=from_date, end=to_date)
        session.add(enrollment)


def delete_unique_identity(db, uuid):
    """Remove a unique identity from the registry.

    Function that removes from the registry, the unique identity
    that matches with uuid. Data related to this identity will be
    also removed.
    It checks first whether the identity is already on the registry.
    When it is found, the identity is removed. Otherwise, it will raise
    a 'NotFoundError' exception.

    :param db: database manager
    :param uuid: unique identifier assigned to the identity set for being removed

    :raises NotFoundError: raised when the identity does not exist
        in the registry.
    """
    with db.connect() as session:
        identity = session.query(UniqueIdentity).\
            filter(UniqueIdentity.identifier == uuid).first()

        if not identity:
            raise NotFoundError(entity=uuid)

        session.delete(identity)


def delete_organization(db, organization):
    """Remove an organization from the registry.

    This function removes the given organization from the registry.
    Related information such as domains or enrollments are also removed.
    It checks first whether the organization is already on the registry.
    When it is found, the organization is removed. Otherwise,
    it will raise a 'NotFoundError'.

    :param db: database manager
    :param organization: name of the organization to remove

    :raises NotFoundError: raised when the organization does not exist
        in the registry.
    """
    with db.connect() as session:
        org = session.query(Organization).\
            filter(Organization.name == organization).first()

        if not org:
            raise NotFoundError(entity=organization)

        session.delete(org)


def delete_domain(db, organization, domain):
    """Remove an organization from the registry.

    This function removes the given domain from the registry. Both
    organization and domain must exist in the registry. Otherwise,
    it will raise a 'NotFoundError' exception.

    :param db: database manager
    :param organization: name of the organization
    :param domain: name of the domain to remove

    :raises NotFoundError: raised when the organization or the domain
        do not exist in the registry.
    """
    with db.connect() as session:
        org = session.query(Organization).\
            filter(Organization.name == organization).first()

        if not org:
            raise NotFoundError(entity=organization)

        dom = session.query(Domain).join(Organization).\
            filter(Organization.name == organization,
                   Domain.domain == domain).first()

        if not dom:
            raise NotFoundError(entity=domain)

        session.delete(dom)


def delete_enrollment(db, uuid, organization, from_date=None, to_date=None):
    """Withdraw a unique identity from an organization.

    This function removes all the enrollments between the unique identity
    identified by 'uuid' and the given 'organization'. Both 'uuid' and
    organization must exists before deleting. Otherwise, it will raise a
    'NotFoundError' exception.

    When a period of time is given using 'from_date' and 'to_date'
    parameters, the function will remove those periods on which
    'from_date' <= enrollment <= 'to_date'. Default values for these dates
    are '1900-01-01' and '2100-01-01'.

    :param db: database manager
    :param uuid: unique identifier
    :param organization: name of the organization
    :param from_date: date when the enrollment starts
    :param to_date: date when the enrollment ends

    :raises NotFoundError: when either 'uuid' or 'organization' are not
        found in the registry.
    :raises ValeError: when "from_date > to_date".
    """
    if from_date and to_date and from_date > to_date:
        raise ValueError('start date %s cannot be greater than %s'
                         % (from_date, to_date))

    if not from_date:
        from_date = DEFAULT_START_DATE
    if not to_date:
        to_date = DEFAULT_END_DATE

    with db.connect() as session:
        identity = session.query(UniqueIdentity).\
            filter(UniqueIdentity.identifier == uuid).first()

        if not identity:
            raise NotFoundError(entity=uuid)

        org = session.query(Organization).\
            filter(Organization.name == organization).first()

        if not org:
            raise NotFoundError(entity=organization)

        enrollments = session.query(Enrollment).\
            filter(Enrollment.identity == identity,
                   Enrollment.organization == org,
                   from_date <= Enrollment.init,
                   Enrollment.end <= to_date).all()

        if not enrollments:
            entity = '-'.join((uuid, organization,
                              str(from_date), str(to_date)))
            raise NotFoundError(entity=entity)

        for enr in enrollments:
            session.delete(enr)


def registry(db, organization=None):
    """List the organizations available in the registry.

    The function will return the list of organizations. If organization
    parameter is set, it will only return the information about
    that organization. When the given organization is not in the registry
    a 'NotFounError' exception will be raised.

    :param db: database manager
    :param organization: name of the organization

    :returns: a list of organizations sorted by their name

    :raises NotFoundError: raised when the given organization is not found
        in the registry
    """
    orgs = []

    with db.connect() as session:
        if organization:
            org = session.query(Organization).\
                filter(Organization.name == organization).first()

            if not org:
                raise NotFoundError(entity=organization)

            orgs = [org]
        else:
            orgs = session.query(Organization).\
                order_by(Organization.name).all()

        # Detach objects from the session
        session.expunge_all()

    return orgs
