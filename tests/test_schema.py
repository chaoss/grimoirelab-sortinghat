#!/usr/bin/env python
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

import datetime
import unittest.mock
import json
import httpretty

import dateutil

import django.core.exceptions
import django.test
import django_rq.queues
import graphene
import graphene.test

from dateutil.tz import UTC

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from grimoirelab_toolkit.datetime import (datetime_utcnow,
                                          str_to_datetime,
                                          InvalidDateError)

from sortinghat.core import api
from sortinghat.core import db
from sortinghat.core.context import SortingHatContext
from sortinghat.core.log import TransactionsLog
from sortinghat.core.models import (Organization,
                                    Team,
                                    Group,
                                    Domain,
                                    Country,
                                    Individual,
                                    Identity,
                                    Profile,
                                    Enrollment,
                                    RecommenderExclusionTerm,
                                    Transaction,
                                    Operation,
                                    MergeRecommendation,
                                    GenderRecommendation,
                                    AffiliationRecommendation,
                                    ScheduledTask,
                                    Alias)
from sortinghat.core.schema import (SortingHatQuery,
                                    SortingHatMutation,
                                    parse_date_filter)

DUPLICATED_ORG_ERROR = "Organization 'Example' already exists in the registry"
DUPLICATED_DOM_ERROR = "Domain 'example.net' already exists in the registry"
DUPLICATED_TEAM_ERROR = "Team 'Example_team' already exists in the registry"
DUPLICATED_INDIVIDUAL = "Individual 'eda9f62ad321b1fbe5f283cc05e2484516203117' already exists in the registry"
DUPLICATED_ENROLLMENT_ERROR = "range date '{}'-'{}' is part of an existing range for {}"
DUPLICATED_RET_ERROR = "RecommenderExclusionTerm 'John Smith' already exists in the registry"
DUPLICATED_ALIAS_ERROR = "Alias 'Example Inc.' already exists in the registry"
TERM_EMPTY_ERROR = "'term' cannot be an empty string"
TERM_EXAMPLE_DOES_NOT_EXIST_ERROR = "John Smith not found in the registry"
RECOMMENDATION_MERGE_DOES_NOT_EXIST_ERROR = "MergeRecommendation matching query does not exist."
RECOMMENDATION_GENDER_DOES_NOT_EXIST_ERROR = "GenderRecommendation matching query does not exist."
RECOMMENDATION_AFFILIATION_DOES_NOT_EXIST_ERROR = "AffiliationRecommendation matching query does not exist."
NAME_EMPTY_ERROR = "'name' cannot be an empty string"
DOMAIN_NAME_EMPTY_ERROR = "'domain_name' cannot be an empty string"
TEAM_NAME_EMPTY_ERROR = "'team_name' cannot be an empty string"
SOURCE_EMPTY_ERROR = "'source' cannot be an empty string"
IDENTITY_EMPTY_DATA_ERROR = 'identity data cannot be empty'
FROM_UUID_IS_MK_ERROR = "'from_uuid' is an individual and it cannot be moved; use 'merge' instead"
FROM_UUID_EMPTY_ERROR = "'from_uuid' cannot be an empty string"
FROM_UUIDS_EMPTY_ERROR = "'from_uuids' cannot be an empty list"
TO_UUID_EMPTY_ERROR = "'to_uuid' cannot be an empty string"
FROM_UUID_TO_UUID_EQUAL_ERROR = "'to_uuid' e8284285566fdc1f41c8a22bb84a295fc3c4cbb3 cannot be part of 'from_uuids'"
UUID_EMPTY_ERROR = "'uuid' cannot be an empty string"
UUID_LOCKED_ERROR = "Individual e8284285566fdc1f41c8a22bb84a295fc3c4cbb3 is locked"
UUIDS_EMPTY_ERROR = "'uuids' cannot be an empty list"
ORG_DOES_NOT_EXIST_ERROR = "Organization matching query does not exist."
DOMAIN_DOES_NOT_EXIST_ERROR = "Domain matching query does not exist."
DOMAIN_NOT_FOUND_ERROR = "example.net not found in the registry"
INDIVIDUAL_DOES_NOT_EXIST_ERROR = "FFFFFFFFFFFFFFF not found in the registry"
ORGANIZATION_BITERGIA_DOES_NOT_EXIST_ERROR = "Bitergia not found in the registry"
ORGANIZATION_EXAMPLE_DOES_NOT_EXIST_ERROR = "Example not found in the registry"
ORGANIZATION_LIBRESOFT_DOES_NOT_EXIST_ERROR = "LibreSoft not found in the registry"
TEAM_EXAMPLE_DOES_NOT_EXIST_ERROR = "Example_team not found in the registry"
ENROLLMENT_DOES_NOT_EXIST_ERROR = "enrollment with range '2050-01-01 00:00:00+00:00'-'2060-01-01 00:00:00+00:00'"\
                                  " for Example not found in the registry"
PAGINATION_NO_RESULTS_ERROR = "That page contains no results"
PAGINATION_PAGE_LESS_THAN_ONE_ERROR = "That page number is less than 1"
PAGINATION_PAGE_SIZE_NEGATIVE_ERROR = "Negative indexing is not supported."
PAGINATION_PAGE_SIZE_ZERO_ERROR = "division by zero"
AUTHENTICATION_ERROR = "You do not have permission to perform this action"
PARSE_DATE_INVALID_DATE_ERROR = "{} is not a valid date"
PARSE_DATE_INVALID_FORMAT_ERROR = "Filter format is not valid"
INVALID_FILTER_DATE_ERROR = "Error in {} filter: {} is not a valid date"
INVALID_FILTER_FORMAT_ERROR = "Error in {} filter: Filter format is not valid"
INVALID_FILTER_RANGE_ERROR = "Error in {} filter: Date range is invalid. {}"
FROM_DATE_EMPTY_ERROR = "'from_date' cannot be empty"
TO_DATE_EMPTY_ERROR = "'to_date' cannot be empty"
BOTH_NEW_DATES_NONE_ERROR = "'new_from_date' and 'to_from_date' cannot be None at the same time"
EXECUTE_JOB_PERMISSION = "core.execute_job"
FROM_ORG_EMPTY_ERROR = "'from_org' cannot be an empty string"
TO_ORG_EMPTY_ERROR = "'to_org' cannot be an empty string"
EQUAL_ORGS_ERROR = "'to_org' cannot be the same as 'from_org'"
UNSUPPORTED_JOB_ERROR = "Job '{}' cannot be scheduled."
ALIAS_NOT_FOUND_ERROR = "Example Inc. not found in the registry"

