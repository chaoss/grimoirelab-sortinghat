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
#

import itertools

import django_rq
import django_rq.utils
import rq

from .api import enroll
from .context import SortingHatContext
from .errors import BaseError, NotFoundError
from .log import TransactionsLog
from .models import Individual
from .recommendations.engine import RecommendationEngine


MAX_CHUNK_SIZE = 2000


def find_job(job_id):
    """Find a job in the jobs registry.

    Search for a job using its identifier. When the job is
    not found, a `NotFoundError` exception is raised.

    :param job_id: job identifier

    :returns: a Job instance

    :raises NotFoundError: when the job identified by `job_id`
        is not found.
    """
    queue = django_rq.get_queue()
    jobs = django_rq.utils.get_jobs(queue, [job_id])

    if not jobs:
        raise NotFoundError(entity=job_id)

    return jobs[0]


@django_rq.job
def recommend_affiliations(ctx, uuids=None):
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

    :returns: a dictionary with which individuals are recommended to be
        affiliated to which organization.
    """
    if not uuids:
        uuids = Individual.objects.values_list('mk', flat=True).iterator()
    else:
        uuids = iter(uuids)

    results = {}
    job_result = {
        'results': results
    }

    engine = RecommendationEngine()

    # Create a new context to include the reference
    # to the job id that will perform the transaction.
    job = rq.get_current_job()
    job_ctx = SortingHatContext(ctx.user, job.id)

    # Create an empty transaction to log which job
    # will generate the enroll transactions.
    trxl = TransactionsLog.open('recommend_affiliations', job_ctx)

    for chunk in _iter_split(uuids, size=MAX_CHUNK_SIZE):
        for rec in engine.recommend('affiliation', chunk):
            results[rec.key] = rec.options

    trxl.close()

    return job_result


@django_rq.job
def affiliate(ctx, uuids=None):
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

    :returns: a dictionary with which individuals were enrolled
        and the errors found running the job
    """
    if not uuids:
        uuids = Individual.objects.values_list('mk', flat=True).iterator()
    else:
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
    job = rq.get_current_job()
    job_ctx = SortingHatContext(ctx.user, job.id)

    # Create an empty transaction to log which job
    # will generate the enroll transactions.
    trxl = TransactionsLog.open('affiliate', job_ctx)

    for chunk in _iter_split(uuids, size=MAX_CHUNK_SIZE):
        for rec in engine.recommend('affiliation', chunk):
            affiliated, errs = _affiliate_individual(job_ctx, rec.key, rec.options)
            results[rec.key] = affiliated
            errors.extend(errs)

    trxl.close()

    return job_result


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
    affiliated = []
    errors = []

    for name in organizations:
        try:
            enroll(job_ctx, uuid, name)
        except BaseError as exc:
            errors.append(str(exc))
        else:
            affiliated.append(name)
    return affiliated, errors


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
    while True:
        slice_iter = itertools.islice(iterator, size)
        peek = next(slice_iter)
        yield itertools.chain([peek], slice_iter)
