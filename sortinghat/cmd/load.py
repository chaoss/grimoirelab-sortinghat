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
import json
import sys
import re

import dateutil.parser

from sortinghat import api
from sortinghat.command import Command
from sortinghat.db.model import MIN_PERIOD_DATE, MAX_PERIOD_DATE
from sortinghat.exceptions import AlreadyExistsError, NotFoundError,\
    BadFileFormatError


# Regex for parsing domains input
LINES_TO_IGNORE_REGEX = ur"^\s*(#.*)?\s*$"
DOMAINS_LINE_REGEX = ur"^(?P<domain>\w\S+)[ \t]+(?P<organization>\w[^#\t\n\r\f\v]+)(([ \t]+#.+)?|\s*)$"


class Load(Command):
    """Import data into the registry.

    This command is able to import data about identities, organizationsa and
    domains. Data are read, by default, from the standard input. Files can also
    be used as data input giving the path to file as a positional argument.

    Identities are added to the registry using the option '--identities' while
    domains are added using the option '--domains'. Remember that a domain can
    only be assigned to one company. If one of the given domains is already on
    the registry, the new relationship will NOT be created unless --overwrite
    option were set.

    Using the option '--source' will set on the registry where the information
    to load comes from. This option only has effect when loading identities.
    The default value for '--source' is 'unknown'.
    """
    def __init__(self, **kwargs):
        super(Load, self).__init__(**kwargs)

        self._set_database(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Actions
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument('--identities', action='store_true',
                           help="import identities")
        group.add_argument('--domains', action='store_true',
                           help="import domains - organizations file")

        # General options
        self.parser.add_argument('--source', dest='source', default='unknown',
                                 help="name of the source where the information to load comes from")
        self.parser.add_argument('--overwrite', action='store_true',
                                 help="force to overwrite existing domain relationships")

        # Positional arguments
        self.parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                                 default=sys.stdin,
                                 help="input file")

    @property
    def description(self):
        return """Import data on the registry."""

    @property
    def usage(self):
        return "%(prog)s load --identities [file]\n   or: %(prog)s load --domains [--overwrite] [file]"

    def run(self, *args):
        """Import data on the registry.

        By default, it reads the data from the standard input. If a positional
        argument is given, it will read the data from there.
        """
        params = self.parser.parse_args(args)

        infile = params.infile

        if params.identities:
            source = params.source
            self.import_identities(infile, source)
        elif params.domains:
            overwrite = params.overwrite
            self.import_domains(infile, overwrite)

    def import_identities(self, infile, source='unknown'):
        """Import identities information from a file on the registry.

        New unique identities, organizations and enrollment data stored
        on 'infile' will be added to the registry.

        :param infile: file to import
        :param source: name of the source where the identities were extracted
        """
        try:
            identities = self.__parse_identities_file(infile)
        except BadFileFormatError, e:
            self.error(str(e))
            return
        except (IOError, TypeError, AttributeError), e:
            raise RuntimeError(str(e))

        if not 'committers' in identities:
            return

        # Add identities
        try:
            for identity in identities['committers'].values():
                uuid = self.__import_identity_json(identity, source)

                if not 'affiliations' in identity:
                    continue

                self.__import_affiliations_json(uuid, identity['affiliations'])
        except KeyError, e:
            # This is a BadFileFormatError
            msg = "invalid json format. Attribute %s not found" % e.args
            self.error(msg)

    def import_domains(self, infile, overwrite=False):
        """Import domains from a file on the registry.

        New domains and organizations stored on 'infile' will be added
        to the registry. Remember that a domain can only be assigned to
        one company. If one of the given domains is already on the registry,
        the new relationship will NOT be created unless 'overwrite' were set
        to 'True'.

        Each line of the file has to contain a domain and a company, separated
        by white spaces or tabs. Comment lines start with the hash character (#)
        For example:

        # Domains from domains.txt
        example.org        Example
        example.com        Example
        bitergia.com       Bitergia
        libresoft.es       LibreSoft
        example.org        LibreSoft

        :param infile: file to import
        :param overwrite: force to reassign domains
        """
        try:
            entries = self.__parse_domains_file(infile)
        except BadFileFormatError, e:
            self.error(str(e))
            return
        except (IOError, TypeError), e:
            raise RuntimeError(str(e))

        for domain, organization in entries:
            # Add organization
            try:
                api.add_organization(self.db, organization)
            except ValueError, e:
                raise RuntimeError(str(e))
            except AlreadyExistsError, e:
                pass

            # Add domain
            try:
                api.add_domain(self.db, organization, domain, overwrite)
                self.display('load_domains.tmpl', domain=domain,
                             organization=organization)
            except (ValueError, NotFoundError), e:
                raise RuntimeError(str(e))
            except AlreadyExistsError, e:
                msg = "%s. Not updated." % str(e)
                self.warning(msg)

    def __parse_identities_file(self, infile):
        """Parse identities file object into a dict"""

        content = infile.read().decode('UTF-8')

        try:
            data = json.loads(content)
        except ValueError, e:
            cause = "invalid json format. %s" % str(e)
            raise BadFileFormatError(cause=cause)

        return data

    def __parse_domains_file(self, infile):
        """Parse domains file object into a list of tuples"""

        domains = []
        nline = 0

        for line in infile:
            nline += 1

            line = line.decode('UTF-8')

            # Ignore blank lines and comments
            m = re.match(LINES_TO_IGNORE_REGEX, line, re.UNICODE)
            if m:
                continue

            m = re.match(DOMAINS_LINE_REGEX, line, re.UNICODE)
            if not m:
                cause = "invalid format on line %s" % str(nline)
                raise BadFileFormatError(cause=cause)

            domain = m.group('domain').strip()
            organization = m.group('organization').strip()
            domains.append((domain, organization))

        return domains

    def __import_identity_json(self, identity, source):
        """Import an identity from a json dict"""

        name = (identity['first'] + ' ' + identity['last']).encode('UTF-8')
        email = identity['primary'].encode('UTF-8')
        username = identity['id'].encode('UTF-8')

        try:
            uuid = api.add_identity(self.db, source, email,
                                    name, username)
        except AlreadyExistsError, e:
            uuid = e.uuid
            msg = "%s. Unique identity not updated." % str(e)
            self.warning(msg)

        if not 'email' in identity:
            return uuid

        # Import alternative identities
        for alt_email in identity['email']:
            if alt_email == email:
                continue
            try:
                api.add_identity(self.db, source,
                                 alt_email, name, username, uuid)
            except AlreadyExistsError, e:
                msg = "%s. Identity not updated." % str(e)
                self.warning(msg)
            except (ValueError, NotFoundError), e:
                raise RuntimeError(str(e))

        return uuid

    def __import_affiliations_json(self, uuid, affiliations):
        """Import identity's affiliations from a json dict"""

        for affiliation in affiliations.values():
            organization = affiliation['name'].encode('UTF-8')

            try:
                api.add_organization(self.db, organization)
            except AlreadyExistsError, e:
                msg = "%s. Organization not updated." % str(e)
                self.warning(msg)

            to_datetime = lambda x, d: dateutil.parser.parse(x) if x else d

            from_date = to_datetime(affiliation['active'], MIN_PERIOD_DATE)
            to_date = to_datetime(affiliation['inactive'], MAX_PERIOD_DATE)

            try:
                api.add_enrollment(self.db, uuid, organization,
                                   from_date, to_date)
            except AlreadyExistsError, e:
                msg = "%s. Enrollment not updated." % str(e)
                self.warning(msg)
            except (ValueError, NotFoundError), e:
                raise RuntimeError(str(e))
