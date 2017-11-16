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

from __future__ import absolute_import
from __future__ import unicode_literals

import argparse

from .. import api
from ..command import Command, CMD_SUCCESS, HELP_LIST
from ..exceptions import MatcherNotSupportedError
from ..matcher import create_identity_matcher, match
from ..matching import SORTINGHAT_IDENTITIES_MATCHERS


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

        # Exit early if help is requested
        if 'cmd_args' in kwargs and [i for i in kwargs['cmd_args'] if i in HELP_LIST]:
            return

        self._set_database(**kwargs)
        self.total = 0
        self.matched = 0

    @property
    def description(self):
        return """Merge unique identities using a matching algorithm."""

    @property
    def usage(self):
        usg = "%(prog)s unify"
        usg += " [--matching <matcher>] [--sources <srcs>]"
        usg += " [--fast-matching] [--no-strict-matching] [--interactive]"
        return usg

    def run(self, *args):
        """Merge unique identities using a matching algorithm."""

        params = self.parser.parse_args(args)

        code = self.unify(params.matching, params.sources,
                          params.fast_matching, params.no_strict,
                          params.interactive)

        return code

    def unify(self, matching=None, sources=None,
              fast_matching=False, no_strict_matching=False,
              interactive=False):
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
        """
        matcher = None

        if not matching:
            matching = 'default'

        strict = not no_strict_matching

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

        matched = match(uidentities, matcher, fastmode=fast_matching)
        self.__merge(matched, interactive)

    def __merge(self, matched, interactive):
        """Merge a lists of matched unique identities"""

        for m in matched:



            u = m[0]

            for c in m[1:]:
                if self.__merge_unique_identities(c, u, interactive):
                    self.matched += 1

                    # Retrieve unique identity to show updated info
                    if interactive:
                        u = api.unique_identities(self.db, uuid=u.uuid)[0]

    def __merge_unique_identities(self, from_uid, to_uid, interactive):
        # By default, always merge
        merge = True

        if interactive:
            self.display('match.tmpl', uid=from_uid, match=to_uid)
            merge = self.__read_verification()

        if not merge:
            return False

        api.merge_unique_identities(self.db, from_uid.uuid, to_uid.uuid)

        self.display('merge.tmpl', from_uuid=from_uid.uuid,
                     to_uuid=to_uid.uuid)

        return True

    def __read_verification(self):
        answer = None

        while answer not in ['y', 'Y', 'n', 'N', '']:
            try:
                answer = raw_input("Merge unique identities [Y/n]? ")
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
