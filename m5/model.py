""" This module defines our local database model. """


from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy.types import Integer, Float, Boolean, Enum, UnicodeText
from sqlalchemy.orm import relationship, backref, synonym
from sqlalchemy.ext.declarative import declarative_base

from m5.settings import JOB_QUERY_URL, JOB_FILENAME


Model = declarative_base()


# ============================
#       Database model
# ============================
#
#   Clients  Users
#      |      |
#      ^      ^
#       Orders   Checkpoints
#          |        |
#          ^        ^
#           Checkins
#
# ============================


class Client(Model):
    __tablename__ = 'clients'

    client_id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(UnicodeText)

    def __str__(self):
        return 'Client = ' + self.name

    __repr__ = __str__


class User(Model):
    __tablename__ = 'users'

    user_id = Column(UnicodeText, primary_key=True, autoincrement=False)

    def __str__(self):
        return 'User = ' + self.user_id

    __repr__ = __str__

    @synonym('user_id')
    def name(self):
        return self.user_id


class Order(Model):
    __tablename__ = 'orders'

    order_id = Column(Integer, primary_key=True, autoincrement=False)
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)

    type = Column(Enum('city_tour', 'overnight', 'service'))
    city_tour = Column(Float)
    overnight = Column(Float)
    waiting_time = Column(Float)
    extra_stops = Column(Float)
    fax_confirm = Column(Float)
    distance = Column(Float)
    cash = Column(Boolean)
    date = Column(DateTime)
    uuid = Column(Integer)

    clients = relationship('Client', backref=backref('orders'))
    users = relationship('User', backref=backref('users'))

    def __str__(self):
        return 'Order = ' + self.order_id

    __repr__ = __str__

    @synonym('order_id')
    def id(self):
        return self.order_rid

    @synonym
    def url(self):
        return JOB_QUERY_URL.format(uuid=self.uuid, date=self.date.strftime('%d.%m.%Y'))

    @synonym
    def file(self):
        return JOB_FILENAME.format(date=self.strftime('%d-%m.-%Y'), uuid=self.uuid)


class Checkin(Model):
    __tablename__ = 'checkins'

    checkin_id = Column(Integer, primary_key=True, autoincrement=False)
    checkpoint_id = Column(Integer, ForeignKey('checkpoints.checkpoint_id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.order_id'), nullable=False)
    user_id = Column(UnicodeText, ForeignKey('users.user_id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    purpose = Column(Enum('pickup', 'dropoff'))
    after_ = Column(DateTime)
    until = Column(DateTime)

    checkpoints = relationship('Checkpoint', backref=backref('checkins'))
    orders = relationship('Order', backref=backref('checkins'))

    def __str__(self):
        return 'Checkin = ' + str(self.timestamp)

    __repr__ = __str__

    @synonym('checkin_id')
    def id(self):
        return self.checkin_rid


class Checkpoint(Model):
    __tablename__ = 'checkpoints'

    checkpoint_id = Column(Integer, primary_key=True, autoincrement=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    city = Column(UnicodeText)
    display_name = Column(UnicodeText)
    postal_code = Column(Integer)
    street = Column(UnicodeText)
    company = Column(UnicodeText)

    def __str__(self):
        return 'Checkpoint = ' + self.display_name

    __repr__ = __str__

    @synonym('checkpoint_id')
    def id(self):
        return self.checkpoint_rid
