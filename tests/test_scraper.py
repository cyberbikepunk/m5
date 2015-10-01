""" Test the scraper module. """


from datetime import date
from bs4 import BeautifulSoup
from os.path import join
from pytest import mark

from m5.scraper import scrape
from m5.settings import ASSETS_DIR
from m5.spider import Stamp, Stamped, RawData


overnight = Stamped(
    Stamp('assets', date(2014, 2, 12), '2041699'),
    RawData(
        {
            'cash': None,
            'city_tour': [],
            'client_id': '59017',
            'client_name': 'Norsk European Wholesale Ltd.',
            'extra_stops': [],
            'fax_confirm': [],
            'km': None,
            'order_id': '1402120029',
            'overnight': ['4,20'],
            'type': 'OV',
            'waiting_time': [],
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


loading_service = Stamped(
    Stamp('assets', date(2013, 3, 7), '1124990'),
    RawData(
        {
            'cash': None,
            'city_tour': [],
            'client_id': '49315',
            'client_name': 'Zalando GmbH',
            'extra_stops': [],
            'fax_confirm': [],
            'km': None,
            'order_id': '1303070990',
            'overnight': [],
            'type': 'Ladehilfe',
            'waiting_time': ['12,00', '(90,00) 36,00'],
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


cash_tour = Stamped(
    Stamp('assets', date(2013, 3, 7), '1124990'),
    RawData(
        {
            'cash': 'BAR',
            'city_tour': ['9,30'],
            'client_id': '66092',
            'client_name': 'Johannes Barthelmes',
            'extra_stops': [],
            'fax_confirm': [],
            'km': '4,294',
            'order_id': '1303070239',
            'overnight': [],
            'type': 'Stadtkurier',
            'waiting_time': [],
        },
        [
            {
                'address': 'Willibald-Alexis-Straße 22',
                'after': '10:37',
                'city': 'Berlin',
                'company': 'Johannes Barthelmes Serenebar',
                'postal_code': '10965',
                'purpose': 'Abholung',
                'timestamp': '11:05',
                'until': '11:30',
            },
            {
                'address': 'Nollendorfplatz 5',
                'after': None,
                'city': 'Berlin',
                'company': 'SB Tiede',
                'postal_code': '10777',
                'purpose': 'Zustellung',
                'timestamp': '11:27',
                'until': None,
            },
        ]
    )
)


tests_examples = [
    ('2014-02-12-uuid-2041699.html', overnight),
    ('2013-03-07-uuid-1124990.html', loading_service),
    ('2013-03-07-uuid-1123772.html', cash_tour)
]


@mark.parametrize('filename, expected', tests_examples)
def test_eval(filename, expected):

    filepath = join(ASSETS_DIR, filename)
    with open(filepath, 'r') as f:
        html = f.read()

    soup = BeautifulSoup(html)
    job = Stamped(expected.stamp, soup)

    result = scrape(job)

    assert result.data.info == expected.data.info
    assert result.data.addresses == expected.data.addresses
