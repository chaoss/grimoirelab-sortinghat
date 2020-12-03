# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2020 Bitergia
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
#     Miguel Ángel Fernández <mafesan@bitergia.com>
#

import json
import re

import graphene
import graphql_jwt

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q, Subquery

from django_mysql.models import JSONField

from django_rq import enqueue

from graphene.types.generic import GenericScalar

from graphene_django.converter import convert_django_field
from graphene_django.types import DjangoObjectType

from grimoirelab_toolkit.datetime import (str_to_datetime,
                                          InvalidDateError)

from .api import (add_identity,
                  delete_identity,
                  update_profile,
                  move_identity,
                  lock,
                  unlock,
                  merge,
                  unmerge_identities,
                  add_organization,
                  add_domain,
                  delete_organization,
                  delete_domain,
                  enroll,
                  withdraw)
from .context import SortingHatContext
from .decorators import check_auth
from .errors import InvalidFilterError
from .jobs import (affiliate,
                   unify,
                   find_job,
                   recommend_affiliations,
                   recommend_matches)
from .models import (Organization,
                     Domain,
                     Country,
                     Individual,
                     Identity,
                     Profile,
                     Enrollment,
                     Transaction,
                     Operation)


@convert_django_field.register(JSONField)
def convert_json_field_to_generic_scalar(field, registry=None):
    """Convert the content of a `JSONField` loading it as an object"""

    return OperationArgsType(description=field.help_text, required=not field.null)


def parse_date_filter(filter_value):
    """Extract the filter terms from a date filter

    The accepted formats are controlled by regular expressions
    matching two patterns: a comparison operator (>, >=, <, <=) and a date
    OR a range operator (..) between two dates.

    The accepted date format is ISO 8601, YYYY-MM-DDTHH:MM:SSZ, also
    accepting microseconds and time zone offset (YYYY-MM-DDTHH:MM:SS.ms+HH:HH).

    :param filter_value: String containing the filter value

    :returns: A dictionary including an operator and the datetime values
    """
    # Accepted date format is ISO 8601, YYYY-MM-DDTHH:MM:SSZ (no `Z` is accepted too)
    filter_data = {
        "operator": None,
        "date1": None,
        "date2": None
    }

    iso_date_group = r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|\+\d{2}:\d{2})?)"
    # Filter with a comparison operator (>, >=, <, <=) and a date (e.g. `>=YYYY-MM-DDTHH:MM:SS`)
    oper_comparison = r"^(<=?|>=?)%s$" % iso_date_group
    # Filter with a range operator (..) between two dates
    # (e.g. YYYY-MM-DDTHH:MM:SSZ..YYYY-MM-DDTHH:MM:SSZ)
    range_comparison = r"^%s\.{2}%s$" % (iso_date_group, iso_date_group)

    oper_result = re.match(oper_comparison, filter_value)
    range_result = re.match(range_comparison, filter_value)

    if not oper_result and not range_result:
        raise ValueError('Filter format is not valid')

    if oper_result:
        filter_data['operator'] = oper_result.group(1)
        filter_data['date1'] = str_to_datetime(oper_result.group(2))

    if range_result:
        filter_data['operator'] = '..'
        filter_data['date1'] = str_to_datetime(range_result.group(1))
        filter_data['date2'] = str_to_datetime(range_result.group(4))

        if filter_data['date1'] > filter_data['date2']:
            range_msg = 'Date range is invalid. Upper bound must be greater than the lower bound'
            raise ValueError(range_msg)

    return filter_data


class PaginationType(graphene.ObjectType):
    page = graphene.Int()
    page_size = graphene.Int()
    num_pages = graphene.Int()
    has_next = graphene.Boolean()
    has_prev = graphene.Boolean()
    start_index = graphene.Int()
    end_index = graphene.Int()
    total_results = graphene.Int()


class OperationArgsType(GenericScalar):
    @classmethod
    def serialize(cls, value):
        value = super().serialize(value)
        value = json.loads(value)
        return value


class OperationType(DjangoObjectType):
    class Meta:
        model = Operation


class TransactionType(DjangoObjectType):
    class Meta:
        model = Transaction


