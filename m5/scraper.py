""" The scraper module extracts data from webpages. """


from re import search, compile
from logging import debug, warning
from m5.spider import Stamped, RawData
from m5.settings import SEPERATOR, FAILURE_REPORT


BLUEPRINTS = {
    'itinerary': {
        'km': {
            'lines': {'default': [0], 'variant': [0]},
            'pattern': compile(r'(\d{1,2},\d{3})\s'),
            'optional': True
        }
    },
    'header': {
        'order_id': {
            'lines': {'default': [0], 'variant': [0]},
            'pattern': compile(r'.*(\d{10})'),
            'optional': True
        },
        'type': {
            'lines': {'default': [0], 'variant': [0]},
            'pattern': compile('.*(OV|Ladehilfe|Stadtkurier|Treibstoff|Kundensupport|t:m'
                               '|Abgabe|IC|Treibst|Staatsoper|Postfesttour|FS)'),
            'optional': False
        },
        'cash': {'lines': {'default': [0], 'variant': [0]},
                 'pattern': compile(r'(BAR)'),
                 'optional': True
                 }
    },
    'client': {
        'client_id': {
            'lines': {'default': [0], 'variant': [0]},
            'pattern': compile(r'.*(\d{5})$'),
            'optional': False
        },
        'client_name': {
            'lines': {'default': [0], 'variant': [0]},
            'pattern': compile(r'Kunde:\s(.*)\s\|'),
            'optional': False
        }
    },
    'address': {
        'company': {
            'lines': {'default': [1], 'variant': [1, 2]},
            'pattern': compile(r'(.*)'),
            'optional': False
        },
        'locality': {
            'lines': {'default': [3], 'variant': [5]},
            'pattern': compile(r'(.*)'),
            'optional': False
        },
        'address': {
            'lines': {'default': [2], 'variant': [4]},
            'pattern': compile(r'(.*)'),
            'optional': False
        },
        'after': {
            'lines': {'default': [-3], 'variant': [-3]},
            'pattern': compile(r'(?:.*)ab\s+(\d{2}:\d{2})'),
            'optional': True
        },
        'purpose': {
            'lines': {'default': [0], 'variant': [0]},
            'pattern': compile(r'(Abh./Zust.|Abholung|Zustellung)'),
            'optional': False
        },
        'timestamp': {
            'lines': {'default': [-2], 'variant': [-2]},
            'pattern': compile(r'ST:\s+(\d{2}:\d{2})'),
            'optional': False
        },
        'until': {
            'lines': {'default': [-3], 'variant': [-3]},
            'pattern': compile(r'(?:.*)bis\s+(\d{2}:\d{2})'),
            'optional': True
        },
    }
}


HTML = {
    'header': {'tag': 'h2', 'attrs': None},
    'client': {'tag': 'h4', 'attrs': None},
    'itinerary': {'tag': 'p', 'attrs': None},
    'prices': {'tag': 'tbody', 'attrs': None},
    'address': {'tag': 'div', 'attrs': {'data-collapsed': 'true'}}
}


PRICE_CATEGORIES = {
    'city_tour': {
        'Stadtkurier',
        't:m Stadt',
        'Subm.Abg.',
        '24/7 Stadt',
        '24SEVEN',
    },
    'cancelled_stop': {
        'Fehlanfarht',
    },
    'extra_stops': {
        'Stadt Stopp(s)'
    },
    'overnight': {
        'OV Ex Nat PU',
        'ON Ex Nat Del.',
        'OV EcoNat PU',
        'OV Ex Int PU',
        'ON Int Exp Del',
        'OV Ex Int TE PU',
        'Roll Out',
        'OV Eco Int PU',
        'Eco Int PU',
    },
    'client_support': {
        '2,50 Euro',
    },
    'fax_confirm': {
        'EmpfangsbestÃ¤t.',
        'Empfangsbestät.'
    },
    'waiting_time': {
        'Wartezeit min.',
        'Ladezeit in min',
    },
    'loading_service': {
        'Ladehilfe',
        'FS Zonen',
    }
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
        fragment = order.find_next(name=HTML[tag]['tag'])
        fields = _scrape_fragment(BLUEPRINTS[tag], fragment, job.stamp)
        info.update(fields)

    # Step 2: scrape the price table
    fragment = order.find(HTML['prices']['tag'])
    prices = _scrape_prices(fragment, job.stamp)
    info.update(prices)

    # Step 3: scrape an arbitrary number of addresses
    fragments = order.find_all(name=HTML['address']['tag'], attrs=HTML['address']['attrs'])

    for fragment in fragments:
        address = _scrape_fragment(BLUEPRINTS['address'], fragment, job.stamp)
        addresses.append(address)

    debug('Scraped %s-uuid-%s.html', job.stamp.date, job.stamp.uuid)

    return Stamped(job.stamp, RawData(info, addresses))


def fix_unicode(original_text):
    # This function is deprecated because web-pages are now correctly decoded into unicode.
    # But there could still be a few in the cache that haven't. This is a really DIRTY FIX.
    substitutions = [
        ('Ã¼', 'ü'),
        ('Ã¤', 'ä'),
        ('Ã¶', 'ö'),
        ('Ã©', 'é'),
        ('â¬', '€'),
        ('Ã', 'ß'),
        ('Ã', 'Ö'),
    ]

    corrected_text = original_text
    for bad, good in substitutions:
        corrected_text = corrected_text.replace(bad, good)

    if corrected_text != original_text:
        debug('Fixed %s', corrected_text)

    return corrected_text


def _scrape_fragment(blueprints, fragment, stamp):
    # Fields are ambiguously inserted in the markup.
    # Fields may or may not be there.
    # Fields may be bundled together inside a single tag.
    # The number of fields inside a tag may vary.
    # The number of lines for a single field may vary.
    # The number of fields inside a single line may vary.

    contents = list(fragment.stripped_strings)
    collected = {}

    # Sometimes addresses are formatted differently
    case = 'variant' if 'Zusatz' in fragment.text else 'default'

    for field, bp in blueprints.items():
        try:
            for line in bp['lines'][case]:
                matched = bp['pattern'].match(contents[line])
                if matched:
                    raw_value = matched.group(1)
                    collected[field] = fix_unicode(raw_value)
                    break
            else:
                raise ValueError

        except (IndexError, ValueError):
            collected[field] = None
            if not bp['optional']:
                _report_failure(stamp, field, contents)

    return collected


def _scrape_prices(fragment, stamp):
    # This fragment is treated separately because it's a
    # table with a whole bunch of possible price labels.
    pattern = r'(\d+,\d{2})$'

    cells = list(fragment.stripped_strings)
    raw_price_table = list(zip(cells[::2], cells[1::2]))
    price_table = {k: [] for k in PRICE_CATEGORIES.keys()}

    for raw_label, raw_price in sorted(raw_price_table):
        for category, category_synonyms in PRICE_CATEGORIES.items():
            if raw_label in category_synonyms:
                matched = search(pattern, raw_price)

                if matched:
                    price = matched.group(0)
                else:
                    price = None
                    warning('Could not convert "%s" into a price', raw_price)

                price_table[category].append(price)

    if not any(price_table.values()):
        _report_failure(stamp, 'prices', cells)

    return price_table


def _report_failure(stamp, field, fragment):
    warning(SEPERATOR)

    warning(FAILURE_REPORT.format(date=stamp.date,
                                  uuid=stamp.uuid,
                                  field=field))
    if len(fragment):
        for line_nb, line_content in enumerate(fragment):
            warning(str(line_nb) + ': ' + line_content)
    else:
        warning('No content inside the fragment')

    warning(SEPERATOR)
