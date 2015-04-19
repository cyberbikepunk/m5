""" The factory module migrates remote data to the local database. """

import sys

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

from settings import DEBUG, DOWNLOADS, ELUCIDATE, JOB, SUMMARY, OFFLINE
from utilities import log_me, time_me, Stamped, Stamp, Tables
from model import Checkin, Checkpoint, Client, Order
from user import User


class Archiver():
    """ The Archiver class pushes packaged data into the local database. """

    def __init__(self, local_session: LocalSession):
        self._local_session = local_session

    def archive(self, tables: Tables):
        """
        The archive method takes Table objects produced by the packager and
        commits them into the database. If a row already exists, the database
        session will raise an IntegrityError and rollback the commit.
        """

        for table in tables:
            for row in table:
                try:
                    self._local_session.merge(row)
                    self._local_session.commit()
                except IntegrityError:
                    self._local_session.rollback()
                    print('Database Intergrity ERROR: {table}'
                          .format(table=str(row)))


class Downloader():
    """ The Downloader class gets html files from the remote server. """

    def __init__(self, remote_session: RemoteSession, overwrite: bool=None):
        """ Instantiate a re-useable Downloader object. """

        assert OFFLINE is False, 'OFFLINE flag must be turned off in settings modules.'

        self._overwrite = overwrite
        self._remote_session = remote_session
        self._stamp = None

    @time_me
    def bulk_download(self, start_date=date.today()):
        """  Download all html pages since that day. """

        assert start_date <= date.today(), 'The date parameter must be a date in the past.'

        delta = date.today() - start_date
        for d in range(delta.days):
            self.download(start_date + timedelta(days=d))

    def download(self, day: date) -> list:
        """
        Download the web-page showing one day of messenger data.
        Save the raw html files and and return a list of beautiful soups.
        If that day has already been cached, serve the soup from file.
        """

        assert isinstance(day, date), 'Argument must be a date object'

        if self._is_hopeless(day):
            # We have already checked online in the
            # past: there are no jobs for that day.
            return None

        # Go browse the 'summary' for that day
        # and find out how many jobs we have.
        uuids = self._scrape_uuids(day)
        soup_jobs = list()

        if not uuids:
            soup_jobs = None
            if DEBUG:
                print('No jobs to download on {day}.'.format(day=str(day)))

        else:
            for i, uuid in enumerate(uuids):
                self._stamp = Stamp(day, uuid)

                if self._is_cached() and not self._overwrite:
                    soup = self._load_job()
                    verb = 'Loaded'
                else:
                    soup = self._get_job()
                    self._save_job(soup)
                    verb = 'Downloaded'

                if DEBUG:
                    print('{verb} {n}/{N}. {url}'.
                          format(verb=verb, n=i+1, N=len(uuids), url=self._job_url()))

                soup_jobs.append(Stamped(self._stamp, soup))

        return soup_jobs

    def _scrape_uuids(self, day: date) -> set:
        """ Return uuid request parameters for each job by scraping the summary page. """

        url = SUMMARY
        payload = {'status': 'delivered', 'datum': day.strftime('%d.%m.%Y')}
        response = self._remote_session.get(url, params=payload)

        # The so called 'uuids' are
        # actually 7 digit numbers.
        pattern = 'uuid=(\d{7})'
        jobs = findall(pattern, response.text)

        # Dump the duplicates.
        return set(jobs)

    def _get_job(self) -> BeautifulSoup:
        """ Browse the web-page for that day and return a beautiful soup. """

        url = JOB
        payload = {'status': 'delivered',
                   'uuid': self._stamp.uuid,
                   'datum': self._stamp.date.strftime('%d.%m.%Y')}

        response = self._remote_session.get(url, params=payload)
        soup = BeautifulSoup(response.text)

        return soup

    def _is_hopeless(self, day: date):
        """ True if we already know that the day has jobs to be downloaded. """
        # If we have already requested this day and found that it has no jobs,
        # there is an empty file with 'NO_JOBS' stamped on it inside the downloads
        # directory. So we just check whether that empty file is there or not.
        self._stamp = Stamp(day, 'NO_JOBS')
        return self._is_cached()

    def _filepath(self) -> str:
        """ Where a job's html file is saved. """
        filename = '%s-uuid-%s.html' % (self._stamp.date.strftime('%Y-%m-%d'), self._stamp.uuid)
        return path.join(DOWNLOADS, filename)

    def _job_url(self) -> bool:
        """ Return the job url for a given day and uuid. """
        return 'http://bamboo-mec.de/ll_detail.php5?status=delivered&uuid={uuid}&datum={date}'\
            .format(uuid=self._stamp.uuid, date=self._stamp.date.strftime('%d.%m.%Y'))

    def _is_cached(self) -> bool:
        """ True if the html file is found locally. """
        return True if isfile(self._filepath()) else False

    def _save_job(self, soup):
        """ Prettify the soup and save it to file. """
        with open(self._filepath(), 'w+') as f:
            f.write(soup.prettify())

    def _load_job(self) -> BeautifulSoup:
        """ Load an html file and return a beautiful soup. """
        with open(self._filepath(), 'r') as f:
            html = f.read()
        return BeautifulSoup(html)


