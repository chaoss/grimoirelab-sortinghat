# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2021 Bitergia
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
#     Quan Zhou <quan@bitergia.com>
#

"""
SortingHat client schema.

Automatically generated using sgqlc tools.
"""

import sgqlc.types
import sgqlc.types.datetime


sh_schema = sgqlc.types.Schema()


########################################################################
# Scalars and Enumerations
########################################################################
Boolean = sgqlc.types.Boolean

DateTime = sgqlc.types.datetime.DateTime


class GenericScalar(sgqlc.types.Scalar):
    __schema__ = sh_schema


ID = sgqlc.types.ID

Int = sgqlc.types.Int


class OperationArgsType(sgqlc.types.Scalar):
    __schema__ = sh_schema


class OperationOpType(sgqlc.types.Enum):
    __schema__ = sh_schema
    __choices__ = ('ADD', 'DELETE', 'UPDATE')


String = sgqlc.types.String


########################################################################
# Input Objects
########################################################################
class CountryFilterType(sgqlc.types.Input):
    __schema__ = sh_schema
    __field_names__ = ('code', 'term')
    code = sgqlc.types.Field(String, graphql_name='code')
    term = sgqlc.types.Field(String, graphql_name='term')


class GroupFilterType(sgqlc.types.Input):
    __schema__ = sh_schema
    __field_names__ = ('name', 'parent', 'term')
    name = sgqlc.types.Field(String, graphql_name='name')
    parent = sgqlc.types.Field(String, graphql_name='parent')
    term = sgqlc.types.Field(String, graphql_name='term')


class IdentityFilterType(sgqlc.types.Input):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'term', 'is_locked', 'is_bot', 'gender', 'country', 'source', 'enrollment', 'enrollment_parent_org', 'enrollment_date', 'is_enrolled', 'last_updated', 'last_reviewed', 'is_reviewed')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    term = sgqlc.types.Field(String, graphql_name='term')
    is_locked = sgqlc.types.Field(Boolean, graphql_name='isLocked')
    is_bot = sgqlc.types.Field(Boolean, graphql_name='isBot')
    gender = sgqlc.types.Field(String, graphql_name='gender')
    country = sgqlc.types.Field(String, graphql_name='country')
    source = sgqlc.types.Field(String, graphql_name='source')
    enrollment = sgqlc.types.Field(String, graphql_name='enrollment')
    enrollment_parent_org = sgqlc.types.Field(String, graphql_name='enrollmentParentOrg')
    enrollment_date = sgqlc.types.Field(String, graphql_name='enrollmentDate')
    is_enrolled = sgqlc.types.Field(Boolean, graphql_name='isEnrolled')
    last_updated = sgqlc.types.Field(String, graphql_name='lastUpdated')
    last_reviewed = sgqlc.types.Field(String, graphql_name='lastReviewed')
    is_reviewed = sgqlc.types.Field(Boolean, graphql_name='isReviewed')


class OperationFilterType(sgqlc.types.Input):
    __schema__ = sh_schema
    __field_names__ = ('ouid', 'op_type', 'entity_type', 'target', 'from_date', 'to_date')
    ouid = sgqlc.types.Field(String, graphql_name='ouid')
    op_type = sgqlc.types.Field(String, graphql_name='opType')
    entity_type = sgqlc.types.Field(String, graphql_name='entityType')
    target = sgqlc.types.Field(String, graphql_name='target')
    from_date = sgqlc.types.Field(DateTime, graphql_name='fromDate')
    to_date = sgqlc.types.Field(DateTime, graphql_name='toDate')


class OrganizationFilterType(sgqlc.types.Input):
    __schema__ = sh_schema
    __field_names__ = ('name', 'term')
    name = sgqlc.types.Field(String, graphql_name='name')
    term = sgqlc.types.Field(String, graphql_name='term')


class ProfileInputType(sgqlc.types.Input):
    __schema__ = sh_schema
    __field_names__ = ('name', 'email', 'gender', 'gender_acc', 'is_bot', 'country_code')
    name = sgqlc.types.Field(String, graphql_name='name')
    email = sgqlc.types.Field(String, graphql_name='email')
    gender = sgqlc.types.Field(String, graphql_name='gender')
    gender_acc = sgqlc.types.Field(Int, graphql_name='genderAcc')
    is_bot = sgqlc.types.Field(Boolean, graphql_name='isBot')
    country_code = sgqlc.types.Field(String, graphql_name='countryCode')


