# -*- coding: utf-8 -*-
#
# Copyright (C) 2023-2024 Bitergia
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
#     Santiago Dueñas <sduenas@bitergia.com>
#

import django_rq

from django.contrib.auth import get_user_model
from django.test import TestCase

from grimoirelab_toolkit.datetime import datetime_utcnow
from sortinghat.core import api, tenant, jobs
from sortinghat.core.context import SortingHatContext
from sortinghat.core.errors import JobError
from sortinghat.core.models import Transaction


class TestTenantJob(TestCase):
    """Unit tests for jobs using tenants"""

    databases = {'default', 'tenant_1', 'tenant_2'}

    def setUp(self):
        """Initialize database with a dataset"""

        self.user = get_user_model().objects.create(username='test')
        ctx = SortingHatContext(user=self.user, tenant='tenant_1')

        tenant.set_db_tenant('tenant_1')
        # Organization and domain
        api.add_organization(ctx, 'Example')
        api.add_domain(ctx, 'Example', 'example.com', is_top_domain=True)

        # Identities
        self.jsmith = api.add_identity(ctx,
                                       source='scm',
                                       email='jsmith@example.com',
                                       name='John Smith',
                                       username='jsmith')
        tenant.unset_db_tenant()

        tenant.set_db_tenant('tenant_2')
        # Jane Roe identity
        self.jroe = api.add_identity(ctx,
                                     source='scm',
                                     email='jroe@example.com',
                                     name='Jane Roe',
                                     username='jroe')
        tenant.unset_db_tenant()

    def test_tenant_recommend_affiliations(self):
        """Check if recommendations are obtained only for one tenant"""

        ctx_1 = SortingHatContext(user=self.user, tenant='tenant_1')
        ctx_2 = SortingHatContext(user=self.user, tenant='tenant_2')

        # Test
        expected_tenant_1 = {
            'results': {
                self.jsmith.pk: ['Example']
            }
        }
        expected_tenant_2 = {
            'results': {
                self.jroe.pk: ['Example']
            }
        }

        job_1 = jobs.recommend_affiliations.delay(ctx_1)
        self.assertDictEqual(job_1.result, expected_tenant_1)
        job_2 = jobs.recommend_affiliations.delay(ctx_2)
        self.assertDictEqual(job_2.result, expected_tenant_2)

    def test_transactions(self):
        """Check if the right transactions were created"""

        timestamp = datetime_utcnow()
        ctx = SortingHatContext(user=self.user, tenant='tenant_1')
        jobs.recommend_affiliations.delay(ctx, job_id='1234-5678-90AB-CDEF')

        transactions = Transaction.objects.using('tenant_1').filter(created_at__gte=timestamp)
        self.assertEqual(len(transactions), 1)
        trx = transactions[0]
        self.assertIsInstance(trx, Transaction)
        self.assertEqual(trx.name, 'recommend_affiliations-1234-5678-90AB-CDEF')
        self.assertGreater(trx.created_at, timestamp)
        self.assertEqual(trx.authored_by, ctx.user.username)
        self.assertEqual(trx.tenant, ctx.tenant)


class TestScheduleJobMultiTenant(TestCase):
    """Unit tests for schedule_job"""

    databases = {'default', 'tenant_1', 'tenant_2'}

    def setUp(self):
        """Initialize database with a dataset"""

        self.user = get_user_model().objects.create(username='test')
        ctx = SortingHatContext(user=self.user, tenant='tenant_1')

        tenant.set_db_tenant('tenant_1')
        # Organization and domain
        api.add_organization(ctx, 'Example')
        api.add_domain(ctx, 'Example', 'example.com', is_top_domain=True)

        # Identities
        self.jsmith = api.add_identity(ctx,
                                       source='scm',
                                       email='jsmith@example.com',
                                       name='John Smith',
                                       username='jsmith')
        tenant.unset_db_tenant()

        tenant.set_db_tenant('tenant_2')
        # Jane Roe identity
        self.jroe = api.add_identity(ctx,
                                     source='scm',
                                     email='jroe@example.com',
                                     name='Jane Roe',
                                     username='jroe')
        tenant.unset_db_tenant()

    def test_schedule_job_dedicated_queue(self):
        """Check if a job is scheduled properly on its dedicated queue"""

        tenant.set_db_tenant('tenant_1')

        ctx = SortingHatContext(user=self.user, tenant='tenant_1')

        task = jobs.create_scheduled_task(ctx, 'affiliate', None, None)

        # The job should be stored on a dedicated queue
        job = jobs.find_job(task.job_id, 'tenant_1')
        queue = django_rq.get_queue('tenant_1')

        job_queue = django_rq.utils.get_jobs(queue, [job.id])[0]

        self.assertEqual(job, job_queue)

        tenant.unset_db_tenant()

    def test_schedule_job_default_queue(self):
        """Check if a job is scheduled properly on the default queue"""

        tenant.set_db_tenant('tenant_2')

        ctx = SortingHatContext(user=self.user, tenant='tenant_2')

        task = jobs.create_scheduled_task(ctx, 'affiliate', None, None)

        # The job should be stored on a dedicated queue
        job = jobs.find_job(task.job_id, 'tenant_2')
        queue = django_rq.get_queue('default')

        job_queue = django_rq.utils.get_jobs(queue, [job.id])[0]

        self.assertEqual(job, job_queue)

        tenant.unset_db_tenant()


class TestGetTenantQueue(TestCase):
    """Unit tests for get_tenant_job"""

    def test_dedicated_tenant_queue(self):
        """Check if the dedicated queue is returned when defined"""

        queue = jobs.get_tenant_queue('tenant_1')
        self.assertEqual(queue.name, 'tenant_1')

    def test_default_tenant_queue(self):
        """Check if the default queue is returned when no dedicated queues are set"""

        queue = jobs.get_tenant_queue('tenant_2')
        self.assertEqual(queue.name, 'default')

    def test_not_found_queue(self):
        """Check it an error is raised when the queue is not found"""

        # The configuration in settings.config_testing_tenant ignores
        # the creation of this queue, so it should raise an error.
        with self.assertRaisesRegex(JobError, "Queue 'error_tenant' not found."):
            jobs.get_tenant_queue('error_tenant')
