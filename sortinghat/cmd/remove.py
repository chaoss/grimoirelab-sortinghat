# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2017 Bitergia
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

import argparse
import logging

from .. import api
from ..command import Command, CMD_SUCCESS, HELP_LIST
from ..exceptions import NotFoundError


logger = logging.getLogger(__name__)


class Remove(Command):
    """Remove identities from the registry.

    By default, this command removes a unique identity, identified by
    <identifier> from the registry. When '--identity' option is set, it
    will remove an identity, not a unique identity.

    When a unique identity is removed, its related information such as
    enrollments or identities will be also removed.
    """
    def __init__(self, **kwargs):
        super(Remove, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Optional arguments
        self.parser.add_argument('--identity', action='store_true',
                                 help="set to remove an identity")

        # Positional arguments
        self.parser.add_argument('identifier',
                                 help="identifier of the (unique) identity to remove")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

    @property
    def description(self):
        return """Remove unique identities or identities from the registry."""

    @property
    def usage(self):
        return "%(prog)s rm [--identity] <identifier>"

    def run(self, *args):
        """Remove unique identities or identities from the registry.

        By default, it removes the unique identity identified by <identifier>.
        To remove an identity, set <identity> parameter.
        """
        params = self.parser.parse_args(args)

        identifier = params.identifier
        identity = params.identity

        code = self.remove(identifier, identity)

        return code

    def remove(self, uuid_or_id, identity=False):
        """Remove an identity from the registry.

        This method removes the unique identity associated to the given
        uuid and its related information, such as identities or enrollments.
        When <identity> is set to True, it will remove the identity (not the
        unique identity) which its id is <uuid_or_id>.

        :param uuid_or_id: identifier of the unique identity or
            identity to remove
        :param identity: when it is set to True, it will remove an identity,
            not a unique identity.  By default it is set to False.
        """
        if not uuid_or_id:
            return CMD_SUCCESS

        try:
            if not identity:
                api.delete_unique_identity(self.db, uuid_or_id)
            else:
                api.delete_identity(self.db, uuid_or_id)

            self.display('remove.tmpl',
                         uuid_or_id=uuid_or_id, identity=identity)
        except NotFoundError as e:
            self.error(str(e))
            return e.code

        return CMD_SUCCESS
