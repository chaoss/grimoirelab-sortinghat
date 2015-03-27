# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Bitergia
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
from sortinghat.db.model import MIN_PERIOD_DATE, MAX_PERIOD_DATE,\
    UniqueIdentity, Identity, Profile, Organization, Domain, Country, Enrollment
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
        uidentity = session.query(UniqueIdentity).\
            filter(UniqueIdentity.uuid == uuid).first()

        if uidentity:
            raise AlreadyExistsError(entity=uuid, uuid=uuid)

        uidentity = UniqueIdentity(uuid=uuid)
        session.add(uidentity)


def add_identity(db, source, email=None, name=None, username=None, uuid=None):
    """Add an identity to the registry.

    This function adds a new identity to the registry. By default, a new
    unique identity will be also added an associated to the new identity.
    When 'uuid' parameter is set, it creates a new identity that will be
    associated to the unique identity defined by 'uuid' that already exists
    on the registry. If the given unique identity does not exist, it raises
    a 'NotFoundError' exception.

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
        uidentity = session.query(UniqueIdentity).\
            filter(UniqueIdentity.uuid == uuid).first()
        return uidentity

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
            entity = '-'.join((unicode(source), unicode(email), unicode(name), unicode(username)))
            raise AlreadyExistsError(entity=entity,
                                     uuid=identity.uuid)

        # Each identity needs a unique identifier
        identity_id = utils.uuid(source, email=email,
                                 name=name, username=username)

        if not uuid:
            uidentity = UniqueIdentity(uuid=identity_id)
            session.add(uidentity)
        else:
            uidentity = _find_unique_identity(session, uuid)

        if not uidentity:
            raise NotFoundError(entity=uuid)

        identity = Identity(id=identity_id, name=name, email=email,
                            username=username, source=source)
        identity.uidentity = uidentity
        session.add(identity)

        return identity_id


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


def add_domain(db, organization, domain, is_top_domain=False, overwrite=False):
    """Add a domain to the registry.

    This function adds a new domain to the given organization.
    The organization must exists on the registry prior to insert the new
    domain. Otherwise, it will raise a 'NotFoundError' exception. Moreover,
    if the given domain is already in the registry an 'AlreadyExistsError'
    exception will be raised.

    The new domain can be also set as a top domain. That is useful to avoid
    the insertion of sub-domains that belong to the same organization (i.e
    eu.example.com, us.example.com).

    Remember that a domain can only be assigned to one (and only one)
    organization.

    When the given domain already exist on the registry, you can use
    'overwrite' parameter to update its information. For instance, shift
    the domain to another organization or to update the top domain flag.
    Take into account that both fields will be updated at the same time.

    :param db: database manager
    :param organization: name of the organization
    :param domain: domain to add to the registry
    :param is_top_domain: set this domain as a top domain
    :param overwrite: force to reassign the domain to the given organization
        and to update top domain field

    :raises ValueError: raised when domain is None or an empty string or
        is_top_domain does not have a boolean value
    :raises NotFoundError: raised when the given organization is not found
        in the registry
    :raises AlreadyExistsError: raised when the domain already exists
        in the registry
    """
    if domain is None:
        raise ValueError('domain cannot be None')
    if domain == '':
        raise ValueError('domain cannot be an empty string')
    if type(is_top_domain) != bool:
        raise ValueError('top_domain must have a boolean value')

    with db.connect() as session:
        org = session.query(Organization).\
            filter(Organization.name == organization).first()

        if not org:
            raise NotFoundError(entity=organization)

        dom = session.query(Domain).\
            filter(Domain.domain == domain).first()

        if dom and not overwrite:
            raise AlreadyExistsError(entity=dom)
        elif not dom:
            dom = Domain(domain=domain)

        dom.organization = org
        dom.is_top_domain = is_top_domain
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
    :raises ValeError: raised in three cases, when either identity or
        organization are None or empty strings; when "from_date" < 1900-01-01 or
        "to_date" > 2100-01-01; when "from_date > to_date"
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

    if not from_date:
        from_date = MIN_PERIOD_DATE
    if not to_date:
        to_date = MAX_PERIOD_DATE

    if from_date < MIN_PERIOD_DATE or from_date > MAX_PERIOD_DATE:
        raise ValueError('start date %s is out of bounds' % str(from_date))
    if to_date < MIN_PERIOD_DATE or to_date > MAX_PERIOD_DATE:
        raise ValueError('end date %s is out of bounds' % str(to_date))

    if from_date > to_date:
        raise ValueError('start date %s cannot be greater than %s'
                         % (from_date, to_date))

    with db.connect() as session:
        uidentity = session.query(UniqueIdentity).\
            filter(UniqueIdentity.uuid == uuid).first()

        if not uidentity:
            raise NotFoundError(entity=uuid)

        org = session.query(Organization).\
            filter(Organization.name == organization).first()

        if not org:
            raise NotFoundError(entity=organization)

        enrollment = session.query(Enrollment).\
            filter(Enrollment.uidentity == uidentity,
                   Enrollment.organization == org,
                   Enrollment.start == from_date,
                   Enrollment.end == to_date).first()

        if enrollment:
            entity = '-'.join((uuid, organization,
                              str(enrollment.start), str(enrollment.end)))
            raise AlreadyExistsError(entity=entity)

        enrollment = Enrollment(uidentity=uidentity, organization=org,
                                start=from_date, end=to_date)
        session.add(enrollment)


def edit_profile(db, uuid, **kwargs):
    """Edit unique identity profile.

    This function allows to edit or update the profile information of the
    unique identity identified by 'uuid'. When there is not a profile
    for the given 'uuid', a new one will be created.

    The values to update are given as keyword arguments. The allowed
    keys are listed below (other keywords will be ignored):

       - 'name' : name of the unique identity
       - 'email' : email address of the unique identity
       - 'is_bot' : boolean value to determine whether a unique identity is
             a bot or not. By default, this value is initialized to
             False.
       - 'country_code' : ISO-3166 country code

    :raises NotFoundError: raised when either the unique identity
        or the country code do not exist in the registry.
    :raises ValueError: raised when is_bot does not have a boolean
        value.
    """
    with db.connect() as session:
        uidentity = session.query(UniqueIdentity).\
            filter(UniqueIdentity.uuid == uuid).first()

        if not uidentity:
            raise NotFoundError(entity=uuid)

        if not uidentity.profile:
            # Create a new profile
            profile = Profile(uuid=uuid)
        else:
            profile = uidentity.profile

        if 'is_bot' in kwargs:
            is_bot = kwargs['is_bot']

            if type(is_bot) != bool:
                raise ValueError('is_bot must have a boolean value')

            profile.is_bot = is_bot

        if 'country_code' in kwargs:
            code = kwargs['country_code']

            country = session.query(Country).\
                filter(Country.code == code).first()

            if not country:
                raise NotFoundError(entity='country code %s' % str(code))

            profile.country_code = country.code

        # Function to avoid empty strings on the database
        to_none_if_empty = lambda x: None if x == '' else x

        if 'name' in kwargs:
            profile.name = to_none_if_empty(kwargs['name'])
        if 'email' in kwargs:
            profile.email = to_none_if_empty(kwargs['email'])

        session.add(profile)


def delete_unique_identity(db, uuid):
    """Remove a unique identity from the registry.

    Function that removes from the registry, the unique identity
    that matches with uuid. Data related to this identity will be
    also removed.

    It checks first whether the unique identity is already on the registry.
    When it is found, the unique identity is removed. Otherwise, it will
    raise a 'NotFoundError' exception.

    :param db: database manager
    :param uuid: unique identifier assigned to the unique identity set
        for being removed

    :raises NotFoundError: raised when the unique identity does not exist
        in the registry.
    """
    with db.connect() as session:
        uidentity = session.query(UniqueIdentity).\
            filter(UniqueIdentity.uuid == uuid).first()

        if not uidentity:
            raise NotFoundError(entity=uuid)

        session.delete(uidentity)


def delete_identity(db, identity_id):
    """Remove an identity from the registry.

    This function removes from the registry, the identity which its identifier
    matches with id. Take into account that this function does not remove
    unique identities.

    When the given identity is not found in the registry a 'NotFoundError'
    exception is raised.

    :param db: database manager
    :param identity_id: identifier assigned to the identity that will
        be removed

    :raises NotFoundError: raised when the identity does not exist in the
        registry.
    """
    with db.connect() as session:
        identity = session.query(Identity).\
            filter(Identity.id == identity_id).first()

        if not identity:
            raise NotFoundError(entity=identity_id)

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
    :raises ValeError: it is raised in two cases, when "from_date" < 1900-01-01 or
        "to_date" > 2100-01-01; when "from_date > to_date".
    """
    if not from_date:
        from_date = MIN_PERIOD_DATE
    if not to_date:
        to_date = MAX_PERIOD_DATE

    if from_date < MIN_PERIOD_DATE or from_date > MAX_PERIOD_DATE:
        raise ValueError('start date %s is out of bounds' % str(from_date))
    if to_date < MIN_PERIOD_DATE or to_date > MAX_PERIOD_DATE:
        raise ValueError('end date %s is out of bounds' % str(to_date))

    if from_date > to_date:
        raise ValueError('start date %s cannot be greater than %s'
                         % (from_date, to_date))

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
                   from_date <= Enrollment.start,
                   Enrollment.end <= to_date).all()

        if not enrollments:
            entity = '-'.join((uuid, organization,
                              str(from_date), str(to_date)))
            raise NotFoundError(entity=entity)

        for enr in enrollments:
            session.delete(enr)


