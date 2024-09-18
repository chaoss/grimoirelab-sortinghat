# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2024 Bitergia
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
import itertools
import logging

import django_rq
import django_rq.utils
import rq
import redis.exceptions
from django.db import IntegrityError, transaction, connection
from rq.job import Job

from .db import find_individual_by_uuid, find_organization
from .api import enroll, merge, update_profile, add_scheduled_task, delete_scheduled_task
from .context import SortingHatContext
from .decorators import job_using_tenant, job_callback_using_tenant
from .errors import (BaseError,
                     NotFoundError,
                     EqualIndividualError,
                     InvalidValueError,
                     JobError)
from .importer.backend import find_import_identities_backends
from .log import TransactionsLog
from .models import (Individual,
                     AffiliationRecommendation,
                     MergeRecommendation,
                     GenderRecommendation,
                     ScheduledTask,
                     MIN_PERIOD_DATE)
from .recommendations.engine import RecommendationEngine


MAX_CHUNK_SIZE = 2000
DEFAULT_JOB_RESULT_TTL = 60 * 60 * 24 * 7  # seconds


logger = logging.getLogger(__name__)


def find_job(job_id, tenant):
    """Find a job in the jobs registry.

    Search for a job using its identifier. When the job is
    not found, a `NotFoundError` exception is raised.

    :param job_id: job identifier
    :param tenant: tenant where the job is running

    :returns: a Job instance

    :raises NotFoundError: when the job identified by `job_id`
        is not found.
    """
    logger.debug(f"Finding job {job_id} ...")

    queue = get_tenant_queue(tenant)
    jobs = django_rq.utils.get_jobs(queue, [job_id])

    if not jobs:
        logger.debug(f"Job with id {job_id} does not exist")
        raise NotFoundError(entity=job_id)

    logger.debug(f"Job with id {job_id} was found")

    return jobs[0]


def get_jobs(tenant):
    """Get a list of all jobs

    This function returns a list of all jobs found in the main queue and its
    registries, sorted by date. If a tenant is specified, filter the jobs for
    that tenant.

    :param tenant: filter the jobs for a specific tenant

    :returns: a list of Job instances
    """
    def job_in_tenant(job, tenant):
        ctx = job.kwargs.get('ctx')
        if not ctx:
            ctx = job.args[0]
        return tenant == ctx.tenant

    logger.debug("Retrieving list of jobs ...")

    queue = get_tenant_queue(tenant)
    started_jobs = django_rq.utils.get_jobs(
        queue,
        queue.started_job_registry.get_job_ids(),
        queue.started_job_registry
    )
    deferred_jobs = django_rq.utils.get_jobs(
        queue,
        queue.deferred_job_registry.get_job_ids(),
        queue.deferred_job_registry
    )
    finished_jobs = django_rq.utils.get_jobs(
        queue,
        queue.finished_job_registry.get_job_ids(),
        queue.finished_job_registry
    )
    failed_jobs = django_rq.utils.get_jobs(
        queue,
        queue.failed_job_registry.get_job_ids(),
        queue.failed_job_registry
    )
    scheduled_jobs = django_rq.utils.get_jobs(
        queue,
        queue.scheduled_job_registry.get_job_ids(),
        queue.scheduled_job_registry
    )
    jobs = (queue.jobs + started_jobs + deferred_jobs + finished_jobs + failed_jobs + scheduled_jobs)
    jobs = (job for job in jobs if job_in_tenant(job, tenant))

    sorted_jobs = sorted(jobs, key=lambda x: x.enqueued_at if x.enqueued_at else datetime.datetime.utcnow(), reverse=True)

    logger.debug(f"List of jobs retrieved; total jobs: {len(sorted_jobs)};")

    return sorted_jobs


class SortingHatJob(Job):
    """Custom RQ Job class for SortingHat jobs.

    This class closes the db connection before finishing
    the job to avoid the 'aborted connection' error in
    the database.

    See also https://github.com/rq/django-rq/issues/17
    """
    def perform(self):
        result = super().perform()
        connection.close()
        return result