class TeamFilterType(sgqlc.types.Input):
    __schema__ = sh_schema
    __field_names__ = ('name', 'organization', 'parent', 'term')
    name = sgqlc.types.Field(String, graphql_name='name')
    organization = sgqlc.types.Field(String, graphql_name='organization')
    parent = sgqlc.types.Field(String, graphql_name='parent')
    term = sgqlc.types.Field(String, graphql_name='term')


class TransactionFilterType(sgqlc.types.Input):
    __schema__ = sh_schema
    __field_names__ = ('tuid', 'name', 'is_closed', 'from_date', 'to_date', 'authored_by')
    tuid = sgqlc.types.Field(String, graphql_name='tuid')
    name = sgqlc.types.Field(String, graphql_name='name')
    is_closed = sgqlc.types.Field(Boolean, graphql_name='isClosed')
    from_date = sgqlc.types.Field(DateTime, graphql_name='fromDate')
    to_date = sgqlc.types.Field(DateTime, graphql_name='toDate')
    authored_by = sgqlc.types.Field(String, graphql_name='authoredBy')


########################################################################
# Output Objects and Interfaces
########################################################################

class AddDomain(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('domain',)
    domain = sgqlc.types.Field('DomainType', graphql_name='domain')


class AddIdentity(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'individual')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    individual = sgqlc.types.Field('IndividualType', graphql_name='individual')


class AddOrganization(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('organization',)
    organization = sgqlc.types.Field('OrganizationType', graphql_name='organization')


class AddRecommenderExclusionTerm(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('exclusion',)
    exclusion = sgqlc.types.Field('RecommenderExclusionTermType', graphql_name='exclusion')


class AddTeam(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('team',)
    team = sgqlc.types.Field('TeamType', graphql_name='team')


class Affiliate(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('job_id',)
    job_id = sgqlc.types.Field(String, graphql_name='jobId')


class AffiliationRecommendationType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'organizations')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    organizations = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='organizations')


class AffiliationResultType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'organizations')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    organizations = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='organizations')


class CountryPaginatedType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('entities', 'page_info')
    entities = sgqlc.types.Field(sgqlc.types.list_of('CountryType'), graphql_name='entities')
    page_info = sgqlc.types.Field('PaginationType', graphql_name='pageInfo')


class CountryType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('created_at', 'last_modified', 'code', 'name', 'alpha3', 'profile_set')
    created_at = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='createdAt')
    last_modified = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='lastModified')
    code = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='code')
    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')
    alpha3 = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='alpha3')
    profile_set = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('ProfileType'))), graphql_name='profileSet')


class DeleteDomain(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('domain',)
    domain = sgqlc.types.Field('DomainType', graphql_name='domain')


class DeleteIdentity(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'individual')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    individual = sgqlc.types.Field('IndividualType', graphql_name='individual')


class DeleteOrganization(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('organization',)
    organization = sgqlc.types.Field('OrganizationType', graphql_name='organization')


class DeleteRecommenderExclusionTerm(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('exclusion',)
    exclusion = sgqlc.types.Field('RecommenderExclusionTermType', graphql_name='exclusion')


class DeleteTeam(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('team',)
    team = sgqlc.types.Field('TeamType', graphql_name='team')


class DomainType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('created_at', 'last_modified', 'id', 'domain', 'is_top_domain', 'organization')
    created_at = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='createdAt')
    last_modified = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='lastModified')
    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')
    domain = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='domain')
    is_top_domain = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isTopDomain')
    organization = sgqlc.types.Field(sgqlc.types.non_null('TeamType'), graphql_name='organization')


class AliasType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('created_at', 'last_modified', 'id', 'alias', 'organization')
    created_at = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='createdAt')
    last_modified = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='lastModified')
    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')
    alias = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='alias')
    organization = sgqlc.types.Field(sgqlc.types.non_null('TeamType'), graphql_name='organization')


class Enroll(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'individual')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    individual = sgqlc.types.Field('IndividualType', graphql_name='individual')


class EnrollmentType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('created_at', 'last_modified', 'id', 'individual', 'group', 'start', 'end')
    created_at = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='createdAt')
    last_modified = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='lastModified')
    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')
    individual = sgqlc.types.Field(sgqlc.types.non_null('IndividualType'), graphql_name='individual')
    group = sgqlc.types.Field('GroupType', graphql_name='group')
    start = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='start')
    end = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='end')


class GenderRecommendationType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'gender', 'accuracy')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    gender = sgqlc.types.Field(String, graphql_name='gender')
    accuracy = sgqlc.types.Field(Int, graphql_name='accuracy')