def merge_unique_identities(db, from_uuid, to_uuid):
    """Merge one unique identity into another.

    Use this function to join 'from_uuid' unique identity into
    'to_uuid'. Identities and enrollments related to 'from_uuid' will be
    assigned to 'to_uuid'. In addition, 'from_uuid' will be removed
    from the registry. Duplicated enrollments will be also removed from the
    registry.

    When 'from_uuid' and 'to_uuid' are equal, the action does not have any
    effect.

    The function raises a 'NotFoundError exception when either 'from_uuid'
    or 'to_uuid' do not exist in the registry.

    :param from_uuid: identifier of the unique identity set to merge
    :param to_uuid: identifier of the unique identity where 'from_uuid'
        will be merged

    :raises NotFoundError: raised when either 'from_uuid' or 'to_uuid'
        do not exist in the registry
    """
    with db.connect() as session:
        fuid = session.query(UniqueIdentity).\
            filter(UniqueIdentity.uuid == from_uuid).first()
        tuid = session.query(UniqueIdentity).\
            filter(UniqueIdentity.uuid == to_uuid).first()

        if not fuid:
            raise NotFoundError(entity=from_uuid)

        if from_uuid == to_uuid:
            return

        if not tuid:
            raise NotFoundError(entity=to_uuid)

        # Update identities
        for identity in fuid.identities:
            identity.uuid = to_uuid

        # Update and remove duplicated enrollments
        for rol in fuid.enrollments:
            enrollment = session.query(Enrollment).\
                filter(Enrollment.uidentity == tuid,
                       Enrollment.organization == rol.organization,
                       Enrollment.start == rol.start,
                       Enrollment.end == rol.end).first()

            if enrollment:
                session.delete(rol)
            else:
                rol.uuid = to_uuid

        # For some reason, uuid are not updated until changes are
        # committed (flush does nothing). Force to commit changes
        # to avoid deletion of identities when removing 'fuid'
        session.commit()

        session.delete(fuid)


