# -*- coding: utf-8 -*-
#
# Copyright (C) Bitergia
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
#     Eva Millán <evamillan@bitergia.com>
#

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.core import exceptions
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.db import DEFAULT_DB_ALIAS
from sortinghat.core.models import Tenant


class Command(BaseCommand):
    help = "Assign a user to a permission group"

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('group_name')
        parser.add_argument(
            '--database',
            default=DEFAULT_DB_ALIAS,
            help='Specifies the database to use. Default is "default".',
        )

    def handle(self, *args, **options):
        try:
            group = Group.objects.get(name=options['group_name'])
            user = get_user_model().objects.get(username=options['username'])
        except Group.DoesNotExist:
            raise CommandError(f"Group '{options['group_name']}' not found")
        except exceptions.ObjectDoesNotExist:
            raise CommandError(f"User '{options['username']}' not found")

        if settings.MULTI_TENANT:
            tenant = Tenant.objects.get(user=user, database=options['database'])
            tenant.perm_group = group.name
            tenant.save()
        else:
            user.groups.set([group.id])
