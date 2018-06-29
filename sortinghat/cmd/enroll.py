# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2018 Bitergia
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

import argparse
import logging

from .. import api
from ..command import Command, CMD_SUCCESS, HELP_LIST
from ..exceptions import AlreadyExistsError, InvalidDateError, NotFoundError, InvalidValueError
from ..utils import  (MAX_PERIOD_DATE,
                      MIN_PERIOD_DATE,
                      str_to_datetime)


logger = logging.getLogger(__name__)


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

    Setting the option --merge will merge overlapped enrollments related
    to <uuid> and <organization> found on the registry. The given enrollment
    will be also merged.
    """
    def __init__(self, **kwargs):
        super(Enroll, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Enrollment period options
        self.parser.add_argument('--from', dest='from_date', default=None,
                                 help="date (YYYY-MM-DD hh:mm:ss) when the enrollment starts")
        self.parser.add_argument('--to', dest='to_date', default=None,
                                 help="date (YYYY-MM-DD hh:mm:ss) when the enrollment ends")

        # Merge enrollment option
        self.parser.add_argument('--merge', action='store_true',
                                 help="merge existing enrollments")

        # Positional arguments
        self.parser.add_argument('uuid', default=None,
                                 help="unique identity to enroll")
        self.parser.add_argument('organization', default=None,
                                 help="organization where the uuid will be enrolled")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)

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
            from_date = str_to_datetime(params.from_date)
            to_date = str_to_datetime(params.to_date)
            merge = params.merge

            code = self.enroll(uuid, organization, from_date, to_date, merge)
        except InvalidDateError as e:
            self.error(str(e))
            return e.code

        return code

    def enroll(self, uuid, organization, from_date=MIN_PERIOD_DATE, to_date=MAX_PERIOD_DATE,
               merge=False):
        """Enroll a unique identity in an organization.

        This method adds a new relationship between the unique identity,
        identified by <uuid>, and <organization>. Both entities must exist
        on the registry before creating the new enrollment.

        The period of the enrollment can be given with the parameters <from_date>
        and <to_date>, where "from_date <= to_date". Default values for these
        dates are '1900-01-01' and '2100-01-01'.

        When "merge" parameter is set to True, those overlapped enrollments related
        to <uuid> and <organization> found on the registry will be merged. The given
        enrollment will be also merged.

        :param uuid: unique identifier
        :param organization: name of the organization
        :param from_date: date when the enrollment starts
        :param to_date: date when the enrollment ends
        :param merge: merge overlapped enrollments; by default, it is set to False
        """
        # Empty or None values for uuid and organizations are not allowed
        if not uuid or not organization:
            return CMD_SUCCESS

        try:
            api.add_enrollment(self.db, uuid, organization, from_date, to_date)
            code = CMD_SUCCESS
        except (NotFoundError, InvalidValueError) as e:
            self.error(str(e))
            code = e.code
        except AlreadyExistsError as e:
            if not merge:
                msg_data = {
                    'uuid': uuid,
                    'org': organization,
                    'from_dt': str(from_date),
                    'to_dt': str(to_date)
                }
                msg = "enrollment for '%(uuid)s' at '%(org)s' (from: %(from_dt)s, to: %(to_dt)s) already exists in the registry"
                msg = msg % msg_data
                self.error(msg)
                code = e.code

        if not merge:
            return code

        try:
            api.merge_enrollments(self.db, uuid, organization)
        except (NotFoundError, InvalidValueError) as e:
            # These exceptions were checked above. If any of these raises
            # is due to something really wrong has happened
            raise RuntimeError(str(e))

        return CMD_SUCCESS
