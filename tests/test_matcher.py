#!/usr/bin/env python
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

import sys
import unittest

if not '..' in sys.path:
    sys.path.insert(0, '..')

from sortinghat.exceptions import MatcherNotSupportedError
from sortinghat.matcher import IdentityMatcher, create_identity_matcher
from sortinghat.matching import SimpleMatcher


class TestCreateIdentityMatcher(unittest.TestCase):

    def test_identity_matcher_instance(self):
        """Test if the factory function returns an identity matcher instance"""

        matcher = create_identity_matcher('default')
        self.assertIsInstance(matcher, IdentityMatcher)

        matcher = create_identity_matcher('simple')
        self.assertIsInstance(matcher, SimpleMatcher)

    def test_not_supported_matcher(self):
        """Check if an exception is raised when the given matcher type is not supported"""

        self.assertRaises(MatcherNotSupportedError,
                          create_identity_matcher, 'custom')


if __name__ == "__main__":
    unittest.main()