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

import datetime

from sqlalchemy import Column, Integer, String, DateTime,\
    ForeignKey, UniqueConstraint
from sqlalchemy.orm import backref, relationship
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base


# Default dates for periods
DEFAULT_START_DATE = datetime.datetime(1900, 1, 1, 0, 0, 0)
DEFAULT_END_DATE = datetime.datetime(2100, 1, 1, 0, 0, 0)


ModelBase = declarative_base()


class Organization(ModelBase):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)

    # One-to-Many relationship
    domains = relationship('Domain', backref='companies',
                           lazy='joined', cascade="save-update, merge, delete")

    # Enrollment relationships
    identities = association_proxy('upeople_companies', 'upeople')

    __table_args__ = (UniqueConstraint('name', name='_name_unique'),
                      {'mysql_charset': 'utf8'})


class Domain(ModelBase):
    __tablename__ = 'domains_companies'

    id = Column(Integer, primary_key=True)
    domain = Column(String(128), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'),
                        nullable=False)

    # Many-to-One relationship
    company = relationship("Organization", backref='domains_companies')

    __table_args__ = (UniqueConstraint('domain', name='_domain_unique'),
                      {'mysql_charset': 'utf8'})


class UniqueIdentity(ModelBase):
    __tablename__ = 'upeople'

    id = Column(Integer, primary_key=True) # UUID
    identifier = Column(String(128), nullable=False)

    # Many-to-many association proxy
    organizations = association_proxy('upeople_companies', 'organizations')

    __table_args__ = ({'mysql_charset': 'utf8'})


class Enrollment(ModelBase):
    __tablename__ = 'upeople_companies'

    id = Column(Integer, primary_key=True)
    init = Column(DateTime, default=DEFAULT_START_DATE, nullable=False)
    end = Column(DateTime, default=DEFAULT_END_DATE, nullable=False)
    upeople_id = Column(Integer, ForeignKey('upeople.id', ondelete='CASCADE'),
                        nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id', ondelete='CASCADE'),
                        nullable=False)

    # Bidirectional attribute/collection of "upeople"/"upeople_companies"
    identity = relationship(UniqueIdentity,
                            backref=backref('upeople_companies',
                                            cascade="all, delete-orphan"))

    # Reference to the "Organization" object
    organization = relationship(Organization,
                                backref=backref('upeople_companies',
                                                cascade="all, delete-orphan"))

    __table_args__ = (UniqueConstraint('upeople_id', 'company_id',
                                       'init', 'end',
                                       name='_period_unique'),
                      {'mysql_charset': 'utf8'})
