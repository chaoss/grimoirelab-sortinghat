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
import sys
import re

from sortinghat import api
from sortinghat.command import Command
from sortinghat.exceptions import AlreadyExistsError, NotFoundError,\
    BadFileFormatError


# Regex for parsing domains input
LINES_TO_IGNORE_REGEX = ur"^\s*(#.*)?\s*$"
DOMAINS_LINE_REGEX = ur"^(?P<domain>\w\S+)[ \t]+(?P<organization>\w[^#\t\n\r\f\v]+)(([ \t]+#.+)?|\s*)$"


class Load(Command):
    """Import organizations and domains on the registry.

    Organizations and domains are read, by default, from the standard input.
    Files can also be used as data input giving the path to file as a positional
    argument.

    Domains are added to the registry using the option '--domains'. Remember
    that a domain can only be assigned to one company. If one of the given
    domains is already on the registry, the new relationship will NOT be
    created unless --overwrite option were set.

    Database connection parameters are required to run this command.
    """
    def __init__(self, **kwargs):
        super(Load, self).__init__(**kwargs)

        self._set_database(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Actions
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument('--domains', action='store_true',
                           help="import domains - organizations file")

        # General options
        self.parser.add_argument('--overwrite', action='store_true',
                                 help="force to overwrite existing domain relationships")

        # Positional arguments
        self.parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                                 default=sys.stdin,
                                 help="domains - organization file")

    @property
    def description(self):
        return """Import a list of organizations and domains."""

    @property
    def usage(self):
        return "%(prog)s load --domains [--overwrite] [file]"

    def run(self, *args):
        """Import a list of organizations and domains.

        By default, it reads the data from the standard input. If a positional
        argument is given, it will read the data from there.
        """
        params = self.parser.parse_args(args)

        infile = params.infile
        overwrite = params.overwrite

        if params.domains:
            self.import_domains(infile, overwrite)

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
            print "Error: %s" % str(e)
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
                print "Warning: %s. Not updated." % str(e)

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
