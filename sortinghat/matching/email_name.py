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
NAME_REGEX = ur"^\w+\s\w+"


class EmailNameMatcher(IdentityMatcher):
    """
    Complex unique identities matcher.

    This matcher produces a positive result when one of these cases
    is true (this means OR condition) on a pair of identities:

       - the UUID on both identities is equal
       - identities share the same email address
       - name field is composed by "firstname lastname" and both are
         equal; i.e: "John Smith" and "J Smith Rae" are valid name fields;
         "jonhsmith" are "j.smith" not valid
    """
    def __init__(self):
        super(EmailNameMatcher, self).__init__()
        self.email_pattern = re.compile(EMAIL_ADDRESS_REGEX)
        self.name_pattern = re.compile(NAME_REGEX)

    def match(self, a, b):
        """Determine if two unique identities are the same.

        This method compares the email addresses or the names of each
        identity to check if the given unique identities are the same.
        When the given unique identities are the same object or share
        the same UUID, this will also produce a positive match.

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

        # Compare email addresses first
        emails_a = self._filter_emails(a.identities)
        emails_b = self._filter_emails(b.identities)

        for email in emails_a:
            if email in emails_b:
                return True

        # No match yet, so compare names
        names_a = self._filter_names(a.identities)
        names_b = self._filter_names(b.identities)

        for name in names_a:
            if name in names_b:
                return True

        return False

    def _filter_emails(self, ids):
        return [id_.email.lower() for id_ in ids \
                if self._check_pattern(self.email_pattern, id_.email)]

    def _filter_names(self, ids):
        return [id_.name.lower() for id_ in ids \
                if self._check_pattern(self.name_pattern, id_.name)]

    def _check_pattern(self, pattern, value):
        if not value:
            return False
        return pattern.match(value) is not None
