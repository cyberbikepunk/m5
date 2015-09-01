"""
This module declares the database and specifies the scraping
instructions. In the following diagram, the hat characters
represent many-to-one relationships.

           Clients  Users
              |      |
              ^      ^
               Orders   Checkpoints
                  |        |
                  ^        ^
                   Checkins

"""


from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy.types import Integer, Float, Boolean, Enum, UnicodeText
from sqlalchemy.orm import relationship, backref, synonym
from sqlalchemy.ext.declarative import declarative_base

from m5.settings import JOB_QUERY_URL, JOB_FILENAME


Model = declarative_base()


##########################
#  Database declaration  #
##########################


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
    country = Column(UnicodeText)

    def __str__(self):
        return 'Checkpoint = ' + self.display_name

    __repr__ = __str__

    @synonym('checkpoint_id')
    def id(self):
        return self.checkpoint_rid


###########################
#  Scraping instructions  #
###########################


BLUEPRINTS = {
    'itinerary': {
        'km': {'line_nb': 0, 'pattern': r'(\d{1,2},\d{3})\s', 'nullable': True}
    },
    'header': {
        'order_id': {'line_nb': 0, 'pattern': r'.*(\d{10})', 'nullable': True},
        'type': {'line_nb': 0, 'pattern': r'.*(OV|Ladehilfe|Stadtkurier)', 'nullable': False},
        'cash': {'line_nb': 0, 'pattern': r'(BAR)', 'nullable': True}
    },
    'client': {
        'client_id': {'line_nb': 0, 'pattern': r'.*(\d{5})$', 'nullable': False},
        'client_name': {'line_nb': 0, 'pattern': r'Kunde:\s(.*)\s\|', 'nullable': False}
    },
    'address': {
        'company': {'line_nb': 1, 'pattern': r'(.*)', 'nullable': False},
        'address': {'line_nb': 2, 'pattern': r'(.*)', 'nullable': False},
        'city': {'line_nb': 3, 'pattern': r'(?:\d{5})\s(.*)', 'nullable': False},
        'postal_code': {'line_nb': 3, 'pattern': r'(\d{5})(?:.*)', 'nullable': False},
        'after': {'line_nb': -3, 'pattern': r'(?:.*)ab\s(\d{2}:\d{2})', 'nullable': True},
        'purpose': {'line_nb': 0, 'pattern': r'(Abholung|Zustellung)', 'nullable': False},
        'timestamp': {'line_nb': -2, 'pattern': r'ST:\s(\d{2}:\d{2})', 'nullable': False},
        'until': {'line_nb': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'nullable': True}
    }
}


TAGS = {
    'header': {'name': 'h2', 'attrs': None},
    'client': {'name': 'h4', 'attrs': None},
    'itinerary': {'name': 'p', 'attrs': None},
    'prices': {'name': 'tbody', 'attrs': None},
    'address': {'name': 'div', 'attrs': {'data-collapsed': 'true'}}
}


OVERNIGHTS = [
    ('Stadtkurier', 'city_tour'),
    ('Stadt Stopp(s)', 'extra_stops'),
    ('OV Ex Nat PU', 'overnight'),
    ('ON Ex Nat Del.', 'overnight'),
    ('OV EcoNat PU', 'overnight'),
    ('OV Ex Int PU', 'overnight'),
    ('ON Int Exp Del', 'overnight'),
    ('EmpfangsbestÃ¤t.', 'fax_confirm'),
    ('Wartezeit min.', 'waiting_time')
]

