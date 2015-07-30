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

import argparse
import sys

from sortinghat import api
from sortinghat.command import Command
from sortinghat.db.model import MIN_PERIOD_DATE, MAX_PERIOD_DATE
from sortinghat.exceptions import AlreadyExistsError, NotFoundError,\
    InvalidFormatError, LoadError, MatcherNotSupportedError
from sortinghat.matcher import create_identity_matcher
from sortinghat.matching import SORTINGHAT_IDENTITIES_MATCHERS
from sortinghat.parsing.sh import SortingHatParser


class Load(Command):
    """Import data into the registry.

    This command is able to import data about identities, organizations and
    domains. Data are read, by default, from the standard input. Files can also
    be used as data input giving the path to file as a positional argument.

    By default, identities and organizations are both loaded but two parameters
    can be used to import some parts from the input. When '--identities' option
    is set, only the data related to identities will be loaded. Identities
    matching engine is set with '--matching' option. By default, no matching
    engine is selected. The parameter '--match-new' can also be used to match
    only those identities that are new on the registry.

    Take into account that those organizations set on each identity enrollment
    will be loaded despite '--identities' option were set.

    In the same way, when '--orgs' option is set, the command will only import
    the data from 'organizations' section. Remember that a domain can only be
    assigned to one organization. If one of the given domains is already on the
    registry, the new relationship will NOT be created unless --overwrite
    option were set.
    """
    def __init__(self, **kwargs):
        super(Load, self).__init__(**kwargs)

        self._set_database(**kwargs)
        self.new_uids = set()

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Actions
        group = self.parser.add_mutually_exclusive_group(required=False)
        group.add_argument('--identities', action='store_true',
                           help="import identities")
        group.add_argument('--orgs', action='store_true',
                           help="import organizations")

        # General options
        self.parser.add_argument('--overwrite', action='store_true',
                                 help="force to overwrite existing domain relationships")

        # Matching options
        group = self.parser.add_argument_group('matching options')
        group.add_argument('-m', '--matching', dest='matching', default=None,
                           choices=SORTINGHAT_IDENTITIES_MATCHERS,
                           help="match and merge using this type of matching")
        group.add_argument('-n', '--match-new', dest='match_new', action='store_true',
                           help="match and merge only new unique identities")
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
        return "%(prog)s load [-v] [--identities | --orgs] [-m matching] [-n] [--overwrite] [file]"

    def log(self, msg, debug=True):
        if debug:
            s = msg + '\n'
            sys.stdout.write(s.encode('UTF-8'))

    def warning(self, msg, debug=True):
        if debug:
            Command.warning(self, msg)

    def run(self, *args):
        """Import data on the registry.

        By default, it reads the data from the standard input. If a positional
        argument is given, it will read the data from there.
        """
        params = self.parser.parse_args(args)

        try:
            stream = self.__read_file(params.infile)
            parser = SortingHatParser(stream)
        except InvalidFormatError, e:
            self.error(unicode(e))
            return
        except (IOError, TypeError, AttributeError), e:
            raise RuntimeError(unicode(e))

        if params.identities:
            self.import_blacklist(parser)
            self.import_identities(parser, params.matching,
                                   params.match_new, params.verbose)
        elif params.orgs:
            self.import_organizations(parser, params.overwrite)
        else:
            self.import_organizations(parser, params.overwrite)
            self.import_blacklist(parser)
            self.import_identities(parser, params.matching,
                                   params.match_new, params.verbose)

    def import_blacklist(self, parser):
        """Import blacklist.

        New entries parsed by 'parser' will be added to the blacklist.

        :param parser: sorting hat parser
        """
        blacklist = parser.blacklist

        self.log("Loading blacklist...")
        n = 0

        for entry in blacklist:
            try:
                api.add_to_matching_blacklist(self.db, entry.excluded)
                self.display('load_blacklist.tmpl', entry=entry.excluded)
                n += 1
            except ValueError, e:
                raise RuntimeError(unicode(e))
            except AlreadyExistsError, e:
                msg = "%s. Not added." % unicode(e)
                self.warning(msg)

        self.log("%d/%d blacklist entries loaded" % (n, len(blacklist)))

    def import_organizations(self, parser, overwrite=False):
        """Import organizations.

        New domains and organizations parsed by 'parser' will be added
        to the registry. Remember that a domain can only be assigned to
        one organization. If one of the given domains is already on the registry,
        the new relationship will NOT be created unless 'overwrite' were set
        to 'True'.

        :param parser: sorting hat parser
        :param overwrite: force to reassign domains
        """
        orgs = parser.organizations

        for org in orgs:
            try:
                api.add_organization(self.db, org.name)
            except ValueError, e:
                raise RuntimeError(unicode(e))
            except AlreadyExistsError, e:
                pass

            for dom in org.domains:
                try:
                    api.add_domain(self.db, org.name, dom.domain,
                                   is_top_domain=dom.is_top_domain,
                                   overwrite=overwrite)
                    self.display('load_domains.tmpl', domain=dom.domain,
                                 organization=org.name)
                except (ValueError, NotFoundError), e:
                    raise RuntimeError(unicode(e))
                except AlreadyExistsError, e:
                    msg = "%s. Not updated." % unicode(e)
                    self.warning(msg)

    def import_identities(self, parser, matching=None, match_new=False,
                          verbose=False):
        """Import identities information on the registry.

        New unique identities, organizations and enrollment data parsed
        by 'parser' will be added to the registry.

        Optionally, this method can look for possible identities that match with
        the new one to insert using 'matching' method. If a match is found,
        that means both identities are likely the same. Therefore, both identities
        would be merged into one. The 'match_new' parameter can be set to match
        and merge only new loaded identities.

        :param parser: sorting hat parser
        :param matching: type of matching used to merge existing identities
        :param match_new: match and merge only the new loaded identities
        :param verbose: run in verbose mode when matching is set
        """
        matcher = None

        if matching:
            try:
                blacklist = api.blacklist(self.db)
                matcher = create_identity_matcher(matching, blacklist)
            except MatcherNotSupportedError, e:
                self.error(unicode(e))
                return

        uidentities = parser.identities

        try:
            self.__load_unique_identities(uidentities, matcher, match_new,
                                          verbose)
        except LoadError, e:
            self.error(unicode(e))

    def __load_unique_identities(self, uidentities, matcher, match_new,
                                 verbose):
        """Load unique identities"""

        self.new_uids.clear()

        n = 0

        self.log("Loading unique identities...")

        for uidentity in uidentities:
            self.log("\n=====", verbose)
            self.log("+ Processing %s" % uidentity.uuid, verbose)

            try:
                stored_uuid = self.__load_unique_identity(uidentity, verbose)
            except LoadError, e:
                self.error("%s Skipping." % unicode(e))
                self.log("=====", verbose)
                continue

            stored_uuid = self.__load_identities(uidentity.identities, stored_uuid,
                                                 verbose)

            # The profile will be loaded when the stored unique identity
            # does not have any one.
            try:
                self.__load_profile(uidentity.profile, stored_uuid, verbose)
            except Exception, e:
                self.error("%s. Loading %s profile. Skipping profile." % \
                           (unicode(e), stored_uuid))

            self.__load_enrollments(uidentity.enrollments, stored_uuid,
                                    verbose)

            if matcher and (not match_new or stored_uuid in self.new_uids):
                stored_uuid = self._merge_on_matching(stored_uuid, matcher,
                                                      verbose)

            self.log("+ %s (old %s) loaded" % (stored_uuid, uidentity.uuid))
            self.log("=====", verbose)
            n += 1

        self.log("%d/%d unique identities loaded" % (n, len(uidentities)))

    def __load_unique_identity(self, uidentity, verbose):
        """Seek or store unique identity"""

        uuid = uidentity.uuid

        if uuid:
            try:
                api.unique_identities(self.db, uuid)
                self.log("-- %s already exists." % uuid, verbose)
                return uuid
            except NotFoundError, e:
                self.log("-- %s not found. Generating a new UUID." % uuid, verbose)

        # We don't have a unique identity, so we have to create
        # a new one.
        if len(uidentity.identities) == 0:
            msg = "not enough info to load %s unique identity." % uidentity.uuid
            raise LoadError(cause=msg)

        identity = uidentity.identities.pop(0)

        try:
            stored_uuid = api.add_identity(self.db, identity.source,
                                           identity.email,
                                           identity.name,
                                           identity.username)
            self.new_uids.add(stored_uuid)
        except AlreadyExistsError, e:
            stored_uuid = e.uuid
            self.warning("-- " + unicode(e))
        except ValueError, e:
            raise LoadError(cause=unicode(e))

        self.log("-- using %s for %s unique identity." % (stored_uuid, uuid), verbose)

        return stored_uuid

    def __load_identities(self, identities, uuid, verbose):
        """Store identities"""

        self.log("-- loading identities", verbose)

        for identity in identities:
            try:
                api.add_identity(self.db, identity.source, identity.email,
                                 identity.name, identity.username, uuid)
                self.new_uids.add(uuid)
            except AlreadyExistsError, e:
                self.warning(unicode(e), verbose)

                stored_uuid = e.uuid

                if uuid != stored_uuid:
                    msg = "%s is already assigned to %s. Merging." % (uuid, stored_uuid)
                    self.warning(msg, verbose)

                    api.merge_unique_identities(self.db, uuid, stored_uuid)

                    if uuid in self.new_uids:
                        self.new_uids.remove(uuid)

                    self.new_uids.add(stored_uuid)
                    uuid = stored_uuid

        self.log("-- identities loaded", verbose)

        return uuid

    def __load_profile(self, profile, uuid, verbose):
        """Create a new profile when the unique identity does not have any."""

        uid = api.unique_identities(self.db, uuid)[0]

        if uid.profile:
            self.log("-- profile already available for %s. Not updated" % uuid, verbose)
            return

        if profile:
            self.__create_profile(profile, uuid, verbose)
        else:
            self.__create_profile_from_identities(uid.identities, uuid, verbose)

    def __create_profile(self, profile, uuid, verbose):
        """Create profile information from a profile object"""

        # Set parameters to edit
        kw = profile.to_dict()
        kw['country_code'] = profile.country_code

        # Remove unused keywords
        kw.pop('uuid')
        kw.pop('country')

        api.edit_profile(self.db, uuid, **kw)

        self.log("-- profile %s updated" % uuid, verbose)

    def __create_profile_from_identities(self, identities, uuid, verbose):
        """Create a profile using the data from the identities"""

        import re

        EMAIL_ADDRESS_REGEX = ur"^(?P<email>[^\s@]+@[^\s@.]+\.[^\s@]+)$"
        NAME_REGEX = ur"^\w+\s\w+"

        name = None
        email = None
        username = None

        for identity in identities:
            if not name and identity.name:
                m = re.match(NAME_REGEX, identity.name)

                if m:
                    name = identity.name

            if not email and identity.email:
                m = re.match(EMAIL_ADDRESS_REGEX, identity.email)

                if m:
                    email = identity.email

            if not username:
                if identity.username and identity.username != 'None':
                    username = identity.username

        # We need a name for each profile, so if no one was defined,
        # use email or username to complete it.
        if not name:
            if email:
                name = email.split('@')[0]
            elif username:
                # filter email addresses on username fields
                name = username.split('@')[0]
            else:
                name = 'Unknown'

        kw = {'name' : name,
              'email' : email}

        api.edit_profile(self.db, uuid, **kw)

        self.log("-- profile %s updated" % uuid, verbose)

    def __load_enrollments(self, enrollments, uuid, verbose):
        """Store enrollments"""

        self.log("-- loading enrollments", verbose)

        organizations = []

        for enrollment in enrollments:
            organization = enrollment.organization.name

            try:
                api.add_organization(self.db, organization)
            except AlreadyExistsError, e:
                msg = "%s. Organization not updated." % unicode(e)
                self.warning(msg, verbose)

            if organization not in organizations:
                organizations.append(organization)

            from_date = max(MIN_PERIOD_DATE, enrollment.start)
            to_date = min(MAX_PERIOD_DATE, enrollment.end)

            if from_date != enrollment.start or to_date != enrollment.end:
                msg = "Dates out of bound. Set to %s and %s." % (str(from_date), str(to_date))
                self.warning(msg, verbose)

            try:
                api.add_enrollment(self.db, uuid, enrollment.organization.name,
                                   from_date, to_date)
            except AlreadyExistsError, e:
                msg = "%s. Enrollment not updated." % unicode(e)
                self.warning(msg, verbose)
            except (ValueError, NotFoundError), e:
                raise LoadError(cause=unicode(e))

        for organization in organizations:
            api.merge_enrollments(self.db, uuid, organization)

        self.log("-- enrollments loaded", verbose)

    def _merge_on_matching(self, uuid, matcher, verbose):
        """Merge unique identity with uuid when a match is found"""

        matches = api.match_identities(self.db, uuid, matcher)

        new_uuid = uuid

        u = api.unique_identities(self.db, uuid)[0]

        for m in matches:
            if m.uuid == uuid:
                continue

            self._merge(u, m, verbose)

            new_uuid = m.uuid

            # Swap uids to merge with those that could
            # remain on the list with updated info
            u = api.unique_identities(self.db, m.uuid)[0]

        return new_uuid

    def _merge(self, from_uid, to_uid, verbose):
        """Merge unique identity uid on match"""

        if verbose:
            self.display('match.tmpl', uid=from_uid, match=to_uid)

        api.merge_unique_identities(self.db, from_uid.uuid, to_uid.uuid)

        if verbose:
            self.display('merge.tmpl', from_uuid=from_uid.uuid, to_uuid=to_uid.uuid)

    def __read_file(self, infile):
        """Read a file into a str object"""

        return infile.read().decode('UTF-8')
