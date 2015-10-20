""" Test the pipeline module. """


from pytest import mark, fixture
from datetime import date, datetime

from m5.user import Ghost
from m5.model import Client, Order, Checkpoint, Checkin
from m5.pipeline import process, geocode, archive, fix_unicode
from tests.test_scraper import OVERNIGHT_SCRAPED


OVERNIGHT_PROCESSED = (
    [
        Client(
            client_id=59017,
            name='Norsk European Wholesale Ltd.'
        )
    ],
    [
        Order(
            order_id=1402120029,
            client_id=59017,
            distance=None,
            cash=False,
            city_tour=0,
            extra_stops=0,
            overnight=4.20,
            fax_confirm=0,
            service=0,
            type='overnight',
            uuid=2041699,
            date=date(2014, 2, 12),
            user='pytest'
        )
    ],
    [
        Checkpoint(
            checkpoint_id='Lützowstraße 107, 10785 Berlin, Germany',
            company='messenger Transport Logistik GmbH',
            lat=52.50201999999999,
            lon=13.36934,
            city='Berlin',
            postal_code='10785',
            country='Germany',
            country_code='DE',
            street_name='Lützowstraße',
            street_number='107',
            as_scraped='Luetzowstrasse 107, Berlin 10785',
            place_id='ChIJj6NNFzVQqEcRxpeJsUaDork'
        ),
        Checkpoint(
            checkpoint_id='Potsdamer Straße 4, 10785 Berlin, Germany',
            company='Cinestar iMAX IM Sony Center',
            lat=52.5100083,
            lon=13.3732867,
            city='Berlin',
            postal_code='10785',
            country='Germany',
            country_code='DE',
            street_name='Potsdamer Straße',
            street_number='4',
            as_scraped='Potsdamer Str. 4, BERLIN 10785',
            place_id='ChIJyw9Yv8lRqEcROlWIrlxpItQ'
        ),
    ],
    [
        Checkin(
            timestamp=datetime(2014, 2, 12, 10, 57),
            checkpoint_id='Lützowstraße 107, 10785 Berlin, Germany',
            order_id=1402120029,
            purpose='pickup',
            after_=datetime(2014, 2, 12, 7),
            until=datetime(2014, 2, 12, 8),
            checkin_id='2014-02-12 10:57:00 | Lützowstraße 107, 10785 Berlin, Germany | '
                       '1402120029 | pickup | 2014-02-12 07:00:00 | 2014-02-12 08:00:00',
        ),
        Checkin(
            timestamp=datetime(2014, 2, 12, 11, 9),
            checkpoint_id='Potsdamer Straße 4, 10785 Berlin, Germany',
            order_id=1402120029,
            purpose='dropoff',
            after_=datetime(2014, 2, 12, 8),
            until=datetime(2014, 2, 12, 12),
            checkin_id='2014-02-12 11:09:00 | Potsdamer Straße 4, 10785 Berlin, Germany | '
                       '1402120029 | dropoff | 2014-02-12 08:00:00 | 2014-02-12 12:00:00'
        )
    ]
)


@mark.run(order=1)
@mark.parametrize('scraped_webpage, expected_webpage', zip([OVERNIGHT_SCRAPED], [OVERNIGHT_PROCESSED]))
def test_processor(scraped_webpage, expected_webpage):
    processed_webpage = process(scraped_webpage)

    def expose(tables_, i):
        # I cannot compare whole ORM table objects, only their public attributes
        return {k: v for k, v in vars(tables_[i]).items() if not k.startswith('_')}

    for processed, expected in zip(processed_webpage, expected_webpage):
        for tables in zip(processed, expected):
            assert expose(tables, 0) == expose(tables, 1)


ADDRESS_EXAMPLES = [
    ('Potsdamer Straße 4, 10785 Berlin, Germany', dict(address='Potsdamer Str. 4', city='BERLIN', postal_code='10785')),
    ('Lützowstraße 107, 10785 Berlin, Germany', dict(address='Luetzowstr 107', city='berlin', postal_code='10785')),
]


@mark.run(order=2)
@mark.parametrize('expected_address, raw_address', ADDRESS_EXAMPLES)
def test_geocoder(expected_address, raw_address):
    point = geocode(raw_address)

    assert point['address'] == expected_address


@fixture(scope='function')
def ghost(request):
    user = Ghost(offline=True).bootstrap().flush().init()
    request.addfinalizer(lambda: user.clear())

    return user


@mark.run(order=3)
def test_archiver(ghost):
    tables = [OVERNIGHT_PROCESSED, OVERNIGHT_PROCESSED]
    archive(ghost.db, tables)

    assert len(ghost.db.query(Checkin).all()) == 2
    assert len(ghost.db.query(Checkpoint).all()) == 2
    assert ghost.db.query(Client.id).scalar() == 59017
    assert ghost.db.query(Order.id).scalar() == 1402120029


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