class Genderize(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('job_id',)
    job_id = sgqlc.types.Field(String, graphql_name='jobId')


class GenderizeResultType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'gender', 'accuracy')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    gender = sgqlc.types.Field(String, graphql_name='gender')
    accuracy = sgqlc.types.Field(Int, graphql_name='accuracy')


class GroupType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('id', 'depth', 'numchild', 'created_at', 'last_modified', 'name', 'type', 'parent_org', 'teams', 'domains', 'enrollments')
    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')
    depth = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='depth')
    numchild = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='numchild')
    created_at = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='createdAt')
    last_modified = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='lastModified')
    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')
    type = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='type')
    parent_org = sgqlc.types.Field('TeamType', graphql_name='parentOrg')
    teams = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('TeamType'))), graphql_name='teams')
    domains = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(DomainType))), graphql_name='domains')
    enrollments = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(EnrollmentType))), graphql_name='enrollments')


class IdentityPaginatedType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('entities', 'page_info')
    entities = sgqlc.types.Field(sgqlc.types.list_of('IndividualType'), graphql_name='entities')
    page_info = sgqlc.types.Field('PaginationType', graphql_name='pageInfo')


class IdentityType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('created_at', 'last_modified', 'uuid', 'name', 'email', 'username', 'source', 'individual')
    created_at = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='createdAt')
    last_modified = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='lastModified')
    uuid = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='uuid')
    name = sgqlc.types.Field(String, graphql_name='name')
    email = sgqlc.types.Field(String, graphql_name='email')
    username = sgqlc.types.Field(String, graphql_name='username')
    source = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='source')
    individual = sgqlc.types.Field(sgqlc.types.non_null('IndividualType'), graphql_name='individual')


class IndividualType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('created_at', 'last_modified', 'mk', 'is_locked', 'identities', 'profile', 'enrollments', 'last_reviewed')
    created_at = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='createdAt')
    last_modified = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='lastModified')
    mk = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='mk')
    is_locked = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isLocked')
    identities = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(IdentityType))), graphql_name='identities')
    profile = sgqlc.types.Field('ProfileType', graphql_name='profile')
    enrollments = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(EnrollmentType))), graphql_name='enrollments')
    last_reviewed = sgqlc.types.Field(String, graphql_name='lastReviewed')


class JobPaginatedType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('entities', 'page_info')
    entities = sgqlc.types.Field(sgqlc.types.list_of('JobType'), graphql_name='entities')
    page_info = sgqlc.types.Field('PaginationType', graphql_name='pageInfo')


class JobType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('job_id', 'job_type', 'status', 'result', 'errors', 'enqueued_at')
    job_id = sgqlc.types.Field(String, graphql_name='jobId')
    job_type = sgqlc.types.Field(String, graphql_name='jobType')
    status = sgqlc.types.Field(String, graphql_name='status')
    result = sgqlc.types.Field(sgqlc.types.list_of('JobResultType'), graphql_name='result')
    errors = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='errors')
    enqueued_at = sgqlc.types.Field(DateTime, graphql_name='enqueuedAt')


class Lock(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'individual')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    individual = sgqlc.types.Field(IndividualType, graphql_name='individual')


class MatchesRecommendationType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'matches')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    matches = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='matches')


class Merge(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'individual')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    individual = sgqlc.types.Field(IndividualType, graphql_name='individual')


class MoveIdentity(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'individual')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    individual = sgqlc.types.Field(IndividualType, graphql_name='individual')


class ObtainJSONWebToken(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('payload', 'refresh_expires_in', 'token')
    payload = sgqlc.types.Field(sgqlc.types.non_null(GenericScalar), graphql_name='payload')
    refresh_expires_in = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='refreshExpiresIn')
    token = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='token')


class OperationPaginatedType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('entities', 'page_info')
    entities = sgqlc.types.Field(sgqlc.types.list_of('OperationType'), graphql_name='entities')
    page_info = sgqlc.types.Field('PaginationType', graphql_name='pageInfo')


class OperationType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('ouid', 'op_type', 'entity_type', 'target', 'trx', 'timestamp', 'args')
    ouid = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='ouid')
    op_type = sgqlc.types.Field(sgqlc.types.non_null(OperationOpType), graphql_name='opType')
    entity_type = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='entityType')
    target = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='target')
    trx = sgqlc.types.Field(sgqlc.types.non_null('TransactionType'), graphql_name='trx')
    timestamp = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='timestamp')
    args = sgqlc.types.Field(sgqlc.types.non_null(OperationArgsType), graphql_name='args')


