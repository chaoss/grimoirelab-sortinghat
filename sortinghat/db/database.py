# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Bitergia
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#         Santiago Dueñas <sduenas@bitergia.com>
#

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker

from sortinghat.db.model import ModelBase


class Database(object):

    def __init__(self, user, password, database, host='localhost', port='3306'):
        # Create an engine
        self.url = URL('mysql', user, password, host, port, database,
                       query={'charset' : 'utf8'})
        self._engine = create_engine(self.url, echo=False)
        self._Session = sessionmaker(bind=self._engine)

        # Create the schema on the database.
        # It won't replace any existing schema
        ModelBase.metadata.create_all(self._engine)

    @contextmanager
    def connect(self):
        session = self._Session()

        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def clear(self):
        session = self._Session()

        for table in reversed(ModelBase.metadata.sorted_tables):
            session.execute(table.delete())
            session.commit()
        session.close()
