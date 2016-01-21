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
from ..exceptions import NotFoundError


class Show(Command):
    """Show information about unique identities.

    This command prints information related to the unique identities such as
    identities or enrollments.

    When <uuid> is given, it will only show information about the unique
    identity related to <uuid>.

    When <term> is set, it will only show information about those unique
    identities that have any attribute (name, email, username, source)
    which match with the given term. This parameter does not have any
    effect when <uuid> is set.
    """
    def __init__(self, **kwargs):
        super(Show, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Optional arguments
        self.parser.add_argument('--term', dest='term', default=None,
                                 help="search this term on identities data; ignored when <uuid> is given")
        # Positional arguments
        self.parser.add_argument('uuid', nargs='?', default=None,
                                 help="unique identifier of the identity to show")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

    @property
    def description(self):
        return """Show information about unique identities."""

    @property
    def usage(self):
        return "%(prog)s show [--term <term>][<uuid>]"

    def run(self, *args):
        """Show information about unique identities."""

        params = self.parser.parse_args(args)

        code = self.show(params.uuid, params.term)

        return code

    def show(self, uuid=None, term=None):
        """Show the information related to unique identities.

        This method prints information related to unique identities such as
        identities or enrollments.

        When <uuid> is given, it will only show information about the unique
        identity related to <uuid>.

        When <term> is set, it will only show information about those unique
        identities that have any attribute (name, email, username, source)
        which match with the given term. This parameter does not have any
        effect when <uuid> is set.

        :param uuid: unique identifier
        :param term: term to match with unique identities data
        """
        try:
            if uuid:
                uidentities = api.unique_identities(self.db, uuid)
            elif term:
                uidentities = api.search_unique_identities(self.db, term)
            else:
                uidentities = api.unique_identities(self.db)

            for uid in uidentities:
                # Add enrollments to a new property 'roles'
                enrollments = api.enrollments(self.db, uid.uuid)
                uid.roles = enrollments

            self.display('show.tmpl', uidentities=uidentities)
        except NotFoundError as e:
            self.error(str(e))
            return e.code

        return CMD_SUCCESS