@django_rq.job
@job_using_tenant
def recommend_affiliations(ctx, uuids=None, last_modified=MIN_PERIOD_DATE):
    """Generate a list of affiliation recommendations from a set of individuals.

    This function generates a list of recommendations which include the
    organizations where individuals can be affiliated.
    This job returns a dictionary with which individuals are recommended to be
    affiliated to which organization.

    Individuals are defined by any of their valid keys or UUIDs.
    When the parameter `uuids` is empty, the job will take all
    the individuals stored in the registry.

    :param ctx: context where this job is run
    :param uuids: list of individuals identifiers
    :param last_modified: generate recommendations only for individuals modified after
        this date

    :returns: a dictionary with which individuals are recommended to be
        affiliated to which organization.
    """
    job = rq.get_current_job()

    if not uuids:
        logger.info(f"Running job {job.id} 'recommend affiliations'; uuids='all'; ...")
    else:
        logger.info(f"Running job {job.id} 'recommend affiliations'; uuids={uuids}; ...")
        uuids = iter(uuids)

    results = {}
    job_result = {
        'results': results
    }

    engine = RecommendationEngine()

    # Create a new context to include the reference
    # to the job id that will perform the transaction.
    job_ctx = SortingHatContext(ctx.user, job.id, ctx.tenant)

    # Create an empty transaction to log which job
    # will generate the 'enroll' transactions.
    trxl = TransactionsLog.open('recommend_affiliations', job_ctx)

    for rec in engine.recommend('affiliation', uuids, last_modified):
        results[rec.key] = rec.options

        for org_name in rec.options:
            try:
                org = find_organization(org_name)
            except NotFoundError:
                logger.warning(f"Job {job.id} 'Organization {org_name} not found'")
                continue

            try:
                with transaction.atomic():
                    AffiliationRecommendation.objects.create(individual_id=rec.mk,
                                                             organization=org)
            except IntegrityError:
                logger.debug(
                    f"Job {job.id} 'Unable to create affiliation recommendation for"
                    f"Individual {rec.key} and Organization {org_name}"
                )

    trxl.close()

    logger.info(
        f"Job {job.id} 'recommend affiliations' completed; "
        f"{len(results)} recommendations generated"
    )

    return job_result


@django_rq.job
@job_using_tenant
def recommend_matches(ctx, source_uuids,
                      target_uuids, criteria,
                      exclude=True, verbose=False,
                      strict=True, match_source=False,
                      last_modified=MIN_PERIOD_DATE):
    """Generate a list of affiliation recommendations from a set of individuals.

    This function generates a list of recommendations which include the
    matching identities from the individuals which can be merged with.
    This job returns a dictionary with which individuals are recommended to be
    merged to which individual (or which identities is `verbose` mode is activated).

    Individuals both for `source_uuids` and `target_uuids` are defined by any of
    their valid keys or UUIDs. When the parameter `target_uuids` is empty, the
    recommendation engine will take all the individuals stored in the registry,
    so matches will be found comparing the identities from the individuals in
    `source_uuids` against all the identities on the registry. When the parameter
    `sources_uuid` is empty, matches will be found comparing all the identities
    on the registry against `target_uuids`.

    :param ctx: context where this job is run
    :param source_uuids: list of individuals identifiers to look matches for
    :param target_uuids: list of individuals identifiers where to look for matches
    :param criteria: list of fields which the match will be based on
        (`email`, `name` and/or `username`)
    :param exclude: if set to `True`, the results list will ignore individual identities
        if any value from the `email`, `name`, or `username` fields are found in the
        RecommenderExclusionTerm table. Otherwise, results will not ignore them.
    :param verbose: if set to `True`, the match results will be composed by individual
        identities (even belonging to the same individual).
    :param match_source: only unify individuals that share the same source
    :param last_modified: generate recommendations only for individuals modified after
        this date

    :returns: a dictionary with which individuals are recommended to be
        merged to which individual or which identities.
    """
    check_criteria(criteria)

    job = rq.get_current_job()

    results = {}
    job_result = {
        'results': results
    }

    engine = RecommendationEngine()

    # Create a new context to include the reference
    # to the job id that will perform the transaction.
    job_ctx = SortingHatContext(ctx.user, job.id, ctx.tenant)

    trxl = TransactionsLog.open('recommend_matches', job_ctx)

    recommendations = engine.recommend('matches',
                                       source_uuids,
                                       target_uuids,
                                       criteria,
                                       exclude,
                                       verbose,
                                       strict,
                                       match_source,
                                       last_modified)
    for rec in recommendations:
        results[rec.key] = list(rec.options)
        # Store matches in the database
        for match in rec.options:
            if verbose:
                try:
                    match_indiv = find_individual_by_uuid(match)
                    match = match_indiv.mk
                except NotFoundError:
                    logger.info(f"'Individual {match} does not exists'")
                    continue

            indiv_1, indiv_2 = rec.mk, match

            # Generate the recommendations sorting uuids alphabetical
            if indiv_1 == indiv_2:
                continue
            elif indiv_1 > indiv_2:
                indiv_1, indiv_2 = indiv_2, indiv_1

            try:
                with transaction.atomic():
                    MergeRecommendation.objects.create(individual1_id=indiv_1, individual2_id=indiv_2)
            except IntegrityError:
                pass

    trxl.close()

    logger.info(
        f"Job {job.id} 'recommend matches' completed; "
        f"{len(results)} recommendations generated"
    )

    return job_result