class OrganizationType(DjangoObjectType):
    class Meta:
        model = Organization


class DomainType(DjangoObjectType):
    class Meta:
        model = Domain


class CountryType(DjangoObjectType):
    class Meta:
        model = Country


class IndividualType(DjangoObjectType):
    class Meta:
        model = Individual


class IdentityType(DjangoObjectType):
    class Meta:
        model = Identity


class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile


class EnrollmentType(DjangoObjectType):
    class Meta:
        model = Enrollment


class AffiliationRecommendationType(graphene.ObjectType):
    uuid = graphene.String()
    organizations = graphene.List(graphene.String)


class MatchesRecommendationType(graphene.ObjectType):
    uuid = graphene.String()
    matches = graphene.List(graphene.String)


class AffiliationResultType(graphene.ObjectType):
    uuid = graphene.String()
    organizations = graphene.List(graphene.String)


class UnifyResultType(graphene.ObjectType):
    merged = graphene.List(graphene.String)


class JobResultType(graphene.Union):
    class Meta:
        types = (AffiliationResultType,
                 AffiliationRecommendationType,
                 MatchesRecommendationType,
                 UnifyResultType)


class JobType(graphene.ObjectType):
    job_id = graphene.String()
    job_type = graphene.String()
    status = graphene.String()
    result = graphene.List(JobResultType)
    errors = graphene.List(graphene.String)


class ProfileInputType(graphene.InputObjectType):
    name = graphene.String(required=False)
    email = graphene.String(required=False)
    gender = graphene.String(required=False)
    gender_acc = graphene.Int(required=False)
    is_bot = graphene.Boolean(required=False)
    country_code = graphene.String(required=False)


class CountryFilterType(graphene.InputObjectType):
    code = graphene.String(required=False)
    term = graphene.String(required=False)


class OrganizationFilterType(graphene.InputObjectType):
    name = graphene.String(required=False)


class IdentityFilterType(graphene.InputObjectType):
    uuid = graphene.String(required=False)
    term = graphene.String(required=False)
    is_locked = graphene.Boolean(required=False)
    last_updated = graphene.String(
        required=False,
        description='Filter with a comparison operator (>, >=, <, <=) and a date OR with a range operator (..) between\
                     two dates, following ISO-8601 format. Examples:\n* `>=2020-10-12T09:35:06.13045+01:00` \
                     \n * `2020-10-12T00:00:00..2020-11-22T00:00:00`.'
    )


class TransactionFilterType(graphene.InputObjectType):
    tuid = graphene.String(required=False)
    name = graphene.String(required=False)
    is_closed = graphene.Boolean(required=False)
    from_date = graphene.DateTime(required=False)
    to_date = graphene.DateTime(required=False)
    authored_by = graphene.String(required=False)


class OperationFilterType(graphene.InputObjectType):
    ouid = graphene.String(required=False)
    op_type = graphene.String(required=False)
    entity_type = graphene.String(required=False)
    target = graphene.String(required=False)
    from_date = graphene.DateTime(required=False)
    to_date = graphene.DateTime(required=False)


class AbstractPaginatedType(graphene.ObjectType):

    @classmethod
    def create_paginated_result(cls, query, page=1,
                                page_size=settings.DEFAULT_GRAPHQL_PAGE_SIZE):
        paginator = Paginator(query, page_size)
        result = paginator.page(page)

        entities = result.object_list

        page_info = PaginationType(
            page=result.number,
            page_size=page_size,
            num_pages=paginator.num_pages,
            has_next=result.has_next(),
            has_prev=result.has_previous(),
            start_index=result.start_index(),
            end_index=result.end_index(),
            total_results=len(query)
        )

        return cls(entities=entities, page_info=page_info)


class CountryPaginatedType(AbstractPaginatedType):
    entities = graphene.List(CountryType)
    page_info = graphene.Field(PaginationType)


class OrganizationPaginatedType(AbstractPaginatedType):
    entities = graphene.List(OrganizationType)
    page_info = graphene.Field(PaginationType)


class IdentityPaginatedType(AbstractPaginatedType):
    entities = graphene.List(IndividualType)
    page_info = graphene.Field(PaginationType)


