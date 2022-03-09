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

import logging
import re

from ..db.model import UniqueIdentity
from ..matcher import IdentityMatcher, FilteredIdentity


EMAIL_ADDRESS_REGEX = r"^(?P<email>[^\s@]+@[^\s@.]+\.[^\s@]+)$"

logger = logging.getLogger(__name__)


class EmailIdentity(FilteredIdentity):
    """Class to stored EmailName filtered identities"""

    def __init__(self, id, uuid, email):
        super(EmailIdentity, self).__init__(id, uuid)
        self.email = email

    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'email': self.email
        }


class EmailMatcher(IdentityMatcher):
    """
    Simple unique identities matcher.

    This matcher only produces a positive result when two identities
    from each unique identity share the same email address. When `strict`
    is set, the email must be well-formed. It also returns a positive
    match when the uuid on both unique identities is equal.

    :param blacklist: list of entries to ignore during the matching process
    :param sources: only match the identities from these sources
    :param strict: strict matching with well-formed email addresses
    """
    def __init__(self, blacklist=None, sources=None, strict=True):
        super(EmailMatcher, self).__init__(blacklist=blacklist,
                                           sources=sources,
                                           strict=strict)
        self.email_pattern = re.compile(EMAIL_ADDRESS_REGEX)

    def match(self, a, b):
        """Determine if two unique identities are the same.

        This method compares the email addresses of each identity to check
        if the given unique identities are the same. When the given unique
        identities are the same object or share the same UUID, this will
        also produce a positive match.

        Identities which their email addresses are in the blacklist will be
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

        filtered_a = self.filter(a)
        filtered_b = self.filter(b)

        for fa in filtered_a:
            for fb in filtered_b:
                if self.match_filtered_identities(fa, fb):
                    return True
        return False

    def match_filtered_identities(self, fa, fb):
        """Determine if two filtered identities are the same.

        The method compares the email addresses of each filtered identity
        to check if they are the same. When the given filtered identities
        are the same object or share the same UUID, this will also
        produce a positive match.

        Identities which their email addresses are in the blacklist will be
        ignored and the result of the comparison will be false.

        :param fa: filtered identity to match
        :param fb: filtered identity to match

        :returns: True when both filtered identities are likely to be the same.
            Otherwise, returns False.

        :raises ValueError: when any of the given filtered identities is not
            an instance of EmailIdentity class.
        """
        if not isinstance(fa, EmailIdentity):
            raise ValueError("<fa> is not an instance of UniqueIdentity")
        if not isinstance(fb, EmailIdentity):
            raise ValueError("<fb> is not an instance of EmailNameIdentity")

        if fa.uuid and fb.uuid and fa.uuid == fb.uuid:
            return True

        if self._check_blacklist(fa):
            return False

        # Compare email addresses first
        if fa.email and fa.email == fb.email:
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
            email = None

            if self.sources and id_.source.lower() not in self.sources:
                continue

            if self._check_blacklist(id_):
                continue

            if self.strict:
                if self._check_email(id_.email):
                    email = id_.email.lower()
            else:
                email = id_.email.lower() if id_.email else None

            if email:
                fid = EmailIdentity(id_.id, id_.uuid, email)
                filtered.append(fid)

        return filtered

    @staticmethod
    def matching_criteria():
        """List of keys used during the matching phase.

        returns: a list of keys
        """
        return ['email']

    def _check_blacklist(self, id_):
        if not id_.email:
            return False

        blacklisted = id_.email.lower() in self.blacklist

        return blacklisted

    def _check_email(self, email):
        if not email:
            return False

        checked = self.email_pattern.match(email) is not None

        return checked
