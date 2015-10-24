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
from hashlib import md5

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

    type = Column(Enum('city_tour', 'overnight', 'loading_service'))
    city_tour = Column(Float)
    overnight = Column(Float)
    waiting_time = Column(Float)
    extra_stops = Column(Float)
    fax_confirm = Column(Float)
    cancelled_stop = Column(Float)
    loading_service = Column(Float)
    client_support = Column(Float)
    distance = Column(Float)
    cash = Column(Boolean)
    date = Column(DateTime)
    uuid = Column(Integer)
    user = Column(UnicodeText)

    client = relationship('Client', backref=backref('orders'))

    def __str__(self):

        return 'Order(%s %0.2f€)' % (self.type or 'Type?', self.price or 0.0)

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
                     self.loading_service,
                     self.fax_confirm,
                     self.extra_stops,
                     self.cancelled_stop,
                     self.client_support])
        if total is not None:
            return total


class CheckinError(Exception):
    pass


class Checkin(Model):
    __tablename__ = 'checkins'

    def __init__(self, **kwargs):
        super(Checkin, self).__init__(**kwargs)
        self.checkin_id = self.hexdigest

    checkin_id = Column(String, primary_key=True)
    checkpoint_id = Column(Integer, ForeignKey('checkpoints.checkpoint_id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.order_id'), nullable=False)
    purpose = Column(Enum('pickup', 'dropoff', 'stopover'))
    timestamp = Column(DateTime)
    after_ = Column(DateTime)
    until = Column(DateTime)

    checkpoint = relationship('Checkpoint', backref=backref('checkins'))
    order = relationship('Order', backref=backref('checkins'))

    def __str__(self):
        return 'Checkin(%s %s)' % (self.purpose or 'Purpose?', self.timestamp or 'Timestamp?')

    __repr__ = __str__

    @synonym_for('checkin_id')
    @property
    def id(self):
        return self.checkin_id

    # We hash all attributes to bootstrap an ID
    # because no single attribute does the job.
    @property
    def hexdigest(self):
        h = md5()

        try:
            h.update(bytes(self.checkpoint_id, 'utf-8'))
            h.update(bytes(str(self.order_id), 'utf-8'))
            h.update(bytes(self.purpose, 'utf-8'))
            h.update(bytes(str(self.after_), 'utf-8'))
            h.update(bytes(str(self.until), 'utf-8'))
            h.update(bytes(str(self.timestamp), 'utf-8'))
        except TypeError as e:
            raise CheckinError(e)

        return h.hexdigest()


class Checkpoint(Model):
    __tablename__ = 'checkpoints'

    checkpoint_id = Column(UnicodeText, primary_key=True, autoincrement=False)
    lat = Column(Float)
    lon = Column(Float)
    city = Column(UnicodeText)
    postal_code = Column(UnicodeText)
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
    def is_geocoded(self):
        if self.lat and self.lon:
            return True
