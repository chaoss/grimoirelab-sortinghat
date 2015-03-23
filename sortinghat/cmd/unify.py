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

from sortinghat import api
from sortinghat.command import Command
from sortinghat.exceptions import MatcherNotSupportedError
from sortinghat.matcher import create_identity_matcher
from sortinghat.matching import SORTINGHAT_IDENTITIES_MATCHERS


class Unify(Command):
    """Merge unique identities using a matching algorithm.

    The command looks for sets of similar identities using the given
    <matcher>, merging those identities into one unique identity.
    """
    def __init__(self, **kwargs):
        super(Unify, self).__init__(**kwargs)

        self._set_database(**kwargs)
        self.total = 0
        self.matched = 0

        self.parser = argparse.ArgumentParser(description=self.description,
                                              usage=self.usage)

        # Matching options
        self.parser.add_argument('-m', '--matching', dest='matching', default=None,
                                 choices=SORTINGHAT_IDENTITIES_MATCHERS,
                                 help="find similar unique identities using this type of matching")

    @property
    def description(self):
        return """Merge unique identities using a matching algorithm."""

    @property
    def usage(self):
        return """%(prog)s unify [--matching <matcher>]"""

    def run(self, *args):
        """Merge unique identities using a matching algorithm."""

        params = self.parser.parse_args(args)

        self.unify(params.matching)

    def unify(self, matching=None):
        """Merge unique identities using a matching algorithm.

        This method looks for sets of similar identities, merging those
        identities into one unique identity. To determine when two unique
        identities are likely the same, a matching algorithm will be given
        using the parameter <matching>. When this parameter is not given,
        the default algorithm will be used.

        :param matching: type of matching used to merge existing identities
        """
        matcher = None

        if not matching:
            matching = 'default'

        try:
            matcher = create_identity_matcher(matching)
        except MatcherNotSupportedError, e:
            self.error(str(e))
            return

        uidentities = api.unique_identities(self.db)

        try:
            self.__unify_unique_identities(uidentities, matcher)
            self.__display_stats()
        except Exception, e:
            self.__display_stats()
            raise RuntimeError(unicode(e))

    def __unify_unique_identities(self, uidentities, matcher):
        """Unify unique identities looking for similar identities."""

        remaining = [uidentity for uidentity in uidentities]
        merged = []

        self.total = len(remaining)
        self.matched = 0

        while remaining:
            u = remaining.pop(0)

            was_merged = False

            # Try to find a positive match on the list of merged
            # unique identities. In this case, merge and continue
            # with the next unique identity from the remaining list
            for i in range(len(merged)):
                m = merged[i]

                if not matcher.match(u, m):
                    continue

                # Merge and retrieve the merged uidentity 
                api.merge_unique_identities(self.db, u.uuid, m.uuid)
                m = api.unique_identities(self.db, uuid=m.uuid)[0]
                merged[i] = m
                self.matched += 1

                was_merged = True
                break

            if was_merged:
                continue

            # No match was found on merged list, so find as much as possible
            # matches on the list of remaining unique identities. Those
            # identities that won't match will be added to the not merged
            # list. 
            not_merged = []

            while remaining:
                c = remaining.pop(0)

                if matcher.match(c, u):
                    # Merge and retrieve the merged uidentity 
                    api.merge_unique_identities(self.db, c.uuid, u.uuid)
                    u = api.unique_identities(self.db, uuid=u.uuid)[0]
                    self.matched += 1
                else:
                    not_merged.append(c)

            # Add this unique identity to the list of merged ones, although
            # there were no other identities which matched with it. Swap
            # not merged list with remaining list.
            merged.append(u)

            remaining = not_merged

    def __display_stats(self):
        """Display some stats regarding unify process"""

        self.display('unify.tmpl', processed=self.total,
                     matched=self.matched,
                     unified=self.total - self.matched)
