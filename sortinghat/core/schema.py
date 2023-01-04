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

from django.db.models import JSONField

from django_rq import enqueue

from graphene.types.generic import GenericScalar
from graphene.utils.str_converters import to_snake_case

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
                  add_team,
                  add_domain,
                  delete_organization,
                  delete_team,
                  delete_domain,
                  enroll,
                  withdraw,
                  update_enrollment)
from .context import SortingHatContext
from .decorators import (check_auth, check_permissions)
from .errors import InvalidFilterError, EqualIndividualError
from .jobs import (affiliate,
                   unify,
                   find_job,
                   get_jobs,
                   recommend_affiliations,
                   recommend_matches,
                   recommend_gender,
                   genderize)
from .models import (Organization,
                     Team,
                     Group,
                     Domain,
                     Country,
                     Individual,
                     Identity,
                     Profile,
                     Enrollment,
                     Transaction,
                     Operation,
                     RecommenderExclusionTerm,
                     AffiliationRecommendation,
                     MergeRecommendation,
                     GenderRecommendation)
from .recommendations.exclusion import delete_recommend_exclusion_term, add_recommender_exclusion_term


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
    page = graphene.Int(description='Current page.')
    page_size = graphene.Int(description='Number of items per page.')
    num_pages = graphene.Int(description='Total number of pages.')
    has_next = graphene.Boolean(description='Whether there is a page after the current one.')
    has_prev = graphene.Boolean(description='Whether there is a page before the current one.')
    start_index = graphene.Int(description='Index of the first item on the page.')
    end_index = graphene.Int(description='Index of the last item on the page.')
    total_results = graphene.Int(description='Total number of items.')


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


class GroupType(DjangoObjectType):
    class Meta:
        model = Group
        exclude = ('path',)
        convert_choices_to_enum = False


class OrganizationType(DjangoObjectType):
    class Meta:
        model = Group
        exclude = ('path', 'depth', 'numchild', 'type', 'parent_org')


class TeamType(DjangoObjectType):
    class Meta:
        model = Group
        exclude = ('path', 'depth', 'type', 'domains', 'teams')

    subteams = graphene.List(lambda: TeamType)
    parent_org = graphene.Field(OrganizationType)

    def resolve_subteams(self, info):
        return self.get_children().order_by('name').all()


class DomainType(DjangoObjectType):
    class Meta:
        model = Domain


class CountryType(DjangoObjectType):
    class Meta:
        model = Country


class IndividualType(DjangoObjectType):
    class Meta:
        model = Individual
        exclude = ('match_recommendation_individual_1', 'match_recommendation_individual_2')

    match_recommendation_set = graphene.List(lambda: IndividualRecommendedMergeType)

    @check_auth
    def resolve_match_recommendation_set(self, info):
        indv_recs = []
        recs = self.match_recommendation_individual_1.all() | self.match_recommendation_individual_2.all()
        for rec in recs:
            indv = rec.individual1 if rec.individual1.mk != self.mk else rec.individual2
            indv_recs.append(IndividualRecommendedMergeType(id=rec.id, individual=indv))
        return indv_recs


class IdentityType(DjangoObjectType):
    class Meta:
        model = Identity


class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile


class EnrollmentType(DjangoObjectType):
    class Meta:
        model = Enrollment

    group = graphene.Field(GroupType)


class RecommendedAffiliationType(DjangoObjectType):
    class Meta:
        model = AffiliationRecommendation


class RecommendedMergeType(DjangoObjectType):
    class Meta:
        model = MergeRecommendation


class IndividualRecommendedMergeType(graphene.ObjectType):
    id = graphene.Int(description='ID of the recommendation.')
    individual = graphene.Field(IndividualType, description='Individual that matches.')


class RecommendedGenderType(DjangoObjectType):
    class Meta:
        model = GenderRecommendation


class AffiliationRecommendationType(graphene.ObjectType):
    uuid = graphene.String(description='The unique identifier of an individual.')
    organizations = graphene.List(graphene.String, description='List of recommended organizations.')


class MatchesRecommendationType(graphene.ObjectType):
    uuid = graphene.String(description='The unique identifier of an individual.')
    matches = graphene.List(graphene.String, description='List of recommended matches.')


class GenderRecommendationType(graphene.ObjectType):
    uuid = graphene.String(description='The unique identifier of an individual.')
    gender = graphene.String(description='The suggested gender of an individual')
    accuracy = graphene.Int(description='The probability of the gender to be accurate')


class RecommenderExclusionTermType(DjangoObjectType):
    class Meta:
        model = RecommenderExclusionTerm


class AffiliationResultType(graphene.ObjectType):
    uuid = graphene.String(description='The unique identifier of an individual.')
    organizations = graphene.List(
        graphene.String,
        description='List of organizations an individual was affiliated to using matching recommendations.'
    )


class UnifyResultType(graphene.ObjectType):
    merged = graphene.List(
        graphene.String,
        description='List of individuals that were merged using matching recommendations.'
    )