def merge_enrollments(db, uuid, organization):
    """Merge overlapping enrollments.

    This function merges those enrollments, related to the given 'uuid' and
    'organization', that have overlapping dates. Default start and end dates
    (1900-01-01 and 2100-01-01) are considered range limits and will be
    removed when a set of ranges overlap. For example:

     * [(1900-01-01, 2010-01-01), (2008-01-01, 2100-01-01)]
           --> (2008-01-01, 2010-01-01)
     * [(1900-01-01, 2010-01-01), (2008-01-01, 2010-01-01), (2010-01-02, 2100-01-01)]
           --> (2008-01-01, 2010-01-01),(2010-01-02, 2100-01-01)
     * [(1900-01-01, 2010-01-01), (2010-01-02, 2100-01-01)]
           --> (1900-01-01, 2010-01-01), (2010-01-02, 2100-01-01)

    It may raise a ValueError when any date is out of bounds. In other words, when
    any date < 1900-01-01 or date > 2100-01-01.

    :param db: database manager
    :param uuid: unique identifier
    :param organization: name of the organization

    :raises NotFoundError: when either 'uuid' or 'organization' are not
        found in the registry. It is also raised when there are not enrollments
        related to 'uuid' and 'organization'
    :raises ValueError: when any date is out of bounds
    """
    # Merge enrollments
    with db.connect() as session:
        uidentity = session.query(UniqueIdentity).\
            filter(UniqueIdentity.uuid == uuid).first()

        if not uidentity:
            raise NotFoundError(entity=uuid)

        org = session.query(Organization).\
            filter(Organization.name == organization).first()

        if not org:
            raise NotFoundError(entity=organization)

        disjoint = session.query(Enrollment).\
            filter(Enrollment.uidentity == uidentity,
                   Enrollment.organization == org).all()

        if not disjoint:
            entity = '-'.join((uuid, organization))
            raise NotFoundError(entity=entity)

        dates = [(enr.start, enr.end) for enr in disjoint]

        for st, en in utils.merge_date_ranges(dates):
            # We prefer this method to find duplicates
            # to avoid integrity exceptions when creating
            # enrollments that are already in the database
            is_dup = lambda x, st, en : x.start == st and x.end == en

            filtered = [x for x in disjoint if not is_dup(x, st, en)]

            if len(filtered) != len(disjoint):
                disjoint = filtered
                continue

            # This means no dups where found so we need to add a
            # new enrollment
            enr = Enrollment(uidentity=uidentity, organization=org,
                             start=st, end=en)
            session.add(enr)

        # Remove disjoint enrollments from the registry
        for enr in disjoint:
            session.delete(enr)