@django_rq.job
@job_using_tenant
def recommend_gender(ctx, uuids, exclude=True, no_strict_matching=False):
    """Generate a list of gender recommendations from a set of individuals.

    This job generates a list of recommendations with the
    probable gender of the given individuals.

    :param ctx: context where this job is run
    :param uuids: list of individuals identifiers
    :param exclude: if set to `True`, the results list will ignore individual identities
        if any value from the `email`, `name`, or `username` fields are found in the
        RecommenderExclusionTerm table. Otherwise, results will not ignore them.
    :param no_strict_matching: disable validation for well-formed names

    :returns: a dictionary with the recommended gender and accuracy of the
        prediction for each individual.
    """
    job = rq.get_current_job()

    logger.info(f"Running job {job.id} 'recommend gender'; ...")

    results = {}
    job_result = {
        'results': results
    }

    engine = RecommendationEngine()

    job_ctx = SortingHatContext(ctx.user, job.id, ctx.tenant)

    trxl = TransactionsLog.open('recommend_gender', job_ctx)

    for rec in engine.recommend('gender', uuids, exclude, no_strict_matching):
        gender, accuracy = rec.options[0], rec.options[1]
        results[rec.key] = {'gender': gender,
                            'accuracy': accuracy}
        # Store result in the database
        if not gender or not accuracy:
            continue
        try:
            individual = find_individual_by_uuid(rec.key)
        except NotFoundError:
            logger.warning(f"Job {job.id} 'Individual {rec.key} not found'")
            continue
        genrec, _ = GenderRecommendation.objects.get_or_create(individual=individual,
                                                               defaults={'gender': gender, 'accuracy': accuracy})
        if genrec.gender != gender or genrec.accuracy != accuracy:
            genrec.gender = gender
            genrec.accuracy = accuracy
            genrec.applied = None
            genrec.save()

    trxl.close()

    logger.info(
        f"Job {job.id} 'recommend gender' completed; "
        f"{len(results)} recommendations generated"
    )

    return job_result


