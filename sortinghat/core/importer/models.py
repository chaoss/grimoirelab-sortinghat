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


class Identity:
    def __init__(self, source, name=None, email=None, username=None, uuid=None):
        self.source = source
        self.name = name
        self.username = username
        self.email = email
        self.uuid = uuid


class Individual:
    def __init__(self, uuid=None, profile=None):
        self.uuid = uuid
        self.identities = []
        self.enrollments = []
        self.profile = profile
        self.enrollments = []


class Profile:
    def __init__(self, name=None, email=None, gender=None, gender_acc=None,
                 is_bot=False, country_code=None):
        self.name = name
        self.email = email
        self.gender = gender
        self.gender_acc = gender_acc
        self.is_bot = is_bot
        self.country_code = country_code


class Enrollment:
    def __init__(self, organization, start=None, end=None):
        self.start = start
        self.end = end
        self.organization = organization


class Organization:
    def __init__(self, name=None, type=None, parent_org=None):
        self.name = name
        self.type = type
        self.domains = []
        self.parent_org = parent_org


class Domain:
    def __init__(self, domain, is_top_domain=False):
        self.domain = domain
        self.is_top_domain = is_top_domain


class RecommenderExclusionTerm:
    def __init__(self, term):
        self.term = term