class OrganizationPaginatedType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('entities', 'page_info')
    entities = sgqlc.types.Field(sgqlc.types.list_of('OrganizationType'), graphql_name='entities')
    page_info = sgqlc.types.Field('PaginationType', graphql_name='pageInfo')


class OrganizationType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('id', 'created_at', 'last_modified', 'name', 'teams', 'domains', 'enrollments', 'aliases')
    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')
    created_at = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='createdAt')
    last_modified = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='lastModified')
    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')
    teams = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null('TeamType'))), graphql_name='teams')
    domains = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(DomainType))), graphql_name='domains')
    enrollments = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(EnrollmentType))), graphql_name='enrollments')
    aliases = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(AliasType))), graphql_name='aliases')


class PaginationType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('page', 'page_size', 'num_pages', 'has_next', 'has_prev', 'start_index', 'end_index', 'total_results')
    page = sgqlc.types.Field(Int, graphql_name='page')
    page_size = sgqlc.types.Field(Int, graphql_name='pageSize')
    num_pages = sgqlc.types.Field(Int, graphql_name='numPages')
    has_next = sgqlc.types.Field(Boolean, graphql_name='hasNext')
    has_prev = sgqlc.types.Field(Boolean, graphql_name='hasPrev')
    start_index = sgqlc.types.Field(Int, graphql_name='startIndex')
    end_index = sgqlc.types.Field(Int, graphql_name='endIndex')
    total_results = sgqlc.types.Field(Int, graphql_name='totalResults')


class ProfileType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('created_at', 'last_modified', 'id', 'individual', 'name', 'email', 'gender', 'gender_acc', 'is_bot', 'country')
    created_at = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='createdAt')
    last_modified = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='lastModified')
    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')
    individual = sgqlc.types.Field(sgqlc.types.non_null(IndividualType), graphql_name='individual')
    name = sgqlc.types.Field(String, graphql_name='name')
    email = sgqlc.types.Field(String, graphql_name='email')
    gender = sgqlc.types.Field(String, graphql_name='gender')
    gender_acc = sgqlc.types.Field(Int, graphql_name='genderAcc')
    is_bot = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isBot')
    country = sgqlc.types.Field(CountryType, graphql_name='country')