class TransactionPaginatedType(AbstractPaginatedType):
    entities = graphene.List(TransactionType)
    page_info = graphene.Field(PaginationType)


class OperationPaginatedType(AbstractPaginatedType):
    entities = graphene.List(OperationType)
    page_info = graphene.Field(PaginationType)


class AddOrganization(graphene.Mutation):
    class Arguments:
        name = graphene.String()

    organization = graphene.Field(lambda: OrganizationType)

    @check_auth
    def mutate(self, info, name):
        user = info.context.user
        ctx = SortingHatContext(user)

        org = add_organization(ctx, name)

        return AddOrganization(
            organization=org
        )


class DeleteOrganization(graphene.Mutation):
    class Arguments:
        name = graphene.String()

    organization = graphene.Field(lambda: OrganizationType)

    @check_auth
    def mutate(self, info, name):
        user = info.context.user
        ctx = SortingHatContext(user)

        org = delete_organization(ctx, name)

        return DeleteOrganization(
            organization=org
        )


class AddDomain(graphene.Mutation):
    class Arguments:
        organization = graphene.String()
        domain = graphene.String()
        is_top_domain = graphene.Boolean()

    domain = graphene.Field(lambda: DomainType)

    @check_auth
    def mutate(self, info, organization, domain, is_top_domain=False):
        user = info.context.user
        ctx = SortingHatContext(user)

        dom = add_domain(ctx,
                         organization,
                         domain,
                         is_top_domain=is_top_domain)

        return AddDomain(
            domain=dom
        )


class DeleteDomain(graphene.Mutation):
    class Arguments:
        domain = graphene.String()

    domain = graphene.Field(lambda: DomainType)

    @check_auth
    def mutate(self, info, domain):
        user = info.context.user
        ctx = SortingHatContext(user)

        dom = delete_domain(ctx, domain)

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
    individual = graphene.Field(lambda: IndividualType)

    @check_auth
    def mutate(self, info, source,
               name=None, email=None, username=None,
               uuid=None):
        user = info.context.user
        ctx = SortingHatContext(user)

        identity = add_identity(ctx,
                                source,
                                name=name,
                                email=email,
                                username=username,
                                uuid=uuid)
        individual = identity.individual

        return AddIdentity(
            uuid=identity.uuid,
            individual=individual
        )


