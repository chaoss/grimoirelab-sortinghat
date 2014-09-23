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


class Move(Command):

    def __init__(self, **kwargs):
        super(Move, self).__init__(**kwargs)

        self._set_database(**kwargs)

    def move(self, from_id, to_uuid):
        """Move an identity to a unique identity.

        The method moves the identity identified by <from_id> to
        the unique identity <to_uuid>.

        When <to_uuid> is the unique identity that is currently related to
        <from_id>, the action does not have any effect. The same occurs when
        either <from_id> or <to_uuid> are None or empty.

        :param from_id: identifier of the identity set to be moved
        :param to_uuid: identifier of the unique identity where 'from_id'
            will be moved
        """
        if not from_id or not to_uuid:
            return

        try:
            api.move_identity(self.db, from_id, to_uuid)
            self.display('move.tmpl',
                         from_id=from_id, to_uuid=to_uuid)
        except NotFoundError, e:
            self.error(str(e))
