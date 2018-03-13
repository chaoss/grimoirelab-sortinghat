#!/usr/bin/env python
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

import codecs
import os
import re
import sys
import unittest

# Always prefer setuptools over distutils
from setuptools import setup, Command

here = os.path.abspath(os.path.dirname(__file__))
readme_md = os.path.join(here, 'README.md')
version_py = os.path.join(here, 'sortinghat', '_version.py')

# Pypi wants the description to be in reStrcuturedText, but
# we have it in Markdown. So, let's convert formats.
# Set up thinkgs so that if pypandoc is not installed, it
# just issues a warning.
try:
    import pypandoc
    long_description = pypandoc.convert(readme_md, 'rst')
except (IOError, ImportError):
    print("Warning: pypandoc module not found, or pandoc not installed. "
          + "Using md instead of rst")
    with codecs.open(readme_md, encoding='utf-8') as f:
        long_description = f.read()

with codecs.open(version_py, 'r', encoding='utf-8') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)


class TestCommand(Command):

    user_options = []
    __dir__ = os.path.dirname(os.path.realpath(__file__))

    def initialize_options(self):
        os.chdir(os.path.join(self.__dir__, 'tests'))

    def finalize_options(self):
        pass

    def run(self):
        test_suite = unittest.TestLoader().discover('.', pattern='test*.py')
        result = unittest.TextTestRunner(buffer=True).run(test_suite)
        sys.exit(not result.wasSuccessful())


cmdclass = {'test': TestCommand}

setup(name="sortinghat",
      description="A tool to manage identities",
      long_description=long_description,
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
      install_requires=[
        'PyMySQL>=0.7.0',
        'sqlalchemy>=1.1.15',
        'jinja2',
        'python-dateutil>=2.6.0',
        'pandas>=0.18.1',
        'pyyaml>=3.12',
        'requests>=2.9',
        'urllib3>=1.22'
      ],
      cmdclass=cmdclass,
      zip_safe=False
      )