class Packager():
    """ The Packager class processes the raw serial data produced by the Scraper. """

    def __init__(self):
        pass

    def package(self, serial_items: list) -> Tables:
        """
        In goes serial data (raw strings) as returned by the Scraper. Out comes
        unserialized & packaged ORM table row objects digestable by the database.

        :param serial_items: a list of Stamped(Stamp, serial_data) objects
        :return: a Tables(clients, orders, checkpoints, checkins) object
        """

        assert serial_items is not None, 'Argument cannot be None.'

        clients = list()
        orders = list()
        checkpoints = list()
        checkins = list()

        for serial_item in serial_items:

            # Unpack the data
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

        # The order matters when we commit to the database
        # because foreign keys must be refer to existing
        # rows in related tables, c.f. the model module.
        tables = Tables(clients, orders, checkpoints, checkins)

        return tables

    @staticmethod
    def _geocode(raw_address: dict) -> dict:
        """ Geocode an address with Nominatim (http://nominatim.openstreetmap.org).
        The returned osm_id is used as the primary key in the checkpoint table. So,
        if we can't geocode an address, None won't later make it into the database.
        """
    
        g = Nominatim()

        # TODO Geo-coding must not default to Germany
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
                print('Nominatim skipped {street} due to missing field(s).'.format(street=raw_address['address']))
            return nothing

        else:
            # Here we have to catch everything, including
            # a ssl socket.timeout error that is not raised
            # as a python exception. And so PyCharm needs
            # the following line to avoid squiggling us:
            # noinspection PyBroadException
            try:
                response = g.geocode(json_address)
            except:
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

    # FIXME The unserialisation procedures should be defined inside the orm declaration and dirty fixes removed.

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