class Query(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('countries', 'organizations', 'teams', 'groups', 'individuals', 'transactions', 'operations', 'job', 'jobs', 'recommender_exclusion_terms')
    countries = sgqlc.types.Field(
        CountryPaginatedType,
        graphql_name='countries',
        args=sgqlc.types.ArgDict((
            ('page_size', sgqlc.types.Arg(Int, graphql_name='pageSize', default=None)),
            ('page', sgqlc.types.Arg(Int, graphql_name='page', default=None)),
            ('filters', sgqlc.types.Arg(CountryFilterType, graphql_name='filters', default=None)),
        ))
    )
    organizations = sgqlc.types.Field(
        OrganizationPaginatedType,
        graphql_name='organizations',
        args=sgqlc.types.ArgDict((
            ('page_size', sgqlc.types.Arg(Int, graphql_name='pageSize', default=None)),
            ('page', sgqlc.types.Arg(Int, graphql_name='page', default=None)),
            ('filters', sgqlc.types.Arg(OrganizationFilterType, graphql_name='filters', default=None)),
        ))
    )
    teams = sgqlc.types.Field(
        'TeamPaginatedType',
        graphql_name='teams',
        args=sgqlc.types.ArgDict((
            ('page_size', sgqlc.types.Arg(Int, graphql_name='pageSize', default=None)),
            ('page', sgqlc.types.Arg(Int, graphql_name='page', default=None)),
            ('filters', sgqlc.types.Arg(TeamFilterType, graphql_name='filters', default=None)),
        ))
    )
    groups = sgqlc.types.Field(
        'TeamPaginatedType',
        graphql_name='groups',
        args=sgqlc.types.ArgDict((
            ('page_size', sgqlc.types.Arg(Int, graphql_name='pageSize', default=None)),
            ('page', sgqlc.types.Arg(Int, graphql_name='page', default=None)),
            ('filters', sgqlc.types.Arg(GroupFilterType, graphql_name='filters', default=None)),
        ))
    )
    individuals = sgqlc.types.Field(
        IdentityPaginatedType,
        graphql_name='individuals',
        args=sgqlc.types.ArgDict((
            ('page_size', sgqlc.types.Arg(Int, graphql_name='pageSize', default=None)),
            ('page', sgqlc.types.Arg(Int, graphql_name='page', default=None)),
            ('filters', sgqlc.types.Arg(IdentityFilterType, graphql_name='filters', default=None)),
            ('order_by', sgqlc.types.Arg(String, graphql_name='orderBy', default=None)),
        ))
    )
    transactions = sgqlc.types.Field(
        'TransactionPaginatedType',
        graphql_name='transactions',
        args=sgqlc.types.ArgDict((
            ('page_size', sgqlc.types.Arg(Int, graphql_name='pageSize', default=None)),
            ('page', sgqlc.types.Arg(Int, graphql_name='page', default=None)),
            ('filters', sgqlc.types.Arg(TransactionFilterType, graphql_name='filters', default=None)),
        ))
    )
    operations = sgqlc.types.Field(
        OperationPaginatedType,
        graphql_name='operations',
        args=sgqlc.types.ArgDict((
            ('page_size', sgqlc.types.Arg(Int, graphql_name='pageSize', default=None)),
            ('page', sgqlc.types.Arg(Int, graphql_name='page', default=None)),
            ('filters', sgqlc.types.Arg(OperationFilterType, graphql_name='filters', default=None)),
        ))
    )
    job = sgqlc.types.Field(
        JobType,
        graphql_name='job',
        args=sgqlc.types.ArgDict((
            ('job_id', sgqlc.types.Arg(String, graphql_name='jobId', default=None)),
        ))
    )
    jobs = sgqlc.types.Field(
        JobPaginatedType,
        graphql_name='jobs',
        args=sgqlc.types.ArgDict((
            ('page_size', sgqlc.types.Arg(Int, graphql_name='pageSize', default=None)),
            ('page', sgqlc.types.Arg(Int, graphql_name='page', default=None)),
        ))
    )
    recommender_exclusion_terms = sgqlc.types.Field(
        'RecommenderExclusionTermPaginatedType',
        graphql_name='recommenderExclusionTerms',
        args=sgqlc.types.ArgDict((
            ('page_size', sgqlc.types.Arg(Int, graphql_name='pageSize', default=None)),
            ('page', sgqlc.types.Arg(Int, graphql_name='page', default=None)),
        ))
    )


class RecommendAffiliations(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('job_id',)
    job_id = sgqlc.types.Field(String, graphql_name='jobId')


class RecommendGender(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('job_id',)
    job_id = sgqlc.types.Field(String, graphql_name='jobId')


class RecommendMatches(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('job_id',)
    job_id = sgqlc.types.Field(String, graphql_name='jobId')


class RecommenderExclusionTermPaginatedType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('entities', 'page_info')
    entities = sgqlc.types.Field(sgqlc.types.list_of('RecommenderExclusionTermType'), graphql_name='entities')
    page_info = sgqlc.types.Field(PaginationType, graphql_name='pageInfo')


class RecommenderExclusionTermType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('created_at', 'last_modified', 'id', 'term')
    created_at = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='createdAt')
    last_modified = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='lastModified')
    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')
    term = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='term')


class Refresh(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('payload', 'refresh_expires_in', 'token')
    payload = sgqlc.types.Field(sgqlc.types.non_null(GenericScalar), graphql_name='payload')
    refresh_expires_in = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='refreshExpiresIn')
    token = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='token')


class Review(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'individual')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    individual = sgqlc.types.Field(IndividualType, graphql_name='individual')


