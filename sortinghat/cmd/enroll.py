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

from sortinghat import api, utils
from sortinghat.command import Command
from sortinghat.exceptions import AlreadyExistsError, InvalidDateError, NotFoundError


class Enroll(Command):
    """Enroll identities in organizations.

    This command enrolls a unique identity, identified by <uuid>,
    in an <organization>. Both entities must exist on the registry before
    creating the new relationship.

    The period of the enrollment can be set with --from and --to parameters,
    where --from must be less or equal than --to. Default values for these
    dates are '1900-01-01' and '2100-01-01'.

    Dates may follow the next pattern: 'YYYY-MM-DD'. Optionally, time
    information can be included using patters like 'YYYY-MM-DD hh:mm:ss'.
    """
    def __init__(self, **kwargs):
        super(Enroll, self).__init__(**kwargs)

        self._set_database(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Enrollment period options
        self.parser.add_argument('--from', dest='from_date', default=None,
                                 help="date (YYYY-MM-DD:hh:mm:ss) when the enrollment starts")
        self.parser.add_argument('--to', dest='to_date', default=None,
                                 help="date (YYYY-MM-DD:hh:mm:ss) when the enrollment ends")

        # Positional arguments
        self.parser.add_argument('uuid', default=None,
                                 help="unique identity to enroll")
        self.parser.add_argument('organization', default=None,
                                 help="organization where the uuid will be enrolled")

    @property
    def description(self):
        return """Enroll identities in organizations."""

    @property
    def usage(self):
        return "%(prog)s enroll [--from <date>] [--to <date>] <uuid> <organization>"

    def run(self, *args):
        """Enroll a unique identity in an organization."""

        params = self.parser.parse_args(args)

        uuid = params.uuid
        organization = params.organization

        try:
            from_date = utils.str_to_datetime(params.from_date)
            to_date = utils.str_to_datetime(params.to_date)

            self.enroll(uuid, organization, from_date, to_date)
        except InvalidDateError, e:
            self.error(str(e))

    def enroll(self, uuid, organization, from_date=None, to_date=None):
        """Enroll a unique identity in an organization.

        This method adds a new relationship between the unique identity,
        identified by <uuid>, and <organization>. Both entities must exist
        on the registry before creating the new enrollment.

        The period of the enrollment can be given with the parameters <from_date>
        and <to_date>, where "from_date <= to_date". Default values for these
        dates are '1900-01-01' and '2100-01-01'.

        :param uuid: unique identifier
        :param organization: name of the organization
        :param from_date: date when the enrollment starts
        :param to_date: date when the enrollment ends
        """
        # Empty or None values for uuid and organizations are not allowed
        if not uuid or not organization:
            return

        try:
            api.add_enrollment(self.db, uuid, organization, from_date, to_date)
        except (AlreadyExistsError, NotFoundError, ValueError), e:
            self.error(str(e))
