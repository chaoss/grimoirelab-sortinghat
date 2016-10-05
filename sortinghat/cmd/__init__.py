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

from __future__ import absolute_import
from __future__ import unicode_literals

from .add import Add
from .affiliate import Affiliate
from .autoprofile import AutoProfile
from .blacklist import Blacklist
from .config import Config
from .countries import Countries
from .enroll import Enroll
from .export import Export
from .init import Init
from .load import Load
from .log import Log
from .merge import Merge
from .move import Move
from .organizations import Organizations
from .profile import Profile
from .remove import Remove
from .show import Show
from .unify import Unify
from .withdraw import Withdraw


SORTINGHAT_COMMANDS = {
                       'add'         : Add,
                       'affiliate'   : Affiliate,
                       'autoprofile' : AutoProfile,
                       'blacklist'   : Blacklist,
                       'config'      : Config,
                       'countries'   : Countries,
                       'enroll'      : Enroll,
                       'export'      : Export,
                       'init'        : Init,
                       'load'        : Load,
                       'log'         : Log,
                       'merge'       : Merge,
                       'mv'          : Move,
                       'orgs'        : Organizations,
                       'profile'     : Profile,
                       'rm'          : Remove,
                       'show'        : Show,
                       'unify'       : Unify,
                       'withdraw'    : Withdraw,
                       }
