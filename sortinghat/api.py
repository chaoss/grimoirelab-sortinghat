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

from sortinghat import utils
from sortinghat.db.model import DEFAULT_START_DATE, DEFAULT_END_DATE,\
    UniqueIdentity, Identity, Organization, Domain, Enrollment
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
            filter(UniqueIdentity.uuid == uuid).first()

        if identity:
            raise AlreadyExistsError(entity=uuid)

        identity = UniqueIdentity(uuid=uuid)
        session.add(identity)


def add_identity(db, source, email=None, name=None, username=None, uuid=None):
    """Add an identity to the registry.

    This function adds a new identity to the registry. By default, a new
    unique identity will be also added an associated to the new identity.
    When 'uuid' parameter is set, it only creates a new identity that will be
    associated to a unique identity defined by 'uuid'. If the given unique
    identity does not exist, it raises a 'NotFoundError'.

    The registry considers that two identities are distinct when any value
    of the tuple (source, email, name, username) is different. Thus, the
    identities  id1:('scm', 'jsmith@example.com', 'John Smith', 'jsmith')
    and id2:('mls', 'jsmith@example.com', 'John Smith', 'jsmith') will be
    registered as different identities. A 'AlreadyExistError' exception will
    be raised when the function tries to insert a tuple that exists in the
    registry.

    The function returns the identifier associated to the new registered
    identity. When no 'uuid' is given, this id and the uuid associated to
    the new identity will be the same.

    :param db: database manager
    :param source: data source
    :param email: email of the identity
    :param name: full name of the identity
    :param username: user name used by the identity
    :param uuid: associates the new identity to the unique identity
        identified by this id

    :returns: a universal unique identifier

    :raises ValueError: when source is None or empty; each one of the
        parameters is None; parameters are empty.
    :raises AlreadyExistsError: raised when the identity already exists
        in the registry.
    :raises NotFoundError: raised when the unique identity associated
        to the given 'uuid' is not in the registry.
    """
    def _find_unique_identity(session, uuid):
        """Find a unique identity.

        :param session: database session
        :param uuid: unique identity to find

        :returns: a unique identity object
        """
        uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == uuid).first()
        return uid

    if source is None:
        raise ValueError('source cannot be None')
    if source == '':
        raise ValueError('source cannot be an empty string')
    if not (email or name or username):
        raise ValueError('identity data cannot be None or empty')

    with db.connect() as session:
        identity = session.query(Identity).\
            filter(Identity.name == name,
                   Identity.email == email,
                   Identity.username == username,
                   Identity.source == source).first()

        if identity:
            entity = '-'.join((str(source), str(email), str(name), str(username)))
            raise AlreadyExistsError(entity=entity)

        # Each identity needs a unique identifier
        id = utils.uuid(source, email=email, name=name, username=username)

        if not uuid:
            uid = UniqueIdentity(uuid=id)
            session.add(uid)
        else:
            uid = _find_unique_identity(session, uuid)

        if not uid:
            raise NotFoundError(entity=uuid)

        identity = Identity(id=id, name=name, email=email,
                            username=username, source=source)
        identity.uidentity = uid
        session.add(identity)

        return id


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
    :param overwrite: force to reassign the domain to the given organization

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

        dom.organization = org
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
            filter(UniqueIdentity.uuid == uuid).first()

        if not identity:
            raise NotFoundError(entity=uuid)

        org = session.query(Organization).\
            filter(Organization.name == organization).first()

        if not org:
            raise NotFoundError(entity=organization)

        enrollment = session.query(Enrollment).\
            filter(Enrollment.uidentity == identity,
                   Enrollment.organization == org,
                   Enrollment.init == from_date,
                   Enrollment.end == to_date).first()

        if enrollment:
            entity = '-'.join((uuid, organization,
                              str(enrollment.init), str(enrollment.end)))
            raise AlreadyExistsError(entity=entity)

        enrollment = Enrollment(uidentity=identity, organization=org,
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
            filter(UniqueIdentity.uuid == uuid).first()

        if not identity:
            raise NotFoundError(entity=uuid)

        session.delete(identity)


def delete_identity(db, id):
    """Remove an identity from the registry.

    This function removes from the registry, the identity which its identifier
    matches with id. Take into account that this function does not remove
    unique identities.

    When the given identity is not found in the registry a 'NotFoundError'
    exception is raised.

    :param db: database manager
    :param id: identifier assigned to the identity that will be removed

    :raises NotFoundError: raised when the identity does not exist in the
        registry.
    """
    with db.connect() as session:
        identity = session.query(Identity).\
            filter(Identity.id == id).first()

        if not identity:
            raise NotFoundError(entity=id)

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
            filter(UniqueIdentity.uuid == uuid).first()

        if not identity:
            raise NotFoundError(entity=uuid)

        org = session.query(Organization).\
            filter(Organization.name == organization).first()

        if not org:
            raise NotFoundError(entity=organization)

        enrollments = session.query(Enrollment).\
            filter(Enrollment.uidentity == identity,
                   Enrollment.organization == org,
                   from_date <= Enrollment.init,
                   Enrollment.end <= to_date).all()

        if not enrollments:
            entity = '-'.join((uuid, organization,
                              str(from_date), str(to_date)))
            raise NotFoundError(entity=entity)

        for enr in enrollments:
            session.delete(enr)


def unique_identities(db, uuid=None):
    """List the unique identities available in the registry.

    The function returns a list of unique identities. When 'uuid'
    parameter is set, it will only return the information related
    to the unique identity identified by 'uuid'. When the given
    'uuid' is not in the registry, a 'NotFoundError' exception will
    be raised.

    :param db: database manager
    :param uuid: unique identifier for the identity

    :raises NotFoundError: raised when the given uuid is not found
        in the registry
    """
    uidentities = []

    with db.connect() as session:
        if uuid:
            uid = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == uuid).first()

            if not uid:
                raise NotFoundError(entity=uuid)

            uidentities = [uid]
        else:
            uidentities = session.query(UniqueIdentity).\
                order_by(UniqueIdentity.uuid).all()

        # Detach objects from the session
        session.expunge_all()

    return uidentities


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


