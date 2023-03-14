#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Bitergia
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
#     Jose Javier Merchante <jjmerchante@bitergia.com>
#

from django.test import TestCase

from sortinghat.core.importer.backend import IdentitiesImporter
from sortinghat.core.importer.utils import find_backends

from . import mocked_package
from .mocked_package.backend_a import BackendA
from .mocked_package.nested_package.nested_backend_b import BackendB
from .mocked_package.nested_package.nested_backend_c import BackendC
from .mocked_package.nested_package.nested_not_backend import BackendZ


class TestFindBackends(TestCase):
    """Unit tests for find_backends function"""

    def test_find_backends(self):
        """Check that the backends are correctly found"""

        backends = find_backends(mocked_package, IdentitiesImporter)

        expected_backends = {
            'backend_a': BackendA,
            'nested_backend_b': BackendB,
            'nested_backend_c': BackendC
        }
        self.assertDictEqual(backends, expected_backends)

    def test_find_backends_in_module(self):
        """Check that the backends and their commands are correctly found in a submodule"""

        backends = find_backends(mocked_package.nested_package, IdentitiesImporter)

        expected_backends = {
            'nested_backend_b': BackendB,
            'nested_backend_c': BackendC
        }
        self.assertDictEqual(backends, expected_backends)

    def test_find_different_subclass_module(self):
        """Check that all classes are found under a specific module"""

        backends = find_backends(mocked_package, object)

        expected_backends = {
            'nested_not_backend': BackendZ
        }
        self.assertDictEqual(backends, expected_backends)