class GenderizeResultType(graphene.ObjectType):
    uuid = graphene.String(description='The unique identifier of an individual.')
    gender = graphene.String(description='The suggested gender of an individual')
    accuracy = graphene.Int(description='The probability of the gender to be accurate')


class JobResultType(graphene.Union):
    class Meta:
        types = (AffiliationResultType,
                 AffiliationRecommendationType,
                 MatchesRecommendationType,
                 UnifyResultType,
                 GenderRecommendationType,
                 GenderizeResultType)


class JobType(graphene.ObjectType):
    job_id = graphene.String(description='Job identifier.')
    job_type = graphene.String(description='Type of job.')
    status = graphene.String(description='Job status (`started`, `deferred`, `finished`, `failed` or `scheduled`).')
    result = graphene.List(JobResultType, description='List of job results.')
    errors = graphene.List(graphene.String, description='List of errors.')
    enqueued_at = graphene.DateTime(description='Time the job was enqueued at.')


class ProfileInputType(graphene.InputObjectType):
    name = graphene.String(required=False, description='Name of the individual.')
    email = graphene.String(required=False, description='Email address of the individual.')
    gender = graphene.String(required=False, description='Gender of the individual.')
    gender_acc = graphene.Int(
        required=False,
        description='Gender accuracy (range of 1 to 100; by default, set to 100).'
    )
    is_bot = graphene.Boolean(required=False, description='Whether an individual is a bot or not.')
    country_code = graphene.String(
        required=False,
        description='ISO-3166 country code. Examples: `DK` for Denmark, `IT` for Italy.'
    )


class CountryFilterType(graphene.InputObjectType):
    code = graphene.String(
        required=False,
        description='Filter countries with an ISO Alpha 2 country code. Examples: `DK` for Denmark, `IT` for Italy.'
    )
    term = graphene.String(
        required=False,
        description='Filter countries whose name contains the term.'
    )


class OrganizationFilterType(graphene.InputObjectType):
    name = graphene.String(
        required=False,
        description='Filter organizations with an exact name match.'
    )
    term = graphene.String(
        required=False,
        description='Filter organizations whose name or domains include the term.'
    )


class TeamFilterType(graphene.InputObjectType):
    name = graphene.String(
        required=False,
        description='Filter teams with an exact name match.'
    )
    organization = graphene.String(
        required=False,
        description='Filter teams belonging to this organization.'
    )
    parent = graphene.String(
        required=False,
        description='Filter teams which are subteams of parent.'
    )
    term = graphene.String(
        required=False,
        description='Filter teams whose name include the term.'
    )


class GroupFilterType(graphene.InputObjectType):
    name = graphene.String(
        required=False,
        description='Filter groups with an exact name match.'
    )
    parent = graphene.String(
        required=False,
        description='Filter groups which are subgroups of parent.'
    )
    term = graphene.String(
        required=False,
        description='Filter groups whose name include the term.'
    )


class IdentityFilterType(graphene.InputObjectType):
    uuid = graphene.String(
        required=False,
        description='Find an identity by its unique identifier.'
    )
    term = graphene.String(
        required=False,
        description='Filter individuals whose name, email or username contain the term.'
    )
    is_locked = graphene.Boolean(
        required=False,
        description='Filters individuals by whether their profiles are locked and cannot be edited.'
    )
    is_bot = graphene.Boolean(
        required=False,
        description='Filters individuals by whether they have been marked as bots.'
    )
    gender = graphene.String(
        required=False,
        description='Filters individuals by their gender.'
    )
    country = graphene.String(
        required=False,
        description='Filters individuals using an ISO Alpha 3 or Alpha 2 country code, or with a country name.\
                     Examples:\n * `GB`\n * `GBR`\n * `United Kingdom`'
    )
    source = graphene.String(
        required=False,
        description='Filters individuals by the data source of their identities.'
    )
    enrollment = graphene.String(
        required=False,
        description='Filters individuals affiliated to an organization.'
    )
    enrollment_parent_org = graphene.String(
        required=False,
        description='The parent organization the team in the `enrollment`\
        filter belongs to.'
    )
    enrollment_date = graphene.String(
        required=False,
        description='Filter with a comparison operator (>, >=, <, <=) and a date OR with a range operator (..) between\
                     two dates, following ISO-8601 format. Examples:\n* `>=2020-10-12T09:35:06.13045+01:00` \
                     \n * `2020-10-12T00:00:00..2020-11-22T00:00:00`.'
    )
    is_enrolled = graphene.Boolean(
        required=False,
        description='Filter individuals by whether they are affiliated to any organization.'
    )
    last_updated = graphene.String(
        required=False,
        description='Filter with a comparison operator (>, >=, <, <=) and a date OR with a range operator (..) between\
                     two dates, following ISO-8601 format. Examples:\n* `>=2020-10-12T09:35:06.13045+01:00` \
                     \n * `2020-10-12T00:00:00..2020-11-22T00:00:00`.'
    )