class Scraper:
    """ Basically, the Scraper class scrapes data fields from html files. """

    # Some tags are a target.
    _TAGS = dict(header={'name': 'h2', 'attrs': None},
                 client={'name': 'h4', 'attrs': None},
                 itinerary={'name': 'p', 'attrs': None},
                 prices={'name': 'tbody', 'attrs': None},
                 address={'name': 'div', 'attrs': {'data-collapsed': 'true'}})

    # FIXME blueprints should be defined within the orm declarative model and unwrapped here on the fly.
    # Each field has a regex instructions.
    _BLUEPRINTS = {'itinerary': dict(km={'line_nb': 0, 'pattern': r'(\d{1,2},\d{3})\s', 'nullable': True}),
                   'header': dict(order_id={'line_nb': 0, 'pattern': r'.*(\d{10})', 'nullable': True},
                                  type={'line_nb': 0, 'pattern': r'.*(OV|Ladehilfe|Stadtkurier)', 'nullable': False},
                                  cash={'line_nb': 0, 'pattern': r'(BAR)', 'nullable': True}),
                   'client': dict(client_id={'line_nb': 0, 'pattern': r'.*(\d{5})$', 'nullable': False},
                                  client_name={'line_nb': 0, 'pattern': r'Kunde:\s(.*)\s\|', 'nullable': False}),
                   'address': dict(company={'line_nb': 1, 'pattern': r'(.*)', 'nullable': False},
                                   address={'line_nb': 2, 'pattern': r'(.*)', 'nullable': False},
                                   city={'line_nb': 3, 'pattern': r'(?:\d{5})\s(.*)', 'nullable': False},
                                   postal_code={'line_nb': 3, 'pattern': r'(\d{5})(?:.*)', 'nullable': False},
                                   after={'line_nb': -3, 'pattern': r'(?:.*)ab\s(\d{2}:\d{2})', 'nullable': True},
                                   purpose={'line_nb': 0, 'pattern': r'(Abholung|Zustellung)', 'nullable': False},
                                   timestamp={'line_nb': -2, 'pattern': r'ST:\s(\d{2}:\d{2})', 'nullable': False},
                                   until={'line_nb': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'nullable': True})}

    def __init__(self):
        self._stamp = None

    @log_me
    def scrape(self, soup_jobs: list) -> list:
        """
        In goes a list of html files (in the form of beautiful soups), out comes a list of serial data,
        i.e. dictionaries of field name/value pairs. At this point, values are stored as raw strings.

        :param soup_jobs: a list of Stamped(Stamp, soup)
        :return: a list of Stamped(Stamp, (job_details, addresses))
        """

        assert soup_jobs is not None, 'Argument cannot be None.'
        serial_jobs = list()

        for i, soup_job in enumerate(soup_jobs):
            self._stamp = soup_job.stamp

            job_details, addresses = self._scrape_job(soup_job)
            serial_job = Stamped(soup_job.stamp, (job_details, addresses))

            serial_jobs.append(serial_job)

            if DEBUG:
                print('Scraped {n}/{N}: {date}-uuid-{uuid}.html'
                      .format(date=str(soup_job.stamp.date),
                              uuid=soup_job.stamp.uuid,
                              N=len(soup_jobs),
                              n=i+1))

                pprint(job_details)
                pprint(addresses)

        return serial_jobs

    @property
    def _done(self):
        """ Print the url of the job. """
        return 'Scraped http://bamboo-mec.de/ll_detail.php5?status=delivered&uuid={uuid}&datum={date}'\
            .format(uuid=self._stamp.uuid, date=self._stamp.date.strftime('%d.%m.%Y'))

    def _scrape_job(self, soup_item: Stamped) -> tuple:
        """ Scrape out of a job's web page using bs4 and re modules. In goes the soup,
        out come a tuple of dictionaries contaning field name/value pairs (strings).
        """

        # Pass the soup through the sieve
        soup = soup_item.data.find(id='order_detail')

        # Step 1: scrape job details
        job_details = dict()

        # Step 1.1: in all fragments except prices
        fragments = ['header', 'client', 'itinerary']

        for fragment in fragments:
            soup_fragment = soup.find_next(name=self._TAGS[fragment]['name'])
            fields_subset = self._scrape_fragment(self._BLUEPRINTS[fragment], soup_fragment,
                                                  soup_item.stamp, fragment)
            job_details.update(fields_subset)

        # Step 1.2: in the price table
        soup_fragment = soup.find(self._TAGS['prices']['name'])
        prices = self._scrape_prices(soup_fragment)

        job_details.update(prices)

        # Step 2: scrape an arbitrary number of addresses
        soup_fragments = soup.find_all(name=self._TAGS['address']['name'],
                                       attrs=self._TAGS['address']['attrs'])
        addresses = list()
        for soup_fragment in soup_fragments:
            address = self._scrape_fragment(self._BLUEPRINTS['address'], soup_fragment,
                                            soup_item.stamp, 'address')
            addresses.append(address)

        return job_details, addresses

    def _scrape_fragment(self,
                         blueprints: dict,
                         soup_fragment: BeautifulSoup,
                         stamp: Stamp,
                         tag: str) -> dict:
        """
        Scrape a fragment of the page. In goes hmtl
        with the blueprint, out comes a dictionary.

        :param blueprints: the instructions
        :param soup_fragment: an html fragment
        :return: field name/value pairs
        """

        # The document format quite is unreliable: the number of lines
        # in each section varies and the number of fields on each line
        # also varies. For this reason, our scraping is conservative.
        # The motto is: one field at a time! The goal is to end up with
        # a robust set of data. Failure to collect information is not a
        # show-stopper but we should know about it!

        # Split the contents of the html fragment into a list of lines
        contents = list(soup_fragment.stripped_strings)
        collected = {}

        # Collect each field one by one, even if that
        # means returning to the same line several times.
        for field, blueprint in blueprints.items():
            try:
                matched = match(blueprint['pattern'], contents[blueprint['line_nb']])
            except IndexError:
                collected[field] = None
                self._elucidate(stamp, field, blueprint, contents, tag)
            else:
                if matched:
                    collected[field] = matched.group(1)
                else:
                    collected[field] = None
                    if not blueprint['nullable']:
                        self._elucidate(stamp, field, blueprint, contents, tag)

        return collected

    @staticmethod
    def _scrape_prices(soup_fragment: BeautifulSoup) -> dict:
        """ Scrape the 'prices' table at the bottom of the page. """
        # TODO Get rid of this method! There's no reason why this part should be treated separately.

        # The table is scraped as a one-dimensional list
        # of cells but we want it in dictionary format.
        cells = list(soup_fragment.stripped_strings)
        price_table = dict(zip(cells[::2], cells[1::2]))

        # Original field names are no good. Change them.
        keys = [('Stadtkurier', 'city_tour'),
                ('Stadt Stopp(s)', 'extra_stops'),
                ('OV Ex Nat PU', 'overnight'),
                ('ON Ex Nat Del.', 'overnight'),
                ('OV EcoNat PU', 'overnight'),
                ('OV Ex Int PU', 'overnight'),
                ('ON Int Exp Del', 'overnight'),
                ('EmpfangsbestÃ¤t.', 'fax_confirm'),
                ('Wartezeit min.', 'waiting_time')]

        for old, new in keys:
            if old in price_table:
                price_table[new] = price_table.pop(old)
            else:
                price_table[new] = None

        # The waiting time cell has the time in minutes as well as the price. We just want the price.
        if price_table['waiting_time'] is not None:
            price_table['waiting_time'] = price_table['waiting_time'][7::]

        return price_table

    @staticmethod
    def _elucidate(stamp: Stamp, field_name: str, blueprint: dict, context: list, tag: str):
        """ Print a debug message showing the context in which the scraping went wrong.

        :param: stamp: holds the job date and uuid
        :param field_name: the name of the field
        :param blueprint: the field instructions
        :param context: the document fragment
        """

        reset = sys.stdout
        sys.stdout = open(ELUCIDATE, 'w+')

        print('{date}-{uuid}: Failed to scrape {field} on line {nb} inside {tag}.'
              .format(date=stamp.date,
                      uuid=stamp.uuid,
                      field=field_name,
                      nb=blueprint['line_nb'],
                      tag=tag))

        if len(context):
            for line_nb, line_content in enumerate(context):
                print(str(line_nb) + ': ' + line_content)
        else:
            print('No html content inside {tag}'.format(tag=tag))

        print('-'*100)
        sys.stdout = reset


