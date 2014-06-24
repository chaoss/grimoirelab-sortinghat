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

from sortinghat.db.model import Organization, Domain
from sortinghat.exceptions import AlreadyExistsError, NotFoundError


def add_organization(db, organization):
    """Add an organization to the registry.

    This method adds an organization to the registry.
    It checks first whether the organization is already on the registry.
    When it is not found, the new organization is added. Otherwise,
    it raises a 'AlreadyExistsError' exception to notify that the organization
    already exists.

    :param db: database session
    :param organization: name of the organization
    :raise ValueError: raised when organization is None or an empty string
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

    :raise ValueError: raised when domain is None or an empty string
    :raise NotFoundError: raised when the given organization is not found
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
