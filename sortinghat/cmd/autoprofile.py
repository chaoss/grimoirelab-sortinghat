# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2016 Bitergia
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
import collections

from .. import api
from ..command import Command, CMD_SUCCESS, HELP_LIST
from ..exceptions import NotFoundError, WrappedValueError


AUTOPROFILE_COMMAND_USAGE_MSG = \
"""%(prog)s autoprofile <source> ... <source>"""


class AutoProfile(Command):
    """Auto complete profile information.

    This command autocompletes the profiles information related to
    a set of unique identities. To update the profile, this command
    uses a list of sources ordered by priority. Only those unique
    identities which have one or more identities from any of these
    sources will be updated.
    """
    def __init__(self, **kwargs):
        super(AutoProfile, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Positional arguments
        self.parser.add_argument('source', nargs='+',
                                 help="list of sources used to autocomplete ordered by priority")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

    @property
    def description(self):
        return """Autocomplete profiles information."""

    @property
    def usage(self):
        return AUTOPROFILE_COMMAND_USAGE_MSG

    def run(self, *args):
        """Autocomplete profile information."""

        params = self.parser.parse_args(args)
        sources = params.source
        code = self.autocomplete(sources)

        return code

    def autocomplete(self, sources):
        """Autocomplete unique identities profiles.

        Autocomplete unique identities profiles using the information
        of their identities. The selection of the data used to fill
        the profile is prioritized using a list of sources.
        """
        identities = self.__select_autocomplete_identities(sources)

        for uuid, ids in identities.items():
            # Among the identities (with the same priority) selected
            # to complete the profile, it will choose the longest 'name'.
            # If no name is available, it will use the field 'username'.
            name = None
            email = None

            for identity in ids:
                if not name:
                    name = identity.name or identity.username
                elif identity.name and len(identity.name) > len(name):
                    name = identity.name

                if not email and identity.email:
                    email = identity.email

            kw = {
                'name' : name,
                'email' : email
            }

            try:
                api.edit_profile(self.db, uuid, **kw)
                self.display('autoprofile.tmpl', identity=identity)
            except (NotFoundError, WrappedValueError) as e:
                self.error(str(e))
                return e.code

        return CMD_SUCCESS

    def __select_autocomplete_identities(self, sources):
        """Select the identities used for autocompleting"""

        MIN_PRIORITY = 99999999

        checked = {}

        for source in sources:
            uids = api.unique_identities(self.db, source=source)

            for uid in uids:
                if uid.uuid in checked:
                    continue

                max_priority = MIN_PRIORITY
                selected = []

                for identity in sorted(uid.identities, key=lambda x: x.id):
                    try:
                        priority = sources.index(identity.source)

                        if priority < max_priority:
                            selected = [identity]
                            max_priority = priority
                        elif priority == max_priority:
                            selected.append(identity)
                    except ValueError:
                        continue

                checked[uid.uuid] = selected

        identities = collections.OrderedDict(sorted(checked.items(),
                                             key=lambda t: t[0]))

        return identities
