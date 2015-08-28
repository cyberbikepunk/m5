from geopy import Nominatim
from datetime import datetime
from time import strptime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session as LocalSession


from m5.settings import DEBUG, DOWNLOADS, SCRAPING_WARNING_LOG, JOB_URL, BREAK, SUMMARY_URL, OFFLINE
from m5.model import Checkin, Checkpoint, Client, Order


class Packager():
    """ The Packager class processes the raw data produced by the Reader. """

    def __init__(self):
        pass

    def package(self, serial_items: list) -> Tables:
        """ In goes raw data (strings) as returned by the Reader. Out comes
        type-casted data, packaged as Tables objects digestable by the database.
        """

        assert serial_items is not None, 'Cannot package nothingness.'

        clients = list()
        orders = list()
        checkpoints = list()
        checkins = list()

        for serial_item in serial_items:

            day = serial_item[0][0]
            uuid = serial_item[0][1]
            job_details = serial_item[1][0]
            addresses = serial_item[1][1]

            client = Client(**{'client_id': self._unserialise(int, job_details['client_id']),
                               'name': self._unserialise(str, job_details['client_name'])})
            order = Order(**{'order_id': self._unserialise(int, job_details['order_id']),
                             'client_id': self._unserialise(int, job_details['client_id']),
                             'uuid': int(uuid),
                             'date': day,
                             'distance': self._unserialise_float(job_details['km']),
                             'cash': self._unserialise(bool, job_details['cash']),
                             'city_tour': self._unserialise_float(job_details['city_tour']),
                             'extra_stops': self._unserialise_float(job_details['extra_stops']),
                             'overnight': self._unserialise_float(job_details['overnight']),
                             'fax_confirm': self._unserialise_float(job_details['fax_confirm']),
                             'waiting_time': self._unserialise_float(job_details['waiting_time']),
                             'type': self._unserialise_type(job_details['type'])})

            clients.append(client)
            orders.append(order)

            for address in addresses:
                geocoded = self._geocode(address)

                checkpoint = Checkpoint(**{'checkpoint_id': geocoded['osm_id'],
                                           'display_name': geocoded['display_name'],
                                           'lat': geocoded['lat'],
                                           'lon': geocoded['lon'],
                                           'street': self._unserialise(str, address['address']),
                                           'city': self._unserialise(str, address['city']),
                                           'postal_code': self._unserialise(int, address['postal_code']),
                                           'company': self._unserialise(str, address['company'])})
                checkin = Checkin(**{'checkin_id': self._hash_timestamp(day, address['timestamp']),
                                     'checkpoint_id': geocoded['osm_id'],
                                     'order_id': self._unserialise(int, job_details['order_id']),
                                     'timestamp': self._unserialise_timestamp(day, address['timestamp']),
                                     'purpose': self._unserialise_purpose(address['purpose']),
                                     'after_': self._unserialise_timestamp(day, address['after']),
                                     'until': self._unserialise_timestamp(day, address['until'])})

                checkpoints.append(checkpoint)
                checkins.append(checkin)

            print('Packaged {day}-uuid-{uuid}.'.format(day=str(day), uuid=uuid))

        # Does order matters when I commit?
        return Tables(clients, orders, checkpoints, checkins)

    @staticmethod
    def _geocode(raw_address: dict) -> dict:
        """ Geocode an address with Nominatim (http://nominatim.openstreetmap.org).
        The returned osm_id is used as the primary key in the checkpoint table. So,
        if we can't geocode an address, it won't later make it into the database.
        """
    
        g = Nominatim()

        # Geo-coding must not default to Germany
        json_address = {'postalcode': raw_address['postal_code'],
                        'street': raw_address['address'],
                        'city': raw_address['city'],
                        'country': 'Germany'}

        nothing = {'osm_id': None,
                   'lat': None,
                   'lon': None,
                   'display_name': None}

        if not all(json_address.values()):
            if DEBUG:
                print('Nominatim skipped {street} due to missing field(s).'
                      .format(street=raw_address['address']))
            return nothing
        else:
            try:
                response = g.geocode(json_address)
            except:
                # Here we have to catch a ssl socket.timeout error
                # that is not raised as a python exception.
                print('Nominatim returned an error for {street}.'
                      .format(street=raw_address['address']))
                geocoded = nothing
            else:
                if response is None:
                    geocoded = nothing
                    verb = 'failed to match'
                else:
                    geocoded = response.raw
                    verb = 'matched'
                if DEBUG:
                    print('Nominatim {verb} {street}.'
                          .format(verb=verb, street=raw_address['address']))
        return geocoded

    @staticmethod
    def _unserialise(type_cast: type, raw_value: str):
        """ Dynamically type-cast raw strings returned by the
        scraper, with a twist: empty and None return None.
        """

        # The point is that the database will refuse to add a row
        # if a non-nullable column gets the value None. That keeps the
        # database clean. The other variants of this function do the same.
        if raw_value in (None, ''):
            return raw_value
        else:
            return type_cast(raw_value)

    @staticmethod
    def _unserialise_purpose(raw_value: str):
        """ This is a dirty fix """
        if raw_value == 'Abholung':
            return 'pickup'
        elif raw_value == 'Zustellung':
            return 'dropoff'
        else:
            return None

    @staticmethod
    def _unserialise_timestamp(day, raw_time: str):
        """ This is a dirty fix """
        if raw_time in ('', None):
            return None
        else:
            t = strptime(raw_time, '%H:%M')
            return datetime(day.year,
                            day.month,
                            day.day,
                            hour=t.tm_hour,
                            minute=t.tm_min)

    @staticmethod
    def _unserialise_type(raw_value: str):
        """ This is a dirty fix """
        if raw_value == 'OV':
            return 'overnight'
        elif raw_value is 'Ladehilfe':
            return 'help'
        elif raw_value == 'Stadtkurier':
            return 'city_tour'
        else:
            return None

    @staticmethod
    def _hash_timestamp(day, raw_time: str):
        """ This is a dirty fix """
        if raw_time in (None, ''):
            return None
        else:
            t = strptime(raw_time, '%H:%M')
            d = datetime(day.year,
                         day.month,
                         day.day,
                         hour=t.tm_hour,
                         minute=t.tm_min)
            return d.__hash__()

    @staticmethod
    def _unserialise_float(raw_price: str):
        """ This is a dirty fix """
        if raw_price in (None, ''):
            return None
        else:
            return float(raw_price.replace(',', '.'))

class Archiver():
    """ The Archiver class pushes Tables objects data into the local database. """

    def __init__(self, local_session: LocalSession):
        self._local_session = local_session

    def archive(self, tables: Tables):
        """ The archive method takes Table objects produced by the packager and
        commits them into the database. The strategy is primitive: if a row
        already exists, we raise an IntegrityError and rollback the commit.
        """

        for table in tables:
            for row in table:
                try:
                    self._local_session.merge(row)
                    self._local_session.commit()
                except IntegrityError:
                    self._local_session.rollback()
                    print('Database Intergrity ERROR: {table}'.format(table=str(row)))