class SortingHatMutation(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('add_organization', 'delete_organization', 'add_team', 'delete_team', 'add_domain', 'delete_domain', 'add_identity', 'delete_identity', 'update_profile', 'move_identity', 'lock', 'unlock', 'merge', 'unmerge_identities', 'enroll', 'withdraw', 'update_enrollment', 'recommend_affiliations', 'recommend_matches', 'recommend_gender', 'affiliate', 'unify', 'genderize', 'add_recommender_exclusion_term', 'delete_recommender_exclusion_term', 'token_auth', 'verify_token', 'refresh_token')
    add_organization = sgqlc.types.Field(
        AddOrganization,
        graphql_name='addOrganization',
        args=sgqlc.types.ArgDict((
            ('name', sgqlc.types.Arg(String, graphql_name='name', default=None)),
        ))
    )
    delete_organization = sgqlc.types.Field(
        DeleteOrganization,
        graphql_name='deleteOrganization',
        args=sgqlc.types.ArgDict((
            ('name', sgqlc.types.Arg(String, graphql_name='name', default=None)),
        ))
    )
    add_team = sgqlc.types.Field(
        AddTeam,
        graphql_name='addTeam',
        args=sgqlc.types.ArgDict((
            ('organization', sgqlc.types.Arg(String, graphql_name='organization', default=None)),
            ('parent_name', sgqlc.types.Arg(String, graphql_name='parentName', default=None)),
            ('team_name', sgqlc.types.Arg(String, graphql_name='teamName', default=None)),
        ))
    )
    delete_team = sgqlc.types.Field(
        DeleteTeam,
        graphql_name='deleteTeam',
        args=sgqlc.types.ArgDict((
            ('organization', sgqlc.types.Arg(String, graphql_name='organization', default=None)),
            ('team_name', sgqlc.types.Arg(String, graphql_name='teamName', default=None)),
        ))
    )
    add_domain = sgqlc.types.Field(
        AddDomain,
        graphql_name='addDomain',
        args=sgqlc.types.ArgDict((
            ('domain', sgqlc.types.Arg(String, graphql_name='domain', default=None)),
            ('is_top_domain', sgqlc.types.Arg(Boolean, graphql_name='isTopDomain', default=None)),
            ('organization', sgqlc.types.Arg(String, graphql_name='organization', default=None)),
        ))
    )
    delete_domain = sgqlc.types.Field(
        DeleteDomain,
        graphql_name='deleteDomain',
        args=sgqlc.types.ArgDict((
            ('domain', sgqlc.types.Arg(String, graphql_name='domain', default=None)),
        ))
    )
    add_identity = sgqlc.types.Field(
        AddIdentity,
        graphql_name='addIdentity',
        args=sgqlc.types.ArgDict((
            ('email', sgqlc.types.Arg(String, graphql_name='email', default=None)),
            ('name', sgqlc.types.Arg(String, graphql_name='name', default=None)),
            ('source', sgqlc.types.Arg(String, graphql_name='source', default=None)),
            ('username', sgqlc.types.Arg(String, graphql_name='username', default=None)),
            ('uuid', sgqlc.types.Arg(String, graphql_name='uuid', default=None)),
        ))
    )
    delete_identity = sgqlc.types.Field(
        DeleteIdentity,
        graphql_name='deleteIdentity',
        args=sgqlc.types.ArgDict((
            ('uuid', sgqlc.types.Arg(String, graphql_name='uuid', default=None)),
        ))
    )
    update_profile = sgqlc.types.Field(
        'UpdateProfile',
        graphql_name='updateProfile',
        args=sgqlc.types.ArgDict((
            ('data', sgqlc.types.Arg(ProfileInputType, graphql_name='data', default=None)),
            ('uuid', sgqlc.types.Arg(String, graphql_name='uuid', default=None)),
        ))
    )
    move_identity = sgqlc.types.Field(
        MoveIdentity,
        graphql_name='moveIdentity',
        args=sgqlc.types.ArgDict((
            ('from_uuid', sgqlc.types.Arg(String, graphql_name='fromUuid', default=None)),
            ('to_uuid', sgqlc.types.Arg(String, graphql_name='toUuid', default=None)),
        ))
    )
    lock = sgqlc.types.Field(
        Lock,
        graphql_name='lock',
        args=sgqlc.types.ArgDict((
            ('uuid', sgqlc.types.Arg(String, graphql_name='uuid', default=None)),
        ))
    )
    unlock = sgqlc.types.Field(
        'Unlock',
        graphql_name='unlock',
        args=sgqlc.types.ArgDict((
            ('uuid', sgqlc.types.Arg(String, graphql_name='uuid', default=None)),
        ))
    )
    merge = sgqlc.types.Field(
        Merge,
        graphql_name='merge',
        args=sgqlc.types.ArgDict((
            ('from_uuids', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='fromUuids', default=None)),
            ('to_uuid', sgqlc.types.Arg(String, graphql_name='toUuid', default=None)),
        ))
    )
    unmerge_identities = sgqlc.types.Field(
        'UnmergeIdentities',
        graphql_name='unmergeIdentities',
        args=sgqlc.types.ArgDict((
            ('uuids', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='uuids', default=None)),
        ))
    )
    enroll = sgqlc.types.Field(
        Enroll,
        graphql_name='enroll',
        args=sgqlc.types.ArgDict((
            ('force', sgqlc.types.Arg(Boolean, graphql_name='force', default=None)),
            ('from_date', sgqlc.types.Arg(DateTime, graphql_name='fromDate', default=None)),
            ('group', sgqlc.types.Arg(String, graphql_name='group', default=None)),
            ('parent_org', sgqlc.types.Arg(String, graphql_name='parentOrg', default=None)),
            ('to_date', sgqlc.types.Arg(DateTime, graphql_name='toDate', default=None)),
            ('uuid', sgqlc.types.Arg(String, graphql_name='uuid', default=None)),
        ))
    )
    withdraw = sgqlc.types.Field(
        'Withdraw',
        graphql_name='withdraw',
        args=sgqlc.types.ArgDict((
            ('from_date', sgqlc.types.Arg(DateTime, graphql_name='fromDate', default=None)),
            ('group', sgqlc.types.Arg(String, graphql_name='group', default=None)),
            ('parent_org', sgqlc.types.Arg(String, graphql_name='parentOrg', default=None)),
            ('to_date', sgqlc.types.Arg(DateTime, graphql_name='toDate', default=None)),
            ('uuid', sgqlc.types.Arg(String, graphql_name='uuid', default=None)),
        ))
    )
    update_enrollment = sgqlc.types.Field(
        'UpdateEnrollment',
        graphql_name='updateEnrollment',
        args=sgqlc.types.ArgDict((
            ('force', sgqlc.types.Arg(Boolean, graphql_name='force', default=None)),
            ('from_date', sgqlc.types.Arg(DateTime, graphql_name='fromDate', default=None)),
            ('group', sgqlc.types.Arg(String, graphql_name='group', default=None)),
            ('new_from_date', sgqlc.types.Arg(DateTime, graphql_name='newFromDate', default=None)),
            ('new_to_date', sgqlc.types.Arg(DateTime, graphql_name='newToDate', default=None)),
            ('parent_org', sgqlc.types.Arg(String, graphql_name='parentOrg', default=None)),
            ('to_date', sgqlc.types.Arg(DateTime, graphql_name='toDate', default=None)),
            ('uuid', sgqlc.types.Arg(String, graphql_name='uuid', default=None)),
        ))
    )
    recommend_affiliations = sgqlc.types.Field(
        RecommendAffiliations,
        graphql_name='recommendAffiliations',
        args=sgqlc.types.ArgDict((
            ('uuids', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='uuids', default=None)),
        ))
    )
    recommend_matches = sgqlc.types.Field(
        RecommendMatches,
        graphql_name='recommendMatches',
        args=sgqlc.types.ArgDict((
            ('criteria', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='criteria', default=None)),
            ('exclude', sgqlc.types.Arg(Boolean, graphql_name='exclude', default=None)),
            ('source_uuids', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='sourceUuids', default=None)),
            ('target_uuids', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='targetUuids', default=None)),
            ('verbose', sgqlc.types.Arg(Boolean, graphql_name='verbose', default=None)),
        ))
    )
    recommend_gender = sgqlc.types.Field(
        RecommendGender,
        graphql_name='recommendGender',
        args=sgqlc.types.ArgDict((
            ('exclude', sgqlc.types.Arg(Boolean, graphql_name='exclude', default=None)),
            ('no_strict_matching', sgqlc.types.Arg(Boolean, graphql_name='noStrictMatching', default=None)),
            ('uuids', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='uuids', default=None)),
        ))
    )
    affiliate = sgqlc.types.Field(
        Affiliate,
        graphql_name='affiliate',
        args=sgqlc.types.ArgDict((
            ('uuids', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='uuids', default=None)),
        ))
    )
    unify = sgqlc.types.Field(
        'Unify',
        graphql_name='unify',
        args=sgqlc.types.ArgDict((
            ('criteria', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='criteria', default=None)),
            ('exclude', sgqlc.types.Arg(Boolean, graphql_name='exclude', default=None)),
            ('source_uuids', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='sourceUuids', default=None)),
            ('target_uuids', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='targetUuids', default=None)),
        ))
    )
    genderize = sgqlc.types.Field(
        Genderize,
        graphql_name='genderize',
        args=sgqlc.types.ArgDict((
            ('exclude', sgqlc.types.Arg(Boolean, graphql_name='exclude', default=None)),
            ('no_strict_matching', sgqlc.types.Arg(Boolean, graphql_name='noStrictMatching', default=None)),
            ('uuids', sgqlc.types.Arg(sgqlc.types.list_of(String), graphql_name='uuids', default=None)),
        ))
    )
    add_recommender_exclusion_term = sgqlc.types.Field(
        AddRecommenderExclusionTerm,
        graphql_name='addRecommenderExclusionTerm',
        args=sgqlc.types.ArgDict((
            ('term', sgqlc.types.Arg(String, graphql_name='term', default=None)),
        ))
    )
    delete_recommender_exclusion_term = sgqlc.types.Field(
        DeleteRecommenderExclusionTerm,
        graphql_name='deleteRecommenderExclusionTerm',
        args=sgqlc.types.ArgDict((
            ('term', sgqlc.types.Arg(String, graphql_name='term', default=None)),
        ))
    )
    review = sgqlc.types.Field(
        Review,
        graphql_name='review',
        args=sgqlc.types.ArgDict((
            ('uuid', sgqlc.types.Arg(String, graphql_name='uuid', default=None)),
        ))
    )
    token_auth = sgqlc.types.Field(
        ObtainJSONWebToken,
        graphql_name='tokenAuth',
        args=sgqlc.types.ArgDict((
            ('username', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='username', default=None)),
            ('password', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='password', default=None)),
        ))
    )
    verify_token = sgqlc.types.Field(
        'Verify',
        graphql_name='verifyToken',
        args=sgqlc.types.ArgDict((
            ('token', sgqlc.types.Arg(String, graphql_name='token', default=None)),
        ))
    )
    refresh_token = sgqlc.types.Field(
        Refresh,
        graphql_name='refreshToken',
        args=sgqlc.types.ArgDict((
            ('token', sgqlc.types.Arg(String, graphql_name='token', default=None)),
        ))
    )


