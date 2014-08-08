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


class Withdraw(Command):

    def __init__(self, **kwargs):
        super(Withdraw, self).__init__(**kwargs)

        self._set_database(**kwargs)

    def withdraw(self, uuid, organization, from_date=None, to_date=None):
        """Withdraw a unique identity from an organization.

        This method removes all the enrollments between the unique identity,
        identified by <uuid>, and <organization>. Both entities must exist
        on the registry before being deleted.

        When a period of time is given using either <from_date> and <to_date>
        parameters, it will remove those enrollments which their periods fall
        between these two parameters. Default values for these dates
        are '1900-01-01' and '2100-01-01'.

        :param uuid: unique identifier
        :param organization: name of the organization
        :param from_date: date when the enrollment starts
        :param to_date: date when the enrollment ends
        """
        # Empty or None values for uuid and organizations are not allowed,
        # so do nothing
        if not uuid or not organization:
            return

        try:
            api.delete_enrollment(self.db, uuid, organization, from_date, to_date)
        except (NotFoundError, ValueError), e:
            print "Error: %s" % str(e)
