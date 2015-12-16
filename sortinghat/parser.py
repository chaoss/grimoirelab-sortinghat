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

from .exceptions import InvalidFormatError


INVALID_FORMAT_MSG = "organizations format not supported. Please check it."


class OrganizationsParser(object):
    """Abstract class for parsing organizations"""

    def organizations(self, stream):
        """Parse organizations from a stream"""
        raise NotImplementedError

    def check(self, stream):
        """Check whether the format of the stream could be valid"""
        raise NotImplementedError


def create_organizations_parser(stream):
    """Create an organizations parser for the given stream.

    Factory function that creates an organizations parser for the
    given stream. The stream is only used to guess the type of the
    required parser.

    :param stream: stream used to guess the type of the parser

    :returns: an organizations parser

    :raise InvalidFormatError: raised when no one of the available
        parsers can parse the given stream
    """
    import sortinghat.parsing as parsing

    # First, try with default parser
    for p in parsing.SORTINGHAT_ORGS_PARSERS:
        klass = parsing.SORTINGHAT_ORGS_PARSERS[p]

        parser = klass()

        if parser.check(stream):
            return parser
    raise InvalidFormatError(cause=INVALID_FORMAT_MSG)
