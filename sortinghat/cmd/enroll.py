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


class Enroll(Command):

    def __init__(self, **kwargs):
        super(Enroll, self).__init__(**kwargs)

        self._set_database(**kwargs)

    def enroll(self, uuid, organization, from_date=None, to_date=None):
        """Enroll a unique identity to an organization.

        This method adda a new relationship between the unique identity,
        identified by <uuid>, and <organization>. Both entities must exist
        on the registry before creating the new enrollment.

        The period of the enrollment can be given with the parameters <from_date>
        and <to_date>, where "from_date <= to_date". Default values for these
        dates are '1900-01-01' and '2100-01-01'.
        """
        # Empty or None values for uuid and organizations are not allowed
        if not uuid or not organization:
            return

        try:
            api.add_enrollment(self.db, uuid, organization, from_date, to_date)
        except (AlreadyExistsError, NotFoundError, ValueError), e:
            print "Error: %s" % str(e)