class DeleteIdentity(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()
        delete_individual = graphene.Boolean()

    uuid = graphene.Field(lambda: graphene.String)
    individual = graphene.Field(lambda: IndividualType)

    @check_auth
    def mutate(self, info, uuid):
        user = info.context.user
        ctx = SortingHatContext(user)

        individual = delete_identity(ctx, uuid)

        return DeleteIdentity(
            uuid=uuid,
            individual=individual
        )


class Lock(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()

    uuid = graphene.Field(lambda: graphene.String)
    individual = graphene.Field(lambda: IndividualType)

    @check_auth
    def mutate(self, info, uuid):
        user = info.context.user
        ctx = SortingHatContext(user)

        individual = lock(ctx, uuid)

        return Lock(
            uuid=uuid,
            individual=individual
        )


class Unlock(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()

    uuid = graphene.Field(lambda: graphene.String)
    individual = graphene.Field(lambda: IndividualType)

    @check_auth
    def mutate(self, info, uuid):
        user = info.context.user
        ctx = SortingHatContext(user)

        individual = unlock(ctx, uuid)

        return Unlock(
            uuid=uuid,
            individual=individual
        )


class UpdateProfile(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()
        data = ProfileInputType()

    uuid = graphene.Field(lambda: graphene.String)
    individual = graphene.Field(lambda: IndividualType)

    @check_auth
    def mutate(self, info, uuid, data):
        user = info.context.user
        ctx = SortingHatContext(user)

        individual = update_profile(ctx, uuid, **data)

        return UpdateProfile(
            uuid=individual.mk,
            individual=individual
        )


class MoveIdentity(graphene.Mutation):
    class Arguments:
        from_uuid = graphene.String()
        to_uuid = graphene.String()

    uuid = graphene.Field(lambda: graphene.String)
    individual = graphene.Field(lambda: IndividualType)

    @check_auth
    def mutate(self, info, from_uuid, to_uuid):
        user = info.context.user
        ctx = SortingHatContext(user)

        individual = move_identity(ctx, from_uuid, to_uuid)

        return MoveIdentity(
            uuid=individual.mk,
            individual=individual
        )


class Merge(graphene.Mutation):
    class Arguments:
        from_uuids = graphene.List(graphene.String)
        to_uuid = graphene.String()

    uuid = graphene.Field(lambda: graphene.String)
    individual = graphene.Field(lambda: IndividualType)

    @check_auth
    def mutate(self, info, from_uuids, to_uuid):
        user = info.context.user
        ctx = SortingHatContext(user)

        individual = merge(ctx, from_uuids, to_uuid)

        return Merge(
            uuid=individual.mk,
            individual=individual
        )


class UnmergeIdentities(graphene.Mutation):
    class Arguments:
        uuids = graphene.List(graphene.String)

    uuids = graphene.Field(lambda: graphene.List(graphene.String))
    individuals = graphene.Field(lambda: graphene.List(IndividualType))

    @check_auth
    def mutate(self, info, uuids):
        user = info.context.user
        ctx = SortingHatContext(user)

        individuals = unmerge_identities(ctx, uuids)
        uuids = [individual.mk for individual in individuals]

        return UnmergeIdentities(
            uuids=uuids,
            individuals=individuals
        )


class Enroll(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()
        organization = graphene.String()
        from_date = graphene.DateTime(required=False)
        to_date = graphene.DateTime(required=False)
        force = graphene.Boolean(required=False)

    uuid = graphene.Field(lambda: graphene.String)
    individual = graphene.Field(lambda: IndividualType)

    @check_auth
    def mutate(self, info, uuid, organization,
               from_date=None, to_date=None,
               force=False):
        user = info.context.user
        ctx = SortingHatContext(user)

        individual = enroll(ctx, uuid, organization,
                            from_date=from_date, to_date=to_date,
                            force=force)
        return Enroll(
            uuid=individual.mk,
            individual=individual
        )


class Withdraw(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()
        organization = graphene.String()
        from_date = graphene.DateTime(required=False)
        to_date = graphene.DateTime(required=False)

    uuid = graphene.Field(lambda: graphene.String)
    individual = graphene.Field(lambda: IndividualType)

    @check_auth
    def mutate(self, info, uuid, organization, from_date=None, to_date=None):
        user = info.context.user
        ctx = SortingHatContext(user)

        individual = withdraw(ctx, uuid, organization,
                              from_date=from_date, to_date=to_date)
        return Withdraw(
            uuid=individual.mk,
            individual=individual
        )


class RecommendAffiliations(graphene.Mutation):
    class Arguments:
        uuids = graphene.List(graphene.String,
                              required=False)

    job_id = graphene.Field(lambda: graphene.String)

    @check_auth
    def mutate(self, info, uuids=None):
        user = info.context.user
        ctx = SortingHatContext(user)

        job = enqueue(recommend_affiliations, ctx, uuids)

        return RecommendAffiliations(
            job_id=job.id
        )


class RecommendMatches(graphene.Mutation):
    class Arguments:
        source_uuids = graphene.List(graphene.String)
        target_uuids = graphene.List(graphene.String,
                                     required=False)
        criteria = graphene.List(graphene.String)
        verbose = graphene.Boolean(required=False)

    job_id = graphene.Field(lambda: graphene.String)

    @check_auth
    def mutate(self, info, source_uuids, criteria, target_uuids=None, verbose=False):
        user = info.context.user
        ctx = SortingHatContext(user)

        job = enqueue(recommend_matches, ctx, source_uuids, target_uuids, criteria, verbose)

        return RecommendMatches(
            job_id=job.id
        )


class Affiliate(graphene.Mutation):
    class Arguments:
        uuids = graphene.List(graphene.String,
                              required=False)

    job_id = graphene.Field(lambda: graphene.String)

    @check_auth
    def mutate(self, info, uuids=None):
        user = info.context.user
        ctx = SortingHatContext(user)

        job = enqueue(affiliate, ctx, uuids)

        return Affiliate(
            job_id=job.id
        )


class Unify(graphene.Mutation):
    class Arguments:
        source_uuids = graphene.List(graphene.String)
        target_uuids = graphene.List(graphene.String,
                                     required=False)
        criteria = graphene.List(graphene.String)

    job_id = graphene.Field(lambda: graphene.String)

    @check_auth
    def mutate(self, info, source_uuids, criteria, target_uuids=None):
        user = info.context.user
        ctx = SortingHatContext(user)

        job = enqueue(unify, ctx, source_uuids, target_uuids, criteria)

        return Unify(
            job_id=job.id
        )


class SortingHatQuery:

    countries = graphene.Field(
        CountryPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=CountryFilterType(required=False)
    )
    organizations = graphene.Field(
        OrganizationPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=OrganizationFilterType(required=False)
    )
    individuals = graphene.Field(
        IdentityPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=IdentityFilterType(required=False)
    )
    transactions = graphene.Field(
        TransactionPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=TransactionFilterType(required=False)
    )
    operations = graphene.Field(
        OperationPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=OperationFilterType(required=False),
    )
    job = graphene.Field(
        JobType,
        job_id=graphene.String()
    )

    @check_auth
    def resolve_countries(self, info, filters=None,
                          page=1,
                          page_size=settings.DEFAULT_GRAPHQL_PAGE_SIZE):
        query = Country.objects.order_by('code')

        if filters and 'code' in filters:
            query = query.filter(code=filters['code'])
        if filters and 'term' in filters:
            query = query.filter(name__icontains=filters['term'])

        return CountryPaginatedType.create_paginated_result(query,
                                                            page,
                                                            page_size=page_size)

    @check_auth
    def resolve_organizations(self, info, filters=None,
                              page=1,
                              page_size=settings.DEFAULT_GRAPHQL_PAGE_SIZE,
                              **kwargs):
        query = Organization.objects.order_by('name')

        if filters and 'name' in filters:
            query = query.filter(name=filters['name'])

        return OrganizationPaginatedType.create_paginated_result(query,
                                                                 page,
                                                                 page_size=page_size)

    @check_auth
    def resolve_individuals(self, info, filters=None,
                            page=1,
                            page_size=settings.DEFAULT_GRAPHQL_PAGE_SIZE,
                            **kwargs):
        query = Individual.objects.order_by('mk')

        if filters and 'uuid' in filters:
            indv_uuid = filters['uuid']
            # Search among all the individuals and their identities
            query = query.filter(mk__in=Subquery(Identity.objects
                                                 .filter(Q(uuid=indv_uuid) |
                                                         Q(individual__mk=indv_uuid))
                                                 .values_list('individual__mk')))
        if filters and 'term' in filters:
            search_term = filters['term']
            # Filter matching individuals by their mk and their identities
            query = query.filter(mk__in=Subquery(Identity.objects
                                                 .filter(Q(name__icontains=search_term) |
                                                         Q(email__icontains=search_term) |
                                                         Q(username__icontains=search_term) |
                                                         Q(individual__profile__name__icontains=search_term) |
                                                         Q(individual__profile__email__icontains=search_term))
                                                 .values_list('individual__mk')))
        if filters and 'is_locked' in filters:
            query = query.filter(is_locked=filters['is_locked'])
        if filters and 'last_updated' in filters:
            # Accepted date format is ISO 8601, YYYY-MM-DDTHH:MM:SS
            try:
                filter_data = parse_date_filter(filters['last_updated'])
            except ValueError as e:
                raise InvalidFilterError(filter_name='last_updated', msg=e)
            except InvalidDateError as e:
                raise InvalidFilterError(filter_name='last_updated', msg=e)

            date1 = filter_data['date1']
            date2 = filter_data['date2']
            if filter_data['operator']:
                operator = filter_data['operator']
                if operator == '<':
                    query = query.filter(last_modified__lt=date1)
                elif operator == '<=':
                    query = query.filter(last_modified__lte=date1)
                elif operator == '>':
                    query = query.filter(last_modified__gt=date1)
                elif operator == '>=':
                    query = query.filter(last_modified__gte=date1)
                elif operator == '..':
                    query = query.filter(last_modified__range=(date1, date2))

        return IdentityPaginatedType.create_paginated_result(query,
                                                             page,
                                                             page_size=page_size)

    @check_auth
    def resolve_job(self, info, job_id):
        job = find_job(job_id)

        status = job.get_status()
        job_type = job.func_name.split('.')[-1]

        result = None
        errors = None

        if (job.result) and (job_type == 'affiliate'):
            errors = job.result['errors']
            result = [
                AffiliationResultType(uuid=uuid, organizations=orgs)
                for uuid, orgs in job.result['results'].items()
            ]
        elif (job.result) and (job_type == 'recommend_affiliations'):
            result = [
                AffiliationRecommendationType(uuid=uuid, organizations=orgs)
                for uuid, orgs in job.result['results'].items()
            ]
        elif (job.result) and (job_type == 'recommend_matches'):
            result = [
                MatchesRecommendationType(uuid=uuid, matches=matches)
                for uuid, matches in job.result['results'].items()
            ]
        elif (job.result) and (job_type == 'unify'):
            errors = job.result['errors']
            result = [
                UnifyResultType(merged=job.result['results'])
            ]

        return JobType(job_id=job_id,
                       job_type=job_type,
                       status=status,
                       result=result,
                       errors=errors)

    @check_auth
    def resolve_transactions(self, info, filters=None,
                             page=1,
                             page_size=settings.DEFAULT_GRAPHQL_PAGE_SIZE,
                             **kwargs):
        query = Transaction.objects.order_by('created_at')

        if filters and 'tuid' in filters:
            query = query.filter(tuid=filters['tuid'])
        if filters and 'name' in filters:
            query = query.filter(name=filters['name'])
        if filters and 'is_closed' in filters:
            query = query.filter(is_closed=filters['isClosed'])
        if filters and 'from_date' in filters:
            query = query.filter(created_at__gte=filters['from_date'])
        if filters and 'to_date' in filters:
            query = query.filter(created_at__lte=filters['to_date'])
        if filters and 'authored_by' in filters:
            query = query.filter(authored_by=filters['authored_by'])

        return TransactionPaginatedType.create_paginated_result(query,
                                                                page,
                                                                page_size=page_size)

    @check_auth
    def resolve_operations(self, info, filters=None,
                           page=1,
                           page_size=settings.DEFAULT_GRAPHQL_PAGE_SIZE,
                           **kwargs):
        query = Operation.objects.order_by('timestamp')

        if filters and 'ouid' in filters:
            query = query.filter(ouid=filters['ouid'])
        if filters and 'op_type' in filters:
            query = query.filter(op_type=filters['op_type'])
        if filters and 'entity_type' in filters:
            query = query.filter(entity_type=filters['entity_type'])
        if filters and 'target' in filters:
            query = query.filter(target=filters['target'])
        if filters and 'from_date' in filters:
            query = query.filter(timestamp__gte=filters['from_date'])
        if filters and 'to_date' in filters:
            query = query.filter(timestamp__lte=filters['to_date'])

        return OperationPaginatedType.create_paginated_result(query,
                                                              page,
                                                              page_size=page_size)


class SortingHatMutation(graphene.ObjectType):
    add_organization = AddOrganization.Field()
    delete_organization = DeleteOrganization.Field()
    add_domain = AddDomain.Field()
    delete_domain = DeleteDomain.Field()
    add_identity = AddIdentity.Field()
    delete_identity = DeleteIdentity.Field()
    update_profile = UpdateProfile.Field()
    move_identity = MoveIdentity.Field()
    lock = Lock.Field()
    unlock = Unlock.Field()
    merge = Merge.Field()
    unmerge_identities = UnmergeIdentities.Field()
    enroll = Enroll.Field()
    withdraw = Withdraw.Field()
    recommend_affiliations = RecommendAffiliations.Field()
    recommend_matches = RecommendMatches.Field()
    affiliate = Affiliate.Field()
    unify = Unify.Field()

    # JWT authentication
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
