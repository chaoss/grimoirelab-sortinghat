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

import argparse

from sortinghat import api
from sortinghat.command import Command
from sortinghat.exceptions import AlreadyExistsError, NotFoundError


class Add(Command):
    """Add an identity to the registry.

    This command adds a new identity to the registry. By default, a new
    unique identity will be also added an associated to the new identity.
    When <uuid> parameter is set, it only creates a new identity that will be
    associated to a unique identity defined by <uuid>.

    To add a new identity, at least one of <name>, <email> or <username> must
    be provided. The default value for <source> is 'unknown'.

    The registry considers that two identities are distinct when any value
    of the tuple <source>, <email>, <name>, <username> is different. Thus, the
    identities  id1:('scm', 'jsmith@example.com', 'John Smith', 'jsmith')
    and id2:('mls', 'jsmith@example.com', 'John Smith', 'jsmith') will be
    registered as different identities.
    """
    def __init__(self, **kwargs):
        super(Add, self).__init__(**kwargs)

        self._set_database(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Identity options
        self.parser.add_argument('--source', dest='source', default='unknown',
                                 help="source where the identity comes from")
        self.parser.add_argument('--name', dest='name', default=None,
                                 help="name of the identity")
        self.parser.add_argument('--email', dest='email', default=None,
                                 help="email address of the identity")
        self.parser.add_argument('--username', dest='username', default=None,
                                 help="user name of the identity")
        self.parser.add_argument('--uuid', dest='uuid', default=None,
                                 help="associates identity to this unique identity")

    @property
    def description(self):
        return """Add an identity to the registry."""

    @property
    def usage(self):
        return "%(prog)s add [--name <name>] [--email <email>] [--username <user>] [--source <src>] [--uuid <uuid>]"

    def run(self, *args):
        """Add an identity to the registry."""

        params = self.parser.parse_args(args)

        self.add(params.source, params.email, params.name, params.username,
                 params.uuid)

    def add(self, source, email=None, name=None, username=None, uuid=None):
        """Add an identity to the registry.

        This method adds a new identity to the registry. By default, a new
        unique identity will be also added an associated to the new identity.
        When <uuid> parameter is set, it only creates a new identity that will be
        associated to a unique identity defined by <uuid>.

        The method will print the uuid associated to the new registered identity.

        :param source: data source
        :param email: email of the identity
        :param name: full name of the identity
        :param username: user name used by the identity
        :param uuid: associates the new identity to the unique identity
            identified by this id
        """
        try:
            new_uuid = api.add_identity(self.db, source, email, name, username, uuid)
            self.display('add.tmpl', new_uuid=new_uuid)
        except (AlreadyExistsError, NotFoundError, ValueError), e:
            print "Error: %s" % str(e)
