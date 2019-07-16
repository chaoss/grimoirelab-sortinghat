# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2019 Bitergia
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
import hashlib
import json
import os

from .. import api
from ..command import Command, CMD_SUCCESS, HELP_LIST
from ..exceptions import MatcherNotSupportedError
from ..matcher import create_identity_matcher, match
from ..matching import SORTINGHAT_IDENTITIES_MATCHERS

logger = logging.getLogger(__name__)

RECOVERY_FOLDER = '~/.sortinghat.d/'


class Unify(Command):
    """Merge unique identities using a matching algorithm.

    The command looks for sets of similar identities using the given
    <matcher>, merging those identities into one unique identity.

    When <interactive> parameter is set, the command will wait for
    the user verification to merge both identities.
    """
    def __init__(self, **kwargs):
        super(Unify, self).__init__(**kwargs)

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Matching options
        self.parser.add_argument('-m', '--matching', dest='matching', default=None,
                                 choices=SORTINGHAT_IDENTITIES_MATCHERS,
                                 help="find similar unique identities using this type of matching")
        self.parser.add_argument('--sources', dest='sources', nargs='*', default=None,
                                 help="unify the unique identities from these sources only")
        self.parser.add_argument('--fast-matching', dest='fast_matching', action='store_true',
                                 help="run fast matching")
        self.parser.add_argument('--no-strict-matching', dest='no_strict', action='store_true',
                                 help="do not rigorous check of values (i.e, well formed email addresses)")
        self.parser.add_argument('-i', '--interactive', action='store_true',
                                 help="run interactive mode while unifying")
        self.parser.add_argument('-r', '--recovery', dest='recovery', action='store_true',
                                 help="Enable recovery mode")

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)
        self.total = 0
        self.matched = 0
        self.recovery = False
        self.recovery_file = RecoveryFile(kwargs['database'], kwargs['host'], kwargs['port'])

    @property
    def description(self):
        return """Merge unique identities using a matching algorithm."""

    @property
    def usage(self):
        usg = "%(prog)s unify"
        usg += " [--matching <matcher>] [--sources <srcs>]"
        usg += " [--fast-matching] [--no-strict-matching] [--interactive] [--recovery]"
        return usg

    def run(self, *args):
        """Merge unique identities using a matching algorithm."""

        params = self.parser.parse_args(args)

        code = self.unify(params.matching, params.sources,
                          params.fast_matching, params.no_strict,
                          params.interactive, params.recovery)

        return code

    def unify(self, matching=None, sources=None,
              fast_matching=False, no_strict_matching=False,
              interactive=False, recovery=False):
        """Merge unique identities using a matching algorithm.

        This method looks for sets of similar identities, merging those
        identities into one unique identity. To determine when two unique
        identities are likely the same, a matching algorithm will be given
        using the parameter <matching>. When this parameter is not given,
        the default algorithm will be used. Rigorous validation of mathching
        values (i.e, well formed email addresses) will be disabled when
        <no_strict_matching> is set to to `True`.

        When <fast_matching> is set, it runs a fast algorithm to find matches
        between identities. This mode will consume more resources (i.e,
        memory) but it is two orders of magnitude faster than the original.
        Not every matcher can support this mode. When this happens, an
        exception will be raised.

        When <interactive> parameter is set to True, the user will have to confirm
        whether these to identities should be merged into one. By default, the method
        is set to False.

        When a list of <sources> is given, only the unique identities from
        those sources will be unified.

        :param matching: type of matching used to merge existing identities
        :param sources: unify the unique identities from these sources only
        :param fast_matching: use the fast mode
        :param no_strict_matching: disable strict matching (i.e, well-formed email addresses)
        :param interactive: interactive mode for merging identities
        :param recovery: if enabled, the unify will read the matching identities stored in
           recovery file (RECOVERY_FILE_PATH) and process them
        """
        matcher = None

        if not matching:
            matching = 'default'

        strict = not no_strict_matching
        self.recovery = recovery

        try:
            blacklist = api.blacklist(self.db)
            matcher = create_identity_matcher(matching, blacklist,
                                              sources, strict)
        except MatcherNotSupportedError as e:
            self.error(str(e))
            return e.code

        uidentities = api.unique_identities(self.db)

        try:
            self.__unify_unique_identities(uidentities, matcher,
                                           fast_matching, interactive)
            self.__display_stats()
        except MatcherNotSupportedError as e:
            self.error(str(e))
            return e.code
        except Exception as e:
            self.__display_stats()
            raise RuntimeError(str(e))

        return CMD_SUCCESS

    def __unify_unique_identities(self, uidentities, matcher,
                                  fast_matching, interactive):
        """Unify unique identities looking for similar identities."""

        self.total = len(uidentities)
        self.matched = 0

        if self.recovery and self.recovery_file.exists():
            print("Loading matches from recovery file: %s" % self.recovery_file.location())
            matched = self.recovery_file.load_matches()
        else:
            matched = match(uidentities, matcher, fastmode=fast_matching)
            # convert the matched identities to a common JSON format to ease resuming operations
            matched = self.__marshal_matches(matched)

        self.__merge(matched, interactive)

        if self.recovery:
            self.recovery_file.delete()

    def __merge(self, matched, interactive):
        """Merge a lists of matched unique identities"""

        for m in matched:
            identities = m['identities']
            uuid = identities[0]

            try:
                for c in identities[1:]:
                    if self.__merge_unique_identities(c, uuid, interactive):
                        self.matched += 1

                        # Retrieve unique identity to show updated info
                        if interactive:
                            uuid = api.unique_identities(self.db, uuid=uuid)[0]
            except Exception as e:
                if self.recovery:
                    self.recovery_file.save_matches(matched)
                raise e

            m['processed'] = True

    def __merge_unique_identities(self, from_uid, to_uid, interactive):
        # By default, always merge
        merge = True

        if interactive:
            self.display('match.tmpl', uid=from_uid, match=to_uid)
            merge = self.__read_verification()

        if not merge:
            return False

        api.merge_unique_identities(self.db, from_uid, to_uid)

        self.display('merge.tmpl', from_uuid=from_uid,
                     to_uuid=to_uid)

        return True

    def __read_verification(self):
        answer = None

        while answer not in ['y', 'Y', 'n', 'N', '']:
            try:
                answer = input("Merge unique identities [Y/n]? ")
            except EOFError:
                return False

        if answer in ['n', 'N']:
            return False

        return True

    def __display_stats(self):
        """Display some stats regarding unify process"""

        self.display('unify.tmpl', processed=self.total,
                     matched=self.matched,
                     unified=self.total - self.matched)

    @staticmethod
    def __marshal_matches(matched):
        """Convert matches to JSON format.

        :param matched: a list of matched identities

        :returns json_matches: a list of matches in JSON format
        """
        json_matches = []
        for m in matched:
            identities = [i.uuid for i in m]

            if len(identities) == 1:
                continue

            json_match = {
                'identities': identities,
                'processed': False
            }
            json_matches.append(json_match)

        return json_matches


