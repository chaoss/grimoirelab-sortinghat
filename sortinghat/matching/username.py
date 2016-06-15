# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Bitergia
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
#     Alvaro del Castillo <acs@bitergia.com>
#

from __future__ import absolute_import
from __future__ import unicode_literals

import re

from ..db.model import UniqueIdentity
from ..matcher import IdentityMatcher, FilteredIdentity


class UsernameIdentity(FilteredIdentity):
    """Class to stored Username filtered identities"""

    def __init__(self, id, uuid, username):
        super(UsernameIdentity, self).__init__(id, uuid)
        self.username = username

    def to_dict(self):
        return {
                'id'    : self.id,
                'uuid'  : self.uuid,
                'username' : self.username
               }


class UsernameMatcher(IdentityMatcher):
    """
    Simple unique identities matcher.

    This matcher only produces a positive result when two identities
    from each unique identity share the same username. It also
    returns a positive match when the uuid on both unique identities is equal.

    :param blacklist: list of entries to ignore during the matching process
    """
    def __init__(self, blacklist=[]):
        super(UsernameMatcher, self).__init__(blacklist=blacklist)

    def match(self, a, b):
        """Determine if two unique identities are the same.

        This method compares the username of each identity to check
        if the given unique identities are the same. When the given unique
        identities are the same object or share the same UUID, this will
        also produce a positive match.

        Identities which their username are in the blacklist will be
        ignored and the result of the comparison will be false.

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

        usernames_a = self._filter_usernames(a.identities)
        usernames_b = self._filter_usernames(b.identities)

        for username in usernames_a:
            if username in usernames_b:
                return True
        return False

    def match_filtered_identities(self, fa, fb):
        """Determine if two filtered identities are the same.

        The method compares the username of each filtered identity
        to check if they are the same. When the given filtered identities
        are the same object or share the same UUID, this will also
        produce a positive match.

        Identities which their username are in the blacklist will be
        ignored and the result of the comparison will be false.

        :param fa: filtered identity to match
        :param fb: filtered identity to match

        :returns: True when both filtered identities are likely to be the same.
            Otherwise, returns False.

        :raises ValueError: when any of the given filtered identities is not
            an instance of UsernameIdentity class.
        """
        if not isinstance(fa, UsernameIdentity):
            raise ValueError("<fa> is not an instance of UsernameIdentity")
        if not isinstance(fb, UsernameIdentity):
            raise ValueError("<fb> is not an instance of UsernameIdentity")

        if fa.uuid and fb.uuid and fa.uuid == fb.uuid:
            return True

        if fa.username in self.blacklist:
            return False

        # Compare username first
        if fa.username and fa.username == fb.username:
            return True

        return False

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
            username = None

            if self._check_username(id_.username):
                username = id_.username.lower()

            if username:
                fid = UsernameIdentity(id_.id, id_.uuid, username)
                filtered.append(fid)

        return filtered

    @staticmethod
    def matching_criteria():
        """List of keys used during the matching phase.

        returns: a list of keys
        """
        return ['username']

    def _filter_usernames(self, ids):
        return [id_.username.lower() for id_ in ids \
                if self._check_username(id_.username)]

    def _check_username(self, username):
        if not username:
            return False
        elif username.lower() in self.blacklist:
            return False
        return True
