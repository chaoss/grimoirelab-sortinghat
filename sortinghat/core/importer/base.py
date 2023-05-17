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

import logging

from datetime import datetime, timedelta, timezone
from django_rq import get_queue

from .. import db, jobs, log
from .backend import find_import_identities_backends
from ..decorators import job_callback_using_tenant
from ..errors import InvalidValueError
from ..models import ImportIdentitiesTask

logger = logging.getLogger(__name__)


def create_import_task(ctx, backend_name, url, interval, params):
    """Create a scheduled Job that import identities to SortingHat.

    This functions generates a task that imports identities using a specific
    backend and a URL with a file or API. Specific backend arguments can be
    specified with 'params' argument.

    The task runs at regular intervals of 'interval' minutes. To prevent it
    from repeating, set 'interval' to 0.

    :param ctx: context from where this method is called
    :param backend_name: name of the importer backend
    :param url: URL of a file or API to fetch the identities from
    :param interval: period of executions, in minutes. None to disable
    :param params: specific arguments for the importer backend

    :returns: ImportIdentitiesTask object

    :raises InvalidValueError: when an argument is not valid
    """

    backends = find_import_identities_backends()
    if backend_name not in backends:
        raise InvalidValueError(msg=f"Backend '{backend_name}' does not exist.")

    if params:
        class_args = backends[backend_name]['args']
        if not all(k in class_args for k in params.keys()):
            raise InvalidValueError(msg=f"Not all arguments in 'params' are available "
                                        f"for {backend_name}")

    trxl = log.TransactionsLog.open('create_import_identities', ctx)

    task = db.add_import_identities_task(trxl=trxl, backend=backend_name, url=url,
                                         args=params, interval=interval)

    schedule_import_task(ctx, task)

    trxl.close()
    return task


def schedule_import_task(ctx, task, scheduled_datetime=None):
    """Schedule a task at a specific time and return the job created"""

    if not scheduled_datetime:
        scheduled_datetime = datetime.now(timezone.utc)

    job = get_queue().enqueue_at(datetime=scheduled_datetime,
                                 f=jobs.import_identities,
                                 ctx=ctx,
                                 backend_name=task.backend,
                                 url=task.url,
                                 params=task.args,
                                 on_success=on_success_job,
                                 on_failure=on_failed_job,
                                 job_timeout=-1)
    task.scheduled_datetime = scheduled_datetime
    task.job_id = job.id
    task.save()

    return job


@job_callback_using_tenant
def on_success_job(job, connection, result, *args, **kwargs):
    """Reschedule the job based on the interval defined by the task

    The new arguments for the job are obtained from ImportIdentitiesTask
    object. This way if the object is updated between runs it will use
    the updated arguments.
    """

    try:
        task = ImportIdentitiesTask.objects.get(job_id=job.id)
    except ImportIdentitiesTask.DoesNotExist:
        logger.error("ImportIdentitiesTask not found. Not rescheduling.")
        return

    task.last_execution = datetime.now(timezone.utc)
    task.executions = task.executions + 1
    task.failed = False

    # Detect if the backend uses 'update_from' argument and update it
    backends = find_import_identities_backends()
    if 'update_from' in backends[task.backend]['args']:
        task.params['update_from'] = task.scheduled_datetime

    if not task.interval:
        logger.info("Interval not defined, not rescheduling task.")
        task.scheduled_datetime = None
        task.job_id = None
    else:
        scheduled_datetime = datetime.now(timezone.utc) + timedelta(minutes=task.interval)
        schedule_import_task(job.kwargs['ctx'], task, scheduled_datetime)

    task.save()


@job_callback_using_tenant
def on_failed_job(job, connection, result, *args, **kwargs):
    """If the job failed to run reschedule it

    The new arguments for the job are obtained from ImportIdentitiesTask
    object. This way if the object is updated between runs it will use
    the updated arguments.
    """

    try:
        task = ImportIdentitiesTask.objects.get(job_id=job.id)
    except ImportIdentitiesTask.DoesNotExist:
        logger.error("ImportIdentitiesTask not found. Not rescheduling.")
        return

    task.last_execution = datetime.now(timezone.utc)
    task.executions = task.executions + 1
    task.failures = task.failures + 1
    task.failed = True

    if not task.interval:
        logger.info("Interval not defined, not rescheduling task.")
        task.scheduled_datetime = None
        task.job_id = None
    else:
        scheduled_datetime = datetime.now(timezone.utc) + timedelta(minutes=task.interval)
        schedule_import_task(job.kwargs['ctx'], task, scheduled_datetime)
        logger.info(f"Reschedule task ID '{task.id}' at '{scheduled_datetime}'.")

    task.save()
