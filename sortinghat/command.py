# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2017 Bitergia
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

import logging
import sys

import jinja2

from .exceptions import DatabaseError
from .db.database import Database

logger = logging.getLogger(__name__)

CMD_SUCCESS = 0
CMD_FAILURE = 1

# List of various help options
HELP_LIST = ['-h', '--help']


class Command(object):
    """Abstract class to run commands"""

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    @property
    def description(self):
        raise NotImplementedError

    @property
    def usage(self):
        raise NotImplementedError

    def run(self, *args):
        raise NotImplementedError

    def display(self, template, **kwargs):
        loader = jinja2.PackageLoader('sortinghat', 'templates')
        env = jinja2.Environment(loader=loader,
                                 lstrip_blocks=True, trim_blocks=True)

        t = env.get_template(template)
        s = t.render(**kwargs)
        sys.stdout.write(s)

    def error(self, msg):
        s = "Error: %s\n" % msg
        sys.stderr.write(s)

    def warning(self, msg):
        s = "Warning: %s\n" % msg
        sys.stderr.write(s)

    def _set_database(self, **kwargs):
        try:
            self.db = Database(kwargs['user'], kwargs['password'],
                               kwargs['database'], kwargs['host'], kwargs['port'])
            logger.info("Database %s:%s %s set", kwargs['database'], kwargs['host'], kwargs['port'])
        except DatabaseError as e:
            raise RuntimeError(str(e))
