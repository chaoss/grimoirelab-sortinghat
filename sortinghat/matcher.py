# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Bitergia
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

from sortinghat.exceptions import MatcherNotSupportedError


class IdentityMatcher(object):
    """Abstract class to determine whether two unique identities match"""

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def match(self, a, b):
        """Abstract method used to determine if both unique identities are the same.

        :param a: unique identity to match
        :param b: unique identity to match

        :returns: True when both unique identities are likely to be the same.
        """
        raise NotImplementedError


def create_identity_matcher(matcher='default'):
    """Create an identity matcher of the given type.

    Factory function that creates an identity matcher object of the type
    defined on 'matcher' parameter.

    :param matcher: type of the matcher

    :returns: a identity matcher object of the given type

    :raises MatcherNotSupportedError: when the given matcher type is not
        supported or available
    """
    import sortinghat.matching as matching

    if matcher not in matching.SORTINGHAT_IDENTITIES_MATCHERS:
        raise MatcherNotSupportedError(matcher=str(matcher))

    klass = matching.SORTINGHAT_IDENTITIES_MATCHERS[matcher]

    return klass()
