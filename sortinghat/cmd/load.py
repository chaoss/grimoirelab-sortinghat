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
    BadFileFormatError, LoadError, MatcherNotSupportedError
from sortinghat.matcher import create_identity_matcher


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

        # Matching options
        group = self.parser.add_argument_group('matching options')
        group.add_argument('-m', '--matching', dest='matching', default=None,
                           help="match and merge using this type of matching")
        group.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                           help="run verbose mode while matching and merging")

        # Positional arguments
        self.parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                                 default=sys.stdin,
                                 help="input file")

    @property
    def description(self):
        return """Import data on the registry."""

    @property
    def usage(self):
        return "%(prog)s load --identities [-m matching] [-v] [file]\n   or: %(prog)s load --domains [--overwrite] [file]"

    def run(self, *args):
        """Import data on the registry.

        By default, it reads the data from the standard input. If a positional
        argument is given, it will read the data from there.
        """
        params = self.parser.parse_args(args)

        if params.identities:
            self.import_identities(params.infile, params.source,
                                   params.matching, params.verbose)
        elif params.domains:
            self.import_domains(params.infile, params.overwrite)

    def import_identities(self, infile, source='unknown', matching=None,
                          verbose=False):
        """Import identities information from a file on the registry.

        New unique identities, organizations and enrollment data stored
        on 'infile' will be added to the registry.

        Optionally, this method can look for possible identities that match with
        the new one to insert using 'matching' method. If a match is found,
        that means both identities are likely the same. Therefore, both identities
        would be merged into one.

        :param infile: file to import
        :param source: name of the source where the identities were extracted
        :param matching: type of matching used to merge existing identities
        :param verbose: run in verbose mode when matching is set
        """
        matcher = None

        if matching:
            try:
                matcher = create_identity_matcher(matching)
            except MatcherNotSupportedError, e:
                self.error(str(e))
                return

        try:
            identities = self.__parse_identities_file(infile)
        except BadFileFormatError, e:
            self.error(str(e))
            return
        except (IOError, TypeError, AttributeError), e:
            raise RuntimeError(str(e))

        if 'committers' in identities:
            loader = EclipseIdentitiesLoader(self.db)
        elif 'identities' in identities:
            loader = GrimoireIdentitiesLoader(self.db)
        else:
            self.error("format not supported")
            return

        try:
            loader.display = self.display
            loader.warning = self.warning
            loader.load(identities, source, matcher, verbose)
        except LoadError, e:
            self.error(str(e))

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
                api.add_domain(self.db, organization, domain,
                               overwrite=overwrite)
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


class IdentitiesLoader(object):
    """Abstract class for loading identities."""

    def __init__(self, db):
        self.db = db

    def load(self, identities, source, matcher=None, verbose=False):
        raise NotImplementedError

    def display(self, msg):
        raise NotImplementedError

    def warning(self, msg):
        raise NotImplementedError

    def _merge_on_matching(self, uuid, matcher, verbose):
        matches = api.match_identities(self.db, uuid, matcher)

        u = api.unique_identities(self.db, uuid)[0]

        for m in matches:
            if m.uuid == uuid:
                continue

            self._merge(u, m, verbose)

            # Swap uids to merge with those that could
            # remain on the list with updated info
            u = api.unique_identities(self.db, m.uuid)[0]

    def _merge(self, uid, match, verbose):
        if verbose:
            self.display('match.tmpl', uid=uid, match=match)

        api.merge_unique_identities(self.db, uid.uuid, match.uuid)

        if verbose:
            self.display('merge.tmpl', from_uuid=uid.uuid, to_uuid=match.uuid)


class GrimoireIdentitiesLoader(IdentitiesLoader):
    """Import identities using Metrics Grimoire identities format.

    This class imports in the registry sets of identities defined
    by the Metrics Grimoire JSON format. When a new instance is
    created, do not forget to set warning method.

    :param db: database manager
    """
    def __init__(self, db):
        super(GrimoireIdentitiesLoader, self).__init__(db)

    def load(self, identities, source, matcher=None, verbose=False):
        """Load a set of identities.

        Method to import identities into the registry. Identities schema must
        follow Metrics Grimoire JSON format. This format includes 'source'
        and 'time' properties that are ignored during loading process.

        LoadError exception is raised when either the format is invalid
        or an error occurs importing the data.

        When 'matcher' parameter is given, this method will look for similar
        identities among those on the registry. If a match is found, identities
        will be merged. The matcher is an instance of IdentityMatcher class.

        :param identities: identities stored in a JSON object
        :param source: name of the source where the identities come from
        :param matcher: matcher instance used to find similar identities
        :param verbose: run in verbose mode when matcher is set
        """
        try:
            for identity in identities['identities']:
                uuid = self.__import_identity_json(identity, source)

                if matcher:
                    self._merge_on_matching(uuid, matcher, verbose)
        except KeyError, e:
            msg = "invalid json format. Attribute %s not found" % e.args
            raise LoadError(cause=msg)

    def __import_identity_json(self, identity, source):
        """Import an identity from a json dict"""

        encode = lambda s: s.encode('UTF-8') if s else None

        name = encode(identity['name'])
        email = encode(identity['email'])
        username = encode(identity['username'])

        try:
            uuid = api.add_identity(self.db, source, email,
                                    name, username)
        except AlreadyExistsError, e:
            uuid = e.uuid
            msg = "%s. Unique identity not updated." % str(e)
            self.warning(msg)

        return uuid


class EclipseIdentitiesLoader(IdentitiesLoader):
    """Import identities using Eclipse identities format.

    This class imports in the registry sets of identities defined
    by the Eclipse identities JSON format. When a new instance is
    created, do not forget to set warning method.

    :param db: database manager
    """
    def __init__(self, db):
        super(EclipseIdentitiesLoader, self).__init__(db)

    def load(self, identities, source, matcher=None, verbose=False):
        """Load a set of identities.

        Method to import identities into the registry. Identities schema must
        follow Eclipse JSON format. LoadError exception is raised when either
        the format is invalid or an error occurs importing the data.

        When 'matcher' parameter is given, this method will look for similar
        identities among those on the registry. If a match is found, identities
        will be merged. The matcher is an instance of IdentityMatcher class.

        :param identities: identities stored in a JSON object
        :param source: name of the source where the identities come from
        :param matcher: matcher instance used to find similar identities
        :param verbose: run in verbose mode when matcher is set
        """
        try:
            for identity in identities['committers'].values():
                uuid = self.__import_identity_json(identity, source)

                if 'affiliations' in identity:
                    self.__import_affiliations_json(uuid, identity['affiliations'])

                if matcher:
                    self._merge_on_matching(uuid, matcher, verbose)
        except KeyError, e:
            msg = "invalid json format. Attribute %s not found" % e.args
            raise LoadError(cause=msg)

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
                raise LoadError(cause=str(e))

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
                raise LoadError(cause=str(e))