@django_rq.job
@job_using_tenant
def affiliate(ctx, uuids=None, last_modified=MIN_PERIOD_DATE):
    """Affiliate a set of individuals using recommendations.

    This function automates the affiliation process obtaining
    a list of recommendations where individuals can be
    affiliated. After that, individuals are enrolled to them.
    This job returns a dictionary with which individuals were
    enrolled and the errors generated during this process.

    Individuals are defined by any of their valid keys or UUIDs.
    When the parameter `uuids` is empty, the job will take all
    the individuals stored in the registry.

    :param ctx: context where this job is run
    :param uuids: list of individuals identifiers
    :param last_modified: only affiliate individuals that have been
        modified after this date

    :returns: a dictionary with which individuals were enrolled
        and the errors found running the job
    """
    job = rq.get_current_job()

    if not uuids:
        logger.info(f"Running job {job.id} 'affiliate'; uuids='all'; ...")
    else:
        logger.info(f"Running job {job.id} 'affiliate'; uuids={uuids}; ...")
        uuids = iter(uuids)

    results = {}
    errors = []
    job_result = {
        'results': results,
        'errors': errors
    }

    engine = RecommendationEngine()

    # Create a new context to include the reference
    # to the job id that will perform the transaction.
    job_ctx = SortingHatContext(ctx.user, job.id, ctx.tenant)

    # Create an empty transaction to log which job
    # will generate the 'enroll' transactions.
    trxl = TransactionsLog.open('affiliate', job_ctx)

    nsuccess = 0

    for rec in engine.recommend('affiliation', uuids, last_modified):
        affiliated, errs = _affiliate_individual(job_ctx, rec.key, rec.options)
        results[rec.key] = affiliated
        errors.extend(errs)

        if affiliated:
            nsuccess += 1

    trxl.close()

    logger.info(
        f"Job {job.id} 'affiliate' completed; "
        f"{nsuccess} individuals have new affiliations"
    )

    return job_result


@django_rq.job
@job_using_tenant
def unify(ctx, criteria, source_uuids=None, target_uuids=None, exclude=True,
          strict=True, match_source=False, last_modified=MIN_PERIOD_DATE):
    """Unify a set of individuals by merging them using matching recommendations.

    This function automates the identities unify process obtaining
    a list of recommendations where matching individuals can be merged.
    After that, matching individuals are merged.
    This job returns a list with the individuals which have been merged
    and the errors generated during this process.

    Individuals both for `source_uuids` and `target_uuids` are defined by
    any of their valid keys or UUIDs. When the parameter `target_uuids` is empty,
    the matches and the later merges will take place comparing the identities
    from the individuals in `source_uuids` against all the identities on the registry.
    When the parameter `sources_uuid` is empty, matches will be found comparing all
    the identities on the registry against `target_uuids`.

    :param ctx: context where this job is run
    :param source_uuids: list of individuals identifiers to look matches for
    :param target_uuids: list of individuals identifiers where to look for matches
    :param criteria: list of fields which the unify will be based on
        (`email`, `name` and/or `username`)
    :param exclude: if set to `True`, the results list will ignore individual identities
        if any value from the `email`, `name`, or `username` fields are found in the
        RecommenderExclusionTerm table. Otherwise, results will not ignore them.
    :param match_source: only unify individuals that share the same source
    :param last_modified: only unify individuals that have been modified after this date

    :returns: a list with the individuals resulting from merge operations
        and the errors found running the job
    """
    def _group_recommendations(recs):
        """Calculate unique sets of identities from matching recommendations.

        For instance, given a dictionary of matching groups like
        {A: [B], B: [A,C], D: [E]} the output will be the groups
        [{A, B, C}, {D, E}].

        :param recs: recommendations of matching identities

        :returns: a list including unique groups of matches
        """
        visited = set()
        result = []

        for key in recs:
            if key in visited:
                continue
            current_set = set()
            stack = [key]

            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                current_set.add(node)
                visited.add(node)
                stack.extend(recs.get(node, []))

            if len(current_set) > 1:
                result.append(current_set)

        return result

    check_criteria(criteria)

    job = rq.get_current_job()

    results = []
    errors = []

    job_result = {
        'results': results,
        'errors': errors
    }

    engine = RecommendationEngine()

    # Create a new context to include the reference
    # to the job id that will perform the transaction.
    job_ctx = SortingHatContext(ctx.user, job.id, ctx.tenant)

    trxl = TransactionsLog.open('unify', job_ctx)

    match_recs = {}
    for rec in engine.recommend('matches',
                                source_uuids,
                                target_uuids,
                                criteria,
                                exclude=exclude,
                                strict=strict,
                                match_source=match_source,
                                last_modified=last_modified):
        match_recs[rec.mk] = list(rec.options)

    match_groups = _group_recommendations(match_recs)

    # Apply the merge of the matching identities
    for group in match_groups:
        group = sorted(group)
        uuid = group[0]
        result = group[1:]
        merged_to, errs = _merge_individuals(job_ctx, uuid, result)
        if merged_to:
            results.append(merged_to)
        errors.extend(errs)

    trxl.close()

    logger.info(
        f"Job {job.id} 'unify' completed; "
        f"{len(results)} individuals have been merged"
    )

    return job_result


