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

from distutils.core import setup


setup(name="sortinghat",
      version="0.0.1",
      author="Bitergia",
      author_email="metrics-grimoire@lists.libresoft.es",
      url="https://github.com/MetricsGrimoire/sortinghat",
      packages=['sortinghat', 'sortinghat.db', 'sortinghat.cmd', 'sortinghat.matching',
                'sortinghat.parsing', 'sortinghat.templates', 'sortinghat.data'],
      package_data={'sortinghat.templates' : ['*.tmpl'],
                    'sortinghat.data' : ['*'],},
      scripts=["bin/sortinghat", "bin/mg2sh", "bin/sh2mg"],
      requires=['sqlalchemy', 'jinja2'])
