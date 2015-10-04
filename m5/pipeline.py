""" The pipeline module processes raw data extracted by the scraper and stores it in the database. """


from logging import warning, debug
from datetime import datetime
from time import strptime
from collections import Iterable
from geopy import GoogleV3
from geopy.exc import GeopyError, GeocoderQuotaExceeded
from re import match
from sqlalchemy.orm.exc import FlushError

from m5.model import Checkin, Checkpoint, Client, Order


def boolean(value):
    return True if value else False


def price(raw_subprices):
    subprices = []
    if raw_subprices:
        for raw_subprice in raw_subprices:
            subprices.append(decimal(raw_subprice))
    return sum(subprices)


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
        return {'Abholung': 'pickup',
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


def archive(db, tables_bundle):
    """
    Take table objects from the processor and commit them to the database.
    Rollback if a row already exists or a non nullable value is missing.
    """

    def flatten(tree):
        for node in tree:
            if isinstance(node, Iterable):
                for subnode in flatten(node):
                    yield subnode
            else:
                yield node

    tables = list(flatten(tables_bundle))

    for table in tables:
        db.merge(table)
    try:
        db.commit()
        debug('Soft inserted %s tables', len(tables))
    except FlushError as e:
        db.rollback()
        warning('%s ! Rollback', e)
        raise


def geocode(address):
    # Google is free up to 2500 requests per day, then 0.50€ per 1000. We don't use
    # Nominatim because it doesn't like bulk requests. Other services cost money.
    service = GoogleV3()

    query = '{address}, {city} {postal_code}'.format(**address)

    try:
        point = service.geocode(query)

        if not point:
            raise GeopyError('Google returned empty object')

        if 'partial_match' in point.raw.keys():
            warning('Google approximately matched %s', query)
        else:
            debug('Google matched %s', query)

    except GeocoderQuotaExceeded:
        raise

    except GeopyError as e:
        warning('Error geocoding %s (%s)', address['address'], e)
        point = None

    def get_raw_info(name, default=None, option='long_name'):
        if not point:
            return
        for component in point.raw['address_components']:
            if name in component['types']:
                return component[option]
        else:
            warning('Google did not return %s', name)
            return default

    address['as_scraped'] = query
    address['lat'] = point.point.latitude if point else None
    address['lon'] = point.point.longitude if point else None
    address['address'] = point.address if point else address['address']

    address['place_id'] = get_raw_info('place_id')
    address['country'] = get_raw_info('country')
    address['street_name'] = get_raw_info('route')
    address['street_number'] = get_raw_info('street_number')
    address['country_code'] = get_raw_info('country', option='short_name')
    address['city'] = get_raw_info('locality', default=address['city'])

    return address


def process(job):
    """
    In goes raw data from the scraper module.
    Out comes table data for the SQLAlchemy API.
    """

    assert job is not None, 'Cannot package nothingness'

    client = Client(
        client_id=number(job.data.info['client_id']),
        name=text(job.data.info['client_name'])
    )

    order = Order(
        order_id=number(job.data.info['order_id']),
        client_id=number(job.data.info['client_id']),
        distance=decimal(job.data.info['km']),
        cash=boolean(job.data.info['cash']),
        city_tour=price(job.data.info['city_tour']),
        extra_stops=price(job.data.info['extra_stops']),
        overnight=price(job.data.info['overnight']),
        fax_confirm=price(job.data.info['fax_confirm']),
        service=price(job.data.info['service']),
        type=type_(job.data.info['type']),
        uuid=number(job.stamp.uuid),
        date=job.stamp.date,
        user=job.stamp.user
    )

    checkpoints = []
    checkins = []

    for address in job.data.addresses:
        address = geocode(address)

        checkpoint = Checkpoint(
            checkpoint_id=address['address'],
            place_id=address['place_id'],
            lat=address['lat'],
            lon=address['lon'],
            street_number=number(address['street_number']),
            city=text(address['city']),
            postal_code=text(address['postal_code']),
            company=text(address['company']),
            country=address['country'],
            country_code=address['country_code'],
            as_scraped=address['as_scraped'],
            street_name=address['street_name']
        )

        _timestamp = timestamp(job.stamp.date, address['timestamp'])
        _checkpoint_id = address['address']
        _order_id = number(job.data.info['order_id'])
        _purpose = purpose(address['purpose'])
        _after = timestamp(job.stamp.date, address['after'])
        _until = timestamp(job.stamp.date, address['until'])

        checkin = Checkin(
            timestamp=_timestamp,
            checkpoint_id=_checkpoint_id,
            order_id=_order_id,
            purpose=_purpose,
            after_=_after,
            until=_until,
            # This is a simple hash of the object itself
            checkin_id=' | '.join([
                str(_timestamp),
                _checkpoint_id,
                str(_order_id),
                _purpose,
                str(_after),
                str(_until)
            ]),

        )

        checkpoints.append(checkpoint)
        checkins.append(checkin)

    debug('Processed %s', job.stamp.date)
    return [client], [order], checkpoints, checkins
