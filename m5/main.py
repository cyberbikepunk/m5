#!/usr/bin/env python
""" The command line API for the M5 package. """


from argparse import ArgumentParser, RawDescriptionHelpFormatter
from logging import basicConfig, INFO, DEBUG, info
from datetime import date, timedelta
from textwrap import dedent
from time import strptime

from m5.user import User
from m5.spider import Downloader
from m5.pipeline import Packager
from m5.scraper import Reader


def build_parser():
    p = ArgumentParser(prog='m5',
                       description=dedent(__doc__),
                       formatter_class=RawDescriptionHelpFormatter,
                       fromfile_prefix_chars='@',
                       epilog='To read arguments from file, type: m5 @/absolute/path/to/file.')

    p.add_argument('-u',
                   help='username for the company website',
                   type=str,
                   default=None,
                   dest='username')

    p.add_argument('-p',
                   help='password for the company website',
                   type=str,
                   default=None,
                   dest='password')

    p.add_argument('-v',
                   help='switch the verbose mode on',
                   default=False,
                   action='store_true',
                   dest='verbose')

    p.add_argument('-o',
                   help='switch the offline mode on',
                   default=False,
                   action='store_true',
                   dest='offline')

    p.add_argument('-s',
                   help='scrape all data since dd-mm-yyyy',
                   type=since,
                   default=date.today(),
                   dest='since')

    return p


def setup_logger(verbose):
    basicConfig(level=DEBUG if verbose else INFO,
                format='M5 '
                       '[%(asctime)s] '
                       '[%(module)s] '
                       '[%(funcName)s] '
                       '%(message)s')


def since(date_string):
    t = strptime(date_string, '%d-%m-%Y')
    day = date(t.tm_year, month=t.tm_mon, day=t.tm_mday)

    if day > date.today():
        raise ValueError

    return day


def factory(**options):
    u = User(**options)
    d = Downloader(u.web_session)
    s = Reader()
    p = Packager()
    a = Archiver(u.db_session)
    return u, d, s, p, a


def scrape(**options):
    """
    Scrape user data from the company website, process it
    as best as we can and store it inside the local database.
    """

    info('Starting the data scraping process.')

    start_date = options.pop('since')
    period = date.today() - start_date
    days = range(period.days)

    u, d, s, p, a = factory(**options)
    u.initialize()

    for day in days:
        date_ = start_date + timedelta(days=day)
        webpage = d.download_one_day(date_)

        if webpage:
            items = s.scrape(webpage)
            tables = p.package(items)
            a.archive(tables)

        info('Processed {n}/{N} ({percent}%).'.
             format(n=day, N=len(days), percent=int((day+1)/len(days)*100)))


if __name__ == '__main__':
    parser = build_parser()
    args = parser.parse_args()
    setup_logger(args.verbose)
    info('Arguments = %s', args)
    scrape(**vars(args))
