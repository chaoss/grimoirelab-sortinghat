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

from .. import jobs
from .backend import find_import_identities_backends
from ..decorators import job_callback_using_tenant
from ..models import ScheduledTask

logger = logging.getLogger(__name__)


@job_callback_using_tenant
def on_success_job(job, connection, result, *args, **kwargs):
    """Reschedule the job based on the interval defined by the task

    The new arguments for the job are obtained from ImportIdentitiesTask
    object. This way if the object is updated between runs it will use
    the updated arguments.

    This method is deprecated.
    """

    try:
        task = ScheduledTask.objects.get(job_id=job.id)
    except ScheduledTask.DoesNotExist:
        logger.error("ScheduledTask not found. Not rescheduling.")
        return

    task.last_execution = datetime.now(timezone.utc)
    task.executions = task.executions + 1
    task.failed = False

    # Detect if the backend uses 'update_from' argument and update it
    backends = find_import_identities_backends()
    backend_name = task.args['backend_name']
    if 'update_from' in backends[backend_name]['args']:
        task.args['params']['update_from'] = task.scheduled_datetime

    if not task.interval:
        logger.info("Interval not defined, not rescheduling task.")
        task.scheduled_datetime = None
        task.job_id = None
    else:
        scheduled_datetime = datetime.now(timezone.utc) + timedelta(minutes=task.interval)
        ctx = job.kwargs.pop('ctx')
        jobs.schedule_task(ctx, jobs.import_identities, task, scheduled_datetime=scheduled_datetime, **job.kwargs)

    task.save()


@job_callback_using_tenant
def on_failed_job(job, connection, result, *args, **kwargs):
    """If the job failed to run reschedule it

    The new arguments for the job are obtained from ImportIdentitiesTask
    object. This way if the object is updated between runs it will use
    the updated arguments.

    This method is deprecated.
    """

    try:
        task = ScheduledTask.objects.get(job_id=job.id)
    except ScheduledTask.DoesNotExist:
        logger.error("ScheduledTask not found. Not rescheduling.")
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
        ctx = job.kwargs.pop('ctx')
        jobs.schedule_task(ctx, jobs.import_identities, task, scheduled_datetime=scheduled_datetime, **job.kwargs)
        logger.info(f"Reschedule task ID '{task.id}' at '{scheduled_datetime}'.")

    task.save()
