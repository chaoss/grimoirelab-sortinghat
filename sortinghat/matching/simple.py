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

import re

from sortinghat.db.model import UniqueIdentity
from sortinghat.matcher import IdentityMatcher


EMAIL_ADDRESS_REGEX = ur"^(?P<email>[^\s@]+@[^\s@.]+\.[^\s@]+)$"


class SimpleMatcher(IdentityMatcher):
    """
    Simple unique identities matcher.

    This matcher only produces a positive result when two identities
    from each unique identity share the same email address. It also
    returns a positive match when the uuid on both unique identities is equal.
    """
    def __init__(self):
        super(SimpleMatcher, self).__init__()
        self.email_pattern = re.compile(EMAIL_ADDRESS_REGEX)

    def match(self, a, b):
        """Determine if two unique identities are the same.

        This method compares the email addresses of each identity to check
        if the given unique identities are the same. When the given unique
        identities are the same object or share the same uuid, this will
        also produce a positive match.

        :param a: unique identity to match
        :param b: unique identity to match

        :returns: True when both unique identities are likely to be the same.
            Otherwise, returns False.

        :raises ValueError: when any of the given unique identities is not
            an instance of UniqueIdentity class
        """
        if not isinstance(a, UniqueIdentity):
            raise ValueError('<a> is not an instance of UniqueIdentity')
        if not isinstance(b, UniqueIdentity):
            raise ValueError('<b> is not an instance of UniqueIdentity')

        if a.uuid == b.uuid:
            return True

        emails_a = self._filter_emails(a.identities)
        emails_b = self._filter_emails(b.identities)

        for email in emails_a:
            if email in emails_b:
                return True
        return False

    def _filter_emails(self, ids):
        return [id.email.lower() for id in ids \
                if self._check_email(id.email)]

    def _check_email(self, email):
        if not email:
            return False
        return self.email_pattern.match(email) is not None
