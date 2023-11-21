# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Bitergia
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
#     Jose Javier Merchante <jjmerchante@bitergia.com>
#

from urllib.request import urlopen

import dateutil.parser
import dateutil.tz
import logging
import re

from ..backend import IdentitiesImporter
from sortinghat.core.importer.models import (Individual,
                                             Identity,
                                             Enrollment,
                                             Organization)
from sortinghat.core.errors import InvalidFormatError
from sortinghat.core.models import MIN_PERIOD_DATE, MAX_PERIOD_DATE

logger = logging.getLogger(__name__)


class GitdmImporter(IdentitiesImporter):

    NAME = 'gitdm'

    def __init__(self, ctx, url, aliases_url=None, email_validation=True):
        super().__init__(ctx, url)
        self.aliases_url = aliases_url
        if isinstance(email_validation, str):
            email_validation = email_validation.lower() in ('true', '1')
        self.email_validation = email_validation

    def get_individuals(self):
        """Get the individuals for the given url"""

        data = self._fetch_data(self.url)
        # Some files include '!' instead of '@'
        data = data.replace('!', '@')

        aliases = None
        if self.aliases_url:
            aliases = self._fetch_data(self.aliases_url)

        parser = GitdmParser(aliases=aliases, email_to_employer=data,
                             email_validation=self.email_validation)
        return parser.individuals

    def _fetch_data(self, url):
        with urlopen(url) as fd:
            content = fd.read().decode()
        return content


