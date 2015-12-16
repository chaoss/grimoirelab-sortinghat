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

from .exceptions import MatcherNotSupportedError


class IdentityMatcher(object):
    """Abstract class to determine whether two unique identities match.

    The object receives a list of keyword arguments. The allowed
    keys are listed below (other keywords will be ignored):

       - 'blacklist' : list of entries to ignore during the matching process
    """
    def __init__(self, **kwargs):

        self._kwargs = kwargs

        if 'blacklist' in self._kwargs:
            self.blacklist = [entry.excluded.lower() \
                              for entry in self._kwargs['blacklist']]
            self.blacklist.sort()
        else:
            self.blacklist = []

    def match(self, a, b):
        """Abstract method used to determine if both unique identities are the same.

        Take into account that some identities cannot match when this class
        was initialized with a blacklist.

        :param a: unique identity to match
        :param b: unique identity to match

        :returns: True when both unique identities are likely to be the same.
        """
        raise NotImplementedError

    def match_filtered_identities(self, fa, fb):
        """Abstract method used to determine if both filtered identities are the same.

        :param fa: filtered identity to match
        :param fb: filtered identity to match

        Take into account that some identities cannot match when this class
        was initialized with a blacklist.

        :returns: True when both filtered identities are likely to be the same.
        """
        raise NotImplementedError

    def filter(self, u):
        """Filter the valid identities for this matcher.

        Some identities can be filtered if this class was initialized
        with a blacklist.

        :param u: unique identity which stores the identities to filter

        :returns: a list of identities valid to work with this matcher.
        """
        raise NotImplementedError


class FilteredIdentity(object):
    """Generic class to store filtered identities"""

    def __init__(self, id, uuid):
        self.id = id
        self.uuid = uuid


def create_identity_matcher(matcher='default', blacklist=[]):
    """Create an identity matcher of the given type.

    Factory function that creates an identity matcher object of the type
    defined on 'matcher' parameter. A blacklist can also be added to
    ignore those values while matching.

    :param matcher: type of the matcher
    :param blacklist: list of entries to ignore while matching

    :returns: a identity matcher object of the given type

    :raises MatcherNotSupportedError: when the given matcher type is not
        supported or available
    """
    import sortinghat.matching as matching

    if matcher not in matching.SORTINGHAT_IDENTITIES_MATCHERS:
        raise MatcherNotSupportedError(matcher=str(matcher))

    klass = matching.SORTINGHAT_IDENTITIES_MATCHERS[matcher]

    return klass(blacklist=blacklist)


def match(uidentities, matcher):
    """Find matches in a set of unique identities.

    This function looks for possible similar or equal identities from a set
    of unique identities. The result will be a list of subsets where each
    subset is a list of matching identities.

    :param uidentities: list of unique identities to match
    :param matcher: instance of the matcher

    :returns: a list of subsets with the matched unique identities

    :raises TypeError: when matcher is not an instance of
        IdentityMatcher class
    """
    def match_filtered_identities(x, ids, matcher):
        """Check if an identity matches a set of identities"""

        for y in ids:
            if x.uuid == y.uuid:
                return True
            if matcher.match_filtered_identities(x, y):
                return True
        return False

    def build_result(matches, uuids, no_filtered):
        """Build a list with the matching subsets"""

        result = []

        for m in matches:
            subset = [uuids[m[0].uuid]]

            for id_ in m[1:]:
                u = uuids[id_.uuid]

                if u not in subset:
                    subset.append(u)

            result.append(subset)

        result += no_filtered

        result.sort(key=len, reverse=True)

        return result

    # The algorithm used to find matches starts here
    if not isinstance(matcher, IdentityMatcher):
        raise TypeError("matcher is not an instance of IdentityMatcher")

    uuids = {}
    no_filtered = []

    remaining = []
    matched = []

    # Filter identities
    for uidentity in uidentities:
        n = len(remaining)

        remaining += matcher.filter(uidentity)

        if len(remaining) > n:
            uuids[uidentity.uuid] = uidentity
        else:
            # This uidentity does not have identities to match
            no_filtered.append([uidentity])

    # Find subsets of matches
    while remaining:
        candidates = []
        no_match = []

        x = remaining.pop(0)

        while matched:
            ids = matched.pop(0)

            if match_filtered_identities(x, ids, matcher):
                candidates += ids
            else:
                no_match.append(ids)

        candidates.append(x)

        # Generate the new list of matched subsets
        matched = [candidates] + no_match

    # All subsets were found, create a list and return it
    return build_result(matched, uuids, no_filtered)
