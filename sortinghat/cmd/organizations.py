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

from sortinghat import api
from sortinghat.command import Command
from sortinghat.exceptions import AlreadyExistsError, NotFoundError


class Organizations(Command):

    def __init__(self, **kwargs):
        super(Organizations, self).__init__(**kwargs)

    def add(self, organization, domain=None, overwrite=False):
        """Add organizations and domains to the registry.

        This method adds the given 'organization' or 'domain' to the registry,
        but not both at the same time.

        When 'organization' is the only parameter given, it will be added to
        the registry. When 'domain' parameter is also given, the function will
        assign it to 'organization'. In this case, 'organization' must exists in
        the registry prior adding the domain.

        A domain can only be assigned to one company. If the given domain is already
        in the registry, the method will fail. Set 'overwrite' to 'True' to create
        the new relationship. In this case, previous relationships will be removed.

        :param organization: name of the organization to add
        :param domain: domain to add to the registry
        :param overwrite: force to reassign the domain to the given company
        """
        # Empty or None values for organizations are not allowed
        if not organization:
            return

        if not domain:
            try:
                api.add_organization(self.db, organization)
            except ValueError, e:
                # If the code reaches here, something really wrong has happened
                # because organization cannot be None or empty
                raise RuntimeError(str(e))
            except AlreadyExistsError, e:
                print "Error: %s" % str(e)
        else:
            try:
                api.add_domain(self.db, organization, domain, overwrite)
            except ValueError, e:
                # Same as above, domains cannot be None or empty
                raise RuntimeError(str(e))
            except (AlreadyExistsError, NotFoundError), e:
                print "Error: %s" % str(e)

    def delete(self, organization, domain=None):
        """Remove organizations and domains from the registry.

        The method removes the given 'organization' or 'domain' from the registry,
        but not both at the same time.

        When 'organization' is the only parameter given, it will be removed from
        the registry, including those domains related to it. When 'domain' parameter
        is also given, only the domain will be deleted. 'organization' must exists in
        the registry prior removing the domain.

        :param organization: name of the organization to remove
        :param domain: domain to remove from the registry
        """
        if not organization:
            return

        if not domain:
            try:
                api.delete_organization(self.db, organization)
            except NotFoundError, e:
                print "Error: %s" % str(e)
        else:
            try:
                api.delete_domain(self.db, organization, domain)
            except NotFoundError, e:
                print "Error: %s" % str(e)

    def registry(self, organization=None):
        """List organizations and domains.

        When no organization is given, the method will list the organizations
        existing in the registry. If 'organization' is set, the method will list
        only those domains related with it.

        :param organization: list the domains related to this organization
        """
        try:
            orgs = api.registry(self.db, organization)
            self._pretty_print(orgs)
        except NotFoundError, e:
            print "Error: %s" % e

    def _pretty_print(self, organizations):
        for org in organizations:
            if not org.domains:
                print org.name
                continue

            for dom in org.domains:
                print "%s    %s" % (org.name, dom.domain)
