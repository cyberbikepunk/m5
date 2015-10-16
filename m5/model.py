""" This module declares the following SQLALchemy database.

               Clients
                  |
                 ^^
               Orders   Checkpoints
                  |        |
                 ^^       ^^
                   Checkins

"""


from sqlalchemy import Column, ForeignKey, DateTime, String
from sqlalchemy.types import Integer, Float, Boolean, Enum, UnicodeText
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base, synonym_for

from m5.settings import JOB_URL_FORMAT, JOB_FILE_FORMAT, FILE_DATE_FORMAT, URL_DATE_FORMAT


Model = declarative_base()


class Client(Model):
    __tablename__ = 'clients'

    client_id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(UnicodeText)

    @synonym_for('client_id')
    @property
    def id(self):
        return self.client_id

    def __str__(self):
        return 'Client(%s)' % self.name

    __repr__ = __str__


class Order(Model):
    __tablename__ = 'orders'

    order_id = Column(Integer, primary_key=True, autoincrement=False)
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)

    type = Column(Enum('city_tour', 'overnight', 'service'))
    city_tour = Column(Float)
    overnight = Column(Float)
    service = Column(Float)
    extra_stops = Column(Float)
    fax_confirm = Column(Float)
    distance = Column(Float)
    cash = Column(Boolean)
    date = Column(DateTime)
    uuid = Column(Integer)
    user = Column(UnicodeText)

    client = relationship('Client', backref=backref('orders'))

    def __str__(self):

        return 'Order(%s %0.2f€)' % (self.type or 'None', self.price or 0.0)

    __repr__ = __str__

    @property
    def url(self):
        return JOB_URL_FORMAT.format(uuid=self.uuid, date=self.date.strftime(URL_DATE_FORMAT))

    @property
    def file(self):
        return JOB_FILE_FORMAT.format(date=self.date.strftime(FILE_DATE_FORMAT), uuid=self.uuid)

    @synonym_for('order_id')
    @property
    def id(self):
        return self.order_id

    @property
    def price(self):
        total = sum([self.city_tour,
                     self.overnight,
                     self.service,
                     self.fax_confirm,
                     self.extra_stops])
        if total is not None:
            return total


class Checkin(Model):
    __tablename__ = 'checkins'

    checkin_id = Column(UnicodeText, primary_key=True, autoincrement=False)
    checkpoint_id = Column(Integer, ForeignKey('checkpoints.checkpoint_id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.order_id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    purpose = Column(Enum('pickup', 'dropoff', 'stopover'))
    after_ = Column(DateTime)
    until = Column(DateTime)

    checkpoint = relationship('Checkpoint', backref=backref('checkins'))
    order = relationship('Order', backref=backref('checkins'))

    def __str__(self):
        return 'Checkin(%s %s)' % (self.purpose, self.timestamp)

    __repr__ = __str__

    @synonym_for('checkin_id')
    @property
    def id(self):
        return self.checkin_id


class Checkpoint(Model):
    __tablename__ = 'checkpoints'

    checkpoint_id = Column(UnicodeText, primary_key=True, autoincrement=False)
    lat = Column(Float)
    lon = Column(Float)
    city = Column(UnicodeText)
    postal_code = Column(String)
    company = Column(UnicodeText)
    country = Column(UnicodeText)
    place_id = Column(String)
    as_scraped = Column(UnicodeText)
    country_code = Column(String)
    street_name = Column(UnicodeText)
    street_number = Column(String)

    def __str__(self):
        return 'Checkpoint(%s %s)' % (self.street_name, self.street_number)

    __repr__ = __str__

    @synonym_for('checkpoint_id')
    @property
    def id(self):
        return self.checkpoint_id

    @synonym_for('checkpoint_id')
    @property
    def address(self):
        return self.checkpoint_id

    @property
    def geocoded(self):
        if self.lat and self.lon:
            return True