class TeamPaginatedType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('entities', 'page_info')
    entities = sgqlc.types.Field(sgqlc.types.list_of('TeamType'), graphql_name='entities')
    page_info = sgqlc.types.Field(PaginationType, graphql_name='pageInfo')


class TeamType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('id', 'numchild', 'created_at', 'last_modified', 'name', 'parent_org', 'enrollments', 'subteams')
    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')
    numchild = sgqlc.types.Field(sgqlc.types.non_null(Int), graphql_name='numchild')
    created_at = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='createdAt')
    last_modified = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='lastModified')
    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')
    parent_org = sgqlc.types.Field(OrganizationType, graphql_name='parentOrg')
    enrollments = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(EnrollmentType))), graphql_name='enrollments')
    subteams = sgqlc.types.Field(sgqlc.types.list_of('TeamType'), graphql_name='subteams')


class TransactionPaginatedType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('entities', 'page_info')
    entities = sgqlc.types.Field(sgqlc.types.list_of('TransactionType'), graphql_name='entities')
    page_info = sgqlc.types.Field(PaginationType, graphql_name='pageInfo')


class TransactionType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('tuid', 'name', 'created_at', 'closed_at', 'is_closed', 'authored_by', 'operations')
    tuid = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='tuid')
    name = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='name')
    created_at = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='createdAt')
    closed_at = sgqlc.types.Field(DateTime, graphql_name='closedAt')
    is_closed = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='isClosed')
    authored_by = sgqlc.types.Field(String, graphql_name='authoredBy')
    operations = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(sgqlc.types.non_null(OperationType))), graphql_name='operations')


