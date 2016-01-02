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


BLACKLIST_COMMAND_USAGE_MSG = \
"""%(prog)s blacklist -l [term]
   or: %(prog)s blacklist -a <entry>
   or: %(prog)s blacklist -d <entry>"""


class Blacklist(Command):
    """List, add or delete entries from the blacklist.

    By default, this command lists the blacklist entries that exist
    in the registry. If <term> is given, the method will list only
    those entries that match with that term.

    Add a new entry to the blacklist is using '--add' option. To delete
    entries use '--delete' option.
    """
    def __init__(self, **kwargs):
        super(Blacklist, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Actions
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument('-l', '--list', action='store_true',
                           help="list the entries of the blacklist")
        group.add_argument('-a', '--add', action='store_true',
                           help="add a new entry to the blacklist")
        group.add_argument('-d', '--delete', action='store_true',
                           help="delete an entry form the blacklist")

        # Positional arguments
        self.parser.add_argument('entry', nargs='?', default=None,
                                 help="entry to list, add or remove")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

    @property
    def description(self):
        return """List, add or delete entries from the blacklist."""

    @property
    def usage(self):
        return BLACKLIST_COMMAND_USAGE_MSG

    def run(self, *args):
        """List, add or delete entries from the blacklist.

        By default, it prints the list of entries available on
        the blacklist.
        """
        params = self.parser.parse_args(args)

        entry = params.entry

        if params.add:
            code = self.add(entry)
        elif params.delete:
            code = self.delete(entry)
        else:
            term = entry
            code = self.blacklist(term)

        return code

    def add(self, entry):
        """Add entries to the blacklist.

        This method adds the given 'entry' to the blacklist.

        :param entry: entry to add to the blacklist
        """
        # Empty or None values for organizations are not allowed
        if not entry:
            return CMD_SUCCESS

        try:
            api.add_to_matching_blacklist(self.db, entry)
        except WrappedValueError as e:
            # If the code reaches here, something really wrong has happened
            # because entry cannot be None or empty
            raise RuntimeError(str(e))
        except AlreadyExistsError as e:
            self.error(str(e))
            return e.code

        return CMD_SUCCESS

    def delete(self, entry):
        """Remove entries from the blacklist.

        The method removes the given 'entry' from the blacklist.

        :param entry: entry to remove from the blacklist
        """
        if not entry:
            return CMD_SUCCESS

        try:
            api.delete_from_matching_blacklist(self.db, entry)
        except NotFoundError as e:
            self.error(str(e))
            return e.code

        return CMD_SUCCESS

    def blacklist(self, term=None):
        """List blacklisted entries.

        When no term is given, the method will list the entries that
        exist in the blacklist. If 'term' is set, the method will list
        only those entries that match with that term.

        :param term: term to match
        """
        try:
            bl = api.blacklist(self.db, term)
            self.display('blacklist.tmpl', blacklist=bl)
        except NotFoundError as e:
            self.error(str(e))
            return e.code

        return CMD_SUCCESS
