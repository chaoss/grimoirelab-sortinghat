# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2018 Bitergia
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

from django.contrib import admin

from .models import (Organization,
                     Team,
                     Domain,
                     Country,
                     Individual,
                     Identity,
                     Profile,
                     Enrollment,
                     AffiliationRecommendation,
                     MergeRecommendation,
                     GenderRecommendation)


admin.site.register(Organization)
admin.site.register(Team)
admin.site.register(Domain)
admin.site.register(Country)
admin.site.register(Individual)
admin.site.register(Identity)
admin.site.register(Profile)
admin.site.register(Enrollment)
admin.site.register(AffiliationRecommendation)
admin.site.register(MergeRecommendation)
admin.site.register(GenderRecommendation)