class GitdmParser(object):
    """Parse identities and organizations using Gitdm files.

    Gitdm provides several files that include information about
    identities, organizations and affiliations. This parser is able
    to parse anyone of these file formats, together or separate.

    The individuals are stored in an object named 'individuals'.
    The keys of this object are the UUID of the individuals.
    Each individual object stores a list of identities and
    enrollments. Email addresses will not be validated when
    `email_validation` is set to `False`.

    Organizations are stored in 'organizations' object. Its keys
    are the name of the organizations and each organization object is
    related to a list of domains.

    :param aliases: aliases stream
    :param email_to_employer: enrollments stream
    :param domain_to_employer: organizations stream
    :param source: source of the data
    :param email_validation: validate email addresses; set to True by default

    :raises InvalidFormatError: raised when the format of any of the
        given streams is not valid.
    """

    # Common Gitdm patterns
    VALID_LINE_REGEX = r"^(\S+)[ \t]+([^#\n\r\f\v]+[^#\s]*)(?:([ \t]+#.*)?|\s*)$"
    LINES_TO_IGNORE_REGEX = r"^\s*(?:#.*)?\s*$"
    EMAIL_ADDRESS_REGEX = r"^(?P<email>[^\s@]+@[^\s@.]+\.[^\s@]+)$"
    ORGANIZATION_REGEX = r"^(?P<organization>[^#<\t\n\r\f\v]*[^#<\t\n\r\f\v\s])?$"
    DOMAIN_REGEX = r"^(?P<domain>\w\S+)$"
    ENROLLMENT_REGEX = r"^(?P<organization>[^#<\n\r\f\v]*[^#<\t\n\r\f\v\s])(?:[ \t]+<[ \t]+(?P<date>\d{4}\-\d{2}\-\d{2}))?$"

    def __init__(self, aliases=None, email_to_employer=None, domain_to_employer=None,
                 source='gitdm', email_validation=True):
        self._individuals = {}
        self._organizations = {}
        self.source = source
        self.email_validation = email_validation

        # Raw data
        self.__raw_identities = {}
        self.__raw_aliases = {}
        self.__raw_orgs = {}

        self.__parse(aliases, email_to_employer,
                     domain_to_employer)

    @property
    def individuals(self):
        uids = [u for u in self._individuals.values()]
        return uids

    @property
    def organizations(self):
        orgs = [o for o in self._organizations.values()]
        return orgs

    def __parse(self, aliases, email_to_employer, domain_to_employer):
        """Parse Gitdm streams"""
        self.__parse_organizations(domain_to_employer)
        self.__parse_identities(aliases, email_to_employer)

    def __parse_identities(self, aliases, email_to_employer):
        """Parse Gitdm identities"""

        # Parse streams
        self.__parse_aliases_stream(aliases)
        self.__parse_email_to_employer_stream(email_to_employer)

        # Create individuals from aliases list
        for alias, email in self.__raw_aliases.items():
            individual = self._individuals.get(email, None)

            if not individual:
                individual = Individual(uuid=email)
                e = re.match(self.EMAIL_ADDRESS_REGEX, email, re.UNICODE)
                if e:
                    identity = Identity(email=email, source=self.source)
                else:
                    identity = Identity(username=email, source=self.source)

                individual.identities.append(identity)

                self._individuals[email] = individual

            # Create identity with alias
            e = re.match(self.EMAIL_ADDRESS_REGEX, alias, re.UNICODE)
            if e:
                identity = Identity(email=alias, source=self.source)
            else:
                identity = Identity(username=alias, source=self.source)
            individual.identities.append(identity)

        # Create individuals from enrollments list
        for email, enrs in self.__raw_identities.items():

            if email in self._individuals:
                individual = self._individuals[email]
            elif email in self.__raw_aliases:
                canonical = self.__raw_aliases[email]
                individual = self._individuals[canonical]
            else:
                individual = Individual(uuid=email)
                identity = Identity(email=email, source=self.source)
                individual.identities.append(identity)
                self._individuals[email] = individual

            # Assign enrollments
            enrs.sort(key=lambda r: r[1])
            start_date = MIN_PERIOD_DATE

            for rol in enrs:
                name = rol[0]
                org = self._organizations.get(name, None)

                if not org:
                    org = Organization(name=name)
                    self._organizations[name] = org

                end_date = rol[1]

                enrollment = Enrollment(start=start_date, end=end_date,
                                        organization=org)
                individual.enrollments.append(enrollment)

                if end_date != MAX_PERIOD_DATE:
                    start_date = end_date

    def __parse_organizations(self, domain_to_employer):
        """Parse Gitdm organizations"""

        # Parse streams
        self.__parse_domain_to_employer_stream(domain_to_employer)

        for org, doms in self.__raw_orgs.items():
            o = Organization(name=org)
            for dom in doms:
                o.domains.append(dom)
            self._organizations[org] = o

    def __parse_aliases_stream(self, stream):
        """Parse aliases stream.

        The stream contains a list of usernames (they can be email addresses
        their username aliases. Each line has a username and an alias separated
        by tabs. Comment lines start with the hash character (#).

        Example:

        # List of email aliases
        jsmith@example.com    jsmith@example.net
        jsmith@example.net    johnsmith@example.com
        jdoe@example.com      john_doe@example.com
        jdoe@example          john_doe@example.com
        """
        if not stream:
            return

        f = self.__parse_aliases_line

        for alias_entries in self.__parse_stream(stream, f):
            alias = alias_entries[0]
            username = alias_entries[1]

            self.__raw_aliases[alias] = username

    def __parse_email_to_employer_stream(self, stream):
        """Parse email to employer stream.

        The stream contains a list of email addresses and their employers.
        Each line has an email address and a organization name separated by
        tabs. Optionally, the date when the identity withdrew from the
        organization can be included followed by a '<' character. Comment
        lines start with the hash character (#).

        Example:

        # List of enrollments
        jsmith@example.com    Example Company # John Smith
        jdoe@example.com    Example Company   # John Doe
        jsmith@example.com    Bitergia < 2015-01-01  # John Smith - Bitergia
        """
        if not stream:
            return

        f = self.__parse_email_to_employer_line

        for rol in self.__parse_stream(stream, f):
            email = rol[0]
            org = rol[1]
            rol_date = rol[2]

            if org not in self.__raw_orgs:
                self.__raw_orgs[org] = []

            if email not in self.__raw_identities:
                self.__raw_identities[email] = [(org, rol_date)]
            else:
                self.__raw_identities[email].append((org, rol_date))

    def __parse_domain_to_employer_stream(self, stream):
        """Parse domain to employer stream.

        Each line of the stream has to contain a domain and a organization,
        or employer, separated by tabs. Comment lines start with the hash
        character (#)

        Example:

        # Domains from domains.txt
        example.org        Example
        example.com        Example
        bitergia.com       Bitergia
        libresoft.es       LibreSoft
        example.org        LibreSoft
        """
        if not stream:
            return

        f = self.__parse_domain_to_employer_line

        for o in self.__parse_stream(stream, f):
            org = o[0]
            dom = o[1]

            if org not in self.__raw_orgs:
                self.__raw_orgs[org] = []

            self.__raw_orgs[org].append(dom)

    def __parse_stream(self, stream, parse_line):
        """Generic method to parse gitdm streams"""

        if not stream:
            raise InvalidFormatError(cause='stream cannot be empty or None')

        nline = 0
        lines = stream.split('\n')

        for line in lines:
            nline += 1

            # Ignore blank lines and comments
            m = re.match(self.LINES_TO_IGNORE_REGEX, line, re.UNICODE)
            if m:
                continue

            m = re.match(self.VALID_LINE_REGEX, line, re.UNICODE)
            if not m:
                cause = "Skip: '%s' -> line %s: invalid line format" % (line, str(nline))
                logger.warning(cause)
                continue

            try:
                result = parse_line(m.group(1), m.group(2))
                yield result
            except InvalidFormatError as e:
                cause = "Skip: '%s' -> line %s: %s" % (line, str(nline), e)
                logger.warning(cause)
                continue

    def __parse_aliases_line(self, raw_alias, raw_username):
        """Parse aliases lines"""

        alias = self.__encode(raw_alias)
        username = self.__encode(raw_username)

        return alias, username

    def __parse_email_to_employer_line(self, raw_email, raw_enrollment):
        """Parse email to employer lines"""

        e = re.match(self.EMAIL_ADDRESS_REGEX, raw_email, re.UNICODE)
        if not e and self.email_validation:
            cause = "invalid email format: '%s'" % raw_email
            raise InvalidFormatError(cause=cause)

        if self.email_validation:
            email = e.group('email').strip()
        else:
            email = raw_email

        raw_enrollment = raw_enrollment.strip() if raw_enrollment != ' ' else raw_enrollment
        r = re.match(self.ENROLLMENT_REGEX, raw_enrollment, re.UNICODE)
        if not r:
            cause = "invalid enrollment format: '%s'" % raw_enrollment
            raise InvalidFormatError(cause=cause)

        org = r.group('organization').strip()
        date = r.group('date')

        if date:
            try:
                dt = dateutil.parser.parse(r.group('date'))
                dt = dt.replace(tzinfo=dateutil.tz.tzutc())
            except Exception as e:
                cause = "invalid date: '%s'" % date
                logger.warning(cause)
                dt = MAX_PERIOD_DATE
        else:
            dt = MAX_PERIOD_DATE

        email = self.__encode(email)
        org = self.__encode(org)

        return email, org, dt

    def __parse_domain_to_employer_line(self, raw_domain, raw_org):
        """Parse domain to employer lines"""

        d = re.match(self.DOMAIN_REGEX, raw_domain, re.UNICODE)
        if not d:
            cause = "invalid domain format: '%s'" % raw_domain
            raise InvalidFormatError(cause=cause)

        dom = d.group('domain').strip()

        raw_org = raw_org.strip() if raw_org != ' ' else raw_org
        o = re.match(self.ORGANIZATION_REGEX, raw_org, re.UNICODE)
        if not o:
            cause = "invalid organization format: '%s'" % raw_org
            raise InvalidFormatError(cause=cause)

        org = o.group('organization').strip()

        org = self.__encode(org)
        dom = self.__encode(dom)

        return org, dom

    def __encode(self, s):
        return s if s else None
