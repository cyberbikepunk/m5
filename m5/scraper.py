""" The scraper module extracts data from webpages. """


from contextlib import redirect_stdout
from os.path import join
from re import match
from collections import namedtuple
from json import loads
from logging import debug

from m5.settings import TAGS_FILE, BLUEPRINT_FILE, OVERNIGHTS_FILE
from m5.settings import BREAK, JOB_URL_QUERY_FORMAT, OUTPUT_DIR, REPORT_MESSAGE


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


Stamped = namedtuple('Stamped', ['stamp', 'data'])
Stamp = namedtuple('Stamp', ['date', 'uuid', 'user'])


with open(OVERNIGHTS_FILE) as f:
    OVERNIGHTS = loads(f.read())

with open(TAGS_FILE) as f:
    TAGS = loads(f.read())

with open(BLUEPRINT_FILE) as f:
    BLUEPRINTS = loads(f.read())


def scrape_one_day(soups):
    """
    In go webpages (typically all the jobs for one day), out comes data.
    The unit of data is a stamped tuple. Each tuple holds a dictionary with
    job details (ID, price etc...) and a list of addresses. All fields are
    stored as strings.
    """

    assert soups is not None, 'Cannot scrape nothing.'
    jobs = list()

    for i, soup in enumerate(soups):
        job, addresses = _scrape_one_job(soup)
        fields = Stamped(soup.stamp, (job, addresses))
        jobs.append(fields)

        debug('(%s/%s) Scraped: %s', len(soups), i+1, job_url_query)

    return jobs


def job_url_query(soup):
    JOB_URL_QUERY_FORMAT.format(uuid=soup.stamp.uuid, date=soup.stamp.date.strftime('%d.%m.%Y'))


def _scrape_one_job(soup):
    """
    Fragment the webpage into small digestable pieces
    and send each one of them off to the regex butcher.
    """

    order = soup.data.find(id='order_detail')

    addresses = list()
    job = dict()

    # Step 1: scrape all sections except prices
    # -----------------------------------------
    sections = ['header', 'client', 'itinerary']

    for section in sections:
        fragment = order.find_next(name=TAGS[section]['name'])
        fields = _scrape_one_fragment(BLUEPRINTS[section], fragment, soup.stamp, section)
        job.update(fields)

    # Step 2: scrape the price table
    # ------------------------------
    fragment = order.find(TAGS['prices']['name'])
    prices = _scrape_prices(fragment)
    job.update(prices)

    # Step 3: scrape an arbitrary number of addresses
    # -----------------------------------------------
    fragments = order.find_all(name=TAGS['address']['name'], attrs=TAGS['address']['attrs'])

    for fragment in fragments:
        address = _scrape_one_fragment(BLUEPRINTS['address'], fragment, soup.stamp, 'address')
        addresses.append(address)

    return job, addresses


def _scrape_one_fragment(blueprints, soup_fragment, stamp, tag):
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

    report_filepath = join(OUTPUT_DIR, stamp.user, job_url_query(stamp))

    with open(report_filepath, 'a') as rf:
        with redirect_stdout(rf):
            print(REPORT_MESSAGE.format(date=stamp.date,
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


if __name__ == '__main__':
    pass
