""" The factory module migrates remote data to the local database. """


from contextlib import redirect_stdout
from os import path
from os.path import isfile
from geopy import Nominatim
from datetime import datetime, date, timedelta
from time import strptime
from requests import Session as RemoteSession
from bs4 import BeautifulSoup
from pprint import pprint
from re import findall, match
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.session import Session as LocalSession
from collections import namedtuple

from settings import DEBUG, DOWNLOADS, ELUCIDATE, JOB, BREAK, SUMMARY, OFFLINE
from model import Checkin, Checkpoint, Client, Order
from user import User


Stamped = namedtuple('Stamped', ['stamp', 'data'])
Stamp = namedtuple('Stamp', ['date', 'uuid'])
Tables = namedtuple('Tables', ['clients', 'orders', 'checkpoints', 'checkins'])


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


class Downloader():
    """ The Downloader class fetches html files from the remote server. """

    def __init__(self, remote_session: RemoteSession, overwrite: bool=None):
        assert OFFLINE is False, 'Turn the OFFLINE flag off (in the settings module).'
        self._overwrite = overwrite
        self._remote_session = remote_session
        self._stamp = None

    def bulk_download(self, start_date: date):
        delta = date.today() - start_date
        for d in range(delta.days):
            self.download(start_date + timedelta(days=d))

    def download(self, day: date) -> list:
        """ Download the web-page for each job on that day. Save it and and return a
        list of beautiful soup objects. Serve from cache whenever it's possible.
        """

        assert isinstance(day, date), 'Argument must be a date object'
        assert day <= date.today(), 'Cannot return to the future.'

        # Resets all object properties
        self._stamp = Stamp(day, 'NO_JOBS')

        if self._is_hopeless:
            return None

        uuids = self._scrape_uuids(day)
        soups = list()

        if not uuids:
            soups = None
            if DEBUG:
                print('No jobs to download on {day}.'.format(day=str(day)))
        else:
            for i, uuid in enumerate(uuids):
                self._stamp = Stamp(day, uuid)

                if self._is_cached and not self._overwrite:
                    soup = self._load_job()
                    verb = 'Loaded'
                else:
                    soup = self._get_job()
                    self._save_job(soup)
                    verb = 'Downloaded'

                if DEBUG:
                    print('{verb} {n}/{N}. {url}'.
                          format(verb=verb, n=i+1, N=len(uuids), url=self._job_url))

                soups.append(Stamped(self._stamp, soup))

        return soups

    def _scrape_uuids(self, day: date) -> set:
        """ Return uuid request parameters for each job by scraping the summary page. """

        url = SUMMARY
        payload = {'status': 'delivered', 'datum': day.strftime('%d.%m.%Y')}
        response = self._remote_session.get(url, params=payload)

        # The so called 'uuids' are actually 7 digit numbers.
        pattern = 'uuid=(\d{7})'
        jobs = findall(pattern, response.text)
        return set(jobs)

    def _get_job(self) -> BeautifulSoup:
        """ Fetch the web-page for that day and return a beautiful soup. """

        url = JOB
        payload = {'status': 'delivered',
                   'uuid': self._stamp.uuid,
                   'datum': self._stamp.date.strftime('%d.%m.%Y')}

        response = self._remote_session.get(url, params=payload)
        return BeautifulSoup(response.text)

    @property
    def _is_hopeless(self):
        """ True if we already know that the day contains no jobs. """
        # We've put an empty file stamped 'NO_JOBS' inside the downloads directory.
        return self._is_cached

    @property
    def _filepath(self) -> str:
        """ Where a job's html file is saved. """
        filename = '%s-uuid-%s.html' % (self._stamp.date.strftime('%Y-%m-%d'), self._stamp.uuid)
        return path.join(DOWNLOADS, filename)

    @property
    def _job_url(self) -> bool:
        """ Return the job url for a given day and uuid. """
        return 'http://bamboo-mec.de/ll_detail.php5?status=delivered&uuid={uuid}&datum={date}'\
            .format(uuid=self._stamp.uuid, date=self._stamp.date.strftime('%d.%m.%Y'))

    @property
    def _is_cached(self) -> bool:
        """ True if the html file is found locally. """
        return True if isfile(self._filepath) else False

    def _save_job(self, soup):
        """ Prettify the soup and save it to file. """
        with open(self._filepath, 'w+') as f:
            f.write(soup.prettify())

    def _load_job(self) -> BeautifulSoup:
        """ Load an html file and return a beautiful soup. """
        with open(self._filepath, 'r') as f:
            html = f.read()
        return BeautifulSoup(html)


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


