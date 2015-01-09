# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Bitergia
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
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from sortinghat.exceptions import DatabaseError
from sortinghat.db.model import ModelBase


class Database(object):

    MYSQL_CREATE_DB = "CREATE DATABASE %(database)s CHARACTER SET utf8 COLLATE utf8_unicode_ci"
    MYSQL_DROP_DB = "DROP DATABASE IF EXISTS %(database)s"


    def __init__(self, user, password, database, host='localhost', port='3306'):
        self._engine = self.build_engine(user, password, database, host, port)
        self._Session = sessionmaker(bind=self._engine)

        try:
            self.__create_schema(self._engine)
        except OperationalError, e:
            raise DatabaseError(error=e.orig[1], code=e.orig[0])

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

    @classmethod
    def create(cls, user, password, database, host='localhost', port='3306'):
        engine = cls.build_engine(user, password, None, host, port)
        query = Database.MYSQL_CREATE_DB % {'database' : database}
        cls.execute(engine, query)

    @classmethod
    def drop(cls, user, password, database, host='localhost', port='3306'):
        engine = cls.build_engine(user, password, None, host, port)
        query = Database.MYSQL_DROP_DB % {'database' : database}
        cls.execute(engine, query)

    @classmethod
    def execute(cls, engine, query):
        try:
            conn = engine.connect()
            conn.execute(query);
        except (OperationalError, ProgrammingError), e:
            raise DatabaseError(error=e.orig[1], code=e.orig[0])

    @classmethod
    def build_engine(cls, user, password, database, host='localhost', port='3306'):
        url = URL('mysql', user, password, host, port, database,
                  query={'charset' : 'utf8'})
        return create_engine(url, poolclass=NullPool, echo=False)

    def __create_schema(self, engine):
        ModelBase.metadata.create_all(engine)
