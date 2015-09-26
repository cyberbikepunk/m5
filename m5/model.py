""" This module declares the following database:

           Clients  Users
              |      |
             ^^     ^^
               Orders   Checkpoints
                  |        |
                 ^^       ^^
                   Checkins

"""


from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy.types import Integer, Float, Boolean, Enum, UnicodeText
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base, synonym_for

from m5.settings import JOB_QUERY_URL, JOB_FILENAME, FILE_DATE_FORMAT, URL_DATE_FORMAT


Model = declarative_base()


class Client(Model):
    __tablename__ = 'clients'

    client_id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(UnicodeText)

    def __str__(self):
        return 'Client (%s)', self.name

    __repr__ = __str__


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

    client = relationship('Client', backref=backref('orders'))

    def __str__(self):
        return 'Order (%s n°%s for %0.2f€)' % (self.type, self.id, self.price)

    __repr__ = __str__

    @property
    def url(self):
        return JOB_QUERY_URL.format(uuid=self.uuid, date=self.date.strftime(URL_DATE_FORMAT))

    @property
    def file(self):
        return JOB_FILENAME.format(date=self.strftime(FILE_DATE_FORMAT), uuid=self.uuid)

    @synonym_for('order_id')
    @property
    def id(self):
        return self.order_id

    @property
    def price(self):
        return sum([self.city_tour,
                    self.overnight,
                    self.waiting_time,
                    self.fax_confirm,
                    self.extra_stops])


class Checkin(Model):
    __tablename__ = 'checkins'

    checkin_id = Column(Integer, primary_key=True, autoincrement=False)
    checkpoint_id = Column(Integer, ForeignKey('checkpoints.checkpoint_id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.order_id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    purpose = Column(Enum('pickup', 'dropoff'))
    after_ = Column(DateTime)
    until = Column(DateTime)

    checkpoint = relationship('Checkpoint', backref=backref('checkins'))
    order = relationship('Order', backref=backref('checkins'))

    def __str__(self):
        return 'Checkin (%s on %s)' % (self.checkpoint_id, self.timestamp)

    __repr__ = __str__

    @synonym_for('checkin_id')
    @property
    def id(self):
        return self.checkin_id


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
    country = Column(UnicodeText)

    def __str__(self):
        return 'Checkpoint (%s)' % self.display_name

    __repr__ = __str__

    @synonym_for('checkpoint_id')
    @property
    def id(self):
        return self.checkpoint_id
