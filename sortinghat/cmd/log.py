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


class Log(Command):

    def __init__(self, **kwargs):
        super(Log, self).__init__(**kwargs)

        self._set_database(**kwargs)

    def log(self, uuid=None, organization=None, from_date=None, to_date=None):
        """"List enrollment information available in the registry.

        Method that returns a list of enrollments. If <uuid> parameter is set,
        it will return the enrollments related to that unique identity;
        if <organization> parameter is given, it will return the enrollments
        related to that organization; if both parameters are set, the function
        will return the list of enrollments of <uuid> on the <organization>.

        Enrollments between a period can also be listed using <from_date> and
        <to_date> parameters. When these are set, the method will return
        all those enrollments where Enrollment.init >= from_date AND
        Enrollment.end <= to_date. Defaults values for these dates are
        1900-01-01 and 2100-01-01.

        :param db: database manager
        :param uuid: unique identifier
        :param organization: name of the organization
        :param from_date: date when the enrollment starts
        :param to_date: date when the enrollment ends
        """
        try:
            enrollments = api.enrollments(self.db, uuid, organization,
                                          from_date, to_date)
            self._pretty_print(enrollments)
        except (NotFoundError, ValueError), e:
            print "Error: %s" % str(e)

    def _pretty_print(self, enrollments):
        for rol in enrollments:
            uuid = rol.identity.identifier
            organization = rol.organization.name
            from_date = str(rol.init)
            to_date = str(rol.end)
            print "%s    %s    %s    %s" % (uuid, organization, from_date, to_date)
