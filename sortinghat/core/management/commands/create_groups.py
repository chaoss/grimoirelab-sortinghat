# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2022 Bitergia
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

import logging
import json

from django.conf import settings
from django.core.management import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import DEFAULT_DB_ALIAS

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create groups with the chosen permissions"

    def add_arguments(self, parser):
        parser.add_argument(
            '--database',
            default=DEFAULT_DB_ALIAS,
            help='Specifies the database to use. Default is "default".',
        )

    def handle(self, *args, **options):
        with open(settings.PERMISSION_GROUPS_LIST_PATH, 'r') as f:
            groups = json.load(f).get('groups', [])
            for group_name, content_types in groups.items():
                new_group, created = Group.objects.using(options['database']).get_or_create(name=group_name)

                for app_label, models in content_types.items():
                    for model, permissions in models.items():
                        try:
                            content_type = ContentType.objects.using(options['database'])\
                                                              .get(app_label=app_label, model=model)
                            for permission_name in permissions:
                                codename = f"{permission_name}_{model}"
                                if model == "custompermissions":
                                    codename = permission_name
                                try:
                                    permission = Permission.objects.using(options['database'])\
                                                           .get(codename=codename, content_type=content_type)
                                    new_group.permissions.add(permission)
                                except Permission.DoesNotExist:
                                    logger.warning(f"Permission {permission_name} not found")
                                    continue
                        except ContentType.DoesNotExist:
                            logger.warning(f"ContentType {model} not found in {app_label}")
                            continue
