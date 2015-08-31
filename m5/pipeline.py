""" The pipeline module processes raw data from the scraper and stores it inside the database. """


from collections import namedtuple
from logging import warning, debug
from geopy import Nominatim
from datetime import datetime
from time import strptime
from sqlalchemy.exc import IntegrityError

from m5.model import Checkin, Checkpoint, Client, Order


Tables = namedtuple('Tables', ['users',
                               'clients',
                               'orders',
                               'checkins',
                               'checkpoints'])


def boolean(value):
    if value:
        return bool(value)


def decimal(value):
    if value:
        return float(value.replace(',', '.'))


def number(value):
    if value:
        return int(value)


def text(value):
    if value:
        return str(value)


def purpose(value):
    if value:
        return {'Abholung': 'purpose',
                'Zustellung': 'dropoff'}[value]


def type_(value):
    if value:
        return {'OV': 'overnight',
                'Ladehilfe': 'service',
                'Stadtkurier': 'city_tour'}[value]


def timestamp(day, time):
    if day and time:
        t = strptime(time, '%H:%M')
        return datetime(day.year,
                        day.month,
                        day.day,
                        hour=t.tm_hour,
                        minute=t.tm_min)


def archive(tables, session):
    """
    Take table objects from the packager and commit them to the database.
    Rollback if a row already exists or a non nullable value is missing.
    """

    for table in tables:
        for row in table:
            session.merge(row)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                warning('Skipped %s', row)


def package(jobs):
    """
    In goes raw data from the scraper module.
    Out comes tabular data for the database.
    """

    assert jobs is not None, 'Cannot package nothingness'

    clients = []
    orders = []
    checkpoints = []
    checkins = []

    for job in jobs:

        client = Client(
            client_id=number(job.info['client_id']),
            name=text(job.info['client_name'])
        )

        order = Order(
            order_id=number(job.info['order_id']),
            client_id=number(job.info['client_id']),
            distance=decimal(job.info['km']),
            cash=boolean(job.info['cash']),
            city_tour=decimal(job.info['city_tour']),
            extra_stops=decimal(job.info['extra_stops']),
            overnight=decimal(job.info['overnight']),
            fax_confirm=decimal(job.info['fax_confirm']),
            waiting_time=decimal(job.info['waiting_time']),
            type=type_(job.info['type']),
            uuid=number(job.stamp.uuid),
            date=job.stamp.date,
            user=job.stamp.user
        )

        clients.append(client)
        orders.append(order)

        for address in job.addresses:
            geocoded = geocode(address)

            checkpoint = Checkpoint(
                checkpoint_id=geocoded['osm_id'],
                display_name=geocoded['display_name'],
                lat=geocoded['lat'],
                lon=geocoded['lon'],
                street=text(address['address']),
                city=text(address['city']),
                postal_code=number(address['postal_code']),
                company=text(address['company'])
            )

            checkin = Checkin(
                checkin_id=timestamp(job.stamp.day, address['timestamp']),
                checkpoint_id=geocoded['osm_id'],
                order_id=number(job.info['order_id']),
                purpose=purpose(address['purpose']),
                after_=timestamp(job.stamp.date, address['after']),
                until=timestamp(job.stamp.day, address['until'])
            )

            checkpoints.append(checkpoint)
            checkins.append(checkin)

        debug('Packaged %s', job.stamp.day)

    return Tables(clients, orders, checkpoints, checkins)


def geocode(address):
    """
    Geocode an address with Nominatim (http://nominatim.openstreetmap.org).
    The osm_id returned by OpenStreetMap is used as the primary key for the
    checkpoint table. If the service fails to geocode an address, it won't
    make it into the database.
    """

    g = Nominatim()

    payload = {'postalcode': address['postal_code'],
               'street': address['address'],
               'city': address['city'],
               'country': address['country']}

    empty = {key: None for key in ('osm_id',
                                   'lat',
                                   'lon',
                                   'display_name')}

    for key, value in payload.items():
        if not value:
            warning('Cannot geocode %s without %s', address['address'], key)
            return empty

    # noinspection PyBroadException
    # We have to catch a socket timeout.
    try:
        response = g.geocode(payload)
    except:
        warning('Nominatim could not geocode %s', address['address'])
        return empty

    if response is None:
        geocoded = empty
        warning('Nominatim failed to match %s', address['address'])
    else:
        geocoded = response.raw
        debug('Nominatim matched %s', address['address'])

    return geocoded
