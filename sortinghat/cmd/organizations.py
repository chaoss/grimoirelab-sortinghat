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

from __future__ import absolute_import
from __future__ import unicode_literals

import argparse

from .. import api
from ..command import Command, CMD_SUCCESS, HELP_LIST
from ..exceptions import AlreadyExistsError, NotFoundError, WrappedValueError


ORGS_COMMAND_USAGE_MSG = \
"""%(prog)s orgs -l [term]
   or: %(prog)s orgs -a <organization> [domain] [--top-domain] [--overwrite]"
   or: %(prog)s orgs -d <organization> [domain]"""


class Organizations(Command):
    """List, add or delete organizations and domains from the registry.

    By default, this command lists the organizations and domains existing
    in the registry. If <term> is given, the method will list only
    those organizations that match with that term.

    Organizations and domains can be added to the registry using '--add'
    option. This will add the given <organization> or <domain>, but not
    both at the same time. When <organization> is the only parameter given,
    it will be added to the registry. When both parameters are given,
    the command will assign <domain> to <organization>. Note: <organization>
    must exists before adding a domain.

    A domain can only be assigned to one company. Use '--overwrite' to to create
    a new relationship. In this case, previous <domain> relationship will be
    removed.

    New domains can be also set as a top domains using '--top-domain' flag. That is
    useful to avoid the insertion of sub-domains that belong to the same organization
    (i.e eu.example.com, us.example.com). Take into account when 'overwrite' is set
    it will also update 'top_domain' flag even when this flag were not set.

    To delete organizations use '--delete' option. When <organization> is the only
    parameter given, it will be removed from the registry, including those domains
    related to it. When both <domain> and <organization> are given, only the domain
    will be deleted.

    Database connection parameters are required to run this command.
    """
    def __init__(self, **kwargs):
        super(Organizations, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Actions
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument('-l', '--list', action='store_true',
                           help="list the contents of the registry")
        group.add_argument('-a', '--add', action='store_true',
                           help="add an organization or domain to the registry")
        group.add_argument('-d', '--delete', action='store_true',
                           help="delete an organization or domain from the registry")

        # Domain options
        group = self.parser.add_argument_group('domain arguments')
        group.add_argument('--top-domain', action='store_true',
                           help="set this domain as a top domain")
        group.add_argument('--overwrite', action='store_true',
                           help="force to overwrite existing domain relationships")

        # Positional arguments
        self.parser.add_argument('organization', nargs='?', default=None,
                                 help="organization to list, add or remove")
        self.parser.add_argument('domain', nargs='?', default=None,
                                 help="domain to add or remove")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

    @property
    def description(self):
        return """List, add or delete organizations and domains from the registry."""

    @property
    def usage(self):
        return ORGS_COMMAND_USAGE_MSG

    def run(self, *args):
        """List, add or delete organizations and domains from the registry.

        By default, it prints the list of organizations available on
        the registry.
        """
        params = self.parser.parse_args(args)

        organization = params.organization
        domain = params.domain
        is_top_domain = params.top_domain
        overwrite = params.overwrite


        if params.add:
            code = self.add(organization, domain, is_top_domain, overwrite)
        elif params.delete:
            code = self.delete(organization, domain)
        else:
            term = organization
            code = self.registry(term)

        return code

    def add(self, organization, domain=None, is_top_domain=False, overwrite=False):
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

        The new domain can be also set as a top domain. That is useful to avoid
        the insertion of sub-domains that belong to the same organization (i.e
        eu.example.com, us.example.com). Take into account when 'overwrite' is set
        it will update 'is_top_domain' flag too.

        :param organization: name of the organization to add
        :param domain: domain to add to the registry
        :param is_top_domain: set the domain as a top domain
        :param overwrite: force to reassign the domain to the given company
        """
        # Empty or None values for organizations are not allowed
        if not organization:
            return CMD_SUCCESS

        if not domain:
            try:
                api.add_organization(self.db, organization)
            except WrappedValueError as e:
                # If the code reaches here, something really wrong has happened
                # because organization cannot be None or empty
                raise RuntimeError(str(e))
            except AlreadyExistsError as e:
                self.error(str(e))
                return e.code
        else:
            try:
                api.add_domain(self.db, organization, domain,
                               is_top_domain=is_top_domain,
                               overwrite=overwrite)
            except WrappedValueError as e:
                # Same as above, domains cannot be None or empty
                raise RuntimeError(str(e))
            except (AlreadyExistsError, NotFoundError) as e:
                self.error(str(e))
                return e.code

        return CMD_SUCCESS

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
            return CMD_SUCCESS

        if not domain:
            try:
                api.delete_organization(self.db, organization)
            except NotFoundError as e:
                self.error(str(e))
                return e.code
        else:
            try:
                api.delete_domain(self.db, organization, domain)
            except NotFoundError as e:
                self.error(str(e))
                return e.code

        return CMD_SUCCESS

    def registry(self, term=None):
        """List organizations and domains.

        When no term is given, the method will list the organizations
        existing in the registry. If 'term' is set, the method will list
        only those organizations and domains that match with that term.

        :param term: term to match
        """
        try:
            orgs = api.registry(self.db, term)
            self.display('organizations.tmpl', organizations=orgs)
        except NotFoundError as e:
            self.error(str(e))
            return e.code

        return CMD_SUCCESS