def factory() -> tuple:
    """ Return """

    u = User()
    d = Downloader(u.remote_session)
    s = Scraper()
    p = Packager()
    a = Archiver(u.local_session)

    return d, s, p, a


@time_me
def fetch(start_date: date):
    """
    Transfer all the user data since that day. Data is transfered
    from the bamboo-mec.de company server to the local database.
    """

    assert isinstance(start_date, date), 'Parameter must be a date object.'
    assert start_date <= date.today(), 'Cannot return to the future'

    d, s, p, a = factory()

    period = date.today() - start_date
    days = range(period.days)

    for day in days:
        # Take one day's worth of data and
        # walk through the data migration
        # process from beginning to end
        _date = start_date + timedelta(days=day)

        # The downloader will serve files
        # from cache if it already has them.
        soup_jobs = d.download(_date)

        if soup_jobs:
            serial_jobs = s.scrape(soup_jobs)
            table_jobs = p.package(serial_jobs)
            a.archive(table_jobs)

        print('Processed {n}/{N} ({percent}%).'
              .format(n=day, N=len(days), percent=int((day+1)/len(days)*100)))


def demo_run(day: date):
    """ Demonstrate the use of the module: download, scrape and package, but don't archive. """

    assert isinstance(day, date), 'Parameter must be a date object.'
    assert day <= date.today(), 'Cannot return to the future'

    d, s, p, a = factory()
    soups = d.download(day)
    serial = s.scrape(soups)
    tables = p.package(serial)
    print(tables)


if __name__ == '__main__':
    demo_run(date(2014, 5, 6))

