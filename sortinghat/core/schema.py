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

import graphene
from graphene_django.types import DjangoObjectType

from .api import (add_identity,
                  delete_identity,
                  update_profile)
from .db import (add_organization,
                 delete_organization,
                 add_domain,
                 delete_domain)
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


class ProfileInputType(graphene.InputObjectType):
    name = graphene.String(required=False)
    email = graphene.String(required=False)
    gender = graphene.String(required=False)
    gender_acc = graphene.Int(required=False)
    is_bot = graphene.Boolean(required=False)
    country_code = graphene.String(required=False)


class AddOrganization(graphene.Mutation):
    class Arguments:
        name = graphene.String()

    organization = graphene.Field(lambda: OrganizationType)

    def mutate(self, info, name):
        org = add_organization(name)

        return AddOrganization(
            organization=org
        )


class DeleteOrganization(graphene.Mutation):
    class Arguments:
        name = graphene.String()

    organization = graphene.Field(lambda: OrganizationType)

    def mutate(self, info, name):
        org = Organization.objects.get(name=name)
        delete_organization(org)

        return DeleteOrganization(
            organization=org
        )


class AddDomain(graphene.Mutation):
    class Arguments:
        organization = graphene.String()
        domain = graphene.String()
        is_top_domain = graphene.Boolean()

    domain = graphene.Field(lambda: DomainType)

    def mutate(self, info, organization, domain, is_top_domain=False):
        org = Organization.objects.get(name=organization)
        dom = add_domain(org, domain, is_top_domain=is_top_domain)

        return AddDomain(
            domain=dom
        )


class DeleteDomain(graphene.Mutation):
    class Arguments:
        domain = graphene.String()

    domain = graphene.Field(lambda: DomainType)

    def mutate(self, info, domain):
        dom = Domain.objects.get(domain=domain)
        delete_domain(dom)

        return DeleteDomain(
            domain=dom
        )


class AddIdentity(graphene.Mutation):
    class Arguments:
        source = graphene.String()
        name = graphene.String()
        email = graphene.String()
        username = graphene.String()
        uuid = graphene.String()

    uuid = graphene.Field(lambda: graphene.String)
    uidentity = graphene.Field(lambda: UniqueIdentityType)

    def mutate(self, info, source,
               name=None, email=None, username=None,
               uuid=None):
        identity = add_identity(source,
                                name=name,
                                email=email,
                                username=username,
                                uuid=uuid)
        id_ = identity.id
        uidentity = identity.uidentity

        return AddIdentity(
            uuid=id_,
            uidentity=uidentity
        )


class DeleteIdentity(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()
        unique_identity = graphene.Boolean()

    uuid = graphene.Field(lambda: graphene.String)
    uidentity = graphene.Field(lambda: UniqueIdentityType)

    def mutate(self, info, uuid):
        uidentity = delete_identity(uuid)

        return DeleteIdentity(
            uuid=uuid,
            uidentity=uidentity
        )


class UpdateProfile(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()
        data = ProfileInputType()

    uuid = graphene.Field(lambda: graphene.String)
    uidentity = graphene.Field(lambda: UniqueIdentityType)

    def mutate(self, info, uuid, data):
        uidentity = update_profile(uuid, **data)

        return UpdateProfile(
            uuid=uidentity.uuid,
            uidentity=uidentity
        )


class SortingHatQuery:
    organizations = graphene.List(OrganizationType)
    uidentities = graphene.List(UniqueIdentityType)

    def resolve_organizations(self, info, **kwargs):
        return Organization.objects.order_by('name')

    def resolve_uidentities(self, info, **kwargs):
        return UniqueIdentity.objects.order_by('uuid')


class SortingHatMutation(graphene.ObjectType):
    add_organization = AddOrganization.Field()
    delete_organization = DeleteOrganization.Field()
    add_domain = AddDomain.Field()
    delete_domain = DeleteDomain.Field()
    add_identity = AddIdentity.Field()
    delete_identity = DeleteIdentity.Field()
    update_profile = UpdateProfile.Field()
