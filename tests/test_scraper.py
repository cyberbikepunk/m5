""" Test the scraper module. """


from datetime import date
from bs4 import BeautifulSoup
from os.path import join
from pytest import mark

from m5.scraper import scrape, fix_unicode
from m5.settings import ASSETS_DIR
from m5.spider import Stamp, Stamped, RawData


OVERNIGHT_SCRAPED = Stamped(
    Stamp('pytest', date(2014, 2, 12), '2041699'),
    RawData(
        {
            'cash': None,
            'city_tour': [],
            'client_id': '59017',
            'client_name': 'Norsk European Wholesale Ltd.',
            'extra_stops': [],
            'fax_confirm': [],
            'waiting_time': [],
            'loading_service': [],
            'client_support': [],
            'cancelled_stop': [],
            'km': None,
            'order_id': '1402120029',
            'overnight': ['4,20'],
            'type': 'OV',
        },
        [
            {
                'address': 'Luetzowstrasse 107',
                'after': '07:00',
                'company': 'messenger Transport Logistik GmbH',
                'locality': '10785 Berlin',
                'purpose': 'Abholung',
                'timestamp': '10:57',
                'until': '08:00',
            },
            {
                'address': 'Potsdamer Str. 4',
                'after': '08:00',
                'company': 'Cinestar iMAX IM Sony Center',
                'locality': '10785 BERLIN',
                'purpose': 'Zustellung',
                'timestamp': '11:09',
                'until': '12:00',
            },
        ]
    )
)


SERVICE = Stamped(
    Stamp('assets', date(2013, 3, 7), '1124990'),
    RawData(
        {
            'cash': None,
            'city_tour': [],
            'client_id': '49315',
            'client_name': 'Zalando GmbH',
            'extra_stops': [],
            'fax_confirm': [],
            'overnight': [],
            'loading_service': ['12,00'],
            'client_support': [],
            'cancelled_stop': [],
            'km': None,
            'order_id': '1303070990',
            'type': 'Ladehilfe',
            'waiting_time': ['36,00'],
        },
        [
            {
                'address': 'Prenzlauer Allee 33',
                'after': '16:15',
                'company': 'Loft Werner Franz',
                'locality': '10405 Berlin',
                'purpose': 'Abholung',
                'timestamp': '16:59',
                'until': None,
            },
            {
                'address': 'Prenzlauer Allee 33',
                'after': None,
                'company': 'Loft Werner Franz',
                'locality': '10405 Berlin',
                'purpose': 'Zustellung',
                'timestamp': '18:45',
                'until': None,
            },
        ]
    )
)


CASH = Stamped(
    Stamp('assets', date(2013, 3, 7), '1124990'),
    RawData(
        {
            'cash': 'BAR',
            'city_tour': ['9,30'],
            'client_id': '66092',
            'client_name': 'Johannes Barthelmes',
            'extra_stops': [],
            'fax_confirm': [],
            'client_support': [],
            'loading_service': [],
            'waiting_time': [],
            'overnight': [],
            'cancelled_stop': [],
            'km': '4,294',
            'order_id': '1303070239',
            'type': 'Stadtkurier',
        },
        [
            {
                'address': 'Willibald-Alexis-Straße 22',
                'after': '10:37',
                'company': 'Johannes Barthelmes Serenebar',
                'locality': '10965 Berlin',
                'purpose': 'Abholung',
                'timestamp': '11:05',
                'until': '11:30',
            },
            {
                'address': 'Nollendorfplatz 5',
                'after': None,
                'company': 'SB Tiede',
                'locality': '10777 Berlin',
                'purpose': 'Zustellung',
                'timestamp': '11:27',
                'until': None,
            },
        ]
    )
)


SCRAPED = [
    ('2014-02-12-uuid-2041699.html', OVERNIGHT_SCRAPED),
    ('2013-03-07-uuid-1124990.html', SERVICE),
    ('2013-03-07-uuid-1123772.html', CASH)
]


@mark.run(order=0)
@mark.parametrize('filename, expected', SCRAPED)
def test_scraper(filename, expected):

    filepath = join(ASSETS_DIR, filename)
    with open(filepath, 'r') as f:
        html = f.read()

    soup = BeautifulSoup(html)
    job = Stamped(expected.stamp, soup)

    result = scrape(job)

    assert result.data.info == expected.data.info
    assert result.data.addresses == expected.data.addresses


def test_unicode_correction():
    original_tokens = [
        'KurfÃ¼rstenstraÃe',
        'KindergÃ¤rten City GeschÃ¤ftsstelle',
        'MÃ¼nchen',
        'Paul-LÃ¶be Haus',
        'LennÃ©straÃe',
        'Auslage 30â¬',
    ]

    final_tokens = [
        'Kurfürstenstraße',
        'Kindergärten City Geschäftsstelle',
        'München',
        'Paul-Löbe Haus',
        'Lennéstraße',
        'Auslage 30€',
    ]

    for original, final in zip(original_tokens, final_tokens):
        assert final == fix_unicode(original)
