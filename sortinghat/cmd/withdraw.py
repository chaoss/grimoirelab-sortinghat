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


class Withdraw(Command):
    """Withdraw identities from organizations.

    This command withdraws all the enrollments of a unique identity,
    identified by <uuid>, from an <organization>.

    The period of the enrollments to withdraw can be set with <from> and <to>
    parameters, where <from> must be less or equal than <to>. Default values
    for these dates are '1900-01-01' and '2100-01-01'.

    Dates may follow several patterns. The most common and recommended
    is 'YYYY-MM-DD'. Optionally, time information can be included using
    patters like 'YYYY-MM-DD hh:mm:ss'.
    """
    def __init__(self, **kwargs):
        super(Withdraw, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Enrollment period options
        self.parser.add_argument('--from', dest='from_date', default=None,
                                 help="date (YYYY-MM-DD hh:mm:ss) when the enrollment starts")
        self.parser.add_argument('--to', dest='to_date', default=None,
                                 help="date (YYYY-MM-DD hh:mm:ss) when the enrollment ends")

        # Positional arguments
        self.parser.add_argument('uuid', default=None,
                                 help="unique identity to withdraw")
        self.parser.add_argument('organization', default=None,
                                 help="organization where the uuid is enrolled")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

    @property
    def description(self):
        return """Withdraw identities from organizations."""

    @property
    def usage(self):
        return "%(prog)s withdraw [--from <date>] [--to <date>] <uuid> <organization>"

    def run(self, *args):
        """Withdraw a unique identity from an organization."""

        params = self.parser.parse_args(args)

        uuid = params.uuid
        organization = params.organization

        try:
            from_date = utils.str_to_datetime(params.from_date)
            to_date = utils.str_to_datetime(params.to_date)

            code = self.withdraw(uuid, organization, from_date, to_date)
        except InvalidDateError as e:
            self.error(str(e))
            return e.code

        return code

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
            return CMD_SUCCESS

        try:
            api.delete_enrollment(self.db, uuid, organization, from_date, to_date)
        except (NotFoundError, WrappedValueError) as e:
            self.error(str(e))
            return e.code

        return CMD_SUCCESS
