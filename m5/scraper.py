""" The scraper module extracts data from webpages. """


from contextlib import redirect_stdout
from os.path import join
from re import match
from logging import debug

from m5.spider import Stamped, RawData
from m5.settings import BREAK, JOB_QUERY_URL, USER_BASE_DIR, FAILURE_REPORT, JOB_FILENAME


# Notes on the scraping strategy:
# ===============================
#
# Given that
#   1. fields may or may not be there
#   2. fields may be bundled together inside a single tag
#   3. the number of fields inside a tag may vary
#   4. the number of lines for a single field may vary
#   5. the number of fields inside a single line may vary
# we use regex extensively and return to the same place
# several times if necessary. The goal is to end up with
# a decent set of data.


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
        'until': {'line_nb': -3, 'pattern': r'(?:.*)bis\s+(\d{2}:\d{2})', 'nullable': True}
    }
}


TAGS = {
    'header': {'name': 'h2', 'attrs': None},
    'client': {'name': 'h4', 'attrs': None},
    'itinerary': {'name': 'p', 'attrs': None},
    'prices': {'name': 'tbody', 'attrs': None},
    'address': {'name': 'div', 'attrs': {'data-collapsed': 'true'}}
}


OVERNIGHTS = [
    ('Stadtkurier', 'city_tour'),
    ('Stadt Stopp(s)', 'extra_stops'),
    ('OV Ex Nat PU', 'overnight'),
    ('ON Ex Nat Del.', 'overnight'),
    ('OV EcoNat PU', 'overnight'),
    ('OV Ex Int PU', 'overnight'),
    ('ON Int Exp Del', 'overnight'),
    ('EmpfangsbestÃ¤t.', 'fax_confirm'),
    ('Wartezeit min.', 'waiting_time')
]


def scrape_from_soup(job):
    """
    In goes a webpage, out comes data. The unit of data is a stamped tuple.
    Each tuple holds a dictionary with job info (ID, price etc...) plus a
    list of addresses. All fields are stored as strings.
    """

    order = job.data.find(id='order_detail')
    addresses = list()
    info = dict()

    # Step 1: scrape all sections except prices
    # -----------------------------------------
    sections = ['header', 'client', 'itinerary']

    for section in sections:
        fragment = order.find_next(name=TAGS[section]['name'])
        fields = _scrape_fragment(BLUEPRINTS[section], fragment, job.stamp, section)
        info.update(fields)

    # Step 2: scrape the price table
    # ------------------------------
    fragment = order.find(TAGS['prices']['name'])
    prices = _scrape_prices(fragment)
    info.update(prices)

    # Step 3: scrape an arbitrary number of addresses
    # -----------------------------------------------
    fragments = order.find_all(name=TAGS['address']['name'], attrs=TAGS['address']['attrs'])

    for fragment in fragments:
        address = _scrape_fragment(BLUEPRINTS['address'], fragment, job.stamp, 'address')
        addresses.append(address)

    return Stamped(job.stamp, RawData(info, addresses))


def _scrape_fragment(blueprints, soup_fragment, stamp, tag):
    """
    Scrape a very small fragment of the webpage following the relevant instructions.
    Save a report inside the log directory if a non-nullable field cannot be found.
    """

    contents = list(soup_fragment.stripped_strings)
    collected = {}

    for field, bp in blueprints.items():
        try:
            matched = match(bp['pattern'], contents[bp['line_nb']])
        except IndexError:
            collected[field] = None
            _report_failure(stamp, field, bp, contents, tag)
        else:
            if matched:
                collected[field] = matched.group(1)
            else:
                collected[field] = None
                if not bp['nullable']:
                    _report_failure(stamp, field, bp, contents, tag)

    return collected


def _scrape_prices(soup_fragment):
    """
    Scrape the price information at the bottom of the webpage. This
    section is treated seperately because it's in the form of a table.
    """

    cells = list(soup_fragment.stripped_strings)
    price_table = dict(zip(cells[::2], cells[1::2]))

    for old, new in OVERNIGHTS:
        if old in price_table:
            price_table[new] = price_table.pop(old)
        else:
            price_table[new] = None

    if price_table['waiting_time'] is not None:
        # We want the price of the waiting time not the time itself.
        price_table['waiting_time'] = price_table['waiting_time'][7::]

    return price_table


def _report_failure(stamp, field_name, blueprint, fragment, tag):
    """
    Print a report showing precisely the context in which
    the scraping went wrong and the reason why it went wrong.
    """

    filepath = _report_filepath(stamp)
    debug('Saving scraping failure report in %s', filepath)

    with open(filepath, 'a') as rf:
        with redirect_stdout(rf):
            print(FAILURE_REPORT.format(date=stamp.date,
                                        uuid=stamp.uuid,
                                        field=field_name,
                                        nb=blueprint['line_nb'],
                                        tag=tag))
            if len(fragment):
                for line_nb, line_content in enumerate(fragment):
                    print(str(line_nb) + ': ' + line_content)
            else:
                print('No content inside %s', tag)

            print(BREAK)


def _job_url_query(stamp):
    return JOB_QUERY_URL.format(uuid=stamp.uuid, date=stamp.date.strftime('%d.%m.%Y'))


def _report_filepath(stamp):
    return join(USER_BASE_DIR, JOB_FILENAME.format(uuid=stamp.uuid, date=stamp.date.strftime('%d-%m-%Y')))

