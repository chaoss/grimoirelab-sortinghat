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
from sortinghat.exceptions import NotFoundError


class Organizations(Command):

    def __init__(self, **kwargs):
        super(Organizations, self).__init__(**kwargs)

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
