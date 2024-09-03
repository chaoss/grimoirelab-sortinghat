#!/bin/bash
#
# Copyright (C) 2014-2021 Bitergia
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

#
# Script to run a SortingHat worker as a container.
#
# By default, it takes configuration settings from
# 'sortinghat.config.settings' module.
#

source /opt/venv/bin/activate

set -e

# Default configuration
export SORTINGHAT_CONFIG="${SORTINGHAT_CONFIG:-sortinghat.config.settings}"

# Build the command to run
set - sortinghatw "$@"

# Run the worker
exec "$@"
