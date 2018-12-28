# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2018 Bitergia
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

import graphene
from graphene_django.types import DjangoObjectType

from .models import (Organization,
                     Domain,
                     Country,
                     UniqueIdentity,
                     Identity,
                     Profile,
                     Enrollment)


class OrganizationType(DjangoObjectType):
    class Meta:
        model = Organization


class DomainType(DjangoObjectType):
    class Meta:
        model = Domain


class CountryType(DjangoObjectType):
    class Meta:
        model = Country


class UniqueIdentityType(DjangoObjectType):
    class Meta:
        model = UniqueIdentity


class IdentityType(DjangoObjectType):
    class Meta:
        model = Identity


class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile


class EnrollmentType(DjangoObjectType):
    class Meta:
        model = Enrollment


class SortingHatQuery:
    organizations = graphene.List(OrganizationType)
    uidentities = graphene.List(UniqueIdentityType)

    def resolve_organizations(self, info, **kwargs):
        return Organization.objects.order_by('name')

    def resolve_uidentities(self, info, **kwargs):
        return UniqueIdentity.objects.order_by('uuid')
