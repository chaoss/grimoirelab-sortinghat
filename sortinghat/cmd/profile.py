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
from ..exceptions import NotFoundError, WrappedValueError


PROFILE_COMMAND_USAGE_MSG = \
"""%(prog)s profile [--name <name>] [--email <email>] [--country <code>]
                          [--bot | --no-bot] <uuid>"""


class Profile(Command):
    """Edit profile information.

    This command edits the profile information related with the unique
    identity <uuid>. Name, email, country or set if the identity
    is a bot can be changed using this command. If the unique identity
    does not have a profile, this command will create a new one.

    When only the <uuid> is provided, the command will display the profile
    information for the given unique identity.
    """
    def __init__(self, **kwargs):
        super(Profile, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Profile options
        self.parser.add_argument('--name', dest='name', type=str, default=None,
                                 help="name of the unique identity")
        self.parser.add_argument('--email', dest='email', default=None,
                                 help="email of the unique identity")
        self.parser.add_argument('--country', dest='country', default=None,
                                 help="ISO_3166-1 country code")

        group = self.parser.add_mutually_exclusive_group()
        group.add_argument('--bot', dest='is_bot', action='store_true',
                           help="set unique identity as a bot")
        group.add_argument('--no-bot', dest='no_bot', action='store_true',
                           help="unset unique identity as a bot")

        # Positional arguments
        self.parser.add_argument('uuid',
                                 help="unique identity identifier")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

    @property
    def description(self):
        return """Edit profile information."""

    @property
    def usage(self):
        return PROFILE_COMMAND_USAGE_MSG

    def run(self, *args):
        """Endit profile information."""

        #params = self.parser.parse_args(args)

        uuid, kwargs = self.__parse_arguments(*args)

        code = self.edit_profile(uuid, **kwargs)

        return code

    def edit_profile(self, uuid, **kwargs):
        """Edit unique identity profile.

        This method allows to edit or update the profile information of the
        unique identity identified by <uuid>. It calls to the api
        'edit_profile' function, so basically receives the same arguments.
        See API documentation for more info.

        When no other parameters than <uuid> is given, the command will
        show the current information stored on the profile.
        """
        try:
            api.edit_profile(self.db, uuid, **kwargs)
            uid = api.unique_identities(self.db, uuid)[0]

            self.display('profile.tmpl', uid=uid)
        except (NotFoundError, WrappedValueError) as e:
            self.error(str(e))
            return e.code

        return CMD_SUCCESS

    def __parse_arguments(self, *args):
        """Parse command line arguments"""

        params = self.parser.parse_args(args)

        uuid = params.uuid

        kw = {}

        if params.name:
            kw['name'] = self.__decode(params.name)
        if params.email:
            kw['email'] = self.__decode(params.email)
        if params.country:
            kw['country_code'] = self.__decode(params.country)

        if params.is_bot:
            kw['is_bot'] = True
        elif params.no_bot:
            kw['is_bot'] = False

        return uuid, kw

    def __decode(self, s):
        import sys

        if sys.version_info[0] >= 3: # Python 3
            return s
        else: # Python 2
            return s.decode('UTF-8')
