""" The pipeline module processes raw data extracted by the scraper and stores it in the database. """


from logging import warning, debug
from datetime import datetime
from time import strptime
from geopy import GoogleV3
from geopy.exc import GeopyError, GeocoderQuotaExceeded, GeocoderTimedOut
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from m5.model import Checkin, Checkpoint, Client, Order
from m5.settings import GOOGLE_API_KEY


def _boolean(value):
    return True if value else False


def _price(raw_subprices):
    subprices = [0.0]
    if raw_subprices:
        for raw_subprice in raw_subprices:
            subprices.append(_decimal(raw_subprice))
    return sum(subprices)


def _decimal(value):
    if value:
        return float(value.replace(',', '.'))


def _number(value):
    if value:
        return int(value)


def _text(value):
    if value:
        return str(value)


def _purpose(value):
    if value:
        return {'Abholung': 'pickup',
                'Zustellung': 'dropoff',
                'Abh./Zust.': 'stopover'}[value]


def _type(value):
    if value:
        return {'OV': 'overnight',
                'Ladehilfe': 'loading_service',
                'Stadtkurier': 'city_tour',
                'Treibstoff': 'overnight',
                'Kundensupport': 'overnight',
                't:m Stadt': 'city_tour'}[value]


def _timestamp(day, time):
    if day and time:
        t = strptime(time, '%H:%M')
        return datetime(day.year,
                        day.month,
                        day.day,
                        hour=t.tm_hour,
                        minute=t.tm_min)


def archive(db, rows):
    """
    Take table objects from the processor, merge and commit them to the database.
    """

    skipped = 0

    for row in rows:
        state = db.merge(row)
        if not inspect(state).pending:
            debug('Row is already in db: %s', row)
            skipped += 1
        else:
            try:
                db.flush()
            except IntegrityError as e:
                db.rollback()
                warning('Rolled back %s (%s)', row, e)
                skipped += 1

    db.commit()

    debug('Committed rows: skipped %s / inserted %s', skipped, len(rows)-skipped)


def _update_address(address, point):

    def get_field(name, default=None, option='long_name'):
        if not point:
            return

        for component in point.raw['address_components']:
            if name in component['types']:
                return component[option]
        else:
            warning('Google did not return %s', name)
            return default

    address['as_scraped'] = '{address}, {locality}'.format(**address)
    address['lat'] = point.point.latitude if point else None
    address['lon'] = point.point.longitude if point else None
    address['address'] = point.address if point else address['address']
    address['place_id'] = point.raw['place_id'] if point else None

    address['country'] = get_field('country')
    address['street_name'] = get_field('route')
    address['street_number'] = get_field('street_number')
    address['country_code'] = get_field('country', option='short_name')
    address['city'] = get_field('locality')
    address['postal_code'] = get_field('postal_code')

    return address


def geocode(address, attempt=0):
    # Google is free up to 2500 requests per day, then 0.50€ per 1000. We don't use
    # Nominatim because it doesn't like bulk requests. Other services cost money.
    service = GoogleV3(api_key=GOOGLE_API_KEY)

    query = '{address}, {locality}'.format(**address)
    point = None

    if attempt > 2:
        warning('Google timed out 3 times. Giving up on %s', query)

    else:
        try:
            point = service.geocode(query)

            if not point:
                raise GeopyError('Google returned empty object')

            if 'partial_match' in point.raw.keys():
                warning('Google partly matched %s', query)
            else:
                debug('Google matched %s', query)

        except GeocoderQuotaExceeded:
            raise

        except GeocoderTimedOut:
            geocode(address, attempt=attempt+1)

        except GeopyError as e:
            warning('Error geocoding %s (%s)', address['address'], e)

    return point


def process(job, is_offline=False):
    """
    In goes raw data from the scraper module.
    Out come table rows for the SQLAlchemy API.
    """

    assert job is not None, 'Cannot package nothingness'
    rows = []

    client = Client(
        client_id=_number(job.data.info['client_id']),
        name=_text(job.data.info['client_name'])
    )
    rows.append(client)

    order = Order(
        order_id=_number(job.data.info['order_id']),
        client_id=_number(job.data.info['client_id']),
        distance=_decimal(job.data.info['km']),
        cash=_boolean(job.data.info['cash']),
        city_tour=_price(job.data.info['city_tour']),
        extra_stops=_price(job.data.info['extra_stops']),
        overnight=_price(job.data.info['overnight']),
        fax_confirm=_price(job.data.info['fax_confirm']),
        loading_service=_price(job.data.info['loading_service']),
        cancelled_stop=_price(job.data.info['cancelled_stop']),
        waiting_time=_price(job.data.info['waiting_time']),
        client_support=_price(job.data.info['client_support']),
        type=_type(job.data.info['type']),
        uuid=_number(job.stamp.uuid),
        date=job.stamp.date,
        user=job.stamp.user
    )
    rows.append(order)

    for address in job.data.addresses:
        if is_offline:
            point = None
        else:
            point = geocode(address)
        address = _update_address(address, point)

        checkpoint = Checkpoint(
            checkpoint_id=address['address'],
            place_id=address['place_id'],
            lat=address['lat'],
            lon=address['lon'],
            street_number=_text(address['street_number']),
            city=_text(address['city']),
            postal_code=_text(address['postal_code']),
            company=_text(address['company']),
            country=address['country'],
            country_code=address['country_code'],
            as_scraped=address['as_scraped'],
            street_name=address['street_name']
        )
        rows.append(checkpoint)

        checkin = Checkin(
            timestamp=_timestamp(job.stamp.date, address['timestamp']),
            checkpoint_id=address['address'],
            order_id=_number(job.data.info['order_id']),
            purpose=_purpose(address['purpose']),
            after_=_timestamp(job.stamp.date, address['after']),
            until=_timestamp(job.stamp.date, address['until']),
        )
        rows.append(checkin)

    debug('Processed %s uuid=%s', job.stamp.date, job.stamp.uuid)
    return rows
