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


class Add(Command):

    def __init__(self, **kwargs):
        super(Add, self).__init__(**kwargs)

        self._set_database(**kwargs)

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
            print "New identity added to %s" % (new_uuid)
        except (AlreadyExistsError, NotFoundError, ValueError), e:
            print "Error: %s" % str(e)