@django_rq.job
@job_using_tenant
def genderize(ctx, uuids=None, exclude=True, no_strict_matching=False):
    """Assign a gender to a set of individuals using recommendations.

    This job autocompletes the gender information (stored in
    the profile) of unique identities after obtaining a list
    of recommendations for their gender based on their name.

    Individuals are defined by any of their valid keys or UUIDs.
    When the parameter `uuids` is empty, the job will take all
    the individuals stored in the registry.

    :param ctx: context where this job is run
    :param uuids: list of individuals identifiers
    :param exclude: if set to `True`, the results list will ignore individual identities
        if any value from the `email`, `name`, or `username` fields are found in the
        RecommenderExclusionTerm table. Otherwise, results will not ignore them.
    :param no_strict_matching: disable validation for well-formed names

    :returns: a dictionary with which individual profiles were
        updated and the errors found running the job
    """
    job = rq.get_current_job()

    if not uuids:
        logger.info(f"Running job {job.id} 'genderize'; uuids='all'; ...")
        uuids = Individual.objects.values_list('mk', flat=True).iterator()
    else:
        logger.info(f"Running job {job.id} 'genderize'; uuids={list(uuids)}; ...")
        uuids = iter(uuids)

    results = {}
    errors = []
    job_result = {
        'results': results,
        'errors': errors
    }

    engine = RecommendationEngine()

    # Create a new context to include the reference
    # to the job id that will perform the transaction.
    job_ctx = SortingHatContext(ctx.user, job.id, ctx.tenant)

    # Create an empty transaction to log which job
    # will generate the enroll transactions.
    trxl = TransactionsLog.open('autogender', job_ctx)

    nsuccess = 0

    for chunk in _iter_split(uuids, size=MAX_CHUNK_SIZE):
        for rec in engine.recommend('gender', chunk, exclude, no_strict_matching):
            gender, acc = rec.options
            updated, errs = _update_individual_gender(job_ctx, rec.key, rec.options)
            results[rec.key] = updated
            errors.extend(errs)

            if updated:
                nsuccess += 1

    trxl.close()

    logger.info(
        f"Job {job.id} 'genderize' completed; "
        f"{nsuccess} individuals have been updated"
    )

    return job_result


@django_rq.job
@job_using_tenant
def import_identities(ctx, backend_name, url, **kwargs):
    """Import identities to SortingHat.

    This job imports identities to SortingHat using the
    data obtained from the URL using the specified backend.

    :param ctx: context where this job is run
    :param backend_name: name of the importer backend
    :param url: URL of a file or API to fetch the identities from
    :param kwargs: specific arguments for the importer backend

    :returns: number of identities imported
    """
    job = rq.get_current_job()

    logger.info(f"Running job {job.id} 'import_identities'; "
                f"backend='{backend_name}'; url='{url}'")

    backends = find_import_identities_backends()
    klass = backends[backend_name]['class']

    # Create a new context to include the reference
    # to the job id that will perform the transaction.
    job_ctx = SortingHatContext(ctx.user, job.id, ctx.tenant)
    trxl = TransactionsLog.open('import_identities', job_ctx)

    importer = klass(ctx=job_ctx, url=url, **kwargs)
    nidentities = importer.import_identities()

    trxl.close()

    logger.info(
        f"Job {job.id} 'import_identities' completed; "
        f"{nidentities} identities imported"
    )

    return nidentities


def _merge_individuals(job_ctx, source_indv, target_indvs):
    """Merge a set of individuals.

    Returns a tuple with two elements: list of the uuids from
    the individuals who were merged; list of errors found
    during the process.

    :param job_ctx: job context
    :param source_indv: valid individual identifier where
        the rest of individuals will be merged to
    :param target_indvs: list of identifiers of the individuals
        who will be merged with the source individual

    :returns: tuple with the uuid from the individual resulting from the merge
     operation (if any), and list of errors found during the process
    """
    logger.debug(
        f"Merging individuals; "
        f"job={job_ctx.job_id} source={source_indv} target={target_indvs}; ..."
    )

    errors = []

    try:
        to_indv = merge(job_ctx, target_indvs, source_indv)
    except EqualIndividualError:
        # When source identity is already part of the destination, the merge is not applied
        to_indv = None
        pass
    except BaseError as exc:
        to_indv = None
        errors.append(str(exc))

    to_indv = to_indv.mk if to_indv else None

    logger.debug(
        f"Individuals merging completed with {len(errors)} errors;"
        f"job={job_ctx.job_id} source={source_indv} target={target_indvs}"
    )

    return to_indv, errors


