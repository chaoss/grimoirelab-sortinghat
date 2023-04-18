
from django.test.runner import DiscoverRunner
from unittest.suite import TestSuite


def from_tenant_module(test):
    return test.__module__.startswith('tests.tenants')


class SkipMultiTenantTestRunner(DiscoverRunner):
    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        suite = super().build_suite(test_labels=test_labels, extra_tests=extra_tests, **kwargs)
        tests = [t for t in suite._tests if not from_tenant_module(t)]
        return TestSuite(tests=tests)


class OnlyMultiTenantTestRunner(DiscoverRunner):
    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        suite = super().build_suite(test_labels=test_labels, extra_tests=extra_tests, **kwargs)
        tests = [t for t in suite._tests if from_tenant_module(t)]
        return TestSuite(tests=tests)
