# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2016 Bitergia
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

import re

from ..db.model import UniqueIdentity
from ..matcher import IdentityMatcher, FilteredIdentity


class GitHubUsernameIdentity(FilteredIdentity):
    """Class to stored GitHub filtered identities"""

    def __init__(self, id, uuid, username, source):
        super(GitHubUsernameIdentity, self).__init__(id, uuid)
        self.username = username
        self.source = source

    def to_dict(self):
        return {
                'id'    : self.id,
                'uuid'  : self.uuid,
                'username' : self.username,
                'source'  : self.source
               }


class GitHubMatcher(IdentityMatcher):
    """Matcher of GitHub identities.

    This matcher produces a positive result when on of these cases
    is true (this means OR condition) on a pair of identities:

       - the UUID on both identities is equal
       - identities share the same username address and both belong to
         a 'GitHub' source; thouse sources start with the keyword 'github'

    :param blacklist: list of entries to ignore during the matching process
    """
    def __init__(self, blacklist=[]):
        super(GitHubMatcher, self).__init__(blacklist=blacklist)

    def match(self, a, b):
        """Determine if two unique identities are the same.

        This method compares the username and the source of each
        identity to check if the given unique identities are the
        same. Identities sources have to start with 'github' keyword
        (uppercase or lowercase).When the given unique identities are
        the same object or share the same UUID, this will also produce
        a positive match.

        Identities which their usernames are in the blacklist will be
        ignored during the matching.

        :param a: unique identity to match
        :param b: unique identity to match

        :returns: True when both unique identities are likely to be the same.
            Otherwise, returns False.

        :raises ValueError: when any of the given unique identities is not
            an instance of UniqueIdentity class
        """
        if not isinstance(a, UniqueIdentity):
            raise ValueError("<a> is not an instance of UniqueIdentity")
        if not isinstance(b, UniqueIdentity):
            raise ValueError("<b> is not an instance of UniqueIdentity")

        if a.uuid and b.uuid and a.uuid == b.uuid:
            return True

        filtered_a = self.filter(a)
        filtered_b = self.filter(b)

        for fa in filtered_a:
            for fb in filtered_b:
                if self.match_filtered_identities(fa, fb):
                    return True
        return False

    def match_filtered_identities(self, fa, fb):
        """Determine if two filtered identities are the same.

        This method compares the username and the source of each
        identity to check if the given unique identities are the
        same. Identities sources have to start with 'github' keyword
        (uppercase or lowercase). When the given filtered identities
        are the same object or share the same UUID, this will also
        produce a positive match.

        Identities which their usernames are in the blacklist will be
        ignored and the result of the comparison will be false.

        :param fa: filtered identity to match
        :param fb: filtered identity to match

        :returns: True when both filtered identities are likely to be the same.
            Otherwise, returns False.

        :raises ValueError: when any of the given filtered identities is not
            an instance of EmailNameIdentity class.
        """
        if not isinstance(fa, GitHubUsernameIdentity):
            raise ValueError("<fa> is not an instance of GitHubUsernameIdentity")
        if not isinstance(fb, GitHubUsernameIdentity):
            raise ValueError("<fb> is not an instance of GitHubUsernameIdentity")

        if fa.uuid and fb.uuid and fa.uuid == fb.uuid:
            return True

        if self._check_blacklist(fa):
            return False

        # Compare username
        return fa.username and (fa.username == fb.username)

    def filter(self, u):
        """Filter the valid identities for this matcher.

        :param u: unique identity which stores the identities to filter

        :returns: a list of identities valid to work with this matcher.

        :raises ValueError: when the unique identity is not an instance
            of UniqueIdentity class
        """
        if not isinstance(u, UniqueIdentity):
            raise ValueError("<u> is not an instance of UniqueIdentity")

        filtered = []

        for id_ in u.identities:
            if self._check_blacklist(id_):
                continue

            source = id_.source.lower()

            if source.startswith('github'):
                fid = GitHubUsernameIdentity(id_.id, id_.uuid,
                                             id_.username, id_.source)
                filtered.append(fid)

        return filtered

    @staticmethod
    def matching_criteria():
        """List of keys used during the matching phase.

        returns: a list of keys
        """
        return ['username']

    def _check_blacklist(self, id_):
        if self._check_value_in_blacklist(id_.username):
            return True

    def _check_value_in_blacklist(self, value):
        return value and value.lower() in self.blacklist