class Unify(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('job_id',)
    job_id = sgqlc.types.Field(String, graphql_name='jobId')


class UnifyResultType(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('merged',)
    merged = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='merged')


class Unlock(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'individual')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    individual = sgqlc.types.Field(IndividualType, graphql_name='individual')


class UnmergeIdentities(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuids', 'individuals')
    uuids = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='uuids')
    individuals = sgqlc.types.Field(sgqlc.types.list_of(IndividualType), graphql_name='individuals')


class UpdateEnrollment(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'individual')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    individual = sgqlc.types.Field(IndividualType, graphql_name='individual')


class UpdateProfile(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'individual')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    individual = sgqlc.types.Field(IndividualType, graphql_name='individual')


class Verify(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('payload',)
    payload = sgqlc.types.Field(sgqlc.types.non_null(GenericScalar), graphql_name='payload')


class Withdraw(sgqlc.types.Type):
    __schema__ = sh_schema
    __field_names__ = ('uuid', 'individual')
    uuid = sgqlc.types.Field(String, graphql_name='uuid')
    individual = sgqlc.types.Field(IndividualType, graphql_name='individual')


########################################################################
# Unions
########################################################################

class JobResultType(sgqlc.types.Union):
    __schema__ = sh_schema
    __types__ = (AffiliationResultType, AffiliationRecommendationType, MatchesRecommendationType, UnifyResultType, GenderRecommendationType, GenderizeResultType)


########################################################################
# Schema Entry Points
########################################################################

sh_schema.query_type = Query
sh_schema.mutation_type = SortingHatMutation
sh_schema.subscription_type = None
