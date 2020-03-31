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

import click


from .cmds.add import add
from .cmds.enroll import enroll
from .cmds.merge import merge
from .cmds.mv import mv
from .cmds.orgs import orgs
from .cmds.profile import profile
from .cmds.rm import rm
from .cmds.withdraw import withdraw


@click.group()
def sortinghat():
    """A tool to manage identities."""

    pass


sortinghat.add_command(add)
sortinghat.add_command(rm)
sortinghat.add_command(profile)
sortinghat.add_command(mv)
sortinghat.add_command(enroll)
sortinghat.add_command(withdraw)
sortinghat.add_command(merge)
sortinghat.add_command(orgs)
