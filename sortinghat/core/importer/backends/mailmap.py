# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2023 Bitergia
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
#     Jose Javier Merchante <jjmerchante@bitergia.com>
#

import email.utils
import logging
import re
from urllib.request import urlopen

from sortinghat.core.importer.backend import IdentitiesImporter
from sortinghat.core.importer.models import (Individual,
                                             Identity,
                                             Enrollment,
                                             Organization)
from sortinghat.core.errors import InvalidFormatError
from sortinghat.core.models import MIN_PERIOD_DATE, MAX_PERIOD_DATE

MAILMAP_NO_ORGS = ['Unaffiliated']


logger = logging.getLogger(__name__)


class MailmapImporter(IdentitiesImporter):

    NAME = 'mailmap'

    def get_individuals(self):
        data = self._fetch_data()
        parser = MailmapParser(data, has_orgs=False)
        return parser.individuals

    def _fetch_data(self):
        with urlopen(self.url) as fd:
            content = fd.read().decode()
        return content


class MailmapParser:
    """Parse identities and organizations using mailmap format.

    Mailmap format is a plain stream that contains information
    about identities and their alias. It can also be used to match
    organizations and identities.

    Parsed individuals will be stored in an object named
    'individuals'. The keys of this object are the UUID of the individuals.
    Each individual object stores a list of identities and enrollments and
    the profile.

    Organizations are stored in 'organizations' object. Its keys
    are the name of the organizations and each organization object is
    related to a list of domains.

    :param data: data to parse
    :param has_orgs: set if the stream maps data about organizations
    :param source: source of the identities

    :raises InvalidFormatError: raised when the format of the stream is
        not valid.
    """
    LINES_TO_IGNORE_REGEX = r"^\s*(?:#.*)?\s*$"

    def __init__(self, data, has_orgs=False, source='mailmap'):
        self._individuals = {}
        self._organizations = {}
        self.source = source

        self.__parse(data, has_orgs)

    @property
    def individuals(self):
        uids = [u for u in self._individuals.values()]
        return uids

    @property
    def organizations(self):
        orgs = [o for o in self._organizations.values()]
        return orgs

    def __parse(self, stream, has_orgs):
        """Parse identities and organizations using mailmap format.

        Mailmap format is a text plain document that stores on each
        line a map between an email address and its aliases. Each
        line follows any of the next formats:

            Proper Name <commit@email.xx>
            <proper@email.xx> <commit@email.xx>
            Proper Name <proper@email.xx> <commit@email.xx>
            Proper Name <proper@email.xx> Commit Name <commit@email.xx>

        When the flag `has_orgs` is set, the stream maps organizations
        an identities, following the next format:

            Organization Name <org@email.xx> Proper Name <proper@email.xx>

        :parse data: mailmap stream to parse

        :raise InvalidFormatError: raised when the format of the stream is
            not valid.
        """
        if has_orgs:
            self.__parse_organizations(stream)
        else:
            self.__parse_identities(stream)

    def __parse_organizations(self, stream):
        """Parse organizations stream"""

        for aliases in self.__parse_stream(stream):
            # Parse identity
            identity = self.__parse_alias(aliases[1])
            uuid = identity.email

            individual = self._individuals.get(uuid, None)

            if not individual:
                individual = Individual(uuid=uuid)
                individual.identities.append(identity)
                self._individuals[uuid] = individual

            # Parse organization
            mailmap_id = aliases[0]
            name = self.__encode(mailmap_id[0])

            if name in MAILMAP_NO_ORGS:
                continue

            org = Organization(name=name)
            self._organizations[name] = org

            enrollment = Enrollment(start=MIN_PERIOD_DATE, end=MAX_PERIOD_DATE,
                                    organization=org, individual=individual)
            individual.enrollments.append(enrollment)

    def __parse_identities(self, stream):
        """Parse identities stream"""

        for aliases in self.__parse_stream(stream):
            identity = self.__parse_alias(aliases[0])
            uuid = identity.email

            individual = self._individuals.get(uuid, None)

            if not individual:
                individual = Individual(uuid=uuid)
                individual.identities.append(identity)

            for alias in aliases[1:]:
                identity = self.__parse_alias(alias)
                individual.identities.append(identity)

            self._individuals[uuid] = individual

    def __parse_alias(self, alias):
        name = self.__encode(alias[0])
        email_addr = self.__encode(alias[1])
        identity = Identity(name=name, email=email_addr, username=None,
                            source=self.source)
        return identity

    def __parse_stream(self, stream):
        """Generic method to parse mailmap streams"""

        nline = 0
        lines = stream.split('\n')

        for line in lines:
            nline += 1

            # Ignore blank lines and comments
            m = re.match(self.LINES_TO_IGNORE_REGEX, line, re.UNICODE)
            if m:
                continue

            line = line.strip('\n').strip(' ')
            parts = line.split('>')

            if len(parts) == 0:
                cause = "line %s: invalid format" % str(nline)
                raise InvalidFormatError(cause=cause)

            aliases = []

            for part in parts:
                part = part.replace(',', ' ')
                part = part.strip('\n').strip(' ')

                if len(part) == 0:
                    continue

                if part.find('<') < 0:
                    cause = "line %s: invalid format" % str(nline)
                    raise InvalidFormatError(cause=cause)

                alias = email.utils.parseaddr(part + '>')
                aliases.append(alias)

            yield aliases

    def __encode(self, s):
        return s if s else None
