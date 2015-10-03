""" The scraper module extracts data from webpages. """


from re import match
from logging import debug
from m5.spider import Stamped, RawData
from m5.settings import SEPERATOR, FAILURE_REPORT


BLUEPRINTS = {
    'itinerary': {
        'km': {'line_nb': 0, 'pattern': r'(\d{1,2},\d{3})\s', 'nullable': True}
    },
    'header': {
        'order_id': {'line_nb': 0, 'pattern': r'.*(\d{10})', 'nullable': True},
        'type': {'line_nb': 0, 'pattern': r'.*(OV|Ladehilfe|Stadtkurier)', 'nullable': False},
        'cash': {'line_nb': 0, 'pattern': r'(BAR)', 'nullable': True}
    },
    'client': {
        'client_id': {'line_nb': 0, 'pattern': r'.*(\d{5})$', 'nullable': False},
        'client_name': {'line_nb': 0, 'pattern': r'Kunde:\s(.*)\s\|', 'nullable': False}
    },
    'address': {
        'company': {'line_nb': 1, 'pattern': r'(.*)', 'nullable': False},
        'address': {'line_nb': 2, 'pattern': r'(.*)', 'nullable': False},
        'city': {'line_nb': 3, 'pattern': r'(?:\d{5})\s(.*)', 'nullable': False},
        'postal_code': {'line_nb': 3, 'pattern': r'(\d{5})(?:.*)', 'nullable': False},
        'after': {'line_nb': -3, 'pattern': r'(?:.*)ab\s(\d{2}:\d{2})', 'nullable': True},
        'purpose': {'line_nb': 0, 'pattern': r'(Abholung|Zustellung)', 'nullable': False},
        'timestamp': {'line_nb': -2, 'pattern': r'ST:\s(\d{2}:\d{2})', 'nullable': False},
        'until': {'line_nb': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'nullable': True},
    }
}


HTML = {
    'header': {'name': 'h2', 'attrs': None},
    'client': {'name': 'h4', 'attrs': None},
    'itinerary': {'name': 'p', 'attrs': None},
    'prices': {'name': 'tbody', 'attrs': None},
    'address': {'name': 'div', 'attrs': {'data-collapsed': 'true'}}
}


def scrape(job):
    """
    In goes a webpage (as a beautiful soup), out comes data (as a Stamped data object).
    Each Stamped data object has an info attribute (a dictionary with IDs, prices etc...)
    and an addresses attribute containing an arbitrary number of addresses. All fields
    are raw strings at this stage.
    """

    order = job.data.find(id='order_detail')
    addresses = list()
    info = dict()

    # Step 1: scrape all information fragments
    tags = ['header', 'client', 'itinerary']

    for tag in tags:
        fragment = order.find_next(name=HTML[tag]['name'])
        fields = _scrape_fragment(BLUEPRINTS[tag], fragment, job.stamp)
        info.update(fields)

    # Step 2: scrape the price table
    fragment = order.find(HTML['prices']['name'])
    prices = _scrape_prices(fragment, job.stamp)
    info.update(prices)

    # Step 3: scrape an arbitrary number of addresses
    fragments = order.find_all(name=HTML['address']['name'], attrs=HTML['address']['attrs'])

    for fragment in fragments:
        address = _scrape_fragment(BLUEPRINTS['address'], fragment, job.stamp)
        addresses.append(address)

    return Stamped(job.stamp, RawData(info, addresses))


def _scrape_fragment(blueprints, fragment, stamp):
    # Fields are ambiguously inserted in the markup.
    # Fields may or may not be there.
    # Fields may be bundled together inside a single tag.
    # The number of fields inside a tag may vary.
    # The number of lines for a single field may vary.
    # The number of fields inside a single line may vary.

    contents = list(fragment.stripped_strings)
    collected = {}

    for field, bp in blueprints.items():
        try:
            matched = match(bp['pattern'], contents[bp['line_nb']])
        except IndexError:
            collected[field] = None
            _report_failure(stamp, field, contents)
        else:
            if matched:
                collected[field] = matched.group(1)
            else:
                collected[field] = None
                if not bp['nullable']:
                    _report_failure(stamp, field, contents)

    return collected


PRICE_CATEGORIES = {
    'city_tour': {
        'Stadtkurier',
        'Fehlanfarht'
    },
    'extra_stops': {
        'Stadt Stopp(s)'
    },
    'overnight': {
        'OV Ex Nat PU',
        'ON Ex Nat Del.',
        'OV EcoNat PU',
        'OV Ex Int PU',
        'ON Int Exp Del'
    },
    'fax_confirm': {
        'EmpfangsbestÃ¤t.',
        'Empfangsbestät.'
    },
    'service': {
        'Wartezeit min.',
        'Ladezeit in min',
        'Ladehilfe'
    }
}


def _scrape_prices(fragment, stamp):
    # This section is treated separately because it's
    # a table containing multiple price categories.

    cells = list(fragment.stripped_strings)
    raw_price_table = dict(zip(cells[::2], cells[1::2]))

    price_table = {k: [] for k in PRICE_CATEGORIES.keys()}

    for label, raw_price in sorted(raw_price_table.items()):
        for category, category_synonyms in PRICE_CATEGORIES.items():
            if label in category_synonyms:
                price_table[category].append(raw_price)
                break
        else:
            _report_failure(stamp, 'prices', fragment)

    return price_table


def _report_failure(stamp, field, fragment):
    debug(SEPERATOR)

    debug(FAILURE_REPORT.format(date=stamp.date,
                                uuid=stamp.uuid,
                                field=field))
    if len(fragment):
        for line_nb, line_content in enumerate(fragment):
            debug(str(line_nb) + ': ' + line_content)
    else:
        debug('No content inside the fragment')

    debug(SEPERATOR)

