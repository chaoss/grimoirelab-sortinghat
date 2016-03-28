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

    @staticmethod
    def matching_criteria():
        """List of keys used during the matching phase.

        This list is only required for matching using the fast mode
        algorithm. Otherwise, raises a `NotImplemetedError` exception.

        returns: a list of keys
        """
        raise NotImplementedError


class FilteredIdentity(object):
    """Generic class to store filtered identities"""

    def __init__(self, id, uuid):
        self.id = id
        self.uuid = uuid

    def to_dict(self):
        return {
                'id'   : self.id,
                'uuid' : self.uuid
               }

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


def match(uidentities, matcher, fastmode=False):
    """Find matches in a set of unique identities.

    This function looks for possible similar or equal identities from a set
    of unique identities. The result will be a list of subsets where each
    subset is a list of matching identities.

    When `fastmode` is set a new and experimental matching algorithm
    will be used. It consumes more resources (a big amount of memory)
    but it is, at least, two orders of maginute faster than the
    classic algorithm.

    :param uidentities: list of unique identities to match
    :param matcher: instance of the matcher
    :param fastmode: use a faster algorithm

    :returns: a list of subsets with the matched unique identities

    :raises MatcherNotSupportedError: when matcher does not support fast
        mode matching
    :raises TypeError: when matcher is not an instance of
        IdentityMatcher class
    """
    if not isinstance(matcher, IdentityMatcher):
        raise TypeError("matcher is not an instance of IdentityMatcher")

    if fastmode:
        try:
            matcher.matching_criteria()
        except NotImplementedError:
            name = "'%s (fast mode)'" % matcher.__class__.__name__.lower()
            raise MatcherNotSupportedError(matcher=name)

    filtered, no_filtered, uuids = \
        _filter_unique_identities(uidentities, matcher)

    if not fastmode:
        matched = _match(filtered, matcher)
    else:
        matched = _match_with_pandas(filtered, matcher)

    matched = _build_matches(matched, uuids, no_filtered, fastmode)

    return matched


def _match(filtered, matcher):
    """Old method to find matches in a set of filtered identities."""

    def match_filtered_identities(x, ids, matcher):
        """Check if an identity matches a set of identities"""

        for y in ids:
            if x.uuid == y.uuid:
                return True
            if matcher.match_filtered_identities(x, y):
                return True
        return False

    # Find subsets of matches
    matched = []

    while filtered:
        candidates = []
        no_match = []

        x = filtered.pop(0)

        while matched:
            ids = matched.pop(0)

            if match_filtered_identities(x, ids, matcher):
                candidates += ids
            else:
                no_match.append(ids)

        candidates.append(x)

        # Generate the new list of matched subsets
        matched = [candidates] + no_match

    return matched


def _match_with_pandas(filtered, matcher):
    """Find matches in a set using Pandas' library."""

    import pandas

    data = [fl.to_dict() for fl in filtered]

    if not data:
        return []

    df = pandas.DataFrame(data)
    df = df.sort(['uuid'])

    cdfs = []
    criteria = matcher.matching_criteria()

    for c in criteria:
        cdf = df[['id', 'uuid', c]]
        cdf = cdf.dropna(subset=[c])
        cdf = pandas.merge(cdf, cdf, on=c, how='left')
        cdf = cdf[['uuid_x', 'uuid_y']]
        cdfs.append(cdf)

    result = pandas.concat(cdfs)
    result = result.drop_duplicates()
    groups = result.groupby(by=['uuid_x'],
                            as_index=True, sort=True)

    matched = _calculate_matches_closures(groups)

    return matched


def _filter_unique_identities(uidentities, matcher):
    """Filter a set of unique identities.

    This function will use the `matcher` to generate a list
    of `FilteredIdentity` objects. It will return a tuple
    with the list of filtered objects, the unique identities
    not filtered and a table mapping uuids with unique
    identities.
    """
    filtered = []
    no_filtered = []
    uuids = {}

    for uidentity in uidentities:
        n = len(filtered)
        filtered += matcher.filter(uidentity)

        if len(filtered) > n:
            uuids[uidentity.uuid] = uidentity
        else:
            no_filtered.append([uidentity])

    return filtered, no_filtered, uuids


def _build_matches(matches, uuids, no_filtered, fastmode=False):
    """Build a list with matching subsets"""

    result = []

    for m in matches:
        mk = m[0].uuid if not fastmode else m[0]
        subset = [uuids[mk]]

        for id_ in m[1:]:
            uk = id_.uuid if not fastmode else id_
            u = uuids[uk]

            if u not in subset:
                subset.append(u)

        result.append(subset)

    result += no_filtered
    result.sort(key=len, reverse=True)

    return result


def _calculate_matches_closures(groups):
    """Find the transitive closure of each unique identity.

    This function uses a BFS algorithm to build set of matches.
    For instance, given a list of matched unique identities like
    A = {A, B}; B = {B,A,C}, C = {C,} and D = {D,} the output
    will be A = {A, B, C} and D = {D,}.

    :param groups: groups of unique identities
    """
    matches = []

    ns = sorted(groups.groups.keys())

    while ns:
        n = ns.pop(0)
        visited = [n]
        vs = [v for v in groups.get_group(n)['uuid_y']]

        while vs:
           v = vs.pop(0)

           if v in visited:
               continue

           nvs = [nv for nv in groups.get_group(v)['uuid_y']]
           vs += nvs
           visited.append(v)

           try:
               ns.remove(v)
           except:
               pass

        matches.append(visited)

    return matches