def move_identity(db, from_id, to_uuid):
    """Move an identity to a unique identity.

    This function shifts the identity identified by 'from_id' to
    the unique identity 'to_uuid'. When 'to_uuid' is the unique
    identity that is currently related to 'from_id', the action does
    not have any effect.

    The function raises a 'NotFoundError exception when either 'from_id'
    or 'to_uuid' do not exist in the registry.

    :param from_id: identifier of the identity set to be moved
    :param to_uuid: identifier of the unique identity where 'from_id'
        will be moved

    :raises NotFoundError: raised when either 'from_uuid' or 'to_uuid'
        do not exist in the registry
    """
    with db.connect() as session:
        fid = session.query(Identity).\
            filter(Identity.id == from_id).first()
        tuid = session.query(UniqueIdentity).\
            filter(UniqueIdentity.uuid == to_uuid).first()

        if not fid:
            raise NotFoundError(entity=from_id)
        if not tuid:
            raise NotFoundError(entity=to_uuid)

        if fid.uuid == to_uuid:
            return

        fid.uuid = to_uuid


def match_identities(db, uuid, matcher):
    """Search for similar unique identities.

    The function will search in the registry for similar identities to 'uuid'.
    The result will be a list matches containing unique identities objects.
    This list will also include the given unique identity.

    The criteria used to check when an identity matches with another one
    is defined by 'matcher' parameter. This parameter is an instance
    of 'IdentityMatcher' class.

    :param db: database manager
    :param uuid: identifier of the identity to match
    :param matcher: criteria used to match identities

    :returns: list of matched unique identities

    :raises NotFoundError: raised when 'uuid' does not exist in the
        registry
    """
    uidentities = []

    with db.connect() as session:
        uid = session.query(UniqueIdentity).\
            filter(UniqueIdentity.uuid == uuid).first()

        if not uid:
            raise NotFoundError(entity=uuid)

        candidates = session.query(UniqueIdentity).all()

        for candidate in candidates:
            if not matcher.match(uid, candidate):
                continue
            uidentities.append(candidate)

        # Detach objects from the session
        session.expunge_all()

    return uidentities


def unique_identities(db, uuid=None, source=None):
    """List the unique identities available in the registry.

    The function returns a list of unique identities. When 'uuid'
    parameter is set, it will only return the information related
    to the unique identity identified by 'uuid'. When 'source' is
    given, only thouse unique identities with one or more identities
    related to that source will be returned.

    When the given 'uuid', assigned to the given 'source', is not in the
    registry, a 'NotFoundError' exception will be raised.

    :param db: database manager
    :param uuid: unique identifier for the identity
    :param source: source of the identities

    :raises NotFoundError: raised when the given uuid is not found
        in the registry
    """
    uidentities = []

    with db.connect() as session:
        query = session.query(UniqueIdentity)

        if source:
            query = query.join(Identity).\
                filter(UniqueIdentity.uuid == Identity.uuid,
                       Identity.source == source)

        if uuid:
            uidentity = query.\
                filter(UniqueIdentity.uuid == uuid).first()

            if not uidentity:
                raise NotFoundError(entity=uuid)

            uidentities = [uidentity]
        else:
            uidentities = query.\
                order_by(UniqueIdentity.uuid).all()

        # Detach objects from the session
        session.expunge_all()

    return uidentities


def registry(db, term=None):
    """List the organizations available in the registry.

    The function will return the list of organizations. If term
    parameter is set, it will only return the information about
    the organizations which match that term. When the given term does
    not match with any organization from the registry a 'NotFounError'
    exception will be raised.

    :param db: database manager
    :param term: term to match with organizations names

    :returns: a list of organizations sorted by their name

    :raises NotFoundError: raised when the given term is not found on
        any organization from the registry
    """
    orgs = []

    with db.connect() as session:
        if term:
            orgs = session.query(Organization).\
                filter(Organization.name.like('%' + term + '%')).\
                order_by(Organization.name).all()

            if not orgs:
                raise NotFoundError(entity=term)
        else:
            orgs = session.query(Organization).\
                order_by(Organization.name).all()

        # Detach objects from the session
        session.expunge_all()

    return orgs


