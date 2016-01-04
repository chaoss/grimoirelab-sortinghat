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

from .. import api, utils
from ..command import Command, CMD_SUCCESS, HELP_LIST
from ..exceptions import InvalidDateError, NotFoundError, WrappedValueError


class Log(Command):
    """List enrollment information available in the registry.

    The command list a set of enrollments. Some searching parameters
    to filter the results are available. Parameters <uuid> and <organization>
    filter by unique identity and organization name. Enrollments between a
    period can also be listed using <from> and <to> parameters, where
    <from> must be less or equal than <to>. Default values for these dates
    are '1900-01-01' and '2100-01-01'.

    Dates may follow several patterns. The most common and recommended
    is 'YYYY-MM-DD'. Optionally, time information can be included using
    patters like 'YYYY-MM-DD hh:mm:ss'.
    """
    def __init__(self, **kwargs):
        super(Log, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Enrollments search options
        self.parser.add_argument('--uuid', default=None,
                                 help="unique identity to withdraw")
        self.parser.add_argument('--organization', default=None,
                                 help="organization where the uuid is enrolled")
        self.parser.add_argument('--from', dest='from_date', default=None,
                                 help="date (YYYY-MM-DD:hh:mm:ss) when the enrollment starts")
        self.parser.add_argument('--to', dest='to_date', default=None,
                                 help="date (YYYY-MM-DD:hh:mm:ss) when the enrollment ends")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

    @property
    def description(self):
        return """List enrollments."""

    @property
    def usage(self):
        return "%(prog)s log [--uuid <uuid>] [--organization <organization>] [--from <date>] [--to <date>]"

    def run(self, *args):
        """List enrollments using search parameters."""

        params = self.parser.parse_args(args)

        uuid = params.uuid
        organization = params.organization

        try:
            from_date = utils.str_to_datetime(params.from_date)
            to_date = utils.str_to_datetime(params.to_date)

            code = self.log(uuid, organization, from_date, to_date)
        except InvalidDateError as e:
            self.error(str(e))
            return e.code

        return code

    def log(self, uuid=None, organization=None, from_date=None, to_date=None):
        """"List enrollment information available in the registry.

        Method that returns a list of enrollments. If <uuid> parameter is set,
        it will return the enrollments related to that unique identity;
        if <organization> parameter is given, it will return the enrollments
        related to that organization; if both parameters are set, the function
        will return the list of enrollments of <uuid> on the <organization>.

        Enrollments between a period can also be listed using <from_date> and
        <to_date> parameters. When these are set, the method will return
        all those enrollments where Enrollment.start >= from_date AND
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
            self.display('log.tmpl', enrollments=enrollments)
        except (NotFoundError, WrappedValueError) as e:
            self.error(str(e))
            return e.code

        return CMD_SUCCESS
