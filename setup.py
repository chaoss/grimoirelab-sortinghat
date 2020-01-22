#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2019 Bitergia
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

import codecs
import os.path
import re
import sys
import unittest

# Always prefer setuptools over distutils
from setuptools import setup
from setuptools.command.test import test as TestClass

here = os.path.abspath(os.path.dirname(__file__))
readme_md = os.path.join(here, 'README.md')
version_py = os.path.join(here, 'sortinghat', '_version.py')

# Get the package description from the README.md file
with codecs.open(readme_md, encoding='utf-8') as f:
    long_description = f.read()

with codecs.open(version_py, 'r', encoding='utf-8') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)


class TestCommand(TestClass):

    user_options = []
    __dir__ = os.path.dirname(os.path.realpath(__file__))

    def initialize_options(self):
        super().initialize_options()
        sys.path.insert(0, os.path.join(self.__dir__, 'tests'))

    def run_tests(self):
        test_suite = unittest.TestLoader().discover('.', pattern='test*.py')
        result = unittest.TextTestRunner(buffer=True).run(test_suite)
        sys.exit(not result.wasSuccessful())


cmdclass = {'test': TestCommand}

setup(name="sortinghat",
      description="A tool to manage identities",
      long_description=long_description,
      long_description_content_type='text/markdown',
      url="https://github.com/grimoirelab/sortinghat",
      version=version,
      author="Bitergia",
      author_email="sduenas@bitergia.com",
      license="GPLv3",
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: '
        'GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4'],
      keywords="development repositories analytics",
      packages=['sortinghat', 'sortinghat.db', 'sortinghat.cmd',
                'sortinghat.matching', 'sortinghat.parsing',
                'sortinghat.templates', 'sortinghat.data'],
      package_data={'sortinghat.templates': ['*.tmpl'],
                    'sortinghat.data': ['*'],
                    },
      scripts=[
        "bin/sortinghat",
        "bin/mg2sh",
        "bin/sh2mg",
        "misc/eclipse2sh",
        "misc/gitdm2sh",
        "misc/grimoirelab2sh",
        "misc/mailmap2sh",
        "misc/mozilla2sh",
        "misc/stackalytics2sh"
      ],
      setup_requires=[
        'wheel',
        'pandoc'],
      tests_require=[
        'httpretty>=0.9.5'
      ],
      install_requires=[
        'PyMySQL>=0.7.0',
        'sqlalchemy>=1.2',
        'jinja2',
        'python-dateutil>=2.6.0',
        'pandas>=0.22.0,<=0.25.3',
        'pyyaml>=3.12',
        'requests>=2.9',
        'urllib3>=1.22'
      ],
      cmdclass=cmdclass,
      zip_safe=False
      )