# Test queries
SH_COUNTRIES_QUERY = """{
  countries {
    entities {
      code
      name
      alpha3
    }
  }
}"""
SH_COUNTRIES_CODE_QUERY_FILTER = """{
  countries (
    filters:{
      code: "%s"
    }
  ){
    entities {
      name
    }
  }
}"""
SH_COUNTRIES_TERM_QUERY_FILTER = """{
  countries (
    filters:{
      term: "%s"
    }
  ){
    entities {
      name
    }
  }
}"""
SH_COUNTRIES_QUERY_PAGINATION = """{
  countries (
    page: %d
    pageSize: %d
  ){
    entities {
      name
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_ORGS_QUERY = """{
  organizations {
    entities {
      name
      domains {
        domain
        isTopDomain
      }
      aliases {
        alias
      }
    }
  }
}"""
SH_ORGS_QUERY_FILTER = """{
  organizations (
    filters:{
      name:"%s"
    }
  ){
    entities {
      name
      domains {
        domain
        isTopDomain
      }
    }
  }
}"""
SH_ORGS_QUERY_TERM_FILTER = """{
  organizations (
    filters:{
      term:"%s"
    }
  ){
    entities {
      name
      domains {
        domain
        isTopDomain
      }
    }
  }
}"""
SH_ORGS_QUERY_PAGINATION = """{
  organizations (
    page: %d
    pageSize: %d
  ){
    entities {
      name
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_TEAMS_QUERY = """{
  teams {
    entities {
      name
      parentOrg {
        name
      }
    }
  }
}"""
SH_TEAMS_QUERY_FILTER = """{
  teams (
    filters:{
      name:"%s"
    }
  ){
    entities {
        name
        parentOrg {
          name
        }
      }
  }
}"""
SH_TEAMS_QUERY_TERM_FILTER = """{
  teams (
    filters:{
      term:"%s"
    }
  ){
    entities {
      name
      parentOrg {
        name
      }
    }
  }
}"""
SH_TEAMS_QUERY_ORG_FILTER = """{
  teams (
    filters:{
      organization:"%s"
    }
  ){
    entities {
      name
      parentOrg {
        name
      }
    }
  }
}"""
SH_TEAMS_QUERY_PARENT_FILTER = """{
  teams (
    filters:{
      parent:"%s"
    }
  ){
    entities {
      name
      parentOrg {
        name
      }
    }
  }
}"""
SH_TEAMS_QUERY_PARENT_ORG_FILTERS = """{
  teams (
      filters:{
        parent:"%s"
        organization:"%s"
      }
    ){
      entities {
        name
        parentOrg {
          name
        }
      }
    }
}"""
SH_TEAMS_QUERY_PAGINATION = """{
  teams (
    page: %d
    pageSize: %d
  ){
    entities {
      name
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_SUBTEAMS_QUERY = """{
  teams {
    entities {
      name
      parentOrg {
        name
      }
      subteams {
        name
        subteams {
          name
        }
      }
    }
  }
}"""
SH_GROUPS_QUERY = """{
  groups {
    entities {
      name
      parentOrg {
        name
      }
    }
  }
}"""
SH_SUBGROUPS_QUERY = """{
  groups {
    entities {
      name
      parentOrg {
        name
      }
      subteams {
        name
        subteams {
          name
        }
      }
    }
  }
}"""
SH_GROUPS_QUERY_FILTER = """{
  groups (
    filters: {
      name: "%s"
    }
  ){
    entities {
      name
    }
  }
}"""
SH_GROUPS_QUERY_TERM_FILTER = """{
  groups (
    filters:{
      term:"%s"
    }
  ){
    entities {
      name
      parentOrg {
        name
      }
    }
  }
}"""
SH_GROUPS_QUERY_PARENT_FILTER = """{
  groups (
    filters:{
      parent:"%s"
    }
  ){
    entities {
      name
      parentOrg {
        name
      }
    }
  }
}"""
SH_GROUPS_QUERY_PAGINATION = """{
  groups (
    page: %d
    pageSize: %d
  ){
    entities {
      name
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_INDIVIDUALS_QUERY = """{
  individuals {
    entities {
      mk
      isLocked
      profile {
        name
        email
        gender
        isBot
        country {
          code
          name
        }
      }
      identities {
        uuid
        name
        email
        username
        source
      }
      enrollments {
        group {
          name
        }
        start
        end
      }
    }
  }
}"""
SH_INDIVIDUAL_MERGE_REC_QUERY = """{
  individuals {
    entities {
      mk
      matchRecommendationSet {
        id
        individual {
          mk
        }
      }
    }
  }
}"""
SH_INDIVIDUALS_UUID_FILTER = """{
  individuals(filters: {uuid: "%s"}) {
    entities {
      mk
      isLocked
      profile {
        name
        email
        gender
        isBot
        country {
          code
          name
        }
      }
      identities {
        uuid
        name
        email
        username
        source
      }
      enrollments {
        group {
          name
        }
        start
        end
      }
    }
  }
}"""
SH_INDIVIDUALS_TERM_FILTER = """{
  individuals(filters: {term: "%s"}) {
    entities {
      mk
      isLocked
      profile {
        name
        email
        gender
        isBot
        country {
          code
          name
        }
      }
      identities {
        uuid
        name
        email
        username
        source
      }
      enrollments {
        group {
          name
        }
        start
        end
      }
    }
  }
}"""
SH_INDIVIDUALS_LOCKED_FILTER = """{
  individuals(filters: {isLocked: true}) {
    entities {
      mk
      isLocked
      profile {
        name
        email
        gender
        isBot
        country {
          code
          name
        }
      }
      identities {
        uuid
        name
        email
        username
        source
      }
      enrollments {
        group {
          name
        }
        start
        end
      }
    }
  }
}"""
SH_INDIVIDUALS_BOT_FILTER = """{
  individuals(filters: {isBot: true}) {
    entities {
      mk
      profile {
        isBot
      }
    }
  }
}"""
SH_INDIVIDUALS_BOT_FILTER_FALSE = """{
  individuals(filters: {isBot: false}) {
    entities {
      mk
      profile {
        isBot
      }
    }
  }
}"""
SH_INDIVIDUALS_GENDER_FILTER = """{
  individuals(filters: {gender: "%s"}) {
    entities {
      mk
      profile {
        gender
      }
    }
  }
}
"""
SH_INDIVIDUALS_COUNTRY_FILTER = """{
  individuals(filters: {country: "%s"}) {
    entities {
      profile {
        country {
          code
          name
          alpha3
        }
      }
    }
  }
}"""
SH_INDIVIDUALS_SOURCE_FILTER = """{
    individuals(filters: {source: "%s"}) {
      entities {
        mk
        identities {
          source
        }
      }
    }
}"""
SH_INDIVIDUALS_ENROLLMENT_FILTER = """{
    individuals(filters: {enrollment: "%s"}) {
      entities {
        mk
        enrollments {
          group {
            name
          }
        }
      }
    }
}"""
SH_INDIVIDUALS_ENROLLMENT_TEAM_FILTER = """{
    individuals(filters: {enrollment: "%s", enrollmentParentOrg: "Bitergia"}) {
      entities {
        mk
        enrollments {
          group {
            name
            type
            parentOrg {
              name
            }
          }
        }
      }
    }
}"""
SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER = """{
    individuals(filters: {enrollmentDate: "%s"}) {
      entities {
        mk
        enrollments {
          start
          end
        }
      }
    }
}"""
SH_INDIVIDUALS_IS_ENROLLED_FILTER = """{
    individuals(filters: {isEnrolled: %s}) {
      entities {
        mk
        enrollments {
          group {
            name
          }
        }
      }
    }
}"""
SH_INDIVIDUALS_LAST_UPDATED_FILTER = """{
  individuals(filters: {lastUpdated: "%s"}) {
    entities {
      mk
      isLocked
      profile {
        name
        email
        gender
        isBot
        country {
          code
          name
        }
      }
      identities {
        uuid
        name
        email
        username
        source
      }
      enrollments {
        group {
          name
        }
        start
        end
      }
    }
  }
}"""
SH_INDIVIDUALS_UUID_PAGINATION = """{
  individuals(
    page: %d
    pageSize: %d
  ){
    entities {
      mk
      isLocked
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}
"""
SH_INDIVIDUALS_ORDER_BY = """{
  individuals(orderBy: "%s") {
    entities {
      mk
    }
  }
}"""
SH_TRANSACTIONS_QUERY = """{
  transactions {
    entities {
      name
      createdAt
      tuid
      isClosed
      closedAt
      authoredBy
    }
  }
}"""
SH_TRANSACTIONS_QUERY_FILTER = """{
  transactions(
    filters: {
      tuid: "%s",
      name: "%s",
      fromDate: "%s",
      authoredBy: "%s"
    }
  ){
    entities {
      name
      createdAt
      tuid
      isClosed
      closedAt
      authoredBy
    }
  }
}"""
SH_TRANSACTIONS_QUERY_PAGINATION = """{
  transactions(
    page: %d
    pageSize: %d
  ){
    entities {
      name
      createdAt
      tuid
      isClosed
      closedAt
      authoredBy
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_OPERATIONS_QUERY = """{
  operations {
    entities {
      ouid
      opType
      entityType
      target
      timestamp
      args
      trx{
        name
        createdAt
        tuid
      }
    }
  }
}"""
SH_OPERATIONS_QUERY_FILTER = """{
  operations(
    filters:{
      opType:"%s",
      entityType:"%s",
      fromDate:"%s"
    }
  ){
    entities {
      ouid
      opType
      entityType
      target
      timestamp
      args
      trx{
        name
        createdAt
        tuid
      }
    }
  }
}"""
SH_OPERATIONS_QUERY_PAGINATION = """{
  operations(
    page: %d
    pageSize: %d
  ){
    entities{
      ouid
      opType
      entityType
      target
      timestamp
      args
      trx{
        name
        createdAt
        tuid
      }
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_OPERATIONS_QUERY_PAGINATION_NO_PAGE = """{
  operations(
    pageSize: %d
  ){
    entities{
      ouid
      opType
      entityType
      target
      timestamp
      args
      trx{
        name
        createdAt
        tuid
      }
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_OPERATIONS_QUERY_PAGINATION_NO_PAGE_SIZE = """{
  operations(
    page: %d
  ){
    entities{
      ouid
      opType
      entityType
      target
      timestamp
      args
      trx{
        name
        createdAt
        tuid
      }
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_JOB_QUERY_AFFILIATE = """{
  job(
    jobId:"%s"
  ){
    jobId
    jobType
    status
    errors
    result {
      __typename
      ... on AffiliationResultType {
          uuid
          organizations
      }
    }
  }
}
"""
SH_JOB_QUERY_RECOMMEND_AFFILIATIONS = """{
  job(
    jobId:"%s"
  ){
    jobId
    jobType
    status
    errors
    result {
      __typename
      ... on AffiliationRecommendationType {
          uuid
          organizations
      }
    }
  }
}
"""
SH_JOB_QUERY_RECOMMEND_MATCHES = """{
  job(
    jobId:"%s"
  ){
    jobId
    jobType
    status
    errors
    result {
      __typename
      ... on MatchesRecommendationType {
          uuid
          matches
      }
    }
  }
}
"""
SH_JOB_QUERY_UNIFY = """{
  job(
    jobId:"%s"
  ){
    jobId
    jobType
    status
    errors
    result {
      __typename
      ... on UnifyResultType {
          merged
      }
    }
  }
}"""
SH_JOBS_QUERY = """{
  jobs(page: 1) {
    entities {
      jobId
      jobType
      status
      errors
      result {
        ... on AffiliationRecommendationType {
            uuid
        }
      }
    }
  }
}
"""
SH_JOBS_QUERY_PAGINATION = """{
  jobs(page: %d, pageSize: %d) {
    entities {
      jobId
      jobType
      status
      errors
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}
"""
SH_JOB_QUERY_RECOMMEND_GENDER = """{
  job(
    jobId:"%s"
  ){
    jobId
    jobType
    status
    errors
    result {
      __typename
      ... on GenderRecommendationType {
        uuid
        gender
        accuracy
      }
    }
  }
}
"""
SH_JOB_QUERY_GENDERIZE = """{
  job(
    jobId:"%s"
  ){
    jobId
    jobType
    status
    errors
    result {
      __typename
      ... on GenderizeResultType {
        uuid
        gender
      }
    }
  }
}
"""
SH_RET_QUERY = """{
  recommenderExclusionTerms {
    entities {
      term
    }
  }
}"""
SH_RET_QUERY_PAGINATION = """{
  recommenderExclusionTerms (
    page: %d
    pageSize: %d
  ){
    entities {
      term
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_AFF_REC_QUERY = """{
  recommendedAffiliations {
    entities {
      individual {
        mk
      }
      organization {
        name
      }
    }
  }
}"""
SH_AFF_REC_QUERY_PAGINATION = """{
  recommendedAffiliations (
    page: %d
    pageSize: %d
  ){
    entities {
      individual {
        mk
      }
      organization {
        name
      }
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_AFF_REC_FILTER = """{
  recommendedAffiliations(filters: {isApplied: %s}) {
    entities {
      individual {
        mk
      }
      organization {
        name
      }
      applied
    }
  }
}"""
SH_MERGE_REC_QUERY = """{
  recommendedMerge {
    entities {
      individual1 {
        mk
      }
      individual2 {
        mk
      }
    }
  }
}"""
SH_MERGE_REC_QUERY_PAGINATION = """{
  recommendedMerge (
    page: %d
    pageSize: %d
  ){
    entities {
      individual1 {
        mk
      }
      individual2 {
        mk
      }
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_MERGE_REC_FILTER = """{
  recommendedMerge(filters: {isApplied: %s}) {
    entities {
      individual1 {
        mk
      }
      individual2 {
        mk
      }
    }
  }
}"""
SH_GENDER_REC_QUERY = """{
  recommendedGender {
    entities {
      individual {
        mk
      }
      gender
      accuracy
    }
  }
}"""
SH_GENDER_REC_QUERY_PAGINATION = """{
  recommendedGender (
    page: %d
    pageSize: %d
  ){
    entities {
      individual {
        mk
      }
      gender
      accuracy
    }
    pageInfo{
      page
      pageSize
      numPages
      hasNext
      hasPrev
      startIndex
      endIndex
      totalResults
    }
  }
}"""
SH_GENDER_REC_FILTER = """{
  recommendedGender(filters: {isApplied: %s}) {
    entities {
      individual {
        mk
      }
      gender
      accuracy
    }
  }
}"""

# API endpoint to obtain a context for executing queries
GRAPHQL_ENDPOINT = '/api/'


class TestQuery(SortingHatQuery, graphene.ObjectType):
    pass


class TestQueryPagination(django.test.TestCase):

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        api.add_organization(self.ctx, 'Example')

        api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.update_profile(self.ctx,
                           uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                           name='J. Smith', email='jsmith@example',
                           gender='male', gender_acc=75)
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2017, 6, 1))

        # Create an additional transaction controlling input values
        self.timestamp = datetime_utcnow()  # This will be used as a filter
        self.trx = Transaction(name='test_trx',
                               tuid='012345abcdef',
                               created_at=datetime_utcnow())
        self.trx.save()

    def test_pagination(self):
        """Check if the expected page and number of results is returned"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (2, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        entities = executed['data']['operations']['entities']
        self.assertEqual(len(entities), 2)

        op1 = entities[0]
        self.assertEqual(op1['opType'], Operation.OpType.UPDATE.value)
        self.assertEqual(op1['entityType'], 'profile')
        self.assertEqual(op1['target'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        op2 = entities[1]
        self.assertEqual(op2['opType'], Operation.OpType.ADD.value)
        self.assertEqual(op2['entityType'], 'identity')
        self.assertEqual(op2['target'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        pag_data = executed['data']['operations']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 2)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 3)
        self.assertTrue(pag_data['hasNext'])
        self.assertTrue(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 3)
        self.assertEqual(pag_data['endIndex'], 4)
        self.assertEqual(pag_data['totalResults'], 6)

    def test_page_not_set(self):
        """Check if returns the first page when `page` is not set"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION_NO_PAGE % 2
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        entities = executed['data']['operations']['entities']
        self.assertEqual(len(entities), 2)

        pag_data = executed['data']['operations']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 3)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 6)

    def test_page_exceeded(self):
        """Check if it fails when `page` is greater than the number of pages"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (30, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, PAGINATION_NO_RESULTS_ERROR)

    def test_page_negative(self):
        """Check if it fails when `page` is a negative number"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (-1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, PAGINATION_PAGE_LESS_THAN_ONE_ERROR)

    def test_page_zero(self):
        """Check if it fails when `page` is set to `0`"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (0, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, PAGINATION_PAGE_LESS_THAN_ONE_ERROR)

    def test_page_size_not_set(self):
        """Check if it takes the default value from settings when `pageSize` is not set"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION_NO_PAGE_SIZE % 1
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        pag_data = executed['data']['operations']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], settings.SORTINGHAT_API_PAGE_SIZE)
        self.assertEqual(pag_data['totalResults'], 6)

    def test_page_size_exceeded(self):
        """Check if returns all the elements when `pageSize` is greater than number of results"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (1, 30)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        pag_data = executed['data']['operations']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 30)
        self.assertEqual(pag_data['numPages'], 1)
        self.assertFalse(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 6)
        self.assertEqual(pag_data['totalResults'], 6)

    def test_page_size_negative(self):
        """Check if it fails when `pageSize` is a negative number"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (1, -2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, PAGINATION_PAGE_SIZE_NEGATIVE_ERROR)

    def test_page_size_zero(self):
        """Check if it fails when `pageSize` is set to `0`"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (1, 0)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, PAGINATION_PAGE_SIZE_ZERO_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        test_query = SH_OPERATIONS_QUERY_PAGINATION % (2, 2)
        executed = client.execute(test_query,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)

    def test_authentication_disabled(self):
        """Check if it doesn't fail when authentication is disabled"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (2, 2)

        # Check it raises the error
        with self.settings(SORTINGHAT_AUTHENTICATION_REQUIRED=True):
            executed = client.execute(test_query,
                                      context_value=context_value)
            msg = executed['errors'][0]['message']
            self.assertEqual(msg, AUTHENTICATION_ERROR)

        # Check it doesn't raise the error
        with self.settings(SORTINGHAT_AUTHENTICATION_REQUIRED=False):
            executed = client.execute(test_query,
                                      context_value=context_value)

            entities = executed['data']['operations']['entities']
            self.assertEqual(len(entities), 2)


class TestMutations(SortingHatMutation):
    pass


schema = graphene.Schema(query=TestQuery,
                         mutation=TestMutations)


class TestQueryCountries(django.test.TestCase):
    """Unit tests for country queries"""

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_countries(self):
        """Check if it returns the registry of countries"""

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')
        Country.objects.create(code='ES',
                               name='Spain',
                               alpha3='ESP')
        Country.objects.create(code='GB',
                               name='United Kingdom',
                               alpha3='GBR')

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_COUNTRIES_QUERY,
                                  context_value=self.context_value)

        cs = executed['data']['countries']['entities']
        self.assertEqual(len(cs), 3)

        country0 = cs[0]
        self.assertEqual(country0['name'], 'Spain')
        self.assertEqual(country0['code'], 'ES')
        self.assertEqual(country0['alpha3'], 'ESP')

        country1 = cs[1]
        self.assertEqual(country1['name'], 'United Kingdom')
        self.assertEqual(country1['code'], 'GB')
        self.assertEqual(country1['alpha3'], 'GBR')

        country2 = cs[2]
        self.assertEqual(country2['name'], 'United States of America')
        self.assertEqual(country2['code'], 'US')
        self.assertEqual(country2['alpha3'], 'USA')

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_COUNTRIES_QUERY,
                                  context_value=self.context_value)

        cs = executed['data']['countries']['entities']
        self.assertListEqual(cs, [])

    def test_filter_code_registry(self):
        """Check whether it returns the country searched when using code filter"""

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')
        Country.objects.create(code='ES',
                               name='Spain',
                               alpha3='ESP')
        Country.objects.create(code='GB',
                               name='United Kingdom',
                               alpha3='GBR')

        client = graphene.test.Client(schema)
        test_query = SH_COUNTRIES_CODE_QUERY_FILTER % 'ES'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        cs = executed['data']['countries']['entities']
        self.assertEqual(len(cs), 1)

        country = cs[0]
        self.assertEqual(country['name'], 'Spain')

        # No code found produces an empty response
        test_query = SH_COUNTRIES_CODE_QUERY_FILTER % 'ABC'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        cs = executed['data']['countries']['entities']
        self.assertListEqual(cs, [])

    def test_filter_term_registy(self):
        """Check whether it returns the countries searched when using term filter"""

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')
        Country.objects.create(code='ES',
                               name='Spain',
                               alpha3='ESP')
        Country.objects.create(code='GB',
                               name='United Kingdom',
                               alpha3='GBR')

        client = graphene.test.Client(schema)
        test_query = SH_COUNTRIES_TERM_QUERY_FILTER % 'ited'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        cs = executed['data']['countries']['entities']
        self.assertEqual(len(cs), 2)

        country = cs[0]
        self.assertEqual(country['name'], 'United Kingdom')

        country = cs[1]
        self.assertEqual(country['name'], 'United States of America')

        # Queries are not case sensitive
        client = graphene.test.Client(schema)
        test_query = SH_COUNTRIES_TERM_QUERY_FILTER % 'spa'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        cs = executed['data']['countries']['entities']
        self.assertEqual(len(cs), 1)

        country = cs[0]
        self.assertEqual(country['name'], 'Spain')

        # No term found produces an empty response
        test_query = SH_COUNTRIES_TERM_QUERY_FILTER % 'ABCD'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        cs = executed['data']['countries']['entities']
        self.assertListEqual(cs, [])

    def test_pagination(self):
        """Check whether it returns the countries searched when using pagination"""

        cs0 = Country.objects.create(code='US',
                                     name='United States of America',
                                     alpha3='USA')
        cs1 = Country.objects.create(code='ES',
                                     name='Spain',
                                     alpha3='ESP')
        cs2 = Country.objects.create(code='GB',
                                     name='United Kingdom',
                                     alpha3='GBR')

        client = graphene.test.Client(schema)
        test_query = SH_COUNTRIES_QUERY_PAGINATION % (1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        cs = executed['data']['countries']['entities']
        self.assertEqual(len(cs), 2)

        # As countries are sorted by name, the first two will be cs1 and cs2
        country = cs[0]
        self.assertEqual(country['name'], cs1.name)

        country = cs[1]
        self.assertEqual(country['name'], cs2.name)

        pag_data = executed['data']['countries']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 2)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 3)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_COUNTRIES_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestQueryOrganizations(django.test.TestCase):
    """Unit tests for organization queries"""

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_organizations(self):
        """Check if it returns the registry of organizations"""

        org = Organization.add_root(name='Example')
        Domain.objects.create(domain='example.com', organization=org)
        Domain.objects.create(domain='example.org', organization=org)
        Alias.objects.create(alias='Example Inc.', organization=org)
        Alias.objects.create(alias='Example Ltd.', organization=org)
        org = Organization.add_root(name='Bitergia')
        Alias.objects.create(alias='Bitergium', organization=org)
        Domain.objects.create(domain='bitergia.com', organization=org)
        _ = Organization.add_root(name='LibreSoft')

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_ORGS_QUERY,
                                  context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
        self.assertEqual(len(orgs), 3)

        org1 = orgs[0]
        self.assertEqual(org1['name'], 'Bitergia')
        self.assertEqual(len(org1['domains']), 1)
        self.assertEqual(len(org1['aliases']), 1)

        org2 = orgs[1]
        self.assertEqual(org2['name'], 'Example')
        self.assertEqual(len(org2['domains']), 2)
        self.assertEqual(len(org2['aliases']), 2)

        org3 = orgs[2]
        self.assertEqual(org3['name'], 'LibreSoft')
        self.assertEqual(len(org3['domains']), 0)
        self.assertEqual(len(org3['aliases']), 0)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_ORGS_QUERY,
                                  context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
        self.assertListEqual(orgs, [])

    def test_filter_registry(self):
        """Check whether it returns the organization searched when using name filter"""

        org1 = Organization.add_root(name='Example')
        org2 = Organization.add_root(name='Bitergia')
        org3 = Organization.add_root(name='LibreSoft')

        client = graphene.test.Client(schema)
        test_query = SH_ORGS_QUERY_FILTER % 'Bitergia'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
        self.assertEqual(len(orgs), 1)

        # As organizations are sorted by name, the first one will be org2
        org = orgs[0]
        self.assertEqual(org['name'], org2.name)

    def test_filter_registry_alias(self):
        """Check whether it returns the organization with a matching alias when using name filter"""

        org1 = Organization.add_root(name='Example')
        org2 = Organization.add_root(name='Bitergia')
        org3 = Organization.add_root(name='LibreSoft')

        Alias.objects.create(alias='Example Inc.', organization=org1)

        client = graphene.test.Client(schema)
        test_query = SH_ORGS_QUERY_FILTER % 'Example Inc.'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
        self.assertEqual(len(orgs), 1)

        # As organizations are sorted by name, the first one will be org2
        org = orgs[0]
        self.assertEqual(org['name'], org1.name)

    def test_filter_non_exist_registry(self):
        """Check whether it returns an empty list when searched with a non existing organization"""

        org1 = Organization.add_root(name='Example')
        org2 = Organization.add_root(name='Bitergia')
        org3 = Organization.add_root(name='LibreSoft')

        client = graphene.test.Client(schema)
        test_query = SH_ORGS_QUERY_FILTER % 'Test'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
        self.assertListEqual(orgs, [])

    def test_filter_term(self):
        """Check whether it returns the organization searched when using term filter"""

        org1 = Organization.add_root(name='Example')
        org2 = Organization.add_root(name='Bitergia')
        org3 = Organization.add_root(name='LibreSoft')
        Domain.objects.create(domain='domain1.com', organization=org1)
        Domain.objects.create(domain='domain2.com', organization=org2)
        Domain.objects.create(domain='domain3.com', organization=org3)

        # Tests

        # Test 'Bitergia' should return one of the organizations
        client = graphene.test.Client(schema)
        test_query = SH_ORGS_QUERY_TERM_FILTER % 'Bitergia'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
        self.assertEqual(len(orgs), 1)

        org = orgs[0]
        self.assertEqual(org['name'], org2.name)

        # Test 'domain' should return all 3 organizations
        test_query = SH_ORGS_QUERY_TERM_FILTER % 'domain'
        executed = client.execute(test_query, context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
        self.assertEqual(len(orgs), 3)

        # Test '123' shouldn't return any organizations
        test_query = SH_ORGS_QUERY_TERM_FILTER % '123'
        executed = client.execute(test_query, context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
        self.assertEqual(len(orgs), 0)

    def test_pagination(self):
        """Check whether it returns the organizations searched when using pagination"""

        org1 = Organization.add_root(name='Example')
        org2 = Organization.add_root(name='Bitergia')
        org3 = Organization.add_root(name='LibreSoft')

        client = graphene.test.Client(schema)
        test_query = SH_ORGS_QUERY_PAGINATION % (1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        orgs = executed['data']['organizations']['entities']
        self.assertEqual(len(orgs), 2)

        # As organizations are sorted by name, the first two will be org2 and org1
        org = orgs[0]
        self.assertEqual(org['name'], org2.name)

        org = orgs[1]
        self.assertEqual(org['name'], org1.name)

        pag_data = executed['data']['organizations']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 2)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 3)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_ORGS_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestQueryTeams(django.test.TestCase):
    """Unit tests for team queries"""

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user
        self.ctx = SortingHatContext(self.user)

    def test_teams(self):
        """Check if it returns the registry of teams"""

        example_org = api.add_organization(self.ctx, 'Example')
        api.add_team(self.ctx, 'Example_team', organization='Example')
        bitergia_org = api.add_organization(self.ctx, 'Bitergia')
        team = api.add_team(self.ctx, 'Bitergia_team', organization='Bitergia')
        subteam = api.add_team(self.ctx, 'Bitergia_subteam', organization='Bitergia')
        noorgterm = api.add_team(self.ctx, 'Mozilla')

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_TEAMS_QUERY,
                                  context_value=self.context_value)

        # show only top level teams
        teams = executed['data']['teams']['entities']
        self.assertEqual(len(teams), 3)

        teams_in_example_org = example_org.teams.all()
        self.assertEqual(len(teams_in_example_org), 1)

        teams_in_bitergia_org = bitergia_org.teams.all()
        self.assertEqual(len(teams_in_bitergia_org), 2)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_TEAMS_QUERY,
                                  context_value=self.context_value)

        orgs = executed['data']['teams']['entities']
        self.assertListEqual(orgs, [])

    def test_subteams(self):
        chaoss_org = api.add_organization(self.ctx, 'Grimoirelab')
        percevalteam = api.add_team(self.ctx,
                                    'Perceval',
                                    organization='Grimoirelab')
        percevalsubteam1 = api.add_team(self.ctx,
                                        'Perceval Slack',
                                        organization='Grimoirelab',
                                        parent_name='Perceval')
        percevalsubteam2 = api.add_team(self.ctx,
                                        'Perceval Git',
                                        organization='Grimoirelab',
                                        parent_name='Perceval')
        percevalsubteam3 = api.add_team(self.ctx,
                                        'Perceval Gitlab',
                                        organization='Grimoirelab',
                                        parent_name='Perceval Git')

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_SUBTEAMS_QUERY,
                                  context_value=self.context_value)

        # show only top level teams
        teams = executed['data']['teams']['entities']
        self.assertEqual(len(teams), 1)

        # check subteams
        team = executed['data']['teams']['entities'][0]
        subteams = team['subteams']
        self.assertEqual(len(subteams), 2)
        # subteams are sorted by name
        self.assertEqual(subteams[0]['name'], percevalsubteam2.name)
        self.assertEqual(subteams[1]['name'], percevalsubteam1.name)

        # test another level of subteams
        self.assertEqual(len(subteams[0]['subteams']), 1)
        self.assertEqual(len(subteams[1]['subteams']), 0)
        childteam = subteams[0]['subteams'][0]
        self.assertEqual(childteam['name'], percevalsubteam3.name)

    def test_filter_registry(self):
        """Check whether it returns the teams searched when using name filter"""

        team = Team.add_root(name='Example_team1')

        client = graphene.test.Client(schema)
        test_query = SH_TEAMS_QUERY_FILTER % 'Example_team1'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        teams = executed['data']['teams']['entities']
        self.assertEqual(len(teams), 1)

        self.assertEqual(teams[0]['name'], team.name)

    def test_filter_non_exist_registry(self):
        """Check whether it returns an empty list when searched with a non existing team"""

        api.add_organization(self.ctx, 'Example')
        api.add_team(self.ctx, 'Example_team1', organization='Example')

        client = graphene.test.Client(schema)
        test_query = SH_TEAMS_QUERY_FILTER % 'Example'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        teams = executed['data']['teams']['entities']
        self.assertListEqual(teams, [])

    def test_filter_term(self):
        """Check whether it returns the teams searched when using term filter"""

        api.add_organization(self.ctx, 'Example')
        team1 = api.add_team(self.ctx, 'team1', organization='Example')
        api.add_team(self.ctx, 'team2', organization='Example')
        api.add_team(self.ctx, 'team3', organization='Example')

        client = graphene.test.Client(schema)

        # Test 'team1' should return one of the organizations
        test_query = SH_TEAMS_QUERY_TERM_FILTER % 'team1'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        team = executed['data']['teams']['entities']
        self.assertEqual(len(team), 1)

        team = team[0]
        self.assertEqual(team['name'], team1.name)

        # Test 'team' should return all 3 teams
        test_query = SH_TEAMS_QUERY_TERM_FILTER % 'team'
        executed = client.execute(test_query, context_value=self.context_value)

        teams = executed['data']['teams']['entities']
        self.assertEqual(len(teams), 3)

        # Test '123' shouldn't return any organizations
        test_query = SH_TEAMS_QUERY_TERM_FILTER % '123'
        executed = client.execute(test_query, context_value=self.context_value)

        teams = executed['data']['teams']['entities']
        self.assertEqual(len(teams), 0)

    def test_filter_organization(self):
        """Check whether it returns the correct teams when using organization filter"""

        example_org = api.add_organization(self.ctx, 'Example')
        example_team = api.add_team(self.ctx, 'example_team', organization='Example')
        example_subteam = api.add_team(self.ctx,
                                       'example_subteam',
                                       organization='Example',
                                       parent_name='example_team')
        api.add_organization(self.ctx, 'Bitergia')
        api.add_team(self.ctx, 'bitergia_team', organization='Bitergia')

        client = graphene.test.Client(schema)

        # Test 'Example' as organization should return 'Example_team'
        test_query = SH_TEAMS_QUERY_ORG_FILTER % 'Example'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        # show only top level teams in 'Example'
        teams = executed['data']['teams']['entities']
        self.assertEqual(len(teams), 1)

        team = teams[0]
        self.assertEqual(team['name'], example_team.name)
        self.assertEqual(team['parentOrg']['name'], example_org.name)

    def test_filter_parent(self):
        """Check whether it returns the correct teams when using parent filter"""

        team = api.add_team(self.ctx, 'example_team')
        subteam1 = api.add_team(self.ctx, 'subteam1', parent_name='example_team')
        subteam2 = api.add_team(self.ctx, 'subteam2', parent_name='subteam1')

        client = graphene.test.Client(schema)

        # Test 'example_team' should return 'subteam1'
        test_query = SH_TEAMS_QUERY_PARENT_FILTER % 'example_team'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        teams = executed['data']['teams']['entities']
        self.assertEqual(len(teams), 1)

        # Teams are sorted by name
        team = teams[0]
        self.assertEqual(team['name'], subteam1.name)

    def test_filter_parent_and_organization(self):
        """Check whether it returns the correct teams when using parent filter
           for a particular organization"""

        example_org = api.add_organization(self.ctx, 'Example')
        bitergia_org = api.add_organization(self.ctx, 'Bitergia')

        example_team = api.add_team(self.ctx, 'example_team', organization='Example')
        example_subteam = api.add_team(self.ctx, 'example_subteam',
                                       organization='Example',
                                       parent_name='example_team')

        _ = api.add_team(self.ctx, 'example_team', organization='Bitergia')

        client = graphene.test.Client(schema)
        test_query = SH_TEAMS_QUERY_PARENT_ORG_FILTERS % ('example_team', 'Example')
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        teams = executed['data']['teams']['entities']
        self.assertEqual(len(teams), 1)

        team = teams[0]
        self.assertEqual(team['name'], example_subteam.name)

    def test_pagination(self):
        """Check whether it returns the teams searched when using pagination"""

        example_org = api.add_organization(self.ctx, 'Example')
        team1 = api.add_team(self.ctx, 'team1', organization='Example')
        team2 = api.add_team(self.ctx, 'team2', organization='Example')
        api.add_team(self.ctx, 'team3', organization='Example')

        client = graphene.test.Client(schema)
        test_query = SH_TEAMS_QUERY_PAGINATION % (1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        teams = executed['data']['teams']['entities']
        self.assertEqual(len(teams), 2)

        # As organizations are sorted by name, the first two will be org2 and org1
        team = teams[0]
        self.assertEqual(team['name'], team1.name)

        team = teams[1]
        self.assertEqual(team['name'], team2.name)

        pag_data = executed['data']['teams']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 2)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 3)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_TEAMS_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestQueryGroups(django.test.TestCase):
    """Unit tests for groups queries"""

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user
        self.ctx = SortingHatContext(self.user)

    def test_groups(self):
        """Check if it returns the registry of groups"""

        api.add_organization(self.ctx, name='Example')
        api.add_team(self.ctx, 'Example_team', organization='Example')
        no_org_group = api.add_team(self.ctx, 'Example_team')
        api.add_team(self.ctx, 'Example_subteam', parent_name='Example_team')

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_GROUPS_QUERY,
                                  context_value=self.context_value)

        # show only top level groups that arent linked to any organization
        groups = executed['data']['groups']['entities']
        self.assertEqual(len(groups), 1)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_GROUPS_QUERY,
                                  context_value=self.context_value)

        orgs = executed['data']['groups']['entities']
        self.assertListEqual(orgs, [])

    def test_subteams(self):
        """Check if it returns the subteams of groups"""

        percevalteam = api.add_team(self.ctx, 'Perceval')
        percevalsubteam1 = api.add_team(self.ctx, 'Perceval Slack', parent_name='Perceval')
        percevalsubteam2 = api.add_team(self.ctx, 'Perceval Git', parent_name='Perceval')
        percevalsubteam3 = api.add_team(self.ctx, 'Perceval Gitlab', parent_name='Perceval Git')

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_SUBGROUPS_QUERY,
                                  context_value=self.context_value)

        # show only top level groups
        groups = executed['data']['groups']['entities']
        self.assertEqual(len(groups), 1)

        # check subteams
        group = executed['data']['groups']['entities'][0]
        subteams = group['subteams']
        self.assertEqual(len(subteams), 2)
        # subteams are sorted by name
        self.assertEqual(subteams[0]['name'], percevalsubteam2.name)
        self.assertEqual(subteams[1]['name'], percevalsubteam1.name)

        # test another level of groups
        self.assertEqual(len(subteams[0]['subteams']), 1)
        self.assertEqual(len(subteams[1]['subteams']), 0)
        childteam = subteams[0]['subteams'][0]
        self.assertEqual(childteam['name'], percevalsubteam3.name)

    def test_filter_registry(self):
        """Check whether it returns the groups searched when using name filter"""

        group = Team.add_root(name='Example_group')

        client = graphene.test.Client(schema)
        test_query = SH_GROUPS_QUERY_FILTER % 'Example_group'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        groups = executed['data']['groups']['entities']
        self.assertEqual(len(groups), 1)

        self.assertEqual(groups[0]['name'], group.name)

    def test_filter_non_exist_registry(self):
        """Check whether it returns an empty list when searched with a non existing team"""

        Team.add_root(name='Example_team1', parent_org=None)

        client = graphene.test.Client(schema)
        test_query = SH_GROUPS_QUERY_FILTER % 'Example'
        executed = client.execute(test_query,
                                  context_value=self.context_value)
        groups = executed['data']['groups']['entities']
        self.assertListEqual(groups, [])

    def test_filter_term(self):
        """Check whether it returns the groups searched when using term filter"""

        group1 = Team.add_root(name='team1', parent_org=None)
        Team.add_root(name='team2', parent_org=None)
        Team.add_root(name='team3', parent_org=None)

        client = graphene.test.Client(schema)

        # Test 'team1' should return one of the organizations
        test_query = SH_GROUPS_QUERY_TERM_FILTER % 'team1'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        group = executed['data']['groups']['entities']
        self.assertEqual(len(group), 1)

        group = group[0]
        self.assertEqual(group['name'], group1.name)

        # Test 'team' should return all 3 groups
        test_query = SH_GROUPS_QUERY_TERM_FILTER % 'team'
        executed = client.execute(test_query, context_value=self.context_value)

        groups = executed['data']['groups']['entities']
        self.assertEqual(len(groups), 3)

        # Test '123' shouldn't return any organizations
        test_query = SH_GROUPS_QUERY_TERM_FILTER % '123'
        executed = client.execute(test_query, context_value=self.context_value)

        teams = executed['data']['groups']['entities']
        self.assertEqual(len(teams), 0)

    def test_filter_parent(self):
        """Check whether it returns the correct groups when using parent filter"""

        team = Team.add_root(name='example_team')
        subteam1 = team.add_child(name='subteam1')
        subteam2 = subteam1.add_child(name='subteam2')

        client = graphene.test.Client(schema)

        # Test 'example_team' should return 'subteam1'
        test_query = SH_GROUPS_QUERY_PARENT_FILTER % 'example_team'
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        groups = executed['data']['groups']['entities']
        self.assertEqual(len(groups), 1)

        # Groups are sorted by name
        group = groups[0]
        self.assertEqual(group['name'], subteam1.name)

    def test_pagination(self):
        """Check whether it returns the groups searched when using pagination"""

        team1 = Team.add_root(name='team1', parent_org=None)
        team2 = Team.add_root(name='team2', parent_org=None)
        Team.add_root(name='team3', parent_org=None)

        client = graphene.test.Client(schema)
        test_query = SH_GROUPS_QUERY_PAGINATION % (1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        groups = executed['data']['groups']['entities']
        self.assertEqual(len(groups), 2)

        group = groups[0]
        self.assertEqual(group['name'], team1.name)

        group = groups[1]
        self.assertEqual(group['name'], team2.name)

        pag_data = executed['data']['groups']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 2)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 3)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_TEAMS_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestQueryIndividuals(django.test.TestCase):
    """Unit tests for individuals queries"""

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_individuals(self):
        """Check if it returns the registry of individuals"""

        cn = Country.objects.create(code='US',
                                    name='United States of America',
                                    alpha3='USA')

        org_ex = Organization.add_root(name='Example')
        org_bit = Organization.add_root(name='Bitergia')

        indv = Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        Profile.objects.create(name=None,
                               email='jsmith@example.com',
                               is_bot=True,
                               gender='M',
                               country=cn,
                               individual=indv)
        Identity.objects.create(uuid='A001',
                                name='John Smith',
                                email='jsmith@example.com',
                                username='jsmith',
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='A002',
                                name=None,
                                email='jsmith@bitergia.com',
                                username=None,
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='A003',
                                name=None,
                                email='jsmith@bitergia.com',
                                username=None,
                                source='mls',
                                individual=indv)
        Enrollment.objects.create(individual=indv, group=org_ex)
        Enrollment.objects.create(individual=indv, group=org_bit,
                                  start=datetime.datetime(1999, 1, 1, 0, 0, 0,
                                                          tzinfo=dateutil.tz.tzutc()),
                                  end=datetime.datetime(2000, 1, 1, 0, 0, 0,
                                                        tzinfo=dateutil.tz.tzutc()))

        indv = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               is_bot=False,
                               gender='M',
                               country=None,
                               individual=indv)
        Identity.objects.create(uuid='B001',
                                name='John Doe',
                                email='jdoe@example.com',
                                username='jdoe',
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='B002',
                                name=None,
                                email='jdoe@libresoft.es',
                                username=None,
                                source='scm',
                                individual=indv)

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_QUERY,
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 2)

        # Test John Smith individual
        indv = individuals[0]
        self.assertEqual(indv['mk'], 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(indv['isLocked'], False)

        self.assertEqual(indv['profile']['name'], None)
        self.assertEqual(indv['profile']['email'], 'jsmith@example.com')
        self.assertEqual(indv['profile']['isBot'], True)
        self.assertEqual(indv['profile']['country']['code'], 'US')
        self.assertEqual(indv['profile']['country']['name'], 'United States of America')

        identities = indv['identities']
        identities.sort(key=lambda x: x['uuid'])
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1['email'], 'jsmith@example.com')

        id2 = identities[1]
        self.assertEqual(id2['email'], 'jsmith@bitergia.com')
        self.assertEqual(id2['source'], 'scm')

        id3 = identities[2]
        self.assertEqual(id3['email'], 'jsmith@bitergia.com')
        self.assertEqual(id3['source'], 'mls')

        enrollments = indv['enrollments']
        enrollments.sort(key=lambda x: x['group']['name'])
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1['group']['name'], 'Bitergia')
        self.assertEqual(rol1['start'], '1999-01-01T00:00:00+00:00')
        self.assertEqual(rol1['end'], '2000-01-01T00:00:00+00:00')

        rol2 = enrollments[1]
        self.assertEqual(rol2['group']['name'], 'Example')
        self.assertEqual(rol2['start'], '1900-01-01T00:00:00+00:00')
        self.assertEqual(rol2['end'], '2100-01-01T00:00:00+00:00')

        # Test John Doe individual
        indv = individuals[1]
        self.assertEqual(indv['mk'], 'c6d2504fde0e34b78a185c4b709e5442d045451c')
        self.assertEqual(indv['isLocked'], False)

        self.assertEqual(indv['profile']['name'], None)
        self.assertEqual(indv['profile']['email'], None)

        identities = indv['identities']
        identities.sort(key=lambda x: x['uuid'])
        self.assertEqual(len(identities), 2)

        id1 = identities[0]
        self.assertEqual(id1['email'], 'jdoe@example.com')

        id2 = identities[1]
        self.assertEqual(id2['email'], 'jdoe@libresoft.es')

        enrollments = indv['enrollments']
        self.assertEqual(len(enrollments), 0)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_QUERY,
                                  context_value=self.context_value)

        indvs = executed['data']['individuals']['entities']
        self.assertListEqual(indvs, [])

    def tests_resolve_merge_recommendation(self):
        """Check if it resolves the merge recommendation in the individual"""

        indv1 = Individual.objects.create(mk='AAAA')
        indv2 = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name="Jhon",
                               email='jsmith@example.com',
                               is_bot=False,
                               gender='Male',
                               individual=indv1)
        Profile.objects.create(name="Jhon",
                               email='jsmith2@example.com',
                               is_bot=False,
                               gender='Male',
                               individual=indv2)
        rec = MergeRecommendation.objects.create(individual1=indv1, individual2=indv2)

        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUAL_MERGE_REC_QUERY,
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 2)

        indv1 = individuals[0]
        self.assertEqual(indv1['mk'], 'AAAA')
        self.assertEqual(indv1['matchRecommendationSet'][0]['individual']['mk'], 'BBBB')

        indv2 = individuals[1]
        self.assertEqual(indv2['mk'], 'BBBB')
        self.assertEqual(indv2['matchRecommendationSet'][0]['individual']['mk'], 'AAAA')

    def test_filter_registry(self):
        """Check whether it returns the uuid searched when using uuid filter"""

        cn = Country.objects.create(code='US',
                                    name='United States of America',
                                    alpha3='USA')

        org_ex = Organization.add_root(name='Example')
        org_bit = Organization.add_root(name='Bitergia')

        indv = Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        Profile.objects.create(name=None,
                               email='jsmith@example.com',
                               is_bot=True,
                               gender='M',
                               country=cn,
                               individual=indv)
        Identity.objects.create(uuid='A001',
                                name='John Smith',
                                email='jsmith@example.com',
                                username='jsmith',
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='A002',
                                name=None,
                                email='jsmith@bitergia.com',
                                username=None,
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='A003',
                                name=None,
                                email='jsmith@bitergia.com',
                                username=None,
                                source='mls',
                                individual=indv)
        Enrollment.objects.create(individual=indv, group=org_ex)
        Enrollment.objects.create(individual=indv, group=org_bit,
                                  start=datetime.datetime(1999, 1, 1, 0, 0, 0,
                                                          tzinfo=dateutil.tz.tzutc()),
                                  end=datetime.datetime(2000, 1, 1, 0, 0, 0,
                                                        tzinfo=dateutil.tz.tzutc()))

        indv = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               is_bot=False,
                               gender='M',
                               country=None,
                               individual=indv)
        Identity.objects.create(uuid='B001',
                                name='John Doe',
                                email='jdoe@example.com',
                                username='jdoe',
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='B002',
                                name=None,
                                email='jdoe@libresoft.es',
                                username=None,
                                source='scm',
                                individual=indv)

        # Tests
        client = graphene.test.Client(schema)
        indv_mk = 'a9b403e150dd4af8953a52a4bb841051e4b705d9'
        executed = client.execute(SH_INDIVIDUALS_UUID_FILTER % indv_mk,
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        # Test John Smith individual
        indv = individuals[0]
        self.assertEqual(indv['mk'], 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        self.assertEqual(indv['profile']['name'], None)
        self.assertEqual(indv['profile']['email'], 'jsmith@example.com')
        self.assertEqual(indv['profile']['isBot'], True)
        self.assertEqual(indv['profile']['country']['code'], 'US')
        self.assertEqual(indv['profile']['country']['name'], 'United States of America')

        identities = indv['identities']
        identities.sort(key=lambda x: x['uuid'])
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1['email'], 'jsmith@example.com')

        id2 = identities[1]
        self.assertEqual(id2['email'], 'jsmith@bitergia.com')
        self.assertEqual(id2['source'], 'scm')

        id3 = identities[2]
        self.assertEqual(id3['email'], 'jsmith@bitergia.com')
        self.assertEqual(id3['source'], 'mls')

        enrollments = indv['enrollments']
        enrollments.sort(key=lambda x: x['group']['name'])
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1['group']['name'], 'Bitergia')
        self.assertEqual(rol1['start'], '1999-01-01T00:00:00+00:00')
        self.assertEqual(rol1['end'], '2000-01-01T00:00:00+00:00')

        rol2 = enrollments[1]
        self.assertEqual(rol2['group']['name'], 'Example')
        self.assertEqual(rol2['start'], '1900-01-01T00:00:00+00:00')
        self.assertEqual(rol2['end'], '2100-01-01T00:00:00+00:00')

        # Test if it works when asking for any of the UUIDs
        indv_uuid = 'A002'
        executed = client.execute(SH_INDIVIDUALS_UUID_FILTER % indv_uuid,
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        # Test John Smith individual
        indv = individuals[0]
        self.assertEqual(indv['mk'], 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        self.assertEqual(indv['profile']['name'], None)
        self.assertEqual(indv['profile']['email'], 'jsmith@example.com')
        self.assertEqual(indv['profile']['isBot'], True)
        self.assertEqual(indv['profile']['country']['code'], 'US')
        self.assertEqual(indv['profile']['country']['name'], 'United States of America')

        identities = indv['identities']
        identities.sort(key=lambda x: x['uuid'])
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1['email'], 'jsmith@example.com')

        id2 = identities[1]
        self.assertEqual(id2['email'], 'jsmith@bitergia.com')
        self.assertEqual(id2['source'], 'scm')

        id3 = identities[2]
        self.assertEqual(id3['email'], 'jsmith@bitergia.com')
        self.assertEqual(id3['source'], 'mls')

        enrollments = indv['enrollments']
        enrollments.sort(key=lambda x: x['group']['name'])
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1['group']['name'], 'Bitergia')
        self.assertEqual(rol1['start'], '1999-01-01T00:00:00+00:00')
        self.assertEqual(rol1['end'], '2000-01-01T00:00:00+00:00')

        rol2 = enrollments[1]
        self.assertEqual(rol2['group']['name'], 'Example')
        self.assertEqual(rol2['start'], '1900-01-01T00:00:00+00:00')
        self.assertEqual(rol2['end'], '2100-01-01T00:00:00+00:00')

    def test_filter_term(self):
        """Check whether it returns the uuids searched when using a search term"""

        cn = Country.objects.create(code='US',
                                    name='United States of America',
                                    alpha3='USA')

        org_ex = Organization.add_root(name='Example')
        org_bit = Organization.add_root(name='Bitergia')

        indv = Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        Profile.objects.create(name=None,
                               email='jsmith@example.com',
                               is_bot=True,
                               gender='M',
                               country=cn,
                               individual=indv)
        Identity.objects.create(uuid='A001',
                                name='John Smith',
                                email='jsmith@example.com',
                                username='jsmith',
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='A002',
                                name=None,
                                email='jsmith@bitergia.com',
                                username=None,
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='A003',
                                name=None,
                                email='jsmith@bitergia.com',
                                username=None,
                                source='mls',
                                individual=indv)
        Enrollment.objects.create(individual=indv, group=org_ex)
        Enrollment.objects.create(individual=indv, group=org_bit,
                                  start=datetime.datetime(1999, 1, 1, 0, 0, 0,
                                                          tzinfo=dateutil.tz.tzutc()),
                                  end=datetime.datetime(2000, 1, 1, 0, 0, 0,
                                                        tzinfo=dateutil.tz.tzutc()))

        indv = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(name='John Doe (profile)',
                               email=None,
                               is_bot=False,
                               gender='M',
                               country=None,
                               individual=indv)
        Identity.objects.create(uuid='B001',
                                name='John Doe',
                                email='jdoe@example.com',
                                username='jdoe',
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='B002',
                                name=None,
                                email='jdoe@libresoft.es',
                                username=None,
                                source='scm',
                                individual=indv)

        # Tests

        # Test "jsmith", it should return one of the individuals
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_TERM_FILTER % 'jsmith',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        # Test John Smith individual
        indv = individuals[0]
        self.assertEqual(indv['mk'], 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        self.assertEqual(indv['profile']['name'], None)
        self.assertEqual(indv['profile']['email'], 'jsmith@example.com')
        self.assertEqual(indv['profile']['isBot'], True)
        self.assertEqual(indv['profile']['country']['code'], 'US')
        self.assertEqual(indv['profile']['country']['name'], 'United States of America')

        identities = indv['identities']
        identities.sort(key=lambda x: x['uuid'])
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1['email'], 'jsmith@example.com')

        id2 = identities[1]
        self.assertEqual(id2['email'], 'jsmith@bitergia.com')
        self.assertEqual(id2['source'], 'scm')

        id3 = identities[2]
        self.assertEqual(id3['email'], 'jsmith@bitergia.com')
        self.assertEqual(id3['source'], 'mls')

        # Test "jdoe@libresoft.es", it should return one of the individuals
        executed = client.execute(SH_INDIVIDUALS_TERM_FILTER % 'jdoe@libresoft.es',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        # Test John Doe individual
        indv = individuals[0]
        self.assertEqual(indv['mk'], 'c6d2504fde0e34b78a185c4b709e5442d045451c')

        self.assertEqual(indv['profile']['name'], 'John Doe (profile)')
        self.assertEqual(indv['profile']['email'], None)
        self.assertEqual(indv['profile']['isBot'], False)
        self.assertEqual(indv['profile']['gender'], 'M')
        self.assertEqual(indv['profile']['country'], None)

        identities = indv['identities']
        identities.sort(key=lambda x: x['uuid'])
        self.assertEqual(len(identities), 2)

        id1 = identities[0]
        self.assertEqual(id1['uuid'], 'B001')
        self.assertEqual(id1['name'], 'John Doe')
        self.assertEqual(id1['email'], 'jdoe@example.com')
        self.assertEqual(id1['username'], 'jdoe')
        self.assertEqual(id1['source'], 'scm')

        id2 = identities[1]
        self.assertEqual(id2['uuid'], 'B002')
        self.assertEqual(id2['name'], None)
        self.assertEqual(id2['email'], 'jdoe@libresoft.es')
        self.assertEqual(id2['username'], None)
        self.assertEqual(id2['source'], 'scm')

        # Test "John", it should return both individuals
        executed = client.execute(SH_INDIVIDUALS_TERM_FILTER % 'John',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 2)

        # Test John Smith individual
        indv = individuals[0]
        self.assertEqual(indv['mk'], 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        self.assertEqual(indv['profile']['name'], None)
        self.assertEqual(indv['profile']['email'], 'jsmith@example.com')
        self.assertEqual(indv['profile']['isBot'], True)
        self.assertEqual(indv['profile']['country']['code'], 'US')
        self.assertEqual(indv['profile']['country']['name'], 'United States of America')

        identities = indv['identities']
        identities.sort(key=lambda x: x['uuid'])
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1['email'], 'jsmith@example.com')

        id2 = identities[1]
        self.assertEqual(id2['email'], 'jsmith@bitergia.com')
        self.assertEqual(id2['source'], 'scm')

        id3 = identities[2]
        self.assertEqual(id3['email'], 'jsmith@bitergia.com')
        self.assertEqual(id3['source'], 'mls')

        # Test John Doe individual
        indv = individuals[1]
        self.assertEqual(indv['mk'], 'c6d2504fde0e34b78a185c4b709e5442d045451c')

        self.assertEqual(indv['profile']['name'], 'John Doe (profile)')
        self.assertEqual(indv['profile']['email'], None)
        self.assertEqual(indv['profile']['isBot'], False)
        self.assertEqual(indv['profile']['gender'], 'M')
        self.assertEqual(indv['profile']['country'], None)

        identities = indv['identities']
        identities.sort(key=lambda x: x['uuid'])
        self.assertEqual(len(identities), 2)

        id1 = identities[0]
        self.assertEqual(id1['uuid'], 'B001')
        self.assertEqual(id1['name'], 'John Doe')
        self.assertEqual(id1['email'], 'jdoe@example.com')
        self.assertEqual(id1['username'], 'jdoe')
        self.assertEqual(id1['source'], 'scm')

        id2 = identities[1]
        self.assertEqual(id2['uuid'], 'B002')
        self.assertEqual(id2['name'], None)
        self.assertEqual(id2['email'], 'jdoe@libresoft.es')
        self.assertEqual(id2['username'], None)
        self.assertEqual(id2['source'], 'scm')

        # Test if John Doe is found looking within its profile
        executed = client.execute(SH_INDIVIDUALS_TERM_FILTER % 'Doe (profile)',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        # Test John Doe individual
        indv = individuals[0]
        self.assertEqual(indv['mk'], 'c6d2504fde0e34b78a185c4b709e5442d045451c')

        self.assertEqual(indv['profile']['name'], 'John Doe (profile)')
        self.assertEqual(indv['profile']['email'], None)
        self.assertEqual(indv['profile']['isBot'], False)
        self.assertEqual(indv['profile']['gender'], 'M')
        self.assertEqual(indv['profile']['country'], None)

        identities = indv['identities']
        identities.sort(key=lambda x: x['uuid'])
        self.assertEqual(len(identities), 2)

        id1 = identities[0]
        self.assertEqual(id1['uuid'], 'B001')
        self.assertEqual(id1['name'], 'John Doe')
        self.assertEqual(id1['email'], 'jdoe@example.com')
        self.assertEqual(id1['username'], 'jdoe')
        self.assertEqual(id1['source'], 'scm')

        id2 = identities[1]
        self.assertEqual(id2['uuid'], 'B002')
        self.assertEqual(id2['name'], None)
        self.assertEqual(id2['email'], 'jdoe@libresoft.es')
        self.assertEqual(id2['username'], None)
        self.assertEqual(id2['source'], 'scm')

    def test_filter_search_4bytes_utf8_identities(self):
        """Check if it returns the unique identities which have 4 bytes UTF8-characters"""

        # Add some identities
        indv = Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        Profile.objects.create(name=None,
                               email='jsmith@example.com',
                               is_bot=True,
                               gender='M',
                               individual=indv)
        Identity.objects.create(uuid='A001',
                                name='John Smith',
                                email='jsmith@example.com',
                                username='jsmith',
                                source='scm',
                                individual=indv)
        emoji_id = Identity.objects.create(uuid='A002',
                                           name='😂',
                                           email='😂',
                                           username='😂',
                                           source='scm',
                                           individual=indv)

        # Add another individual
        indv2 = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               is_bot=False,
                               gender='M',
                               country=None,
                               individual=indv2)
        Identity.objects.create(uuid='B001',
                                name='John Doe',
                                email='jdoe@example.com',
                                username='jdoe',
                                source='scm',
                                individual=indv2)

        # An emoji is 4 bytes UTF-8 character
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_TERM_FILTER % '😂',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        # Test John Doe individual
        indv = individuals[0]
        self.assertEqual(indv['profile']['name'], None)
        self.assertEqual(indv['profile']['email'], 'jsmith@example.com')
        self.assertEqual(indv['profile']['isBot'], True)
        self.assertEqual(indv['profile']['gender'], 'M')

        identities = indv['identities']
        identities.sort(key=lambda x: x['uuid'])
        self.assertEqual(len(identities), 2)

        id1 = identities[0]
        self.assertEqual(id1['name'], 'John Smith')
        self.assertEqual(id1['email'], 'jsmith@example.com')
        self.assertEqual(id1['username'], 'jsmith')
        self.assertEqual(id1['source'], 'scm')

        id2 = identities[1]
        self.assertEqual(id2['name'], '😂')
        self.assertEqual(id2['email'], '😂')
        self.assertEqual(id2['username'], '😂')
        self.assertEqual(id2['source'], 'scm')

    def test_filter_term_non_exist_registry(self):
        """Check whether it returns an empty list when searched with a non existing term"""

        indv = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               is_bot=False,
                               gender='M',
                               country=None,
                               individual=indv)
        Identity.objects.create(uuid='B001',
                                name='John Doe',
                                email='jdoe@example.com',
                                username='jdoe',
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='B002',
                                name=None,
                                email='jdoe@libresoft.es',
                                username=None,
                                source='scm',
                                individual=indv)

        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_TERM_FILTER % 'owl',
                                  context_value=self.context_value)

        indvs = executed['data']['individuals']['entities']
        self.assertListEqual(indvs, [])

    def test_filter_registry_is_locked(self):
        """Check whether it returns the uuid searched when using isLocked filter"""

        cn = Country.objects.create(code='US',
                                    name='United States of America',
                                    alpha3='USA')

        org_ex = Organization.add_root(name='Example')
        org_bit = Organization.add_root(name='Bitergia')

        indv = Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9',
                                         is_locked=True)
        Profile.objects.create(name=None,
                               email='jsmith@example.com',
                               is_bot=True,
                               gender='M',
                               country=cn,
                               individual=indv)
        Identity.objects.create(uuid='A001',
                                name='John Smith',
                                email='jsmith@example.com',
                                username='jsmith',
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='A002',
                                name=None,
                                email='jsmith@bitergia.com',
                                username=None,
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='A003',
                                name=None,
                                email='jsmith@bitergia.com',
                                username=None,
                                source='mls',
                                individual=indv)
        Enrollment.objects.create(individual=indv, group=org_ex)
        Enrollment.objects.create(individual=indv, group=org_bit,
                                  start=datetime.datetime(1999, 1, 1, 0, 0, 0,
                                                          tzinfo=dateutil.tz.tzutc()),
                                  end=datetime.datetime(2000, 1, 1, 0, 0, 0,
                                                        tzinfo=dateutil.tz.tzutc()))

        indv = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               is_bot=False,
                               gender='M',
                               country=None,
                               individual=indv)
        Identity.objects.create(uuid='B001',
                                name='John Doe',
                                email='jdoe@example.com',
                                username='jdoe',
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='B002',
                                name=None,
                                email='jdoe@libresoft.es',
                                username=None,
                                source='scm',
                                individual=indv)

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_LOCKED_FILTER,
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        # Test John Smith individual
        indv = individuals[0]
        self.assertEqual(indv['mk'], 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(indv['isLocked'], True)

        self.assertEqual(indv['profile']['name'], None)
        self.assertEqual(indv['profile']['email'], 'jsmith@example.com')
        self.assertEqual(indv['profile']['isBot'], True)
        self.assertEqual(indv['profile']['country']['code'], 'US')
        self.assertEqual(indv['profile']['country']['name'], 'United States of America')

        identities = indv['identities']
        identities.sort(key=lambda x: x['uuid'])
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1['email'], 'jsmith@example.com')

        id2 = identities[1]
        self.assertEqual(id2['email'], 'jsmith@bitergia.com')
        self.assertEqual(id2['source'], 'scm')

        id3 = identities[2]
        self.assertEqual(id3['email'], 'jsmith@bitergia.com')
        self.assertEqual(id3['source'], 'mls')

        enrollments = indv['enrollments']
        enrollments.sort(key=lambda x: x['group']['name'])
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1['group']['name'], 'Bitergia')
        self.assertEqual(rol1['start'], '1999-01-01T00:00:00+00:00')
        self.assertEqual(rol1['end'], '2000-01-01T00:00:00+00:00')

        rol2 = enrollments[1]
        self.assertEqual(rol2['group']['name'], 'Example')
        self.assertEqual(rol2['start'], '1900-01-01T00:00:00+00:00')
        self.assertEqual(rol2['end'], '2100-01-01T00:00:00+00:00')

    def test_filter_registry_is_bot(self):
        """Check whether it returns the uuid searched when using isBot filter"""

        indv = Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9',
                                         is_locked=True)
        Profile.objects.create(name=None,
                               email='jsmith@example.com',
                               is_bot=True,
                               individual=indv)
        Identity.objects.create(uuid='A001',
                                name='John Smith',
                                email='jsmith@example.com',
                                source='scm',
                                individual=indv)

        indv = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               is_bot=False,
                               individual=indv)
        Identity.objects.create(uuid='B001',
                                name='John Doe',
                                email='jdoe@example.com',
                                source='scm',
                                individual=indv)

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_BOT_FILTER,
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        indv = individuals[0]
        self.assertEqual(indv['mk'], 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        self.assertEqual(indv['profile']['isBot'], True)

        # Test isBot: false
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_BOT_FILTER_FALSE,
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        indv = individuals[0]
        self.assertEqual(indv['mk'], 'c6d2504fde0e34b78a185c4b709e5442d045451c')
        self.assertEqual(indv['profile']['isBot'], False)

    def test_filter_non_exist_registry(self):
        """Check whether it returns an empty list when searched with a non existing uuid"""

        indv = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               is_bot=False,
                               gender='M',
                               country=None,
                               individual=indv)
        Identity.objects.create(uuid='B001',
                                name='John Doe',
                                email='jdoe@example.com',
                                username='jdoe',
                                source='scm',
                                individual=indv)
        Identity.objects.create(uuid='B002',
                                name=None,
                                email='jdoe@libresoft.es',
                                username=None,
                                source='scm',
                                individual=indv)

        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_UUID_FILTER,
                                  context_value=self.context_value)

        indvs = executed['data']['individuals']['entities']
        self.assertListEqual(indvs, [])

    def test_filter_gender(self):
        """Check whether it returns the individual searched when using the gender filter"""

        indv = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               gender='NB',
                               individual=indv)
        Identity.objects.create(uuid='B001',
                                name='John Doe',
                                source='scm',
                                individual=indv)

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_GENDER_FILTER % 'NB',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        indv = individuals[0]
        self.assertEqual(indv['mk'], 'c6d2504fde0e34b78a185c4b709e5442d045451c')
        self.assertEqual(indv['profile']['gender'], 'NB')

    def test_filter_gender_non_exist_registry(self):
        """Check whether it returns an empty list when searched with a non existing gender"""

        indv = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               gender='NB',
                               individual=indv)
        Identity.objects.create(uuid='B001',
                                name='John Doe',
                                source='scm',
                                individual=indv)

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_GENDER_FILTER % 'gender',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

    def test_filter_source(self):
        """Check whether it returns the individual searched when using the source filter"""

        indv = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               individual=indv)
        Identity.objects.create(uuid='B001',
                                name='John Doe',
                                source='git',
                                individual=indv)

        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_SOURCE_FILTER % 'git',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        indv = individuals[0]
        self.assertEqual(indv['mk'], 'c6d2504fde0e34b78a185c4b709e5442d045451c')

    def test_filter_source_non_exist_registry(self):
        """Check whether it returns an empty list when searched with a non existing source"""

        indv = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               individual=indv)
        Identity.objects.create(uuid='B001',
                                name='John Doe',
                                source='git',
                                individual=indv)

        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_SOURCE_FILTER % 'slack',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

    def test_filter_enrollment_date(self):
        """Check whether it returns the individual searched when using an enrollment date filter"""

        # Individual is enrolled 1999-2000
        org = Organization.add_root(name='Bitergia')
        indv = Individual.objects.create(mk='17ab00ed3825ec2f50483e33c88df223264182ba')
        Enrollment.objects.create(individual=indv, group=org,
                                  start=datetime.datetime(1999, 1, 1, 0, 0, 0,
                                                          tzinfo=dateutil.tz.tzutc()),
                                  end=datetime.datetime(2000, 1, 1, 0, 0, 0,
                                                        tzinfo=dateutil.tz.tzutc()))
        client = graphene.test.Client(schema)

        # Test enrollment before date '<'
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '<1998-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '<1999-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '<2000-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '<2001-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        # Test enrollment before or on date '<='
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '<=1998-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '<=1999-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '<=2000-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '<=2001-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        # Test enrollment after date '>'
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '>1998-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '>1999-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '>2000-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '>2001-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

        # Test enrollment after or on date '>='
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '>=1998-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '>=1999-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '>=2000-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '>=2001-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

        # Test enrollment range '..'
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '1997-01-01T00:00:00..1998-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '1998-01-01T00:00:00..1999-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '1999-01-01T00:00:00..2000-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '2000-01-01T00:00:00..2001-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % '2001-01-01T00:00:00..2002-01-01T00:00:00',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

    def test_filter_is_enrolled(self):
        """Check whether it returns the uuids searched when using isEnrolled filter"""

        org = Organization.add_root(name='Bitergia')
        indv1 = Individual.objects.create(mk='17ab00ed3825ec2f50483e33c88df223264182ba')
        indv2 = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Enrollment.objects.create(individual=indv1, group=org)

        client = graphene.test.Client(schema)

        # Test enrolled individual
        executed = client.execute(SH_INDIVIDUALS_IS_ENROLLED_FILTER % 'true',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)
        indv = individuals[0]
        self.assertEqual(indv['mk'], '17ab00ed3825ec2f50483e33c88df223264182ba')
        enrollment = indv['enrollments'][0]
        self.assertEqual(enrollment['group']['name'], 'Bitergia')

        # Test not enrolled individual
        executed = client.execute(SH_INDIVIDUALS_IS_ENROLLED_FILTER % 'false',
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)
        indv = individuals[0]
        self.assertEqual(indv['mk'], 'c6d2504fde0e34b78a185c4b709e5442d045451c')

    def test_filter_enrollment_date_invalid_date(self):
        """Check whether it fails when the filter has an invalid date"""

        client = graphene.test.Client(schema)

        invalid_date_filter = "2020-43-89T32:62:85..2020-67-90T45:76:15"
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % invalid_date_filter,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INVALID_FILTER_DATE_ERROR.format('enrollment_date', '2020-43-89T32:62:85'))

    def test_filter_enrollment_date_invalid_range(self):
        """Check whether it fails when the filter has an invalid date range"""

        date_1 = '2002-01-01T00:00:00'
        date_2 = '2001-01-01T00:00:00'

        filter_invalid_format = "{}..{}".format(date_1, date_2)

        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_DATE_FILTER % filter_invalid_format,
                                  context_value=self.context_value)

        expected_error = "Upper bound must be greater than the lower bound"

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INVALID_FILTER_RANGE_ERROR.format('enrollment_date', expected_error))

    def test_filter_last_updated(self):
        """Check whether it returns the uuids searched when using a date filter"""

        timestamp_1 = datetime_utcnow()
        Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')

        timestamp_2 = datetime_utcnow()
        Individual.objects.create(mk='e0e34b7c6d2504fd8a1842d045451c5c4b709e54')

        timestamp_3 = datetime_utcnow()

        # Tests

        ts_1 = timestamp_1.strftime("%Y-%m-%dT%H:%M:%S.%f")
        ts_2 = timestamp_2.strftime("%Y-%m-%dT%H:%M:%S.%f")
        ts_3 = timestamp_3.strftime("%Y-%m-%dT%H:%M:%S.%f")

        # Test individuals last_updated before first timestamp, it should return none
        filter_no_indvs = '<={}'.format(ts_1)

        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_LAST_UPDATED_FILTER % filter_no_indvs,
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

        # Test individuals last_updated between first and second timestamp, it should return two
        filter_first_indv = "{}..{}".format(ts_1, ts_2)

        executed = client.execute(SH_INDIVIDUALS_LAST_UPDATED_FILTER % filter_first_indv,
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 2)

        indv = individuals[0]
        self.assertEqual(indv['mk'], 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        indv = individuals[1]
        self.assertEqual(indv['mk'], 'c6d2504fde0e34b78a185c4b709e5442d045451c')

        # Test individuals last_updated after the first timestamp, it should return all
        filter_all_indv = ">{}".format(ts_1)

        executed = client.execute(SH_INDIVIDUALS_LAST_UPDATED_FILTER % filter_all_indv,
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 3)

        indv = individuals[0]
        self.assertEqual(indv['mk'], 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        indv = individuals[1]
        self.assertEqual(indv['mk'], 'c6d2504fde0e34b78a185c4b709e5442d045451c')

        indv = individuals[2]
        self.assertEqual(indv['mk'], 'e0e34b7c6d2504fd8a1842d045451c5c4b709e54')

        # Test individuals last_updated after last timestamp, it should return none
        filter_last_ts = '>{}'.format(ts_3)

        executed = client.execute(SH_INDIVIDUALS_LAST_UPDATED_FILTER % filter_last_ts,
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

        # Test individuals last_updated before and not equal to first timestamp, it
        # should return none.
        filter_no_indvs = '<{}'.format(ts_1)

        executed = client.execute(SH_INDIVIDUALS_LAST_UPDATED_FILTER % filter_no_indvs,
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

        # Test individuals last_updated after and equal to first timestamp. it should
        # return three.
        filter_all_indvs = '>={}'.format(ts_1)

        executed = client.execute(SH_INDIVIDUALS_LAST_UPDATED_FILTER % filter_all_indvs,
                                  context_value=self.context_value)
        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 3)

    def test_filter_last_updated_invalid_date(self):
        """Check whether it fails when the filter has an invalid date"""

        client = graphene.test.Client(schema)

        invalid_date_filter = "2020-86-32T28:72:99..2020-08-06T10:25:15"
        executed = client.execute(SH_INDIVIDUALS_LAST_UPDATED_FILTER % invalid_date_filter,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INVALID_FILTER_DATE_ERROR.format('last_updated', '2020-86-32T28:72:99'))

        zero_date_filter = "0000-00-00T00:00:00..0000-00-00T00:00:00"
        executed = client.execute(SH_INDIVIDUALS_LAST_UPDATED_FILTER % zero_date_filter,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INVALID_FILTER_DATE_ERROR.format('last_updated', '0000-00-00T00:00:00'))

    def test_filter_last_updated_invalid_format_operator(self):
        """Check whether it fails when the filter has an invalid operator"""

        timestamp_1 = datetime_utcnow()

        Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')

        timestamp_2 = datetime_utcnow()

        Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')

        ts_1 = timestamp_1.strftime("%Y-%m-%dT%H:%M:%S.%f")

        # Test invalid format (wrong operator)
        filter_invalid_format = '<<={}'.format(ts_1)

        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_LAST_UPDATED_FILTER % filter_invalid_format,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INVALID_FILTER_FORMAT_ERROR.format('last_updated'))

    def test_filter_last_updated_invalid_format_range_operator(self):
        """Check whether it fails when the filter has an invalid range operator"""

        timestamp_1 = datetime_utcnow()

        Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')

        timestamp_2 = datetime_utcnow()

        Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')

        ts_1 = timestamp_1.strftime("%Y-%m-%dT%H:%M:%S.%f")
        ts_2 = timestamp_2.strftime("%Y-%m-%dT%H:%M:%S.%f")

        # Test invalid format (wrong operator)
        filter_invalid_format_2 = "{}...{}".format(ts_1, ts_2)

        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_LAST_UPDATED_FILTER % filter_invalid_format_2,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INVALID_FILTER_FORMAT_ERROR.format('last_updated'))

    def test_filter_last_updated_invalid_format_iso_date(self):
        """Check whether it fails when the filter has an invalid date format"""

        timestamp_1 = datetime_utcnow()

        Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')

        timestamp_2 = datetime_utcnow()

        Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')

        # Test wrong ISO 8601 format (%Y-%m-%dT%H:%M:%S), with a missing "T" between date and time
        invalid_format_filter = "2020-06-16 10:34:29..2020-08-06T10:25:15"

        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_LAST_UPDATED_FILTER % invalid_format_filter,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INVALID_FILTER_FORMAT_ERROR.format('last_updated'))

    def test_filter_last_updated_invalid_range(self):
        """Check whether it fails when the filter has an invalid date range"""

        timestamp_1 = datetime_utcnow()

        Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')

        timestamp_2 = datetime_utcnow()

        Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')

        # Tests
        ts_1 = timestamp_1.strftime("%Y-%m-%dT%H:%M:%S.%f")
        ts_2 = timestamp_2.strftime("%Y-%m-%dT%H:%M:%S.%f")

        # Test invalid range
        filter_invalid_format_2 = "{}..{}".format(ts_2, ts_1)

        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_LAST_UPDATED_FILTER % filter_invalid_format_2,
                                  context_value=self.context_value)

        expected_error = 'Upper bound must be greater than the lower bound'

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INVALID_FILTER_RANGE_ERROR.format('last_updated', expected_error))

    def test_filter_country(self):
        """Check whether it returns the uuid searched when using the country filter"""

        cn = Country.objects.create(code='US',
                                    name='United States of America',
                                    alpha3='USA')

        indv = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               country=cn,
                               individual=indv)
        Identity.objects.create(uuid='B001',
                                name='John Doe',
                                source='scm',
                                individual=indv)

        # Test filter by country code
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_COUNTRY_FILTER % 'US',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        indv = individuals[0]
        self.assertEqual(indv['profile']['country']['code'], 'US')

        # Test filter by alpha3 code
        executed = client.execute(SH_INDIVIDUALS_COUNTRY_FILTER % 'USA',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        indv = individuals[0]
        self.assertEqual(indv['profile']['country']['alpha3'], 'USA')

        # Test filter by country name
        executed = client.execute(SH_INDIVIDUALS_COUNTRY_FILTER % 'United States',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        indv = individuals[0]
        self.assertEqual(indv['profile']['country']['name'], 'United States of America')

    def test_filter_enrollment(self):
        """Check whether it returns the uuid searched when using enrollment filter"""

        org1 = Organization.add_root(name='Bitergia')
        org2 = Organization.add_root(name='Bit Company')
        indv1 = Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        indv2 = Individual.objects.create(mk='185c4b709e5446d250b4fde0e34b78a2b4fde0e3')
        Enrollment.objects.create(individual=indv1, group=org1)
        Enrollment.objects.create(individual=indv2, group=org2)

        # Test full organization name match
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_FILTER % 'Bitergia',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        indv = individuals[0]
        self.assertEqual(indv['mk'], 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        enrollment = indv['enrollments'][0]
        self.assertEqual(enrollment['group']['name'], 'Bitergia')

        # Test no results for partial organization name match
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_FILTER % 'bit',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

        # Test organization name with spaces
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_FILTER % 'bit company',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)
        indv = individuals[0]
        self.assertEqual(indv['mk'], '185c4b709e5446d250b4fde0e34b78a2b4fde0e3')
        enrollment = indv['enrollments'][0]
        self.assertEqual(enrollment['group']['name'], 'Bit Company')

        # Test no results for enrollment
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_FILTER % 'Organization',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

    def test_filter_team_enrollment(self):
        """Check whether it returns the uuid searched when using enrollment filter"""

        org = Organization.add_root(name='Bitergia')
        team1 = Team.add_root(name='Team 1', parent_org=org)
        team2 = Team.add_root(name='Team 2', parent_org=org)
        indv1 = Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        indv2 = Individual.objects.create(mk='185c4b709e5446d250b4fde0e34b78a2b4fde0e3')
        Enrollment.objects.create(individual=indv1, group=team1)
        Enrollment.objects.create(individual=indv2, group=team2)

        # Test full team name match
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_TEAM_FILTER % 'Team 1',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 1)

        indv = individuals[0]
        self.assertEqual(indv['mk'], 'a9b403e150dd4af8953a52a4bb841051e4b705d9')
        enrollment = indv['enrollments'][0]
        self.assertEqual(enrollment['group']['name'], 'Team 1')
        self.assertEqual(enrollment['group']['type'], 'team')

        # Test no results for partial team name match
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_FILTER % 'tea',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

        # Test no results for enrollment
        executed = client.execute(SH_INDIVIDUALS_ENROLLMENT_FILTER % 'Organization',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']
        self.assertEqual(len(individuals), 0)

    def test_order_by_last_modified(self):
        """Check whether it returns the individuals ordered by last modified date"""

        indv1 = Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        indv2 = Individual.objects.create(mk='185c4b709e5446d250b4fde0e34b78a2b4fde0e3')
        indv3 = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')

        # Test default order by mk
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_ORDER_BY % 'mk',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']

        indv = individuals[0]
        self.assertEqual(indv['mk'], indv2.mk)
        indv = individuals[1]
        self.assertEqual(indv['mk'], indv1.mk)
        indv = individuals[2]
        self.assertEqual(indv['mk'], indv3.mk)

        # Test ascending order
        executed = client.execute(SH_INDIVIDUALS_ORDER_BY % 'lastModified',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']

        indv = individuals[0]
        self.assertEqual(indv['mk'], indv1.mk)
        indv = individuals[1]
        self.assertEqual(indv['mk'], indv2.mk)
        indv = individuals[2]
        self.assertEqual(indv['mk'], indv3.mk)

        # Test descending order
        executed = client.execute(SH_INDIVIDUALS_ORDER_BY % '-lastModified',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']

        indv = individuals[0]
        self.assertEqual(indv['mk'], indv3.mk)
        indv = individuals[1]
        self.assertEqual(indv['mk'], indv2.mk)
        indv = individuals[2]
        self.assertEqual(indv['mk'], indv1.mk)

    def test_order_by_created_at(self):
        """Check whether it returns the individuals ordered by their creation date"""

        indv1 = Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        indv2 = Individual.objects.create(mk='185c4b709e5446d250b4fde0e34b78a2b4fde0e3')
        indv3 = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')

        # Test default order by mk
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_ORDER_BY % 'mk',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']

        indv = individuals[0]
        self.assertEqual(indv['mk'], indv2.mk)
        indv = individuals[1]
        self.assertEqual(indv['mk'], indv1.mk)
        indv = individuals[2]
        self.assertEqual(indv['mk'], indv3.mk)

        # Test ascending order
        executed = client.execute(SH_INDIVIDUALS_ORDER_BY % 'createdAt',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']

        indv = individuals[0]
        self.assertEqual(indv['mk'], indv1.mk)
        indv = individuals[1]
        self.assertEqual(indv['mk'], indv2.mk)
        indv = individuals[2]
        self.assertEqual(indv['mk'], indv3.mk)

        # Test descending order
        executed = client.execute(SH_INDIVIDUALS_ORDER_BY % '-createdAt',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']

        indv = individuals[0]
        self.assertEqual(indv['mk'], indv3.mk)
        indv = individuals[1]
        self.assertEqual(indv['mk'], indv2.mk)
        indv = individuals[2]
        self.assertEqual(indv['mk'], indv1.mk)

    def test_order_by_profile_name(self):
        """Check whether it returns the individuals ordered by their name"""

        indv1 = Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        indv2 = Individual.objects.create(mk='185c4b709e5446d250b4fde0e34b78a2b4fde0e3')
        indv3 = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(name='AA', individual=indv1)
        Profile.objects.create(name='ZZ', individual=indv2)
        Profile.objects.create(name='MM', individual=indv3)

        # Test ascending order
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_ORDER_BY % 'profile__name',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']

        indv = individuals[0]
        self.assertEqual(indv['mk'], indv1.mk)
        indv = individuals[1]
        self.assertEqual(indv['mk'], indv3.mk)
        indv = individuals[2]
        self.assertEqual(indv['mk'], indv2.mk)

        # Test descending order
        executed = client.execute(SH_INDIVIDUALS_ORDER_BY % '-profile__name',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']

        indv = individuals[0]
        self.assertEqual(indv['mk'], indv2.mk)
        indv = individuals[1]
        self.assertEqual(indv['mk'], indv3.mk)
        indv = individuals[2]
        self.assertEqual(indv['mk'], indv1.mk)

    def test_order_by_identities_count(self):
        """Check whether it returns the individuals ordered by their number of identities"""

        indv1 = Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        Identity.objects.create(uuid='A001',
                                name='John Doe',
                                source='scm',
                                individual=indv1)
        indv2 = Individual.objects.create(mk='185c4b709e5446d250b4fde0e34b78a2b4fde0e3')
        Identity.objects.create(uuid='B001',
                                name='Jane Roe',
                                source='scm',
                                individual=indv2)
        Identity.objects.create(uuid='B002',
                                name='Jane Roe',
                                source='mls',
                                individual=indv2)
        Identity.objects.create(uuid='B003',
                                name='Jane Roe',
                                source='alt',
                                individual=indv2)
        indv3 = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Identity.objects.create(uuid='C001',
                                name='John Smith',
                                source='scm',
                                individual=indv3)
        Identity.objects.create(uuid='C002',
                                name='John Smith',
                                source='mls',
                                individual=indv3)

        # Test ascending order
        client = graphene.test.Client(schema)
        executed = client.execute(SH_INDIVIDUALS_ORDER_BY % 'identitiesCount',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']

        indv = individuals[0]
        self.assertEqual(indv['mk'], indv1.mk)
        indv = individuals[1]
        self.assertEqual(indv['mk'], indv3.mk)
        indv = individuals[2]
        self.assertEqual(indv['mk'], indv2.mk)

        # Test descending order
        executed = client.execute(SH_INDIVIDUALS_ORDER_BY % '-identitiesCount',
                                  context_value=self.context_value)

        individuals = executed['data']['individuals']['entities']

        indv = individuals[0]
        self.assertEqual(indv['mk'], indv2.mk)
        indv = individuals[1]
        self.assertEqual(indv['mk'], indv3.mk)
        indv = individuals[2]
        self.assertEqual(indv['mk'], indv1.mk)

    def test_pagination(self):
        """Check whether it returns the individuals searched when using pagination"""

        indv1 = Individual.objects.create(mk='185c4b709e5446d250b4fde0e34b78a2b4fde0e3')
        indv2 = Individual.objects.create(mk='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        indv3 = Individual.objects.create(mk='c6d2504fde0e34b78a185c4b709e5442d045451c')

        client = graphene.test.Client(schema)
        test_query = SH_INDIVIDUALS_UUID_PAGINATION % (1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        indvs = executed['data']['individuals']['entities']
        self.assertEqual(len(indvs), 2)

        indv = indvs[0]
        self.assertEqual(indv['mk'], indv1.mk)

        indv = indvs[1]
        self.assertEqual(indv['mk'], indv2.mk)

        pag_data = executed['data']['individuals']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 2)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 3)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_INDIVIDUALS_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestQueryTransactions(django.test.TestCase):
    """Unit tests for transaction queries"""

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        api.add_organization(self.ctx, 'Example')

        api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.update_profile(self.ctx,
                           uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                           name='J. Smith', email='jsmith@example',
                           gender='male', gender_acc=75)
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2017, 6, 1))

        # Create an additional transaction controlling input values
        self.timestamp = datetime_utcnow()  # This will be used as a filter
        self.trx = Transaction(name='test_trx',
                               tuid='012345abcdef',
                               created_at=datetime_utcnow(),
                               authored_by=self.user.username)
        self.trx.save()

    def test_transaction(self):
        """Check if it returns the registry of transactions"""

        timestamp = datetime_utcnow()
        client = graphene.test.Client(schema)
        executed = client.execute(SH_TRANSACTIONS_QUERY,
                                  context_value=self.context_value)

        transactions = executed['data']['transactions']['entities']
        self.assertEqual(len(transactions), 5)

        trx = transactions[0]
        self.assertEqual(trx['name'], 'add_organization')
        self.assertLess(str_to_datetime(trx['createdAt']), timestamp)
        self.assertIsInstance(trx['tuid'], str)
        self.assertLess(str_to_datetime(trx['closedAt']), timestamp)
        self.assertTrue(trx['isClosed'])
        self.assertEqual(trx['authoredBy'], 'test')

        trx = transactions[1]
        self.assertEqual(trx['name'], 'add_identity')
        self.assertLess(str_to_datetime(trx['createdAt']), timestamp)
        self.assertIsInstance(trx['tuid'], str)
        self.assertLess(str_to_datetime(trx['closedAt']), timestamp)
        self.assertTrue(trx['isClosed'])
        self.assertEqual(trx['authoredBy'], 'test')

        trx = transactions[2]
        self.assertEqual(trx['name'], 'update_profile')
        self.assertLess(str_to_datetime(trx['createdAt']), timestamp)
        self.assertIsInstance(trx['tuid'], str)
        self.assertLess(str_to_datetime(trx['closedAt']), timestamp)
        self.assertTrue(trx['isClosed'])
        self.assertEqual(trx['authoredBy'], 'test')

        trx = transactions[3]
        self.assertEqual(trx['name'], 'enroll')
        self.assertLess(str_to_datetime(trx['createdAt']), timestamp)
        self.assertIsInstance(trx['tuid'], str)
        self.assertLess(str_to_datetime(trx['closedAt']), timestamp)
        self.assertTrue(trx['isClosed'])
        self.assertEqual(trx['authoredBy'], 'test')

        trx = transactions[4]
        self.assertEqual(trx['name'], self.trx.name)
        self.assertEqual(str_to_datetime(trx['createdAt']), self.trx.created_at)
        self.assertEqual(trx['tuid'], self.trx.tuid)
        self.assertIsNone(trx['closedAt'])
        self.assertFalse(trx['isClosed'])
        self.assertEqual(trx['authoredBy'], 'test')

    def test_filter_registry(self):
        """Check whether it returns the transaction searched when using filters"""

        client = graphene.test.Client(schema)
        test_query = SH_TRANSACTIONS_QUERY_FILTER % ('012345abcdef', 'test_trx',
                                                     self.timestamp.isoformat(),
                                                     'test')
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        transactions = executed['data']['transactions']['entities']
        self.assertEqual(len(transactions), 1)

        trx = transactions[0]
        self.assertEqual(trx['name'], self.trx.name)
        self.assertEqual(str_to_datetime(trx['createdAt']), self.trx.created_at)
        self.assertEqual(trx['tuid'], self.trx.tuid)
        self.assertIsNone(trx['closedAt'])
        self.assertFalse(trx['isClosed'])
        self.assertEqual(trx['authoredBy'], 'test')

    def test_filter_non_existing_registry(self):
        """Check whether it returns an empty list when searched with a non existing transaction"""

        client = graphene.test.Client(schema)
        test_query = SH_TRANSACTIONS_QUERY_FILTER % ('012345abcdefg', 'test_trx',
                                                     self.timestamp.isoformat(),
                                                     'test')
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        transactions = executed['data']['transactions']['entities']
        self.assertListEqual(transactions, [])

    def test_pagination(self):
        """Check whether it returns the transactions searched when using pagination"""

        timestamp = datetime_utcnow()

        client = graphene.test.Client(schema)
        test_query = SH_TRANSACTIONS_QUERY_PAGINATION % (1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        transactions = executed['data']['transactions']['entities']
        self.assertEqual(len(transactions), 2)

        trx = transactions[0]
        self.assertEqual(trx['name'], 'add_organization')
        self.assertLess(str_to_datetime(trx['createdAt']), timestamp)
        self.assertIsInstance(trx['tuid'], str)
        self.assertLess(str_to_datetime(trx['closedAt']), timestamp)
        self.assertTrue(trx['isClosed'])
        self.assertEqual(trx['authoredBy'], 'test')

        trx = transactions[1]
        self.assertEqual(trx['name'], 'add_identity')
        self.assertLess(str_to_datetime(trx['createdAt']), timestamp)
        self.assertIsInstance(trx['tuid'], str)
        self.assertLess(str_to_datetime(trx['closedAt']), timestamp)
        self.assertTrue(trx['isClosed'])
        self.assertEqual(trx['authoredBy'], 'test')

        pag_data = executed['data']['transactions']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 3)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 5)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        # Delete Transactions created in `setUp` method
        Transaction.objects.all().delete()
        transactions = Transaction.objects.all()

        self.assertEqual(len(transactions), 0)

        # Test query
        client = graphene.test.Client(schema)
        executed = client.execute(SH_TRANSACTIONS_QUERY,
                                  context_value=self.context_value)

        q_transactions = executed['data']['transactions']['entities']
        self.assertListEqual(q_transactions, [])

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_TRANSACTIONS_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestQueryOperations(django.test.TestCase):
    """Unit tests for operation queries"""

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        api.add_organization(self.ctx, 'Example')

        # Create an additional operation controlling input values
        trx = Transaction(name='test_trx',
                          tuid='012345abcdef',
                          created_at=datetime_utcnow(),
                          authored_by=self.user.username)
        trx.save()

        self.trxl = TransactionsLog(trx, self.ctx)
        self.timestamp = datetime_utcnow()  # This will be used as a filter
        self.trxl.log_operation(op_type=Operation.OpType.UPDATE,
                                entity_type='test_entity',
                                timestamp=datetime_utcnow(),
                                args={'test_arg': 'test_value'},
                                target='test_target')
        self.trxl.close()

    def test_operation(self):
        """Check if it returns the registry of operations"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_OPERATIONS_QUERY,
                                  context_value=self.context_value)

        operations = executed['data']['operations']['entities']
        self.assertEqual(len(operations), 2)

        op1 = operations[0]
        self.assertEqual(op1['opType'], Operation.OpType.ADD.value)
        self.assertEqual(op1['entityType'], 'organization')
        self.assertLess(str_to_datetime(op1['timestamp']), self.timestamp)
        self.assertEqual(op1['args'], {'name': 'Example'})

        # Check if the query returns the associated transaction
        trx1 = op1['trx']
        self.assertEqual(trx1['name'], 'add_organization')
        self.assertIsInstance(trx1['tuid'], str)
        self.assertLess(str_to_datetime(trx1['createdAt']), self.timestamp)

        op2 = operations[1]
        self.assertEqual(op2['opType'], Operation.OpType.UPDATE.value)
        self.assertEqual(op2['entityType'], 'test_entity')
        self.assertGreater(str_to_datetime(op2['timestamp']), self.timestamp)
        self.assertEqual(op2['args'], {'test_arg': 'test_value'})

        # Check if the query returns the associated transaction
        trx2 = op2['trx']
        self.assertEqual(trx2['name'], self.trxl.trx.name)
        self.assertEqual(trx2['tuid'], self.trxl.trx.tuid)
        self.assertEqual(str_to_datetime(trx2['createdAt']), self.trxl.trx.created_at)

    def test_filter_registry(self):
        """Check whether it returns the operation searched when using filters"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_FILTER % ('UPDATE', 'test_entity',
                                                   self.timestamp.isoformat())
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        operations = executed['data']['operations']['entities']
        self.assertEqual(len(operations), 1)

        op1 = operations[0]
        self.assertEqual(op1['opType'], Operation.OpType.UPDATE.value)
        self.assertEqual(op1['entityType'], 'test_entity')
        self.assertGreater(str_to_datetime(op1['timestamp']), self.timestamp)
        self.assertEqual(op1['args'], {'test_arg': 'test_value'})

        # Check if the query returns the associated transaction
        trx1 = op1['trx']
        self.assertEqual(trx1['name'], self.trxl.trx.name)
        self.assertEqual(trx1['tuid'], self.trxl.trx.tuid)
        self.assertEqual(str_to_datetime(trx1['createdAt']), self.trxl.trx.created_at)

    def test_filter_non_existing_registry(self):
        """Check whether it returns an empty list when searched with a non existing operation"""

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_FILTER % ('DELETE', 'test_entity',
                                                   self.timestamp.isoformat())
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        operations = executed['data']['operations']['entities']
        self.assertListEqual(operations, [])

    def test_pagination(self):
        """Check whether it returns the operations searched when using pagination"""

        # Add an additional operation by calling an API method
        api.add_domain(self.ctx, organization='Example', domain_name='example.com')

        client = graphene.test.Client(schema)
        test_query = SH_OPERATIONS_QUERY_PAGINATION % (1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        operations = executed['data']['operations']['entities']
        self.assertEqual(len(operations), 2)

        op1 = operations[0]
        self.assertEqual(op1['opType'], Operation.OpType.ADD.value)
        self.assertEqual(op1['entityType'], 'organization')
        self.assertEqual(op1['target'], 'Example')
        self.assertLess(str_to_datetime(op1['timestamp']), self.timestamp)
        self.assertEqual(op1['args'], {'name': 'Example'})

        op2 = operations[1]
        self.assertEqual(op2['opType'], Operation.OpType.UPDATE.value)
        self.assertEqual(op2['entityType'], 'test_entity')
        self.assertGreater(str_to_datetime(op2['timestamp']), self.timestamp)
        self.assertEqual(op2['args'], {'test_arg': 'test_value'})

        pag_data = executed['data']['operations']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 2)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 3)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        # Delete Operations created in `setUp` method
        Operation.objects.all().delete()
        operations = Operation.objects.all()

        self.assertEqual(len(operations), 0)

        # Test query
        client = graphene.test.Client(schema)
        executed = client.execute(SH_OPERATIONS_QUERY,
                                  context_value=self.context_value)

        q_operations = executed['data']['operations']['entities']
        self.assertListEqual(q_operations, [])

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_OPERATIONS_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestParseDateFilter(django.test.TestCase):
    """Unit tests for parse_date_filter method"""

    def test_parse_date_filter(self):
        """Test if the method extracts the fields from the filter correctly"""

        # Test a comparison operator and a complete date (microseconds and time offset)
        expected_result = {
            'operator': '>=',
            'date1': str_to_datetime('2020-11-22T12:26:41.740227+00:00'),
            'date2': None
        }

        filter_string = '>=2020-11-22T12:26:41.740227+00:00'
        result = parse_date_filter(filter_string)
        self.assertDictEqual(result, expected_result)

        # Test range operator
        expected_result = {
            'operator': '..',
            'date1': str_to_datetime('2020-10-12T00:00:00'),
            'date2': str_to_datetime('2020-11-22T12:26:41.740227+00:00')
        }

        filter_string = '2020-10-12T00:00:00..2020-11-22T12:26:41.740227+00:00'
        result = parse_date_filter(filter_string)
        self.assertDictEqual(result, expected_result)

        # Test ISO date format from Javascript's method `toISOString` (web interface)
        expected_result = {
            'operator': '..',
            'date1': str_to_datetime('2020-10-12T00:00:00Z'),
            'date2': str_to_datetime('2020-11-22T12:26:41.740227Z')
        }

        filter_string = '2020-10-12T00:00:00Z..2020-11-22T12:26:41.740227Z'
        result = parse_date_filter(filter_string)
        self.assertDictEqual(result, expected_result)

    def test_invalid_date(self):
        """Test if the method fails when it receives a wrong date"""

        # Test range operator
        date_1 = '2020-10-12T00:00:00'
        date_2 = '2020-41-22T12:26:41.740227+00:00'
        filter_string = '{}..{}'.format(date_1, date_2)
        with self.assertRaisesRegex(InvalidDateError, PARSE_DATE_INVALID_DATE_ERROR.format('')):
            parse_date_filter(filter_string)

    def test_invalid_format(self):
        """Test if the method raises an exception with invalid filter formats"""

        # Test range operator
        date_1 = '2020-10-12T00:00:00'
        date_2 = '2020-11-22T12:26:41.740227+00:00'
        filter_string = '-{}..{}'.format(date_1, date_2)

        with self.assertRaisesRegex(ValueError, PARSE_DATE_INVALID_FORMAT_ERROR):
            parse_date_filter(filter_string)


class TestQueryRecommenderExclusionTerms(django.test.TestCase):
    """Unit tests for recommenderExclusionTerms queries"""

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_recommender_exclusion_terms(self):
        """Check if it returns the registry of recommenderExclusionTerms"""

        RecommenderExclusionTerm.objects.create(term='Example')
        RecommenderExclusionTerm.objects.create(term='John Smith')

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_RET_QUERY,
                                  context_value=self.context_value)

        rels = executed['data']['recommenderExclusionTerms']['entities']
        self.assertEqual(len(rels), 2)

        rel1 = rels[0]
        self.assertEqual(rel1['term'], 'Example')

        rel2 = rels[1]
        self.assertEqual(rel2['term'], 'John Smith')

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_RET_QUERY,
                                  context_value=self.context_value)

        rels = executed['data']['recommenderExclusionTerms']['entities']
        self.assertListEqual(rels, [])

    def test_pagination(self):
        """Check whether it returns the recommenderExclusionTerms searched when using pagination"""

        rel1 = RecommenderExclusionTerm.objects.create(term='Tom')
        rel2 = RecommenderExclusionTerm.objects.create(term='John')
        rel3 = RecommenderExclusionTerm.objects.create(term='Quan')

        client = graphene.test.Client(schema)
        test_query = SH_RET_QUERY_PAGINATION % (1, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        rels = executed['data']['recommenderExclusionTerms']['entities']

        self.assertEqual(len(rels), 2)

        # As recommenderExclusionTerm are sorted by excluded, the first two will be rel2 and rel3
        rel = rels[0]
        self.assertEqual(rel['term'], rel2.term)

        rel = rels[1]
        self.assertEqual(rel['term'], rel3.term)

        pag_data = executed['data']['recommenderExclusionTerms']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 2)
        self.assertEqual(pag_data['numPages'], 2)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 2)
        self.assertEqual(pag_data['totalResults'], 3)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_RET_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestQueryRecommendedAffiliation(django.test.TestCase):
    """Unit tests for RecommendedAffiliation queries"""

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_recommended_affiliations(self):
        """Check if it returns the registry of AffiliationRecommendation"""

        indv1 = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               individual=indv1)
        indv2 = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               individual=indv2)
        org_ex1 = Organization.add_root(name='Example1')
        org_ex2 = Organization.add_root(name='Example2')
        AffiliationRecommendation.objects.create(individual=indv1, organization=org_ex1)
        AffiliationRecommendation.objects.create(individual=indv2, organization=org_ex2)

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_AFF_REC_QUERY,
                                  context_value=self.context_value)

        rels = executed['data']['recommendedAffiliations']['entities']
        self.assertEqual(len(rels), 2)
        rel1 = rels[0]
        self.assertEqual(rel1['individual']['mk'], indv1.mk)
        self.assertEqual(rel1['organization']['name'], 'Example1')

        rel1 = rels[1]
        self.assertEqual(rel1['individual']['mk'], indv2.mk)
        self.assertEqual(rel1['organization']['name'], 'Example2')

    def test_filter_is_applied(self):
        """Check whether it filter recommendations by is_applied"""

        indv1 = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               individual=indv1)
        indv2 = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               individual=indv2)
        indv3 = Individual.objects.create(mk='CCCC')
        Profile.objects.create(name='Mary Doe',
                               email='mdoe@bitergia.com',
                               individual=indv3)
        org_ex1 = Organization.add_root(name='Example1')
        org_ex2 = Organization.add_root(name='Example2')
        AffiliationRecommendation.objects.create(individual=indv1, organization=org_ex1, applied=True)
        AffiliationRecommendation.objects.create(individual=indv2, organization=org_ex2, applied=False)
        AffiliationRecommendation.objects.create(individual=indv3, organization=org_ex1)

        # Test isApplied true
        client = graphene.test.Client(schema)
        executed = client.execute(SH_AFF_REC_FILTER % "true",
                                  context_value=self.context_value)
        recommendations = executed['data']['recommendedAffiliations']['entities']
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]['individual']['mk'], indv1.mk)
        self.assertEqual(recommendations[0]['organization']['name'], "Example1")

        # Test isApplied false
        client = graphene.test.Client(schema)
        executed = client.execute(SH_AFF_REC_FILTER % "false",
                                  context_value=self.context_value)

        recommendations = executed['data']['recommendedAffiliations']['entities']
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]['individual']['mk'], indv2.mk)
        self.assertEqual(recommendations[0]['organization']['name'], "Example2")

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_AFF_REC_QUERY,
                                  context_value=self.context_value)
        rels = executed['data']['recommendedAffiliations']['entities']
        self.assertListEqual(rels, [])

    def test_pagination(self):
        """Check whether it returns the recommenderExclusionTerms searched when using pagination"""

        indv1 = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               individual=indv1)
        indv2 = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               individual=indv2)
        org_ex1 = Organization.add_root(name='Example1')
        org_ex2 = Organization.add_root(name='Example2')
        rec = AffiliationRecommendation.objects.create(individual=indv1, organization=org_ex1)
        rec = AffiliationRecommendation.objects.create(individual=indv2, organization=org_ex2)

        client = graphene.test.Client(schema)
        test_query = SH_AFF_REC_QUERY_PAGINATION % (1, 1)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        rels = executed['data']['recommendedAffiliations']['entities']

        self.assertEqual(len(rels), 1)

        pag_data = executed['data']['recommendedAffiliations']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 1)
        self.assertEqual(pag_data['numPages'], 2)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 1)
        self.assertEqual(pag_data['totalResults'], 2)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_AFF_REC_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestQueryRecommendedMerge(django.test.TestCase):
    """Unit tests for RecommendedMerge queries"""

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_recommended_merge(self):
        """Check if it returns the registry of RecommendedMerge"""

        indv1 = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               individual=indv1)
        indv2 = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               individual=indv2)
        indv3 = Individual.objects.create(mk='CCCC')
        Profile.objects.create(name='Mary Doe',
                               email='mdoe@bitergia.com',
                               individual=indv3)
        MergeRecommendation.objects.create(individual1=indv1, individual2=indv2)
        MergeRecommendation.objects.create(individual1=indv1, individual2=indv3)

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_MERGE_REC_QUERY,
                                  context_value=self.context_value)

        rels = executed['data']['recommendedMerge']['entities']
        self.assertEqual(len(rels), 2)
        rel1 = rels[0]
        self.assertEqual(rel1['individual1']['mk'], indv1.mk)
        self.assertEqual(rel1['individual2']['mk'], indv2.mk)

        rel1 = rels[1]
        self.assertEqual(rel1['individual1']['mk'], indv1.mk)
        self.assertEqual(rel1['individual2']['mk'], indv3.mk)

    def test_filter_is_applied(self):
        """Check whether it filter recommendations by is_applied"""

        indv1 = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               individual=indv1)
        indv2 = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               individual=indv2)
        indv3 = Individual.objects.create(mk='CCCC')
        Profile.objects.create(name='Mary Doe',
                               email='mdoe@bitergia.com',
                               individual=indv3)
        indv4 = Individual.objects.create(mk='DDDD')
        Profile.objects.create(name='Pepe Doe',
                               email='mdoe@bitergia.com',
                               individual=indv4)
        MergeRecommendation.objects.create(individual1=indv1, individual2=indv2, applied=True)
        MergeRecommendation.objects.create(individual1=indv1, individual2=indv3, applied=False)
        MergeRecommendation.objects.create(individual1=indv1, individual2=indv4)

        # Test isApplied true
        client = graphene.test.Client(schema)
        executed = client.execute(SH_MERGE_REC_FILTER % "true",
                                  context_value=self.context_value)
        recommendations = executed['data']['recommendedMerge']['entities']
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]['individual1']['mk'], indv1.mk)
        self.assertEqual(recommendations[0]['individual2']['mk'], indv2.mk)

        # Test isApplied false
        client = graphene.test.Client(schema)
        executed = client.execute(SH_MERGE_REC_FILTER % "false",
                                  context_value=self.context_value)

        recommendations = executed['data']['recommendedMerge']['entities']
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]['individual1']['mk'], indv1.mk)
        self.assertEqual(recommendations[0]['individual2']['mk'], indv3.mk)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_MERGE_REC_QUERY,
                                  context_value=self.context_value)

        rels = executed['data']['recommendedMerge']['entities']
        self.assertListEqual(rels, [])

    def test_pagination(self):
        """Check whether it returns the recommenderExclusionTerms searched when using pagination"""

        indv1 = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               individual=indv1)
        indv2 = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               individual=indv2)
        indv3 = Individual.objects.create(mk='CCCC')
        Profile.objects.create(name='Mary Doe',
                               email='mdoe@bitergia.com',
                               individual=indv3)
        MergeRecommendation.objects.create(individual1=indv1, individual2=indv2)
        MergeRecommendation.objects.create(individual1=indv1, individual2=indv3)

        client = graphene.test.Client(schema)
        test_query = SH_MERGE_REC_QUERY_PAGINATION % (1, 1)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        rels = executed['data']['recommendedMerge']['entities']

        self.assertEqual(len(rels), 1)

        pag_data = executed['data']['recommendedMerge']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 1)
        self.assertEqual(pag_data['numPages'], 2)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 1)
        self.assertEqual(pag_data['totalResults'], 2)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_MERGE_REC_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestQueryRecommendedGender(django.test.TestCase):
    """Unit tests for RecommendedGender queries"""

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_recommended_gender(self):
        """Check if it returns the registry of GenderRecommendation"""

        indv1 = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               individual=indv1)
        indv2 = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               individual=indv2)
        GenderRecommendation.objects.create(individual=indv1, gender='Male', accuracy=80)
        GenderRecommendation.objects.create(individual=indv2, gender='Female', accuracy=90)

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_GENDER_REC_QUERY,
                                  context_value=self.context_value)

        rels = executed['data']['recommendedGender']['entities']
        self.assertEqual(len(rels), 2)
        rel1 = rels[0]
        self.assertEqual(rel1['individual']['mk'], indv1.mk)
        self.assertEqual(rel1['gender'], 'Male')
        self.assertEqual(rel1['accuracy'], 80)

        rel1 = rels[1]
        self.assertEqual(rel1['individual']['mk'], indv2.mk)
        self.assertEqual(rel1['gender'], 'Female')
        self.assertEqual(rel1['accuracy'], 90)

    def test_filter_is_applied(self):
        """Check whether it filter recommendations by is_applied"""

        indv1 = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               individual=indv1)
        indv2 = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name='May Doe',
                               email='jdoe@bitergia.com',
                               individual=indv2)
        indv3 = Individual.objects.create(mk='CCCC')
        Profile.objects.create(name='May Walker',
                               email='mwalker@bitergia.com',
                               individual=indv3)
        GenderRecommendation.objects.create(individual=indv1, gender='Male', accuracy=80, applied=True)
        GenderRecommendation.objects.create(individual=indv2, gender='Female', accuracy=90, applied=False)
        GenderRecommendation.objects.create(individual=indv3, gender='Female', accuracy=95)

        # Test isApplied true
        client = graphene.test.Client(schema)
        executed = client.execute(SH_GENDER_REC_FILTER % "true",
                                  context_value=self.context_value)
        recommendations = executed['data']['recommendedGender']['entities']
        self.assertEqual(len(recommendations), 1)
        rel1 = recommendations[0]
        self.assertEqual(rel1['individual']['mk'], indv1.mk)
        self.assertEqual(rel1['gender'], 'Male')
        self.assertEqual(rel1['accuracy'], 80)

        # Test isApplied false
        client = graphene.test.Client(schema)
        executed = client.execute(SH_GENDER_REC_FILTER % "false",
                                  context_value=self.context_value)
        recommendations = executed['data']['recommendedGender']['entities']
        self.assertEqual(len(recommendations), 1)
        rel1 = recommendations[0]
        self.assertEqual(rel1['individual']['mk'], indv2.mk)
        self.assertEqual(rel1['gender'], 'Female')
        self.assertEqual(rel1['accuracy'], 90)

        # Test isApplied unknow (no filter)
        client = graphene.test.Client(schema)
        executed = client.execute(SH_GENDER_REC_QUERY,
                                  context_value=self.context_value)
        recommendations = executed['data']['recommendedGender']['entities']
        self.assertEqual(len(recommendations), 1)
        rel1 = recommendations[0]
        self.assertEqual(rel1['individual']['mk'], indv3.mk)
        self.assertEqual(rel1['gender'], 'Female')
        self.assertEqual(rel1['accuracy'], 95)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_GENDER_REC_QUERY,
                                  context_value=self.context_value)
        rels = executed['data']['recommendedGender']['entities']
        self.assertListEqual(rels, [])

    def test_pagination(self):
        """Check whether it returns the recommenderExclusionTerms searched when using pagination"""

        indv1 = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               individual=indv1)
        indv2 = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               individual=indv2)
        GenderRecommendation.objects.create(individual=indv1, gender='Male', accuracy=80)
        GenderRecommendation.objects.create(individual=indv2, gender='Female', accuracy=90)

        client = graphene.test.Client(schema)
        test_query = SH_GENDER_REC_QUERY_PAGINATION % (1, 1)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        rels = executed['data']['recommendedGender']['entities']

        self.assertEqual(len(rels), 1)

        pag_data = executed['data']['recommendedGender']['pageInfo']
        self.assertEqual(len(pag_data), 8)
        self.assertEqual(pag_data['page'], 1)
        self.assertEqual(pag_data['pageSize'], 1)
        self.assertEqual(pag_data['numPages'], 2)
        self.assertTrue(pag_data['hasNext'])
        self.assertFalse(pag_data['hasPrev'])
        self.assertEqual(pag_data['startIndex'], 1)
        self.assertEqual(pag_data['endIndex'], 1)
        self.assertEqual(pag_data['totalResults'], 2)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_GENDER_REC_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class MockJob:
    """Class mock job queries."""

    def __init__(self, job_id, func_name, status, result, error=None):
        self.id = job_id
        self.func_name = func_name
        self.status = status
        self.result = result
        self.exc_info = error
        self.enqueued_at = datetime_utcnow()

    def get_status(self):
        return self.status

    def get_id(self):
        return self.id


class TestQueryJob(django.test.TestCase):
    """Unit tests for job queries"""

    def setUp(self):
        """Set queries context"""

        conn = django_rq.queues.get_redis_connection(None, True)
        conn.flushall()

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    @unittest.mock.patch('sortinghat.core.schema.find_job')
    def test_affiliate_job(self, mock_job):
        """Check if it returns an affiliated result type"""

        result = {
            'results': {
                '0c1e1701bc819495acf77ef731023b7d789a9c71': [],
                '17ab00ed3825ec2f50483e33c88df223264182ba': ['Bitergia', 'Example'],
                'dc31d2afbee88a6d1dbc1ef05ec827b878067744': ['Example']
            },
            'errors': None
        }

        job = MockJob('1234-5678-90AB-CDEF', 'affiliate', 'finished', result)
        mock_job.return_value = job

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_AFFILIATE % '1234-5678-90AB-CDEF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        job_data = executed['data']['job']
        self.assertEqual(job_data['jobId'], '1234-5678-90AB-CDEF')
        self.assertEqual(job_data['jobType'], 'affiliate')
        self.assertEqual(job_data['status'], 'finished')
        self.assertEqual(job_data['errors'], None)

        job_results = job_data['result']
        self.assertEqual(len(job_results), 3)

        res = job_results[0]
        self.assertEqual(res['__typename'], 'AffiliationResultType')
        self.assertEqual(res['uuid'], '0c1e1701bc819495acf77ef731023b7d789a9c71')
        self.assertEqual(res['organizations'], [])

        res = job_results[1]
        self.assertEqual(res['__typename'], 'AffiliationResultType')
        self.assertEqual(res['uuid'], '17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(res['organizations'], ['Bitergia', 'Example'])

        res = job_results[2]
        self.assertEqual(res['__typename'], 'AffiliationResultType')
        self.assertEqual(res['uuid'], 'dc31d2afbee88a6d1dbc1ef05ec827b878067744')
        self.assertEqual(res['organizations'], ['Example'])

    @unittest.mock.patch('sortinghat.core.schema.find_job')
    def test_affiliate_job_no_results(self, mock_job):
        """Check if it does not fail when there are not results ready"""

        job = MockJob('1234-5678-90AB-CDEF', 'affiliate', 'queued', None)
        mock_job.return_value = job

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_AFFILIATE % '1234-5678-90AB-CDEF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        job_data = executed['data']['job']
        self.assertEqual(job_data['jobId'], '1234-5678-90AB-CDEF')
        self.assertEqual(job_data['jobType'], 'affiliate')
        self.assertEqual(job_data['status'], 'queued')
        self.assertEqual(job_data['errors'], None)
        self.assertEqual(job_data['result'], None)

    @unittest.mock.patch('sortinghat.core.schema.find_job')
    def test_affiliate_job_errors(self, mock_job):
        """Check job errors field"""

        errors = [
            "dc31d2afbee88a6d1dbc1ef05ec827b878067744 not found in the registry"
        ]
        result = {
            'results': {
                'dc31d2afbee88a6d1dbc1ef05ec827b878067744': []
            },
            'errors': errors
        }

        job = MockJob('1234-5678-90AB-CDEF', 'affiliate', 'finished', result)
        mock_job.return_value = job

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_AFFILIATE % '1234-5678-90AB-CDEF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        job_data = executed['data']['job']
        self.assertEqual(job_data['jobId'], '1234-5678-90AB-CDEF')
        self.assertEqual(job_data['jobType'], 'affiliate')
        self.assertEqual(job_data['status'], 'finished')
        self.assertEqual(job_data['errors'], errors)

    @unittest.mock.patch('sortinghat.core.schema.find_job')
    def test_recommend_affiliation_job(self, mock_job):
        """Check if it returns an affiliation recommendation type"""

        result = {
            'results': {
                '0c1e1701bc819495acf77ef731023b7d789a9c71': [],
                '17ab00ed3825ec2f50483e33c88df223264182ba': ['Bitergia', 'Example'],
                'dc31d2afbee88a6d1dbc1ef05ec827b878067744': ['Example']
            }
        }

        job = MockJob('1234-5678-90AB-CDEF', 'recommend_affiliations', 'finished', result)
        mock_job.return_value = job

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_RECOMMEND_AFFILIATIONS % '1234-5678-90AB-CDEF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        job_data = executed['data']['job']
        self.assertEqual(job_data['jobId'], '1234-5678-90AB-CDEF')
        self.assertEqual(job_data['jobType'], 'recommend_affiliations')
        self.assertEqual(job_data['status'], 'finished')
        self.assertEqual(job_data['errors'], None)

        job_results = job_data['result']
        self.assertEqual(len(job_results), 3)

        res = job_results[0]
        self.assertEqual(res['__typename'], 'AffiliationRecommendationType')
        self.assertEqual(res['uuid'], '0c1e1701bc819495acf77ef731023b7d789a9c71')
        self.assertEqual(res['organizations'], [])

        res = job_results[1]
        self.assertEqual(res['__typename'], 'AffiliationRecommendationType')
        self.assertEqual(res['uuid'], '17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(res['organizations'], ['Bitergia', 'Example'])

        res = job_results[2]
        self.assertEqual(res['__typename'], 'AffiliationRecommendationType')
        self.assertEqual(res['uuid'], 'dc31d2afbee88a6d1dbc1ef05ec827b878067744')
        self.assertEqual(res['organizations'], ['Example'])

    @unittest.mock.patch('sortinghat.core.schema.find_job')
    def test_recommend_affiliation_job_no_results(self, mock_job):
        """Check if it does not fail when there are not results ready"""

        job = MockJob('1234-5678-90AB-CDEF', 'recommend_affiliations', 'queued', None)
        mock_job.return_value = job

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_RECOMMEND_AFFILIATIONS % '1234-5678-90AB-CDEF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        job_data = executed['data']['job']
        self.assertEqual(job_data['jobId'], '1234-5678-90AB-CDEF')
        self.assertEqual(job_data['jobType'], 'recommend_affiliations')
        self.assertEqual(job_data['status'], 'queued')
        self.assertEqual(job_data['errors'], None)
        self.assertEqual(job_data['result'], None)

    @unittest.mock.patch('sortinghat.core.schema.find_job')
    def test_recommend_matches_job(self, mock_job):
        """Check if it returns a matches recommendation type"""

        result = {
            'results': {
                '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331':
                    ['400fdfaab5918d1b7e0e0efba4797abdc378bd7d',
                     '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'],
                '54806f99212ac5de67684dabda6db139fc6507ee':
                    ['9cb28b6fb034393bbe4749081e0da6cc5a715b85',
                     'bc02398823c5a8f3cb77fa77b183119a7d6685d8'],
                'e00e8f2480021ce2b9e78fc8cfcab81be1f4d3a6':
                    ['9cb28b6fb034393bbe4749081e0da6cc5a715b85',
                     'bc02398823c5a8f3cb77fa77b183119a7d6685d8']
            }
        }

        job = MockJob('1234-5678-90AB-CDEF', 'recommend_matches', 'finished', result)
        mock_job.return_value = job

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_RECOMMEND_MATCHES % '1234-5678-90AB-CDEF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        job_data = executed['data']['job']
        self.assertEqual(job_data['jobId'], '1234-5678-90AB-CDEF')
        self.assertEqual(job_data['jobType'], 'recommend_matches')
        self.assertEqual(job_data['status'], 'finished')
        self.assertEqual(job_data['errors'], None)

        job_results = job_data['result']
        self.assertEqual(len(job_results), 3)

        res = job_results[0]
        self.assertEqual(res['__typename'], 'MatchesRecommendationType')
        self.assertEqual(res['uuid'], '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(res['matches'], ['400fdfaab5918d1b7e0e0efba4797abdc378bd7d',
                                          '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'])

        res = job_results[1]
        self.assertEqual(res['__typename'], 'MatchesRecommendationType')
        self.assertEqual(res['uuid'], '54806f99212ac5de67684dabda6db139fc6507ee')
        self.assertEqual(res['matches'], ['9cb28b6fb034393bbe4749081e0da6cc5a715b85',
                                          'bc02398823c5a8f3cb77fa77b183119a7d6685d8'])

        res = job_results[2]
        self.assertEqual(res['__typename'], 'MatchesRecommendationType')
        self.assertEqual(res['uuid'], 'e00e8f2480021ce2b9e78fc8cfcab81be1f4d3a6')
        self.assertEqual(res['matches'], ['9cb28b6fb034393bbe4749081e0da6cc5a715b85',
                                          'bc02398823c5a8f3cb77fa77b183119a7d6685d8'])

    @unittest.mock.patch('sortinghat.core.schema.find_job')
    def test_recommend_matches_job_no_results(self, mock_job):
        """Check if it does not fail when there are not results ready"""

        job = MockJob('1234-5678-90AB-CDEF', 'recommend_matches', 'queued', None)
        mock_job.return_value = job

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_RECOMMEND_MATCHES % '1234-5678-90AB-CDEF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        job_data = executed['data']['job']
        self.assertEqual(job_data['jobId'], '1234-5678-90AB-CDEF')
        self.assertEqual(job_data['jobType'], 'recommend_matches')
        self.assertEqual(job_data['status'], 'queued')
        self.assertEqual(job_data['errors'], None)
        self.assertEqual(job_data['result'], None)

    @unittest.mock.patch('sortinghat.core.schema.find_job')
    def test_unify_job(self, mock_job):
        """Check if it returns a unify result type"""

        result = {
            'results': ['880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'],
            'errors': None
        }

        job = MockJob('90AB-CD12-3456-78EF', 'unify', 'finished', result)
        mock_job.return_value = job

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_UNIFY % '90AB-CD12-3456-78EF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        job_data = executed['data']['job']
        self.assertEqual(job_data['jobId'], '90AB-CD12-3456-78EF')
        self.assertEqual(job_data['jobType'], 'unify')
        self.assertEqual(job_data['status'], 'finished')
        self.assertEqual(job_data['errors'], None)

        job_results = job_data['result']
        self.assertEqual(len(job_results), 1)

        res = job_results[0]
        self.assertEqual(res['__typename'], 'UnifyResultType')
        self.assertEqual(res['merged'], ['880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'])

    @unittest.mock.patch('sortinghat.core.schema.find_job')
    def test_unify_job_no_results(self, mock_job):
        """Check if it does not fail when there are not results ready"""

        job = MockJob('90AB-CD12-3456-78EF', 'unify', 'queued', None)
        mock_job.return_value = job

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_UNIFY % '90AB-CD12-3456-78EF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        job_data = executed['data']['job']
        self.assertEqual(job_data['jobId'], '90AB-CD12-3456-78EF')
        self.assertEqual(job_data['jobType'], 'unify')
        self.assertEqual(job_data['status'], 'queued')
        self.assertEqual(job_data['errors'], None)
        self.assertEqual(job_data['result'], None)

    def test_job_not_found(self):
        """Check if it returns an error when the job is not found"""

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_AFFILIATE % '1234-5678-90AB-CDEF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, "1234-5678-90AB-CDEF not found in the registry")

    @unittest.mock.patch('sortinghat.core.schema.find_job')
    def test_failed_job(self, mock_job):
        """Check if it returns an error when the job has failed"""

        job = MockJob('90AB-CD12-3456-78EF', 'unify', 'failed', None, 'Error')
        mock_job.return_value = job

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_UNIFY % '90AB-CD12-3456-78EF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        job_data = executed['data']['job']
        self.assertEqual(job_data['status'], 'failed')
        self.assertEqual(job_data['errors'], ['Error'])

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(SH_ORGS_QUERY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)

    @unittest.mock.patch('sortinghat.core.schema.get_jobs')
    def test_jobs(self, mock_jobs):
        """Check if it returns a list of jobs"""

        job = MockJob('1234-5678-90AB-CDEF', 'affiliate', 'queued', None)
        mock_jobs.return_value = [job]

        # Tests
        client = graphene.test.Client(schema)

        executed = client.execute(SH_JOBS_QUERY,
                                  context_value=self.context_value)

        jobs_entities = executed['data']['jobs']['entities']
        self.assertEqual(len(jobs_entities), 1)
        self.assertEqual(jobs_entities[0]['jobId'], '1234-5678-90AB-CDEF')
        self.assertEqual(jobs_entities[0]['jobType'], 'affiliate')
        self.assertEqual(jobs_entities[0]['status'], 'queued')
        self.assertEqual(jobs_entities[0]['errors'], [])
        self.assertEqual(jobs_entities[0]['result'], [])

    def test_jobs_no_results(self):
        """Check if it returns an empty list when no jobs are found"""

        client = graphene.test.Client(schema)

        executed = client.execute(SH_JOBS_QUERY,
                                  context_value=self.context_value)

        jobs_entities = executed['data']['jobs']['entities']
        self.assertEqual(len(jobs_entities), 0)

    @unittest.mock.patch('sortinghat.core.schema.get_jobs')
    def test_jobs_pagination(self, mock_jobs):
        """Check if it returns a paginated list of jobs"""

        job1 = MockJob('1234-5678-90AB-CDEF', 'affiliate', 'queued', None)
        job2 = MockJob('5678-5678-90EF-GHIJ', 'unify', 'queued', None)
        job3 = MockJob('9123-5678-90IJ-KLMN', 'recommend_matches', 'queued', None)
        mock_jobs.return_value = [job1, job2, job3]

        # Tests
        client = graphene.test.Client(schema)
        test_query = SH_JOBS_QUERY_PAGINATION % (2, 2)
        executed = client.execute(test_query,
                                  context_value=self.context_value)

        jobs_entities = executed['data']['jobs']['entities']
        self.assertEqual(len(jobs_entities), 1)
        self.assertEqual(jobs_entities[0]['jobId'], '9123-5678-90IJ-KLMN')
        self.assertEqual(jobs_entities[0]['jobType'], 'recommend_matches')
        self.assertEqual(jobs_entities[0]['status'], 'queued')
        self.assertEqual(jobs_entities[0]['errors'], [])

        jobs_pagination = executed['data']['jobs']['pageInfo']
        self.assertEqual(jobs_pagination['page'], 2)
        self.assertEqual(jobs_pagination['pageSize'], 2)
        self.assertEqual(jobs_pagination['numPages'], 2)
        self.assertFalse(jobs_pagination['hasNext'])
        self.assertTrue(jobs_pagination['hasPrev'])
        self.assertEqual(jobs_pagination['startIndex'], 3)
        self.assertEqual(jobs_pagination['endIndex'], 3)
        self.assertEqual(jobs_pagination['totalResults'], 3)

    @unittest.mock.patch('sortinghat.core.schema.find_job')
    def test_recommend_gender_job(self, mock_job):
        """Check if it returns a gender recommendation type"""

        result = {
            'results': {
                '0c1e1701bc819495acf77ef731023b7d789a9c71': {
                    'gender': 'male',
                    'accuracy': 78
                },
                '17ab00ed3825ec2f50483e33c88df223264182ba': {
                    'gender': 'female',
                    'accuracy': 98
                }
            }
        }

        job = MockJob('1234-5678-90AB-CDEF', 'recommend_gender', 'finished', result)
        mock_job.return_value = job

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_RECOMMEND_GENDER % '1234-5678-90AB-CDEF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        job_data = executed['data']['job']

        self.assertEqual(job_data['jobId'], '1234-5678-90AB-CDEF')
        self.assertEqual(job_data['jobType'], 'recommend_gender')
        self.assertEqual(job_data['status'], 'finished')
        self.assertEqual(job_data['errors'], None)

        job_results = job_data['result']
        self.assertEqual(len(job_results), 2)

        res = job_results[0]
        self.assertEqual(res['__typename'], 'GenderRecommendationType')
        self.assertEqual(res['uuid'], '0c1e1701bc819495acf77ef731023b7d789a9c71')
        self.assertEqual(res['gender'], 'male')
        self.assertEqual(res['accuracy'], 78)

        res = job_results[1]
        self.assertEqual(res['__typename'], 'GenderRecommendationType')
        self.assertEqual(res['uuid'], '17ab00ed3825ec2f50483e33c88df223264182ba')
        self.assertEqual(res['gender'], 'female')
        self.assertEqual(res['accuracy'], 98)

    @unittest.mock.patch('sortinghat.core.schema.find_job')
    def test_recommend_gender_job_no_results(self, mock_job):
        """Check if it does not fail when there are not results ready"""

        job = MockJob('1234-5678-90AB-CDEF', 'recommend_gender', 'queued', None)
        mock_job.return_value = job

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_RECOMMEND_GENDER % '1234-5678-90AB-CDEF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        job_data = executed['data']['job']
        self.assertEqual(job_data['jobId'], '1234-5678-90AB-CDEF')
        self.assertEqual(job_data['jobType'], 'recommend_gender')
        self.assertEqual(job_data['status'], 'queued')
        self.assertEqual(job_data['errors'], None)
        self.assertEqual(job_data['result'], None)

    @unittest.mock.patch('sortinghat.core.schema.find_job')
    def test_genderize_job(self, mock_job):
        """Check if it returns an genderize result type"""

        result = {
            'results': {
                'f507a33bbeffe58ae3eb192fc371e7cea65488f6': ('male', 95)
            },
            'errors': []
        }

        job = MockJob('1234-5678-90AB-CDEF', 'genderize', 'finished', result)
        mock_job.return_value = job

        # Tests
        client = graphene.test.Client(schema)

        query = SH_JOB_QUERY_GENDERIZE % '1234-5678-90AB-CDEF'

        executed = client.execute(query,
                                  context_value=self.context_value)

        job_data = executed['data']['job']

        self.assertEqual(job_data['jobId'], '1234-5678-90AB-CDEF')
        self.assertEqual(job_data['jobType'], 'genderize')
        self.assertEqual(job_data['status'], 'finished')

        job_results = job_data['result']
        self.assertEqual(len(job_results), 1)

        res = job_results[0]
        self.assertEqual(res['__typename'], 'GenderizeResultType')
        self.assertEqual(res['uuid'], 'f507a33bbeffe58ae3eb192fc371e7cea65488f6')
        self.assertEqual(res['gender'], 'male')


class TestAddOrganizationMutation(django.test.TestCase):
    """Unit tests for mutation to add organizations"""

    SH_ADD_ORG = """
      mutation addOrg {
        addOrganization(name: "Example") {
          organization {
            name
            domains {
              domain
              isTopDomain
            }
          }
        }
      }
    """

    SH_ADD_ORG_NAME_EMPTY = """
      mutation addOrg {
        addOrganization(name: "") {
          organization {
            name
            domains {
              domain
              isTopDomain
            }
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_add_organization(self):
        """Check if a new organization is added"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG,
                                  context_value=self.context_value)

        # Check result
        org = executed['data']['addOrganization']['organization']
        self.assertEqual(org['name'], 'Example')
        self.assertListEqual(org['domains'], [])

        # Check database
        org = Organization.objects.get(name='Example')
        self.assertEqual(org.name, 'Example')

    def test_name_empty(self):
        """Check whether organizations with empty names cannot be added"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG_NAME_EMPTY,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, NAME_EMPTY_ERROR)

        # Check database
        orgs = Organization.objects.all()
        self.assertEqual(len(orgs), 0)

    def test_integrity_error(self):
        """Check whether organizations with the same name cannot be inserted"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG,
                                  context_value=self.context_value)

        # Check database
        org = Organization.objects.get(name='Example')
        self.assertEqual(org.name, 'Example')

        # Try to insert it twice
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_ORG_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_ADD_ORG,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestDeleteOrganizationMutation(django.test.TestCase):
    """Unit tests for mutation to delete organizations"""

    SH_DELETE_ORG = """
      mutation delOrg {
        deleteOrganization(name: "Example") {
          organization {
            name
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_delete_organization(self):
        """Check whether it deletes an organization"""

        org_ex = Organization.add_root(name='Example')
        Domain.objects.create(domain='example.org',
                              organization=org_ex)
        org_bit = Organization.add_root(name='Bitergia')

        jsmith = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               individual=jsmith)
        Enrollment.objects.create(individual=jsmith, group=org_ex)

        jdoe = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               individual=jdoe)
        Enrollment.objects.create(individual=jdoe, group=org_ex)
        Enrollment.objects.create(individual=jdoe, group=org_bit)

        # Delete organization
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_ORG,
                                  context_value=self.context_value)

        # Check result
        org = executed['data']['deleteOrganization']['organization']
        self.assertEqual(org['name'], 'Example')

        # Tests
        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            Organization.objects.get(name='Example')

        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            Domain.objects.get(domain='example.org')

        enrollments = Enrollment.objects.filter(group__name='Example')
        self.assertEqual(len(enrollments), 0)

        enrollments = Enrollment.objects.filter(group__name='Bitergia')
        self.assertEqual(len(enrollments), 1)

    def test_not_found_organization(self):
        """Check if it returns an error when an organization does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_ORG,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_EXAMPLE_DOES_NOT_EXIST_ERROR)

        # It should not remove anything
        Organization.add_root(name='Bitergia')

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_EXAMPLE_DOES_NOT_EXIST_ERROR)

        orgs = Organization.objects.all()
        self.assertEqual(len(orgs), 1)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_DELETE_ORG,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestAddTeamMutation(django.test.TestCase):
    """Unit tests for mutation to add teams"""

    SH_ADD_TEAM = """
      mutation {
        addTeam(teamName: "Example_team", organization: "Example") {
          team {
            name
            parentOrg {
              name
            }
          }
        }
      }
    """

    SH_ADD_SUBTEAM = """
          mutation {
            addTeam(teamName: "Example_subteam", parentName: "Example_team") {
              team {
                name
                parentOrg {
                  name
                }
              }
            }
          }
    """

    SH_ADD_TEAM_EMPTY = """
      mutation {
        addTeam(teamName: "", organization: "Example") {
          team {
            name
          }
        }
      }
    """

    SH_ADD_ORG_EMPTY = """
      mutation {
        addTeam(teamName: "Example_team") {
          team {
            name
            parentOrg {
              name
            }
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_add_team(self):
        """Check if a new team is added"""

        Organization.add_root(name='Example')

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_TEAM,
                                  context_value=self.context_value)

        # Check result
        team = executed['data']['addTeam']['team']
        self.assertEqual(team['name'], 'Example_team')
        self.assertEqual(team['parentOrg']['name'], 'Example')

        # Check database
        org = Organization.objects.all_organizations().get(name='Example')
        teams = org.teams.all()
        self.assertEqual(len(teams), 1)

        team = teams[0]
        self.assertEqual(team.name, 'Example_team')

    def test_no_org_team(self):
        """Check whether teams can be added without organization"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG_EMPTY,
                                  context_value=self.context_value)

        # Check result
        team = executed['data']['addTeam']['team']
        self.assertEqual(team['name'], 'Example_team')
        self.assertEqual(team['parentOrg'], None)

    def test_add_subteam(self):
        """Check if a team can be made as a subteam"""

        client = graphene.test.Client(schema)
        client.execute(self.SH_ADD_ORG_EMPTY,
                       context_value=self.context_value)

        client = graphene.test.Client(schema)
        subteam = client.execute(self.SH_ADD_SUBTEAM,
                                 context_value=self.context_value)

        # Check result
        subteam = subteam['data']['addTeam']['team']
        self.assertEqual(subteam['name'], 'Example_subteam')
        self.assertEqual(subteam['parentOrg'], None)

        team = Team.objects.get(name="Example_team")
        subteam = Team.objects.get(name="Example_subteam")
        self.assertTrue(subteam.is_child_of(team))

    def test_team_empty(self):
        """Check whether teams with empty names cannot be added"""

        Organization.add_root(name='Example')

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_TEAM_EMPTY,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, TEAM_NAME_EMPTY_ERROR)

        # Check database
        teams = Team.objects.all_teams()
        self.assertEqual(len(teams), 0)

    def test_integrity_error(self):
        """Check whether teams with the same team name cannot be inserted"""

        Organization.add_root(name='Example')

        client = graphene.test.Client(schema)
        client.execute(self.SH_ADD_TEAM, context_value=self.context_value)

        # Check database
        team = Team.objects.get(name='Example_team')
        self.assertEqual(team.name, 'Example_team')
        self.assertEqual(team.parent_org.name, 'Example')

        # Try to insert it twice
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_TEAM,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_TEAM_ERROR)

    def test_not_found_organization(self):
        """Check if it returns an error when an organization does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_TEAM,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_EXAMPLE_DOES_NOT_EXIST_ERROR)

    def test_not_found_parent(self):
        """Check if it returns an error when a parent does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_SUBTEAM,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, TEAM_EXAMPLE_DOES_NOT_EXIST_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_ADD_TEAM,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestDeleteTeamMutation(django.test.TestCase):
    """Unit tests for mutation to delete teams"""

    SH_DELETE_TEAM = """
      mutation delT {
        deleteTeam(teamName: "Example_team", organization: "Example") {
          team {
            name
          }
        }
      }
    """

    SH_DELETE_TEAM_NO_ORG = """
      mutation delT {
        deleteTeam(teamName: "Example_team", organization: "Example") {
          team {
            name
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_delete_team(self):
        """Check whether it deletes a team"""

        org = Organization.add_root(name='Example')
        Team.add_root(name='Example_team', parent_org=org)

        # Delete team
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_TEAM,
                                  context_value=self.context_value)

        # Check result
        team = executed['data']['deleteTeam']['team']
        self.assertEqual(team['name'], 'Example_team')

        # Tests
        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            Team.objects.all_teams().get(name='Example_team')

        teams = Team.objects.all_teams()
        self.assertEqual(len(teams), 0)

    def test_delete_no_org_team(self):
        """Check if it deletes a team that does not belong to any organization"""

        org = Organization.add_root(name='Example')
        org.add_child(name='Example_team', parent_org=org, type='team')
        Team.add_root(name='Example_team', parent_org=None)

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_TEAM_NO_ORG,
                                  context_value=self.context_value)

        # Check result
        team = executed['data']['deleteTeam']['team']
        self.assertEqual(team['name'], 'Example_team')

        # Check if other team still exists
        teams = Team.objects.all_teams()
        self.assertEqual(len(teams), 1)

        team = teams[0]
        self.assertEqual(team.name, 'Example_team')
        self.assertEqual(team.parent_org, None)

    def test_not_found_team_in_org(self):
        """Check if it returns an error when a team does not
           exist in the given organization"""

        org = Group.add_root(name='Example', type='organization')
        org.add_child(name='Example_different_team', parent_org=org, type='team')

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_TEAM,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, TEAM_EXAMPLE_DOES_NOT_EXIST_ERROR)

        # It should not remove anything
        teams = Team.objects.all_teams()
        self.assertEqual(len(teams), 1)

    def test_not_found_org(self):
        """Check if it returns an error when a organization doesnt exist"""

        org = Organization.add_root(name='ORG')
        org.add_child(name='Example_team', parent_org=org, type='team')

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_TEAM,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_EXAMPLE_DOES_NOT_EXIST_ERROR)

        # It should not remove anything
        teams = Team.objects.all_teams()
        self.assertEqual(len(teams), 1)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_DELETE_TEAM,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestAddDomainMutation(django.test.TestCase):
    """Unit tests for mutation to add domains"""

    SH_ADD_DOMAIN = """
      mutation addDom {
        addDomain(organization: "Example",
                  domain: "example.net"
                  isTopDomain: true)
        {
          domain {
            domain
            isTopDomain
            organization {
              name
            }
          }
        }
      }
    """

    SH_ADD_DOMAIN_EMPTY = """
      mutation addDom {
        addDomain(organization: "Example",
                  domain: ""
                  isTopDomain: true)
        {
          domain {
            domain
            isTopDomain
            organization {
              name
            }
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_add_domain(self):
        """Check if a new domain is added"""

        Organization.add_root(name='Example')

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_DOMAIN,
                                  context_value=self.context_value)

        # Check result
        dom = executed['data']['addDomain']['domain']
        self.assertEqual(dom['domain'], 'example.net')
        self.assertEqual(dom['isTopDomain'], True)
        self.assertEqual(dom['organization']['name'], 'Example')

        # Check database
        org = Organization.objects.get(name='Example')
        domains = org.domains.all()
        self.assertEqual(len(domains), 1)

        dom = domains[0]
        self.assertEqual(dom.domain, 'example.net')
        self.assertEqual(dom.is_top_domain, True)

    def test_domain_empty(self):
        """Check whether domains with empty names cannot be added"""

        Organization.add_root(name='Example')

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_DOMAIN_EMPTY,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DOMAIN_NAME_EMPTY_ERROR)

        # Check database
        domains = Domain.objects.all()
        self.assertEqual(len(domains), 0)

    def test_integrity_error(self):
        """Check whether domains with the same domain name cannot be inserted"""

        Organization.add_root(name='Example')

        client = graphene.test.Client(schema)
        client.execute(self.SH_ADD_DOMAIN, context_value=self.context_value)

        # Check database
        dom = Domain.objects.get(domain='example.net')
        self.assertEqual(dom.domain, 'example.net')

        # Try to insert it twice
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_DOMAIN,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_DOM_ERROR)

    def test_not_found_organization(self):
        """Check if it returns an error when an organization does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_DOMAIN,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_EXAMPLE_DOES_NOT_EXIST_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_ADD_DOMAIN,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestDeleteDomainMutation(django.test.TestCase):
    """Unit tests for mutation to delete domains"""

    SH_DELETE_DOMAIN = """
      mutation delDom {
        deleteDomain(domain: "example.net") {
          domain {
            domain
            isTopDomain
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_delete_domain(self):
        """Check whether it deletes a domain"""

        org = Organization.add_root(name='Example')
        Domain.objects.create(domain='example.net', organization=org)
        Domain.objects.create(domain='example.com', organization=org)

        # Delete organization
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_DOMAIN,
                                  context_value=self.context_value)

        # Check result
        dom = executed['data']['deleteDomain']['domain']
        self.assertEqual(dom['domain'], 'example.net')

        # Tests
        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            Domain.objects.get(domain='example.net')

        domains = Domain.objects.all()
        self.assertEqual(len(domains), 1)

    def test_not_found_domain(self):
        """Check if it returns an error when a domain does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_DOMAIN,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DOMAIN_NOT_FOUND_ERROR)

        # It should not remove anything
        org = Organization.add_root(name='Bitergia')
        Domain.objects.create(domain='example.com', organization=org)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DOMAIN_NOT_FOUND_ERROR)

        domains = Domain.objects.all()
        self.assertEqual(len(domains), 1)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_DELETE_DOMAIN,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestAddIdentityMutation(django.test.TestCase):
    """Unit tests for mutation to add identities"""

    SH_ADD_IDENTITY = """
      mutation addId(
        $source: String,
        $name: String,
        $email: String,
        $username: String
        $uuid: String) {
          addIdentity(
            source: $source
            name: $name
            email: $email
            username: $username
            uuid: $uuid) {
              uuid
              individual {
                mk
                identities {
                  uuid
                  name
                  email
                  username
                  source
                }
                profile {
                  name
                  email
                }
              }
          }
        }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

    def test_add_new_identities(self):
        """Check if everything goes OK when adding new identities"""

        client = graphene.test.Client(schema)

        params = {
            'source': 'scm',
            'name': 'Jane Roe',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results
        individual = executed['data']['addIdentity']['individual']
        self.assertEqual(individual['mk'], 'eda9f62ad321b1fbe5f283cc05e2484516203117')

        identities = individual['identities']
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity['uuid'], 'eda9f62ad321b1fbe5f283cc05e2484516203117')
        self.assertEqual(identity['source'], 'scm')
        self.assertEqual(identity['name'], 'Jane Roe')
        self.assertEqual(identity['email'], 'jroe@example.com')
        self.assertEqual(identity['username'], 'jrae')

        uuid = executed['data']['addIdentity']['uuid']
        self.assertEqual(uuid, 'eda9f62ad321b1fbe5f283cc05e2484516203117')

        # Check database
        individual = Individual.objects.get(mk='eda9f62ad321b1fbe5f283cc05e2484516203117')
        self.assertEqual(individual.mk, identity['uuid'])

        identities = Identity.objects.filter(uuid=identity['uuid'])
        self.assertEqual(len(identities), 1)

        id0 = identities[0]
        self.assertEqual(id0.source, identity['source'])
        self.assertEqual(id0.name, identity['name'])
        self.assertEqual(id0.email, identity['email'])
        self.assertEqual(id0.username, identity['username'])

    def test_add_existing_uuid(self):
        """Check it it adds an identity to an existing individual"""

        individual = Individual.objects.create(mk='eda9f62ad321b1fbe5f283cc05e2484516203117')
        Identity.objects.create(uuid='eda9f62ad321b1fbe5f283cc05e2484516203117',
                                source='scm',
                                name='Jane Roe',
                                email='jroe@example.com',
                                username='jrae',
                                individual=individual)

        client = graphene.test.Client(schema)

        params = {
            'source': 'mls',
            'name': 'Jane Roe',
            'email': 'jroe@example.com',
            'username': 'jrae',
            'uuid': 'eda9f62ad321b1fbe5f283cc05e2484516203117'
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results
        individual = executed['data']['addIdentity']['individual']
        self.assertEqual(individual['mk'], 'eda9f62ad321b1fbe5f283cc05e2484516203117')

        identities = individual['identities']
        self.assertEqual(len(identities), 2)

        identity = identities[0]
        self.assertEqual(identity['uuid'], '55d88f85a41f3a9afa4dc9d4dfb6009c62f42fe3')
        self.assertEqual(identity['source'], 'mls')
        self.assertEqual(identity['name'], 'Jane Roe')
        self.assertEqual(identity['email'], 'jroe@example.com')
        self.assertEqual(identity['username'], 'jrae')

        uuid = executed['data']['addIdentity']['uuid']
        self.assertEqual(uuid, '55d88f85a41f3a9afa4dc9d4dfb6009c62f42fe3')

        # Check database
        identities = Identity.objects.filter(individual__mk='eda9f62ad321b1fbe5f283cc05e2484516203117')
        self.assertEqual(len(identities), 2)

    def test_non_existing_uuid(self):
        """Check if it fails adding identities to individuals that do not exist"""

        client = graphene.test.Client(schema)

        params = {
            'source': 'mls',
            'email': 'jroe@example.com',
            'uuid': 'FFFFFFFFFFFFFFF'
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INDIVIDUAL_DOES_NOT_EXIST_ERROR)

    def test_add_identity_name_none(self):
        """Check if the username is set to the profile when no name is provided"""

        client = graphene.test.Client(schema)

        params = {
            'source': 'scm',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results
        individual = executed['data']['addIdentity']['individual']
        self.assertEqual(individual['mk'], '23dbd01fd319999965e95115ba8e59d9502e13ba')

        profile = individual['profile']
        # The profile name must match with the username, as no name was provided
        self.assertEqual(profile['name'], 'jrae')
        self.assertEqual(profile['email'], 'jroe@example.com')

        identities = individual['identities']
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity['uuid'], '23dbd01fd319999965e95115ba8e59d9502e13ba')
        self.assertEqual(identity['source'], 'scm')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jroe@example.com')
        self.assertEqual(identity['username'], 'jrae')

        uuid = executed['data']['addIdentity']['uuid']
        self.assertEqual(uuid, '23dbd01fd319999965e95115ba8e59d9502e13ba')

        # Check database
        individual = Individual.objects.get(mk='23dbd01fd319999965e95115ba8e59d9502e13ba')
        self.assertEqual(individual.mk, identity['uuid'])

        profile = Profile.objects.get(individual=individual)
        self.assertEqual(profile.name, 'jrae')
        self.assertEqual(profile.email, 'jroe@example.com')

        identities = Identity.objects.filter(uuid=identity['uuid'])
        self.assertEqual(len(identities), 1)

        id0 = identities[0]
        self.assertEqual(id0.source, identity['source'])
        self.assertEqual(id0.name, identity['name'])
        self.assertEqual(id0.email, identity['email'])
        self.assertEqual(id0.username, identity['username'])

    def test_integrity_error(self):
        """Check if it fails adding an identity that already exists"""

        individual = Individual.objects.create(mk='eda9f62ad321b1fbe5f283cc05e2484516203117')
        Identity.objects.create(uuid='eda9f62ad321b1fbe5f283cc05e2484516203117',
                                source='scm',
                                name='Jane Roe',
                                email='jroe@example.com',
                                username='jrae',
                                individual=individual)

        client = graphene.test.Client(schema)

        # Tests
        params = {
            'source': 'scm',
            'name': 'Jane Roe',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_INDIVIDUAL)

        # Different case letters, but same identity
        params = {
            'source': 'scm',
            'name': 'jane roe',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_INDIVIDUAL)

        # Different accents, but same identity
        params = {
            'source': 'scm',
            'name': 'Jane Röe',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_INDIVIDUAL)

    def test_empty_source(self):
        """Check whether new identities cannot be added when giving an empty source"""

        client = graphene.test.Client(schema)

        params = {'source': ''}
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, SOURCE_EMPTY_ERROR)

    def test_none_or_empty_data(self):
        """Check whether new identities cannot be added when identity data is None or empty"""

        client = graphene.test.Client(schema)

        # Tests
        params = {
            'source': 'scm',
            'name': '',
            'email': None,
            'username': None,
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, IDENTITY_EMPTY_DATA_ERROR)

        params = {
            'source': 'scm',
            'name': '',
            'email': '',
            'username': '',
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, IDENTITY_EMPTY_DATA_ERROR)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        client = graphene.test.Client(schema)

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.lock(self.ctx, jsmith.uuid)

        # Tests
        params = {
            'source': 'git',
            'email': 'jsmith-git@example',
            'uuid': jsmith.uuid
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_LOCKED_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'source': 'scm',
            'name': 'Jane Roe',
            'email': 'jroe@example.com',
            'username': 'jrae',
        }
        executed = client.execute(self.SH_ADD_IDENTITY,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestDeleteIdentityMutation(django.test.TestCase):
    """Unit tests for mutation to delete identities"""

    SH_DELETE_IDENTITY = """
      mutation delId($uuid: String) {
        deleteIdentity(uuid: $uuid) {
          uuid
          individual {
            mk
            identities {
              uuid
              name
              email
              username
              source
            }
          }
        }
      }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        # Transaction
        self.trxl = TransactionsLog.open('delete_identity', self.ctx)

        # Organizations
        example_org = db.add_organization(self.trxl, 'Example')
        bitergia_org = db.add_organization(self.trxl, 'Bitergia')
        libresoft_org = db.add_organization(self.trxl, 'LibreSoft')

        # Identities
        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_identity(self.ctx,
                         'scm',
                         name='John Smith',
                         email='jsmith@example',
                         uuid=jsmith.uuid)
        Enrollment.objects.create(individual=jsmith.individual,
                                  group=example_org)
        Enrollment.objects.create(individual=jsmith.individual,
                                  group=bitergia_org)

        jdoe = api.add_identity(self.ctx, 'scm', email='jdoe@example')
        Enrollment.objects.create(individual=jdoe.individual,
                                  group=example_org)

        jrae = api.add_identity(self.ctx,
                                'scm',
                                name='Jane Rae',
                                email='jrae@example')
        Enrollment.objects.create(individual=jrae.individual,
                                  group=libresoft_org)

    def test_delete_identity(self):
        """Check if everything goes OK when deleting identities"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': '1387b129ab751a3657312c09759caa41dfd8d07d',
        }
        executed = client.execute(self.SH_DELETE_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, only one identity remains
        individual = executed['data']['deleteIdentity']['individual']
        self.assertEqual(individual['mk'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(len(individual['identities']), 1)

        identity = individual['identities'][0]
        self.assertEqual(identity['source'], 'scm')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith@example')
        self.assertEqual(identity['username'], None)
        self.assertEqual(identity['uuid'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        uuid = executed['data']['deleteIdentity']['uuid']
        self.assertEqual(uuid, '1387b129ab751a3657312c09759caa41dfd8d07d')

        # Check database
        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            Individual.objects.get(mk='eda9f62ad321b1fbe5f283cc05e2484516203117')

        identities = Identity.objects.filter(uuid=identity['uuid'])
        self.assertEqual(len(identities), 1)

        id0 = identities[0]
        self.assertEqual(id0.source, identity['source'])
        self.assertEqual(id0.name, identity['name'])
        self.assertEqual(id0.email, identity['email'])
        self.assertEqual(id0.username, identity['username'])

    def test_delete_individual(self):
        """Check if everything goes OK when deleting individuals"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
        }
        executed = client.execute(self.SH_DELETE_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results
        individual = executed['data']['deleteIdentity']['individual']
        self.assertEqual(individual, None)

        uuid = executed['data']['deleteIdentity']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            Individual.objects.get(mk='eda9f62ad321b1fbe5f283cc05e2484516203117')

    def test_non_existing_uuid(self):
        """Check if it fails removing identities or individuals that do not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'FFFFFFFFFFFFFFF'
        }
        executed = client.execute(self.SH_DELETE_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INDIVIDUAL_DOES_NOT_EXIST_ERROR)

    def test_empty_uuid(self):
        """Check whether identities cannot be removed when giving an empty UUID"""

        client = graphene.test.Client(schema)

        params = {'uuid': ''}
        executed = client.execute(self.SH_DELETE_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_EMPTY_ERROR)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        client = graphene.test.Client(schema)

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'
        api.lock(self.ctx, uuid)

        # Tests
        params = {
            'uuid': uuid,
        }
        executed = client.execute(self.SH_DELETE_IDENTITY,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_LOCKED_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'uuid': '1387b129ab751a3657312c09759caa41dfd8d07d',
        }
        executed = client.execute(self.SH_DELETE_IDENTITY,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestLockMutation(django.test.TestCase):
    """Unit tests for mutation to lock individuals"""

    SH_LOCK_INDIVIDUAL = """
          mutation lockIndv($uuid: String) {
            lock(uuid: $uuid) {
              uuid
              individual {
                mk
                isLocked
              }
            }
          }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        # Transaction
        self.trxl = TransactionsLog.open('lock', self.ctx)

    def test_lock(self):
        """Check if everything goes OK when locking an individual"""

        api.add_identity(self.ctx, 'scm', email='jsmith@example')

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
        }
        executed = client.execute(self.SH_LOCK_INDIVIDUAL,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results
        uuid = executed['data']['lock']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        individual = executed['data']['lock']['individual']
        self.assertEqual(individual['mk'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(individual['isLocked'], True)

    def test_non_existing_uuid(self):
        """Check if it fails when the uuid does not exists"""

        api.add_identity(self.ctx, 'scm', email='jsmith@example')

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'FFFFFFFFFFFFFFF',
        }
        executed = client.execute(self.SH_LOCK_INDIVIDUAL,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INDIVIDUAL_DOES_NOT_EXIST_ERROR)

    def test_empty_uuid(self):
        """Check if it fails when the uuid is an empty string"""

        api.add_identity(self.ctx, 'scm', email='jsmith@example')

        client = graphene.test.Client(schema)

        params = {
            'uuid': '',
        }
        executed = client.execute(self.SH_LOCK_INDIVIDUAL,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_EMPTY_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        api.add_identity(self.ctx, 'scm', email='jsmith@example')

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'uuid': '1387b129ab751a3657312c09759caa41dfd8d07d',
        }
        executed = client.execute(self.SH_LOCK_INDIVIDUAL,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestUnlockMutation(django.test.TestCase):
    """Unit tests for mutation to unlock individuals"""

    SH_UNLOCK_INDIVIDUAL = """
          mutation unlockIndv($uuid: String) {
            unlock(uuid: $uuid) {
              uuid
              individual {
                mk
                isLocked
              }
            }
          }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        # Transaction
        self.trxl = TransactionsLog.open('lock', self.ctx)

    def test_unlock(self):
        """Check if everything goes OK when unlocking an individual"""

        api.add_identity(self.ctx, 'scm', email='jsmith@example')

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
        }
        executed = client.execute(self.SH_UNLOCK_INDIVIDUAL,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results
        uuid = executed['data']['unlock']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        individual = executed['data']['unlock']['individual']
        self.assertEqual(individual['mk'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(individual['isLocked'], False)

    def test_non_existing_uuid(self):
        """Check if it fails when the uuid does not exists"""

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'FFFFFFFFFFFFFFF',
        }
        executed = client.execute(self.SH_UNLOCK_INDIVIDUAL,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INDIVIDUAL_DOES_NOT_EXIST_ERROR)

    def test_empty_uuid(self):
        """Check if it fails when the uuid is an empty string"""

        api.add_identity(self.ctx, 'scm', email='jsmith@example')

        client = graphene.test.Client(schema)

        params = {
            'uuid': '',
        }
        executed = client.execute(self.SH_UNLOCK_INDIVIDUAL,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_EMPTY_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        api.add_identity(self.ctx, 'scm', email='jsmith@example')

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
        }
        executed = client.execute(self.SH_UNLOCK_INDIVIDUAL,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestUpdateProfileMutation(django.test.TestCase):
    """Unit tests for mutation to update profiles"""

    SH_UPDATE_PROFILE = """
      mutation editProfile($uuid: String, $data: ProfileInputType) {
        updateProfile(uuid: $uuid, data: $data) {
          uuid
          individual {
            mk
            profile {
              name
              email
              gender
              genderAcc
              isBot
              country {
                name
                code
              }
            }
          }
        }
      }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')
        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.update_profile(self.ctx,
                           jsmith.uuid,
                           name='Smith J,',
                           email='jsmith@example.com')

    def test_update_profile(self):
        """Check if it updates a profile"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'data': {
                'name': 'John Smith',
                'email': 'jsmith@example.net',
                'isBot': True,
                'countryCode': 'US',
                'gender': 'male',
                'genderAcc': 89
            }
        }
        executed = client.execute(self.SH_UPDATE_PROFILE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, profile was updated
        profile = executed['data']['updateProfile']['individual']['profile']
        self.assertEqual(profile['name'], 'John Smith')
        self.assertEqual(profile['email'], 'jsmith@example.net')
        self.assertEqual(profile['isBot'], True)
        self.assertEqual(profile['gender'], 'male')
        self.assertEqual(profile['genderAcc'], 89)
        self.assertEqual(profile['country']['code'], 'US')
        self.assertEqual(profile['country']['name'], 'United States of America')

        uuid = executed['data']['updateProfile']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        individual = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        profile = individual.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@example.net')
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 89)
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.name, 'United States of America')

    def test_non_existing_uuid(self):
        """Check if it fails updating profiles of individuals that do not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'FFFFFFFFFFFFFFF',
            'data': {
                'name': 'John Smith',
            }
        }
        executed = client.execute(self.SH_UPDATE_PROFILE,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INDIVIDUAL_DOES_NOT_EXIST_ERROR)

    def test_name_email_empty(self):
        """Check if name and email are set to None when an empty string is given"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'data': {
                'name': '',
                'email': ''
            }
        }
        executed = client.execute(self.SH_UPDATE_PROFILE,
                                  context_value=self.context_value,
                                  variables=params)

        profile = executed['data']['updateProfile']['individual']['profile']
        self.assertEqual(profile['name'], None)
        self.assertEqual(profile['email'], None)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        client = graphene.test.Client(schema)

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'
        api.lock(self.ctx, uuid)

        # Tests
        params = {
            'uuid': uuid,
            'data': {
                'name': 'John Smith',
                'email': 'jsmith@example.net',
                'isBot': True,
                'countryCode': 'US',
                'gender': 'male',
                'genderAcc': 89
            }
        }
        executed = client.execute(self.SH_UPDATE_PROFILE,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_LOCKED_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'data': {
                'name': 'John Smith',
                'email': 'jsmith@example.net',
                'isBot': True,
                'countryCode': 'US',
                'gender': 'male',
                'genderAcc': 89
            }
        }
        executed = client.execute(self.SH_UPDATE_PROFILE,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestMoveIdentityMutation(django.test.TestCase):
    """Unit tests for mutation to move identities"""

    SH_MOVE = """
      mutation moveId($fromUUID: String, $toUUID: String) {
        moveIdentity(fromUuid: $fromUUID, toUuid: $toUUID) {
          uuid
          individual {
            mk
            identities {
              uuid
              name
              email
              username
              source
            }
          }
        }
      }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example.com')
        api.add_identity(self.ctx,
                         'scm',
                         name='John Smith',
                         email='jsmith@example.com',
                         uuid=jsmith.uuid)
        jsmith2 = api.add_identity(self.ctx, 'scm', email='jdoe@example.com')
        api.add_identity(self.ctx,
                         'phab',
                         name='J. Smith',
                         email='jsmith@example.org',
                         uuid=jsmith2.uuid)

    def test_move_identity(self):
        """Test whether an identity is moved to an individual"""

        client = graphene.test.Client(schema)

        params = {
            'fromUUID': '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331',
            'toUUID': '03877f31261a6d1a1b3971d240e628259364b8ac'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, identity was moved
        identities = executed['data']['moveIdentity']['individual']['identities']

        self.assertEqual(len(identities), 3)

        identity = identities[0]
        self.assertEqual(identity['uuid'], '03877f31261a6d1a1b3971d240e628259364b8ac')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jdoe@example.com')

        identity = identities[1]
        self.assertEqual(identity['uuid'], '0880dc4e621877e8520cef1747d139dd4f9f110e')
        self.assertEqual(identity['name'], 'J. Smith')
        self.assertEqual(identity['email'], 'jsmith@example.org')

        identity = identities[2]
        self.assertEqual(identity['uuid'], '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity['name'], 'John Smith')
        self.assertEqual(identity['email'], 'jsmith@example.com')

        uuid = executed['data']['moveIdentity']['uuid']
        self.assertEqual(uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')

        # Check database objects
        individual_db = Individual.objects.get(mk='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '334da68fcd3da4e799791f73dfada2afb22648c6')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jsmith@example.com')

        individual_db = Individual.objects.get(mk='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 3)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jdoe@example.com')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.uuid, '0880dc4e621877e8520cef1747d139dd4f9f110e')
        self.assertEqual(identity_db.name, 'J. Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.org')

        identity_db = identities_db[2]
        self.assertEqual(identity_db.uuid, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity_db.name, 'John Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.com')

    def test_equal_related_individual(self):
        """Check if identities are not moved when 'to_uuid' is the individual related to 'from_uuid'"""

        client = graphene.test.Client(schema)

        params = {
            'fromUUID': '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331',
            'toUUID': '334da68fcd3da4e799791f73dfada2afb22648c6'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, identity was not moved
        identities = executed['data']['moveIdentity']['individual']['identities']

        self.assertEqual(len(identities), 2)

        identity = identities[0]
        self.assertEqual(identity['uuid'], '334da68fcd3da4e799791f73dfada2afb22648c6')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith@example.com')

        identity = identities[1]
        self.assertEqual(identity['uuid'], '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity['name'], 'John Smith')
        self.assertEqual(identity['email'], 'jsmith@example.com')

        uuid = executed['data']['moveIdentity']['uuid']
        self.assertEqual(uuid, '334da68fcd3da4e799791f73dfada2afb22648c6')

        # Check database objects
        individual_db = Individual.objects.get(mk='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 2)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '334da68fcd3da4e799791f73dfada2afb22648c6')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.uuid, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')

        individual_db = Individual.objects.get(mk='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 2)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.uuid, '0880dc4e621877e8520cef1747d139dd4f9f110e')

    def test_create_new_individual(self):
        """Check if a new individual is created when 'from_uuid' has the same value of 'to_uuid'"""

        client = graphene.test.Client(schema)

        params = {
            'fromUUID': '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331',
            'toUUID': '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        # This will create a new individual,
        # moving the identity to this new individual
        identities = executed['data']['moveIdentity']['individual']['identities']

        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity['uuid'], '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity['name'], 'John Smith')
        self.assertEqual(identity['email'], 'jsmith@example.com')

        uuid = executed['data']['moveIdentity']['uuid']
        self.assertEqual(uuid, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')

        # Check database objects
        individual_db = Individual.objects.get(mk='334da68fcd3da4e799791f73dfada2afb22648c6')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '334da68fcd3da4e799791f73dfada2afb22648c6')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jsmith@example.com')

        individual_db = Individual.objects.get(mk='880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 1)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331')
        self.assertEqual(identity_db.name, 'John Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.com')

        individual_db = Individual.objects.get(mk='03877f31261a6d1a1b3971d240e628259364b8ac')
        identities_db = individual_db.identities.all()
        self.assertEqual(len(identities_db), 2)

        identity_db = identities_db[0]
        self.assertEqual(identity_db.uuid, '03877f31261a6d1a1b3971d240e628259364b8ac')
        self.assertEqual(identity_db.name, None)
        self.assertEqual(identity_db.email, 'jdoe@example.com')

        identity_db = identities_db[1]
        self.assertEqual(identity_db.uuid, '0880dc4e621877e8520cef1747d139dd4f9f110e')
        self.assertEqual(identity_db.name, 'J. Smith')
        self.assertEqual(identity_db.email, 'jsmith@example.org')

    def test_from_uuid_is_individual(self):
        """Test whether it fails when 'from_uuid' is an individual"""

        client = graphene.test.Client(schema)

        params = {
            'fromUUID': '03877f31261a6d1a1b3971d240e628259364b8ac',
            'toUUID': '334da68fcd3da4e799791f73dfada2afb22648c6'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, FROM_UUID_IS_MK_ERROR)

    def test_not_found_from_identity(self):
        """Test whether it fails when 'from_uuid' identity is not found"""

        client = graphene.test.Client(schema)

        params = {
            'fromUUID': 'FFFFFFFFFFFFFFF',
            'toUUID': '03877f31261a6d1a1b3971d240e628259364b8ac'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INDIVIDUAL_DOES_NOT_EXIST_ERROR)

    def test_not_found_to_identity(self):
        """Test whether it fails when 'to_uuid' individual is not found"""

        client = graphene.test.Client(schema)

        params = {
            'fromUUID': '0880dc4e621877e8520cef1747d139dd4f9f110e',
            'toUUID': 'FFFFFFFFFFFFFFF'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INDIVIDUAL_DOES_NOT_EXIST_ERROR)

    def test_empty_from_uuid(self):
        """Check whether identities cannot be moved when giving an empty uuid"""

        client = graphene.test.Client(schema)

        params = {
            'fromUUID': '',
            'toUUID': '03877f31261a6d1a1b3971d240e628259364b8ac'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, FROM_UUID_EMPTY_ERROR)

    def test_empty_to_uuid(self):
        """Check whether identities cannot be moved when giving an empty UUID"""

        client = graphene.test.Client(schema)

        params = {
            'fromUUID': '03877f31261a6d1a1b3971d240e628259364b8ac',
            'toUUID': ''
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, TO_UUID_EMPTY_ERROR)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        client = graphene.test.Client(schema)

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.lock(self.ctx, jsmith.uuid)

        # Tests
        params = {
            'fromUUID': '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331',
            'toUUID': jsmith.uuid
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_LOCKED_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'fromUUID': '880b3dfcb3a08712e5831bddc3dfe81fc5d7b331',
            'toUUID': '03877f31261a6d1a1b3971d240e628259364b8ac'
        }
        executed = client.execute(self.SH_MOVE,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestEnrollMutation(django.test.TestCase):
    """Unit tests for mutation to enroll identities"""

    SH_ENROLL = """
      mutation enrollId($uuid: String, $group: String, $parentOrg: String,
                        $fromDate: DateTime, $toDate: DateTime,
                        $force: Boolean) {
        enroll(uuid: $uuid, group: $group, parentOrg: $parentOrg,
               fromDate: $fromDate, toDate: $toDate,
               force: $force) {
          uuid
          individual {
            mk
            enrollments {
              group {
                name
                type
                parentOrg {
                  name
                }
              }
            start
            end
            }
          }
        }
      }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        # Transaction
        self.trxl = TransactionsLog.open('enroll', self.ctx)

        jsmith = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        org = db.add_organization(self.trxl, 'Example')
        db.add_team(self.trxl, 'Example Team', organization=org)

        api.enroll(self.ctx, jsmith.uuid, 'Example',
                   from_date=datetime.datetime(1999, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))
        api.enroll(self.ctx, jsmith.uuid, 'Example',
                   from_date=datetime.datetime(2004, 1, 1),
                   to_date=datetime.datetime(2006, 1, 1))
        api.enroll(self.ctx, jsmith.uuid, 'Example Team',
                   parent_org='Example',
                   from_date=datetime.datetime(2005, 1, 1),
                   to_date=datetime.datetime(2006, 1, 1))

    def test_enroll(self):
        """Check if it enrolls an individual"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Example',
            'fromDate': '2008-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, profile was updated
        enrollments = executed['data']['enroll']['individual']['enrollments']

        self.assertEqual(len(enrollments), 4)

        enrollment = enrollments[0]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['group']['type'], 'organization')
        self.assertEqual(enrollment['start'], '1999-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2000-01-01T00:00:00+00:00')

        enrollment = enrollments[1]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['group']['type'], 'organization')
        self.assertEqual(enrollment['start'], '2004-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2006-01-01T00:00:00+00:00')

        enrollment = enrollments[2]
        self.assertEqual(enrollment['group']['name'], 'Example Team')
        self.assertEqual(enrollment['group']['type'], 'team')
        self.assertEqual(enrollment['start'], '2005-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2006-01-01T00:00:00+00:00')

        enrollment = enrollments[3]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['group']['type'], 'organization')
        self.assertEqual(enrollment['start'], '2008-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2009-01-01T00:00:00+00:00')

        uuid = executed['data']['enroll']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        individual = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments_db = individual.enrollments.all()
        self.assertEqual(len(enrollments_db), 4)

    def test_enroll_in_team(self):
        """Check if it enrolls an individual in a team"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Example Team',
            'parentOrg': 'Example',
            'fromDate': '2008-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, profile was updated
        enrollments = executed['data']['enroll']['individual']['enrollments']

        self.assertEqual(len(enrollments), 4)

        enrollment = enrollments[0]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['group']['type'], 'organization')
        self.assertEqual(enrollment['start'], '1999-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2000-01-01T00:00:00+00:00')

        enrollment = enrollments[1]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['group']['type'], 'organization')
        self.assertEqual(enrollment['start'], '2004-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2006-01-01T00:00:00+00:00')

        enrollment = enrollments[2]
        self.assertEqual(enrollment['group']['name'], 'Example Team')
        self.assertEqual(enrollment['group']['type'], 'team')
        self.assertEqual(enrollment['group']['parentOrg']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2005-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2006-01-01T00:00:00+00:00')

        enrollment = enrollments[3]
        self.assertEqual(enrollment['group']['name'], 'Example Team')
        self.assertEqual(enrollment['group']['type'], 'team')
        self.assertEqual(enrollment['group']['parentOrg']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2008-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2009-01-01T00:00:00+00:00')

        uuid = executed['data']['enroll']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        individual = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments_db = individual.enrollments.all()
        self.assertEqual(len(enrollments_db), 4)

    def test_enroll_ignore_default(self):
        """Check if it enrolls an individual ignoring default dates"""

        client = graphene.test.Client(schema)

        db.add_organization(self.trxl, 'Bitergia')

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Bitergia',
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        # Checking results with default dates
        enrollments = executed['data']['enroll']['individual']['enrollments']

        self.assertEqual(len(enrollments), 4)

        enrollment = enrollments[0]
        self.assertEqual(enrollment['group']['name'], 'Bitergia')
        self.assertEqual(enrollment['start'], '1900-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2100-01-01T00:00:00+00:00')

        enrollment = enrollments[1]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '1999-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2000-01-01T00:00:00+00:00')

        enrollment = enrollments[2]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2004-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2006-01-01T00:00:00+00:00')

        enrollment = enrollments[3]
        self.assertEqual(enrollment['group']['name'], 'Example Team')
        self.assertEqual(enrollment['group']['type'], 'team')
        self.assertEqual(enrollment['group']['parentOrg']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2005-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2006-01-01T00:00:00+00:00')

        uuid = executed['data']['enroll']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        individual = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments_db = individual.enrollments.all()
        self.assertEqual(len(enrollments_db), 4)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Bitergia',
            'fromDate': '2008-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000',
            'force': True
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        # Checking results with updated dates
        enrollments = executed['data']['enroll']['individual']['enrollments']

        self.assertEqual(len(enrollments), 4)

        enrollment = enrollments[0]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '1999-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2000-01-01T00:00:00+00:00')

        enrollment = enrollments[1]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2004-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2006-01-01T00:00:00+00:00')

        enrollment = enrollments[2]
        self.assertEqual(enrollment['group']['name'], 'Example Team')
        self.assertEqual(enrollment['group']['type'], 'team')
        self.assertEqual(enrollment['group']['parentOrg']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2005-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2006-01-01T00:00:00+00:00')

        enrollment = enrollments[3]
        self.assertEqual(enrollment['group']['name'], 'Bitergia')
        self.assertEqual(enrollment['start'], '2008-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2009-01-01T00:00:00+00:00')

        uuid = executed['data']['enroll']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        individual = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments_db = individual.enrollments.all()
        self.assertEqual(len(enrollments_db), 4)

    def test_merge_enrollments(self):
        """Check if enrollments are merged for overlapped new entries"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Example',
            'fromDate': '1998-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, profile was updated
        enrollments = executed['data']['enroll']['individual']['enrollments']

        self.assertEqual(len(enrollments), 2)

        enrollment = enrollments[0]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '1998-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2009-01-01T00:00:00+00:00')

        uuid = executed['data']['enroll']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        individual = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments_db = individual.enrollments.all()
        self.assertEqual(len(enrollments_db), 2)

    def test_non_existing_uuid(self):
        """Check if it fails when the individual does not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'FFFFFFFFFFFFFFF',
            'group': 'Example',
            'fromDate': '1998-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INDIVIDUAL_DOES_NOT_EXIST_ERROR)

    def test_non_existing_organization(self):
        """Check if it fails when the organization does not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Bitergia',
            'fromDate': '1998-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_BITERGIA_DOES_NOT_EXIST_ERROR)

    def test_error_ignore_default_false(self):
        """Check whether enrollments in an existing default
           period cannot be inserted when `ignore_default`
           flag is not set
        """
        client = graphene.test.Client(schema)

        db.add_organization(self.trxl, 'Bitergia')

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Bitergia'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        # Checking results with default dates
        enrollments = executed['data']['enroll']['individual']['enrollments']

        self.assertEqual(len(enrollments), 4)

        enrollment = enrollments[0]
        self.assertEqual(enrollment['group']['name'], 'Bitergia')
        self.assertEqual(enrollment['start'], '1900-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2100-01-01T00:00:00+00:00')

        enrollment = enrollments[1]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '1999-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2000-01-01T00:00:00+00:00')

        enrollment = enrollments[2]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2004-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2006-01-01T00:00:00+00:00')

        enrollment = enrollments[3]
        self.assertEqual(enrollment['group']['name'], 'Example Team')
        self.assertEqual(enrollment['group']['type'], 'team')
        self.assertEqual(enrollment['group']['parentOrg']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2005-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2006-01-01T00:00:00+00:00')

        # Tests
        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Bitergia',
            'fromDate': '2005-01-01T00:00:00+0000',
            'toDate': '2005-06-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        start = '2005-01-01 00:00:00+00:00'
        end = '2005-06-01 00:00:00+00:00'
        org_name = 'Bitergia'
        err = DUPLICATED_ENROLLMENT_ERROR.format(start, end, org_name)
        self.assertEqual(msg, err)

    def test_integrity_error(self):
        """Check whether enrollments in an existing period cannot be inserted"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Example',
            'fromDate': '2005-01-01T00:00:00+0000',
            'toDate': '2005-06-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        start = '2005-01-01 00:00:00+00:00'
        end = '2005-06-01 00:00:00+00:00'
        org_name = 'Example'
        err = DUPLICATED_ENROLLMENT_ERROR.format(start, end, org_name)
        self.assertEqual(msg, err)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        client = graphene.test.Client(schema)

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'
        api.lock(self.ctx, uuid)

        # Tests
        params = {
            'uuid': uuid,
            'group': 'Example',
            'fromDate': '2008-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_LOCKED_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Example',
            'fromDate': '2008-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_ENROLL,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestWithdrawMutation(django.test.TestCase):
    """Unit tests for mutation to withdraw identities"""

    SH_WITHDRAW = """
      mutation withdrawId($uuid: String, $group: String, $parentOrg: String,
                          $fromDate: DateTime, $toDate: DateTime) {
        withdraw(uuid: $uuid, group: $group, parentOrg: $parentOrg,
                 fromDate: $fromDate, toDate: $toDate) {
          uuid
          individual {
            mk
            enrollments {
              group {
                name
                type
              }
            start
            end
            }
          }
        }
      }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        # Transaction
        self.trxl = TransactionsLog.open('withdraw', self.ctx)

        org = db.add_organization(self.trxl, 'Example')
        db.add_team(self.trxl, 'Example Team', organization=org)
        db.add_organization(self.trxl, 'LibreSoft')

        api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2006, 1, 1),
                   to_date=datetime.datetime(2008, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2009, 1, 1),
                   to_date=datetime.datetime(2011, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'LibreSoft',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example Team',
                   parent_org='Example',
                   from_date=datetime.datetime(2015, 1, 1),
                   to_date=datetime.datetime(2016, 1, 1))

        api.add_identity(self.ctx, 'scm', email='jrae@example')
        api.enroll(self.ctx,
                   '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

    def test_withdraw(self):
        """Check if it withdraws an individual from an organization"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Example',
            'fromDate': '2007-01-01T00:00:00+0000',
            'toDate': '2013-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, enrollments were updated
        enrollments = executed['data']['withdraw']['individual']['enrollments']

        self.assertEqual(len(enrollments), 4)

        enrollment = enrollments[0]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2006-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2007-01-01T00:00:00+00:00')

        enrollment = enrollments[1]
        self.assertEqual(enrollment['group']['name'], 'LibreSoft')
        self.assertEqual(enrollment['start'], '2012-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2014-01-01T00:00:00+00:00')

        enrollment = enrollments[2]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2013-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2014-01-01T00:00:00+00:00')

        enrollment = enrollments[3]
        self.assertEqual(enrollment['group']['name'], 'Example Team')
        self.assertEqual(enrollment['start'], '2015-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2016-01-01T00:00:00+00:00')

        uuid = executed['data']['withdraw']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        individual = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments_db = individual.enrollments.all()
        self.assertEqual(len(enrollments_db), 4)

        # Other enrollments were not deleted
        individual_db = Individual.objects.get(mk='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

    def test_withdraw_from_team(self):
        """Check if it withdraws an individual from a team"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Example Team',
            'parentOrg': 'Example',
            'fromDate': '2015-01-01T00:00:00+0000',
            'toDate': '2016-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, enrollments were updated
        enrollments = executed['data']['withdraw']['individual']['enrollments']

        self.assertEqual(len(enrollments), 4)

        enrollment = enrollments[0]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2006-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2008-01-01T00:00:00+00:00')

        enrollment = enrollments[1]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2009-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2011-01-01T00:00:00+00:00')

        enrollment = enrollments[2]
        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2012-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2014-01-01T00:00:00+00:00')

        enrollment = enrollments[3]
        self.assertEqual(enrollment['group']['name'], 'LibreSoft')
        self.assertEqual(enrollment['start'], '2012-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2014-01-01T00:00:00+00:00')

        uuid = executed['data']['withdraw']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        individual = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments_db = individual.enrollments.all()
        self.assertEqual(len(enrollments_db), 4)

        # Other enrollments were not deleted
        individual_db = Individual.objects.get(mk='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

    def test_withdraw_default_ranges(self):
        """Check if it withdraws an individual using default ranges when they are not given"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Example'
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, enrollments were updated
        enrollments = executed['data']['withdraw']['individual']['enrollments']

        self.assertEqual(len(enrollments), 2)

        enrollment = enrollments[0]
        self.assertEqual(enrollment['group']['name'], 'LibreSoft')
        self.assertEqual(enrollment['start'], '2012-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2014-01-01T00:00:00+00:00')

        enrollment = enrollments[1]
        self.assertEqual(enrollment['group']['name'], 'Example Team')
        self.assertEqual(enrollment['start'], '2015-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2016-01-01T00:00:00+00:00')

        uuid = executed['data']['withdraw']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        individual = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        enrollments_db = individual.enrollments.all()
        self.assertEqual(len(enrollments_db), 2)

    def test_non_existing_uuid(self):
        """Check if it fails when the individual does not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'FFFFFFFFFFFFFFF',
            'group': 'Example',
            'fromDate': '1998-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INDIVIDUAL_DOES_NOT_EXIST_ERROR)

    def test_non_existing_organization(self):
        """Check if it fails when the organization does not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Bitergia',
            'fromDate': '1998-01-01T00:00:00+0000',
            'toDate': '2009-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_BITERGIA_DOES_NOT_EXIST_ERROR)

    def test_non_existing_enrollments(self):
        """Check if it fails when the enrollments for a period do not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Example',
            'fromDate': '2050-01-01T00:00:00+0000',
            'toDate': '2060-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ENROLLMENT_DOES_NOT_EXIST_ERROR)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        client = graphene.test.Client(schema)

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'
        api.lock(self.ctx, uuid)

        # Tests
        params = {
            'uuid': uuid,
            'group': 'Example',
            'fromDate': '2007-01-01T00:00:00+0000',
            'toDate': '2013-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_LOCKED_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Example',
            'fromDate': '2007-01-01T00:00:00+0000',
            'toDate': '2013-01-01T00:00:00+0000',
        }
        executed = client.execute(self.SH_WITHDRAW,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestUpdateEnrollmentMutation(django.test.TestCase):
    """Unit tests for mutation to update enrollments from identities"""

    SH_UPDATE_ENROLLMENT = """
      mutation updateEnrollmentId($uuid: String, $group: String,
                                  $parentOrg: String,
                                  $fromDate: DateTime, $toDate: DateTime,
                                  $newFromDate: DateTime, $newToDate: DateTime,
                                  $force: Boolean) {
        updateEnrollment(uuid: $uuid, group: $group, parentOrg: $parentOrg,
                 fromDate: $fromDate, toDate: $toDate,
                 newFromDate: $newFromDate, newToDate: $newToDate,
                 force: $force) {
          uuid
          individual {
            mk
            enrollments {
              group {
                name
              }
            start
            end
            }
          }
        }
      }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        api.add_organization(self.ctx, 'Example')
        api.add_team(self.ctx, 'Example Team', organization='Example')
        api.add_organization(self.ctx, 'Bitergia')

        api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2006, 1, 1),
                   to_date=datetime.datetime(2008, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2009, 1, 1),
                   to_date=datetime.datetime(2011, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Bitergia',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example Team',
                   parent_org='Example',
                   from_date=datetime.datetime(2013, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

        api.add_identity(self.ctx, 'scm', email='jrae@example')
        api.enroll(self.ctx,
                   '3283e58cef2b80007aa1dfc16f6dd20ace1aee96', 'Example',
                   from_date=datetime.datetime(2012, 1, 1),
                   to_date=datetime.datetime(2014, 1, 1))

    def test_update_enrollment(self):
        """Check whether it updates an individual's enrollment from an organization during the given period"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': '3283e58cef2b80007aa1dfc16f6dd20ace1aee96',
            'group': 'Example',
            'fromDate': '2012-01-01T00:00:00+0000',
            'toDate': '2014-01-01T00:00:00+0000',
            'newFromDate': '2012-01-02T00:00:00+0000',
            'newToDate': '2013-12-31T00:00:00+0000'
        }
        executed = client.execute(self.SH_UPDATE_ENROLLMENT,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, enrollments were updated
        enrollments = executed['data']['updateEnrollment']['individual']['enrollments']

        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]

        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2012-01-02T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2013-12-31T00:00:00+00:00')

        uuid = executed['data']['updateEnrollment']['uuid']
        self.assertEqual(uuid, '3283e58cef2b80007aa1dfc16f6dd20ace1aee96')

        # Check database
        individual = Individual.objects.get(mk='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')

        enrollments_db = individual.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        # Other enrollments were not updated
        individual_db = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 5)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2006, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2008, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[1]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2009, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2011, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[2]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[3]
        self.assertEqual(enrollment_db.group.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[4]
        self.assertEqual(enrollment_db.group.name, 'Example Team')
        self.assertEqual(enrollment_db.start, datetime.datetime(2013, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_update_team_enrollment(self):
        """Check whether it updates an individual's enrollment from a team during the given period"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
            'group': 'Example Team',
            'parentOrg': 'Example',
            'fromDate': '2013-01-01T00:00:00+0000',
            'toDate': '2014-01-01T00:00:00+0000',
            'newFromDate': '2012-01-02T00:00:00+0000',
            'newToDate': '2015-12-31T00:00:00+0000'
        }
        executed = client.execute(self.SH_UPDATE_ENROLLMENT,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, enrollments were updated
        enrollments = executed['data']['updateEnrollment']['individual']['enrollments']

        self.assertEqual(len(enrollments), 5)

        enrollment = enrollments[4]

        self.assertEqual(enrollment['group']['name'], 'Example Team')
        self.assertEqual(enrollment['start'], '2012-01-02T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2015-12-31T00:00:00+00:00')

        uuid = executed['data']['updateEnrollment']['uuid']
        self.assertEqual(uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        # Check database
        individual = Individual.objects.get(mk='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')

        enrollments_db = individual.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        # Other enrollments were not updated
        individual_db = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 5)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2006, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2008, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[1]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2009, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2011, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[2]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[3]
        self.assertEqual(enrollment_db.group.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_update_using_any_identity_uuid(self):
        """
        Check whether it updates an enrollment from an individual
        during the given period using any valid identity uuid
        """

        api.add_identity(self.ctx, 'mls', email='jsmith@example',
                         uuid='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'de176236636bc488d31e9f91952ecfc6d976a69e',
            'group': 'Example',
            'fromDate': '2012-01-01T00:00:00+0000',
            'toDate': '2014-01-01T00:00:00+0000',
            'newFromDate': '2012-01-02T00:00:00+0000',
            'newToDate': '2013-12-31T00:00:00+0000'
        }
        executed = client.execute(self.SH_UPDATE_ENROLLMENT,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, enrollment was updated
        enrollments = executed['data']['updateEnrollment']['individual']['enrollments']

        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]

        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2012-01-02T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2013-12-31T00:00:00+00:00')

        uuid = executed['data']['updateEnrollment']['uuid']
        self.assertEqual(uuid, '3283e58cef2b80007aa1dfc16f6dd20ace1aee96')

        # Check database
        individual = Individual.objects.get(mk='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')

        enrollments_db = individual.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 2, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2013, 12, 31, tzinfo=UTC))

        # Other enrollments were not updated
        individual_db = Individual.objects.get(mk='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 5)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2006, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2008, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[1]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2009, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2011, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[2]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[3]
        self.assertEqual(enrollment_db.group.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[4]
        self.assertEqual(enrollment_db.group.name, 'Example Team')
        self.assertEqual(enrollment_db.start, datetime.datetime(2013, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_update_no_new_to_date(self):
        """Check if the enrollment is updated as expected when new to_date is not provided"""

        client = graphene.test.Client(schema)

        # Test only with 'newFromDate' date
        params = {
            'uuid': '3283e58cef2b80007aa1dfc16f6dd20ace1aee96',
            'group': 'Example',
            'fromDate': '2012-01-01T00:00:00+0000',
            'toDate': '2014-01-01T00:00:00+0000',
            'newFromDate': '2012-01-02T00:00:00+0000'
        }
        executed = client.execute(self.SH_UPDATE_ENROLLMENT,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, enrollment was not updated
        enrollments = executed['data']['updateEnrollment']['individual']['enrollments']

        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]

        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2012-01-02T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2014-01-01T00:00:00+00:00')

        uuid = executed['data']['updateEnrollment']['uuid']
        self.assertEqual(uuid, '3283e58cef2b80007aa1dfc16f6dd20ace1aee96')

        # Check database
        individual = Individual.objects.get(mk='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')

        enrollments_db = individual.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 2, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2014, 1, 1, tzinfo=UTC))

    def test_update_no_new_from_date(self):
        """Check if the enrollment is updated as expected when new from_date is not provided"""

        client = graphene.test.Client(schema)

        # Test only with 'newToDate' date
        params = {
            'uuid': '3283e58cef2b80007aa1dfc16f6dd20ace1aee96',
            'group': 'Example',
            'fromDate': '2012-01-01T00:00:00+0000',
            'toDate': '2014-01-01T00:00:00+0000',
            'newToDate': '2013-12-31T00:00:00+0000'
        }
        executed = client.execute(self.SH_UPDATE_ENROLLMENT,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, enrollment was not updated
        enrollments = executed['data']['updateEnrollment']['individual']['enrollments']

        self.assertEqual(len(enrollments), 1)

        enrollment = enrollments[0]

        self.assertEqual(enrollment['group']['name'], 'Example')
        self.assertEqual(enrollment['start'], '2012-01-01T00:00:00+00:00')
        self.assertEqual(enrollment['end'], '2013-12-31T00:00:00+00:00')

        uuid = executed['data']['updateEnrollment']['uuid']
        self.assertEqual(uuid, '3283e58cef2b80007aa1dfc16f6dd20ace1aee96')

        # Check database
        individual = Individual.objects.get(mk='3283e58cef2b80007aa1dfc16f6dd20ace1aee96')

        enrollments_db = individual.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(2012, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2013, 12, 31, tzinfo=UTC))

    def test_update_both_new_dates_none(self):
        """Check if it fails when no new dates are provided (None)"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': '3283e58cef2b80007aa1dfc16f6dd20ace1aee96',
            'group': 'Example',
            'fromDate': '2012-01-01T00:00:00+0000',
            'toDate': '2014-01-01T00:00:00+0000'
        }
        executed = client.execute(self.SH_UPDATE_ENROLLMENT,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, BOTH_NEW_DATES_NONE_ERROR)

    def test_non_existing_uuid(self):
        """Check if it fails when the individual does not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': 'FFFFFFFFFFFFFFF',
            'group': 'Example',
            'fromDate': '2012-01-01T00:00:00+0000',
            'toDate': '2014-01-01T00:00:00+0000',
            'newFromDate': '2012-01-02T00:00:00+0000',
            'newToDate': '2013-12-31T00:00:00+0000'
        }
        executed = client.execute(self.SH_UPDATE_ENROLLMENT,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, INDIVIDUAL_DOES_NOT_EXIST_ERROR)

    def test_non_existing_organization(self):
        """Check if it fails when the organization does not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': '3283e58cef2b80007aa1dfc16f6dd20ace1aee96',
            'group': 'LibreSoft',
            'fromDate': '2012-01-01T00:00:00+0000',
            'toDate': '2014-01-01T00:00:00+0000',
            'newFromDate': '2012-01-02T00:00:00+0000',
            'newToDate': '2013-12-31T00:00:00+0000'
        }
        executed = client.execute(self.SH_UPDATE_ENROLLMENT,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_LIBRESOFT_DOES_NOT_EXIST_ERROR)

    def test_non_existing_enrollments(self):
        """Check if it fails when the enrollments for a period do not exist"""

        client = graphene.test.Client(schema)

        params = {
            'uuid': '3283e58cef2b80007aa1dfc16f6dd20ace1aee96',
            'group': 'Example',
            'fromDate': '2050-01-01T00:00:00+0000',
            'toDate': '2060-01-01T00:00:00+0000',
            'newFromDate': '2012-01-02T00:00:00+0000',
            'newToDate': '2013-12-31T00:00:00+0000'
        }
        executed = client.execute(self.SH_UPDATE_ENROLLMENT,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ENROLLMENT_DOES_NOT_EXIST_ERROR)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        client = graphene.test.Client(schema)

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'
        api.lock(self.ctx, uuid)

        # Tests
        params = {
            'uuid': uuid,
            'group': 'Example',
            'fromDate': '2006-01-01T00:00:00+0000',
            'toDate': '2008-01-01T00:00:00+0000',
            'newFromDate': '2012-01-02T00:00:00+0000',
            'newToDate': '2013-12-31T00:00:00+0000'
        }
        executed = client.execute(self.SH_UPDATE_ENROLLMENT,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_LOCKED_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'uuid': '3283e58cef2b80007aa1dfc16f6dd20ace1aee96',
            'group': 'Example',
            'fromDate': '2012-01-01T00:00:00+0000',
            'toDate': '2014-01-01T00:00:00+0000',
            'newFromDate': '2012-01-02T00:00:00+0000',
            'newToDate': '2013-12-31T00:00:00+0000'
        }
        executed = client.execute(self.SH_UPDATE_ENROLLMENT,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestMergeMutation(django.test.TestCase):
    """Unit tests for mutation to merge individuals"""

    SH_MERGE = """
          mutation mergeIds($fromUuids: [String], $toUuid: String) {
            merge(fromUuids: $fromUuids, toUuid: $toUuid) {
              uuid
              individual {
                mk
                identities {
                  uuid
                  name
                  email
                  username
                  source
                }
              }
            }
          }
        """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        # Transaction
        self.trxl = TransactionsLog.open('merge', self.ctx)

        db.add_organization(self.trxl, 'Example')
        db.add_organization(self.trxl, 'Bitergia')

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')

        api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_identity(self.ctx,
                         'git',
                         email='jsmith-git@example',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        api.update_profile(self.ctx,
                           uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', name='J. Smith',
                           email='jsmith@example', gender='male', gender_acc=75)
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2017, 6, 1))

        api.add_identity(self.ctx, 'scm', email='jsmith@bitergia')
        api.add_identity(self.ctx,
                         'phabricator',
                         email='jsmith-phab@bitergia',
                         uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        api.update_profile(self.ctx,
                           uuid='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed', name='John Smith',
                           email='jsmith@profile-email', is_bot=True, country_code='US')
        api.enroll(self.ctx,
                   'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed', 'Bitergia',
                   from_date=datetime.datetime(2017, 6, 2),
                   to_date=datetime.datetime(2100, 1, 1))

        api.add_identity(self.ctx, 'scm', email='jsmith@libresoft')
        api.add_identity(self.ctx,
                         'phabricator',
                         email='jsmith2@libresoft',
                         uuid='1c13fec7a328201fc6a230fe43eb81df0e20626e')
        api.add_identity(self.ctx,
                         'phabricator',
                         email='jsmith3@libresoft',
                         uuid='1c13fec7a328201fc6a230fe43eb81df0e20626e')
        api.update_profile(self.ctx,
                           uuid='1c13fec7a328201fc6a230fe43eb81df0e20626e', name='John Smith',
                           email='jsmith@profile-email', is_bot=False, country_code='US')

    def test_merge_individuals(self):
        """Check whether it merges two individuals, merging their ids, enrollments and profiles"""

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': ['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
            'toUuid': 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed'
        }

        executed = client.execute(self.SH_MERGE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, identities were merged
        identities = executed['data']['merge']['individual']['identities']

        self.assertEqual(len(identities), 4)

        identity = identities[0]
        self.assertEqual(identity['uuid'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith-git@example')
        self.assertEqual(identity['source'], 'git')

        identity = identities[1]
        self.assertEqual(identity['uuid'], '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith-phab@bitergia')
        self.assertEqual(identity['source'], 'phabricator')

        identity = identities[2]
        self.assertEqual(identity['uuid'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith@bitergia')
        self.assertEqual(identity['source'], 'scm')

        identity = identities[3]
        self.assertEqual(identity['uuid'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith@example')
        self.assertEqual(identity['source'], 'scm')

        uuid = executed['data']['merge']['uuid']
        self.assertEqual(uuid, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        # Check database objects
        individual_db = Individual.objects.get(mk='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        self.assertIsInstance(individual_db, Individual)
        self.assertEqual(individual_db.mk, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = individual_db.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 75)
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.country_id, 'US')

        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.alpha3, 'USA')

        identities = individual_db.identities.all()
        self.assertEqual(len(identities), 4)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id1.email, 'jsmith-git@example')
        self.assertEqual(id1.source, 'git')

        id2 = identities[1]
        self.assertEqual(id2.uuid, '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(id2.email, 'jsmith-phab@bitergia')
        self.assertEqual(id2.source, 'phabricator')

        id3 = identities[2]
        self.assertEqual(id3.uuid, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(id3.email, 'jsmith@bitergia')
        self.assertEqual(id3.source, 'scm')

        id4 = identities[3]
        self.assertEqual(id4.uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(id4.email, 'jsmith@example')
        self.assertEqual(id4.source, 'scm')

        enrollments = individual_db.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1.group.name, 'Example')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.group.name, 'Bitergia')
        self.assertEqual(rol2.start, datetime.datetime(2017, 6, 2, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_merge_multiple_individuals(self):
        """Check whether it merges more than two individuals, merging their ids, enrollments and profiles"""

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': ['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3',
                          '1c13fec7a328201fc6a230fe43eb81df0e20626e'],
            'toUuid': 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed'
        }

        executed = client.execute(self.SH_MERGE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, identities were merged
        identities = executed['data']['merge']['individual']['identities']

        self.assertEqual(len(identities), 7)

        identity = identities[0]
        self.assertEqual(identity['uuid'], '1c13fec7a328201fc6a230fe43eb81df0e20626e')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith@libresoft')
        self.assertEqual(identity['source'], 'scm')

        identity = identities[1]
        self.assertEqual(identity['uuid'], '31581d7c6b039318e9048c4d8571666c26a5622b')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith3@libresoft')
        self.assertEqual(identity['source'], 'phabricator')

        identity = identities[2]
        self.assertEqual(identity['uuid'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith-git@example')
        self.assertEqual(identity['source'], 'git')

        identity = identities[3]
        self.assertEqual(identity['uuid'], '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith-phab@bitergia')
        self.assertEqual(identity['source'], 'phabricator')

        identity = identities[4]
        self.assertEqual(identity['uuid'], 'c2f5aa44e920b4fbe3cd36894b18e80a2606deba')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith2@libresoft')
        self.assertEqual(identity['source'], 'phabricator')

        identity = identities[5]
        self.assertEqual(identity['uuid'], 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith@bitergia')
        self.assertEqual(identity['source'], 'scm')

        identity = identities[6]
        self.assertEqual(identity['uuid'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith@example')
        self.assertEqual(identity['source'], 'scm')

        uuid = executed['data']['merge']['uuid']
        self.assertEqual(uuid, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        # Check database objects
        individual_db = Individual.objects.get(mk='caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        self.assertIsInstance(individual_db, Individual)
        self.assertEqual(individual_db.mk, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')

        profile = individual_db.profile
        self.assertEqual(profile.name, 'John Smith')
        self.assertEqual(profile.email, 'jsmith@profile-email')
        self.assertEqual(profile.gender, 'male')
        self.assertEqual(profile.gender_acc, 75)
        self.assertEqual(profile.is_bot, True)
        self.assertEqual(profile.country_id, 'US')

        self.assertEqual(profile.country.name, 'United States of America')
        self.assertEqual(profile.country.code, 'US')
        self.assertEqual(profile.country.alpha3, 'USA')

        identities = individual_db.identities.all()
        self.assertEqual(len(identities), 7)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '1c13fec7a328201fc6a230fe43eb81df0e20626e')
        self.assertEqual(id1.email, 'jsmith@libresoft')
        self.assertEqual(id1.source, 'scm')

        id2 = identities[1]
        self.assertEqual(id2.uuid, '31581d7c6b039318e9048c4d8571666c26a5622b')
        self.assertEqual(id2.email, 'jsmith3@libresoft')
        self.assertEqual(id2.source, 'phabricator')

        id3 = identities[2]
        self.assertEqual(id3.uuid, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id3.email, 'jsmith-git@example')
        self.assertEqual(id3.source, 'git')

        id4 = identities[3]
        self.assertEqual(id4.uuid, '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(id4.email, 'jsmith-phab@bitergia')
        self.assertEqual(id4.source, 'phabricator')

        id5 = identities[4]
        self.assertEqual(id5.uuid, 'c2f5aa44e920b4fbe3cd36894b18e80a2606deba')
        self.assertEqual(id5.email, 'jsmith2@libresoft')
        self.assertEqual(id5.source, 'phabricator')

        id6 = identities[5]
        self.assertEqual(id6.uuid, 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed')
        self.assertEqual(id6.email, 'jsmith@bitergia')
        self.assertEqual(id6.source, 'scm')

        id7 = identities[6]
        self.assertEqual(id7.uuid, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(id7.email, 'jsmith@example')
        self.assertEqual(id7.source, 'scm')

        enrollments = individual_db.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1.group.name, 'Example')
        self.assertEqual(rol1.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(rol1.end, datetime.datetime(2017, 6, 1, tzinfo=UTC))

        rol2 = enrollments[1]
        self.assertEqual(rol2.group.name, 'Bitergia')
        self.assertEqual(rol2.start, datetime.datetime(2017, 6, 2, tzinfo=UTC))
        self.assertEqual(rol2.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

    def test_non_existing_from_uuids(self):
        """Check if it fails merging individuals when source uuids field is `None` or empty"""

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': [],
            'toUuid': 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed'
        }

        executed = client.execute(self.SH_MERGE,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']

        self.assertEqual(msg, FROM_UUIDS_EMPTY_ERROR)

    def test_non_existing_from_uuid(self):
        """Check if it fails merging two individuals when source uuid is `None` or empty"""

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': [''],
            'toUuid': 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed'
        }

        executed = client.execute(self.SH_MERGE,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']

        self.assertEqual(msg, FROM_UUID_EMPTY_ERROR)

    def test_non_existing_to_uuid(self):
        """Check if it fails merging two individuals when destination uuid is `None` or empty"""

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': ['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
            'toUuid': ''
        }

        executed = client.execute(self.SH_MERGE,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']

        self.assertEqual(msg, TO_UUID_EMPTY_ERROR)

    def test_from_uuid_to_uuid_equal(self):
        """Check if it fails merging two individuals when they are equal"""

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': ['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
            'toUuid': 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'
        }

        executed = client.execute(self.SH_MERGE,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']

        self.assertEqual(msg, FROM_UUID_TO_UUID_EQUAL_ERROR)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        client = graphene.test.Client(schema)

        from_uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'
        api.lock(self.ctx, from_uuid)

        # Tests
        params = {
            'fromUuids': [from_uuid],
            'toUuid': 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed'
        }
        executed = client.execute(self.SH_MERGE,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_LOCKED_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'fromUuids': ['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'],
            'toUuid': 'caa5ebfe833371e23f0a3566f2b7ef4a984c4fed'
        }
        executed = client.execute(self.SH_MERGE,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestUnmergeIdentitiesMutation(django.test.TestCase):
    """Unit tests for mutation to unmerge individuals"""

    SH_UNMERGE = """
          mutation unmergeIds($uuids: [String]) {
            unmergeIdentities(uuids: $uuids) {
              uuids
              individuals {
                mk
                identities {
                  uuid
                  name
                  email
                  username
                  source
                }
              }
            }
          }
        """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        # Transaction
        self.trxl = TransactionsLog.open('unmerge_identities', self.ctx)

        db.add_organization(self.trxl, 'Example')
        db.add_organization(self.trxl, 'Bitergia')

        Country.objects.create(code='US',
                               name='United States of America',
                               alpha3='USA')

        api.add_identity(self.ctx, 'scm', email='jsmith@example')
        api.add_identity(self.ctx,
                         'git',
                         email='jsmith-git@example',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        api.update_profile(self.ctx,
                           uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', name='John Smith',
                           email='jsmith@profile-email', is_bot=False, country_code='US')
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2017, 6, 1))

        api.add_identity(self.ctx, 'scm', email='jsmith@bitergia')
        api.add_identity(self.ctx,
                         'phabricator',
                         email='jsmith-phab@bitergia',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        api.enroll(self.ctx,
                   'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3', 'Bitergia',
                   from_date=datetime.datetime(2017, 6, 2),
                   to_date=datetime.datetime(2100, 1, 1))

        api.add_identity(self.ctx,
                         'scm',
                         email='jsmith@libresoft',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        api.add_identity(self.ctx,
                         'phabricator',
                         email='jsmith2@libresoft',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        api.add_identity(self.ctx,
                         'phabricator',
                         email='jsmith3@libresoft',
                         uuid='e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

    def test_unmerge_identities(self):
        """Check whether it unmerges one identity from its parent individual"""

        client = graphene.test.Client(schema)

        params = {
            'uuids': ['67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6']
        }

        executed = client.execute(self.SH_UNMERGE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, identities were unmerged
        uuids = executed['data']['unmergeIdentities']['uuids']
        self.assertEqual(len(uuids), 1)

        uuid1 = uuids[0]
        self.assertEqual(uuid1, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')

        individuals = executed['data']['unmergeIdentities']['individuals']
        self.assertEqual(len(individuals), 1)

        individual = individuals[0]
        self.assertEqual(individual['mk'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')

        identities = individual['identities']
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity['uuid'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith-git@example')
        self.assertEqual(identity['source'], 'git')

        # Check database objects
        individual_db = Individual.objects.get(mk='67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')

        self.assertIsInstance(individual_db, Individual)
        self.assertEqual(individual_db.mk, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')

        profile = individual_db.profile
        self.assertIsNone(profile.name)
        self.assertEqual(profile.email, 'jsmith-git@example')
        self.assertEqual(profile.is_bot, False)

        identities = individual_db.identities.all()
        self.assertEqual(len(identities), 1)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id1.email, 'jsmith-git@example')
        self.assertEqual(id1.source, 'git')

        enrollments = individual_db.enrollments.all()
        self.assertEqual(len(enrollments), 0)

    def test_unmerge_multiple_identities(self):
        """Check whether it unmerges more than two identities"""

        client = graphene.test.Client(schema)

        params = {
            'uuids': ['67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6',
                      '31581d7c6b039318e9048c4d8571666c26a5622b']
        }

        executed = client.execute(self.SH_UNMERGE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, identities were unmerged
        uuids = executed['data']['unmergeIdentities']['uuids']
        self.assertEqual(len(uuids), 2)

        uuid1 = uuids[0]
        self.assertEqual(uuid1, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')

        uuid2 = uuids[1]
        self.assertEqual(uuid2, '31581d7c6b039318e9048c4d8571666c26a5622b')

        individuals = executed['data']['unmergeIdentities']['individuals']
        self.assertEqual(len(individuals), 2)

        individual = individuals[0]
        self.assertEqual(individual['mk'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')

        identities = individual['identities']
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity['uuid'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith-git@example')
        self.assertEqual(identity['source'], 'git')

        individual = individuals[1]
        self.assertEqual(individual['mk'], '31581d7c6b039318e9048c4d8571666c26a5622b')

        identities = individual['identities']
        self.assertEqual(len(identities), 1)

        identity = identities[0]
        self.assertEqual(identity['uuid'], '31581d7c6b039318e9048c4d8571666c26a5622b')
        self.assertEqual(identity['name'], None)
        self.assertEqual(identity['email'], 'jsmith3@libresoft')
        self.assertEqual(identity['source'], 'phabricator')

        # Check database objects
        individual_db = Individual.objects.get(mk='67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')

        self.assertIsInstance(individual_db, Individual)
        self.assertEqual(individual_db.mk, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')

        profile = individual_db.profile
        self.assertIsNone(profile.name)
        self.assertEqual(profile.email, 'jsmith-git@example')
        self.assertEqual(profile.is_bot, False)

        identities = individual_db.identities.all()
        self.assertEqual(len(identities), 1)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id1.email, 'jsmith-git@example')
        self.assertEqual(id1.source, 'git')

        enrollments = individual_db.enrollments.all()
        self.assertEqual(len(enrollments), 0)

        individual_db = Individual.objects.get(mk='31581d7c6b039318e9048c4d8571666c26a5622b')

        self.assertIsInstance(individual_db, Individual)
        self.assertEqual(individual_db.mk, '31581d7c6b039318e9048c4d8571666c26a5622b')

        profile = individual_db.profile
        self.assertIsNone(profile.name)
        self.assertEqual(profile.email, 'jsmith3@libresoft')
        self.assertEqual(profile.is_bot, False)

        identities = individual_db.identities.all()
        self.assertEqual(len(identities), 1)

        id1 = identities[0]
        self.assertEqual(id1.uuid, '31581d7c6b039318e9048c4d8571666c26a5622b')
        self.assertEqual(id1.email, 'jsmith3@libresoft')
        self.assertEqual(id1.source, 'phabricator')

        enrollments = individual_db.enrollments.all()
        self.assertEqual(len(enrollments), 0)

    def test_unmerge_uuid_from_individual(self):
        """Check if it ignores when the identity to unmerge is the same as the parent individual"""

        client = graphene.test.Client(schema)

        params = {
            'uuids': ['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3']
        }

        executed = client.execute(self.SH_UNMERGE,
                                  context_value=self.context_value,
                                  variables=params)

        individuals = executed['data']['unmergeIdentities']['individuals']
        self.assertEqual(len(individuals), 1)

        individual = individuals[0]
        self.assertEqual(individual['mk'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')

        identities = individual['identities']
        self.assertEqual(len(identities), 6)

        id1 = identities[0]
        self.assertEqual(id1['uuid'], '1c13fec7a328201fc6a230fe43eb81df0e20626e')
        self.assertEqual(id1['email'], 'jsmith@libresoft')
        self.assertEqual(id1['source'], 'scm')

        id2 = identities[1]
        self.assertEqual(id2['uuid'], '31581d7c6b039318e9048c4d8571666c26a5622b')
        self.assertEqual(id2['email'], 'jsmith3@libresoft')
        self.assertEqual(id2['source'], 'phabricator')

        id3 = identities[2]
        self.assertEqual(id3['uuid'], '67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6')
        self.assertEqual(id3['email'], 'jsmith-git@example')
        self.assertEqual(id3['source'], 'git')

        id4 = identities[3]
        self.assertEqual(id4['uuid'], '9225e296be341c20c11c4bae76df4190a5c4a918')
        self.assertEqual(id4['email'], 'jsmith-phab@bitergia')
        self.assertEqual(id4['source'], 'phabricator')

        id5 = identities[4]
        self.assertEqual(id5['uuid'], 'c2f5aa44e920b4fbe3cd36894b18e80a2606deba')
        self.assertEqual(id5['email'], 'jsmith2@libresoft')
        self.assertEqual(id5['source'], 'phabricator')

        id6 = identities[5]
        self.assertEqual(id6['uuid'], 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        self.assertEqual(id6['email'], 'jsmith@example')
        self.assertEqual(id6['source'], 'scm')

    def test_non_existing_uuids(self):
        """Check if it fails when source `uuids` field is `None` or an empty list"""

        client = graphene.test.Client(schema)

        params = {
            'uuids': []
        }

        executed = client.execute(self.SH_UNMERGE,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']

        self.assertEqual(msg, UUIDS_EMPTY_ERROR)

    def test_non_existing_uuid(self):
        """Check if it fails when any `uuid` is `None` or empty"""

        client = graphene.test.Client(schema)

        params = {
            'uuids': ['']
        }

        executed = client.execute(self.SH_UNMERGE,
                                  context_value=self.context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']

        self.assertEqual(msg, UUID_EMPTY_ERROR)

    def test_locked_uuid(self):
        """Check if it fails when the individual is locked"""

        client = graphene.test.Client(schema)

        uuid = 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3'
        api.lock(self.ctx, uuid)

        # Tests
        params = {
            'uuids': ['67fc4f8a56aa12ab981d2a4c1de065bb9936c9f6']
        }
        executed = client.execute(self.SH_UNMERGE,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UUID_LOCKED_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'uuids': ['e8284285566fdc1f41c8a22bb84a295fc3c4cbb3']
        }

        executed = client.execute(self.SH_UNMERGE,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']

        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestAffiliateMutation(django.test.TestCase):
    """Unit tests for mutation to affiliate individuals"""

    SH_AFFILIATE = """
        mutation affiliate($uuids: [String], $lastModified: DateTime) {
            affiliate(uuids: $uuids, lastModified: $lastModified) {
                jobId
            }
        }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        conn = django_rq.queues.get_redis_connection(None, True)
        conn.flushall()

        self.user = get_user_model().objects.create(username='test',
                                                    is_superuser=True)
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        # Organizations and domains
        api.add_organization(self.ctx, 'Example')
        api.add_domain(self.ctx, 'Example', 'example.com', is_top_domain=True)

        api.add_organization(self.ctx, 'Example Int.')
        api.add_domain(self.ctx, 'Example Int.', 'u.example.com',
                       is_top_domain=True)
        api.add_domain(self.ctx, 'Example Int.', 'es.u.example.com')
        api.add_domain(self.ctx, 'Example Int.', 'en.u.example.com')

        api.add_organization(self.ctx, 'Bitergia')
        api.add_domain(self.ctx, 'Bitergia', 'bitergia.com')
        api.add_domain(self.ctx, 'Bitergia', 'bitergia.org')

        api.add_organization(self.ctx, 'LibreSoft')

        # John Smith identity
        self.jsmith = api.add_identity(self.ctx,
                                       source='scm',
                                       email='jsmith@us.example.com',
                                       name='John Smith',
                                       username='jsmith')
        api.add_identity(self.ctx,
                         source='scm',
                         email='jsmith@example.net',
                         name='John Smith',
                         uuid=self.jsmith.uuid)

        # Add John Doe identity
        self.jdoe = api.add_identity(self.ctx,
                                     source='unknown',
                                     email=None,
                                     name='John Doe',
                                     username='jdoe')

        # Jane Roe identity
        self.jroe = api.add_identity(self.ctx,
                                     source='scm',
                                     email='jroe@example.com',
                                     name='Jane Roe',
                                     username='jroe')
        api.add_identity(self.ctx,
                         source='scm',
                         email='jroe@example.com',
                         uuid=self.jroe.uuid)
        api.add_identity(self.ctx,
                         source='unknown',
                         email='jroe@bitergia.com',
                         uuid=self.jroe.uuid)

    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_affiliate(self, mock_job_id_gen):
        """Check if all the individuals stored in the registry are affiliated"""

        mock_job_id_gen.return_value = "1234-5678-90AB-CDEF"

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_AFFILIATE,
                                  context_value=self.context_value)

        # Check if the job was run and individuals were affiliated
        job_id = executed['data']['affiliate']['jobId']
        self.assertEqual(job_id, "1234-5678-90AB-CDEF")

        # Check database objects
        individual_db = Individual.objects.get(mk=self.jroe.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 2)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        enrollment_db = enrollments_db[1]
        self.assertEqual(enrollment_db.group.name, 'Bitergia')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        individual_db = Individual.objects.get(mk=self.jsmith.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        # John Doe was not affiliated
        individual_db = Individual.objects.get(mk=self.jdoe.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 0)

    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_affiliate_uuid(self, mock_job_id_gen):
        """Check if only the given individuals are affiliated"""

        mock_job_id_gen.return_value = "1234-5678-90AB-CDEF"

        client = graphene.test.Client(schema)

        params = {
            'uuids': ['dc31d2afbee88a6d1dbc1ef05ec827b878067744']
        }

        executed = client.execute(self.SH_AFFILIATE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check if the job was run and individuals were affiliated
        job_id = executed['data']['affiliate']['jobId']
        self.assertEqual(job_id, "1234-5678-90AB-CDEF")

        # Check database objects

        # Only John Smith was affiliated
        individual_db = Individual.objects.get(mk=self.jsmith.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        # Jane Roe and John Doe were not affiliated
        individual_db = Individual.objects.get(mk=self.jroe.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 0)

        individual_db = Individual.objects.get(mk=self.jdoe.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 0)

    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_affiliate_last_modified(self, mock_job_id_gen):
        """Check if only the individuals modified after a given date are affiliated"""

        mock_job_id_gen.return_value = "1234-5678-90AB-CDEF"

        client = graphene.test.Client(schema)

        timestamp = datetime_utcnow()

        api.add_identity(self.ctx,
                         source='alt',
                         email='jsmith@example.net',
                         name='John Smith',
                         uuid=self.jsmith.uuid)

        params = {
            'lastModified': timestamp
        }

        executed = client.execute(self.SH_AFFILIATE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check if the job was run and individuals were affiliated
        job_id = executed['data']['affiliate']['jobId']
        self.assertEqual(job_id, "1234-5678-90AB-CDEF")

        # Check database objects

        # Only John Smith was affiliated
        individual_db = Individual.objects.get(mk=self.jsmith.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 1)

        enrollment_db = enrollments_db[0]
        self.assertEqual(enrollment_db.group.name, 'Example')
        self.assertEqual(enrollment_db.start, datetime.datetime(1900, 1, 1, tzinfo=UTC))
        self.assertEqual(enrollment_db.end, datetime.datetime(2100, 1, 1, tzinfo=UTC))

        # Jane Roe and John Doe were not affiliated
        individual_db = Individual.objects.get(mk=self.jroe.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 0)

        individual_db = Individual.objects.get(mk=self.jdoe.uuid)
        enrollments_db = individual_db.enrollments.all()
        self.assertEqual(len(enrollments_db), 0)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_AFFILIATE,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']

        self.assertEqual(msg, AUTHENTICATION_ERROR)

    def test_authorization(self):
        """Check if it fails when a non-authorized user executes the job"""

        user = get_user_model().objects.create(username='test_unauthorized')
        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = user
        client = graphene.test.Client(schema)

        self.assertFalse(user.has_perm(EXECUTE_JOB_PERMISSION))

        executed = client.execute(self.SH_AFFILIATE,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']

        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestUnifyMutation(django.test.TestCase):
    """Unit tests for mutation to unify individuals"""

    SH_UNIFY = """
        mutation unify($sourceUuids: [String],
                       $targetUuids: [String],
                       $criteria: [String],
                       $strict: Boolean,
                       $matchSource: Boolean,
                       $lastModified: DateTime) {
            unify(sourceUuids: $sourceUuids,
                  targetUuids: $targetUuids,
                  criteria: $criteria,
                  strict: $strict,
                  matchSource: $matchSource
                  lastModified: $lastModified) {
                jobId
            }
        }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        conn = django_rq.queues.get_redis_connection(None, True)
        conn.flushall()

        self.user = get_user_model().objects.create(username='test', is_superuser=True)
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        # Individual 1
        self.john_smith = api.add_identity(self.ctx,
                                           email='jsmith@example.com',
                                           name='John Smith',
                                           source='scm')
        self.js2 = api.add_identity(self.ctx,
                                    name='John Smith',
                                    source='scm',
                                    uuid=self.john_smith.uuid)
        self.js3 = api.add_identity(self.ctx,
                                    username='jsmith',
                                    source='scm',
                                    uuid=self.john_smith.uuid)

        # Individual 2
        self.jsmith = api.add_identity(self.ctx,
                                       name='J. Smith',
                                       username='john_smith',
                                       source='alt')
        self.jsm2 = api.add_identity(self.ctx,
                                     name='John Smith',
                                     username='jsmith',
                                     source='alt',
                                     uuid=self.jsmith.uuid)
        self.jsm3 = api.add_identity(self.ctx,
                                     email='jsmith@example.com',
                                     source='alt',
                                     uuid=self.jsmith.uuid)

        # Individual 3
        self.jane_rae = api.add_identity(self.ctx,
                                         name='Janer Rae',
                                         source='mls')
        self.jr2 = api.add_identity(self.ctx,
                                    email='jane.rae@example.net',
                                    name='Jane Rae Doe',
                                    source='mls',
                                    uuid=self.jane_rae.uuid)

        # Individual 4
        self.js_alt = api.add_identity(self.ctx,
                                       name='J. Smith',
                                       username='john_smith',
                                       source='scm')
        self.js_alt2 = api.add_identity(self.ctx,
                                        email='JSmith@example.com',
                                        username='john_smith',
                                        source='mls',
                                        uuid=self.js_alt.uuid)
        self.js_alt3 = api.add_identity(self.ctx,
                                        username='Smith. J',
                                        source='mls',
                                        uuid=self.js_alt.uuid)
        self.js_alt4 = api.add_identity(self.ctx,
                                        email='JSmith@example.com',
                                        name='Smith. J',
                                        source='mls',
                                        uuid=self.js_alt.uuid)

        # Individual 5
        self.jrae = api.add_identity(self.ctx,
                                     email='jrae@example.net',
                                     name='Jane Rae Doe',
                                     source='mls')
        self.jrae2 = api.add_identity(self.ctx,
                                      name='jrae',
                                      source='mls',
                                      uuid=self.jrae.uuid)
        self.jrae3 = api.add_identity(self.ctx,
                                      name='jrae',
                                      source='scm',
                                      uuid=self.jrae.uuid)

    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_unify(self, mock_job_id_gen):
        """Check if unify is applied for the specified individuals"""

        mock_job_id_gen.return_value = "1234-5678-90AB-CDEF"

        client = graphene.test.Client(schema)

        params = {
            'sourceUuids': [self.john_smith.uuid, self.jrae3.uuid, self.jr2.uuid],
            'targetUuids': [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                            self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                            self.jane_rae.uuid, self.jr2.uuid,
                            self.js_alt.uuid, self.js_alt2.uuid,
                            self.js_alt3.uuid, self.js_alt4.uuid,
                            self.jrae.uuid, self.jrae2.uuid, self.jrae3.uuid],
            'criteria': ['email', 'name', 'username'],
            'strict': False
        }

        executed = client.execute(self.SH_UNIFY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check if the job was run and individuals were merged
        job_id = executed['data']['unify']['jobId']
        self.assertEqual(job_id, "1234-5678-90AB-CDEF")

        # Checking if the identities have been merged
        # Individual 1
        individual_db_1 = Individual.objects.get(mk=self.jsmith.uuid)
        identities = individual_db_1.identities.all()
        self.assertEqual(len(identities), 6)

        id1 = identities[0]
        self.assertEqual(id1, self.jsm2)

        id2 = identities[1]
        self.assertEqual(id2, self.jsmith)

        id3 = identities[2]
        self.assertEqual(id3, self.jsm3)

        id4 = identities[3]
        self.assertEqual(id4, self.john_smith)

        id5 = identities[4]
        self.assertEqual(id5, self.js2)

        id6 = identities[5]
        self.assertEqual(id6, self.js3)

        # Individual 2
        individual_db_2 = Individual.objects.get(mk=self.jrae.uuid)
        identities = individual_db_2.identities.all()
        self.assertEqual(len(identities), 5)

        id1 = identities[0]
        self.assertEqual(id1, self.jrae2)

        id2 = identities[1]
        self.assertEqual(id2, self.jrae3)

        id3 = identities[2]
        self.assertEqual(id3, self.jrae)

        id4 = identities[3]
        self.assertEqual(id4, self.jane_rae)

        id5 = identities[4]
        self.assertEqual(id5, self.jr2)

    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_unify_last_modified(self, mock_job_id_gen):
        """Check if unify is applied only for the individuals modified after a date"""

        mock_job_id_gen.return_value = "1234-5678-90AB-CDEF"

        client = graphene.test.Client(schema)

        timestamp = datetime_utcnow()

        new_identity = api.add_identity(self.ctx,
                                        email='jsmith.alt@example.com',
                                        source='alt',
                                        uuid=self.js_alt.uuid)

        params = {
            'lastModified': timestamp,
            'criteria': ['email', 'name', 'username']
        }

        executed = client.execute(self.SH_UNIFY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check if the job was run and individuals were merged
        job_id = executed['data']['unify']['jobId']
        self.assertEqual(job_id, "1234-5678-90AB-CDEF")

        # Checking if the identities have been merged
        # Individual 1
        individual_db_1 = Individual.objects.get(mk=self.js_alt.uuid)
        identities = individual_db_1.identities.all()
        self.assertEqual(len(identities), 8)

        id1 = identities[0]
        self.assertEqual(id1, self.jsm2)

        id2 = identities[1]
        self.assertEqual(id2, self.js_alt)

        id3 = identities[2]
        self.assertEqual(id3, self.js_alt4)

        id4 = identities[3]
        self.assertEqual(id4, self.js_alt3)

        id5 = identities[4]
        self.assertEqual(id5, self.jsmith)

        id6 = identities[5]
        self.assertEqual(id6, self.jsm3)

        id7 = identities[6]
        self.assertEqual(id7, new_identity)

        id8 = identities[7]
        self.assertEqual(id8, self.js_alt2)

        # Individual 2
        individual_db_2 = Individual.objects.get(mk=self.john_smith.uuid)
        identities = individual_db_2.identities.all()
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1, self.john_smith)

        id2 = identities[1]
        self.assertEqual(id2, self.js2)

        id3 = identities[2]
        self.assertEqual(id3, self.js3)

        # Individual 3
        individual_db_3 = Individual.objects.get(mk=self.jrae.uuid)
        identities = individual_db_3.identities.all()
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1, self.jrae2)

        id2 = identities[1]
        self.assertEqual(id2, self.jrae3)

        id3 = identities[2]
        self.assertEqual(id3, self.jrae)

        # Individual 4
        individual_db_4 = Individual.objects.get(mk=self.jane_rae.uuid)
        identities = individual_db_4.identities.all()
        self.assertEqual(len(identities), 2)

        id1 = identities[0]
        self.assertEqual(id1, self.jane_rae)

        id2 = identities[1]
        self.assertEqual(id2, self.jr2)

    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_unify_exclude(self, mock_job_id_gen):
        """Check if unify is applied for the specified individuals"""

        sh_add_ret = """
          mutation addRecommenderExclusionTerm {
            addRecommenderExclusionTerm(term: "%s") {
              exclusion {
                term
              }
            }
          }
        """

        mock_job_id_gen.return_value = "1234-5678-90AB-CDEF"

        client = graphene.test.Client(schema)

        params = {
            'sourceUuids': [self.john_smith.uuid, self.jrae3.uuid, self.jr2.uuid],
            'targetUuids': [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                            self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                            self.jane_rae.uuid, self.jr2.uuid,
                            self.js_alt.uuid, self.js_alt2.uuid,
                            self.js_alt3.uuid, self.js_alt4.uuid,
                            self.jrae.uuid, self.jrae2.uuid, self.jrae3.uuid],
            'criteria': ['email', 'name', 'username'],
            'strict': False
        }

        # Add jsmith@example.com to RecommenderExclusionTerm
        executed_add_1 = client.execute(sh_add_ret % "jsmith@example.com",
                                        context_value=self.context_value)
        exclusion = executed_add_1['data']['addRecommenderExclusionTerm']['exclusion']
        self.assertEqual(exclusion['term'], "jsmith@example.com")

        # Add jsmith to RecommenderExclusionTerm
        executed_add_2 = client.execute(sh_add_ret % "jsmith",
                                        context_value=self.context_value)
        exclusion = executed_add_2['data']['addRecommenderExclusionTerm']['exclusion']
        self.assertEqual(exclusion['term'], "jsmith")

        executed = client.execute(self.SH_UNIFY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check if the job was run and individuals were merged
        job_id = executed['data']['unify']['jobId']
        self.assertEqual(job_id, "1234-5678-90AB-CDEF")

        # Checking if the identities have been merged
        # Individual 1
        individual_db_1 = Individual.objects.get(mk=self.jsmith.uuid)
        identities = individual_db_1.identities.all()
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1, self.jsm2)

        id2 = identities[1]
        self.assertEqual(id2, self.jsmith)

        id3 = identities[2]
        self.assertEqual(id3, self.jsm3)

        # Individual 2
        individual_db_2 = Individual.objects.get(mk=self.john_smith.uuid)
        identities = individual_db_2.identities.all()
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1, self.john_smith)

        id2 = identities[1]
        self.assertEqual(id2, self.js2)

        id3 = identities[2]
        self.assertEqual(id3, self.js3)

        # Individual 3
        individual_db_3 = Individual.objects.get(mk=self.jrae.uuid)
        identities = individual_db_3.identities.all()
        self.assertEqual(len(identities), 5)

        id1 = identities[0]
        self.assertEqual(id1, self.jrae2)

        id2 = identities[1]
        self.assertEqual(id2, self.jrae3)

        id3 = identities[2]
        self.assertEqual(id3, self.jrae)

        id4 = identities[3]
        self.assertEqual(id4, self.jane_rae)

        id5 = identities[4]
        self.assertEqual(id5, self.jr2)

    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_unify_strict(self, mock_job_id_gen):
        """Check if unify is applied for the specified individuals with strict criteria"""
        mock_job_id_gen.return_value = "1234-5678-90AB-CDEF"

        client = graphene.test.Client(schema)

        params = {
            'sourceUuids': [self.js_alt.uuid],
            'targetUuids': [self.jsmith.uuid],
            'criteria': ['name'],
            'strict': True
        }

        executed = client.execute(self.SH_UNIFY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check if the job was run
        job_id = executed['data']['unify']['jobId']
        self.assertEqual(job_id, "1234-5678-90AB-CDEF")

        # Checking if the identities have not been merged
        # Individual 1
        individual_db_1 = Individual.objects.get(mk=self.jsmith.uuid)
        identities = individual_db_1.identities.all()
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1, self.jsm2)

        id2 = identities[1]
        self.assertEqual(id2, self.jsmith)

        id3 = identities[2]
        self.assertEqual(id3, self.jsm3)

        # Individual 4
        individual_db_4 = Individual.objects.get(mk=self.js_alt.uuid)
        identities = individual_db_4.identities.all()

        self.assertEqual(len(identities), 4)

        id1 = identities[0]
        self.assertEqual(id1, self.js_alt)

        id2 = identities[1]
        self.assertEqual(id2, self.js_alt4)

        id3 = identities[2]
        self.assertEqual(id3, self.js_alt3)

        id4 = identities[3]
        self.assertEqual(id4, self.js_alt2)

        # Check that they are merged if 'strict' is disabled
        params = {
            'sourceUuids': [self.js_alt.uuid],
            'targetUuids': [self.jsmith.uuid],
            'criteria': ['name'],
            'strict': False
        }

        executed = client.execute(self.SH_UNIFY,
                                  context_value=self.context_value,
                                  variables=params)

        individual_db_1 = Individual.objects.get(mk=self.js_alt.uuid)
        identities = individual_db_1.identities.all()

        self.assertEqual(len(identities), 7)

    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_unify_match_source(self, mock_job_id_gen):
        """Check if unify is applied for the specified individuals"""

        mock_job_id_gen.return_value = "1234-5678-90AB-CDEF"

        client = graphene.test.Client(schema)

        jr3 = api.add_identity(self.ctx,
                               name='J. Rae',
                               username='jane_rae',
                               source='github',
                               uuid=self.jane_rae.uuid)
        jrae_github = api.add_identity(self.ctx,
                                       name='Jane Rae',
                                       username='jane_rae',
                                       source='github')

        params = {
            'sourceUuids': [self.john_smith.uuid, self.jrae3.uuid, self.jr2.uuid],
            'targetUuids': [self.john_smith.uuid, self.js2.uuid, self.js3.uuid,
                            self.jsmith.uuid, self.jsm2.uuid, self.jsm3.uuid,
                            self.jane_rae.uuid, self.jr2.uuid,
                            self.js_alt.uuid, self.js_alt2.uuid,
                            self.js_alt3.uuid, self.js_alt4.uuid,
                            self.jrae.uuid, self.jrae2.uuid, self.jrae3.uuid,
                            jrae_github.uuid],
            'criteria': ['email', 'name', 'username'],
            'strict': False,
            'matchSource': True
        }

        executed = client.execute(self.SH_UNIFY,
                                  context_value=self.context_value,
                                  variables=params)

        # Check if the job was run and individuals were merged
        job_id = executed['data']['unify']['jobId']
        self.assertEqual(job_id, "1234-5678-90AB-CDEF")

        # Individual 1 no changed
        individual_db_1 = Individual.objects.get(mk=self.jsmith.uuid)
        identities = individual_db_1.identities.all()
        self.assertEqual(len(identities), 3)

        # Individual 3 with new identities merged
        individual_db_2 = Individual.objects.get(mk=jrae_github.uuid)
        identities = individual_db_2.identities.all()
        self.assertEqual(len(identities), 4)

        id1 = identities[0]
        self.assertEqual(id1, jrae_github)

        id2 = identities[1]
        self.assertEqual(id2, jr3)

        id3 = identities[2]
        self.assertEqual(id3, self.jane_rae)

        id4 = identities[3]
        self.assertEqual(id4, self.jr2)

    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_unify_source_not_mk(self, mock_job_id_gen):
        """Check if unify works when the provided uuid is not an Individual's main key"""
        pass

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_UNIFY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']

        self.assertEqual(msg, AUTHENTICATION_ERROR)

    def test_authorization(self):
        """Check if it fails when a non-authorized user executes the job"""

        user = get_user_model().objects.create(username='test_unauthorized')
        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = user
        client = graphene.test.Client(schema)

        self.assertFalse(user.has_perm(EXECUTE_JOB_PERMISSION))

        executed = client.execute(self.SH_UNIFY,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']

        self.assertEqual(msg, AUTHENTICATION_ERROR)


def setup_genderize_server():
    """Setup a mock HTTP server for genderize.io"""

    http_requests = []

    def request_callback(method, uri, headers):
        last_request = httpretty.last_request()
        http_requests.append(last_request)

        params = last_request.querystring
        name = params['name'][0].lower()

        if name == 'error':
            return 502, headers, 'Bad Gateway'

        if name == 'john':
            data = {
                'gender': 'male',
                'probability': 0.99
            }
        elif name == 'jane':
            data = {
                'gender': 'female',
                'probability': 0.99
            }
        else:
            data = {
                'gender': None,
                'probability': None
            }

        body = json.dumps(data)

        return (200, headers, body)

    httpretty.register_uri(httpretty.GET,
                           "https://api.genderize.io/",
                           responses=[
                               httpretty.Response(body=request_callback)
                           ])

    return http_requests


class TestGenderizeMutation(django.test.TestCase):
    """Unit tests for mutation to autocomplete gender information"""

    SH_GENDERIZE = """
        mutation genderize($uuids: [String], $noStrictMatching: Boolean) {
            genderize(uuids: $uuids, noStrictMatching: $noStrictMatching) {
                jobId
            }
        }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        conn = django_rq.queues.get_redis_connection(None, True)
        conn.flushall()

        self.user = get_user_model().objects.create(username='test',
                                                    is_superuser=True)
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        ctx = SortingHatContext(self.user)

        self.john_smith = api.add_identity(ctx,
                                           email='jsmith@example.com',
                                           name='John Smith',
                                           source='scm')
        self.jane_roe = api.add_identity(ctx,
                                         email='jroe@example.com',
                                         name='Jane Roe',
                                         source='scm')
        self.john = api.add_identity(ctx,
                                     email='jsmith@example.com',
                                     name='John',
                                     source='scm')

    @httpretty.activate
    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_genderize(self, mock_job_id_gen):
        """Check if genderize is applied for the specified individuals"""

        setup_genderize_server()

        mock_job_id_gen.return_value = "1234-5678-90AB-CDEF"

        client = graphene.test.Client(schema)

        params = {
            'uuids': [self.john_smith.uuid]
        }

        executed = client.execute(self.SH_GENDERIZE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check if the job was run
        job_id = executed['data']['genderize']['jobId']
        self.assertEqual(job_id, "1234-5678-90AB-CDEF")

        # Check if the individual's gender was updated
        indv = Individual.objects.get(mk=self.john_smith.uuid)
        gender = indv.profile.gender
        self.assertEqual(gender, "male")

        # Check if the rest of the individuals were not updated
        indv = Individual.objects.get(mk=self.jane_roe.uuid)
        gender = indv.profile.gender
        self.assertEqual(gender, None)

    @httpretty.activate
    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_genderize_not_strict(self, mock_job_id_gen):
        """Check if genderize is applied without strict validation"""

        setup_genderize_server()

        mock_job_id_gen.return_value = "1234-5678-90AB-CDEF"

        client = graphene.test.Client(schema)

        params = {
            'uuids': [self.john_smith.uuid, self.john.uuid],
            'noStrictMatching': True
        }

        executed = client.execute(self.SH_GENDERIZE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check if the job was run
        job_id = executed['data']['genderize']['jobId']
        self.assertEqual(job_id, "1234-5678-90AB-CDEF")

        # Check if the individual's gender was updated
        indv = Individual.objects.get(mk=self.john_smith.uuid)
        gender = indv.profile.gender
        self.assertEqual(gender, "male")

        indv = Individual.objects.get(mk=self.john.uuid)
        gender = indv.profile.gender
        self.assertEqual(gender, "male")

        # Check if the rest of the individuals were not updated
        indv = Individual.objects.get(mk=self.jane_roe.uuid)
        gender = indv.profile.gender
        self.assertEqual(gender, None)

    @httpretty.activate
    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_genderize_all_strict(self, mock_job_id_gen):
        """Check if genderize is applied for all valid individuals in the registry"""

        setup_genderize_server()

        mock_job_id_gen.return_value = "1234-5678-90AB-CDEF"

        client = graphene.test.Client(schema)

        params = {
            'uuids': None
        }

        executed = client.execute(self.SH_GENDERIZE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check if the job was run
        job_id = executed['data']['genderize']['jobId']
        self.assertEqual(job_id, "1234-5678-90AB-CDEF")

        # Check if all the valid individuals genders were updated
        indv1 = Individual.objects.get(mk=self.john_smith.uuid)
        gender1 = indv1.profile.gender
        self.assertEqual(gender1, "male")

        indv2 = Individual.objects.get(mk=self.jane_roe.uuid)
        gender2 = indv2.profile.gender
        self.assertEqual(gender2, "female")

        # Check if the individuals with invalid names were not updated
        indv = Individual.objects.get(mk=self.john.uuid)
        gender = indv.profile.gender
        self.assertEqual(gender, None)

    @httpretty.activate
    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_genderize_all_not_strict(self, mock_job_id_gen):
        """Check if genderize is applied for all individuals in the registry"""

        setup_genderize_server()

        mock_job_id_gen.return_value = "1234-5678-90AB-CDEF"

        client = graphene.test.Client(schema)

        params = {
            'uuids': None,
            'noStrictMatching': True
        }

        executed = client.execute(self.SH_GENDERIZE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check if the job was run
        job_id = executed['data']['genderize']['jobId']
        self.assertEqual(job_id, "1234-5678-90AB-CDEF")

        # Check if all the individuals genders were updated
        indv1 = Individual.objects.get(mk=self.john_smith.uuid)
        gender1 = indv1.profile.gender
        self.assertEqual(gender1, "male")

        indv2 = Individual.objects.get(mk=self.jane_roe.uuid)
        gender2 = indv2.profile.gender
        self.assertEqual(gender2, "female")

        indv = Individual.objects.get(mk=self.john.uuid)
        gender = indv.profile.gender
        self.assertEqual(gender, "male")

    @httpretty.activate
    @unittest.mock.patch('sortinghat.core.jobs.rq.job.uuid4')
    def test_genderize_exclude(self, mock_job_id_gen):
        """Check if genderize activating exclude"""
        sh_add_ret = """
          mutation addRecommenderExclusionTerm {
            addRecommenderExclusionTerm(term: "jsmith@example.com") {
              exclusion {
                term
              }
            }
          }
        """

        setup_genderize_server()

        mock_job_id_gen.return_value = "1234-5678-90AB-CDEF"

        client = graphene.test.Client(schema)

        params = {
            'uuids': None
        }

        # Add jsmith@example.com to excluded
        executed_add_exclusion = client.execute(sh_add_ret,
                                                context_value=self.context_value)

        exclusion = executed_add_exclusion['data']['addRecommenderExclusionTerm']['exclusion']
        self.assertEqual(exclusion['term'], "jsmith@example.com")

        executed = client.execute(self.SH_GENDERIZE,
                                  context_value=self.context_value,
                                  variables=params)

        # Check if the job was run
        job_id = executed['data']['genderize']['jobId']
        self.assertEqual(job_id, "1234-5678-90AB-CDEF")

        # Check if all the individuals genders were updated
        indv1 = Individual.objects.get(mk=self.john_smith.uuid)
        gender1 = indv1.profile.gender
        self.assertIsNone(gender1)

        indv2 = Individual.objects.get(mk=self.jane_roe.uuid)
        gender2 = indv2.profile.gender
        self.assertEqual(gender2, "female")

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the job"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_GENDERIZE,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']

        self.assertEqual(msg, AUTHENTICATION_ERROR)

    def test_authorization(self):
        """Check if it fails when a non-authorized user executes the job"""

        user = get_user_model().objects.create(username='test_unauthorized')
        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = user
        client = graphene.test.Client(schema)

        self.assertFalse(user.has_perm(EXECUTE_JOB_PERMISSION))

        executed = client.execute(self.SH_GENDERIZE,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']

        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestAddRecommenderExclusionTermMutation(django.test.TestCase):
    """Unit tests for mutation to add recommenderExclusionTerm"""

    SH_ADD_RET = """
      mutation addRecommenderExclusionTerm {
        addRecommenderExclusionTerm(term: "John Smith") {
          exclusion {
            term
          }
        }
      }
    """

    SH_ADD_RET_NAME_EMPTY = """
      mutation addRecommenderExclusionTerm {
        addRecommenderExclusionTerm(term: "") {
          exclusion {
            term
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_add_recommenderExclusionTerm(self):
        """Check if a new recommenderExclusionTerm is added"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_RET,
                                  context_value=self.context_value)

        # Check result
        rel = executed['data']['addRecommenderExclusionTerm']['exclusion']
        self.assertEqual(rel['term'], 'John Smith')

        # Check database
        rel = RecommenderExclusionTerm.objects.get(term='John Smith')
        self.assertEqual(rel.term, 'John Smith')

    def test_name_empty(self):
        """Check whether recommenderExclusionTerm with empty entry cannot be added"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_RET_NAME_EMPTY,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, TERM_EMPTY_ERROR)

        # Check database
        rel = RecommenderExclusionTerm.objects.all()
        self.assertEqual(len(rel), 0)

    def test_integrity_error(self):
        """Check whether recommenderExclusionTerm with the same entry cannot be inserted"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_RET,
                                  context_value=self.context_value)

        # Check database
        rel = RecommenderExclusionTerm.objects.get(term='John Smith')
        self.assertEqual(rel.term, 'John Smith')

        # Try to insert it twice
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_RET,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_RET_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_ADD_RET,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestDeleteRecommenderExclusionTermMutation(django.test.TestCase):
    """Unit tests for mutation to delete recommenderExclusionTerm entry"""

    SH_DELETE_RET = """
      mutation deleteRecommenderExclusionTerm {
        deleteRecommenderExclusionTerm(term: "John Smith"){
          exclusion {
            term
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_delete_recommenderExclusionTerm(self):
        """Check whether it deletes an entry"""

        # Add entry
        RecommenderExclusionTerm.objects.create(term='John Smith')

        # Delete entry
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_RET,
                                  context_value=self.context_value)

        # Check result
        rel = executed['data']['deleteRecommenderExclusionTerm']['exclusion']
        self.assertEqual(rel['term'], 'John Smith')

        # Tests
        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            RecommenderExclusionTerm.objects.get(term='John Smith')

    def test_not_found_recommenderExclusionTerm(self):
        """Check if it returns an error when an entry does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_RET,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, TERM_EXAMPLE_DOES_NOT_EXIST_ERROR)

        # It should not remove anything
        RecommenderExclusionTerm.objects.create(term='Quan')

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, TERM_EXAMPLE_DOES_NOT_EXIST_ERROR)

        rel = RecommenderExclusionTerm.objects.all()
        self.assertEqual(len(rel), 1)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_DELETE_RET,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestManageRecommendationMergeMutation(django.test.TestCase):
    """Unit tests for mutation to accept a match recommendation"""

    SH_MANAGE_REC = """
      mutation manageMergeRecommendation {
        manageMergeRecommendation (recommendationId: %s, apply: %s) {
          applied
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_apply_recommendation_merge(self):
        """Check whether it merges a recommendation"""

        # Create recommendation
        indv1 = Individual.objects.create(mk='AAAA')
        indv2 = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name="Jhon",
                               email='jsmith@example.com',
                               is_bot=False,
                               gender='Male',
                               individual=indv1)
        Profile.objects.create(name="Jhon",
                               email='jsmith2@example.com',
                               is_bot=False,
                               gender='Male',
                               individual=indv2)
        rec = MergeRecommendation.objects.create(individual1=indv1, individual2=indv2)

        # Apply recommendation
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_MANAGE_REC % (rec.id, "true"),
                                  context_value=self.context_value)

        # Check result
        rel = executed['data']['manageMergeRecommendation']
        self.assertEqual(rel['applied'], True)

        # Tests
        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            MergeRecommendation.objects.get(id=rec.id)

    def test_dismiss_recommendation_merge(self):
        """Check whether it dismiss a recommendation"""

        # Create recommendation
        indv1 = Individual.objects.create(mk='AAAA')
        indv2 = Individual.objects.create(mk='BBBB')
        Profile.objects.create(name="Jhon",
                               email='jsmith@example.com',
                               is_bot=False,
                               gender='Male',
                               individual=indv1)
        Profile.objects.create(name="Jhon",
                               email='jsmith2@example.com',
                               is_bot=False,
                               gender='Male',
                               individual=indv2)
        rec = MergeRecommendation.objects.create(individual1=indv1, individual2=indv2)

        # Dismiss recommendation
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_MANAGE_REC % (rec.id, "false"),
                                  context_value=self.context_value)

        # Check result
        rel = executed['data']['manageMergeRecommendation']
        self.assertEqual(rel['applied'], False)

        # Tests
        updated_rec = MergeRecommendation.objects.get(id=rec.id)
        self.assertFalse(updated_rec.applied)

    def test_not_found_recommendationMerge(self):
        """Check if it returns an error when an entry does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_MANAGE_REC % (1000, "true"),
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, RECOMMENDATION_MERGE_DOES_NOT_EXIST_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_MANAGE_REC % (1, "true"),
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestManageRecommendationGenderMutation(django.test.TestCase):
    """Unit tests for mutation to accept a match recommendation"""

    SH_MANAGE_REC = """
      mutation manageGenderRecommendation {
        manageGenderRecommendation (recommendationId: %s, apply: %s) {
          applied
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_apply_recommendation_gender(self):
        """Check whether it applies a recommendation"""

        # Create recommendation
        indv1 = Individual.objects.create(mk='AAAA')
        p = Profile.objects.create(name="Jhon",
                                   email='jsmith@example.com',
                                   is_bot=False,
                                   gender='Male',
                                   individual=indv1)
        rec = GenderRecommendation.objects.create(individual=indv1, gender='Female', accuracy=90)

        # Apply recommendation
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_MANAGE_REC % (rec.id, "true"),
                                  context_value=self.context_value)

        # Check result
        rel = executed['data']['manageGenderRecommendation']
        self.assertTrue(rel['applied'])

        # Tests
        updated_rec = GenderRecommendation.objects.get(id=rec.id)
        self.assertTrue(updated_rec.applied)
        p.refresh_from_db()
        self.assertEqual(p.gender, 'Female')

    def test_dismiss_recommendation_gender(self):
        """Check whether it dismiss a recommendation"""

        # Create recommendation
        indv1 = Individual.objects.create(mk='AAAA')
        p = Profile.objects.create(name="Jhon",
                                   email='jsmith@example.com',
                                   is_bot=False,
                                   gender='Male',
                                   individual=indv1)
        rec = GenderRecommendation.objects.create(individual=indv1, gender='Female', accuracy=90)

        # Apply recommendation
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_MANAGE_REC % (rec.id, "false"),
                                  context_value=self.context_value)

        # Check result
        rel = executed['data']['manageGenderRecommendation']
        self.assertFalse(rel['applied'])

        # Tests
        updated_rec = GenderRecommendation.objects.get(id=rec.id)
        self.assertFalse(updated_rec.applied)
        p.refresh_from_db()
        self.assertEqual(p.gender, 'Male')

    def test_not_found_recommendationGender(self):
        """Check if it returns an error when an entry does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_MANAGE_REC % (1000, "true"),
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, RECOMMENDATION_GENDER_DOES_NOT_EXIST_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_MANAGE_REC % (1, "true"),
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestManageRecommendationAffiliationMutation(django.test.TestCase):
    """Unit tests for mutation to accept an affiliation recommendation"""

    SH_MANAGE_REC = """
      mutation manageAffiliationRecommendation {
        manageAffiliationRecommendation (recommendationId: %s, apply: %s) {
          applied
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_apply_recommendation_affiliation(self):
        """Check whether it applies a recommendation"""

        # Create recommendation
        indv1 = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name="Jhon",
                               email='jsmith@example.com',
                               is_bot=False,
                               gender='Male',
                               individual=indv1)
        org_ex = Organization.add_root(name='Example')
        rec = AffiliationRecommendation.objects.create(individual=indv1, organization=org_ex)

        # Apply recommendation
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_MANAGE_REC % (rec.id, "true"),
                                  context_value=self.context_value)

        # Check result
        rel = executed['data']['manageAffiliationRecommendation']
        self.assertTrue(rel['applied'])

        # Tests
        updated_rec = AffiliationRecommendation.objects.get(id=rec.id)
        self.assertTrue(updated_rec.applied)
        indv1.refresh_from_db()
        self.assertTrue(indv1.enrollments.filter(group__name='Example').exists())

    def test_dismiss_recommendation_affiliation(self):
        """Check whether it dismiss a recommendation"""

        # Create recommendation
        indv1 = Individual.objects.create(mk='AAAA')
        Profile.objects.create(name="Jhon",
                               email='jsmith@example.com',
                               is_bot=False,
                               gender='Male',
                               individual=indv1)
        org_ex = Organization.add_root(name='Example')
        rec = AffiliationRecommendation.objects.create(individual=indv1, organization=org_ex)

        # Apply recommendation
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_MANAGE_REC % (rec.id, "false"),
                                  context_value=self.context_value)

        # Check result
        rel = executed['data']['manageAffiliationRecommendation']
        self.assertFalse(rel['applied'])

        # Tests
        updated_rec = AffiliationRecommendation.objects.get(id=rec.id)
        self.assertFalse(updated_rec.applied)
        indv1.refresh_from_db()
        self.assertFalse(indv1.enrollments.exists())

    def test_not_found_recommendationAffiliation(self):
        """Check if it returns an error when an entry does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_MANAGE_REC % (1000, "true"),
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, RECOMMENDATION_AFFILIATION_DOES_NOT_EXIST_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_MANAGE_REC % (1, "true"),
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestMergeOrganizationsMutation(django.test.TestCase):
    """Unit tests for mutation to merge organizations"""

    SH_MERGE_ORGS = """
          mutation mergeOrgs($fromOrg: String, $toOrg: String) {
            mergeOrganizations(fromOrg: $fromOrg, toOrg: $toOrg) {
              organization {
                lastModified
                name
                teams {
                  name
                }
                domains {
                  domain
                }
                enrollments {
                  individual {
                    mk
                  }
                }
                aliases {
                  alias
                }
              }
            }
          }
        """

    def setUp(self):
        """Load initial dataset and set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

        self.ctx = SortingHatContext(self.user)

        # Transaction
        self.trxl = TransactionsLog.open('merge_organizations', self.ctx)

        db.add_organization(self.trxl, 'Example')
        db.add_organization(self.trxl, 'Bitergia')

        api.add_domain(self.ctx,
                       organization='Example',
                       domain_name='example.com',
                       is_top_domain=True)
        api.add_domain(self.ctx,
                       organization='Bitergia',
                       domain_name='bitergia.com',
                       is_top_domain=True)

        api.add_alias(self.ctx, organization='Example', name='Example Inc.')
        api.add_alias(self.ctx, organization='Bitergia', name='Bitergium')

        api.add_team(self.ctx, 'Example team', organization='Example')
        api.add_team(self.ctx, 'Bitergia team', organization='Bitergia')

        indv1 = api.add_identity(self.ctx, 'scm', email='jsmith@example')
        indv2 = api.add_identity(self.ctx, 'git', email='jsmith@bitergia')

        api.enroll(self.ctx,
                   indv1.uuid,
                   'Example',
                   from_date=datetime.datetime(1900, 1, 1),
                   to_date=datetime.datetime(2017, 1, 1))
        api.enroll(self.ctx,
                   indv2.uuid,
                   'Bitergia',
                   from_date=datetime.datetime(1990, 1, 1),
                   to_date=datetime.datetime(2000, 1, 1))

    def test_merge_organizations(self):
        """Check whether it merges two organizations, merging their domains, teams and enrollments"""

        client = graphene.test.Client(schema)

        params = {
            'fromOrg': 'Example',
            'toOrg': 'Bitergia'
        }

        executed = client.execute(self.SH_MERGE_ORGS,
                                  context_value=self.context_value,
                                  variables=params)

        # Check results, organizations were merged
        organization = executed['data']['mergeOrganizations']['organization']

        domains = organization['domains']
        self.assertEqual(len(domains), 2)
        self.assertEqual(domains[0]['domain'], 'bitergia.com')
        self.assertEqual(domains[1]['domain'], 'example.com')

        teams = organization['teams']
        self.assertEqual(len(teams), 2)
        self.assertEqual(teams[0]['name'], 'Bitergia team')
        self.assertEqual(teams[1]['name'], 'Example team')

        enrollments = organization['enrollments']
        self.assertEqual(len(enrollments), 2)
        individual = enrollments[0]['individual']['mk']
        self.assertEqual(individual, 'e8284285566fdc1f41c8a22bb84a295fc3c4cbb3')
        individual = enrollments[1]['individual']['mk']
        self.assertEqual(individual, 'c79e5c1587ac851b9b44720bd2242e9358a6eb70')

        aliases = organization['aliases']
        self.assertEqual(len(aliases), 3)
        self.assertEqual(aliases[0]['alias'], 'Bitergium')
        self.assertEqual(aliases[1]['alias'], 'Example')
        self.assertEqual(aliases[2]['alias'], 'Example Inc.')

        # Check database objects
        organization_db = Organization.objects.get(name='Bitergia')
        self.assertIsInstance(organization_db, Organization)

        domains = organization_db.domains.all()
        self.assertEqual(len(domains), 2)

        teams = organization_db.teams.all()
        self.assertEqual(len(teams), 2)

        enrollments = organization_db.enrollments.all()
        self.assertEqual(len(enrollments), 2)

        aliases = organization_db.aliases.all()
        self.assertEqual(len(aliases), 3)

        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            Organization.objects.get(name='Example')

    def test_non_existing_from_org(self):
        """Check if it fails merging two organizations when `from_org` is `None` or empty"""

        client = graphene.test.Client(schema)

        params = {
            'fromOrg': '',
            'toOrg': 'Bitergia'
        }

        executed = client.execute(self.SH_MERGE_ORGS,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']

        self.assertEqual(msg, FROM_ORG_EMPTY_ERROR)

    def test_non_existing_to_org(self):
        """Check if it fails merging two organizations when `to_org` is `None` or empty"""

        client = graphene.test.Client(schema)

        params = {
            'fromOrg': 'Example',
            'toOrg': ''
        }

        executed = client.execute(self.SH_MERGE_ORGS,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']

        self.assertEqual(msg, TO_ORG_EMPTY_ERROR)

    def test_equal_orgs(self):
        """Check if it fails merging two organizations when `from_org` and `to_org` are equal"""

        client = graphene.test.Client(schema)

        params = {
            'fromOrg': 'Example',
            'toOrg': 'Example'
        }

        executed = client.execute(self.SH_MERGE_ORGS,
                                  context_value=self.context_value,
                                  variables=params)
        msg = executed['errors'][0]['message']

        self.assertEqual(msg, EQUAL_ORGS_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the mutation"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        params = {
            'fromOrg': 'Example',
            'toOrg': 'Bitergia'
        }
        executed = client.execute(self.SH_MERGE_ORGS,
                                  context_value=context_value,
                                  variables=params)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestScheduleTaskMutation(django.test.TestCase):
    """Unit tests for mutation to schedule a task"""

    SH_SCHEDULE_TASK = """
    mutation scheduleTask($job: String,
                          $interval: Int,
                          $params: JSONString) {
      scheduleTask(job: $job, interval: $interval, params: $params) {
        task {
          jobType
          interval
          scheduledDatetime
          args
        }
      }
    }
    """

    def setUp(self):
        """Load initial dataset and set queries context"""

        conn = django_rq.queues.get_redis_connection(None, True)
        conn.flushall()

        self.user = get_user_model().objects.create(username='test', is_superuser=True)
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_schedule_task(self):
        """Check if it schedules a task"""

        client = graphene.test.Client(schema)

        variables = {
            'job': 'unify',
            'interval': 3,
            'params': "{\"criteria\": [\"name\"]}"
        }

        timestamp = datetime_utcnow()

        executed = client.execute(self.SH_SCHEDULE_TASK,
                                  context_value=self.context_value,
                                  variables=variables)

        # Check if the task was created
        task = executed['data']['scheduleTask']['task']
        self.assertEqual(task['jobType'], 'unify')
        self.assertEqual(task['interval'], 3)
        self.assertGreater(str_to_datetime(task['scheduledDatetime']), timestamp)
        self.assertEqual(task['args'], {'criteria': ['name']})

    def test_schedule_task_unsupported_job(self):
        """Check if it returns an error if the job is not supported"""

        client = graphene.test.Client(schema)

        variables = {
            'job': 'foo',
            'interval': 1
        }

        executed = client.execute(self.SH_SCHEDULE_TASK,
                                  context_value=self.context_value,
                                  variables=variables)

        # Check the error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, UNSUPPORTED_JOB_ERROR.format('foo'))

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        variables = {
            'job': 'unify',
            'interval': 3,
            'params': "{\"criteria\": [\"name\"]}"
        }

        executed = client.execute(self.SH_SCHEDULE_TASK,
                                  context_value=context_value,
                                  variables=variables)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestScheduledTasksQuery(django.test.TestCase):
    """Unit tests for scheduled tasks queries"""

    SH_SCHEDULED_TASKS = """
    query scheduledTasks {
      scheduledTasks {
        entities {
          jobType
          args
          interval
        }
        pageInfo {
          page
          totalResults
        }
      }
    }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user
        self.ctx = SortingHatContext(self.user)

    def test_scheduled_tasks(self):
        """Check if it returns the registry of tasks"""

        ScheduledTask.objects.create(job_type='affiliate', interval=10)
        ScheduledTask.objects.create(job_type='unify', interval=20, args={'criteria': ['name']})

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_SCHEDULED_TASKS,
                                  context_value=self.context_value)

        tasks = executed['data']['scheduledTasks']['entities']
        self.assertEqual(len(tasks), 2)

        task = tasks[0]
        self.assertEqual(task['jobType'], 'affiliate')
        self.assertEqual(task['args'], None)
        self.assertEqual(task['interval'], 10)

        task = tasks[1]
        self.assertEqual(task['jobType'], 'unify')
        self.assertEqual(task['args'], {'criteria': ['name']})
        self.assertEqual(task['interval'], 20)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_SCHEDULED_TASKS,
                                  context_value=self.context_value)

        tasks = executed['data']['scheduledTasks']['entities']
        self.assertEqual(tasks, [])

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_SCHEDULED_TASKS,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']

        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestAddAliasMutation(django.test.TestCase):
    """Unit tests for mutation to add aliases"""

    SH_ADD_ALIAS = """
      mutation addAlias {
        addAlias(organization: "Example", alias: "Example Inc.")
        {
          alias {
            alias
            organization {
              name
            }
          }
        }
      }
    """

    SH_ADD_ALIAS_EMPTY = """
      mutation addAlias {
        addAlias(organization: "Example", alias: "")
        {
          alias {
            alias
            organization {
              name
            }
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_add_alias(self):
        """Check if a new alias is added"""

        Organization.add_root(name='Example')

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ALIAS,
                                  context_value=self.context_value)

        # Check result
        alias = executed['data']['addAlias']['alias']
        self.assertEqual(alias['alias'], 'Example Inc.')
        self.assertEqual(alias['organization']['name'], 'Example')

        # Check database
        org = Organization.objects.get(name='Example')
        aliases = org.aliases.all()
        self.assertEqual(len(aliases), 1)

        alias = aliases[0]
        self.assertEqual(alias.alias, 'Example Inc.')

    def test_alias_empty(self):
        """Check whether aliases with empty names cannot be added"""

        Organization.add_root(name='Example')

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ALIAS_EMPTY,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, NAME_EMPTY_ERROR)

        # Check database
        aliases = Alias.objects.all()
        self.assertEqual(len(aliases), 0)

    def test_integrity_error(self):
        """Check whether duplicated aliases cannot be inserted"""

        Organization.add_root(name='Example')

        client = graphene.test.Client(schema)
        client.execute(self.SH_ADD_ALIAS, context_value=self.context_value)

        # Check database
        alias = Alias.objects.get(alias='Example Inc.')
        self.assertEqual(alias.alias, 'Example Inc.')

        # Try to insert it twice
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ALIAS,
                                  context_value=self.context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_ALIAS_ERROR)

    def test_not_found_organization(self):
        """Check if it returns an error when an organization does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ALIAS,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORGANIZATION_EXAMPLE_DOES_NOT_EXIST_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_ADD_ALIAS,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)


class TestDeleteAliasMutation(django.test.TestCase):
    """Unit tests for mutation to delete aliases"""

    SH_DELETE_ALIAS = """
      mutation deleteAlias {
        deleteAlias(alias: "Example Inc.") {
          alias {
            alias
          }
        }
      }
    """

    def setUp(self):
        """Set queries context"""

        self.user = get_user_model().objects.create(username='test')
        self.context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        self.context_value.user = self.user

    def test_delete_alias(self):
        """Check whether it deletes an alias"""

        org = Organization.add_root(name='Example')
        Alias.objects.create(alias='Example Inc.', organization=org)
        Alias.objects.create(alias='Example Ltd.', organization=org)

        # Delete organization
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_ALIAS,
                                  context_value=self.context_value)

        # Check result
        alias = executed['data']['deleteAlias']['alias']
        self.assertEqual(alias['alias'], 'Example Inc.')

        # Tests
        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            Alias.objects.get(alias='Example Inc.')

        aliases = Alias.objects.all()
        self.assertEqual(len(aliases), 1)

    def test_not_found_alias(self):
        """Check if it returns an error when an alias does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_ALIAS,
                                  context_value=self.context_value)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ALIAS_NOT_FOUND_ERROR)

    def test_authentication(self):
        """Check if it fails when a non-authenticated user executes the query"""

        context_value = RequestFactory().get(GRAPHQL_ENDPOINT)
        context_value.user = AnonymousUser()

        client = graphene.test.Client(schema)

        executed = client.execute(self.SH_DELETE_ALIAS,
                                  context_value=context_value)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, AUTHENTICATION_ERROR)
