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

from django.core.management import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)

SORTINGHAT_PERMISSION_GROUPS = {
    "admin": {
        "admin": {
            "logentry": ["add", "change", "delete", "view"]
        },
        "auth": {
            "group": ["add", "change", "delete", "view"],
            "permission": ["add", "change", "delete", "view"],
            "user": ["add", "change", "delete", "view"]
        },
        "contenttypes": {
            "contenttype": ["add", "change", "delete", "view"]
        },
        "core": {
            "country": ["add", "change", "delete", "view"],
            "domain": ["add", "change", "delete", "view"],
            "enrollment": ["add", "change", "delete", "view"],
            "identity": ["add", "change", "delete", "view"],
            "organization": ["add", "change", "delete", "view"],
            "profile": ["add", "change", "delete", "view"],
            "operation": ["add", "change", "delete", "view"],
            "transaction": ["add", "change", "delete", "view"],
            "individual": ["add", "change", "delete", "view"],
            "team": ["add", "change", "delete", "view"],
            "recommenderexclusionterm": ["add", "change", "delete", "view"],
            "group": ["add", "change", "delete", "view"],
            "custompermissions": ["execute_job"]
        },
        "sessions": {
            "session": ["add", "change", "delete", "view"]
        }
    }
}


class Command(BaseCommand):
    help = "Create groups with the chosen permissions"

    def handle(self, *args, **options):
        for group_name, content_types in SORTINGHAT_PERMISSION_GROUPS.items():
            new_group, created = Group.objects.get_or_create(name=group_name)

            for app_label, models in content_types.items():
                for model, permissions in models.items():
                    try:
                        content_type = ContentType.objects.get(app_label=app_label,
                                                               model=model)
                        for permission_name in permissions:
                            codename = f"{permission_name}_{model}"
                            if model == "custompermissions":
                                codename = permission_name
                            try:
                                permission = Permission.objects.get(codename=codename,
                                                                    content_type=content_type)
                                new_group.permissions.add(permission)
                            except Permission.DoesNotExist:
                                logger.warning(f"Permission {permission_name} not found")
                                continue
                    except ContentType.DoesNotExist:
                        logger.warning(f"ContentType {model} not found in {app_label}")
                        continue