class RecoveryFile:
    """A class to perform operation on the recovery file.

    The class contains four static methods that check whether a recovery file exists,
    allow to load the identity matches within it, convert the matches in a JSON
    format and delete the file.

    :param db_name: the name of the database
    :param host: the database host
    :param port: the database port
    """
    def __init__(self, db_name, host, port):
        path = os.path.join(RECOVERY_FOLDER, self.__uuid(db_name, host, port))
        self.recovery_path = os.path.expanduser(path + '.log')

    def location(self):
        """Return the recovery file path"""

        return self.recovery_path

    def exists(self):
        """Check whether a recovery file exists"""

        return os.path.exists(self.location())

    def load_matches(self):
        """Load matches of the previous failed execution from the recovery file.

        :returns matches: a list of matches in JSON format
        """
        if not self.exists():
            return []

        matches = []
        with open(self.location(), 'r') as f:
            for line in f.readlines():
                match_obj = json.loads(line.strip("\n"))
                if match_obj['processed']:
                    continue

                matches.append(match_obj)

        return matches

    def save_matches(self, matches):
        """Save matches of a failed execution to the log.

        :param matches: a list of matches in JSON format
        """
        if not os.path.exists(os.path.dirname(self.location())):
            os.makedirs(os.path.dirname(self.location()))

        with open(self.location(), "w+") as f:
            matches = [m for m in matches if not m['processed']]
            for m in matches:
                match_obj = json.dumps(m)
                f.write(match_obj + "\n")

    def delete(self):
        """Delete the recovery file."""

        if self.exists():
            os.remove(self.location())

    @staticmethod
    def __uuid(*args):
        """Generate a UUID based on the given parameters."""

        s = '-'.join(args)

        sha1 = hashlib.sha1(s.encode('utf-8', errors='surrogateescape'))
        uuid_sha1 = sha1.hexdigest()

        return uuid_sha1
