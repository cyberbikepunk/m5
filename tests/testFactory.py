""" Varrious unittest scripts for the factory module. """


from unittest import TestCase

from os import listdir, remove
from requests import Session
from bs4 import BeautifulSoup
from random import randint
from os.path import join, dirname, normpath
from random import sample
from re import search, match
from datetime import datetime, date

from m5.factory import Scraper, Miner, Packager
from m5.utilities import Stamp, Stamped, Tables
from m5.model import Client, Order, Checkin, Checkpoint


class TestDownloader(TestCase):

    def setUp(self):
        """  Log into the remote server. """

        self.url = 'http://bamboo-mec.de/ll.php5'

        test_dir = dirname(__file__)
        self.directory = join(test_dir, 'temp')

        credentials = {'username': 'm-134',
                       'password': 'PASSWORD'}

        self.session = Session()
        headers = {'user-agent': 'Mozilla/5.0'}
        self.session.headers.update(headers)

        response = self.session.post(self.url, credentials)
        if response.ok:
            print('Now logged into remote server.')
        else:
            print('Failed to log in')
            exit(1)

    def tearDown(self):
        """  Logout. """

        # Say goodbye to the server
        url = 'http://bamboo-mec.de/index.php5'
        payload = {'logout': '1'}

        response = self.session.get(url, params=payload)

        if response.history[0].status_code == 302:
            # We have been redirected to the home page
            print('Logged out from remote server. Goodbye!')

        self.session.close()

        # Clean up the temp directory
        for file in listdir(self.directory):
            if search(self.day.strftime('%Y-%m-%d'), file):
                remove(join(self.directory, file))

    def testMiner(self):
        """ Check if the Miner class can download files correctly from the company server. """

        m = Miner(self.session,
                  self.directory,
                  overwrite=True)

        random_day = randint(1, 28)
        random_month = randint(1, 12)
        self.day = date(2014, random_month, random_day)

        print('Testing file download for %s.' % str(self.day))
        soups = m.mine(self.day)

        if not soups:
            # No jobs on that day... try again
            self.testMiner()
        else:
            for soup in soups:
                self.assertIsInstance(soup.data, BeautifulSoup)
                self.assertIsInstance(soup.stamp.date, date)
                self.assertIsInstance(soup.stamp.uuid, str)

                order_detail = soup.data.find(id='order_detail')
                self.assertIsNotNone(order_detail)


class TestScraper(TestCase):

    def SetUp(self):
        pass

    def tearDown(self):
        pass

    def testScraper(self):
        """
        Test the Scraper class by feeding it a sample of html
        files randomly picked from the download directory.
        """

        path_ = dirname(__file__)
        downloads = normpath(join(path_, '../downloads/m-134'))

        files = listdir(downloads)
        files = [file for file in files if 'NO_JOBS' not in file]

        min_ = 1
        max_ = len(files)
        size = 100

        samples = sample(range(min_, max_), size)
        soup_items = list()

        for i in samples:
            filepath = join(downloads, files[i])

            with open(filepath, 'r') as f:
                html = f.read()
                f.close()
                soup = BeautifulSoup(html)

                uuid_match = search(r'uuid-(\d{7})', files[i])
                uuid = uuid_match.group(1)

                date_match = match(r'(\d{4}-\d{2}-\d{2})', files[i])
                sdate = date_match.group(1)
                date_ = datetime.strptime(sdate, '%Y-%m-%d').date()

                stamp = Stamp(date_, uuid)
                soup_item = Stamped(stamp, soup)
                soup_items.append(soup_item)

        s = Scraper()
        serial_items = s.scrape(soup_items)

        self.assertIsNotNone(serial_items)


class TestPackager(TestCase):

    def SetUp(self):
        pass

    def tearDown(self):
        pass

    def testScraper(self):
        """
        Test the Scraper class by feeding it a sample of html
        files randomly picked from the download directory.
        """
        stamp = Stamp(date(1, 1, 1), 1234567)
        serial_items = list()

        job_details = {'fax_confirm': '3,50',
                       'city_tour': '11,20',
                       'extra_stops': '3,50',
                       'client_name': 'Lisa D. Productions',
                       'client_id': '30349',
                       'waiting_time': '2,00',
                       'km': '6,414',
                       'order_id': '1412050834',
                       'cash': 'BAR',
                       'type': 'Stadtkurier',
                       'overnight': '3,50'}

        addresses = [{'company': 'Lisa D. Productions',
                      'address': 'Rosenthaler StraÃ\x9fe 40-41',
                      'postal_code': '10178',
                      'after': '14:03',
                      'purpose': 'Abholung',
                      'until': '15:03',
                      'timestamp': '14:46',
                      'city': 'Berlin'},
                     {'company': 'Lisa D. Productions',
                      'address': 'Frankenstrasse 1',
                      'postal_code': '10781',
                      'after': '16:03',
                      'purpose': 'Zustellung',
                      'until': '17:03',
                      'timestamp': '15:10',
                      'city': 'Berlin'}]

        serial_items.append(Stamped(stamp, (job_details, addresses)))

        job_details = {'fax_confirm': None,
                       'city_tour': None,
                       'extra_stops': None,
                       'client_name': None,
                       'client_id': None,
                       'waiting_time': None,
                       'km': None,
                       'order_id': None,
                       'cash': None,
                       'type': None,
                       'overnight': None}

        addresses = [{'company': None,
                      'address': None,
                      'postal_code': None,
                      'after': None,
                      'purpose': None,
                      'until': None,
                      'timestamp': None,
                      'city': None},
                     {'company': None,
                      'address': None,
                      'postal_code': None,
                      'after': None,
                      'purpose': None,
                      'until': None,
                      'timestamp': None,
                      'city': None}]

        serial_items.append(Stamped(stamp, (job_details, addresses)))

        p = Packager()
        tables = p.package(serial_items)

        from pprint import PrettyPrinter
        pp = PrettyPrinter()
        pp.pprint(tables)

        self.assertIsNotNone(tables)
        self.assertIsInstance(tables, Tables)

        self.assertIsInstance(tables.clients, list)
        self.assertIsInstance(tables.orders, list)
        self.assertIsInstance(tables.checkins, list)
        self.assertIsInstance(tables.checkpoints, list)

        self.assertIsInstance(tables.clients[0], Client)
        self.assertIsInstance(tables.orders[0], Order)
        self.assertIsInstance(tables.checkins[0], Checkin)
        self.assertIsInstance(tables.checkpoints[0], Checkpoint)