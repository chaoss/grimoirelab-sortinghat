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
# Script to run SortingHat service inside of a container.
#
# By default, it takes configuration settings from
# 'sortinghat.config.settings' module.
#
# It also configures the service when it is not initialized
# (i.e. when the database defined in the settings wasn't created yet).
# A superuser will be created during the setup, which requires to pass
# SORTINGHAT_SUPERUSER_USERNAME and SORTINGHAT_SUPERUSER_PASSWORD
# environment variables to configure this super user.
#
# When the flag '--upgrade' is set, it will update the database to its
# last version applying new migrations and fixtures. It will also update
# the UI interface files.
#
# To run the service in developer mode use the flag '--dev'. This will
# start a HTTP server you can access in port 8000. You can also use
# UWSGI_HTTP env var to define where you want to start the service.
#

source /opt/venv/bin/activate

set -e

# Default configuration
export SORTINGHAT_CONFIG=sortinghat.config.settings

sortinghat_check_service() {
    django-admin check --settings=$SORTINGHAT_CONFIG --database default > /dev/null 2>&1
    return $?
}

# Parse flag arguments
while [ $# -gt 0 ]; do
    flag="$1"

    case $flag in
      --upgrade)
          UPGRADE_FLAG=1
          shift
          ;;
      --dev)
          DEV_FLAG=1
          shift
          ;;
    esac
done

# Migrate SortingHat database from 0.7 to 0.8 if needed
sortinghat-admin migrate-old-database --no-interactive

# Setup the service if the database doesn't exist
if ! sortinghat_check_service ; then
    sortinghat-admin setup --no-interactive

    if [ "$?" -ne "0" ]; then
        echo "SortingHat setup failed."
        return 1
    fi
# Upgrade the service on demand
elif [ $UPGRADE_FLAG ]; then
    sortinghat-admin upgrade

    if [ "$?" -ne "0" ]; then
        echo "SortingHat upgrade failed."
        return 1
    fi
fi

# Build the command to run
set - sortinghatd

if [ $DEV_FLAG ]; then
    set -- "$@" --dev
fi

# Run the service
exec "$@"
