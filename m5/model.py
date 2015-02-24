""" This module defines our local database model. """

from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy.types import Integer, Float, String, Boolean, Enum
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base, synonym_for

Base = declarative_base()

#       Clients
#           ^
#           |
#       Orders   Checkpoints
#           ^      ^
#           |      |
#           Check-ins
#
#              One
#               ^
#               |
#            Many to
#    (foreign key + back-ref)


class Client(Base):
    __tablename__ = 'client'

    client_id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String)

    @synonym_for('client_id')
    @property
    def id(self):
        return self.client_id

    def __str__(self):
        """ Return something easy to read. """
        strings = list()
        keys = [k for k in self.__dict__.keys() if k[0] is not '_']
        for key in keys:
            strings.append('{key}={value}'.format(key=key, value=self.__dict__[key]))
        return '<' + self.__class__.__name__ + ' (' + ', '.join(strings) + ')>'

    def __repr__(self):
        """ Return something easy to read. """
        return self.__str__()


class Order(Base):
    __tablename__ = 'order'

    order_id = Column(Integer, primary_key=True, autoincrement=False)
    client_id = Column(Integer, ForeignKey('client.client_id'), nullable=False)
    type = Column(Enum('city_tour', 'overnight', 'help'))
    city_tour = Column(Float, default=0)
    overnight = Column(Float, default=0)
    waiting_time = Column(Float, default=0)
    extra_stops = Column(Float, default=0)
    fax_confirm = Column(Float, default=0)
    distance = Column(Float, default=0)
    cash = Column(Boolean)
    date = Column(DateTime)
    uuid = Column(Integer)

    client = relationship('Client', backref=backref('order'))

    @synonym_for('order_id')
    @property
    def id(self):
        return self.order_id

    def __str__(self):
        """ Return something easy to read. """
        strings = list()
        keys = [k for k in self.__dict__.keys() if k[0] is not '_']
        for key in keys:
            strings.append('{key}={value}'.format(key=key, value=self.__dict__[key]))
        return '<' + self.__class__.__name__ + ' (' + ', '.join(strings) + ')>'

    def __repr__(self):
        """ Return something easy to read. """
        return self.__str__()


class Checkin(Base):
    __tablename__ = 'checkin'

    checkin_id = Column(Integer, primary_key=True, autoincrement=False)
    checkpoint_id = Column(Integer, ForeignKey('checkpoint.checkpoint_id'), nullable=False)
    order_id = Column(Integer, ForeignKey('order.order_id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    purpose = Column(Enum('pickup', 'dropoff'))
    after_ = Column(DateTime)
    until = Column(DateTime)

    checkpoint = relationship('Checkpoint', backref=backref('checkin'))
    order = relationship('Order', backref=backref('checkin'))

    @synonym_for('checkin_id')
    @property
    def id(self):
        return self.checkin_id

    def __str__(self):
        """ Return something easy to read. """
        strings = list()
        keys = [k for k in self.__dict__.keys() if k[0] is not '_']
        for key in keys:
            strings.append('{key}={value}'.format(key=key, value=self.__dict__[key]))
        return '<' + self.__class__.__name__ + ' (' + ', '.join(strings) + ')>'

    def __repr__(self):
        """ Return something easy to read. """
        return self.__str__()


class Checkpoint(Base):
    __tablename__ = 'checkpoint'

    checkpoint_id = Column(String, primary_key=True, autoincrement=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    city = Column(String, default='Berlin')
    display_name = Column(String)
    postal_code = Column(Integer)
    street = Column(String)
    company = Column(String)

    @synonym_for('checkpoint_id')
    @property
    def id(self):
        return self.checkpoint_id

    def __str__(self):
        """ Return something easy to read. """
        strings = list()
        keys = [k for k in self.__dict__.keys() if k[0] is not '_']
        for key in keys:
            strings.append('{key}={value}'.format(key=key, value=self.__dict__[key]))
        return '<' + self.__class__.__name__ + ' (' + ', '.join(strings) + ')>'

    def __repr__(self):
        """ Return something easy to read. """
        return self.__str__()