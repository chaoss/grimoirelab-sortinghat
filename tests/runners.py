# -*- coding: utf-8 -*-
#
# Copyright (C) Bitergia
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

from django.conf import settings
from django.test.runner import DiscoverRunner
from testcontainers.mysql import MySqlContainer
from unittest.suite import TestSuite


class TestContainersRunner(DiscoverRunner):
    _mysql_container: MySqlContainer = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        db_image = getattr(settings, "TEST_DATABASE_IMAGE", "mariadb:latest")

        self._mysql_container = MySqlContainer(image=db_image,
                                               root_password="root")

    def _setup_container(self):
        self._mysql_container.start()

        for database in settings.DATABASES:
            settings.DATABASES[database]["HOST"] = "127.0.0.1"
            settings.DATABASES[database]["PORT"] = self._mysql_container.get_exposed_port(3306)
            settings.DATABASES[database]["USER"] = "root"
            settings.DATABASES[database]["PASSWORD"] = self._mysql_container.root_password

    def _teardown_container(self):
        self._mysql_container.stop()

    def setup_databases(self, **kwargs):
        self._setup_container()
        return super().setup_databases(**kwargs)

    def teardown_databases(self, old_config, **kwargs):
        super().teardown_databases(old_config, **kwargs)
        self._teardown_container()


def from_tenant_module(test):
    return test.__module__.startswith('tests.tenants')


class SkipMultiTenantTestRunner(TestContainersRunner):
    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        suite = super().build_suite(test_labels=test_labels, extra_tests=extra_tests, **kwargs)
        tests = [t for t in suite._tests if not from_tenant_module(t)]
        return TestSuite(tests=tests)


class OnlyMultiTenantTestRunner(TestContainersRunner):
    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        suite = super().build_suite(test_labels=test_labels, extra_tests=extra_tests, **kwargs)
        tests = [t for t in suite._tests if from_tenant_module(t)]
        return TestSuite(tests=tests)