class Reader:
    """ Basically, the Reader class extracts data fields from html files. """
    # If would be better if the blueprints were defined within the orm model.

    _OVERNIGHTS = [('Stadtkurier', 'city_tour'),
                   ('Stadt Stopp(s)', 'extra_stops'),
                   ('OV Ex Nat PU', 'overnight'),
                   ('ON Ex Nat Del.', 'overnight'),
                   ('OV EcoNat PU', 'overnight'),
                   ('OV Ex Int PU', 'overnight'),
                   ('ON Int Exp Del', 'overnight'),
                   ('EmpfangsbestÃ¤t.', 'fax_confirm'),
                   ('Wartezeit min.', 'waiting_time')]

    _TAGS = {'header': {'name': 'h2', 'attrs': None}, 'client': {'name': 'h4', 'attrs': None},
             'itinerary': {'name': 'p', 'attrs': None}, 'prices': {'name': 'tbody', 'attrs': None},
             'address': {'name': 'div', 'attrs': {'data-collapsed': 'true'}}}

    _BLUEPRINTS = {'itinerary': {'km': {'line_nb': 0, 'pattern': r'(\d{1,2},\d{3})\s', 'nullable': True}},
                   'header': {'order_id': {'line_nb': 0, 'pattern': r'.*(\d{10})', 'nullable': True},
                              'type': {'line_nb': 0, 'pattern': r'.*(OV|Ladehilfe|Stadtkurier)', 'nullable': False},
                              'cash': {'line_nb': 0, 'pattern': r'(BAR)', 'nullable': True}},
                   'client': {'client_id': {'line_nb': 0, 'pattern': r'.*(\d{5})$', 'nullable': False},
                              'client_name': {'line_nb': 0, 'pattern': r'Kunde:\s(.*)\s\|', 'nullable': False}},
                   'address': {'company': {'line_nb': 1, 'pattern': r'(.*)', 'nullable': False},
                               'address': {'line_nb': 2, 'pattern': r'(.*)', 'nullable': False},
                               'city': {'line_nb': 3, 'pattern': r'(?:\d{5})\s(.*)', 'nullable': False},
                               'postal_code': {'line_nb': 3, 'pattern': r'(\d{5})(?:.*)', 'nullable': False},
                               'after': {'line_nb': -3, 'pattern': r'(?:.*)ab\s(\d{2}:\d{2})', 'nullable': True},
                               'purpose': {'line_nb': 0, 'pattern': r'(Abholung|Zustellung)', 'nullable': False},
                               'timestamp': {'line_nb': -2, 'pattern': r'ST:\s(\d{2}:\d{2})', 'nullable': False},
                               'until': {'line_nb': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'nullable': True}}}

    def __init__(self):
        self._stamp = None

    def scrape(self, soups: list) -> list:
        """ In goes a list of BeautifulSoup objects (typically all the jobs for one
        day), out comes a list of tuples. Each tuple has two variables: a dictionary
        holding the job details and a list of dictionaries, each holding one address.
        At this stage, all the fields are stored as strings.
        """

        assert soups is not None, 'Argument cannot be None.'
        jobs = list()

        for i, soup in enumerate(soups):
            # Reset object properties.
            self._stamp = soup.stamp

            job, addresses = self._scrape_job(soup)
            fields = Stamped(soup.stamp, (job, addresses))
            jobs.append(fields)
            print(self._job_done)

            if DEBUG:
                print('hello')
                print('Scraped {n}/{N}: {date}-uuid-{uuid}.html'
                      .format(date=str(soup.stamp.date),
                              uuid=soup.stamp.uuid,
                              N=len(soups),
                              n=i+1))
                pprint(job)
                pprint(addresses)

        return jobs

    @property
    def _job_done(self):
        """ Print the url of the job. """
        return 'Scraped http://bamboo-mec.de/ll_detail.php5?status=delivered&uuid={uuid}&datum={date}'\
            .format(uuid=self._stamp.uuid, date=self._stamp.date.strftime('%d.%m.%Y'))

    def _scrape_job(self, soup: Stamped) -> tuple:
        """ Fragment a web page (one job) and scrape it using bs4 and re modules.
        The method takes a BeautifulSoup object and returns job details and addresses
        in the form of dictionaries of field name/value pairs (values are strings).
        """

        assert soup is not None, 'Cannot scrape nothingness'

        order = soup.data.find(id='order_detail')
        job = dict()
        addresses = list()

        # Step 1.1: in all fragments except prices
        sections = ['header', 'client', 'itinerary']
        for section in sections:
            fragment = order.find_next(name=self._TAGS[section]['name'])
            fields = self._scrape_fragment(self._BLUEPRINTS[section],
                                           fragment,
                                           soup.stamp,
                                           section)
            job.update(fields)

        # Step 1.2: in the price table. There's no reason
        # why this fragment should be treated separately.
        fragment = order.find(self._TAGS['prices']['name'])
        prices = self._scrape_prices(fragment)
        job.update(prices)

        # Step 2: scrape an arbitrary number of addresses
        fragments = order.find_all(name=self._TAGS['address']['name'], attrs=self._TAGS['address']['attrs'])
        for fragment in fragments:
            address = self._scrape_fragment(self._BLUEPRINTS['address'],
                                            fragment,
                                            soup.stamp,
                                            'address')
            addresses.append(address)

        return job, addresses

    def _scrape_fragment(self, blueprints: dict, soup_fragment: BeautifulSoup, stamp: Stamp, tag: str) -> dict:
        """ Scrape a fragment of an html page following a blueprint. """
        # The document format quite is unreliable: the number of lines
        # in a section varies, the number of lines in a field varies
        # and the number of fields in a line varies. So we scrape one
        # field at a time. It's okay to return to the same line several
        # times. The goal is to end up with a robust set of data.

        contents = list(soup_fragment.stripped_strings)
        collected = {}

        for field, bp in blueprints.items():
            try:
                matched = match(bp['pattern'], contents[bp['line_nb']])
            except IndexError:
                collected[field] = None
                self._elucidate(stamp, field, bp, contents, tag)
            else:
                if matched:
                    collected[field] = matched.group(1)
                else:
                    collected[field] = None
                    if not bp['nullable']:
                        self._elucidate(stamp, field, bp, contents, tag)

        return collected

    def _scrape_prices(self, soup_fragment: BeautifulSoup) -> dict:
        """ Scrape the 'prices' table at the bottom of the page. """

        cells = list(soup_fragment.stripped_strings)
        price_table = dict(zip(cells[::2], cells[1::2]))

        keys = self._OVERNIGHTS
        for old, new in keys:
            if old in price_table:
                price_table[new] = price_table.pop(old)
            else:
                price_table[new] = None

        if price_table['waiting_time'] is not None:
            # We want the price not the time.
            price_table['waiting_time'] = price_table['waiting_time'][7::]

        return price_table

    @staticmethod
    def _elucidate(stamp: Stamp, field_name: str, blueprint: dict, fragment: list, tag: str):
        """ Print a debug message showing the context in which the scraping went wrong. """

        with open(ELUCIDATE, 'a') as f:
            with redirect_stdout(f):
                print('{date}-{uuid}: Failed to scrape {field} on line {nb} inside {tag}.'
                      .format(date=stamp.date,
                              uuid=stamp.uuid,
                              field=field_name,
                              nb=blueprint['line_nb'],
                              tag=tag))
                if len(fragment):
                    for line_nb, line_content in enumerate(fragment):
                        print(str(line_nb) + ': ' + line_content)
                else:
                    print('No content inside {tag}'.format(tag=tag))
                print(BREAK)


def factory() -> tuple:
    u = User(username='m-134', password='PASSWORD')
    d = Downloader(u.remote_session)
    s = Reader()
    p = Packager()
    a = Archiver(u.local_session)
    return d, s, p, a


def scrape(start_date: date, option):
    """ Migrate user data from the company server (bamboo-mec.de) to the local database. """

    assert option == '-since'
    assert isinstance(start_date, date), 'Parameter must be a date object.'
    assert start_date <= date.today(), 'Cannot return to the future'

    print('Migrating data from the remote server...')

    d, s, p, a = factory()
    period = date.today() - start_date
    days = range(period.days)

    for day in days:
        date_ = start_date + timedelta(days=day)
        soups = d.download(date_)

        if soups:
            strings = s.scrape(soups)
            tables = p.package(strings)
            a.archive(tables)

        print('Processed {n}/{N} ({percent}%).'.format(n=day, N=len(days), percent=int((day+1)/len(days)*100)))


def demo_run(day: date):
    """ Demonstrate the use of the module: don't push to database. """
    d, s, p, a = factory()
    soups = d.download(day)
    strings = s.scrape(soups)
    tables = p.package(strings)
    pprint(tables)


if __name__ == '__main__':
    demo_run(date(2014, 5, 6))

