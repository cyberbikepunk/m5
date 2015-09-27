""" Test the scraper module. """


from time import strptime
from datetime import date
from bs4 import BeautifulSoup
from os.path import join

from m5.scraper import scrape_job
from m5.settings import ASSETS_DIR
from m5.spider import Stamp, Stamped


webpages = {
    '2014-02-12-uuid-2041699.html': {
        'info': {
            'cash': None,
            'city_tour': None,
            'client_id': '59017',
            'client_name': 'Norsk European Wholesale Ltd.',
            'extra_stops': None,
            'fax_confirm': None,
            'km': None,
            'order_id': '1402120029',
            'overnight': None,
            'type': 'OV',
            'waiting_time': None,
        },
        'addresses': [
            {
                'address': 'Luetzowstrasse 107',
                'after': '07:00',
                'city': 'Berlin',
                'company': 'messenger Transport Logistik GmbH',
                'postal_code': '10785',
                'purpose': 'Abholung',
                'timestamp': '10:57',
                'until': '08:00',
            },
            {
                'address': 'Potsdamer Str. 4',
                'after': '08:00',
                'city': 'BERLIN',
                'company': 'Cinestar iMAX IM Sony Center',
                'postal_code': '10785',
                'purpose': 'Zustellung',
                'timestamp': '11:09',
                'until': '12:00',
            },
        ]
    }
}


def read_stamp(filename):
    uuid = filename[-12:-5]
    t = strptime(filename[0:9], '%Y-%m-%d')
    day = date(year=t.tm_year, month=t.tm_mon, day=t.tm_mday)

    return uuid, day


def test_scraper():

    filename = '2014-02-12-uuid-2041699.html'
    filepath = join(ASSETS_DIR, filename)

    with open(filepath, 'r') as f:
        html = f.read()

    soup = BeautifulSoup(html)
    uuid, day = read_stamp(filename)

    stamp = Stamp('mickey', day, uuid)
    job = Stamped(stamp, soup)

    scraped = scrape_job(job)

    info = webpages['2014-02-12-uuid-2041699.html']['info']
    addresses = webpages['2014-02-12-uuid-2041699.html']['addresses']

    assert scraped.data.info == info
    for expected, calculated in zip(addresses, scraped.data.addresses):
        assert expected == calculated


if __name__ == '__main__':
    test_scraper()