def enrollments(db, uuid=None, organization=None, from_date=None, to_date=None):
    """List the enrollment information available in the registry.

    This function will return a list of enrollments. If 'uuid'
    parameter is set, it will return the enrollments related to that
    unique identity; if 'organization' parameter is given, it will
    return the enrollments related to that organization; if both
    parameters are set, the function will return the list of enrollments
    of 'uuid' on the 'organization'.

    Enrollments between a period can also be listed using 'from_date' and
    'to_date' parameters. When these are set, the function will return
    all those enrollments where Enrollment.init >= from_date AND
    Enrollment.end <= to_date. Defaults values for these dates are
    1900-01-01 and 2100-01-01.

    When either 'uuid' or 'organization' are not in the registry a
    'NotFoundError' exception will be raised.

    :param db: database manager
    :param uuid: unique identifier
    :param organization: name of the organization
    :param from_date: date when the enrollment starts
    :param to_date: date when the enrollment ends

    :returns: a list of enrollments sorted by uuid or by organization.

    :raises NotFoundError: when either 'uuid' or 'organization' are not
        found in the registry.
    """
    enrollments = []

    if from_date and to_date and from_date > to_date:
        raise ValueError('start date %s cannot be greater than %s'
                         % (from_date, to_date))

    if not from_date:
        from_date = DEFAULT_START_DATE
    if not to_date:
        to_date = DEFAULT_END_DATE

    with db.connect() as session:
        query = session.query(Enrollment).\
            join(UniqueIdentity, Organization).\
            filter(Enrollment.init >= from_date,
                   Enrollment.end <= to_date)

        # Filter by uuid
        if uuid:
            identity = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == uuid).first()

            if not identity:
                raise NotFoundError(entity=uuid)

            query = query.filter(Enrollment.uidentity == identity)

        # Filter by organization
        if organization:
            org = session.query(Organization).\
                filter(Organization.name == organization).first()

            if not org:
                raise NotFoundError(entity=organization)

            query = query.filter(Enrollment.organization == org)

        # Get the results
        enrollments = query.order_by(UniqueIdentity.uuid,
                                     Organization.name,
                                     Enrollment.init,
                                     Enrollment.end).all()

        # Detach objects from the session
        session.expunge_all()

    return enrollments