def _affiliate_individual(job_ctx, uuid, organizations):
    """Affiliate an individual to a list of organizations.

    Returns a tuple with two elements: list of the organizations
    the individual was enrolled to; list of the errors found
    during the process.

    :param job_ctx: job context
    :param uuid: valid individual identifier
    :param organizations: list of organization names

    :returns: tuple with the organizations affiliated to the i
    """
    logger.debug(
        f"Affiliating individual; "
        f"job={job_ctx.job_id} uuid={uuid} organizations={organizations}; ..."
    )

    affiliated = []
    errors = []

    for name in organizations:
        try:
            enroll(job_ctx, uuid, name)
        except BaseError as exc:
            errors.append(str(exc))
        else:
            affiliated.append(name)

    logger.debug(
        f"Individual affiliation completed with {len(errors)} errors; "
        f"job={job_ctx.job_id} uuid={uuid} organizations={organizations}; ..."
    )

    return affiliated, errors


def _update_individual_gender(job_ctx, uuid, recommendation):
    errors = []
    gender, gender_acc = recommendation

    logger.debug(
        f"Updating individual profile; "
        f"job={job_ctx.job_id} uuid={uuid} gender={gender} gender_acc={gender_acc}; ..."
    )

    try:
        update_profile(job_ctx, uuid, gender=gender, gender_acc=gender_acc)
    except BaseError as exc:
        errors.append(str(exc))

    logger.debug(
        f"Profile updated with {len(errors)} errors; "
        f"job={job_ctx.job_id} uuid={uuid} gender={gender} gender_acc={gender_acc}; ..."
    )

    return recommendation, errors


def _iter_split(iterator, size=None):
    """Split an iterator in chunks of the same size.

    When size is `None` the iterator will only return
    one chunk.

    :param iterator: iterator to split
    :param size: size of the chunk;

    :returns: generator of chunks
    """
    # This code is based on Ashley Waite's answer to StackOverflow question
    # "split a generator/iterable every n items in python (splitEvery)"
    # (https://stackoverflow.com/a/44320132).
    try:
        while True:
            slice_iter = itertools.islice(iterator, size)
            peek = next(slice_iter)
            yield itertools.chain([peek], slice_iter)
    except StopIteration:
        return


def check_criteria(criteria):
    """ Check if all given criteria are valid.

    Raises an error if a criterion is not in the valid criteria list
    (`email`, `name` and/or `username`).

    :param criteria: list of criteria to check
    """
    valid_criteria = ['name', 'email', 'username']
    if any(criterion not in valid_criteria for criterion in criteria):
        raise ValueError(f"Invalid criteria {criteria}. Valid values are: {valid_criteria}")


def create_scheduled_task(ctx, job, interval, params):
    """Create a task that runs a function at a regular interval.

    This function generates a task that runs the 'job_fn' job at regular
    intervals of 'interval' minutes. To prevent it from repeating, set
    'interval' to 0.

    :param ctx: context from where this method is called
    :param job: job to be run
    :param interval: period of executions, in minutes. None to disable
    :param args: specific arguments for the 'job_fn' function

    :returns: ScheduledTask object

    :raises InvalidValueError: when an argument is not valid
    """
    if job == 'affiliate':
        job_fn = affiliate
    elif job == 'unify':
        job_fn = unify
    elif job == 'import_identities':
        job_fn = import_identities
    else:
        raise InvalidValueError(msg=f"Job '{job}' cannot be scheduled.")

    task = add_scheduled_task(ctx, job, interval, params)

    if not params:
        params = dict()

    try:
        schedule_task(ctx, job_fn, task, **params)
    except redis.exceptions.ConnectionError as e:
        delete_scheduled_task(ctx, task.id)
        raise e

    return task


