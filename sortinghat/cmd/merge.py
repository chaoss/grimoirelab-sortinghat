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
from sortinghat.exceptions import NotFoundError


class Merge(Command):
    """Merge one unique identity into another.

    This command merges <from_uuid> unique identity into <to_uuid>,
    removing the first unique identity from the registry. Identities
    and enrollments will be also merged. Duplicated enrollments will be
    removed from the registry.
    """
    def __init__(self, **kwargs):
        super(Merge, self).__init__(**kwargs)

        self._set_database(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Positional arguments
        self.parser.add_argument('from_uuid',
                                 help="Unique identity to merge")
        self.parser.add_argument('to_uuid',
                                 help="Merge on this unique identity")

    @property
    def description(self):
        return """Merge a unique identity into another one."""

    @property
    def usage(self):
        return "%(prog)s merge <from_uuid> <to_uuid>"

    def run(self, *args):
        """Merge two identities.

        When <from_uuid> or <to_uuid> are empty the command does not have
        any effect. The same happens when both <from_uuid> and <to_uuid>
        are the same unique identity.
        """
        params = self.parser.parse_args(args)

        from_uuid = params.from_uuid
        to_uuid = params.to_uuid

        self.merge(from_uuid, to_uuid)

    def merge(self, from_uuid, to_uuid):
        """Merge one unique identity into another.

        Method that joins <from_uuid> unique identity into <to_uuid>.
        Identities and enrollments related to <from_uuid> will be
        assigned to <to_uuid>. In addition, <from_uuid> will be removed
        from the registry. Duplicated enrollments will be also removed from the
        registry.

        When <from_uuid> and <to_uuid> are equal, None or empty, the action does
        not have any effect.

        :param from_uuid: identifier of the unique identity set to merge
        :param to_uuid: identifier of the unique identity where 'from_uuid'
            will be merged
        """
        if not from_uuid or not to_uuid:
            return

        try:
            api.merge_unique_identities(self.db, from_uuid, to_uuid)
            self.display('merge.tmpl',
                         from_uuid=from_uuid, to_uuid=to_uuid)
        except NotFoundError, e:
            self.error(str(e))
