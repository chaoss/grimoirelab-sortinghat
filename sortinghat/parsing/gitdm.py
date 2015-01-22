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

import re

from sortinghat.db.model import Organization, Domain
from sortinghat.exceptions import InvalidFormatError
from sortinghat.parser import OrganizationsParser


class GitdmOrganizationsParser(OrganizationsParser):
    """Parse organizations using Gitdm format.

    Each line of the stream has to contain a domain and a organization, separated
    by white spaces or tabs. Comment lines start with the hash character (#)
    For example:

    # Domains from domains.txt
    example.org        Example
    example.com        Example
    bitergia.com       Bitergia
    libresoft.es       LibreSoft
    example.org        LibreSoft
    """
    # Regex for parsing domains input
    LINES_TO_IGNORE_REGEX = ur"^\s*(#.*)?\s*$"
    DOMAINS_LINE_REGEX = ur"^(?P<domain>\w\S+)[ \t]+(?P<organization>\w[^#\t\n\r\f\v]+)(([ \t]+#.+)?|\s*)$"

    def __init__(self):
        super(GitdmOrganizationsParser, self).__init__()

    def organizations(self, stream):
        """Parse organizations stream.

        This method creates a generator of Organization objects from the
        'stream' object.

        :param stream: string of organizations

        :returns: organizations generator

        :raises InvalidFormatError: exception raised when the format of
            the stream is not valid
        """
        if not stream:
            raise InvalidFormatError(cause='stream cannot be empty or None')

        nline = 0
        lines = stream.split('\n')

        for line in lines:
            nline += 1

            line = line.decode('UTF-8')

            # Ignore blank lines and comments
            m = re.match(self.LINES_TO_IGNORE_REGEX, line, re.UNICODE)
            if m:
                continue

            m = re.match(self.DOMAINS_LINE_REGEX, line, re.UNICODE)
            if not m:
                cause = "invalid format on line %s" % str(nline)
                raise InvalidFormatError(cause=cause)

            domain = m.group('domain').strip()
            organization = m.group('organization').strip()

            org = Organization(name=organization)
            dom = Domain(domain=domain, is_top_domain=False)
            org.domains.append(dom)

            yield org

    def check(self, stream):
        """Check if the format of the stream could be parsed.

        The method check if the stream could be parsed. This does not imply
        that the stream is a valid input.

        It checks if the first 10 lines follows the Gitdm pattern. If this
        check fails, the stream format is not supported.

        :param stream: string of organizations to check

        :returns: boolean value
        """
        if not stream:
            return False

        lines = stream.split('\n')
        count = min(len(lines), 10)

        for i in range(count):
            line = lines[i]

            m = re.match(self.LINES_TO_IGNORE_REGEX, line, re.UNICODE)
            if m:
                continue

            m = re.match(self.DOMAINS_LINE_REGEX, line, re.UNICODE)
            if not m:
                return False
        return True
