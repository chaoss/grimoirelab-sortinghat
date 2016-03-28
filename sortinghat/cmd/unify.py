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
        self.parser.add_argument('--fast-matching', dest='fast_matching', action='store_true',
                                 help="run fast matching")
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
        return """%(prog)s unify [--matching <matcher>] [--fast-matching] [--interactive]"""

    def run(self, *args):
        """Merge unique identities using a matching algorithm."""

        params = self.parser.parse_args(args)

        code = self.unify(params.matching, params.fast_matching,
                          params.interactive)

        return code

    def unify(self, matching=None, fast_matching=False, interactive=False):
        """Merge unique identities using a matching algorithm.

        This method looks for sets of similar identities, merging those
        identities into one unique identity. To determine when two unique
        identities are likely the same, a matching algorithm will be given
        using the parameter <matching>. When this parameter is not given,
        the default algorithm will be used.

        When <fast_matching> is set, it runs a fast algorithm to find matches
        between identities. This mode will consume more resources (i.e,
        memory) but it is two orders of magnitude faster than the original.
        Not every matcher can support this mode. When this happens, an
        exception will be raised.

        When <interactive> parameter is set to True, the user will have to confirm
        whether these to identities should be merged into one. By default, the method
        is set to False.

        :param matching: type of matching used to merge existing identities
        :param interactive: interactive mode for merging identities
        """
        matcher = None

        if not matching:
            matching = 'default'

        try:
            blacklist = api.blacklist(self.db)
            matcher = create_identity_matcher(matching, blacklist)
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
            raise RuntimeError(unicode(e))

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

        if interactive:
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