def schedule_task(ctx, fn, task, scheduled_datetime=None, **kwargs):
    """Schedule a task at a specific time and return the job created"""

    if not scheduled_datetime:
        scheduled_datetime = datetime.datetime.now(datetime.timezone.utc)

    job = get_tenant_queue(ctx.tenant).enqueue_at(datetime=scheduled_datetime,
                                                  f=fn,
                                                  ctx=ctx,
                                                  on_success=on_success_job,
                                                  on_failure=on_failed_job,
                                                  job_timeout=-1,
                                                  result_ttl=DEFAULT_JOB_RESULT_TTL,
                                                  failure_ttl=DEFAULT_JOB_RESULT_TTL,
                                                  **kwargs)
    task.scheduled_datetime = scheduled_datetime
    task.job_id = job.id
    task.save()

    return job


def get_tenant_queue(tenant):
    """Get the job queue used by a tenant.

    When multi-tenancy is active, it's possible to use
    dedicated queues per tenant. This function returns
    what queue is associated to each tenant.

    When the tenant doesn't have a dedicated queue or
    the server doesn't have activated the multi-tenancy
    feature the default queue will be returned.

    :param tenant: name of the tenant

    :returns: RQ queue

    :raises JobError: when there's no queue available for
        the given tenant
    """
    from django.conf import settings

    try:
        if settings.MULTI_TENANT and tenant in settings.TENANTS_DEDICATED_QUEUES:
            return django_rq.get_queue(tenant)
        else:
            return django_rq.get_queue()
    except KeyError:
        raise JobError(msg=f"Queue '{tenant}' not found. Please check your configuration")


@job_callback_using_tenant
def on_success_job(job, connection, result, *args, **kwargs):
    """Reschedule the job based on the interval defined by the task

    The new arguments for the job are obtained from the ScheduledTask
    object. This way if the object is updated between runs it will use
    the updated arguments.
    """
    try:
        task = ScheduledTask.objects.get(job_id=job.id)
    except ScheduledTask.DoesNotExist:
        logger.error("ScheduledTask not found. Not rescheduling.")
        return

    task.last_execution = datetime.datetime.now(datetime.timezone.utc)
    task.executions = task.executions + 1
    task.failed = False

    # Detect if the importer backend uses 'update_from' argument and update it
    if task.job_type == 'import_identities':
        backends = find_import_identities_backends()
        backend_name = task.args['backend_name']
        if 'update_from' in backends[backend_name]['args']:
            task.args['params']['update_from'] = task.scheduled_datetime

    if not task.interval:
        logger.info("Interval not defined, not rescheduling task.")
        task.scheduled_datetime = None
        task.job_id = None
    else:
        scheduled_datetime = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=task.interval)
        ctx = job.kwargs.pop('ctx')
        schedule_task(ctx, job.func, task, scheduled_datetime=scheduled_datetime, **job.kwargs)

    task.save()


@job_callback_using_tenant
def on_failed_job(job, connection, result, *args, **kwargs):
    """If the job failed to run reschedule it

    The new arguments for the job are obtained from the ScheduledTask
    object. This way if the object is updated between runs it will use
    the updated arguments.
    """
    try:
        task = ScheduledTask.objects.get(job_id=job.id)
    except ScheduledTask.DoesNotExist:
        logger.error("ScheduledTask not found. Not rescheduling.")
        return

    task.last_execution = datetime.datetime.now(datetime.timezone.utc)
    task.executions = task.executions + 1
    task.failures = task.failures + 1
    task.failed = True

    if not task.interval:
        logger.info("Interval not defined, not rescheduling task.")
        task.scheduled_datetime = None
        task.job_id = None
    else:
        scheduled_datetime = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=task.interval)
        ctx = job.kwargs.pop('ctx')
        schedule_task(ctx, job.func, task, scheduled_datetime=scheduled_datetime, **job.kwargs)
        logger.info(f"Reschedule task ID '{task.id}' at '{scheduled_datetime}'.")

    task.save()
