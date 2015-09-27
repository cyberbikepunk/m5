""" Test the scraper module. """


from datetime import date
from bs4 import BeautifulSoup
from os.path import join
from pytest import mark

from m5.scraper import scrape_from_soup
from m5.settings import ASSETS_DIR
from m5.spider import Stamp, Stamped, RawData


overnight = Stamped(
    Stamp('assets', date(2014, 2, 12), '2041699'),
    RawData(
        {
            'cash': None,
            'city_tour': '12,00',
            'client_id': '59017',
            'client_name': 'Norsk European Wholesale Ltd.',
            'extra_stops': None,
            'fax_confirm': None,
            'km': None,
            'order_id': '1402120029',
            'overnight': None,
            'type': 'OV',
            'waiting_time': '36,00',
        },
        [
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
    )
)


ladehilfe = Stamped(
    Stamp('assets', date(2013, 3, 7), '1124990'),
    RawData(
        {
            'cash': None,
            'city_tour': None,
            'client_id': '49315',
            'client_name': 'Zalando GmbH',
            'extra_stops': None,
            'fax_confirm': None,
            'km': None,
            'order_id': '1303070990',
            'overnight': None,
            'type': 'Ladehilfe',
            'waiting_time': None,
        },
        [
            {
                'address': 'Prenzlauer Allee 33',
                'after': '16:15',
                'city': 'Berlin',
                'company': 'Loft Werner Franz',
                'postal_code': '10405',
                'purpose': 'Abholung',
                'timestamp': '16:59',
                'until': None,
            },
            {
                'address': 'Prenzlauer Allee 33',
                'after': None,
                'city': 'Berlin',
                'company': 'Loft Werner Franz',
                'postal_code': '10405',
                'purpose': 'Zustellung',
                'timestamp': '18:45',
                'until': None,
            },
        ]
    )
)


tests_examples = [
    ('2014-02-12-uuid-2041699.html', overnight),
    ('2013-03-07-uuid-1124990.html', ladehilfe)
]


@mark.parametrize('filename, expected', tests_examples)
def test_eval(filename, expected):

    filepath = join(ASSETS_DIR, filename)
    with open(filepath, 'r') as f:
        html = f.read()

    soup = BeautifulSoup(html)
    job = Stamped(expected.stamp, soup)
    result = scrape_from_soup(job)

    assert result.data.info == expected.data.info
    assert result.data.addresses == expected.data.addresses