class TransactionFilterType(graphene.InputObjectType):
    tuid = graphene.String(
        required=False,
        description='Find a transaction using its unique id.'
    )
    name = graphene.String(
        required=False,
        description='Find a transaction using its name.'
    )
    is_closed = graphene.Boolean(
        required=False,
        description='Filter transactions by whether they are closed.'
    )
    from_date = graphene.DateTime(
        required=False,
        description='Find transactions created after a date, following ISO-8601 format. For example, `2020-04-22T00:00:00Z`.'
    )
    to_date = graphene.DateTime(
        required=False,
        description='Find transactions created before a date, following ISO-8601 format. For example, `2020-04-22T00:00:00Z`.'
    )
    authored_by = graphene.String(
        required=False,
        description='Filter transactions using the username of their author.'
    )


class OperationFilterType(graphene.InputObjectType):
    ouid = graphene.String(
        required=False,
        description='Find an operation using its unique id.'
    )
    op_type = graphene.String(
        required=False,
        description='Filter operations by their type: `ADD`, `DELETE` or `UPDATE`.'
    )
    entity_type = graphene.String(
        required=False,
        description='Filter by the type of entity involved in the operations, eg. `individual`, `profile`, `enrollment`.'
    )
    target = graphene.String(
        required=False,
        description='Filter by the argument which the operation is directed to.'
    )
    from_date = graphene.DateTime(
        required=False,
        description='Find operations created after a date, following ISO-8601 format. For example, `2020-04-22T00:00:00Z`.'
    )
    to_date = graphene.DateTime(
        required=False,
        description='Find operations created before a date, following ISO-8601 format. For example, `2020-04-22T00:00:00Z`.'
    )


class RecommendationFilterType(graphene.InputObjectType):
    is_applied = graphene.Boolean(
        required=False,
        description='Filter recommendations by their status.'
    )


class AbstractPaginatedType(graphene.ObjectType):

    @classmethod
    def create_paginated_result(cls, query, page=1,
                                page_size=settings.SORTINGHAT_API_PAGE_SIZE):
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
    entities = graphene.List(CountryType, description='A list of countries.')
    page_info = graphene.Field(PaginationType, description='Information to aid in pagination.')


class OrganizationPaginatedType(AbstractPaginatedType):
    entities = graphene.List(OrganizationType, description='A list of organizations.')
    page_info = graphene.Field(PaginationType, description='Information to aid in pagination.')


class TeamPaginatedType(AbstractPaginatedType):
    entities = graphene.List(TeamType, description='A list of teams.')
    page_info = graphene.Field(PaginationType, description='Information to aid in pagination.')


class IdentityPaginatedType(AbstractPaginatedType):
    entities = graphene.List(IndividualType, description='A list of identities.')
    page_info = graphene.Field(PaginationType, description='Information to aid in pagination.')


class TransactionPaginatedType(AbstractPaginatedType):
    entities = graphene.List(TransactionType, description='A list of transactions.')
    page_info = graphene.Field(PaginationType, description='Information to aid in pagination.')


class OperationPaginatedType(AbstractPaginatedType):
    entities = graphene.List(OperationType, description='A list of operations.')
    page_info = graphene.Field(PaginationType, description='Information to aid in pagination.')


class JobPaginatedType(AbstractPaginatedType):
    entities = graphene.List(JobType, description='A list of jobs.')
    page_info = graphene.Field(PaginationType, description='Information to aid in pagination.')


class RecommenderExclusionTermPaginatedType(AbstractPaginatedType):
    entities = graphene.List(RecommenderExclusionTermType, description='A list of recommender exclusion terms.')
    page_info = graphene.Field(PaginationType, description='Information to aid in pagination.')


class RecommendedAffiliationPaginatedType(AbstractPaginatedType):
    entities = graphene.List(RecommendedAffiliationType, description='A list of recommended affiliations.')
    page_info = graphene.Field(PaginationType, description='Information to aid in pagination.')


class RecommendedMergePaginatedType(AbstractPaginatedType):
    entities = graphene.List(RecommendedMergeType, description='A list of recommended identities matches.')
    page_info = graphene.Field(PaginationType, description='Information to aid in pagination.')


class RecommendedGenderPaginatedType(AbstractPaginatedType):
    entities = graphene.List(RecommendedGenderType, description='A list of gender recommendations from individuals.')
    page_info = graphene.Field(PaginationType, description='Information to aid in pagination.')


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


class AddTeam(graphene.Mutation):
    class Arguments:
        team_name = graphene.String()
        organization = graphene.String()
        parent_name = graphene.String()

    team = graphene.Field(lambda: TeamType)

    @check_auth
    def mutate(self, info, team_name, organization=None, parent_name=None):
        user = info.context.user
        ctx = SortingHatContext(user)

        team = add_team(ctx, team_name, organization, parent_name)

        return AddTeam(
            team=team
        )