def domains(db, domain=None, top=False):
    """List the domains available in the registry.

    The function will return the list of domains. Settting the top flag,
    it will look for those domains that are top domains. If domain parameter
    is set, it will only return the information about that domain.

    When both paramaters are set, it will first search for the given domain.
    If it is not found, it will look for its top domains. In the case of
    neither the domain exists nor has top domains, a 'NotFoundError' exception
    will be raised.

    :param db: database manager
    :param domain: name of the domain
    :param top: filter by top domains

    :returns: a list of domains

    :raises NotFoundError: raised when the given domain is not found in the
        registry
    """
    doms = []

    with db.connect() as session:
        if domain:
            dom = session.query(Domain).\
                filter(Domain.domain == domain).first()

            if not dom:
                if not top:
                    raise NotFoundError(entity=domain)
                else:
                    # Adds a dot to the beggining of the domain.
                    # Useful to compare domains like example.com and
                    # myexample.com
                    add_dot = lambda d: '.' + d if not d.startswith('.') else d

                    d = add_dot(domain)

                    tops = session.query(Domain).\
                        filter(Domain.is_top_domain).order_by(Domain.domain).all()

                    doms = [t for t in tops\
                            if d.endswith(add_dot(t.domain))]

                    if not doms:
                        raise NotFoundError(entity=domain)
            else:
                doms = [dom]
        else:
            query = session.query(Domain)

            if top:
                query = query.filter(Domain.is_top_domain)

            doms = query.order_by(Domain.domain).all()

        # Detach objects from the session
        session.expunge_all()

    return doms


def countries(db, code=None, term=None):
    """List the countries available in the registry.

    The function will return the list of countries. When either 'code' or
    'term' parameters are set, it will only return the information about
    those countries that match them.

    Take into account that 'code' is a country identifier composed by two
    letters (i.e ES or US). A 'ValueError' exception will be raised when
    this identifier is not valid. If this value is valid, 'term' parameter
    will be ignored.

    When the given values do not match with any country from the registry
    a 'NotFounError' exception will be raised.

    :param db: database manager
    :param code: country identifier composed by two letters
    :param term: term to match with countries names

    :returns: a list of countries sorted by their country id

    :raises ValueError: raised when 'code' is not a string composed by
        two letters
    :raises NotFoundError: raised when the given 'code' or 'term' is not
        found for any country from the registry
    """
    def _is_code_valid(code):
        return type(code) == str \
            and len(code) == 2 \
            and code.isalpha()

    if code is not None and not _is_code_valid(code):
        raise ValueError('country code must be a 2 length alpha string - %s given' \
                         % str(code))

    cs = []

    with db.connect() as session:
        query = session.query(Country)

        if code or term:
            if code:
                query = query.filter(Country.code == code.upper())
            elif term:
                query = query.filter(Country.name.like('%' + term + '%'))

            cs = query.order_by(Country.code).all()

            if not cs:
                e = code if code else term
                raise NotFoundError(entity=e)
        else:
            cs = session.query(Country).\
                order_by(Country.code).all()

        # Detach objects from the session
        session.expunge_all()

    return cs


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
    all those enrollments where Enrollment.start >= from_date AND
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
    :raises ValeError: it is raised in two cases, when "from_date" < 1900-01-01 or
        "to_date" > 2100-01-01; when "from_date > to_date".
    """
    if not from_date:
        from_date = MIN_PERIOD_DATE
    if not to_date:
        to_date = MAX_PERIOD_DATE

    if from_date < MIN_PERIOD_DATE or from_date > MAX_PERIOD_DATE:
        raise ValueError('start date %s is out of bounds' % str(from_date))
    if to_date < MIN_PERIOD_DATE or to_date > MAX_PERIOD_DATE:
        raise ValueError('end date %s is out of bounds' % str(to_date))

    if from_date and to_date and from_date > to_date:
        raise ValueError('start date %s cannot be greater than %s'
                         % (from_date, to_date))

    enrollments = []

    with db.connect() as session:
        query = session.query(Enrollment).\
            join(UniqueIdentity, Organization).\
            filter(Enrollment.start >= from_date,
                   Enrollment.end <= to_date)

        # Filter by uuid
        if uuid:
            uidentity = session.query(UniqueIdentity).\
                filter(UniqueIdentity.uuid == uuid).first()

            if not uidentity:
                raise NotFoundError(entity=uuid)

            query = query.filter(Enrollment.uidentity == uidentity)

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
                                     Enrollment.start,
                                     Enrollment.end).all()

        # Detach objects from the session
        session.expunge_all()

    return enrollments