class DeleteTeam(graphene.Mutation):
    class Arguments:
        team_name = graphene.String()
        organization = graphene.String()

    team = graphene.Field(lambda: TeamType)

    @check_auth
    def mutate(self, info, team_name, organization=None):
        user = info.context.user
        ctx = SortingHatContext(user)

        team = delete_team(ctx, team_name, organization)

        return DeleteTeam(
            team=team
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
        group = graphene.String()
        parent_org = graphene.String(required=False)
        from_date = graphene.DateTime(required=False)
        to_date = graphene.DateTime(required=False)
        force = graphene.Boolean(required=False)

    uuid = graphene.Field(lambda: graphene.String)
    individual = graphene.Field(lambda: IndividualType)

    @check_auth
    def mutate(self, info, uuid, group,
               parent_org=None,
               from_date=None, to_date=None,
               force=False):
        user = info.context.user
        ctx = SortingHatContext(user)

        individual = enroll(ctx, uuid, group, parent_org=parent_org,
                            from_date=from_date, to_date=to_date,
                            force=force)
        return Enroll(
            uuid=individual.mk,
            individual=individual
        )


class Withdraw(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()
        group = graphene.String()
        parent_org = graphene.String(required=False)
        from_date = graphene.DateTime(required=False)
        to_date = graphene.DateTime(required=False)

    uuid = graphene.Field(lambda: graphene.String)
    individual = graphene.Field(lambda: IndividualType)

    @check_auth
    def mutate(self, info, uuid, group, parent_org=None,
               from_date=None, to_date=None):
        user = info.context.user
        ctx = SortingHatContext(user)

        individual = withdraw(ctx, uuid, group, parent_org=parent_org,
                              from_date=from_date, to_date=to_date)
        return Withdraw(
            uuid=individual.mk,
            individual=individual
        )


class UpdateEnrollment(graphene.Mutation):
    class Arguments:
        uuid = graphene.String()
        group = graphene.String()
        from_date = graphene.DateTime()
        to_date = graphene.DateTime()
        new_from_date = graphene.DateTime(required=False)
        new_to_date = graphene.DateTime(required=False)
        parent_org = graphene.String(required=False)
        force = graphene.Boolean(required=False)

    uuid = graphene.Field(lambda: graphene.String)
    individual = graphene.Field(lambda: IndividualType)

    @check_auth
    def mutate(self, info, uuid, group,
               from_date, to_date,
               new_from_date=None, new_to_date=None,
               parent_org=None, force=True):
        user = info.context.user
        ctx = SortingHatContext(user)

        individual = update_enrollment(ctx, uuid, group,
                                       parent_org=parent_org,
                                       from_date=from_date,
                                       to_date=to_date,
                                       new_from_date=new_from_date,
                                       new_to_date=new_to_date,
                                       force=force)
        return UpdateEnrollment(
            uuid=individual.mk,
            individual=individual
        )


class RecommendAffiliations(graphene.Mutation):
    class Arguments:
        uuids = graphene.List(graphene.String,
                              required=False)

    job_id = graphene.Field(lambda: graphene.String)

    @check_permissions('core.execute_job')
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
        exclude = graphene.Boolean(required=False)

    job_id = graphene.Field(lambda: graphene.String)

    @check_permissions('core.execute_job')
    @check_auth
    def mutate(self, info, source_uuids, criteria, target_uuids=None, exclude=True, verbose=False):
        user = info.context.user
        ctx = SortingHatContext(user)

        job = enqueue(recommend_matches, ctx, source_uuids, target_uuids, criteria, exclude, verbose)

        return RecommendMatches(
            job_id=job.id
        )


class RecommendGender(graphene.Mutation):
    class Arguments:
        uuids = graphene.List(graphene.String)
        exclude = graphene.Boolean(required=False)
        no_strict_matching = graphene.Boolean(required=False)

    job_id = graphene.Field(lambda: graphene.String)

    @check_permissions('core.execute_job')
    @check_auth
    def mutate(self, info, uuids=None, exclude=True, no_strict_matching=False):
        user = info.context.user
        ctx = SortingHatContext(user)

        job = enqueue(recommend_gender, ctx, uuids, exclude, no_strict_matching)

        return RecommendGender(
            job_id=job.id
        )


class Affiliate(graphene.Mutation):
    class Arguments:
        uuids = graphene.List(graphene.String,
                              required=False)

    job_id = graphene.Field(lambda: graphene.String)

    @check_permissions('core.execute_job')
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
        exclude = graphene.Boolean(required=False)

    job_id = graphene.Field(lambda: graphene.String)

    @check_permissions('core.execute_job')
    @check_auth
    def mutate(self, info, source_uuids, criteria, target_uuids=None, exclude=True):
        user = info.context.user
        ctx = SortingHatContext(user)

        job = enqueue(unify, ctx, source_uuids, target_uuids, criteria, exclude)

        return Unify(
            job_id=job.id
        )


class Genderize(graphene.Mutation):
    class Arguments:
        uuids = graphene.List(graphene.String)
        exclude = graphene.Boolean(required=False)
        no_strict_matching = graphene.Boolean(required=False)

    job_id = graphene.Field(lambda: graphene.String)

    @check_permissions('core.execute_job')
    @check_auth
    def mutate(self, info, uuids=None, exclude=True, no_strict_matching=False):
        user = info.context.user
        ctx = SortingHatContext(user)

        job = enqueue(genderize, ctx, uuids, exclude, no_strict_matching)

        return Genderize(
            job_id=job.id
        )


class AddRecommenderExclusionTerm(graphene.Mutation):
    class Arguments:
        term = graphene.String()

    exclusion = graphene.Field(lambda: RecommenderExclusionTermType)

    @check_auth
    def mutate(self, info, term):
        user = info.context.user
        ctx = SortingHatContext(user)

        rel = add_recommender_exclusion_term(ctx, term)

        return AddRecommenderExclusionTerm(
            exclusion=rel
        )


class DeleteRecommenderExclusionTerm(graphene.Mutation):
    class Arguments:
        term = graphene.String()

    exclusion = graphene.Field(lambda: RecommenderExclusionTermType)

    @check_auth
    def mutate(self, info, term):
        user = info.context.user
        ctx = SortingHatContext(user)

        rel = delete_recommend_exclusion_term(ctx, term)

        return DeleteRecommenderExclusionTerm(
            exclusion=rel
        )


class ManageMergeRecommendation(graphene.Mutation):
    class Arguments:
        recommendation_id = graphene.Int()
        apply = graphene.Boolean()

    applied = graphene.Boolean()

    @check_auth
    def mutate(self, info, recommendation_id, apply):
        user = info.context.user
        ctx = SortingHatContext(user)

        recommendation = MergeRecommendation.objects.get(id=int(recommendation_id))
        if apply:
            try:
                merge(ctx, [recommendation.individual2.mk], recommendation.individual1.mk)
            except EqualIndividualError:
                pass
            # Can't keep a recommendation in which one individual is missing
            recommendation.delete()
        else:
            recommendation.applied = False
            recommendation.save()

        return ManageMergeRecommendation(
            applied=apply
        )


class ManageAffiliationRecommendation(graphene.Mutation):
    class Arguments:
        recommendation_id = graphene.Int()
        apply = graphene.Boolean()

    applied = graphene.Boolean()

    @check_auth
    def mutate(self, info, recommendation_id, apply):
        user = info.context.user
        ctx = SortingHatContext(user)

        recommendation = AffiliationRecommendation.objects.get(id=int(recommendation_id))
        if apply:
            enroll(ctx, recommendation.individual.mk, recommendation.organization.name)

        recommendation.applied = apply
        recommendation.save()

        return ManageAffiliationRecommendation(
            applied=apply
        )


class ManageGenderRecommendation(graphene.Mutation):
    class Arguments:
        recommendation_id = graphene.Int()
        apply = graphene.Boolean()

    applied = graphene.Boolean()

    @check_auth
    def mutate(self, info, recommendation_id, apply):
        user = info.context.user
        ctx = SortingHatContext(user)

        recommendation = GenderRecommendation.objects.get(id=int(recommendation_id))

        if apply:
            update_profile(ctx,
                           recommendation.individual.mk,
                           gender=recommendation.gender,
                           gender_acc=recommendation.accuracy)

        recommendation.applied = apply
        recommendation.save()

        return ManageGenderRecommendation(
            applied=apply
        )


class SortingHatQuery:

    countries = graphene.Field(
        CountryPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=CountryFilterType(required=False),
        description='Find countries.'
    )
    organizations = graphene.Field(
        OrganizationPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=OrganizationFilterType(required=False),
        description='Find organizations.'
    )
    teams = graphene.Field(
        TeamPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=TeamFilterType(required=False),
        description='Find teams.'
    )
    groups = graphene.Field(
        TeamPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=GroupFilterType(required=False),
        description='Find groups that are not linked to organizations.'
    )
    individuals = graphene.Field(
        IdentityPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=IdentityFilterType(required=False),
        order_by=graphene.String(required=False),
        description='Find individuals.'
    )
    transactions = graphene.Field(
        TransactionPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=TransactionFilterType(required=False),
        description='Find transactions.'
    )
    operations = graphene.Field(
        OperationPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=OperationFilterType(required=False),
        description='Find operations.'
    )
    job = graphene.Field(
        JobType,
        job_id=graphene.String(),
        description='Find a single job by its id.'
    )
    jobs = graphene.Field(
        JobPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        description='Get all jobs.'
    )
    recommender_exclusion_terms = graphene.Field(
        RecommenderExclusionTermPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        description='Get all recommender exclusion terms.'
    )
    recommended_affiliations = graphene.Field(
        RecommendedAffiliationPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=RecommendationFilterType(required=False),
        description='Get all recommended affiliations.'
    )
    recommended_merge = graphene.Field(
        RecommendedMergePaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=RecommendationFilterType(required=False),
        description='Get all recommended matched identities.'
    )
    recommended_gender = graphene.Field(
        RecommendedGenderPaginatedType,
        page_size=graphene.Int(),
        page=graphene.Int(),
        filters=RecommendationFilterType(required=False),
        description='Get all gender recommendations for the identities.'
    )

    @check_auth
    def resolve_countries(self, info, filters=None,
                          page=1,
                          page_size=settings.SORTINGHAT_API_PAGE_SIZE):
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
                              page_size=settings.SORTINGHAT_API_PAGE_SIZE,
                              **kwargs):
        query = Organization.objects.all_organizations().order_by('name')

        if filters and 'name' in filters:
            query = query.filter(name=filters['name'])
        if filters and 'term' in filters:
            search_term = filters['term']
            query = query.filter(Q(name__icontains=search_term) |
                                 Q(name__in=Subquery(Domain.objects
                                                    .filter(domain__icontains=search_term)
                                                    .values_list('organization__name'))))

        return OrganizationPaginatedType.create_paginated_result(query,
                                                                 page,
                                                                 page_size=page_size)

    @check_auth
    def resolve_teams(self, info, filters=None, page=1,
                      page_size=settings.SORTINGHAT_API_PAGE_SIZE, **kwargs):
        if filters:
            query = Team.objects.all_teams().order_by('name')

            # Filter teams that belong to the given organization filter
            if 'organization' in filters:
                # If no other filter is present, only show top level teams of organization
                if not ('name' in filters or 'term' in filters) and 'parent' not in filters:
                    query = Team.objects.team_root_nodes().order_by('name')
                query = query.filter(
                    Q(parent_org__in=Organization.objects.filter(name=filters['organization'])))

            query = apply_team_query_filters(query, filters)
        else:
            # If no filters are given, show all top level teams
            query = Team.objects.team_root_nodes().order_by('name')
        return TeamPaginatedType.create_paginated_result(query, page,
                                                         page_size=page_size)

    @check_auth
    def resolve_groups(self, info, filters=None, page=1,
                       page_size=settings.SORTINGHAT_API_PAGE_SIZE, **kwargs):
        if filters:
            query = Team.objects.all_teams().order_by('name')

            # Filter groups that do not belong to any organization
            query = query.filter(parent_org=None)

            query = apply_team_query_filters(query, filters)
        else:
            # If no filters are given, show all top level groups
            query = Team.objects.groups().order_by('name')
            query = query.filter(parent_org=None)
        return TeamPaginatedType.create_paginated_result(query, page,
                                                         page_size=page_size)

    @check_auth
    def resolve_individuals(self, info, filters=None,
                            page=1,
                            page_size=settings.SORTINGHAT_API_PAGE_SIZE,
                            order_by='mk',
                            **kwargs):
        query = Individual.objects.order_by(to_snake_case(order_by))

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
        if filters and 'is_bot' in filters:
            query = query.filter(mk__in=Subquery(Profile.objects
                                                 .filter(is_bot=filters['is_bot'])
                                                 .values_list('individual__mk')))
        if filters and 'gender' in filters:
            query = query.filter(profile__gender=filters['gender'])
        if filters and 'country' in filters:
            country = filters['country']
            query = query.filter(mk__in=Subquery(Profile.objects
                                                 .filter(Q(country__name__icontains=country) |
                                                         Q(country__code=country) |
                                                         Q(country__alpha3=country))
                                                 .values_list('individual__mk')))
        if filters and 'source' in filters:
            query = query.filter(mk__in=Subquery(Identity.objects
                                                 .filter(source=filters['source'])
                                                 .values_list('individual__mk')))
        if filters and 'enrollment' in filters:
            query = query.filter(mk__in=Subquery(Enrollment.objects
                                                 .filter(group__name__icontains=filters['enrollment'])
                                                 .values_list('individual__mk')))
            if 'enrollment_parent_org' in filters:
                query = query.filter(mk__in=Subquery(Enrollment.objects
                                                     .filter(group__parent_org__name=filters['enrollment_parent_org'])
                                                     .values_list('individual__mk')))
        if filters and 'enrollment_date' in filters:
            # Accepted date format is ISO 8601, YYYY-MM-DDTHH:MM:SS
            try:
                filter_data = parse_date_filter(filters['enrollment_date'])
            except ValueError as e:
                raise InvalidFilterError(filter_name='enrollment_date', msg=e)
            except InvalidDateError as e:
                raise InvalidFilterError(filter_name='enrollment_date', msg=e)
            date1 = filter_data['date1']
            date2 = filter_data['date2']
            if filter_data['operator']:
                operator = filter_data['operator']
                if operator == '<':
                    query = query.filter(mk__in=Subquery(Enrollment.objects
                                                         .filter(start__lt=date1)
                                                         .values_list('individual__mk')))
                elif operator == '<=':
                    query = query.filter(mk__in=Subquery(Enrollment.objects
                                                         .filter(start__lte=date1)
                                                         .values_list('individual__mk')))
                elif operator == '>':
                    query = query.filter(mk__in=Subquery(Enrollment.objects
                                                         .filter(end__gt=date1)
                                                         .values_list('individual__mk')))
                elif operator == '>=':
                    query = query.filter(mk__in=Subquery(Enrollment.objects
                                                         .filter(end__gte=date1)
                                                         .values_list('individual__mk')))
                elif operator == '..':
                    query = query.filter(mk__in=Subquery(Enrollment.objects
                                                         .filter(start__lte=date2,
                                                                 end__gte=date1)
                                                         .values_list('individual__mk')))
        if filters and 'is_enrolled' in filters:
            query = query.filter(mk__in=Subquery(Individual.objects
                                                 .filter(enrollments__isnull=not filters['is_enrolled'])
                                                 .values_list('mk')))

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
        enqueued_at = job.enqueued_at

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
        elif (job.result) and (job_type == 'recommend_gender'):
            result = [
                GenderRecommendationType(uuid=uuid,
                                         gender=rec['gender'],
                                         accuracy=rec['accuracy'])
                for uuid, rec in job.result['results'].items()
            ]
        elif (job.result) and (job_type == 'unify'):
            errors = job.result['errors']
            result = [
                UnifyResultType(merged=job.result['results'])
            ]
        elif (job.result) and (job_type == 'genderize'):
            errors = job.result['errors']
            result = [
                GenderizeResultType(uuid=uuid, gender=rec[0], accuracy=rec[1])
                for uuid, rec in job.result['results'].items()
            ]
        elif status == 'failed':
            errors = [job.exc_info]

        return JobType(job_id=job_id,
                       job_type=job_type,
                       status=status,
                       result=result,
                       errors=errors,
                       enqueued_at=enqueued_at)

    @check_auth
    def resolve_jobs(self, info, page=1, page_size=settings.SORTINGHAT_API_PAGE_SIZE):
        jobs = get_jobs()
        result = []

        for job in jobs:
            job_id = job.get_id()
            status = job.get_status()
            job_type = job.func_name.split('.')[-1]
            enqueued_at = job.enqueued_at

            result.append(JobType(job_id=job_id,
                                  job_type=job_type,
                                  status=status,
                                  result=[],
                                  errors=[],
                                  enqueued_at=enqueued_at))

        return JobPaginatedType.create_paginated_result(result,
                                                        page,
                                                        page_size=page_size)

    @check_auth
    def resolve_recommender_exclusion_terms(self, info,
                                            page=1,
                                            page_size=settings.SORTINGHAT_API_PAGE_SIZE):
        query = RecommenderExclusionTerm.objects.order_by('term')

        return RecommenderExclusionTermPaginatedType.create_paginated_result(query,
                                                                             page,
                                                                             page_size=page_size)

    @check_auth
    def resolve_transactions(self, info, filters=None,
                             page=1,
                             page_size=settings.SORTINGHAT_API_PAGE_SIZE,
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
                           page_size=settings.SORTINGHAT_API_PAGE_SIZE,
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

    @check_auth
    def resolve_recommended_affiliations(self, info, filters=None, page=1,
                                         page_size=settings.SORTINGHAT_API_PAGE_SIZE, **kwargs):
        if filters and 'is_applied' in filters:
            query = AffiliationRecommendation.objects.filter(applied=filters['is_applied'])
        else:
            query = AffiliationRecommendation.objects.filter(applied=None)

        query = query.order_by('created_at')

        return RecommendedAffiliationPaginatedType.create_paginated_result(query,
                                                                           page,
                                                                           page_size=page_size)

    @check_auth
    def resolve_recommended_merge(self, info, filters=None, page=1,
                                  page_size=settings.SORTINGHAT_API_PAGE_SIZE, **kwargs):
        if filters and 'is_applied' in filters:
            query = MergeRecommendation.objects.filter(applied=filters['is_applied'])
        else:
            query = MergeRecommendation.objects.filter(applied=None)

        query = query.order_by('created_at')

        return RecommendedMergePaginatedType.create_paginated_result(query,
                                                                     page,
                                                                     page_size=page_size)

    @check_auth
    def resolve_recommended_gender(self, info, filters=None, page=1,
                                   page_size=settings.SORTINGHAT_API_PAGE_SIZE, **kwargs):
        if filters and 'is_applied' in filters:
            query = GenderRecommendation.objects.filter(applied=filters['is_applied'])
        else:
            query = GenderRecommendation.objects.filter(applied=None)

        query = query.order_by('created_at')

        return RecommendedGenderPaginatedType.create_paginated_result(query,
                                                                      page,
                                                                      page_size=page_size)


class SortingHatMutation(graphene.ObjectType):
    add_organization = AddOrganization.Field(
        description='Add an organization to the registry.'
    )
    delete_organization = DeleteOrganization.Field(
        description='Remove an organization from the registry. Related information\
        such as domains or enrollments is also removed.'
    )
    add_team = AddTeam.Field(
        description='Add a team to the registry.'
    )
    delete_team = DeleteTeam.Field(
        description='Remove a team from the registry. Related information\
        such as subteams is also removed.'
    )
    add_domain = AddDomain.Field(
        description='Add a new domain to an organization. The new domain is set\
        as a top domain by default. A domain can only be assigned to one organization.'
    )
    delete_domain = DeleteDomain.Field(
        description='Remove a domain from the registry.'
    )
    add_identity = AddIdentity.Field(
        description='Add a new identity to the registry. A new individual will be\
        also added and associated to the new identity unless an `uuid` is provided.\
        When `uuid` is set, it creates a new identity associated to the individual\
        defined by this identifier.'
    )
    delete_identity = DeleteIdentity.Field(
        description='Remove an identity from the registry. If the `uuid` also\
        belongs to an individual, this entry and those identities linked to it\
        will be removed too.'
    )
    update_profile = UpdateProfile.Field(
        description='Update an individual profile.'
    )
    move_identity = MoveIdentity.Field(
        description='Shift the identity identified by `from_uuid` to the individual\
        identified by `to_uuid`.'
    )
    lock = Lock.Field(
        description='Lock an individual so it cannot be modified.'
    )
    unlock = Unlock.Field(
        description='Unlock an individual so it can be modified.'
    )
    merge = Merge.Field(
        description='Join a list of individuals, defined in `from_uuid` by any of\
        their valid identities ids, into `to_uuid` individual. Identities and enrollments\
        related to each `from_uuid` will be assigned to `to_uuid`. In addition, each\
        `from_uuid` will be removed from the registry.'
    )
    unmerge_identities = UnmergeIdentities.Field(
        description='Separate a list of `uuid` identities, creating an individual for each one.'
    )
    enroll = Enroll.Field(
        description='Enroll an individual in an organization. Existing enrollments\
        for the same individual and organization which overlap with the new period\
        will be merged into a single enrollment.'
    )
    withdraw = Withdraw.Field(
        description='Withdraw an individual identified by `uuid` from the given\
        `organization` during the given period of time.'
    )
    update_enrollment = UpdateEnrollment.Field(
        description='Update one or more enrollments from an individual given a new\
        date range. By default, `force` is set to `true`. In case any of the new\
        dates are missing, the former value for that date will be preserved.'
    )
    recommend_affiliations = RecommendAffiliations.Field(
        description='Recommend organizations for a list of individuals based on their emails.'
    )
    recommend_matches = RecommendMatches.Field(
        description='Recommend identity matches for a list of individuals based\
        on a list of criteria composed by `email`, `name` and/or `username`.'
    )
    recommend_gender = RecommendGender.Field(
        description='Recommend genders for a list of individuals based on their names\
        using the genderize.io API. `noStrictMatching` disables strict name validation.'
    )
    affiliate = Affiliate.Field(
        description='Affiliate a set of individuals using recommendations.'
    )
    unify = Unify.Field(
        description='Unify a set of individuals by merging them using matching recommendations.'
    )
    genderize = Genderize.Field(
        description='Autocomplete the gender information of a set of individuals\
        using genderize.io recommendations. `noStrictMatching` disables strict name validation.'
    )
    add_recommender_exclusion_term = AddRecommenderExclusionTerm.Field(
        description='Add a recommender exclusion to the registry.'
    )
    delete_recommender_exclusion_term = DeleteRecommenderExclusionTerm.Field(
        description='Remove a recommender exclusion from the registry.'
    )
    manage_merge_recommendation = ManageMergeRecommendation.Field(
        description='Manage a matching recommendation between identities.'
    )
    manage_affiliation_recommendation = ManageAffiliationRecommendation.Field(
        description='Manage an affiliation recommendation for an identity.'
    )
    manage_gender_recommendation = ManageGenderRecommendation.Field(
        description='Manage a gender recommendation.'
    )

    # JWT authentication
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field(description='Verify a JSON Web Token.')
    refresh_token = graphql_jwt.Refresh.Field(description='Refresh a JSON Web Token.')


def apply_team_query_filters(query, filters):
    """Apply filters to queryset containing Team objects.

    This method takes in the passed queryset and applies the `name`, `term`
    and `parent` filters to it.

    :param query: a queryset of Team objects
    :param filters: a dictionary of filters and their values

    :returns: a filtered queryset
    """
    # Filter teams that are subteams of the parent filter value
    if 'parent' in filters:
        query = query.filter(name=filters['parent'])
        if query:
            query = query.first().get_children()

    # Filter by 'name' or 'term'
    if 'name' in filters:
        query = query.filter(name=filters['name'])
    if 'term' in filters:
        query = query.filter(name__icontains=filters['term'])

    return query
